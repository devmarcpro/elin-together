using System.Linq;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     "Follow" on another player's character: the local character walks after it with the game's own click-to-move
///     (AI_Goto on the character), on the same map only. Nothing new goes on the wire: the steps are the ones a click
///     would make. Any key or click, a blow, a hostile in sight, a window, the other player leaving the map, dead or
///     gone stop it, with a line (llm-council 2026-10-24: never travels, no world map, a host option)
/// </summary>
[HarmonyPatch]
internal static class PlayerFollow
{
    private static Chara? _leader;
    private static Zone? _zone;
    private static Game? _game;
    private static int _hp;

    // the walk Follow started (a click of the player's own is not cancelled), and walks that got nowhere in a row
    private static AI_Goto? _walk;
    private static int _stuck;
    private static int _lastDist;

    // the click that chose Follow in the menu is not a "key to stop"
    private static int _armedFrame;

    internal static bool Enabled => NetSession.Instance.Rules.AllowFollow;

    /// <summary>
    ///     For the test bridge: who the local character follows, its uid or 0
    /// </summary>
    internal static int LeaderUid => _leader?.uid ?? 0;

    internal static void Start(Chara leader)
    {
        _leader = leader;
        _zone = EClass._zone;
        _game = EClass.game;
        _hp = EClass.pc.hp;
        _walk = null;
        _stuck = 0;
        _armedFrame = Time.frameCount + 2;
        Msg.Say("emp_follow_start".lang(leader.Name));
    }

    internal static void Stop(string key = "emp_follow_stop")
    {
        if (_leader is not { } leader) {
            return;
        }

        _leader = null;
        if (_walk is not null && EClass.pc.ai == _walk) {
            EClass.pc.ai.Cancel();
        }

        _walk = null;

        Msg.Say(key.lang(leader.Name));
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(AM_Adv), nameof(AM_Adv._OnUpdateInput))]
    internal static void OnUpdate()
    {
        if (_leader is not { } leader) {
            return;
        }

        // (a follow from a game since left: nothing to say about it)
        if (EClass.game != _game) {
            _leader = null;
            return;
        }

        var pc = EClass.pc;
        if (!Enabled || NetSession.Instance.Connection is null) {
            Stop();
        } else if (EClass._zone != _zone || leader.currentZone != EClass._zone || !EClass._map.charas.Contains(leader)) {
            Stop("emp_follow_left");
        } else if (leader.isDead || pc.isDead) {
            Stop();
        } else if (Time.frameCount > _armedFrame && (Input.anyKeyDown || EInput.leftMouse.down || EInput.rightMouse.down)) {
            Stop();
        } else if (pc.hp < _hp || EClass.ui.layers.Count > 0 ||
                   EClass._map.charas.Any(c => c.IsHostile(pc) && !c.isDead && c.Dist(pc) < 10 && pc.CanSee(c))) {
            Stop("emp_follow_danger");
        } else if (!pc.CanSee(leader) && pc.Dist(leader) > 12) {
            Stop("emp_follow_lost");
        } else if (pc.ai is NoGoal or GoalManualMove && pc.Dist(leader) > 2) {
            // a walk that ended no closer (no path: water, a wall) counts; a few in a row and the leader is out of reach
            var dist = pc.Dist(leader);
            _stuck = _walk is not null && dist >= _lastDist ? _stuck + 1 : 0;
            _lastDist = dist;
            if (_stuck >= 5) {
                Stop("emp_follow_lost");
                return;
            }

            // (the game's own click on a character: one step per turn, the path planned again each step)
            pc.SetAIImmediate(_walk = new AI_Goto(leader, 1));
        }

        _hp = Mathf.Max(_hp, pc.hp);
    }
}
