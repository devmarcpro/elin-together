using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Client -> Host <br />
///     A lease arrived that this player is not waiting for anymore (it inherited the map it stands on in the
///     meantime): the host takes it back, the zone must not stay held by someone who is not in it
/// </summary>
[MessagePackObject]
public class ZoneLeaseDecline
{
    [Key(0)]
    public required int ZoneUid { get; init; }
}
