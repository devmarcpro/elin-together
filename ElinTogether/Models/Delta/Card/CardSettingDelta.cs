using ElinTogether.Patches;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     What a player sets on an object of the map from its menu: the note written on it, the sale tag, who sleeps
///     in a bed and what kind of bed it is, the name of a teleporter. Each game changed its own copy only: a guest's settings never reached
///     the host, who runs the residents and keeps the save, and the host's never reached the guests <br />
///     <see cref="Fields" /> is what the tools of a held item change on an object (wrench, eco mark, brush, hammer), told by
///     the host only <br />
///     Closed list. The whole state is sent, not the click: applying it twice changes nothing
/// </summary>
[MessagePackObject]
public class CardSettingDelta : ElinDelta
{
    public const byte Note = 0;
    public const byte Sale = 1;
    public const byte Bed = 2;
    public const byte Teleporter = 3;
    public const byte Fields = 4;

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

    /// <summary>
    ///     The fields of the object, in the order of <see cref="FieldsOf" />
    /// </summary>
    [Key(5)]
    public int[]? Numbers { get; init; }

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
            Numbers = kind == Fields ? FieldsOf(card) : null,
        };
    }

    internal static int[] FieldsOf(Card c)
    {
        // a magic chest makes its (empty) upgrade when it is read, as the game does
        var up = c.trait is TraitMagicChest ? c.c_containerUpgrade : null;
        return [
            c.isWeightChanged ? c.c_weight : -1, // 0 eco mark
            c.elements.Base(652), // 1 eco mark
            c.isDyed ? c.c_dyeMat : 0, // 2 brush
            c.encLV, // 3 hammer
            c.c_containerSize, // 4 wrench: bed, chest
            up?.cap ?? 0, // 5 wrench: magic chest
            up?.cool ?? 0, // 6
            c.elements.Base(405), // 7 wrench: fridge
        ];
    }

    internal static List<(Thing Thing, int[] Fields)> Snapshot(Point pos)
    {
        return pos.Things.Where(t => t.IsInstalled).Select(t => (t, FieldsOf(t))).ToList();
    }

    /// <summary>
    ///     After the tool: tell the others about the objects of the tile that it changed
    /// </summary>
    internal static void TellChanged(List<(Thing Thing, int[] Fields)> before)
    {
        foreach (var (thing, old) in before) {
            if (!thing.isDestroyed && !FieldsOf(thing).SequenceEqual(old)) {
                CardSettingEvent.Tell(thing, Fields);
            }
        }
    }

    protected override void OnApply(ElinNetBase net)
    {
        // an object of the map, or one the sender carries; a bed setting only on a bed
        if (Card.Find() is not Thing { isDestroyed: false } thing || (Kind == Bed && thing.trait is not TraitBed) ||
            (Kind == Teleporter && thing.trait is not TraitTeleporter) || Kind > Fields) {
            return;
        }

        if (net is ElinNetHost host) {
            // the fields are the host's to tell
            if (Kind == Fields || !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) ||
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
            case Fields when Numbers is { Length: 8 } n:
                if (n[0] >= 0) {
                    thing.ChangeWeight(n[0]);
                }

                if (n[1] > 0) {
                    thing.elements.SetBase(652, n[1]);
                }

                thing.Dye(sources.materials.map.TryGetValue(n[2]));
                if (thing.encLV != n[3]) {
                    thing.SetEncLv(n[3]);
                }

                if (thing.trait is TraitBed) {
                    // a counter for a bed (TraitWrench), not width and height
                    thing.c_containerSize = n[4];
                } else if (thing.c_containerSize != n[4]) {
                    thing.things.SetSize(n[4] / 100, n[4] % 100);
                }

                if (thing.trait is TraitMagicChest) {
                    var up = thing.c_containerUpgrade;
                    (up.cap, up.cool) = (n[5], n[6]);
                }

                if (n[7] > 0) {
                    thing.elements.SetBase(405, n[7]);
                }

                break;
        }
    }
}
