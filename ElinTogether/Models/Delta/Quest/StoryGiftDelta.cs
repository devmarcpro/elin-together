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
        Bound(thing);
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

    /// <summary>
    ///     The client's gift is kept whole (a bill, a love lunch, a chest's contents are set after it is made),
    ///     only what no dialog or wish can give is brought back within the game's maxima: currency up to
    ///     QuestRandom's 10,000,000, other stacks up to the 1000 of ActEffect.Wish, one of what does not stack,
    ///     an enchant up to what Thing.GetEnchant rolls at the game's level cap (ElementContainer, 10,000,000),
    ///     one charge on a rod of wishing (TraitRod.OnCreate)
    /// </summary>
    private void Bound(Thing thing)
    {
        var max = thing.trait is TraitCurrency ? 10_000_000 : thing.trait.CanStack ? 1000 : 1;
        if (thing.Num > max) {
            Odd(thing, "Num", thing.Num, max);
            thing.SetNum(max);
        }

        if (thing.id == "rod_wish" && thing.c_charges > 1) {
            Odd(thing, "charges", thing.c_charges, 1);
            thing.c_charges = 1;
        }

        foreach (var e in thing.elements.dict.Values) {
            if (e.source.encFactor <= 0) {
                continue;
            }

            // (mtp + rnd(mtp + 3 + 15 + sqrt(lv * encFactor / 100))) / mtp
            var cap = 20 + (int)System.Math.Sqrt(10_000_000L * e.source.encFactor / 100);
            if (System.Math.Abs(e.vBase) > cap) {
                Odd(thing, $"element {e.id}", e.vBase, cap);
                e.vBase = System.Math.Sign(e.vBase) * cap;
            }
        }

        foreach (var held in thing.things) {
            Bound(held);
        }
    }

    private void Odd(Thing thing, string what, int value, int max)
    {
        EmpLog.Warning("Story gift {ThingId} from peer {PeerIndex}: {What} {Value} brought back to {Max}",
            thing.id, OriginPeer, what, value, max);
    }
}
