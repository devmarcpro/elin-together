using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A player alone on a map of its own plays in its copy of the world. What travels with it comes back with it
///     (its character, its companions). A character of the base that does NOT travel with it stayed in that copy
///     for good: a recruit sent home from the field, an egg hatched there, a companion told to go home or dead and
///     waiting at the base. Reported by a player on 2026-10-12: "the NPCs I recruit alone in the field always
///     disappear". They are noted here as they join the base or leave the party, and handed to the host with the
///     next release of the zone (ZoneLeaseRelease.Residents)
/// </summary>
[HarmonyPatch]
internal static class AwayResidents
{
    private static readonly HashSet<int> _changed = [];

    private static bool Alone => !ElinDelta.IsApplying && NetSession.Instance is { IsZoneAuthority: true, Transport: ElinNetClient };

    [HarmonyPostfix]
    [HarmonyPatch(typeof(FactionBranch), nameof(FactionBranch.AddMemeber))]
    internal static void OnJoinedBase(Chara c)
    {
        if (Alone && c is { IsPlayer: false }) {
            _changed.Add(c.uid);
        }
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Party), nameof(Party.RemoveMember))]
    internal static void OnLeftParty(Chara c)
    {
        if (Alone && c is { IsPlayer: false }) {
            _changed.Add(c.uid);
        }
    }

    /// <param name="handed">the zone is handed back (not a checkpoint): what is sent now is not sent again</param>
    internal static List<LZ4Bytes>? Collect(bool handed)
    {
        if (_changed.Count == 0) {
            return null;
        }

        // (a companion that died on the way still travels with its player, dead: it goes with the companions)
        var travelling = CompanionHelper.TravellingWith(EClass.pc);
        var residents = _changed
            .Select(uid => EClass.game.cards.globalCharas.Find(uid))
            .Where(c => c is { isDestroyed: false, IsPCParty: false, IsPlayer: false } && !travelling.Contains(c))
            .Select(c => LZ4Bytes.Create(c!))
            .ToList();
        if (handed) {
            _changed.Clear();
        }

        return residents.Count == 0 ? null : residents;
    }
}
