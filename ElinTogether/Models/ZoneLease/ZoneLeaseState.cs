using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace ElinTogether.Models;

/// <summary>
///     What travels with a zone lease: the map files and the packed zone state
/// </summary>
internal static class ZoneLeaseState
{
    // Spatial._ints entries owned by the host: uid, world map x, world map y
    private static readonly HashSet<int> _hostOwnedInts = [1, 3, 4];

    /// <summary>
    ///     Map files of the zone, saving the loaded map first. Null when there is nothing on disk
    /// </summary>
    internal static Dictionary<string, LZ4Bytes>? CollectMap(Zone zone)
    {
        zone.map?.Save(zone.pathSave);

        if (!Directory.Exists(zone.pathSave)) {
            return null;
        }

        return Directory
            .GetFiles(zone.pathSave, "*.*", SearchOption.TopDirectoryOnly)
            .ToDictionary(Path.GetFileNameWithoutExtension, LZ4Bytes.CreateFromFile);
    }

    internal static void WriteMap(Zone zone, Dictionary<string, LZ4Bytes> map)
    {
        Directory.CreateDirectory(zone.pathSave);

        foreach (var (id, asset) in map) {
            if (id.Contains('.') || id.Contains('/') || id.Contains('\\')) {
                continue;
            }

            asset.DecompressToFile(Path.Combine(zone.pathSave, id));
        }
    }

    /// <summary>
    ///     Flags, visit count, dates... everything Elin persists about a zone besides its map
    /// </summary>
    internal static int[] GetState(Zone zone)
    {
        var state = zone._ints.ToArray();
        // flags live in bits at runtime, _ints[0] is only refreshed when serializing
        state[0] = (int)zone.bits.Bits;
        return state;
    }

    /// <summary>
    ///     Zones this game is about to enter while another player is in them, with the state that player's game
    ///     sent. See BossFleePatch
    /// </summary>
    internal static readonly HashSet<int> Imported = [];

    internal static void ApplyState(Zone zone, int[] state, string? subset)
    {
        for (var i = 0; i < Math.Min(state.Length, zone._ints.Length); i++) {
            if (!_hostOwnedInts.Contains(i)) {
                zone._ints[i] = state[i];
            }
        }

        zone.bits.Bits = (uint)state[0];
        zone.idCurrentSubset = subset;
    }
}
