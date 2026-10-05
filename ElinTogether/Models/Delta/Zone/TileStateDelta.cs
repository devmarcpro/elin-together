using System;
using System.Collections.Generic;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The terrain of the cells that changed on the map of whoever simulates it: floor, block, tile object, bridge,
///     roof, deco, directions and heights (council 5). The whole state of a cell is sent, not what was done to it:
///     applying it twice, or after a replay that already made the same change, changes nothing <br />
///     Without it terrain only followed by each game replaying the same act: what the build mode of the host made
///     (no act is told for it) reached the others at their next visit of the zone
/// </summary>
[MessagePackObject]
public class TileStateDelta : ElinDelta
{
    private const int Width = 21;

    // cells of one delta: a floor dragged over a whole map goes in several
    private const int MaxCells = 2048;

    private static readonly HashSet<int> _dirty = [];

    /// <summary>
    ///     x, z and the 19 terrain fields of each cell, one after the other
    /// </summary>
    [Key(0)]
    public required int[] Cells { get; init; }

    /// <summary>
    ///     The zone these cells are of: one told around a change of zone must not land on another map
    /// </summary>
    [Key(1)]
    public required int ZoneUid { get; init; }

    internal static void Mark(Map map, int x, int z)
    {
        // generating or loading a map is not a change to tell: everyone gets the whole map then
        if (!ZoneActivateEvent.IsHappening && core.IsGameStarted && !game.isLoading &&
            NetSession.Instance.Connection is ElinNetHost && map == _map) {
            _dirty.Add(x + z * map.Size);
        }
    }

    /// <summary>
    ///     The marks of a map that is left are not of the next one
    /// </summary>
    internal static void Forget()
    {
        _dirty.Clear();
    }

    /// <summary>
    ///     End of the frame, after the replays of the frame were queued (a task replayed on a cell that already
    ///     has its final state would act again: TaskMine digs stairs under a wall that is gone): keep it there
    /// </summary>
    internal static void Flush()
    {
        if (_dirty.Count == 0) {
            return;
        }

        if (NetSession.Instance.Connection is ElinNetHost host && !ZoneActivateEvent.IsHappening) {
            var size = _map.Size;
            var cells = new List<int>(Math.Min(_dirty.Count, MaxCells) * Width);
            void Send()
            {
                host.Delta.AddRemote(new TileStateDelta { Cells = [..cells], ZoneUid = _zone.uid });
                cells.Clear();
            }

            foreach (var index in _dirty) {
                int x = index % size, z = index / size;
                if (z >= size) {
                    continue;
                }

                var c = _map.cells[x, z];
                cells.AddRange([
                    x, z, c._block, c._blockMat, c._floor, c._floorMat, c.obj, c.objMat, c._bridge, c._bridgeMat,
                    c._roofBlock, c._roofBlockMat, c._deco, c._decoMat, c._dirs, c.objVal, c._roofBlockDir,
                    c.bridgePillar, c.height, c.bridgeHeight, c.hidePillar ? 1 : 0,
                ]);
                if (cells.Count >= MaxCells * Width) {
                    Send();
                }
            }

            if (cells.Count > 0) {
                Send();
            }
        }

        _dirty.Clear();
    }

    protected override void OnApply(ElinNetBase net)
    {
        // only ever told by the one simulating the map
        if (net.IsHost || _zone?.uid != ZoneUid || _map is not { } map) {
            return;
        }

        // many cells at once (a dragged floor): one refresh of the sight for all
        var many = Cells.Length > 64 * Width;

        for (var i = 0; i + Width <= Cells.Length; i += Width) {
            int x = Cells[i], z = Cells[i + 1];
            if (x < 0 || z < 0 || x >= map.Size || z >= map.Size) {
                continue;
            }

            var s = Cells.AsSpan(i + 2, Width - 2);
            var c = map.cells[x, z];
            var dirs = (byte)s[12];
            var same = c._block == s[0] && c._blockMat == s[1] && c._floor == s[2] && c._floorMat == s[3] &&
                       c.obj == s[4] && c.objMat == s[5] && c._bridge == s[6] && c._bridgeMat == s[7] &&
                       c._roofBlock == s[8] && c._roofBlockMat == s[9] && c._deco == s[10] && c._decoMat == s[11] &&
                       c._dirs == dirs && c.objVal == s[13] && c._roofBlockDir == s[14] && c.bridgePillar == s[15] &&
                       c.height == s[16] && c.bridgeHeight == s[17] && c.hidePillar == (s[18] != 0);
            if (same) {
                continue;
            }

            // the game's own setters for what has side effects (rooms, light, fire on a removed block), then the rest
            if (c._block != s[0] || c._blockMat != s[1]) {
                map.SetBlock(x, z, s[1], s[0]);
            }

            if (c._floor != s[2] || c._floorMat != s[3]) {
                map.SetFloor(x, z, s[3], s[2]);
            }

            if (c.obj != s[4] || c.objMat != s[5]) {
                map.SetObj(x, z, s[5], s[4], s[13], 0, true);
            }

            c._bridge = s[6];
            c._bridgeMat = s[7];
            c._roofBlock = s[8];
            c._roofBlockMat = s[9];
            c._deco = s[10];
            c._decoMat = s[11];
            c._dirs = dirs;
            c.objVal = (byte)s[13];
            c._roofBlockDir = (byte)s[14];
            c.bridgePillar = s[15];
            c.height = (byte)s[16];
            c.bridgeHeight = (byte)s[17];
            c.hidePillar = s[18] != 0;
            c.room?.SetDirty();
            map.RefreshNeighborTiles(x, z);
            if (!many) {
                map.RefreshFOV(x, z);
            }
        }

        if (many) {
            map.RefreshFOVAll();
        }
    }
}
