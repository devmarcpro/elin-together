using System;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The flight of a thrown thing is drawn before the thing lands (ActThrow.Throw). In a session the picture of
///     a thing another player throws again and again (a ball) sometimes cannot be drawn: the exception stopped the
///     throw half way in this game, the thing never landed here. The flight is given up, the throw goes on
/// </summary>
[HarmonyPatch(typeof(EffectIRenderer), nameof(EffectIRenderer.OnUpdate))]
internal static class ThrowEffectGuardPatch
{
    [HarmonyFinalizer]
    internal static Exception? OnUpdateEnd(EffectIRenderer __instance, Exception? __exception)
    {
        if (__exception is null || NetSession.Instance.Connection is null) {
            return __exception;
        }

        EmpLog.Warning(__exception, "Flight of a thrown thing not drawn, the throw goes on");
        try {
            __instance.Kill();
        } catch (Exception) {
            // nothing left to stop
        }

        return null;
    }
}
