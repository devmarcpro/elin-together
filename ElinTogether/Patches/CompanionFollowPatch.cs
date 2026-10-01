using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Companions follow the player who owns them instead of the party leader
/// </summary>
[HarmonyPatch]
internal static class CompanionFollowPatch
{
    [HarmonyTranspiler]
    [HarmonyPatch(typeof(AI_Idle), nameof(AI_Idle.Run), MethodType.Enumerator)]
    internal static IEnumerable<CodeInstruction> OnRun(IEnumerable<CodeInstruction> instructions, MethodBase original)
    {
        var self = AccessTools.Field(original.DeclaringType, "<>4__this");
        var getLeader = AccessTools.PropertyGetter(typeof(Party), nameof(Party.leader));

        // party.leader -> FollowTarget(party, this), only the follow block of AI_Idle reads it
        foreach (var instruction in instructions) {
            if (!instruction.Calls(getLeader)) {
                yield return instruction;
                continue;
            }

            yield return new CodeInstruction(OpCodes.Ldarg_0) {
                labels = instruction.labels,
                blocks = instruction.blocks,
            };
            yield return new CodeInstruction(OpCodes.Ldfld, self);
            yield return CodeInstruction.Call(typeof(CompanionFollowPatch), nameof(FollowTarget));
        }
    }

    internal static Chara FollowTarget(Party party, AI_Idle ai)
    {
        return ai.owner?.FindCompanionOwnerHere() ?? party.leader;
    }
}
