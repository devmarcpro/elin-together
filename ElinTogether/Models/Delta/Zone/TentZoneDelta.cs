using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A wrench upgrades the inside of a tent (TraitWrench.Upgrade: electricity, soil, sea bed). That is the zone of
///     the tent, not a card: nothing told it to the other games, and the game that did it alone (a guest on a map
///     of its own) lost it when the world's copy came back. "The electricity works, then stops after a while"
///     (player report, 2026-10-14). Told as values, not steps: a game that hears it twice keeps the same
/// </summary>
[MessagePackObject]
public class TentZoneDelta : ElinDelta
{
    internal static readonly int[] Upgrades = [3606, 2201, 2200];

    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     The base value of each of <see cref="Upgrades" />, in that order
    /// </summary>
    [Key(1)]
    public required int[] Values { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            host.SendDeltaToAllExcept(OriginPeer, this);
        }

        if (game?.spatials.Find(ZoneUid) is not Zone zone) {
            EmpLog.Warning("Tent zone {ZoneUid} is unknown here, its upgrade is not taken", ZoneUid);
            return;
        }

        for (var i = 0; i < Upgrades.Length && i < Values.Length; i++) {
            zone.elements.SetBase(Upgrades[i], Values[i]);
        }

        EmpLog.Debug("Tent zone {ZoneUid}: upgrades {Values}", ZoneUid, string.Join(",", Values));
    }

    internal static TentZoneDelta Of(Zone zone)
    {
        return new() {
            ZoneUid = zone.uid,
            Values = System.Array.ConvertAll(Upgrades, id => zone.elements.Base(id)),
        };
    }
}
