using System;
using ElinTogether.Elements;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Chara), nameof(Chara.TickConditions))]
internal static class CharaTickConditionEvent
{
    [HarmonyPrefix]
    internal static bool OnCharaTickConditions(Chara __instance, bool __runOriginal)
    {
        // Harmony runs this prefix even after another one (TravelStepTurnsPatch) skipped the original: nothing is
        // ticked here then, and nothing is told (or it is told twice)
        if (!__runOriginal) {
            return false;
        }

        if (NetSession.Instance.Connection is not { } connection) {
            return true;
        }

        // only host and clients can tick conditions
        // host also relays it to all other clients
        if (__instance.ai is GoalRemote) {
            return false;
        }

        CharaTickConditionDelta.Emit(connection, __instance);

        return true;
    }

    extension(Chara chara)
    {
        [HarmonyReversePatch(HarmonyReversePatchType.Snapshot)]
        internal void Stub_TickConditions()
        {
            throw new NotImplementedException("Chara.TickConditions");
        }
    }
}