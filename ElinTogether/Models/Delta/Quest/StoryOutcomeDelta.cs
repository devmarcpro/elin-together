using System;
using ElinTogether.Net;
using ElinTogether.Patches;
using HarmonyLib;
using MessagePack;
using UnityEngine;

namespace ElinTogether.Models;

/// <summary>
///     To the host: a dialog triggered this in the world (a fight set up, someone moving in, land claimed)
/// </summary>
[MessagePackObject]
public class StoryOutcomeDelta : ElinDelta
{
    [Key(0)]
    public required string Method { get; init; }

    /// <summary>
    ///     Who the player was talking to
    /// </summary>
    [Key(1)]
    public required RemoteCard? Target { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host) {
            return;
        }

        var away = host.IsAwayPeer(OriginPeer);
        if (!StoryOutcomePatch.RunsOnHost(Method, away)) {
            EmpLog.Warning("Refusing story outcome {Method} from peer {PeerIndex}", Method, OriginPeer);
            return;
        }

        var target = FindTarget();

        // travelling alone, the player ran it in its copy of the world and got what it gives there
        using (away ? QuestRewardPatch.GiveNothing() : QuestRewardPatch.GiveTo(host, OriginPeer)) {
            using (Simulate()) {
                try {
                    Run(target, away);
                } catch (Exception ex) {
                    EmpLog.Warning(ex, "Story outcome {Method} failed", Method);
                }
            }
        }

        EmpLog.Debug("Ran story outcome {Method} for peer {PeerIndex}", Method, OriginPeer);
    }

    private void Run(Chara? target, bool away)
    {
        switch (Method) {
            case StoryOutcomePatch.Recruit:
                if (target is not null && EClass.Branch is { } branch) {
                    target.SetBool(18, true);
                    branch.Recruit(target);
                }

                return;
            case nameof(DramaOutcome.QuestExploration_AfterCrystal) when away:
                // the crystal room is on the player's map, only who goes home is about the world
                if (game.cards.globalCharas.Find("fiama") is { } fiama) {
                    fiama.MoveHome(game.StartZone);
                    fiama.RemoveEditorTag(EditorTag.AINoMove);
                }

                return;
        }

        // the game's own code, with the dialog it expects around it
        var stage = new GameObject("emp_story_outcome");
        stage.SetActive(false);
        try {
            var manager = stage.AddComponent<DramaManager>();
            manager.tg = target is null ? new Person() : new Person(target);

            var outcome = stage.AddComponent<DramaOutcome>();
            outcome.manager = manager;

            AccessTools.Method(typeof(DramaOutcome), Method).Invoke(outcome, null);
        } finally {
            UnityEngine.Object.Destroy(stage);
        }
    }

    /// <summary>
    ///     Who the player was talking to. Not always a card the host handed out: someone waiting to be hired
    ///     only exists in the list of the base
    /// </summary>
    private Chara? FindTarget()
    {
        if (Target is null) {
            return null;
        }

        return Target.Find() as Chara ??
               game.cards.globalCharas.Find(Target.Uid) ??
               _map.charas.Find(c => c.uid == Target.Uid) ??
               EClass.Branch?.listRecruit.Find(hire => hire.chara?.uid == Target.Uid)?.chara;
    }
}
