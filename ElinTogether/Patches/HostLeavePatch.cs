using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The host leaves through the game's own menu while a guest would take the world over (WorldTakeover): the
///     same question and the same save as the game's, then the guests get that save before the game goes to the
///     title or closes (ElinNetHost.LeaveWithLastCopy). Otherwise the game's own code runs untouched
/// </summary>
[HarmonyPatch]
internal class HostLeavePatch
{
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Game), nameof(Game.GotoTitle))]
    internal static bool OnGotoTitle(bool showDialog)
    {
        // without the question the game does not save (the end of a character): nothing new to give
        if (!showDialog || !ElinNetHost.OwesGuestsLastCopy) {
            return true;
        }

        Dialog.YesNo("dialog_gotoTitle", () => {
            if (EClass.game.Save(true)) {
                ElinNetHost.LeaveWithLastCopy(false, () => EClass.scene.Init(Scene.Mode.Title));
            }
        });
        return false;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Game), nameof(Game.Quit))]
    internal static bool OnQuit()
    {
        if (!ElinNetHost.OwesGuestsLastCopy) {
            return true;
        }

        Dialog.YesNo("dialog_quit", () => {
            if (EClass.game.Save()) {
                ElinNetHost.LeaveWithLastCopy(false, () => EClass.core.Quit());
            }
        });
        return false;
    }
}
