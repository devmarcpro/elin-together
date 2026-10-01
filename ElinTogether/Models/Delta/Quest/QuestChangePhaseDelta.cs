using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class QuestChangePhaseDelta : ElinDelta
{
    [Key(0)]
    public required int Uid { get; init; }

    [Key(1)]
    public required int Modifier { get; init; }

    /// <summary>
    ///     Tells which quest it is while a quest started by a dialog on a client has no number from the host yet
    /// </summary>
    [Key(2)]
    public string? Id { get; init; }

    /// <summary>
    ///     The phase the sender was moving on from, -1 when it does not matter
    /// </summary>
    [Key(3)]
    public int From { get; set; } = -1;

    protected override void OnApply(ElinNetBase net)
    {
        var quest = SharedQuests.Find(Uid, Id);
        if (quest is null) {
            return;
        }

        // already there: what the phase triggers is not to happen twice
        if (quest.phase == Modifier) {
            return;
        }

        if (net is not ElinNetHost host) {
            quest.ChangePhase(Modifier);
            return;
        }

        if (host.IsAwayPeer(OriginPeer)) {
            // progress made by a player travelling alone, in its copy of the world: what the phase gives
            // was given there
            using (QuestRewardPatch.GiveNothing()) {
                quest.ChangePhase(Modifier);
            }

            // not back to the player who made it: what a phase triggers already happened there
            host.SendDeltaToAllExcept(OriginPeer, new QuestChangePhaseDelta {
                Uid = quest.uid,
                Modifier = Modifier,
            });
            return;
        }

        if (From >= 0 && quest.phase != From) {
            // someone else moved the quest on in the meantime
            EmpLog.Debug("Ignoring stale quest phase {QuestId} {From}->{Phase}, at {Current}", quest.id, From, Modifier, quest.phase);
            host.SendDeltaTo(OriginPeer, new QuestChangePhaseDelta {
                Uid = quest.uid,
                Modifier = quest.phase,
            });
            return;
        }

        // progress made by a player on this map: what the phase triggers happens here, for everyone
        using (QuestRewardPatch.GiveTo(host, OriginPeer)) {
            using (Simulate()) {
                quest.ChangePhase(Modifier);
            }
        }
    }
}
