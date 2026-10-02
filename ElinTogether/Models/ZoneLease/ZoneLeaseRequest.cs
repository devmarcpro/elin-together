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

    /// <summary>
    ///     Set when the client created the zone itself (world map field, dungeon floor...), the host creates
    ///     it too and assigns the uid, see <see cref="ZoneLeaseGrant.RequestedUid" />
    /// </summary>
    [Key(2)]
    public LeaseZoneBlueprint? Blueprint { get; init; }

    public static ZoneLeaseRequest Create(Zone zone, bool createdLocally)
    {
        return new() {
            ZoneUid = zone.uid,
            ZoneFullName = zone.ZoneFullName,
            Blueprint = createdLocally ? LeaseZoneBlueprint.Create(zone) : null,
        };
    }
}

/// <summary>
///     Enough to recreate a zone with SpatialGen, like <see cref="SpatialGenDelta" /> does host -> client
/// </summary>
[MessagePackObject]
public class LeaseZoneBlueprint
{
    [Key(0)]
    public required string Id { get; init; }

    [Key(1)]
    public required int ParentUid { get; init; }

    [Key(2)]
    public required int X { get; init; }

    [Key(3)]
    public required int Y { get; init; }

    [Key(4)]
    public required int Icon { get; init; }

    [Key(5)]
    public required int[] ZoneState { get; init; }

    [Key(6)]
    public string? IdCurrentSubset { get; init; }

    /// <summary>
    ///     The zone of a quest: it has no place on the world map, belongs to the player who took the quest, and is
    ///     gone when that player leaves it
    /// </summary>
    [Key(7)]
    public bool Instance { get; set; }

    public static LeaseZoneBlueprint Create(Zone zone)
    {
        return new() {
            Id = zone.id,
            ParentUid = zone.parent?.uid ?? -1,
            X = zone.x,
            Y = zone.y,
            Icon = zone.icon,
            ZoneState = ZoneLeaseState.GetState(zone),
            IdCurrentSubset = zone.idCurrentSubset,
            Instance = zone.IsInstance,
        };
    }
}
