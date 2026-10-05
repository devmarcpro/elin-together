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

    private static bool? _sent;
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
            _sent = null;
            return;
        }

        if (_to == client && _sent == tactics.allyKeepDistance && Time.unscaledTime < _next) {
            return;
        }

        _to = client;
        _sent = tactics.allyKeepDistance;
        _next = Time.unscaledTime + ResendSeconds;
        client.Delta.AddRemote(new PlayerTacticsDelta {
            AllyKeepDistance = tactics.allyKeepDistance,
        });
    }
}
