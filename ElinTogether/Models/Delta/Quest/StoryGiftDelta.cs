using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Client to host: a dialog gave this, create it for real
/// </summary>
[MessagePackObject]
public class StoryGiftDelta : ElinDelta
{
    [Key(0)]
    public required LZ4Bytes Data { get; init; }

    [Key(1)]
    public required Position Pos { get; init; }

    /// <summary>
    ///     The story gave it (a story quest that completes, the outcome of a dialog): the other players get their
    ///     share, see ElinNetHost.ShareStoryReward
    /// </summary>
    [Key(2)]
    public bool Story { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        // travelling alone, a player creates its own things
        if (net is not ElinNetHost host || host.IsAwayPeer(OriginPeer) || !Pos.IsInActiveMapBounds) {
            return;
        }

        var thing = Data.Decompress<Thing>();
        game.cards.AssignUIDRecursive(thing);
        CardCache.Add(thing);
        CardCache.CacheContainer(thing.things);

        using (Simulate()) {
            host.Delta.AddRemote(CardGenDelta.Create(thing));
            _zone.AddCard(thing, new Point(Pos.X, Pos.Z));
        }

        if (Story) {
            ElinNetHost.ShareStoryReward(thing, host.PlayerChara(OriginPeer));
        }

        EmpLog.Debug("Created story gift {ThingId} for peer {PeerIndex}", thing.id, OriginPeer);
    }
}
