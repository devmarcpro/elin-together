using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using ElinTogether.Helper;
using ElinTogether.Net;
using EModding.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Three rules of a base that ask about "the player" (EClass.pc) mean the game that simulates the base map,
///     and so, in a session, one player only (audit 2026-10-23, NetSessionRules.PlayersAtBase). Each now counts
///     every player standing on that map. Alone on it, that is EClass.pc only: the game's own rule <br />
///     - raids (FactionBranch.OnSimulateHour) did not come while the host slept, even with a guest awake at the
///     base. They stop while nobody there is awake, as for a player alone <br />
///     - the lucky month (FactionBranch.OnSimulateDay) followed the god of whoever simulated the base. The chance
///     of a follower of Ehekatl applies when any player on the base map has that god: the simplest rule that gives
///     each player the same say, without a sum of chances (two followers do not make a luckier month than one,
///     as one player alone cannot have two gods) <br />
///     - days together (FactionBranch.OnAdvanceDay, c_daysWithPC) were only counted by the world keeper for
///     residents standing where the keeper stands. A player holding a map of its own does not run that hook
///     (WorldKeeper), and the residents of that map come back with its release: their days at its side were lost.
///     That player counts them, for the residents on its map, see <see cref="OnAdvanceDayAway" />
/// </summary>
[HarmonyPatch]
internal static class PlayersAtBase
{
    private static bool Enabled => NetSession.Instance is { HasActiveConnection: true, Rules.PlayersAtBase: true };

    private static readonly MethodInfo GetPc = AccessTools.PropertyGetter(typeof(EClass), nameof(EClass.pc));

    /// <summary>
    ///     The other players standing on the map this game simulates
    /// </summary>
    private static IEnumerable<Chara> OtherPlayersHere()
    {
        return EClass._map?.charas.Where(c => !c.IsPC && c.IsPlayer) ?? [];
    }

    [HarmonyTranspiler]
    [HarmonyPatch(typeof(FactionBranch), nameof(FactionBranch.OnSimulateHour))]
    internal static IEnumerable<CodeInstruction> OnRaidCheck(IEnumerable<CodeInstruction> instructions)
    {
        // !EClass.pc.IsDeadOrSleeping: the only call of that getter on EClass.pc in the method
        return new CodeMatcher(instructions)
            .MatchStartForward(
                new CodeMatch(OpCodes.Call, GetPc),
                new CodeMatch(ci => ci.operand is MethodInfo { Name: "get_IsDeadOrSleeping" }))
            .EnsureValid("FactionBranch.OnSimulateHour EClass.pc.IsDeadOrSleeping")
            .Advance(1)
            .SetInstruction(Transpilers.EmitDelegate(NobodyAwake))
            .InstructionEnumeration();
    }

    private static bool NobodyAwake(Chara pc)
    {
        if (!pc.IsDeadOrSleeping) {
            return false;
        }

        return !Enabled || OtherPlayersHere().All(c => c.IsDeadOrSleeping);
    }

    [HarmonyTranspiler]
    [HarmonyPatch(typeof(FactionBranch), nameof(FactionBranch.OnSimulateDay))]
    internal static IEnumerable<CodeInstruction> OnLuckyMonth(IEnumerable<CodeInstruction> instructions)
    {
        // EClass.pc.faith == EClass.game.religions.Luck (the faith of the residents is read too, not after EClass.pc)
        return new CodeMatcher(instructions)
            .MatchStartForward(
                new CodeMatch(OpCodes.Call, GetPc),
                new CodeMatch(ci => ci.operand is MethodInfo { Name: "get_faith" }))
            .EnsureValid("FactionBranch.OnSimulateDay EClass.pc.faith")
            .Advance(1)
            .SetInstruction(Transpilers.EmitDelegate(FaithForLuck))
            .InstructionEnumeration();
    }

    private static Religion FaithForLuck(Chara pc)
    {
        var luck = EClass.game.religions.Luck;
        if (pc.faith == luck || !Enabled) {
            return pc.faith;
        }

        return OtherPlayersHere().Any(c => c.faith == luck) ? luck : pc.faith;
    }

    /// <summary>
    ///     A player holding a map of its own: the residents of the base on it spent the day with a player, as
    ///     FactionBranch.OnAdvanceDay counts them for the keeper (its party, or on its map). Only when the keeper's
    ///     hook did not run here, or they would count twice
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Faction), nameof(Faction.OnAdvanceDay))]
    internal static void OnAdvanceDayAway(Faction __instance)
    {
        if (!Enabled || !WorldKeeper.Skip || !NetSession.Instance.IsZoneAuthority || EClass.pc is not { } pc ||
            __instance != pc.faction) {
            return;
        }

        foreach (var branch in __instance.GetChildren()) {
            foreach (var member in branch.members) {
                if (!member.IsPC && !member.isDead && !member.IsPlayer && member.currentZone == pc.currentZone) {
                    member.c_daysWithPC++;
                }
            }
        }
    }
}
