using System.Collections.Generic;
using ElinTogether.Elements;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     Combat on each player's own time: what fights a player (or its companions) only acts when that player
///     takes a turn, like in single player where time stands still while you think. Others keep playing meanwhile <br />
///     The host hands out the time: a player's turn grants act time to everything on its clock,
///     which no longer accumulates real time, see ActionModeCombat.AccumulateRoundTimer
/// </summary>
[HarmonyPatch]
internal static class PlayerCombatTime
{
    /// <summary>
    ///     The world must run a moment after a grant, for the granted turns to play out
    /// </summary>
    private const float HoldSeconds = 0.3f;

    private static float _lastGrant = -1f;

    // Council 13: the clock of a monster in a fight is the clock of the fastest player engaged with it, never the
    // sum of theirs. Engaged: the player it fights (TimeOwner), and any player who struck it within its own last
    // few turns. Counted in turns, never in seconds: a player who thinks stops nothing but its own stream
    //   _given: the act time handed to a monster so far; _stream: what each engaged player's turns add up to for it
    //   _struck: how many of its own turns a player still counts as engaged with a monster it struck
    private const int StruckTurns = 5;
    private static readonly Dictionary<int, float> _given = [];
    private static readonly Dictionary<(int Monster, int Player), float> _stream = [];
    private static readonly Dictionary<(int Monster, int Player), int> _struck = [];
    private static Map? _map;

    /// <summary>
    ///     A hostile act (melee, shot, throw, spell; hit or miss) in the game that simulates the map: its player,
    ///     or the player of the companion that did it, is engaged with the target. Without
    ///     this, a monster that fights one player was frozen for the other players who attacked it while the
    ///     first one stood still, and died without a fight (real games, 2026-10-10)
    /// </summary>
    internal static void Struck(Card target, Card? origin)
    {
        if (!HostActive || target is not Chara { IsPC: false, isDead: false } monster || monster.ai is GoalRemote ||
            PlayerOf(origin as Chara) is not { } player || PlayerOf(monster) == player) {
            return;
        }

        _struck[(monster.uid, player.uid)] = StruckTurns;
    }

    internal static bool Enabled => NetSession.Instance.Rules.UsePlayerCombatTime;

    /// <summary>
    ///     Only whoever simulates the map hands out time, and only with someone else on it
    /// </summary>
    private static bool HostActive => Enabled && NetSession.Instance.Connection is ElinNetHost &&
                                      NetSession.Instance.CurrentPlayers.Count >= 2;

    internal static bool HoldsWorld => HostActive && Time.unscaledTime - _lastGrant < HoldSeconds;

    internal static bool IsBound(Chara chara)
    {
        return HostActive && TimeOwner(chara) is not null;
    }

    /// <summary>
    ///     The player whose turns make this character act: the one it fights (or whose companion it fights),
    ///     its owner for a companion or a minion in a fight. None out of combat: world time
    /// </summary>
    internal static Chara? TimeOwner(Chara chara)
    {
        if (chara.IsPC || chara.isDead || chara.ai is GoalRemote || chara.enemy is not { isDead: false } foe) {
            return null;
        }

        var player = PlayerOf(foe) ?? PlayerOf(chara);
        return player is { isDead: false, IsAliveInCurrentZone: true } ? player : null;
    }

    private static Chara? PlayerOf(Chara? chara)
    {
        for (var depth = 0; depth < 4 && chara is not null; depth++) {
            // a player, or the owner of a companion
            if (CompanionHelper.OwnerOf(chara) is { } owner) {
                return owner;
            }

            // minions and summons follow their master
            chara = chara.master;
        }

        return null;
    }

    /// <summary>
    ///     A player took a turn: everything on its clock gets the time of that turn
    /// </summary>
    internal static void OnPlayerTurn(Chara player)
    {
        if (!HostActive || EClass.game?.activeZone?.map is not { } map) {
            return;
        }

        // the speed its own game computes. The copy kept here is no local player for the game and does not pay
        // what only the player pays: measured on an overloaded player, 52 at home and 105 here, so its monsters
        // got half the time they were due
        var speed = !player.IsPC && player.RemoteState is { Speed: > 0 } reported ? reported.Speed : player.Speed;

        var grant = EClass.player.baseActTime *
                    Mathf.Max(0.1f, (float)SynchronizationContext.RefSpeed / Mathf.Max(1, speed));

        // another map: what was noted is about monsters that are not here
        if (!ReferenceEquals(_map, map)) {
            _map = map;
            _given.Clear();
            _stream.Clear();
            _struck.Clear();
        }

        var granted = false;
        foreach (var chara in map.charas) {
            var key = (chara.uid, player.uid);
            var struck = _struck.TryGetValue(key, out var left) && left > 0;
            if (struck) {
                _struck[key] = left - 1;
            }

            // (a monster that fights nobody anymore is on world time again: nothing to hand out)
            if (TimeOwner(chara) is not { } owner || (owner != player && !struck)) {
                continue;
            }

            // the fastest engaged player sets the pace: this player's turns only count beyond what the monster
            // already got from the others. A player back after a pause starts one turn behind, not at zero: its
            // first turn gives nothing while someone else is playing, and everything if nobody is
            var given = _given.GetValueOrDefault(chara.uid);
            var stream = Mathf.Max(_stream.GetValueOrDefault(key), given - grant) + grant;
            _stream[key] = stream;
            if (stream > given) {
                chara.roundTimer += stream - given;
                _given[chara.uid] = stream;
                granted = true;
            }
        }

        if (granted) {
            _lastGrant = Time.unscaledTime;
        }
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Tick))]
    private static void CaptureTurnCount(Chara __instance, out int __state)
    {
        __state = __instance.IsPC && Enabled ? EClass.player.stats.turns : -1;
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Tick))]
    private static void ReportTurnConsumed(Chara __instance, int __state)
    {
        // an idle tick does not count turns, see Chara.Tick
        if (__state < 0 || EClass.player.stats.turns == __state) {
            return;
        }

        switch (NetSession.Instance.Connection) {
            case ElinNetHost:
                OnPlayerTurn(__instance);
                break;
            case ElinNetClient client:
                client.Delta.AddRemote(new PlayerTurnDelta());
                break;
        }
    }
}
