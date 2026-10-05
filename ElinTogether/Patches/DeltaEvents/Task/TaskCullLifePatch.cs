using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The sickle hands its ecopo to "the player" whoever reaps: on the host, where the task of another player
///     runs, that was the host. The host runs that task with the reaper standing in for "the player"
/// </summary>
[HarmonyPatch(typeof(TaskCullLife), nameof(TaskCullLife.Run), MethodType.Enumerator)]
internal static class TaskCullLifePatch
{
    [HarmonyPrefix]
    internal static void OnRun(object __instance, out ScopeExit? __state)
    {
        __state = null;
        if (NetSession.Instance.Connection is not ElinNetHost ||
            Traverse.Create(__instance).Field<TaskCullLife>("<>4__this").Value?.owner is not { IsRemotePlayer: true } reaper) {
            return;
        }

        // the task of another player runs while its tick is applied, when nothing is sent: what it picks must be
        var standIn = RemoteCraft.AsCrafter(reaper);
        var sent = ElinDelta.Simulate();
        __state = new() {
            OnExit = () => {
                sent.Dispose();
                standIn.Dispose();
            },
        };
    }

    [HarmonyFinalizer]
    internal static void OnRunEnd(ScopeExit? __state)
    {
        __state?.Dispose();
    }
}
