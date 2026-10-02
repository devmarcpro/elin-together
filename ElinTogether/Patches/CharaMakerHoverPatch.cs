using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal class CharaMakerHoverPatch
{
    /// <summary>
    ///     The character screen reads what is under the pointer and throws on anything destroyed since
    ///     (a window without focus keeps its last hovered objects) <br />
    ///     Thrown while the screen opens, it cut OnSessionNewPlayerRequest short: the button kept the game's
    ///     own action and the new player never got past the world settings
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(UICharaMaker), nameof(UICharaMaker.RefreshPortraitZoom))]
    internal static void OnRefreshPortraitZoom()
    {
        InputModuleEX.GetPointerEventData()?.hovered.RemoveAll(hovered => hovered == null);
    }
}
