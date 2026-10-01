using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Quest), nameof(Quest.Fail))]
internal static class QuestFailEvent
{
    [HarmonyPostfix]
    internal static void OnQuestFail(Quest __instance)
    {
        if (ElinDelta.IsApplying) {
            return;
        }

        var delta = new QuestFailDelta {
            Uid = __instance.uid,
        };

        // travelling alone: the quest log is the world's, the host tells everyone
        QuestAwaySync.Send(delta);

        // a client on the host map fails it at the same hour as the host, the host is the one telling
        if (NetSession.Instance.Connection is ElinNetHost host) {
            host.Delta.AddRemote(delta);
        }
    }

    /// <summary>
    ///     Gone from the quest log, without what a failure costs: that is counted once, by the host
    /// </summary>
    internal static void FailQuietly(Quest quest)
    {
        Msg.Say("questExpired", quest.GetTitle());
        EClass.Sound.Play("questFail");

        EClass.game.quests.Remove(quest);

        if (quest.chara?.quest?.uid == quest.uid) {
            quest.chara.quest = null;
        }

        quest.ClientZone?.completedQuests.Add(quest.uid);
    }
}
