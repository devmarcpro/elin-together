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

    [HarmonyPrefix]
    internal static bool OnAdvanceMin()
    {
        return NetSession.Instance.IsHost;
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
    ///     with everything a passing hour or day does here, and its player lives that time. <br />
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

        EClass.world.date.AdvanceMin(behind);

        // as a client does for the time its host advanced, see WorldDateAdvanceDelta
        var pc = EClass.pc;
        var ticks = behind * 4 / 6;
        for (var i = 0; i < ticks && pc is { isDead: false }; ++i) {
            pc.TickConditions();
        }

        return behind;
    }
}
