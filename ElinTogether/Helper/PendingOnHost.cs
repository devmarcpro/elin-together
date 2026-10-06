using System;
using System.Collections;
using ElinTogether.Elements;
using ElinTogether.Net;
using ElinTogether.Patches;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     What this game's player waits for from the game that keeps the map: a progress held until that game ends
///     it (see CharaTaskProgressEvents). Many of them cannot be stopped by hand (a reading: AIAct.CanManualCancel),
///     so one that is never answered locks the player for good. It is let go the moment that game stops keeping
///     the map for us (it left and handed us the map, we left, the link changed), and after a while without an end
/// </summary>
internal static class PendingOnHost
{
    // the keeper runs the same progress at the same pace: it ends in about MaxProgress turns of the player
    private const int OverdueFactor = 3;
    private const int OverdueTurns = 20;
    private const float OverdueSeconds = 6f;

    // when the turns do not pass here: no game speed is slower than a turn a second
    private const float SecondsPerTurn = 1f;

    internal static void Watch(AIProgress progress, ElinNetBase keeper)
    {
        EmpMod.Instance.StartCoroutine(WatchHeld(progress, keeper));
    }

    private static bool IsHeld(AIProgress progress)
    {
        return EClass.core.IsGameStarted && progress.progress < 0 && progress.status == AIAct.Status.Running &&
               EClass.pc is { } pc && pc.ai?.Current == progress;
    }

    // HeldProgress.Held is -int.MaxValue and a held progress still counts its turns
    private static int TurnsHeld(AIProgress progress)
    {
        return progress.progress + int.MaxValue;
    }

    private static IEnumerator WatchHeld(AIProgress progress, ElinNetBase keeper)
    {
        var since = Time.realtimeSinceStartup;

        // asked from inside the first tick of the progress: watched from the next frame, once it is in place
        yield return null;

        while (IsHeld(progress)) {
            if (!ReferenceEquals(NetSession.Instance.Connection, keeper)) {
                Release(progress);
                yield break;
            }

            var seconds = Time.realtimeSinceStartup - since;
            if (seconds > OverdueSeconds &&
                (TurnsHeld(progress) > (long)progress.MaxProgress * OverdueFactor + OverdueTurns ||
                 seconds > OverdueSeconds + progress.MaxProgress * SecondsPerTurn)) {
                EmpLog.Warning("No end to {ActType} after {Turns} turns ({MaxProgress} needed) and {Seconds:F0} s, stopping it",
                    progress.parent?.GetType().Name ?? progress.GetType().Name, TurnsHeld(progress),
                    progress.MaxProgress, seconds);

                // the player's own stop: told to the keeper, made here when it does not answer (CharaTaskCancelEvent)
                EClass.pc.Say("cancel_act_pc", EClass.pc);
                EClass.pc.ai.Cancel();
                yield break;
            }

            yield return null;
        }
    }

    private static void Release(AIProgress progress)
    {
        var pc = EClass.pc;
        var name = progress.parent?.GetType().Name ?? progress.GetType().Name;

        // this game keeps the map now (alone, or for its visitors): the keeper did not end the progress, or its
        // end would have come first, so it ends here once, as alone, counting the turns already waited.
        // Not a craft: its product is made by the keeper (RemoteCraft), here it would end with nothing
        if (NetSession.Instance.Connection is not ElinNetClient && progress is not HeldProgress) {
            progress.progress = Math.Max(1, TurnsHeld(progress));
            EmpLog.Information("The game that kept the map is gone, {ActType} goes on here at {Turns}/{MaxProgress}",
                name, progress.progress, progress.MaxProgress);
            return;
        }

        // another game keeps the map and knows nothing of this task: stopped as by hand, nothing is used up
        EmpLog.Information("The game that kept the map is gone, {ActType} is stopped", name);
        pc.Say("cancel_act_pc", pc);
        pc.ai.Stub_Cancel();
    }
}
