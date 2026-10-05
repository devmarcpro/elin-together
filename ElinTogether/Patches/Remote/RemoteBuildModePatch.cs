using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Build mode of a player who does not simulate the map. Building from the menu, mining, digging and cutting
///     are asked of the game that keeps the map (AgentTaskDelta, council 5). Areas, the terrain tool and
///     blueprints are not yet: they only changed this game's copy of the map, undone at the next visit, so the
///     click is refused with a message. Left alone: picking and moving installed furniture (AM_Inspect), which
///     is told as cards
/// </summary>
[HarmonyPatch(typeof(BaseTileSelector), nameof(BaseTileSelector.TryProcessTiles))]
internal static class RemoteBuildModePatch
{
    [HarmonyPrefix]
    private static bool OnTryProcessTiles(BaseTileSelector __instance)
    {
        if (EInput.skipFrame > 0 || NetSession.Instance.Connection is not ElinNetClient || ElinDelta.IsApplying) {
            return true;
        }

        // asked of the game that keeps the map, unless its host said no. The roof mode is the Alt key of the
        // machine that does the task: refused here, before the click pays
        var mode = __instance.mode;
        var asked = mode is AM_Build or AM_Mine or AM_Dig or AM_Cut;
        if (asked && NetSession.Instance.Rules.AllowGuestBuild && !mode.IsRoofEditMode()) {
            return true;
        }

        if (!asked && mode is not (AM_CreateArea or AM_ExpandArea or AM_EditArea or AM_Terrain or AM_Copy)) {
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
