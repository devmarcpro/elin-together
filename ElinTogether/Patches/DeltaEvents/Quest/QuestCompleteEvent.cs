using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Quest), nameof(Quest.Complete))]
internal static class QuestCompleteEvent
{
    [HarmonyPrefix]
    internal static bool OnClientComplete(Quest __instance)
    {
        if (NetSession.Instance.IsHost) {
            return true;
        }

        CompleteQuietly(__instance, false);
        return false;
    }

    /// <summary>
    ///     The quest is done for the quest log, without the rewards: they go to the player who completed it,
    ///     where it completed it
    /// </summary>
    /// <param name="shared">on the host: fame and karma are the world's, whoever completed the quest</param>
    internal static void CompleteQuietly(Quest quest, bool shared)
    {
        var game = EClass.game;
        game.quests.Remove(quest);
        game.quests.completedIDs.Add(quest.id);
        game.quests.completedTypes.Add(quest.GetType().ToString());

        quest.ShowCompleteText();

        if (quest.chara?.quest?.uid == quest.uid) {
            quest.chara.quest = null;
        }

        quest.ClientZone?.completedQuests.Add(quest.uid);
        quest.isComplete = true;

        if (!shared) {
            return;
        }

        if (quest.FameOnComplete > 0) {
            EClass.player.ModFame(EClass.rndHalf(quest.FameOnComplete));
        }

        EClass.player.ModKarma(1);
    }

    [HarmonyPostfix]
    internal static void OnQuestComplete(Quest __instance)
    {
        if (ElinDelta.IsApplying) {
            return;
        }

        // travelling alone: the quest log is the world's, the host tells everyone
        QuestAwaySync.Send(new QuestCompleteDelta {
            Uid = __instance.uid,
        });

        if (NetSession.Instance.Connection is not { } connection) {
            return;
        }

        connection.Delta.AddRemote(new QuestCompleteDelta {
            Uid = __instance.uid,
        });
    }
}

/// <summary>
///     Quests of a player away from the host (travelling alone, or hosting a zone): accepted, advanced and
///     completed in its copy of the world, reported to the host, which keeps the one quest log of the world
/// </summary>
internal static class QuestAwaySync
{
    internal static void Send(ElinDelta delta)
    {
        if (NetSession.Instance is { IsZoneAuthority: true, Transport: ElinNetClient main }) {
            main.SendWhileAway(delta);
        }
    }
}

/// <summary>
///     Quest rewards drop where the player who completed the quest stands
/// </summary>
[HarmonyPatch(typeof(Player), nameof(Player.DropReward))]
internal static class QuestRewardPatch
{
    /// <summary>
    ///     Set by the host while it completes a quest for another player
    /// </summary>
    internal static Chara? Receiver { get; set; }

    [HarmonyPrefix]
    internal static bool OnDropReward(Thing t, ref Thing __result)
    {
        if (Receiver is not { isDead: false, IsAliveInCurrentZone: true } receiver) {
            return true;
        }

        t.things.DestroyAll();
        EClass._zone.AddCard(t, receiver.pos);
        __result = t;
        return false;
    }
}
