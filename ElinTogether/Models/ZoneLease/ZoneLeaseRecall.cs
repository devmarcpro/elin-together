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

    /// <summary>
    ///     Host rule SoftRecall: the client may stay on that map and become a client of the host again in place,
    ///     without a copy of the world, see <see cref="ZoneSoftRejoin" />
    /// </summary>
    [Key(1)]
    public bool Soft { get; set; } = false;
}
