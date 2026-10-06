using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The host cleans up zones nobody needs when it saves (expired fields, quest zones). A zone a player is in
///     is needed, whatever the host's copy of it looks like
/// </summary>
[HarmonyPatch(typeof(Zone), nameof(Zone.CanDestroy))]
internal static class LeasedZonePatch
{
    [HarmonyPostfix]
    internal static void OnCanDestroy(Zone __instance, ref bool __result)
    {
        if (!__result || NetSession.Instance.Transport is not ElinNetHost host) {
            return;
        }

        // the whole dungeon: the floors between the top and the one a player is on are its way back
        if (host.IsHeld(__instance)) {
            __result = false;
        }
    }
}
