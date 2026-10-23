using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The curse, enchant level and acid coating of an item a player carries (or a companion of theirs). Acts are
///     replayed in every game with its own dice, so each game picked another item to curse or rust: the game of
///     the player is the one that counts, the others do not roll for that item and take this. The whole state is
///     sent, applying it twice changes nothing
/// </summary>
[MessagePackObject]
public class CardItemStateDelta : ElinDelta
{
    /// <summary>
    ///     Set while a state is landing, so that the patches neither skip it nor tell it back
    /// </summary>
    internal static bool Landing;

    [Key(0)]
    public required RemoteCard Card { get; init; }

    [Key(1)]
    public required int Blessed { get; init; }

    [Key(2)]
    public required int EncLv { get; init; }

    [Key(3)]
    public required bool Acidproof { get; init; }

    internal static CardItemStateDelta Create(Card card)
    {
        return new() {
            Card = card,
            Blessed = (int)card.blessedState,
            EncLv = card.encLV,
            Acidproof = card.isAcidproof,
        };
    }

    /// <summary>
    ///     The player the item belongs to, if it is on one of them or on a companion
    /// </summary>
    internal static Chara? OwnerOf(Card card)
    {
        return card is Thing && card.GetRootCard() is Chara root ? CompanionHelper.OwnerOf(root) : null;
    }

    /// <summary>
    ///     On a player of another game: its game decides, ours does not roll for it
    /// </summary>
    internal static bool IsForeign(Card card)
    {
        return NetSession.Instance.Connection is not null && OwnerOf(card) is { IsPC: false } owner && owner.IsPlayer;
    }

    internal static void Land(Card card, int blessed, int encLv, bool acidproof)
    {
        var landing = Landing;
        Landing = true;
        try {
            if ((int)card.blessedState != blessed) {
                card.SetBlessedState((BlessedState)blessed);
            }

            if (card.encLV != encLv) {
                card.SetEncLv(encLv);
            }

            card.isAcidproof = acidproof;
        } finally {
            Landing = landing;
        }

        if (card is Thing thing) {
            LayerInventory.SetDirty(thing);
        }
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Card.Find() is not Thing { isDestroyed: false } thing || !IsForeign(thing)) {
            return;
        }

        if (net is ElinNetHost host) {
            // only the player the item belongs to tells its state
            if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) || OwnerOf(thing) != sender) {
                return;
            }

            host.Delta.AddRemote(this);
        }

        Land(thing, Blessed, EncLv, Acidproof);
    }
}
