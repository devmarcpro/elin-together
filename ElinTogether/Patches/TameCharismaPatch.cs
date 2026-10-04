using System.Collections.Generic;
using System.Reflection.Emit;
using ElinTogether.Helper;
using EModding.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Taming with a brush succeeds when the animal's best attribute is under the tamer's charisma. The game
///     reads the charisma of the local player: at the host, where the task of a guest runs, that is the host's,
///     so a guest tamed with the host's charisma. It is the charisma of the one who brushes
/// </summary>
[HarmonyPatch(typeof(AI_Fuck), nameof(AI_Fuck.Finish))]
internal static class TameCharismaPatch
{
    [HarmonyTranspiler]
    internal static IEnumerable<CodeInstruction> OnFinishIl(IEnumerable<CodeInstruction> instructions)
    {
        // EClass.pc.CHA -> Tamer(this).CHA
        return new CodeMatcher(instructions)
            .MatchStartForward(
                new CodeMatch(OpCodes.Call, AccessTools.PropertyGetter(typeof(EClass), nameof(EClass.pc))),
                new CodeMatch(OpCodes.Callvirt, AccessTools.PropertyGetter(typeof(Card), nameof(Card.CHA))))
            .EnsureValid("AI_Fuck.Finish EClass.pc.CHA")
            .SetInstructionAndAdvance(new(OpCodes.Ldarg_0))
            .InsertAndAdvance(Transpilers.EmitDelegate(Tamer))
            .InstructionEnumeration();
    }

    private static Chara Tamer(AI_Fuck act)
    {
        return act.owner is { IsPlayer: true } player ? player : EClass.pc;
    }
}
