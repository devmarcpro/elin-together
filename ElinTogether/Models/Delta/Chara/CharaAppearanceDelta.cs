using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A player changed its look (mirror): parts, colours, portrait. Nothing carried it: the others never saw
///     it, and the copy of the character kept by the host brought the old look back at the next map change
///     or reconnection
/// </summary>
[MessagePackObject]
public class CharaAppearanceDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required Dictionary<string, string[]> Parts { get; init; }

    [Key(2)]
    public required string? Portrait { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Owner.Find() is not Chara { pccData: { } look } chara) {
            return;
        }

        if (net is ElinNetHost host) {
            // a player only dresses its own character
            if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) || sender != chara) {
                EmpLog.Warning("Refusing {DeltaType} on {Uid} from peer {PeerIndex}",
                    nameof(CharaAppearanceDelta), Owner.Uid, OriginPeer);
                return;
            }

            net.Delta.AddRemote(this);
        }

        // our own change coming back
        if (chara.IsPC) {
            return;
        }

        look.Set(new PCCData {
            map = Parts.ToDictionary(part => part.Key, part => part.Value.ToArray()),
        });

        if (Portrait is not null) {
            chara.c_idPortrait = Portrait;
        }

        // what LayerEditPCC.Apply does once the look is set
        PCC.Get(look).Build();
        chara.SetInt(105, IntColor.ToInt(look.GetHairColor()));
    }

    internal static CharaAppearanceDelta Create(Chara chara)
    {
        return new() {
            Owner = chara,
            Parts = chara.pccData.map.ToDictionary(part => part.Key, part => part.Value.ToArray()),
            Portrait = chara.c_idPortrait,
        };
    }
}
