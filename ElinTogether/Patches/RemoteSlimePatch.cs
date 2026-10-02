using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The game only lets "the player" be an evolving slime (eat genes, grow gene slots with levels). The
///     character of another player is no local player on the side that simulates it: there it could not eat a
///     gene, and whatever its own game had absorbed was gone with the next copy sent back to it
/// </summary>
[HarmonyPatch]
internal static class RemoteSlimePatch
{
    private const int FeatSlime = 1274;

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Card), nameof(Card.IsSlimeEvolvable), MethodType.Getter)]
    internal static void OnIsSlimeEvolvable(Card __instance, ref bool __result)
    {
        if (!__result && __instance is Chara { IsRemotePlayer: true } chara && chara.HasElement(FeatSlime)) {
            __result = true;
        }
    }

    /// <summary>
    ///     A gene costs the player a twentieth of what it costs anyone else in feat points: the copy of a player
    ///     paid the full price, its feat points drifted from the ones its own game shows
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.GeneCostMTP), MethodType.Getter)]
    internal static void OnGeneCostMTP(Chara __instance, ref int __result)
    {
        if (__instance.IsRemotePlayer) {
            // what Chara.GeneCostMTP answers for the player
            __result = 5;
        }
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(AI_Eat), nameof(AI_Eat.IsValidTarget))]
    internal static void OnIsValidTarget(AI_Eat __instance, Card c, ref bool __result)
    {
        if (!__result && c?.trait is TraitGene && __instance.owner is { IsRemotePlayer: true } owner) {
            __result = owner.HasElement(FeatSlime);
        }
    }
}
