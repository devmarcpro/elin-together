using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client <br />
///     Answer to <see cref="ZoneLeaseAck" />, sent after the host applied the client's last actions and sent back
///     their results (stack merges, uid rebinds...), so the client leaves with the host's view of its character
/// </summary>
[MessagePackObject]
public class ZoneLeaseDepart
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     Guest lease: the zone session to join
    /// </summary>
    [Key(1)]
    public ZoneGuestAddress? Guest { get; init; }
}
