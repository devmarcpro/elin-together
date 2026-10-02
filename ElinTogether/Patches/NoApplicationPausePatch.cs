using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal class NoApplicationPausePatch
{
    [HarmonyCleanup]
    [HarmonyPostfix]
    [HarmonyPatch(typeof(CoreConfig), nameof(CoreConfig.Apply))]
    internal static void OnOverrideBackgroundRunning()
    {
        Application.runInBackground = true;
        // very first launch of the game: no config yet when the patches are installed
        if (EMono.core?.config?.other is { } other) {
            other.runBackground = true;
        }
    }
}