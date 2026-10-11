using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Taking a god's artifact, the game destroys every other one of its kind held by "the player's side": the
///     whole party and the residents. Each player has its own here (RemoteGodGiftPatch): the second to take its
///     gift destroyed the first one's. What another player and its companions hold is left out of that purge, as
///     the game leaves replicas out: marked as one while it runs
/// </summary>
[HarmonyPatch(typeof(Card), nameof(Card.PurgeDuplicateArtifact))]
internal static class OwnArtifactPatch
{
    [HarmonyPrefix]
    internal static void OnPurge(Card __instance, Thing af, out List<Thing>? __state)
    {
        __state = null;
        if (NetSession.Instance.Connection is null) {
            return;
        }

        var taker = __instance.GetRootCard() as Chara ?? EClass.pc;
        var mine = CompanionHelper.OwnerOf(taker) ?? taker;
        var others = EClass._map.charas
            .Concat(EClass.pc.faction.GetChildren().SelectMany(b => b.members))
            .Distinct()
            .Where(c => CompanionHelper.OwnerOf(c) is { IsPlayer: true } owner && owner != mine);

        __state = [];
        foreach (var chara in others) {
            foreach (var kept in chara.things.List(t => !t.isReplica && t != af && (t.id == af.id || t.HasTag(CTAG.godArtifact)))) {
                kept.isReplica = true;
                __state.Add(kept);
            }
        }
    }

    [HarmonyFinalizer]
    internal static void OnPurgeEnd(List<Thing>? __state)
    {
        foreach (var kept in __state ?? []) {
            kept.isReplica = false;
        }
    }
}
