using ElinTogether.Models;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The step of the dialog that opens the deposit box of Kettle and Demitas makes the box in the game that plays it,
///     see <see cref="CopyShopDelta" />. A client without the host's box is sent back to the step it came from (shown
///     again as for any other "back") and the request goes out; the step is played again when the answer comes
/// </summary>
[HarmonyPatch(typeof(DramaSequence), nameof(DramaSequence.Play), typeof(string))]
internal static class DramaCopyShopPatch
{
    [HarmonyPrefix]
    private static void OnPlayStep(DramaSequence __instance, ref string id)
    {
        if (id == "_copyItem" && CopyShopDelta.Ask(__instance)) {
            id = __instance.lastStep ?? "";
        }
    }
}
