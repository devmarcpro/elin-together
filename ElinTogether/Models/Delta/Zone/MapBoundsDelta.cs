using System;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Land bought from the maid of a base (daBuyLand) widens the bounds of the map one can build in, by hand:
///     no setter to watch. The player who bought sends the bounds its map now has, every game showing that map
///     takes them. Bounds only grow: one that does not hold the present one is not taken
/// </summary>
[MessagePackObject]
public class MapBoundsDelta : ElinDelta
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     x, z, maxX, maxZ
    /// </summary>
    [Key(1)]
    public required int[] Bounds { get; init; }

    internal static void Emit(MapBounds bounds)
    {
        if (IsApplying || EClass._map?.bounds != bounds || EClass._zone is not { } zone ||
            NetSession.Instance.Connection is not { } connection) {
            return;
        }

        connection.Delta.AddRemote(new MapBoundsDelta {
            ZoneUid = zone.uid,
            Bounds = [bounds.x, bounds.z, bounds.maxX, bounds.maxZ],
        });
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Bounds.Length != 4) {
            return;
        }

        if (net is ElinNetHost host) {
            // (a player elsewhere drops it: the map comes whole when it walks in)
            host.SendDeltaToAllExcept(OriginPeer, this);
        }

        if (_zone?.uid != ZoneUid || _map is not { bounds: { } now } map) {
            return;
        }

        int x = Math.Max(1, Bounds[0]), z = Math.Max(1, Bounds[1]);
        int maxX = Math.Min(map.Size - 2, Bounds[2]), maxZ = Math.Min(map.Size - 2, Bounds[3]);
        if (x > now.x || z > now.z || maxX < now.maxX || maxZ < now.maxZ) {
            return;
        }

        (now.x, now.z, now.maxX, now.maxZ) = (x, z, maxX, maxZ);
        map.RefreshAllTiles();
        WidgetMinimap.UpdateMap();
    }
}
