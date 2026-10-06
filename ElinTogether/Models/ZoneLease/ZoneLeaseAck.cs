using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Client -> Host <br />
///     Sent after the client flushed its last deltas from the host zone and stopped syncing it <br />
///     Until then the player is still on the host map, so nothing it did before leaving is lost
/// </summary>
[MessagePackObject]
public class ZoneLeaseAck
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     Joining the player who simulates that map without leaving it (the host left, see StayAsGuest):
    ///     the tile we stand on, kept through the reload
    /// </summary>
    [Key(1)]
    public Position? Stood { get; init; }

    /// <summary>
    ///     Walking into a map another player simulates: the way in
    /// </summary>
    [Key(2)]
    public ZoneArrival? Arrival { get; init; }
}
