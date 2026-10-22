using ElinTogether.Models;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The playlist of a map is the same for every player, see <see cref="PlaylistDelta" />
/// </summary>
[HarmonyPatch(typeof(LayerEditPlaylist), nameof(LayerEditPlaylist.OnKill))]
internal static class PlaylistEvent
{
    [HarmonyPostfix]
    internal static void OnKill(LayerEditPlaylist __instance)
    {
        if (__instance.mode == LayerEditPlaylist.Mode.Playlist) {
            PlaylistDelta.Emit();
        }
    }
}
