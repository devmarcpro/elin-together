using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Client -> the game that keeps the map: the "Reroll Quests" button of the quest board. That game draws the
///     offers again, as its own button does, and pays the influence in its copy as the client did in its own;
///     the new offers and the ones gone reach every game (<see cref="QuestCreateDelta" />, <see cref="QuestOffersDelta" />)
/// </summary>
[MessagePackObject]
public class QuestRerollDelta : ElinDelta
{
    // LayerQuestBoard, GetCost
    private const int Cost = 1;

    [Key(0)]
    public required int ZoneUid { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost || _zone is not { } zone || zone.uid != ZoneUid || zone.influence < Cost) {
            return;
        }

        zone.influence -= Cost;

        // as this game's own gesture, so that what it draws is told like any draw made here
        using var _ = Simulate();
        zone.UpdateQuests(true);
    }
}
