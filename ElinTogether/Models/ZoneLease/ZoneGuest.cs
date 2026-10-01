using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client simulating a zone <br />
///     Another player wants to join the zone: open a zone session if needed and expect it
/// </summary>
[MessagePackObject]
public class ZoneGuestRequest
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     Identity the guest connects with (Steam id, or the debug identity of local sessions)
    /// </summary>
    [Key(1)]
    public required ulong GuestUser { get; init; }

    /// <summary>
    ///     Guest character as the host last knew it
    /// </summary>
    [Key(2)]
    public required LZ4Bytes Chara { get; init; }
}

/// <summary>
///     Net packet: Client simulating a zone -> Host
/// </summary>
[MessagePackObject]
public class ZoneGuestReady
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    [Key(1)]
    public required ulong GuestUser { get; init; }

    [Key(2)]
    public required bool Accepted { get; init; }

    /// <summary>
    ///     Local udp port of the zone session (debug sessions), Steam connects by id
    /// </summary>
    [Key(3)]
    public int Port { get; init; }
}

/// <summary>
///     Where a guest joins the zone session, sent with <see cref="ZoneLeaseDepart" />
/// </summary>
[MessagePackObject]
public class ZoneGuestAddress
{
    [Key(0)]
    public required ulong HostUser { get; init; }

    [Key(1)]
    public required int Port { get; init; }
}

/// <summary>
///     Net packet: Guest -> Zone session host <br />
///     Leaving the zone: like <see cref="ZoneLeaseAck" />, sent after the guest's last deltas
/// </summary>
[MessagePackObject]
public class ZoneGuestLeave
{
    [Key(0)]
    public required int ZoneUid { get; init; }
}

/// <summary>
///     Net packet: Zone session host -> Guest <br />
///     Last actions applied and their results sent, the guest may go
/// </summary>
[MessagePackObject]
public class ZoneGuestLeft
{
    [Key(0)]
    public required int ZoneUid { get; init; }
}
