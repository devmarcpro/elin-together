using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     While the game's split menu does its split (the local function Process of Thing.ShowSplitMenu): the part
///     put back beside the stack is that menu's, see CardSplitStackDelta. Other splits (a meal begun then given up,
///     which puts the bite back) are not
/// </summary>
[HarmonyPatch]
internal static class SplitMenuPatch
{
    internal static bool IsSplitting { get; private set; }

    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return typeof(Thing).GetMethods(BindingFlags.Instance | BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public)
            .Concat(typeof(Thing).GetNestedTypes(BindingFlags.NonPublic).SelectMany(t =>
                t.GetMethods(BindingFlags.Instance | BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public)))
            .Where(m => m.Name.Contains("ShowSplitMenu") && m.Name.Contains("Process"));
    }

    [HarmonyPrefix]
    internal static void Before()
    {
        IsSplitting = true;
    }

    [HarmonyFinalizer]
    internal static void After()
    {
        IsSplitting = false;
    }
}
