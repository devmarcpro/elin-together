using System.Collections.Generic;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Client -> Host <br />
///     Hand a leased zone back, with everything the client changed while simulating it
/// </summary>
[MessagePackObject]
public class ZoneLeaseRelease
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     Client zone state, see <see cref="ZoneLeaseState.GetState" />
    /// </summary>
    [Key(1)]
    public required int[] ZoneState { get; init; }

    [Key(2)]
    public string? IdCurrentSubset { get; init; }

    /// <summary>
    ///     Client map files, null for regions (simulated locally only)
    /// </summary>
    [Key(3)]
    public Dictionary<string, LZ4Bytes>? Map { get; init; }

    /// <summary>
    ///     The client's own character, replacing the host copy
    /// </summary>
    [Key(4)]
    public required LZ4Bytes Chara { get; init; }

    [Key(5)]
    public required int UidNext { get; init; }

    /// <summary>
    ///     Return to the host zone, otherwise another lease request follows
    /// </summary>
    [Key(6)]
    public required bool Rejoin { get; init; }

    /// <summary>
    ///     Progress save while still away: applied by the host, the lease is kept
    /// </summary>
    [Key(7)]
    public bool Checkpoint { get; init; }
}
