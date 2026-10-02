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
        if (__result && NetSession.Instance.Transport is ElinNetHost host && host.IsLeased(__instance.uid)) {
            __result = false;
        }
    }
}
