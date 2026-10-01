using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Goods of two players never merge in the shipping box, each is paid for its own, see ShippingHelper
/// </summary>
[HarmonyPatch(typeof(Thing), nameof(Thing.CanStackTo))]
internal static class ShippingStackPatch
{
    [HarmonyPostfix]
    internal static void OnCanStackTo(Thing __instance, Thing to, ref bool __result)
    {
        if (__result && ShippingHelper.IsShippingBox(to.parent as Card) && __instance.ShipperUid != to.ShipperUid) {
            __result = false;
        }
    }
}
