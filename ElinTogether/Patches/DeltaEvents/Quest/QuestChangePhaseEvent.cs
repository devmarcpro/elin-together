using ElinTogether.Helper;
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

        // a step to a phase this quest does not have: its task was left over from a phase that another game
        // moved on from (QuestChangePhaseDelta), and every kill "completed" it again. The journal threw
        // (KeyNotFoundException 'guild_fighter2', then 3, 4...) before the task could be dropped
        if (QuestPhaseRepair.IsMissing(__instance, a)) {
            EmpLog.Warning("Quest {QuestId} has no phase {Phase}, staying at {Current} and dropping its task",
                __instance.id, a, __instance.phase);
            __instance.task = null;
            __state = a;
            return false;
        }

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
        if (ElinDelta.IsApplying || __state == a || PersonalQuests.IsPersonal(__instance)) {
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

/// <summary>
///     A quest in steps (QuestSequence) reads its texts from the row "id + phase": a phase with no row throws at
///     every look at the journal. One that got there before the guard above (a world played with an older
///     version) is put back on the last phase it has: "joined" for a guild the group is a member of
/// </summary>
[HarmonyPatch(typeof(Quest), nameof(Quest.source), MethodType.Getter)]
internal static class QuestPhaseRepair
{
    internal static bool IsMissing(Quest quest, int phase)
    {
        if (quest is not QuestSequence || phase == 0) {
            return false;
        }

        // the row a quest reads at a phase is the quest's own business: the main quest has one row for all its
        // phases (QuestMain.idSource), and "main250" not existing kept the story from ever moving on
        var at = quest.phase;
        quest.phase = phase;
        try {
            return !EClass.sources.quests.map.ContainsKey(quest.idSource);
        } finally {
            quest.phase = at;
        }
    }

    [HarmonyPrefix]
    internal static void OnSource(Quest __instance)
    {
        if (!IsMissing(__instance, __instance.phase)) {
            return;
        }

        var from = __instance.phase;
        var phase = __instance is QuestGuild { guild.relation.type: FactionRelation.RelationType.Member }
            ? QuestGuild.Joined
            : from;
        while (phase > 0 && IsMissing(__instance, phase)) {
            phase--;
        }

        __instance.phase = phase;
        __instance.task = null;
        EmpLog.Warning("Quest {QuestId} was at phase {From}, which it does not have: back to {Phase}",
            __instance.id, from, phase);
    }
}
