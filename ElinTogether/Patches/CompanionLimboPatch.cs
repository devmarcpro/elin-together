using System;
using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Players away from the host and the companions travelling with them have no zone in its world on purpose,
///     see ElinNetHostTravel and ElinNetHostCompanions <br />
///     Elin sends any home branch member without a zone back home on load (Game.OnLoad): not those
/// </summary>
[HarmonyPatch]
internal static class CompanionLimboPatch
{
    private static bool _loading;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Game), nameof(Game.OnLoad))]
    internal static void OnLoadStart()
    {
        _loading = true;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Game), nameof(Game.OnLoad))]
    internal static Exception? OnLoadEnd(Exception? __exception)
    {
        _loading = false;
        return __exception;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.MoveZone), typeof(Zone), typeof(ZoneTransition))]
    internal static bool OnMoveHomeOnLoad(Chara __instance)
    {
        return !_loading || __instance.IsPC || __instance.currentZone is not null ||
               (__instance.CompanionOwnerUid == 0 && !__instance.GetBool("remote_chara"));
    }
}
