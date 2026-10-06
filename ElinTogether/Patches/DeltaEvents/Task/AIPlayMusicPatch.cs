using System.Collections.Generic;
using System.Reflection.Emit;
using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal static class AIPlayMusicPatch
{
    [HarmonyTranspiler]
    [HarmonyPatch(typeof(AI_PlayMusic), nameof(AI_PlayMusic.Evaluate))]
    internal static IEnumerable<CodeInstruction> OnEvaluate(IEnumerable<CodeInstruction> instructions)
    {
        return new CodeMatcher(instructions)
            .MatchStartForward(
                new CodeMatch(OpCodes.Callvirt, AccessTools.PropertyGetter(typeof(Card), nameof(Card.IsPC))))
            .SetInstructionAndAdvance(
                Transpilers.EmitDelegate((Chara chara) => chara.IsPlayer))
            .InstructionEnumeration();
    }

    [HarmonyTranspiler]
    [HarmonyPatch(typeof(AI_PlayMusic), nameof(AI_PlayMusic.ThrowReward))]
    internal static IEnumerable<CodeInstruction> OnThrowReward(IEnumerable<CodeInstruction> instructions)
    {
        return new CodeMatcher(instructions)
            .MatchStartForward(
                new CodeMatch(OpCodes.Callvirt, AccessTools.PropertyGetter(typeof(Card), nameof(Card.IsPC))))
            .Repeat(cm => cm.SetInstructionAndAdvance(
                Transpilers.EmitDelegate((Chara chara) => chara.IsPlayer)))
            .InstructionEnumeration();
    }
    /// <summary>
    ///     The audience of someone who plays music: the game leaves "the player" out of it, and so are the other
    ///     players. Their characters threw coins at the musician like the people of the town (reported from a real game)
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Point), nameof(Point.ListWitnesses))]
    internal static void OnListWitnesses(WitnessType type, List<Chara> __result)
    {
        if (type == WitnessType.music) {
            __result.RemoveAll(c => c.IsPlayer);
        }
    }
}