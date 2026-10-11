using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     True while the game gives what the STORY gives: a story quest starts or completes (never a random quest, those are
///     each player's own), or the outcome of a dialog runs. What <c>Player.DropReward</c> drops meanwhile is a
///     reward of the group, see ElinNetHost.NoteStoryReward
/// </summary>
internal static class StoryScope
{
    private static int _depth;

    internal static bool Active => _depth > 0;

    [HarmonyPatch(typeof(Quest), nameof(Quest.Complete))]
    internal static class OnQuestComplete
    {
        [HarmonyPrefix]
        internal static void Begin(Quest __instance, out bool __state)
        {
            __state = !__instance.IsRandomQuest;
            if (__state) {
                _depth++;
            }
        }

        // a finalizer: a throw does not leave the story "on"
        [HarmonyFinalizer]
        internal static void End(bool __state)
        {
            if (__state) {
                _depth--;
            }
        }
    }

    // what a story quest gives as it starts (Fiama's lockpick and locked chest)
    [HarmonyPatch(typeof(Quest), nameof(Quest.Start))]
    internal static class OnQuestStart
    {
        [HarmonyPrefix]
        internal static void Begin(Quest __instance, out bool __state)
        {
            __state = !__instance.IsRandomQuest;
            if (__state) {
                _depth++;
            }
        }

        [HarmonyFinalizer]
        internal static void End(bool __state)
        {
            if (__state) {
                _depth--;
            }
        }
    }

    [HarmonyPatch]
    internal static class OnDramaOutcome
    {
        internal static IEnumerable<MethodBase> TargetMethods()
        {
            return typeof(DramaOutcome)
                .GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly)
                .Where(m => !m.IsSpecialName && !m.IsGenericMethod && !m.IsAbstract);
        }

        [HarmonyPrefix]
        internal static void Begin()
        {
            _depth++;
        }

        [HarmonyFinalizer]
        internal static void End()
        {
            _depth--;
        }
    }
}
