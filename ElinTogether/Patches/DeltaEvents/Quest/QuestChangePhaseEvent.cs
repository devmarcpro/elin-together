using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Quest), nameof(Quest.ChangePhase))]
internal class QuestChangePhaseEvent
{
    [HarmonyPrefix]
    internal static bool OnClientChangePhase(Quest __instance, int a, out int __state)
    {
        __state = __instance.phase;

        if (NetSession.Instance.IsHost) {
            return true;
        }

        __instance.phase = a;
        __instance.UpdateJournal();
        return false;
    }

    [HarmonyPostfix]
    internal static void OnChangePhase(Quest __instance, int a, int __state)
    {
        if (ElinDelta.IsApplying || __state == a) {
            return;
        }

        var delta = new QuestChangePhaseDelta {
            Uid = __instance.uid,
            Modifier = a,
            Id = __instance.id,
            From = __state,
        };

        // travelling alone: the quest log is the world's, the host tells everyone
        QuestAwaySync.Send(delta);

        // from a client: the host runs what the phase triggers, and tells the others
        NetSession.Instance.Connection?.Delta.AddRemote(delta);
    }
}
