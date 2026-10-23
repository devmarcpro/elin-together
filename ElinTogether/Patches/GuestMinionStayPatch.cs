using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     When the player of the host walks out of a map, Elin takes out of it every minion of the party that is not
///     its own (Chara.MoveZone), the party being the host's. The summons and raised dead of a guest who stays are
///     in that party too: they stay with their master, only the minions of the host leave with the host
/// </summary>
[HarmonyPatch]
internal static class GuestMinionStayPatch
{
    // the lambda of that loop: c => c.IsPCPartyMinion && c.master != EClass.pc
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return typeof(Chara).GetNestedTypes(AccessTools.all)
            .SelectMany(t => t.GetMethods(AccessTools.all))
            .Where(m => m.Name.Contains("<MoveZone>") && PatchProcessor.GetOriginalInstructions(m)
                .Any(c => c.operand is MethodBase { Name: "get_IsPCPartyMinion" }));
    }

    [HarmonyPostfix]
    internal static void OnLeaveCheck(ref bool __result, Chara __0)
    {
        if (!__result || NetSession.Instance.Connection is not ElinNetHost) {
            return;
        }

        // the master at the end of the chain (a minion of a minion belongs to the same player)
        var owner = __0.master;
        for (var depth = 0; owner?.master is { } above && depth < 8; depth++) {
            owner = above;
        }

        if (owner is { IsRemotePlayer: true }) {
            __result = false;
        }
    }
}
