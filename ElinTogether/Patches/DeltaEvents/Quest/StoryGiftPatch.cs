using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A gacha pull drops its ball through the same door as a story gift, but the host already creates that one
///     (InvOwnerOnProcessDelta)
/// </summary>
[HarmonyPatch(typeof(TraitGacha), nameof(TraitGacha.PlayGacha))]
internal static class StoryGiftPatch
{
    [HarmonyPrefix]
    internal static void OnPlayGacha()
    {
        StoryGifts.HostGives = true;
    }

    [HarmonyFinalizer]
    internal static void OnPlayGachaEnd()
    {
        StoryGifts.HostGives = false;
    }
}
