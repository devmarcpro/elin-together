using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Elin lays out a bag by "is the owner the player": the player's grid holds neither worn nor hotbar items, finds
///     room in nested bags and puts the player's own bag first. A game's copy of ANOTHER player's bag was laid out
///     like an NPC's: worn items took grid cells (a full bag at about 26 of 40), no stacking into bags. Every player
///     is the player here, as for the guest's own game
/// </summary>
[HarmonyPatch]
internal static class RemoteBagPatch
{
    [HarmonyTranspiler]
    [HarmonyPatch(typeof(ThingContainer), nameof(ThingContainer.ShouldShowOnGrid))]
    internal static IEnumerable<CodeInstruction> OnShouldShowOnGrid(IEnumerable<CodeInstruction> instructions)
    {
        return AnyPlayer(instructions);
    }

    [HarmonyTranspiler]
    [HarmonyPatch(typeof(ThingContainer), nameof(ThingContainer.TryStack))]
    internal static IEnumerable<CodeInstruction> OnTryStack(IEnumerable<CodeInstruction> instructions)
    {
        return AnyPlayer(instructions);
    }

    internal static IEnumerable<CodeInstruction> AnyPlayer(IEnumerable<CodeInstruction> instructions)
    {
        var isPc = AccessTools.PropertyGetter(typeof(Card), nameof(Card.IsPC));
        foreach (var instruction in instructions) {
            if (instruction.Calls(isPc)) {
                yield return new CodeInstruction(OpCodes.Call,
                    AccessTools.Method(typeof(CompanionAllyLimitPatch), nameof(CompanionAllyLimitPatch.IsAnyPlayer))) {
                    labels = instruction.labels,
                    blocks = instruction.blocks,
                };
            } else {
                yield return instruction;
            }
        }
    }
}

/// <summary>
///     The tie-break of the container sort in <see cref="ThingContainer.GetDest" /> is a lambda: the player's own
///     bags first, a remote player's too
/// </summary>
[HarmonyPatch]
internal static class RemoteBagSortPatch
{
    [HarmonyTargetMethod]
    internal static MethodBase SortLambda()
    {
        return AccessTools.GetDeclaredMethods(AccessTools.FirstInner(typeof(ThingContainer), t => t.Name == "<>c"))
            .First(m => m.Name.StartsWith("<GetDest>"));
    }

    [HarmonyTranspiler]
    internal static IEnumerable<CodeInstruction> OnSortLambda(IEnumerable<CodeInstruction> instructions)
    {
        return RemoteBagPatch.AnyPlayer(instructions);
    }
}
