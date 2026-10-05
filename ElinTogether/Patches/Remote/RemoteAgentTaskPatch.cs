using System.Collections.Generic;
using System.Reflection;
using ElinTogether.Models;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Mining, digging and cutting from the build mode, in a game that does not keep the map: the task of the
///     agent is sent to the game that does, see <see cref="AgentTaskDelta" />
/// </summary>
[HarmonyPatch]
internal static class RemoteAgentTaskPatch
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return [
            AccessTools.Method(typeof(TaskMine), nameof(TaskMine.OnProgressComplete)),
            AccessTools.Method(typeof(TaskDig), nameof(TaskDig.OnProgressComplete)),
            AccessTools.Method(typeof(TaskCut), nameof(TaskCut.OnProgressComplete)),
        ];
    }

    [HarmonyPrefix]
    internal static bool OnAgentDone(TaskDesignation __instance)
    {
        return !AgentTaskDelta.TrySend(__instance);
    }
}
