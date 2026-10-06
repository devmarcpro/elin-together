using System;
using System.Collections;
using System.Collections.Generic;
using ElinTogether.API.SourceValidation;
using ElinTogether.Elements;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(AIAct), nameof(AIAct.Cancel))]
internal static class CharaTaskCancelEvent
{
    [HarmonyPrefix]
    internal static bool OnCancel(AIAct __instance)
    {
        if (__instance.owner is not { } owner || owner.ai.Current is not AIProgress current) {
            return true;
        }

        var prevent = false;
        var net = NetSession.Instance.Connection;
        switch (net) {
            case ElinNetHost when owner.ai is GoalRemote:
                break;
            case ElinNetClient when owner.IsPC:
                // sent as FakeTask: the host cannot relay a stop of a task it does not know, stop it here
                if (FakeTask.IsMarked(current)) {
                    return true;
                }

                // client can only cancel progress with delta
                prevent = true;
                break;
            case ElinNetClient when owner.ai is GoalRemote:
                return false;
            default:
                return true;
        }

        if (current.parent?.GetType() is not { } actType ||
            !ActMappingValidator.Default.ActToIdMapping.TryGetValue(actType, out var actId)) {
            return true;
        }

        net.Delta.AddRemote(new CharaTaskCancelDelta {
            Owner = owner,
            ActId = actId,
            Reason = net is ElinNetClient && owner.IsPC && TraitBaseSpellbookPatch.HasFailed(current)
                ? CharaTaskCancelDelta.ReadFailed
                : (byte)0,
        });

        // the stop is held back for the host's answer: when none comes the stop is made here, for this act only
        if (prevent && net is ElinNetClient && current.parent is { } act && Waiting.Add(act)) {
            EmpMod.Instance.StartCoroutine(StopIfNoAnswer(owner, act, net));
        }

        return !prevent;
    }

    private const float AnswerSeconds = 2f;

    // the acts whose stop waits for an answer
    private static readonly HashSet<AIAct> Waiting = [];

    /// <summary>
    ///     The host answers a stop by sending it back, and says nothing when it holds the stop back (the act is not
    ///     running there). After <see cref="AnswerSeconds" /> without an answer the act is stopped here. It is tied to
    ///     the act that was asked to stop: once it is over, or replaced by the next task of the player, nothing happens
    /// </summary>
    private static IEnumerator StopIfNoAnswer(Chara owner, AIAct act, ElinNetBase asked)
    {
        // no answer will come from a game that no longer keeps the map for us: not waited for
        var until = UnityEngine.Time.realtimeSinceStartup + AnswerSeconds;
        while (UnityEngine.Time.realtimeSinceStartup < until &&
               ReferenceEquals(NetSession.Instance.Connection, asked)) {
            yield return null;
        }

        Waiting.Remove(act);

        for (var ai = owner.ai?.Current; ai is not null; ai = ai.parent) {
            if (ai != act) {
                continue;
            }

            if (act.status == AIAct.Status.Running) {
                if (ReferenceEquals(NetSession.Instance.Connection, asked)) {
                    EmpLog.Warning("No answer to the stop of {ActType} after {Seconds} s, stopping it here",
                        act.GetType().Name, AnswerSeconds);
                } else {
                    EmpLog.Information("The game that kept the map is gone, the stop of {ActType} is made here",
                        act.GetType().Name);
                }

                act.Stub_Cancel();
            }

            yield break;
        }
    }

    extension(AIAct aIAct)
    {
        [HarmonyReversePatch(HarmonyReversePatchType.Snapshot)]
        internal AIAct.Status Stub_Cancel()
        {
            throw new NotImplementedException("AIAct.Cancel");
        }
    }
}