using System.Collections.Generic;
using System.Reflection;
using ElinTogether.API.SourceValidation;
using ElinTogether.Elements;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal static class CharaTaskProgressEvents
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return OverrideMethodComparer
            .FindAllOverrides(typeof(AIProgress), nameof(AIProgress.OnProgressBegin));
    }

    [HarmonyPrefix]
    internal static bool OnProgressBegin(AIProgress __instance)
    {
        if (NetSession.Instance.Connection is not { } connection) {
            return true;
        }

        if (__instance.owner is not { } owner) {
            return true;
        }

        if (__instance is DelegateProgress) {
            __instance.progress = HeldProgress.Held;
            return true;
        }

        // a task sent as FakeTask has no act on the host to match: not announced, and not held for a completion that
        // would never come
        if (connection.IsClient && owner.IsPC && FakeTask.IsMarked(__instance)) {
            return true;
        }

        if (__instance.parent?.GetType() is not { } actType ||
            !ActMappingValidator.Default.ActToIdMapping.TryGetValue(actType, out var actId)) {
            return true;
        }

        // the next round of a task that loops (chopping logs, drawing or pouring water) is decided inside the replay
        // of the round that ended, before what that round changed has landed here (the last log used up): the host,
        // whose task is over, was told a round began and cancelled it. The round begins on the next tick instead,
        // after the task has checked again that it can go on (AIProgress.Run: progress 0 calls this again)
        if (connection.IsClient && owner.IsPC && CharaProgressCompleteDelta.IsReplaying &&
            __instance.parent is TaskPoint) {
            __instance.progress = -1;
            return false;
        }

        if (connection.IsClient) {
            // we can only complete remote progress with delta
            __instance.progress = HeldProgress.Held;

            // never for good: let go when that game stops keeping the map, or does not end it
            if (owner.IsPC) {
                PendingOnHost.Watch(__instance, connection);
            }
        }

        // for host, run it only when remote players run it
        if (owner.ai is GoalRemote) {
            __instance.progress = HeldProgress.Held;
            return true;
        }

        connection.Delta.AddRemote(new CharaProgressBeginDelta {
            Owner = owner,
            Pos = owner.pos,
            MaxProgress = __instance.MaxProgress,
            ActId = actId,
        });

        return true;
    }
}