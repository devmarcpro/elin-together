using System.Collections.Generic;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client <br />
///     The client now simulates this zone on its own until it releases it
/// </summary>
[MessagePackObject]
public class ZoneLeaseGrant
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     First card uid the client may allocate, reserved above the host's own allocations
    /// </summary>
    [Key(1)]
    public required int UidRangeStart { get; init; }

    /// <summary>
    ///     Host zone state, see <see cref="ZoneLeaseState.GetState" />
    /// </summary>
    [Key(2)]
    public required int[] ZoneState { get; init; }

    [Key(3)]
    public string? IdCurrentSubset { get; init; }

    /// <summary>
    ///     Host map files, null when the host never generated it (or for regions)
    /// </summary>
    [Key(4)]
    public Dictionary<string, LZ4Bytes>? Map { get; init; }
}
