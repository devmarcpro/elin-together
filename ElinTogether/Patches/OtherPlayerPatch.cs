using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Game code that reads "the player" where it means the character at hand, run for another player
///     (audit after the hallucination report, 2026-10-15)
/// </summary>
[HarmonyPatch]
internal static class OtherPlayerPatch
{
    private static bool IsMultiplayer => NetSession.Instance.Transport is not null;

    /// <summary>
    ///     Gene gear asks the feat points of "the player": for another player's equipment, those of the local one
    ///     (a guest with points could not wear a gene the host has no points for, in the host's game). The owner's
    /// </summary>
    [HarmonyTranspiler]
    [HarmonyPatch(typeof(CharaBody), nameof(CharaBody.IsEquippable))]
    internal static IEnumerable<CodeInstruction> OnIsEquippable(IEnumerable<CodeInstruction> instructions)
    {
        var getPc = AccessTools.PropertyGetter(typeof(EClass), nameof(EClass.pc));
        var getFeat = AccessTools.PropertyGetter(typeof(Card), nameof(Card.feat));
        var owner = AccessTools.Field(typeof(CharaBody), nameof(CharaBody.owner));
        var list = instructions.ToList();
        for (var i = 0; i < list.Count - 1; i++) {
            if (list[i].Calls(getPc) && list[i + 1].Calls(getFeat)) {
                var labels = list[i].labels;
                list[i] = new CodeInstruction(OpCodes.Ldarg_0) { labels = labels };
                list.Insert(i + 1, new CodeInstruction(OpCodes.Ldfld, owner));
                break;
            }
        }

        return list;
    }

    /// <summary>
    ///     Another player dies in this game: the game counts it as one of "the player's" pets that died (a statistic,
    ///     and once the tutorial about dead pets). Not a pet: the count stays as it was
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Die))]
    internal static void OnDie(Chara __instance, out int __state)
    {
        __state = -1;
        if (!IsMultiplayer || !__instance.IsRemotePlayer || EClass.player?.stats is not { } stats) {
            return;
        }

        __state = stats.allyDeath;
        // (above 0 the game does not reserve the tutorial)
        if (stats.allyDeath == 0) {
            stats.allyDeath = 1;
        }
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Die))]
    internal static void OnDieEnd(int __state)
    {
        if (__state >= 0 && EClass.player?.stats is { } stats) {
            stats.allyDeath = __state;
        }
    }

    /// <summary>
    ///     "Disband the party" sends away every member but "the player": the other players and their companions
    ///     too. Only the local player's own companions
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Party), nameof(Party.Disband))]
    internal static bool OnDisband(Party __instance)
    {
        if (!IsMultiplayer || EClass.pc is not { } pc || __instance != pc.party) {
            return true;
        }

        foreach (var item in CompanionHelper.CompanionsOf(pc)) {
            __instance.RemoveMember(item);
            if (item.homeZone != EClass._zone) {
                item.MoveZone(item.homeZone);
            }
        }

        return false;
    }

    /// <summary>
    ///     Walking the world map with "eat automatically", the game feeds every member of the party (no food given:
    ///     the best of the eater's bag). The other players and their companions eat in their own game: fed here too,
    ///     they ate twice, from the bag they carry
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.InstantEat))]
    internal static bool OnInstantEat(Chara __instance, Thing? t)
    {
        return t is not null || !IsMultiplayer || EClass.pc is not { } pc || CompanionHelper.OwnerOf(__instance) is not { } owner || owner == pc;
    }
}
