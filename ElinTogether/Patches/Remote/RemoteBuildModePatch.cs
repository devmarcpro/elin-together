using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Build mode of a player who does not simulate the map: the click paid its gold and then built nothing where
///     the map is kept (floors, walls and new furniture were not even made here; mining, digging, cutting, areas
///     and terrain only changed this game's copy of the map, undone at the next visit) <br />
///     Until each of these is a request to the game that keeps the map (council 5), the click is refused before
///     anything is paid. Left alone: picking and moving installed furniture (AM_Inspect), which is told as cards
/// </summary>
[HarmonyPatch(typeof(BaseTileSelector), nameof(BaseTileSelector.TryProcessTiles))]
internal static class RemoteBuildModePatch
{
    [HarmonyPrefix]
    private static bool OnTryProcessTiles(BaseTileSelector __instance)
    {
        if (EInput.skipFrame > 0 || NetSession.Instance.Connection is not ElinNetClient || ElinDelta.IsApplying ||
            __instance.mode is not (AM_Build or AM_Mine or AM_Dig or AM_Cut or AM_CreateArea or AM_ExpandArea
                or AM_EditArea or AM_Terrain or AM_Copy)) {
            return true;
        }

        // terrain and fill modes click again every frame while the button is held: say it once per press
        if (!EInput.leftMouse.pressing || EInput.leftMouse.down) {
            SE.Beep();
            EmpPop.Information("emp_base_host_only".lang());
        }

        return false;
    }
}
