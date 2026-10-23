using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CardChargeDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Card { get; init; }

    [Key(1)]
    public required int Charges { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Card.Find() is not { isDestroyed: false } card) {
            return;
        }

        if (net is ElinNetHost host) {
            // from a guest: only things in its own bag, then on to the others
            if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var owner) || card.GetRootCard() != owner) {
                EmpLog.Warning("Refusing {DeltaType} on {Uid} from peer {PeerIndex}",
                    nameof(CardChargeDelta), card.uid, OriginPeer);
                return;
            }

            host.Delta.AddRemote(this);
        }

        card.c_charges = Charges;
        if (card is Thing thing) {
            LayerInventory.SetDirty(thing);
        }
    }
}