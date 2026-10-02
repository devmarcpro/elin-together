using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class TradeItem
{
    [Key(0)]
    public required int Uid { get; init; }

    [Key(1)]
    public required int Num { get; init; }
}

/// <summary>
///     A player to the game simulating the map: invite, answer, change its offer, confirm, cancel
///     (see <see cref="PlayerTrade" />)
/// </summary>
[MessagePackObject]
public class TradeIntentDelta : ElinDelta
{
    [Key(0)]
    public required int Kind { get; init; }

    [Key(1)]
    public int TradeId { get; set; }

    /// <summary>
    ///     Who to trade with, for an invitation
    /// </summary>
    [Key(2)]
    public int PartnerUid { get; set; }

    [Key(3)]
    public List<TradeItem>? Items { get; set; }

    [Key(4)]
    public int Gold { get; set; }

    /// <summary>
    ///     The state of the table the sender confirms: a confirmation of an older one is ignored
    /// </summary>
    [Key(5)]
    public int Revision { get; set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host && host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var from)) {
            PlayerTrade.Handle(this, from, host);
        }
    }
}

/// <summary>
///     The game simulating the map to the two players of a trade: what is on the table, who confirmed, how it ended
/// </summary>
[MessagePackObject]
public class TradeStateDelta : ElinDelta
{
    [Key(0)]
    public int TradeId { get; set; }

    [Key(1)]
    public int Phase { get; set; }

    [Key(2)]
    public int UidA { get; set; }

    [Key(3)]
    public int UidB { get; set; }

    [Key(4)]
    public List<TradeItem> ItemsA { get; set; } = [];

    [Key(5)]
    public List<TradeItem> ItemsB { get; set; } = [];

    [Key(6)]
    public int GoldA { get; set; }

    [Key(7)]
    public int GoldB { get; set; }

    [Key(8)]
    public bool ReadyA { get; set; }

    [Key(9)]
    public bool ReadyB { get; set; }

    [Key(10)]
    public int Revision { get; set; }

    /// <summary>
    ///     Why it was cancelled, as a text id
    /// </summary>
    [Key(11)]
    public string Reason { get; set; } = "";

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost) {
            PlayerTrade.Show(this);
        }
    }
}
