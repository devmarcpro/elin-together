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
    [HarmonyPostfix]
    internal static void OnSimulateHour(Zone __instance, VirtualDate date)
    {
        if (!date.IsRealTime || __instance != EClass._zone || NetSession.Instance.Connection is not ElinNetHost host) {
            return;
        }

        foreach (var (peerId, player) in host.ActiveRemoteCharas) {
            // an hour another player made pass is not this one's: its food does not go off for it
            if (player is not { isDead: false } || player.currentZone != __instance ||
                !WorldDateAdvanceEvent.LivesThisHour(player)) {
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
