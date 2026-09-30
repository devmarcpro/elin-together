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
}
