using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class QuestChangePhaseDelta : ElinDelta
{
    [Key(0)]
    public required int Uid { get; init; }

    [Key(1)]
    public required int Modifier { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            // progress made by a player travelling alone, in its copy of the world
            if (host.IsAwayPeer(OriginPeer) && game.quests.list.Find(q => q.uid == Uid) is { } advanced) {
                advanced.ChangePhase(Modifier);
                // not back to the player who made it: what a phase triggers already happened there
                host.SendDeltaToAllExcept(OriginPeer, this);
            }

            return;
        }

        var quest = game.quests.list.Find(q => q.uid == Uid);
        quest?.ChangePhase(Modifier);
    }
}