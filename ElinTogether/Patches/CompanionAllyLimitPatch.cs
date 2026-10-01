using System.Collections.Generic;
using System.Reflection.Emit;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     Every player has its own ally limit (its charisma, its companions), not the host's against the whole party,
///     where all players and all companions live <br />
///     Elin compares the party size with the limit for the slots shown, the exceeded party speed malus and
///     the empty slot bonus, see Player.RefreshEmptyAlly
/// </summary>
[HarmonyPatch]
internal static class CompanionAllyLimitPatch
{
    private static bool IsMultiplayerWorld => NetSession.Instance.Transport is not null;

    /// <summary>
    ///     The local player's own party: itself and its companions
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Party), nameof(Party.Count))]
    internal static void OnCount(Party __instance, ref int __result)
    {
        if (!IsMultiplayerWorld || EClass.pc is not { } pc || __instance != pc.party) {
            return;
        }

        __result = 1 + CompanionHelper.UsedAllySlots(pc);
    }

    /// <summary>
    ///     Exceeded party malus of a companion: its owner's slots, the local ones are in Player.lastEmptyAlly
    /// </summary>
    [HarmonyTranspiler]
    [HarmonyPatch(typeof(Chara), nameof(Chara.RefreshSpeed))]
    internal static IEnumerable<CodeInstruction> OnRefreshSpeed(IEnumerable<CodeInstruction> instructions)
    {
        var lastEmptyAlly = AccessTools.Field(typeof(Player), nameof(Player.lastEmptyAlly));

        foreach (var instruction in instructions) {
            if (!instruction.LoadsField(lastEmptyAlly)) {
                yield return instruction;
                continue;
            }

            // player on the stack -> EmptyAllyFor(player, this)
            yield return new CodeInstruction(OpCodes.Ldarg_0) {
                labels = instruction.labels,
                blocks = instruction.blocks,
            };
            yield return CodeInstruction.Call(typeof(CompanionAllyLimitPatch), nameof(EmptyAllyFor));
        }
    }

    internal static int EmptyAllyFor(Player player, Chara chara)
    {
        if (!IsMultiplayerWorld || CompanionHelper.OwnerOf(chara) is not { } owner || owner == EClass.pc) {
            return player.lastEmptyAlly;
        }

        var maxAlly = Mathf.Min(Mathf.Max(owner.CHA / 10, 1), 5) + owner.Evalue(1645);
        return maxAlly - CompanionHelper.UsedAllySlots(owner);
    }

    /// <summary>
    ///     A party change moves the slots of its owner only, Elin refreshes speeds when the local ones change
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Party), nameof(Party.AddMemeber))]
    internal static void OnAddMember(Party __instance)
    {
        RefreshMembers(__instance);
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Party), nameof(Party.RemoveMember))]
    internal static void OnRemoveMember(Party __instance)
    {
        RefreshMembers(__instance);
    }

    private static void RefreshMembers(Party party)
    {
        if (!IsMultiplayerWorld) {
            return;
        }

        foreach (var member in party.members) {
            member?.SetDirtySpeed();
        }
    }
}
