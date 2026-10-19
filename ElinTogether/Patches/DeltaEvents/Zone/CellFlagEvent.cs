using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The cell tool of the build mode (AM_FlagCell), see <see cref="CellFlagDelta" />. Where the map is kept, the
///     changed cell is told like any other terrain; elsewhere the click is asked of the game that keeps it. The
///     shadow flag of the objects of a cell is left to each game (only a look)
/// </summary>
[HarmonyPatch(typeof(AM_FlagCell), nameof(AM_FlagCell.OnProcessTiles))]
internal static class CellFlagEvent
{
    [HarmonyPrefix]
    internal static bool OnFlag(AM_FlagCell __instance, Point point)
    {
        if (NetSession.Instance.Connection is not ElinNetClient client || ElinDelta.IsApplying) {
            return true;
        }

        var flag = __instance.mode switch {
            AM_FlagCell.Mode.flagSnow => 1,
            AM_FlagCell.Mode.flagFloat => 2,
            AM_FlagCell.Mode.flagWallPillar => 4,
            AM_FlagCell.Mode.flagOcclusion => 8,
            AM_FlagCell.Mode.flagClear => 16,
            _ => 0,
        };
        if (flag == 0) {
            return true;
        }

        client.Delta.AddRemote(new CellFlagDelta {
            ZoneUid = EClass._zone.uid,
            X = point.x,
            Z = point.z,
            Flag = flag,
            Value = (TileStateDelta.FlagsOf(point.cell) & flag) == 0,
        });
        return false;
    }

    [HarmonyPostfix]
    internal static void OnFlagged(Point point)
    {
        TileStateDelta.Mark(EClass._map, point.x, point.z);
    }
}
