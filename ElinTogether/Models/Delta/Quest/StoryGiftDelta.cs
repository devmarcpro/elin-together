using System.Linq;
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

        Thing thing;
        using (Simulate()) {
            // the host makes the gift itself (CardGenEvent tells everyone): of what the client sent, only what names it
            if (Rebuild(Data.Decompress<Thing>()) is not { } made) {
                EmpLog.Warning("Refusing story gift from peer {PeerIndex}: not a thing", OriginPeer);
                return;
            }

            thing = made;
            CardCache.Add(thing);
            _zone.AddCard(thing, new Point(Pos.X, Pos.Z));
        }

        if (Story) {
            ElinNetHost.ShareStoryReward(thing, host.PlayerChara(OriginPeer));
        }

        EmpLog.Debug("Created story gift {ThingId} for peer {PeerIndex}", thing.id, OriginPeer);
    }

    // the most a wish gives (ActEffect.Wish at power 1000) or a dialog gives (20 stones)
    private static int MaxNum(Thing thing)
    {
        return thing.id switch {
            "money" => 165000,
            "plat" or "money2" => 114,
            "medal" => 31,
            _ => thing.trait.CanStack ? 20 : 1,
        };
    }

    /// <summary>
    ///     What the game's own code would make of that id: quality, material and enchants rolled here (a wished
    ///     weapon or armor is legendary, as in ActEffect.Wish); the client only names it (what it refers to: the
    ///     recipe, the spell, the figure) and its amount, capped
    /// </summary>
    private static Thing? Rebuild(Thing sent)
    {
        if (!sources.things.map.TryGetValue(sent.id, out var row)) {
            return null;
        }

        var category = sources.categories.map[row.category];
        if (sent.rarity >= Rarity.Legendary &&
            (category.IsChildOf("weapon") || category.IsChildOf("armor") || category.IsChildOf("ranged"))) {
            CardBlueprint.SetRarity(Rarity.Legendary);
        }

        var thing = ThingGen.Create(sent.id, -1, UnityEngine.Mathf.Clamp(sent.LV, 1, 100));

        // a raw material is its material (ThingGen.CreateRawMaterial)
        if (sources.materials.map.TryGetValue(sent.idMaterial, out var material) && material.thing == sent.id) {
            thing.ChangeMaterial(sent.idMaterial);
        }

        thing.idSkin = sent.idSkin;
        thing.c_idRefCard = sent.c_idRefCard;
        thing.c_altName = sent.c_altName;
        thing.SetStr(53, sent.GetStr(53));
        thing.c_IDTState = sent.c_IDTState;
        thing.noSell = sent.noSell;
        if (thing.trait is TraitSpellbook or TraitScrollRandom && sources.elements.map.ContainsKey(sent.refVal)) {
            TraitSpellbook.Create(thing, sent.refVal);
        } else {
            thing.refVal = sent.refVal;
        }

        // fewer charges only: a wished rod of wishing has none
        if (sent.c_charges < thing.c_charges) {
            thing.c_charges = sent.c_charges;
        }

        // a starter gift sets a few small enchants on a thing that cannot be sold (DramaOutcome.fiama_starter_gift)
        if (sent.noSell) {
            foreach (var element in sent.elements.dict.Values.Where(e => e.vBase is > 0 and <= 10 && !thing.elements.Has(e.id)).Take(3)) {
                thing.elements.SetBase(element.id, element.vBase);
            }
        }

        thing.SetNum(System.Math.Clamp(sent.Num, 1, MaxNum(thing)));
        return thing;
    }
}
