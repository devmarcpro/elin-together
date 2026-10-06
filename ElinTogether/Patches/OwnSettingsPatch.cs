using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A client leaves its game (link lost, back to the title): its own settings are noted as they are now, so
///     that it finds them when it joins again, see <see cref="OwnSettings" />
/// </summary>
[HarmonyPatch(typeof(Game), nameof(Game.Kill))]
internal static class OwnSettingsPatch
{
    [HarmonyPrefix]
    private static void OnKill()
    {
        OwnSettings.Keep();
    }
}
