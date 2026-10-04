using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     The blessing of a god grows with the piety of "the player" and its days with that god; for anyone else
///     the game takes its level and its faith skill, as for a pet. A player who is not the host of the save is
///     not marked as "the player" (the mark is removed on purpose, it means "the host" in too many places): it
///     was blessed like a pet, in its own game too
/// </summary>
[HarmonyPatch(typeof(Chara), nameof(Chara.GetPietyValue))]
internal static class RemotePietyPatch
{
    [HarmonyPrefix]
    internal static bool OnGetPietyValue(Chara __instance, ref int __result)
    {
        // asked while a save is read too, before there is a player to compare with
        if (__instance._IsPC || NetSession.Instance.Connection is null || !EClass.core.IsGameStarted ||
            !__instance.IsPlayer) {
            return true;
        }

        __result = 10 + (int)(Mathf.Sqrt(__instance.c_daysWithGod) * 2f + __instance.Evalue(85)) / 2;
        return false;
    }
}
