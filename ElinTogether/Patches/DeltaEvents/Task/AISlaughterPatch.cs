using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The end of a slaughter takes 3 stamina from "the player" whoever slaughtered. The end of another player's
///     task is played on every other game too (the host's, the other players'), where "the player" is someone
///     else: it paid for it. The player pays in its own game, its stamina reaches the others from there
/// </summary>
[HarmonyPatch(typeof(StatsStamina), nameof(StatsStamina.Mod))]
internal static class AISlaughterPatch
{
    [HarmonyPrefix]
    internal static bool OnMod()
    {
        return !(CharaProgressCompleteEvent.IsHappening && CharaProgressCompleteEvent.Action?.parent is AI_Slaughter &&
                 CharaProgressCompleteEvent.Chara is { IsRemotePlayer: true } slaughterer &&
                 BaseStats.CC != slaughterer);
    }
}
