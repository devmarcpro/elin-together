using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client <br />
///     The host wants to enter the leased zone, hand it back and rejoin the host
/// </summary>
[MessagePackObject]
public class ZoneLeaseRecall
{
    [Key(0)]
    public required int ZoneUid { get; init; }
}
