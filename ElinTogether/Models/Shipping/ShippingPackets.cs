using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Client travelling alone (or hosting a zone) -> Host <br />
///     An item put in the shipping box away from the host: the box there is a copy, the real one is the host's
/// </summary>
[MessagePackObject]
public class ShippingDeposit
{
    [Key(0)]
    public required LZ4Bytes Thing { get; init; }

    /// <summary>
    ///     Chara uid of the player shipping it: the sender, or a guest of the zone it simulates
    /// </summary>
    [Key(1)]
    public required int Shipper { get; init; }

    /// <summary>
    ///     Which box of the world: 0 the shipping box, 1 the delivery box (parcels), 2 the bank
    /// </summary>
    [Key(2)]
    public int Box { get; set; }

    /// <summary>
    ///     Not a deposit (Thing is empty): a look into that box, and with TakeNum, that many of its stack TakeUid
    ///     taken out of it. The answer is a ShippingPayout with BoxThings
    /// </summary>
    [Key(3)]
    public bool Ask { get; set; }

    [Key(4)]
    public int TakeUid { get; set; }

    [Key(5)]
    public int TakeNum { get; set; }
}

/// <summary>
///     Net packet: Host -> Client <br />
///     Morning sale of what this player put in the shipping box
/// </summary>
[MessagePackObject]
public class ShippingPayout
{
    /// <summary>
    ///     ShippingResult.ints, the player's own report
    /// </summary>
    [Key(0)]
    public required long[] Ints { get; init; }

    [Key(1)]
    public required string[][] ItemStrs { get; init; }

    /// <summary>
    ///     Shipping totals of the world (one progression for everyone), see Player.Stats
    /// </summary>
    [Key(2)]
    public required long ShipNum { get; init; }

    [Key(3)]
    public required long ShipMoney { get; init; }

    [Key(4)]
    public required int BranchLv { get; init; }

    [Key(5)]
    public required int BranchExp { get; init; }

    /// <summary>
    ///     Money and shipping bonus earned: the client adds them to its own purse, its currency is its own to change
    /// </summary>
    [Key(6)]
    public long Money { get; init; }

    [Key(7)]
    public long Bonus { get; init; }

    // ponytail: the answer about a world box rides on this packet, the only shipping one an away client lets in
    // (ElinNetClientTravel.ShouldReceiveWhileAway); its own packet when that list can take one more line

    /// <summary>
    ///     Not a sale when set: what the box holds now (List of Thing), see ShippingDeposit.Ask
    /// </summary>
    [Key(8)]
    public LZ4Bytes? BoxThings { get; init; }

    [Key(9)]
    public int Box { get; init; }

    /// <summary>
    ///     The thing taken out of the box for this player, it is nowhere else anymore
    /// </summary>
    [Key(10)]
    public LZ4Bytes? Taken { get; init; }

    /// <summary>
    ///     How many were asked for (0: only a look)
    /// </summary>
    [Key(11)]
    public int Asked { get; init; }
}
