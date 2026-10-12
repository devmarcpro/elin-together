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
[HarmonyPatch(typeof(QuestVernis), nameof(QuestVernis.OnEnterZone))]
internal static class QuestVernisRepair
{
    private const string Boss = "vernis_boss";

    /// <summary>
    ///     Host, when the world is hosted
    /// </summary>
    internal static void Repair()
    {
        if (!EClass.core.IsGameStarted || EClass.game.quests.Get<QuestVernis>() is not { } quest) {
            return;
        }

        var floors = EClass.game.spatials.map.Values.OfType<Zone_VernisMine>().ToList();
        var reached = floors.Any(z => z.IsBossLv) ? 8 : floors.Any(z => z.lv < -1) ? 7 : 0;
        if (quest.phase >= reached) {
            return;
        }

        EmpLog.Information("The Vernis quest stood at phase {Phase} in a world whose mine was opened: put back at {Reached}",
            quest.phase, reached);
        quest.phase = reached;
        quest.task = null;
        quest.UpdateJournal();
    }

    [HarmonyPostfix]
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
}
