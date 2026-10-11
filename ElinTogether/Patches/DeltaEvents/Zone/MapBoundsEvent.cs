using ElinTogether.Models;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Land bought for a base is bought for every player, see <see cref="MapBoundsDelta" />
/// </summary>
[HarmonyPatch(typeof(MapBounds), nameof(MapBounds.Expand))]
internal static class MapBoundsEvent
{
    [HarmonyPostfix]
    internal static void OnExpand(MapBounds __instance)
    {
        MapBoundsDelta.Emit(__instance);
    }
}
