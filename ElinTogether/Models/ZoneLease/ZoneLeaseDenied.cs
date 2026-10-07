using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client
/// </summary>
[MessagePackObject]
public class ZoneLeaseDenied
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     Lang key
    /// </summary>
    [Key(1)]
    public required string Reason { get; init; }

    /// <summary>
    ///     Refused because the host stands there (emp_travel_host_zone): the number of that zone in the host's
    ///     game. <see cref="ZoneUid" /> is the number the request came with, which is the client's own for a zone
    ///     it made itself. 0 when not told
    /// </summary>
    [Key(2)]
    public int HostZoneUid { get; set; } = 0;
}
