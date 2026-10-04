using System.Collections.Generic;
using System.Reflection;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     What a passing hour, day or month does to the WORLD (not to one map, not to one player) is done once, by
///     one game: the world keeper. Every game that simulates a map makes the date advance in its own copy of the
///     world (the host, and each player alone on a map it holds, see WorldDateAdvanceEvent), and each of them
///     ran these: a quest expired twice and cost fame twice, the month's tax cost karma twice, each copy drew
///     its own weather, salaries and parcels were made in copies that are thrown away. <br />
///     The keeper is the host for now. The role is meant to move, see dev/PLAN_serveur_depot.md
/// </summary>
[HarmonyPatch(typeof(Weather), nameof(Weather.OnChangeHour))]
internal static class WorldKeeper
{
    /// <summary>
    ///     This game does what time does to the world: no session, or the host of one. Not a player who joined
    ///     one, wherever it is
    /// </summary>
    internal static bool IsKeeper => NetSession.Instance.Transport is not ElinNetClient;

    /// <summary>
    ///     This game leaves the world's hooks to the keeper
    /// </summary>
    internal static bool Skip => !IsKeeper && NetSession.Instance.Rules.UseWorldKeeper;

    /// <summary>
    ///     The keeper's weather is the world's: nobody else draws one any more
    /// </summary>
    [HarmonyPostfix]
    internal static void OnWeatherHour(Weather __instance)
    {
        if (NetSession.Instance.Transport is not ElinNetHost host || !NetSession.Instance.Rules.UseWorldKeeper) {
            return;
        }

        host.Delta.AddRemote(WeatherDelta.Create(__instance));
    }
}

/// <summary>
///     The hooks of the world that only its keeper runs
/// </summary>
[HarmonyPatch]
internal static class WorldKeeperHooks
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        yield return AccessTools.Method(typeof(Weather), nameof(Weather.OnChangeHour));
        // expired quests: fame and karma
        yield return AccessTools.Method(typeof(QuestManager), nameof(QuestManager.OnAdvanceHour));
        yield return AccessTools.Method(typeof(Region), nameof(Region.CheckRandomSites));
        yield return AccessTools.Method(typeof(World), nameof(World.CreateDayData));
        yield return AccessTools.Method(typeof(Faction), nameof(Faction.OnAdvanceDay));
        // salary, tax bill, karma for unpaid bills
        yield return AccessTools.Method(typeof(Faction), nameof(Faction.OnAdvanceMonth));
        yield return AccessTools.Method(typeof(GameDate), nameof(GameDate.ShipLetter));
        yield return AccessTools.Method(typeof(GameDate), nameof(GameDate.ShipRandomPackages));
    }

    [HarmonyPrefix]
    internal static bool OnWorldHook()
    {
        return !WorldKeeper.Skip;
    }
}
