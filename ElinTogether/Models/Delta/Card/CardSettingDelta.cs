using System.Linq;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     What a player sets on an object of the map from its menu: the note written on it, the sale tag, who sleeps
///     in a bed and what kind of bed it is, the name of a teleporter. Each game changed its own copy only: a guest's settings never reached
///     the host, who runs the residents and keeps the save, and the host's never reached the guests <br />
///     Closed list. The whole state is sent, not the click: applying it twice changes nothing
/// </summary>
[MessagePackObject]
public class CardSettingDelta : ElinDelta
{
    public const byte Note = 0;
    public const byte Sale = 1;
    public const byte Bed = 2;
    public const byte Teleporter = 3;

    [Key(0)]
    public required RemoteCard Card { get; init; }

    [Key(1)]
    public required byte Kind { get; init; }

    [Key(2)]
    public string? Text { get; init; }

    /// <summary>
    ///     On sale or not; the kind of bed
    /// </summary>
    [Key(3)]
    public int Value { get; init; }

    /// <summary>
    ///     Those who hold the bed
    /// </summary>
    [Key(4)]
    public int[]? Holders { get; init; }

    internal static CardSettingDelta Create(Card card, byte kind)
    {
        return new() {
            Card = card,
            Kind = kind,
            Text = kind switch {
                Note => card.c_note,
                Teleporter => (card.trait as TraitTeleporter)?.id,
                _ => null,
            },
            Value = kind switch {
                Sale => card.isSale ? 1 : 0,
                Bed => (int)card.c_bedType,
                Teleporter => EClass._zone.uid,
                _ => 0,
            },
            Holders = kind == Bed ? card.c_charaList?.list.ToArray() : null,
        };
    }

    protected override void OnApply(ElinNetBase net)
    {
        // an object of the map, or one the sender carries; a bed setting only on a bed
        if (Card.Find() is not Thing { isDestroyed: false } thing || (Kind == Bed && thing.trait is not TraitBed) ||
            (Kind == Teleporter && thing.trait is not TraitTeleporter) || Kind > Teleporter) {
            return;
        }

        if (net is ElinNetHost host) {
            if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) ||
                (thing.GetRootCard() is Chara holder && holder != sender)) {
                return;
            }

            host.Delta.AddRemote(this);
        }

        switch (Kind) {
            case Note:
                thing.c_note = Text;
                break;
            case Sale:
                thing.SetSale(Value != 0);
                break;
            case Bed:
                thing.c_bedType = (BedType)Value;
                thing.c_charaList = Holders is { Length: > 0 } ? new CharaList { list = [..Holders] } : null;
                break;
            case Teleporter:
                // the name of a teleporter, and the register of each game that links the ones of the same name
                var teleporter = (TraitTeleporter)thing.trait;
                teleporter.id = Text;
                game.teleports.SetID(teleporter, Value);
                break;
        }
    }
}
