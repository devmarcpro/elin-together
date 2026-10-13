using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Net;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     A game that does not simulate its map takes the characters as they are told: a character that comes back
///     with its player (a mount under its rider, after the host went home and the guest followed) was sometimes
///     left twice in the tiles of the map, once as the copy that is on the map and once as an older copy nobody
///     lists (ride_suite V3, one pass in three, 2026-10-14). The game draws what the tiles hold: a mount seen
///     twice, or seen where it is not. <br />
///     Every two seconds, on such a game: a tile keeps a character once, and only the copy the map lists
/// </summary>
internal static class ClientCellSweep
{
    private const float Period = 2f;
    private static float _next;
    private static readonly HashSet<Chara> _listed = [];

    internal static void Update()
    {
        if (Time.unscaledTime < _next || NetSession.Instance.Connection is not ElinNetClient || EClass._map?.cells is not { } cells) {
            return;
        }

        _next = Time.unscaledTime + Period;
        _listed.Clear();
        foreach (var chara in EClass._map.charas) {
            _listed.Add(chara);
        }

        var size = EClass._map.Size;
        for (var x = 0; x < size; ++x) {
            for (var z = 0; z < size; ++z) {
                if (cells[x, z].detail?.charas is not { Count: > 0 } list) {
                    continue;
                }

                for (var i = list.Count - 1; i >= 0; --i) {
                    var chara = list[i];
                    if (chara is not null && _listed.Contains(chara) && list.IndexOf(chara) == i) {
                        continue;
                    }

                    EmpLog.Debug("Tile {X},{Z}: character {Uid} was there twice or as a copy the map does not list, removed",
                        x, z, chara?.uid ?? 0);
                    list.RemoveAt(i);
                }
            }
        }
    }
}
