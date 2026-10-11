using ElinTogether.Helper;
using System;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CardIdentifyDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Card { get; init; }

    [Key(1)]
    public required int State { get; init; }

    [Key(2)]
    public required byte Source { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Card.Find() is not Thing { isDestroyed: false } thing) {
            return;
        }

        if (net is ElinNetHost host) {
            // client wants to identify thingy
            // its own things, or the one it just sold: a shop identifies what it buys, in the seller's game, once
            // the thing is already the merchant's (never another player's or a companion's)
            // (in between, the thing sold is held by nobody for a moment)
            if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var owner) ||
                (thing.GetRootCard() is Chara root && root != owner &&
                 (root.IsPlayer || CompanionHelper.OwnerOf(root) is not null))) {
                EmpLog.Warning("Refusing identify of {Uid} from peer {PeerIndex}",
                    thing.uid, OriginPeer);
                return;
            }

            if (!Enum.IsDefined(typeof(IDTSource), (int)Source)) {
                return;
            }

            using var _ = Simulate();
            thing.Identify(false, (IDTSource)Source);
            return;
        }

        // host says ok
        if (thing.c_IDTState == State) {
            return;
        }

        thing.c_IDTState = State;
        LayerInventory.SetDirty(thing);
    }
}