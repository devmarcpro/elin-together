using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class QuestStartDelta : ElinDelta
{
    [Key(0)]
    public required int Uid { get; init; }

    [Key(1)]
    public required RemoteCard? Owner { get; init; }

    [Key(2)]
    public required bool AssignQuest { get; init; }

    [Key(3)]
    public required LZ4Bytes Data { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            if (game.quests.list.Exists(q => q.uid == Uid)) {
                return;
            }

            if (!host.IsAwayPeer(OriginPeer)) {
                StartForPlayer(host);
                return;
            }

            // accepted by a player travelling alone, in its copy of the world: the quest log is everyone's

            var accepted = Data.Decompress<Quest>();
            game.quests.globalList.RemoveAll(q => q.uid == Uid);
            game.quests.list.Insert(0, accepted);

            accepted.UpdateJournal();
            if (player.questTracker) {
                WidgetQuestTracker.Show();
            }

            // not back to the player who accepted it: its copy is the live one
            host.SendDeltaToAllExcept(OriginPeer, this);
            return;
        }

        var quest = Data.Decompress<Quest>();

        game.quests.globalList.RemoveAll(q => q.uid == Uid);
        // the copy a dialog started here, before the host gave the quest its number
        game.quests.list.RemoveAll(q => q.uid < 0 && q.id == quest.id);
        SharedQuests.HostAnswered(quest.id);

        var i = game.quests.list.FindIndex(q => q.uid == Uid);
        if (i >= 0) {
            game.quests.list[i] = quest;
        } else {
            game.quests.list.Insert(0, quest);
        }

        if (Owner?.Find() is Chara owner) {
            quest.SetClient(owner, AssignQuest);
        }

        quest.UpdateJournal();
        if (player.questTracker) {
            WidgetQuestTracker.Show();
        }
    }

    /// <summary>
    ///     Started by a player on this map, a dialog mostly: the quest is everyone's, what it gives lands at
    ///     that player's feet
    /// </summary>
    private void StartForPlayer(ElinNetHost host)
    {
        var quest = game.quests.globalList.Find(q => q.uid == Uid);
        if (quest is null && Owner?.Find() is Chara { quest: { } offered } && offered.uid == Uid) {
            quest = offered;
        }

        if (quest is null) {
            if (Uid >= 0) {
                EmpLog.Warning("Rejecting quest start, unresolved quest {QuestUid}", Uid);
                return;
            }

            // created by the dialog on the player's side, it gets its number here
            quest = Data.Decompress<Quest>();
            if (game.quests.list.Exists(q => q.id == quest.id)) {
                return;
            }

            quest.uid = game.quests.uid++;
            if (Owner?.Find() is Chara owner) {
                quest.SetClient(owner, AssignQuest);
            }
        }

        if (quest.UseInstanceZone) {
            EmpLog.Warning("Rejecting quest start, instance zone {QuestUid} {QuestId}", Uid, quest.id);
            return;
        }

        game.quests.globalList.Remove(quest);

        using (QuestRewardPatch.GiveTo(host, OriginPeer)) {
            using (Simulate()) {
                game.quests.Start(quest);
            }
        }

        EmpLog.Debug("Started quest {QuestUid} {QuestId} for peer {PeerIndex}", quest.uid, quest.id, OriginPeer);
    }
}
