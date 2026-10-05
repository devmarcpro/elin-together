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
///     "Don't wander": a companion does not run after an enemy "the player" cannot see. For the companion of another
///     player the game read the box of whoever simulates the map and measured from that player's eyes. Where the game
///     decides it (looking for an enemy, a step of combat), that companion gets its own master's box, and its own
///     master as "the player" when the box is ticked. Unticked, nothing else changes
/// </summary>
[HarmonyPatch]
internal static class RemoteDontWanderPatch
{
    private static ScopeExit? Lend(Chara? companion)
    {
        if (companion is null || NetSession.Instance.Connection is not ElinNetHost || companion.IsPC ||
            CompanionHelper.OwnerOf(companion) is not { IsRemotePlayer: true } owner || owner == companion ||
            PlayerTacticsDelta.DontWanderOf(owner) is not { } dontWander) {
            return null;
        }

        var tactics = EClass.game.config.tactics;
        var own = tactics.dontWander;
        tactics.dontWander = dontWander;
        var standIn = dontWander ? RemoteCraft.AsCrafter(owner) : null;
        return new() {
            OnExit = () => {
                standIn?.Dispose();
                tactics.dontWander = own;
            },
        };
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
