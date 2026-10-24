using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A guest used a moongate or a sky helm: it asks the host for the list, or for what it picked in it
///     (see <see cref="GateItems" />)
/// </summary>
[MessagePackObject]
public class GateItemRequest : ElinDelta
{
    [Key(0)]
    public required string Item { get; init; }

    /// <summary>
    ///     The user map picked (moongate)
    /// </summary>
    [Key(1)]
    public string? MapId { get; init; }

    /// <summary>
    ///     The zone picked (sky helm), 0 asks for the list
    /// </summary>
    [Key(2)]
    public int ZoneUid { get; init; }

    /// <summary>
    ///     The gate zone the guest saw with the list: another player moved it since, the pick is refused at no cost
    /// </summary>
    [Key(3)]
    public int Gate { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host && NetSession.Instance.Transport == host) {
            GateItems.OnRequest(host, this);
        }
    }
}

/// <summary>
///     The host to the guest that asked: the list to pick from, where to go, or nothing (refused)
/// </summary>
[MessagePackObject]
public class GateItemAnswer : ElinDelta
{
    [Key(0)]
    public required string Item { get; init; }

    /// <summary>
    ///     The list: user map ids (moongate) or zone uids (sky helm)
    /// </summary>
    [Key(1)]
    public List<string>? Ids { get; init; }

    [Key(2)]
    public List<string>? Names { get; init; }

    [Key(3)]
    public List<int>? Costs { get; init; }

    [Key(4)]
    public int Gate { get; init; }

    /// <summary>
    ///     Where to go (moongate), the new gate zone (sky helm)
    /// </summary>
    [Key(5)]
    public int ZoneUid { get; init; }

    [Key(6)]
    public int Cost { get; init; }

    /// <summary>
    ///     The zones named here, for a guest that did not hear of them yet (they go out a frame later)
    /// </summary>
    [Key(7)]
    public List<SpatialGenDelta>? Zones { get; init; }

    /// <summary>
    ///     The user map file: only the host may have it
    /// </summary>
    [Key(8)]
    public LZ4Bytes? Map { get; init; }

    [Key(9)]
    public string? FileName { get; init; }

    [Key(10)]
    public string? IdUser { get; init; }

    [Key(11)]
    public string? Name { get; init; }

    [Key(12)]
    public bool Underwater { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost) {
            GateItems.OnAnswer(net, this);
        }
    }
}

/// <summary>
///     The survival gate zone (sky helm, landing portal) is the host's, told to everyone when it changes
/// </summary>
[MessagePackObject]
public class GateZoneDelta : ElinDelta
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    // the zone itself, for a player whose world never had it
    [Key(1)]
    public SpatialGenDelta? Zone { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost || game is not { IsSurvival: true }) {
            return;
        }

        if (game.spatials.Find(ZoneUid) is null) {
            Zone?.Apply(net);
        }

        if (ZoneUid == 0 || game.spatials.Find(ZoneUid) is not null) {
            game.survival.gateZone = ZoneUid == 0 ? null : game.spatials.Find(ZoneUid);
        }
    }
}
