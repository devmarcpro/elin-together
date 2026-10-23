using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     What a player summoned goes where that player goes, not where the host goes (audit 2026-10-23,
///     EmpConfig.Server.SummonsFollowMaster). When the host leaves its map, Elin takes off it every minion of
///     the party whose master is not the host, and carries over those of the host only (Chara.MoveZone,
///     player.listCarryoverMap). A player who comes along with the host (independent travel off, still loading
///     the map, or out of a quest zone) lost what it summoned, the host kept its own. Those minions are lent to
///     the host for that move: they are carried over the same way, then given back to their master. <br />
///     A player who stays behind takes the map with it, minions included (ElinNetHost.LeavePlayersBehind takes it
///     off this map before), and one who leaves alone takes them along, see ElinNetHost.TakeMinionsAlong
/// </summary>
[HarmonyPatch(typeof(Chara), nameof(Chara.MoveZone), typeof(Zone), typeof(ZoneTransition))]
internal static class SummonsFollowMaster
{
    internal static bool Enabled => NetSession.Instance.Connection is ElinNetHost && EmpConfig.Server.SummonsFollowMaster.Value;

    /// <summary>
    ///     The minions the game carries over when their master leaves a map (Chara.MoveZone)
    /// </summary>
    internal static bool IsCarriedMinion(Chara c, Chara master)
    {
        return c.c_uidMaster == master.uid && c.c_minionType == MinionType.Default && c != master;
    }

    // after CharaMoveZoneEvent: the host may refuse the move there, and the players staying are off the map by then
    [HarmonyPrefix]
    [HarmonyPriority(Priority.Last)]
    internal static void OnHostLeaves(Chara __instance, bool __runOriginal, out List<(Chara Minion, Chara Master)>? __state)
    {
        __state = null;
        if (!__runOriginal || !__instance.IsPC || EClass.player.simulatingZone || !Enabled || EClass._map is not { } map) {
            return;
        }

        foreach (var c in map.charas) {
            if (c.c_uidMaster == 0 || c.c_minionType != MinionType.Default || c.IsPC) {
                continue;
            }

            if (map.FindChara(c.c_uidMaster) is not { IsPC: false, IsPCParty: true } master || !master.IsPlayer) {
                continue;
            }

            (__state ??= []).Add((c, master));
            c.c_uidMaster = __instance.uid;
            c.master = __instance;
        }
    }

    [HarmonyFinalizer]
    internal static Exception? OnHostLeft(Exception? __exception, List<(Chara Minion, Chara Master)>? __state)
    {
        foreach (var (minion, master) in __state ?? []) {
            minion.c_uidMaster = master.uid;
            minion.master = master;
        }

        return __exception;
    }
}
