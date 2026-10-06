using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     How a piece of furniture sits once the build mode moved it: its height, its free position, its roof flag.
///     The move itself is told as cards (ZoneAddCardDelta, CardPlacedDelta), these fields are written by hand
///     after it (TaskMoveInstalled.OnProgressComplete, AM_MoveInstalled.OnProcessTiles) and nothing else carries them
/// </summary>
[MessagePackObject]
public class CardPoseDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Card { get; init; }

    [Key(1)]
    public required int Altitude { get; init; }

    [Key(2)]
    public required bool FreePos { get; init; }

    [Key(3)]
    public required float Fx { get; init; }

    [Key(4)]
    public required float Fy { get; init; }

    [Key(5)]
    public required bool IgnoreStackHeight { get; init; }

    [Key(6)]
    public required bool IsRoofItem { get; init; }

    internal static CardPoseDelta Create(Card card)
    {
        return new() {
            Card = card,
            Altitude = card.altitude,
            FreePos = card.freePos,
            Fx = card.fx,
            Fy = card.fy,
            IgnoreStackHeight = card.ignoreStackHeight,
            IsRoofItem = card.isRoofItem,
        };
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Card.Find() is not { isDestroyed: false, ExistsOnMap: true, IsPC: false } card) {
            return;
        }

        if (net.IsHost) {
            net.Delta.AddRemote(this);
        }

        card.altitude = Altitude;
        card.freePos = FreePos;
        card.fx = Fx;
        card.fy = Fy;
        card.ignoreStackHeight = IgnoreStackHeight;
        card.isRoofItem = IsRoofItem;

        if (card.renderer is { hasActor: true }) {
            card.renderer.RefreshSprite();
        }
    }
}
