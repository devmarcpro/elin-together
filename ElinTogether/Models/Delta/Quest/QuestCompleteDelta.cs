using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class QuestCompleteDelta : ElinDelta
{
    [Key(1)]
    public required int Uid { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        var quest = game.quests.list.Find(q => q.uid == Uid) ??
                    game.quests.globalList.Find(q => q.uid == Uid);
        if (quest is null || quest.isComplete) {
            return;
        }

        if (net is ElinNetHost host) {
            if (host.IsAwayPeer(OriginPeer)) {
                // completed by a player travelling alone, in its copy of the world: it got the rewards there,
                // the quest log, fame and karma are the world's
                QuestCompleteEvent.CompleteQuietly(quest, true);
                host.SendDeltaToAllExcept(OriginPeer, this);
                return;
            }

            // the rewards drop at the feet of the player who completed it, not the host's
            QuestRewardPatch.Receiver = host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var receiver) ? receiver : null;
            try {
                using (Simulate()) {
                    quest.Complete();
                }
            } finally {
                QuestRewardPatch.Receiver = null;
            }

            return;
        }

        // not Quest.Complete: an away client reads as host there and would drop the rewards again
        QuestCompleteEvent.CompleteQuietly(quest, false);
    }
}
