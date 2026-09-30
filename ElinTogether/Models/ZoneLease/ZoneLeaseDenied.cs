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
}
