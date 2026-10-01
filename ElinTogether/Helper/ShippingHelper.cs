namespace ElinTogether.Helper;

/// <summary>
///     Shipping is per player: the one box of the base remembers who put each item in, the morning sale
///     pays everyone for its own goods, see ElinNetHostShipping
/// </summary>
internal static class ShippingHelper
{
    /// <summary>
    ///     Chara uid of the player who put the item in the shipping box
    /// </summary>
    internal const string ShipperKey = "emp_shipper";

    /// <summary>
    ///     Set while the host puts an item in the box for someone else (deposit of a player travelling alone)
    /// </summary>
    internal static int? ShipperOverride { get; set; }

    /// <summary>
    ///     Host rule, off: goods are not told apart and the host is paid for everything
    /// </summary>
    internal static bool Enabled => ElinTogether.Net.NetSession.Instance.Rules.UsePlayerShipping;

    internal static bool IsShippingBox(Card? card)
    {
        return card is not null && card == EClass.game?.cards?.container_shipping;
    }

    extension(Thing thing)
    {
        internal int ShipperUid => thing.GetInt(ShipperKey);
    }
}
