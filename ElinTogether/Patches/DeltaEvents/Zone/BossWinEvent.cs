using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The boss of the zone dies in the game that simulates it, see <see cref="BossWinDelta" />
/// </summary>
[HarmonyPatch(typeof(Chara), nameof(Chara.TryDropBossLoot))]
internal static class BossWinEvent
{
    [HarmonyPrefix]
    internal static void Before(Chara __instance, out Zone? __state)
    {
        __state = EClass._zone is { } zone && zone.uidBoss != 0 && zone.uidBoss == __instance.uid ? zone : null;
    }

    [HarmonyPostfix]
    internal static void After(Zone? __state)
    {
        var session = NetSession.Instance;
        if (__state is not { uidBoss: 0 } zone || session.Transport is null || ElinDelta.IsApplying ||
            (session.Connection is ElinNetClient && !session.IsZoneAuthority)) {
            return;
        }

        var delta = new BossWinDelta {
            ZoneUid = zone.uid,
            TopZoneUid = zone.GetTopZone().uid,
            Nefia = zone.IsNefia,
            DangerLv = zone.DangerLv,
        };

        // alone on a map of its own: the dungeon is the world's, the host tells everyone
        QuestAwaySync.Send(delta);
        session.Connection?.Delta.AddRemote(delta);
    }
}
