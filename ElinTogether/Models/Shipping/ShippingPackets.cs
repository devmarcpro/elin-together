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
}
