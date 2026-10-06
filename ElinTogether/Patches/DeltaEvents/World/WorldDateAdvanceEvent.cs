using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(GameDate), nameof(GameDate.AdvanceMin))]
internal static class WorldDateAdvanceEvent
{
    /// <summary>
    ///     A date further than this from ours is not a date to catch up with (a month of the game)
    /// </summary>
    private const int MaxCatchUpMinutes = Date.MonthToken;

    // minutes of the AdvanceMin in progress, 0 outside of one
    private static int _advancing;

    /// <summary>
    ///     The date is advancing by time another player made pass on another map: nobody here lived it
    /// </summary>
    internal static bool IsCatchingUp { get; private set; }

    /// <summary>
    ///     Whether the hour passing now is one this other player of the map lives (what it carries goes off). <br />
    ///     Minute by minute is the time of the map, everyone's on it. A jump is the act of the one who simulates
    ///     it (a step on the world map), not theirs; except a night, which every player of the map sleeps
    /// </summary>
    internal static bool LivesThisHour(Chara remotePlayer)
    {
        return !IsCatchingUp && (_advancing == 1 || remotePlayer.conSleep is not null);
    }

    [HarmonyPrefix]
    internal static bool OnAdvanceMin(int a)
    {
        _advancing = a;
        return NetSession.Instance.IsHost;
    }

    // not in the postfix: it is skipped when the game's own code throws, and the jump would never end
    [HarmonyFinalizer]
    internal static void OnAdvanceMinEnd()
    {
        _advancing = 0;
    }

    [HarmonyPostfix]
    internal static void OnAfterAdvanceMin(int a)
    {
        var session = NetSession.Instance;

        // one date for the world: a player who simulates a map on its own tells the host how far it got
        if (session is { IsZoneAuthority: true, Transport: ElinNetClient main } && session.Rules.UseSharedWorldTime) {
            main.SendWhileAway(new WorldTimeReportDelta {
                GameDate = [..EClass.world.date.raw],
            });
        }

        if (session.Connection is not ElinNetHost host) {
            return;
        }

        // host only
        host.Delta.AddRemote(new WorldDateAdvanceDelta {
            Minutes = a,
            GameDate = [..EClass.world.date.raw],
            CatchUp = IsCatchingUp,
        });
    }

    /// <summary>
    ///     Date.GetRaw of a date received as its fields
    /// </summary>
    internal static int Minutes(int[] raw)
    {
        return raw.Length < 5 ? 0 : raw[4] + raw[3] * Date.HourToken + raw[2] * Date.DayToken + raw[1] * Date.MonthToken + raw[0] * 518400;
    }

    /// <summary>
    ///     Another game of the session is further in time: this one, which simulates a map, goes there too,
    ///     with everything a passing hour or day does to the map and the world. Its player did not make that
    ///     time pass and does not live it: no turns of hunger or conditions, nothing going off in its bag, no
    ///     time taken from its quests (a player away saw the host's travel starve it and rot its food). <br />
    ///     Going there tells the others in turn (the host its players, a map holder its visitors)
    /// </summary>
    /// <returns>the minutes advanced, 0 when this game is not behind</returns>
    internal static void CatchUpNextFrame(int[] raw)
    {
        // not from inside the delta loop: what a passing hour does here must be told like anything this game does
        EClass.core.actionsNextFrame.Add(() => CatchUp(raw));
    }

    internal static int CatchUp(int[] raw)
    {
        var behind = Minutes(raw) - EClass.world.date.GetRaw();
        if (behind is <= 0 or > MaxCatchUpMinutes || EClass.game?.activeZone is null) {
            return 0;
        }

        EmpLog.Debug("World time: catching up {Minutes} minute(s)", behind);

        PersonalQuests.Postpone(behind);

        IsCatchingUp = true;
        try {
            EClass.world.date.AdvanceMin(behind);
        } finally {
            IsCatchingUp = false;
        }

        return behind;
    }
}
