using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Curse, enchant level and acid coating of the items of a player are decided by the game of that player, see
///     <see cref="CardItemStateDelta" />
/// </summary>
[HarmonyPatch]
internal static class CardItemStateEvent
{
    private static bool Skip(Card card)
    {
        return !CardItemStateDelta.Landing && CardItemStateDelta.IsForeign(card);
    }

    private static void Tell(Card card)
    {
        if (CardItemStateDelta.Landing || NetSession.Instance.Connection is not { } connection ||
            CardItemStateDelta.OwnerOf(card) is not { IsPC: true } || !CardCache.Contains(card)) {
            return;
        }

        connection.Delta.AddRemote(CardItemStateDelta.Create(card));
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.SetBlessedState))]
    [HarmonyPatch(typeof(Card), nameof(Card.ModEncLv))]
    internal static bool SkipMethod(Card __instance)
    {
        return !Skip(__instance);
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.isAcidproof), MethodType.Setter)]
    internal static bool SkipAcidproof(Card __instance)
    {
        return !Skip(__instance);
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Card), nameof(Card.SetBlessedState))]
    [HarmonyPatch(typeof(Card), nameof(Card.ModEncLv))]
    internal static void OnMethod(Card __instance)
    {
        Tell(__instance);
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Card), nameof(Card.isAcidproof), MethodType.Setter)]
    internal static void OnAcidproof(Card __instance)
    {
        Tell(__instance);
    }
}
