using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A player changed a look (mirror for its own, the list of the base for a resident or a companion): parts, colours, portrait. Nothing carried it: the others never saw
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
        if (Owner.Find() is not Chara chara) {
            return;
        }

        if (net is ElinNetHost host) {
            // a player dresses its own character, its companions and the residents, not another player's
            if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) ||
                (CompanionHelper.OwnerOf(chara) is { } owner ? owner != sender : !chara.IsPCFaction)) {
                EmpLog.Warning("Refusing {DeltaType} on {Uid} from peer {PeerIndex}",
                    nameof(CharaAppearanceDelta), Owner.Uid, OriginPeer);
                return;
            }

            // a resident of the base, when only the host manages it: the sender gets the look back
            // (none here: the sender keeps its own until the next copy of the map, not fixed)
            if (NetSession.Instance.Rules.HostManagesBase && !host.IsZoneSession && CompanionHelper.OwnerOf(chara) is null) {
                if (chara.pccData is not null) {
                    host.SendDeltaTo(OriginPeer, Create(chara));
                }

                return;
            }

            net.Delta.AddRemote(this);
        }

        // our own change coming back
        if (chara.IsPC) {
            return;
        }

        // a resident given a full look here for the first time ("toggle PCC" of the list of the base)
        var fresh = chara.pccData is null;
        var look = chara.pccData ??= PCCData.Create(chara.IDPCCBodySet);
        look.Set(new PCCData {
            map = Parts.ToDictionary(part => part.Key, part => part.Value.ToArray()),
        });

        if (Portrait is not null) {
            chara.c_idPortrait = Portrait;
        }

        // what LayerEditPCC.Apply does once the look is set
        PCC.Get(look).Build();
        chara.SetInt(105, IntColor.ToInt(look.GetHairColor()));
        if (fresh && chara.ExistsOnMap) {
            chara._CreateRenderer();
        }
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
