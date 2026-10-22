using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A theft follows a victim that walks away by moving "the player" towards it (AI_Steal.Run, onProgress). The
///     theft of another player is played on every other game too, where "the player" is someone else: the host's
///     own character walked after the victim. The step is the thief's own
/// </summary>
[HarmonyPatch]
internal static class AIStealPatch
{
    private static Chara? _thief;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Progress_Custom), nameof(Progress_Custom.OnProgress))]
    internal static void OnProgress(Progress_Custom __instance)
    {
        _thief = NetSession.Instance.Connection is not null && __instance.parent is AI_Steal &&
                 __instance.owner is { IsRemotePlayer: true } thief
            ? thief
            : null;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Progress_Custom), nameof(Progress_Custom.OnProgress))]
    internal static void OnProgressEnd()
    {
        _thief = null;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.TryMoveTowards))]
    internal static bool OnTryMoveTowards(Chara __instance, Point p, ref Card.MoveResult __result)
    {
        if (_thief is null || !__instance.IsPC) {
            return true;
        }

        __result = _thief.TryMoveTowards(p);
        return false;
    }
}
