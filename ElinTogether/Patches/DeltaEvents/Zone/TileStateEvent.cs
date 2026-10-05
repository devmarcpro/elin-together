using System.Collections.Generic;
using System.Reflection;
using ElinTogether.Models;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Every setter of a cell's terrain marks the cell: its state is told at the end of the frame, see
///     <see cref="TileStateDelta" />
/// </summary>
[HarmonyPatch]
internal static class TileStateEvent
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return [
            AccessTools.Method(typeof(Map), nameof(Map.SetFloor), [typeof(int), typeof(int), typeof(int), typeof(int), typeof(int)]),
            AccessTools.Method(typeof(Map), nameof(Map.SetBlock), [typeof(int), typeof(int), typeof(int), typeof(int), typeof(int)]),
            AccessTools.Method(typeof(Map), nameof(Map.SetObj),
                [typeof(int), typeof(int), typeof(int), typeof(int), typeof(int), typeof(int), typeof(bool)]),
            AccessTools.Method(typeof(Map), nameof(Map.SetBridge)),
            AccessTools.Method(typeof(Map), nameof(Map.SetRoofBlock)),
            AccessTools.Method(typeof(Map), nameof(Map.SetDeco)),
            AccessTools.Method(typeof(Map), nameof(Map.SetBlockDir)),
        ];
    }

    [HarmonyPostfix]
    internal static void OnSet(Map __instance, int x, int z)
    {
        TileStateDelta.Mark(__instance, x, z);
    }
}
