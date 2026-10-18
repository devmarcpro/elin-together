using System.Collections.Generic;
using System.Linq;
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

        if (card.GetRootCard() is not Chara && kind != CardSettingDelta.Door) {
            RemoteBasePaidPatch.WarnHostOnly();
        }

        connection.Delta.AddRemote(CardSettingDelta.Create(card, kind));
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Card), nameof(Card.c_note), MethodType.Setter)]
    internal static void OnNote(Card __instance)
    {
        Tell(__instance, CardSettingDelta.Note);
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Card), nameof(Card.c_refText), MethodType.Setter)]
    internal static void OnName(Card __instance)
    {
        Tell(__instance, CardSettingDelta.Name);
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.isMasked), MethodType.Setter)]
    internal static void OnMask(Card __instance, out bool __state)
    {
        __state = __instance.isMasked;
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Card), nameof(Card.isMasked), MethodType.Setter)]
    internal static void OnMasked(Card __instance, bool __state)
    {
        if (__instance.isMasked != __state) {
            Tell(__instance, CardSettingDelta.Masked);
        }
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

/// <summary>
///     The house board's roof, walls and music: every change of its menu ends in ApplyData
/// </summary>
[HarmonyPatch(typeof(TraitHouseBoard), nameof(TraitHouseBoard.ApplyData))]
internal static class HouseBoardSettingEvent
{
    [HarmonyPostfix]
    internal static void OnApplyData(TraitHouseBoard __instance)
    {
        CardSettingEvent.Tell(__instance.owner, CardSettingDelta.HouseBoard);
    }
}

[HarmonyPatch(typeof(TeleportManager), nameof(TeleportManager.SetID))]
internal static class TeleporterSettingEvent
{
    [HarmonyPostfix]
    internal static void OnSetId(TraitTeleporter t)
    {
        CardSettingEvent.Tell(t.owner, CardSettingDelta.Teleporter);
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

/// <summary>
///     A door opened or closed by hand (the "open", "close" of its menu). A walker opens it in every game already, and
///     each game shuts its doors after a while by itself: told, a town's doors would never stop talking
/// </summary>
[HarmonyPatch]
internal static class DoorSettingEvent
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return AccessTools.GetDeclaredMethods(typeof(TraitDoor))
            .Concat(typeof(TraitDoor).GetNestedTypes(AccessTools.all).SelectMany(AccessTools.GetDeclaredMethods))
            .Where(m => m.Name.Contains("<TrySetAct>"));
    }

    [HarmonyPostfix]
    internal static void OnDoorByHand(object __instance)
    {
        var door = __instance as TraitDoor ?? AccessTools.GetDeclaredFields(__instance.GetType())
            .Select(f => f.GetValue(__instance)).OfType<TraitDoor>().FirstOrDefault();
        CardSettingEvent.Tell(door?.owner, CardSettingDelta.Door);
    }
}

