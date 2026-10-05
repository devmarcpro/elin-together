using System.Collections.Generic;
using System.Reflection;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The settings of an object of the map are told to the others where they change, not where they are clicked
///     (menus of lambdas), see <see cref="CardSettingDelta" />
/// </summary>
[HarmonyPatch]
internal static class CardSettingEvent
{
    internal static void Tell(Card? card, byte kind)
    {
        if (card is null || ElinDelta.IsApplying || NetSession.Instance.Connection is not { } connection ||
            !CardCache.Contains(card)) {
            return;
        }

        connection.Delta.AddRemote(CardSettingDelta.Create(card, kind));
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Card), nameof(Card.c_note), MethodType.Setter)]
    internal static void OnNote(Card __instance)
    {
        Tell(__instance, CardSettingDelta.Note);
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.SetSale))]
    internal static void OnSale(Card __instance, out bool __state)
    {
        __state = __instance.isSale;
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Card), nameof(Card.SetSale))]
    internal static void OnSaleSet(Card __instance, bool __state)
    {
        if (__instance.isSale != __state) {
            Tell(__instance, CardSettingDelta.Sale);
        }
    }

}

[HarmonyPatch]
internal static class BedSettingEvent
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return [
            AccessTools.Method(typeof(TraitBed), nameof(TraitBed.AddHolder)),
            AccessTools.Method(typeof(TraitBed), nameof(TraitBed.RemoveHolder)),
            AccessTools.Method(typeof(TraitBed), nameof(TraitBed.ClearHolders)),
            AccessTools.Method(typeof(TraitBed), nameof(TraitBed.SetBedType)),
        ];
    }

    [HarmonyPostfix]
    internal static void OnBed(TraitBed __instance)
    {
        CardSettingEvent.Tell(__instance.owner, CardSettingDelta.Bed);
    }
}
