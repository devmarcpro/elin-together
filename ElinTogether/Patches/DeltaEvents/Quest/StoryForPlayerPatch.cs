using System.Collections.Generic;
using System.Reflection;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Ends of story quests the game wrote for "the player", run by the host for the player who made the step
/// </summary>
[HarmonyPatch]
internal static class StoryForPlayerPatch
{
    /// <summary>
    ///     Nasu takes the backpack back from "the player": it is in the bag of the player who talked to her. For
    ///     the host it was not there, the end of the quest threw and its rewards were lost <br />
    ///     The debt starts with Loytel joining "the player" and a cassette in its bag: the player who took the debt
    ///     from Loytel, not the host (when that player has a home, the game reads it)
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(QuestNasu), nameof(QuestNasu.OnComplete))]
    [HarmonyPatch(typeof(QuestDebt), nameof(QuestDebt.OnStart))]
    internal static void OnNasuComplete(MethodBase __originalMethod, out ScopeExit? __state)
    {
        __state = QuestRewardPatch.Receiver is { isDead: false } earner &&
                  (earner.homeBranch is not null || __originalMethod.DeclaringType != typeof(QuestDebt))
            ? RemoteCraft.AsCrafter(earner)
            : null;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(QuestNasu), nameof(QuestNasu.OnComplete))]
    [HarmonyPatch(typeof(QuestDebt), nameof(QuestDebt.OnStart))]
    internal static void OnNasuCompleteEnd(ScopeExit? __state)
    {
        __state?.Dispose();
    }

    /// <summary>
    ///     The dreams of Lesimas: every game moves the quest one step when its player enters a base, at steps 0 to
    ///     3. On one map two games did it one after the other, and a dream was skipped. The game that simulates
    ///     the map does it, alone
    /// </summary>
    [HarmonyTranspiler]
    [HarmonyPatch(typeof(Player.Flags), nameof(Player.Flags.OnEnterZone))]
    internal static IEnumerable<CodeInstruction> OnEnterZone(IEnumerable<CodeInstruction> instructions)
    {
        var getPhase = AccessTools.Method(typeof(QuestManager), nameof(QuestManager.GetPhase)).MakeGenericMethod(typeof(QuestIntoDarkness));
        foreach (var instruction in instructions) {
            yield return instruction;
            if (instruction.operand is MethodInfo method && method == getPhase) {
                yield return CodeInstruction.Call(typeof(StoryForPlayerPatch), nameof(DreamPhase));
            }
        }
    }

    internal static int DreamPhase(int phase)
    {
        var session = NetSession.Instance;
        return session.Connection is ElinNetClient && !session.IsZoneAuthority ? -99 : phase;
    }
}
