using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The game makes the boss of a Nefia flee, and marks the Nefia conquered, when its floor is entered a second
///     time: alone, that is a player who left the fight. The visit count travels with the map, so the first entry of
///     a player joining another one on that floor counted as a second visit: boss gone, dungeon "conquered"
/// </summary>
[HarmonyPatch(typeof(Zone), nameof(Zone.Simulate))]
internal static class BossFleePatch
{
    [HarmonyPrefix]
    internal static void OnSimulate(Zone __instance, out int __state)
    {
        __state = 0;
        // only the first entry of a player who joins another one there
        if (!ZoneLeaseState.Imported.Remove(__instance.uid) || NetSession.Instance.Transport is null) {
            return;
        }

        __state = __instance.uidBoss;
        __instance.uidBoss = 0;
    }

    // (a finalizer: the game swallows an exception of Simulate, the boss must not be forgotten with it)
    [HarmonyFinalizer]
    internal static void OnSimulateEnd(Zone __instance, int __state)
    {
        if (__state != 0) {
            __instance.uidBoss = __state;
        }
    }
}
