using System.Collections.Generic;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Each hour the game lets what "the player" carries go off (food, the "just cooked" bonus): the bag of the
///     local player only. On the host the bags of the other players never aged; they are told how far it went (CardDecayDelta)
/// </summary>
[HarmonyPatch(typeof(Zone), nameof(Zone.OnSimulateHour))]
internal static class RemoteDecayPatch
{
    private static Dictionary<int, int>? _mapBefore;

    // the map's own things (fridges, floor) age in this call too, and the guests' copies must follow
    [HarmonyPrefix]
    internal static void BeforeSimulateHour(Zone __instance, VirtualDate date)
    {
        _mapBefore = date.IsRealTime && __instance == EClass._zone &&
                     NetSession.Instance.Connection is ElinNetHost { ActiveRemoteCharas.Count: > 0 }
            ? CardDecayDelta.SnapshotMap()
            : null;
    }

    [HarmonyPostfix]
    internal static void OnSimulateHour(Zone __instance, VirtualDate date)
    {
        var before = _mapBefore;
        _mapBefore = null;
        if (!date.IsRealTime || __instance != EClass._zone || NetSession.Instance.Connection is not ElinNetHost host) {
            return;
        }

        var mapAged = before is null ? null : CardDecayDelta.CreateMapChanges(before);
        foreach (var (peerId, player) in host.ActiveRemoteCharas) {
            if (player?.currentZone != __instance) {
                continue;
            }

            // the map ages whoever's hour it is
            if (mapAged is not null) {
                host.SendDeltaTo(peerId, mapAged);
            }

            // an hour another player made pass is not this one's: its food does not go off for it
            if (player.isDead || !WorldDateAdvanceEvent.LivesThisHour(player)) {
                continue;
            }

            player.DecayNatural();
            if (CardDecayDelta.Create(player) is { } aged) {
                host.SendDeltaTo(peerId, aged);
            }
        }
    }
}

/// <summary>
///     The same for the local player, whose bag the game ages itself each hour: not during the hours its game
///     catches up with (see WorldDateAdvanceEvent.CatchUp)
/// </summary>
[HarmonyPatch(typeof(Card), nameof(Card.DecayNatural))]
internal static class OwnDecayPatch
{
    [HarmonyPrefix]
    internal static bool OnDecayNatural(Card __instance)
    {
        return !WorldDateAdvanceEvent.IsCatchingUp || __instance != EClass.pc;
    }
}
