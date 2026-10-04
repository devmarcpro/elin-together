using System.Linq;
using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Digging on the world map, the game looks for a treasure map in the bag of "the player". For another
///     player digging here that was this game's player: no chest for the one who dug, and a map of ours for
///     the same spot would have been used up instead. The map is looked for in the bag of the one who digs
/// </summary>
[HarmonyPatch(typeof(TaskDig), nameof(TaskDig.GetTreasureMap))]
internal static class RemoteTreasureMapPatch
{
    [HarmonyPrefix]
    internal static bool OnGetTreasureMap(TaskDig __instance, Point p, ref Thing? __result)
    {
        if (__instance.owner is not { IsRemotePlayer: true } digger) {
            return true;
        }

        __result = digger.things
            .List(t => t.trait is TraitScrollMapTreasure)
            .FirstOrDefault(t => p.Equals(((TraitScrollMapTreasure)t.trait).GetDest(true)));
        return false;
    }
}
