using System.Linq;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The game hallucinates through one switch for the whole screen (Player.seedHallucination), set when a
///     character marked as a player (Card._IsPC) gets ConHallucination and cleared when it loses it. In a guest's
///     game the host's character carries that mark too: the host ate a white mushroom, the guest's screen
///     hallucinated, and stayed so after the host's had ended (player report, 2026-10-15). The switch follows the
///     local player only: on when it hallucinates, off when it does not
/// </summary>
[HarmonyPatch]
internal static class HallucinationPatch
{
    [HarmonyPostfix]
    [HarmonyPatch(typeof(ConHallucination), nameof(ConHallucination.SetOwner))]
    internal static void OnSetOwner()
    {
        Follow(null);
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(ConHallucination), nameof(ConHallucination.OnRemoved))]
    internal static void OnRemoved(ConHallucination __instance)
    {
        Follow(__instance);
    }

    private static void Follow(Condition? leaving)
    {
        if (EClass.pc is not { } pc) {
            return;
        }

        var mine = pc.conditions.Any(c => c is ConHallucination && c != leaving);
        if (!mine) {
            Player.seedHallucination = 0;
        } else if (Player.seedHallucination == 0) {
            Player.seedHallucination = EClass.rnd(10000) + 1;
        }
    }
}
