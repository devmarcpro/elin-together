using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A world whose Vernis quest was taken back after the mine (see <see cref="Models.QuestChangePhaseDelta" />,
///     2026-10-12) could not finish it: the game moves it on at the first entry of the boss floor (7 to 8) and at
///     the death of the boss (8 to 9), and neither comes twice. <br />
///     The mine itself tells how far the world went: its stairs open at phase 7, its boss floor is entered at 8.
///     The quest is put back there when the world is hosted, without playing the phases again (what they gave was
///     given). And the boss floor with no boss left moves the quest on as the death of the boss did
/// </summary>
[HarmonyPatch]
internal static class QuestVernisRepair
{
    private const string Boss = "vernis_boss";

    /// <summary>
    ///     Host, when the world is hosted
    /// </summary>
    internal static void Repair()
    {
        if (!EClass.core.IsGameStarted) {
            return;
        }

        var zones = EClass.game.spatials.map.Values;
        var mine = zones.OfType<Zone_VernisMine>().ToList();
        PutBack(EClass.game.quests.Get<QuestVernis>(), mine.Any(z => z.IsBossLv) ? 8 : mine.Any(z => z.lv < -1) ? 7 : 0);

        // Nymelle, the same way: the game opens the stairs under the first floor at step 1, those of the boss
        // floor at 2 and those under it, to the crystal, at 3 (Zone_Nymelle.LockExit)
        var nymelle = zones.OfType<Zone_Nymelle>().ToList();
        PutBack(EClass.game.quests.Get<QuestExploration>(),
            nymelle.Any(z => z.lv <= z.LvCrystal) ? 3 : nymelle.Any(z => z.lv <= z.LvBoss) ? 2 : nymelle.Any(z => z.lv < -2) ? 1 : 0);
    }

    private static void PutBack(Quest? quest, int reached)
    {
        if (quest is null || quest.phase >= reached) {
            return;
        }

        EmpLog.Information("Quest {QuestId} stood at step {Phase} in a world whose dungeon was opened further: put back at {Reached}",
            quest.id, quest.phase, reached);
        quest.phase = reached;
        quest.task = null;
        quest.UpdateJournal();
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(QuestVernis), nameof(QuestVernis.OnEnterZone))]
    internal static void OnEnterZone(QuestVernis __instance)
    {
        var session = NetSession.Instance;
        if (__instance.phase != 8 || EClass._zone is not Zone_VernisMine { IsBossLv: true } ||
            session.Transport is null || (session.Connection is ElinNetClient && !session.IsZoneAuthority) ||
            EClass._map.charas.Any(c => c is { id: Boss, isDead: false })) {
            return;
        }

        EmpLog.Information("The Vernis quest stood at phase 8 on a boss floor with no boss left: moved on");
        __instance.UpdateOnTalk();
    }

    /// <summary>
    ///     Lesimas, the same way: the death of its boss moves the quest from 5 to 6, in the one game that plays it
    ///     and only if that game's journal reads 5
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(QuestManager), nameof(QuestManager.OnEnterZone))]
    internal static void OnEnterAnyZone()
    {
        var session = NetSession.Instance;
        if (EClass._zone is not Zone_DungeonDead { IsBossLv: true } || EClass.game.quests.Get<QuestIntoDarkness>() is not { phase: 5 } quest ||
            session.Transport is null || (session.Connection is ElinNetClient && !session.IsZoneAuthority) ||
            EClass._map.charas.Any(c => c is { id: "azzrasizzle", isDead: false })) {
            return;
        }

        EmpLog.Information("The Lesimas quest stood at step 5 on a boss floor with no boss left: moved on");
        quest.UpdateOnTalk();
    }
}
