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
    /// <summary>
    ///     Host uid of the zone, differs from <see cref="RequestedUid" /> for a zone the client created
    /// </summary>
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     Uid the client asked for
    /// </summary>
    [Key(5)]
    public required int RequestedUid { get; init; }

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

    /// <summary>
    ///     Another player simulates the zone, join its zone session instead, see <see cref="ZoneGuestRequest" />
    /// </summary>
    [Key(6)]
    public bool Guest { get; init; }

    /// <summary>
    ///     The owner of the zone we visit left it: keep playing there, this client simulates it from now on
    /// </summary>
    [Key(7)]
    public bool Handoff { get; init; }
}
