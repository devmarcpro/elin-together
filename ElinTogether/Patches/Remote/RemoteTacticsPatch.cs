using System.Reflection;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     How far a companion may stay from its master follows the setting of the player it belongs to, see
///     <see cref="PlayerTacticsDelta" />
/// </summary>
[HarmonyPatch(typeof(ConfigTactics), nameof(ConfigTactics.AllyDistance))]
internal static class RemoteTacticsPatch
{
    private const float ResendSeconds = 10f;

    private static int _sent = -1;
    private static ElinNetClient? _to;
    private static float _next;

    [HarmonyPrefix]
    internal static bool OnAllyDistance(Chara c, ref int __result)
    {
        if (NetSession.Instance.Connection is not ElinNetHost || EClass._zone.IsRegion ||
            CompanionHelper.OwnerOf(c) is not { IsRemotePlayer: true } owner ||
            PlayerTacticsDelta.KeepDistanceOf(owner) is not { } keepDistance) {
            return true;
        }

        __result = keepDistance && EClass._zone.KeepAllyDistance ? 5 : c.DestDist;
        return false;
    }

    /// <summary>
    ///     This game's player tells the game it plays on: when it changes, and again now and then (the first one may
    ///     arrive before its character is known there)
    /// </summary>
    internal static void Update()
    {
        if (NetSession.Instance.Connection is not ElinNetClient client || EClass.game?.config?.tactics is not { } tactics) {
            _sent = -1;
            return;
        }

        var boxes = (tactics.allyKeepDistance ? 1 : 0) + (tactics.dontWander ? 2 : 0);
        if (_to == client && _sent == boxes && Time.unscaledTime < _next) {
            return;
        }

        _to = client;
        _sent = boxes;
        _next = Time.unscaledTime + ResendSeconds;
        client.Delta.AddRemote(new PlayerTacticsDelta {
            AllyKeepDistance = tactics.allyKeepDistance,
            DontWander = tactics.dontWander,
        });
    }
}

/// <summary>
///     The companion of another player is run by whoever simulates the map, where "the player" is that one: it ran
///     after enemies only that one saw and held back for its tactics, took from its bag, fished beside it. Where the
///     game decides (an idle step, looking for an enemy, a step of combat), that companion has its own master as
///     "the player" when that master stands on this map, and its master's "don't wander" box once it was told
/// </summary>
[HarmonyPatch]
internal static class RemoteDontWanderPatch
{
    private static ScopeExit? Lend(Chara? companion)
    {
        if (companion is null || NetSession.Instance.Connection is not ElinNetHost || companion.IsPC ||
            CompanionHelper.OwnerOf(companion) is not { IsRemotePlayer: true, IsAliveInCurrentZone: true } owner ||
            owner == companion) {
            return null;
        }

        var tactics = EClass.game.config.tactics;
        var own = tactics.dontWander;
        tactics.dontWander = PlayerTacticsDelta.DontWanderOf(owner) ?? own;
        var standIn = RemoteCraft.AsCrafter(owner);
        return new() {
            OnExit = () => {
                standIn.Dispose();
                tactics.dontWander = own;
            },
        };
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(AI_Idle), nameof(AI_Idle.Run), MethodType.Enumerator)]
    internal static void OnIdleStep(object __instance, out ScopeExit? __state)
    {
        // every idle character of the map steps here: the field is looked up once
        _idleSelf ??= AccessTools.Field(__instance.GetType(), "<>4__this");
        __state = NetSession.Instance.Connection is ElinNetHost ? Lend((_idleSelf.GetValue(__instance) as AI_Idle)?.owner) : null;
    }

    private static FieldInfo? _idleSelf;

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(AI_Idle), nameof(AI_Idle.Run), MethodType.Enumerator)]
    internal static void OnIdleStepEnd(ScopeExit? __state)
    {
        __state?.Dispose();
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.FindNewEnemy))]
    internal static void OnFindNewEnemy(Chara __instance, out ScopeExit? __state)
    {
        __state = Lend(__instance);
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Chara), nameof(Chara.FindNewEnemy))]
    internal static void OnFindNewEnemyEnd(ScopeExit? __state)
    {
        __state?.Dispose();
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(GoalCombat), nameof(GoalCombat.Run), MethodType.Enumerator)]
    internal static void OnCombatStep(object __instance, out ScopeExit? __state)
    {
        __state = Lend(Traverse.Create(__instance).Field<GoalCombat>("<>4__this").Value?.owner);
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(GoalCombat), nameof(GoalCombat.Run), MethodType.Enumerator)]
    internal static void OnCombatStepEnd(ScopeExit? __state)
    {
        __state?.Dispose();
    }
}
