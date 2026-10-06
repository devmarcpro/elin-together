using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal static class QuestGiveClientPatch
{
    [HarmonyPostfix]
    [HarmonyPatch(typeof(TraitChara), nameof(TraitChara.CanGiveRandomQuest), MethodType.Getter)]
    internal static void OnCanGiveRandomQuestToClient(TraitChara __instance, ref bool __result)
    {
        if (!__result) {
            return;
        }

        if (NetSession.Instance.Connection is null) {
            return;
        }

        // alone, the game's own pick: the player may be the one drawn to give a quest
        if (__instance.owner.IsPlayer && NetCompany.HasCompany) {
            __result = false;
        }
    }
}