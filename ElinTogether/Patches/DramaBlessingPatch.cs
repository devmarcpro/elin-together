using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     True while a dialog closes: the priestess' blessing is given there (a SetOnKill of the LayerDrama, when
///     LayerDrama.Instance may already be gone), to the player's group <br />
///     In a client's game that blessing is refused (conditions are not its own to add), so what it gives the player and
///     its companions is asked of the host, see <see cref="CharaAddConditionEvent" />
/// </summary>
[HarmonyPatch(typeof(global::Layer), "Kill")]
internal static class DramaBlessingPatch
{
    private static int _depth;

    internal static bool IsClosingDrama => _depth > 0;

    [HarmonyPrefix]
    private static void OnKill(global::Layer __instance, out bool __state)
    {
        __state = __instance is LayerDrama;
        if (__state) {
            _depth++;
        }
    }

    [HarmonyFinalizer]
    private static void OnKilled(bool __state)
    {
        if (__state) {
            _depth--;
        }
    }
}
