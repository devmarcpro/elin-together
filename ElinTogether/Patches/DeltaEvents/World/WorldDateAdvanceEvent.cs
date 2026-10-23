using System.Linq;
using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(GameDate), nameof(GameDate.AdvanceMin))]
internal static class WorldDateAdvanceEvent
{
    /// <summary>
    ///     A date further than this from ours is not a date to catch up with (a month of the game)
    /// </summary>
    private const int MaxCatchUpMinutes = Date.MonthToken;

    // a player in a fight, loading or in a dialog waits this long at most for a catch-up from someone's trip
    private const float HoldSeconds = 60f;

    // the trip told to this player is over when no hour of it came for this long
    private const float TripEndSeconds = 2f;

    // minutes of the AdvanceMin in progress, 0 outside of one
    private static int _advancing;

    // the catch-up waiting for the next frame: the date to reach (minutes), whose trip it is, since when it waits
    private static int _pendingTarget;
    private static (string Name, int Uid)? _pendingTraveller;
    private static float _pendingSince;
    private static int _pendingLeadOf;
    private static bool _pumping;

    // the trip of another player this player is told about once it is over
    private static string? _tripOf;
    private static int _tripMinutes;
    private static float _tripAt;

    /// <summary>
    ///     The date is advancing by time another player made pass on another map: nobody here lived it
    /// </summary>
    internal static bool IsCatchingUp { get; private set; }

    /// <summary>
    ///     The world map trip the AdvanceMin in progress is part of (a step, an hour of the express travel, a
    ///     catch-up for one): its player, told along with the date (WorldDateAdvanceDelta.Traveller)
    /// </summary>
    internal static (string Name, int Uid)? Traveller { get; set; }

    /// <summary>
    ///     Personal Pace: the catch-up in progress pays the lead of this player (its character), whose own quests
    ///     already lost those hours: it is not told it lost nothing (WorldDateAdvanceDelta.LeadOf)
    /// </summary>
    internal static int LeadOf { get; private set; }

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

        // the timer of a quest's map (harvest, music, wedding) is the time of the player who plays it:
        // GameDate.AdvanceMin just added the time another player made pass elsewhere
        if (IsCatchingUp && session.IsHost && EClass._zone is { } zone) {
            foreach (var zoneEvent in zone.events.list) {
                zoneEvent.minElapsed -= a;
            }
        }

        // one date for the world: a player who simulates a map on its own tells the host how far it got
        if (session is { IsZoneAuthority: true, Transport: ElinNetClient main } && session.Rules.UseSharedWorldTime) {
            main.SendWhileAway(new WorldTimeReportDelta {
                GameDate = [..EClass.world.date.raw],
                Travel = Traveller is not null && !IsCatchingUp,
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
            LeadOf = IsCatchingUp ? LeadOf : 0,
            Traveller = Traveller?.Name,
            TravellerUid = Traveller?.Uid ?? 0,
        });
    }

    /// <summary>
    ///     Date.GetRaw of a date received as its fields
    /// </summary>
    internal static int Minutes(int[] raw)
    {
        return raw.Length < 5 ? 0 : raw[4] + raw[3] * Date.HourToken + raw[2] * Date.DayToken + raw[1] * Date.MonthToken + raw[0] * 518400;
    }

    internal static void CatchUpNextFrame(int[] raw, (string Name, int Uid)? traveller = null)
    {
        CatchUpNextFrame(Minutes(raw), traveller);
    }

    /// <summary>
    ///     Another game of the session is further in time: this one goes there too, see <see cref="CatchUp" />. <br />
    ///     Not from inside the delta loop: what a passing hour does here must be told like anything this game
    ///     does. Council 2026-10-23: a catch-up for someone's trip waits while this player fights, loads or talks
    ///     (60 s at most, silently), and once the trip is over one line says who travelled
    /// </summary>
    internal static void CatchUpNextFrame(int target, (string Name, int Uid)? traveller = null, int leadOf = 0)
    {
        if (target <= _pendingTarget) {
            return;
        }

        if (leadOf != 0) {
            _pendingLeadOf = leadOf;
        }

        if (_pendingTarget == 0) {
            _pendingSince = Time.realtimeSinceStartup;
        }

        _pendingTarget = target;
        _pendingTraveller = traveller ?? _pendingTraveller;
        Pump();
    }

    /// <summary>
    ///     The date this many more minutes reach, counting what already waits to be caught up
    /// </summary>
    internal static int AfterPending(int minutes)
    {
        return System.Math.Max(EClass.world.date.GetRaw(), _pendingTarget) + minutes;
    }

    /// <summary>
    ///     The world went on by someone's trip without this player, which lost nothing: said once the trip is over,
    ///     not at every step of it
    /// </summary>
    internal static void NoteTrip(string traveller, int minutes)
    {
        if (_tripOf != traveller) {
            SayTrip();
        }

        _tripOf = traveller;
        _tripMinutes += minutes;
        _tripAt = Time.realtimeSinceStartup;
        Pump();
    }

    private static void Pump()
    {
        if (_pumping) {
            return;
        }

        _pumping = true;
        EClass.core.actionsNextFrame.Add(OnFrame);
    }

    private static void OnFrame()
    {
        _pumping = false;

        if (_pendingTarget > 0) {
            if (_pendingTraveller is not null && Busy() && Time.realtimeSinceStartup - _pendingSince < HoldSeconds) {
                Pump();
                return;
            }

            var (target, traveller, leadOf) = (_pendingTarget, _pendingTraveller, _pendingLeadOf);
            (_pendingTarget, _pendingTraveller, _pendingLeadOf) = (0, null, 0);
            var moved = CatchUp(target, traveller, leadOf);
            if (traveller is { } who && moved > 0 && (leadOf == 0 || leadOf != EClass.pc?.uid)) {
                NoteTrip(who.Name, moved);
            }
        }

        if (_tripOf is not null) {
            if (Time.realtimeSinceStartup - _tripAt < TripEndSeconds) {
                Pump();
            } else {
                SayTrip();
            }
        }
    }

    private static void SayTrip()
    {
        if (_tripOf is not null && _tripMinutes >= Date.HourToken && EClass.core.IsGameStarted) {
            Msg.Say("emp_ui_travel_bystander".Loc(_tripOf, _tripMinutes / Date.HourToken));
        }

        (_tripOf, _tripMinutes) = (null, 0);
    }

    /// <summary>
    ///     This player is in the middle of something the date should not jump under: a fight, a loading, a dialog
    /// </summary>
    internal static bool Busy()
    {
        if (EClass.game is not { } game || game.isLoading || EClass.scene.mode != Scene.Mode.Zone ||
            EClass.ui.GetLayer<LayerDrama>() is not null) {
            return true;
        }

        if (EClass.pc is not { isDead: false } pc || EClass._map is not { } map) {
            return false;
        }

        return pc.IsInCombat || map.charas.Any(c => !c.isDead && c.IsHostile(pc) && c.Dist(pc) <= 8);
    }

    /// <summary>
    ///     Another game of the session is further in time: this one, which simulates a map, goes there too,
    ///     with everything a passing hour or day does to the map and the world. Its player did not make that
    ///     time pass and does not live it: no turns of hunger or conditions, nothing going off in its bag, no
    ///     time taken from its quests (a player away saw the host's travel starve it and rot its food). <br />
    ///     Going there tells the others in turn (the host its players, a map holder its visitors)
    /// </summary>
    /// <returns>the minutes advanced, 0 when this game is not behind</returns>
    private static int CatchUp(int target, (string Name, int Uid)? traveller, int leadOf)
    {
        var behind = target - EClass.world.date.GetRaw();
        if (behind is <= 0 or > MaxCatchUpMinutes || EClass.game?.activeZone is null) {
            return 0;
        }

        EmpLog.Debug("World time: catching up {Minutes} minute(s)", behind);

        PersonalQuests.Postpone(behind);

        IsCatchingUp = true;
        Traveller = traveller;
        LeadOf = leadOf;
        try {
            EClass.world.date.AdvanceMin(behind);
        } finally {
            IsCatchingUp = false;
            Traveller = null;
            LeadOf = 0;
        }

        return behind;
    }
}
