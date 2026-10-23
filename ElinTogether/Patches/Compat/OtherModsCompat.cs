using System;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Small guards around other mods that assume one game from start to end. A session replaces the game of a
///     client (joining, travelling) and removes it when it ends; what such a mod still holds from the old game
///     then throws every frame. Applied once, the first time a session starts, and left in place: the trouble
///     shows after the session
/// </summary>
internal static class OtherModsCompat
{
    private const string HarmonyId = ModInfo.Guid + ".compat";

    private static bool _applied;

    internal static void Apply()
    {
        if (_applied) {
            return;
        }

        _applied = true;

        // Somewhat Enhanced Display (Workshop 3781674985): its health bar reads the last hovered character every
        // frame, game or no game
        Guard("Somewhat Enhanced Display", "Macchacoffee.ElinMods.SomewhatEnhancedDisplay.UI.ModUI", "Update");

        // Same mod, its hover bars: while the guest's map is replaced (zone state, travel) the bar's Image/Text
        // objects are destroyed under it and every frame throws a NullReferenceException from UpdateValue
        // (found 2026-10-23, guest Player.log). The game is fine a frame later, so the NRE is swallowed there only
        Guard("Somewhat Enhanced Display", "Macchacoffee.ElinMods.SomewhatEnhancedDisplay.UI.HoverGuide.HealthBar", "Update", true);
    }

    private static void Guard(string modName, string typeName, string methodName, bool swallowNre = false)
    {
        try {
            if (AccessTools.TypeByName(typeName) is not { } type || AccessTools.Method(type, methodName) is not { } method) {
                return;
            }

            if (swallowNre) {
                new Harmony(HarmonyId).Patch(method, finalizer: new(typeof(OtherModsCompat), nameof(SwallowNre)));
            } else {
                new Harmony(HarmonyId).Patch(method, new(typeof(OtherModsCompat), nameof(OnlyWithAGame)));
            }

            EmpLog.Information("Compatibility guard set on {ModName}", modName);
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Compatibility guard for {ModName} could not be set", modName);
        }
    }

    private static Exception SwallowNre(Exception __exception)
    {
        return __exception is NullReferenceException ? null : __exception;
    }

    private static bool OnlyWithAGame()
    {
        return EClass.core?.game?.player?.chara is not null;
    }
}
