using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The codex is shared: a card collected by any player is told to all, wherever they are, see
///     <see cref="CodexCardDelta" />
/// </summary>
[HarmonyPatch]
internal static class CodexCardPatch
{
    [HarmonyPostfix]
    [HarmonyPatch(typeof(CodexManager), nameof(CodexManager.AddCard))]
    internal static void OnAddCard(CodexManager __instance, string id, int num)
    {
        Tell(__instance, id, num);
    }

    // a card taken out of the codex as a figure: the count goes down by hand, not through AddCard
    [HarmonyPrefix]
    [HarmonyPatch(typeof(ContentCodex), nameof(ContentCodex.OnClickGetCard))]
    internal static void OnGetCard(ContentCodex __instance)
    {
        if (__instance.currentCodex is { numCard: > 0 } creature) {
            Tell(EClass.player.codex, creature.id, -1);
        }
    }

    private static void Tell(CodexManager codex, string id, int num)
    {
        if (ElinDelta.IsApplying || num == 0 || string.IsNullOrEmpty(id) || !ReferenceEquals(codex, EClass.player?.codex)) {
            return;
        }

        var delta = new CodexCardDelta {
            Id = id,
            Num = num,
        };

        // travelling alone: the codex is the world's, the host tells everyone
        QuestAwaySync.Send(delta);
        NetSession.Instance.Connection?.Delta.AddRemote(delta);
    }
}
