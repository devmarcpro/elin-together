using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     The cursed manor: the first treasure a player takes is allowed and moves the quest on, a second one curses
///     it. The game keeps "took one" for "the player": with the story flags common, the second PLAYER was cursed
///     for its first treasure. "Took one" is now each player's own (DialogFlagSync, own flags), and the quest of
///     the group still moves on once: a mark of the world says a treasure was taken, the first treasure of the
///     next player leaves the quest where it is
/// </summary>
[HarmonyPatch]
internal static class MelilithTreasurePatch
{
    /// <summary>
    ///     Dialog flag of the world (common to every game): a first treasure was taken
    /// </summary>
    internal const string Taken = "emp_melilith_taken";

    // the frame the game noted this player's first treasure: the quest step it makes right after is that one
    private static int _frame = -1;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Player.Flags), nameof(Player.Flags.pickedMelilithTreasure), MethodType.Setter)]
    internal static void OnFirstTreasure(bool value)
    {
        if (value) {
            _frame = Time.frameCount;
        }
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Quest), nameof(Quest.NextPhase))]
    internal static bool OnQuestStep(Quest __instance)
    {
        if (__instance is not QuestCursedManor || Time.frameCount != _frame || EClass.player?.dialogFlags is not { } flags) {
            return true;
        }

        _frame = -1;
        if (flags.TryGetValue(Taken, out var taken) && taken > 0) {
            EmpLog.Information("First treasure of this player in the cursed manor: the quest of the group already moved on");
            return false;
        }

        flags[Taken] = 1;
        return true;
    }

    /// <summary>
    ///     A world played before this: the host's "took one" was the group's, the mark is made from it
    /// </summary>
    internal static void MarkOldWorld(Player player)
    {
        if (NetSession.Instance.Transport is not ElinNetClient && player.flags.pickedMelilithTreasure &&
            !player.dialogFlags.ContainsKey(Taken)) {
            player.dialogFlags[Taken] = 1;
        }
    }
}
