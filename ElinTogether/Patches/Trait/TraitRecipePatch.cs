using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A recipe is learnt by everyone, once: the reader's game learns it and tells the others (AddRecipeDelta).
///     The read of another player is played again here too and taught it a second time
/// </summary>
[HarmonyPatch(typeof(TraitRecipe), nameof(TraitRecipe.OnRead))]
internal static class TraitRecipePatch
{
    [HarmonyPrefix]
    internal static bool OnRead(TraitRecipe __instance, Chara c)
    {
        if (!NetSession.Instance.HasActiveConnection || c.IsPC) {
            return true;
        }

        __instance.owner.ModNum(-1);
        return false;
    }
}
