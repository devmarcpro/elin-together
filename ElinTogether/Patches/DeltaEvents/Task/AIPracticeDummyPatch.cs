using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The practice of another player, as this game keeps it: it only stands for the task (its progress, its
///     cancel). The blows come from the game of the one who practises, replayed one by one, and the game's own
///     progress throws as "the player": here it would strike a second time, or throw for the wrong character
/// </summary>
[HarmonyPatch(typeof(AI_PracticeDummy), nameof(AI_PracticeDummy.CreateProgress))]
internal static class AIPracticeDummyPatch
{
    [HarmonyPostfix]
    internal static void OnCreateProgress(AI_PracticeDummy __instance, AIProgress __result)
    {
        if (NetSession.Instance.Connection is not null && __instance.owner is { IsPC: false } &&
            __result is Progress_Custom progress) {
            progress.onProgress = null;
        }
    }
}
