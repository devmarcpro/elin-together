using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Client -> Host <br />
///     Ask to travel to a zone the host is not in, and simulate it locally
/// </summary>
[MessagePackObject]
public class ZoneLeaseRequest
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    [Key(1)]
    public required string ZoneFullName { get; init; }

    public static ZoneLeaseRequest Create(Zone zone)
    {
        return new() {
            ZoneUid = zone.uid,
            ZoneFullName = zone.ZoneFullName,
        };
    }
}
