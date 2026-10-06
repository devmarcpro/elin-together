using ElinTogether.Elements;
using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaTaskDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required TaskArgsBase? TaskArgs { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Owner.Find() is not Chara { IsPC: false } chara) {
            return;
        }

        var act = TaskArgs?.CreateSubAct();

        if (chara.isDead) {
            if (net.IsHost && act is not null) {
                TaskCache.RequestCancel(net, Owner, act);
            }

            return;
        }

        if (net.IsHost && TaskCache.GetRequiredPos(act) is { } pos &&
            TaskCache.IsPosTaken(pos, chara)) {
            EmpLog.Debug("Task {ActType} on {@Pos} refused for chara {Uid}, pos already taken",
                act!.GetType().Name, pos, Owner.Uid);
            TaskCache.RequestCancel(net, Owner, act!);
            return;
        }

        // relay to clients
        if (net.IsHost) {
            net.Delta.AddRemote(this);
            ActionModeCombat.OnRemoteTaskReport(chara.uid, act is not null);
        }

        if (chara.ai is not GoalRemote) {
            // assume client GoalRemote is a light year away and drop it may desync the goals
            if (!net.IsClient) {
                return;
            }

            chara.SetAI(GoalRemote.Default);
        }

        if (chara.ai is not GoalRemote remote) {
            return;
        }

        if (remote.owner is null) {
            remote.SetOwner(chara);
        }

        // the tool the player holds is not put in this copy's hand while a task runs (CharaSwitchHeldDelta), and a
        // task this game does not stand for (walking: FakeTask, a NoGoal) "runs" until the next one: a tool changed
        // on the way stayed the old one here, and the task that needs it ended as it started (Card.Tool is chara.held)
        if (act is not null &&
            chara.NetProfile.RemoteMainHand.TryGetTarget(out var mainHand) &&
            chara.NetProfile.RemoteOffHand.TryGetTarget(out var offHand) &&
            mainHand == offHand && chara.held != mainHand && mainHand.GetRootCard() == chara) {
            chara.HoldCard(mainHand);
        }

        // now assign new task or reset
        using (Simulate(net.IsHost && RemoteCraft.IsHostRun(act))) {
            remote.InsertAction(act);
        }

        if (net.IsHost && act is not null && act.status != AIAct.Status.Running) {
            // what a later "has no matching act" is about
            EmpLog.Debug("Task {ActType} of chara {Uid} was over as soon as started here, tool {ToolUid}",
                act.GetType().Name, Owner.Uid, chara.held?.uid ?? 0);
        }
    }
}