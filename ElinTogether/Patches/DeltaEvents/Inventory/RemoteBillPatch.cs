using ElinTogether.Models;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The host repeats what a player does at the tax chest so the bill is settled in the world, but the money
///     came out of that player's purse: not out of the host's too
/// </summary>
[HarmonyPatch(typeof(Card), nameof(Card.TryPay))]
internal static class RemoteBillPatch
{
    [HarmonyPrefix]
    internal static bool OnTryPay(Card __instance, ref bool __result)
    {
        if (!InvOwnerOnProcessDelta.PaidByRemote || !__instance.IsPC) {
            return true;
        }

        __result = true;
        return false;
    }
}
