using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A map unknown to this game is built from the state its keeper sends, its region with it. While that is read,
///     a child of the region can still be an empty shell (its id not read yet): the game's check of each child
///     against the list of zones threw on the null id, the map was refused and asked for again. A child with no id
///     yet is left alone, the others are checked as the game does
/// </summary>
[HarmonyPatch(typeof(Region), "_OnDeserialized")]
internal static class RegionChildGuardPatch
{
    [HarmonyPrefix]
    internal static bool OnDeserialized(Region __instance)
    {
        var children = __instance.children;
        if (children is null) {
            return false;
        }

        for (var i = children.Count - 1; i >= 0; i--) {
            var child = children[i];
            if (child?.id is null) {
                continue;
            }

            if (!EClass.sources.zones.map.ContainsKey(child.id)) {
                __instance.RemoveChild(child);
            }
        }

        return false;
    }
}
