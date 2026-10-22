using System.Collections.Generic;
using System.Linq;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     Auto combat in the host's game, which makes all the damage: the game reads "the player" (its auto combat, its
///     tactics 135, its "invulnerable this turn", its stamina). The host's auto combat saved every player and
///     companion, a guest's saved no one. Each one hit now takes these from the player it belongs to (itself or its
///     master): the host for the host's, the guest's own auto combat for a guest's (<see cref="AutoCombatDelta" />),
///     no one for a party member that is no one's (council, 2026-10-22). Host box "auto_combat_per_player"
/// </summary>
[HarmonyPatch]
internal static class AutoCombatPerPlayerPatch
{
    private const float ResendSeconds = 10f;

    private sealed class State
    {
        internal required GoalAutoCombat Goal { get; init; }
        internal bool Invulnerable { get; set; }
    }

    // remote player uid -> its auto combat, as it told it
    private static readonly Dictionary<int, State> States = [];

    // an auto combat can last less than a frame (no enemy left to hit): its end is told once it has been gone a while
    private const float StopSeconds = 1f;

    private static GoalAutoCombat? _sent;
    private static ElinNetClient? _to;
    private static float _next;
    private static float _seen;

    internal static void Set(Chara player, HashSet<int>? healthy)
    {
        if (healthy is null) {
            States.Remove(player.uid);
            return;
        }

        // a goal that is never run, only read for its list (its constructor writes "the player")
        var goal = (GoalAutoCombat)RuntimeHelpers.GetUninitializedObject(typeof(GoalAutoCombat));
        goal.listHealthy = healthy.Select(uid => EClass.game.cards.globalCharas.Find(uid) ?? EClass._map?.FindChara(uid))
            .Where(c => c is not null).ToList();
        // (the game keeps "invulnerable" until the player's next turn: here until its auto combat is over)
        States[player.uid] = new() { Goal = goal, Invulnerable = States.TryGetValue(player.uid, out var old) && old.Invulnerable };
    }

    /// <summary>
    ///     A guest's auto combat begins: the host knows it at once (when it is given to the player, not when it is
    ///     made: the game also makes one to show what a right click on an enemy would do)
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.SetAI))]
    internal static void OnStart(Chara __instance, AIAct g)
    {
        if (g is GoalAutoCombat goal && goal != _sent && __instance.IsPC && NetSession.Instance.Connection is ElinNetClient client) {
            Tell(client, goal);
        }
    }

    private static void Tell(ElinNetClient client, GoalAutoCombat? goal)
    {
        _to = client;
        _sent = goal;
        _seen = Time.unscaledTime;
        _next = Time.unscaledTime + ResendSeconds;
        client.Delta.AddRemote(new AutoCombatDelta { Healthy = goal is null ? null : AutoCombatDelta.Of(goal) });
    }

    /// <summary>
    ///     ... and when it stopped, and again now and then (a first word may arrive before its character is there, a
    ///     host that came back has forgotten)
    /// </summary>
    internal static void Update()
    {
        if (NetSession.Instance.Connection is not ElinNetClient client || EClass.pc is not { } pc) {
            _sent = null;
            _to = null;
            return;
        }

        if (pc.ai is GoalAutoCombat goal) {
            _seen = Time.unscaledTime;
            if (_to != client || goal != _sent || Time.unscaledTime >= _next) {
                Tell(client, goal);
            }
        } else if (_to != client || (_sent is not null && Time.unscaledTime - _seen >= StopSeconds) ||
                   (_sent is null && Time.unscaledTime >= _next)) {
            Tell(client, null);
        }
    }

    /// <summary>
    ///     The player whose auto combat counts for this one: null when it is no one's, the game's "the player" outside
    ///     the host's game or with the box unticked
    /// </summary>
    private static Chara? OwnerOf(Card card)
    {
        if (NetSession.Instance.Connection is not ElinNetHost || !EmpConfig.Server.AutoCombatPerPlayer.Value) {
            return EClass.pc;
        }

        return card is Chara chara ? CompanionHelper.OwnerOf(chara) : null;
    }

    /// <summary>
    ///     What a player still here said (one who left mid-fight never says it stopped)
    /// </summary>
    private static State? StateOf(Chara owner)
    {
        return NetSession.Instance.Connection is ElinNetHost host && host.ActiveRemoteCharas.ContainsValue(owner) &&
               States.TryGetValue(owner.uid, out var state)
            ? state
            : null;
    }

    internal static AIAct? GoalOf(Card card)
    {
        return OwnerOf(card) switch {
            null => null,
            var owner when owner == EClass.pc => EClass.pc.ai,
            var owner => StateOf(owner)?.Goal,
        };
    }

    internal static Chara PlayerOf(Card card)
    {
        return OwnerOf(card) ?? EClass.pc;
    }

    internal static bool IsInvulnerable(Card card)
    {
        return OwnerOf(card) switch {
            null => false,
            var owner when owner == EClass.pc => EClass.player.invlunerable,
            var owner => StateOf(owner)?.Invulnerable ?? false,
        };
    }

    internal static void SetInvulnerable(Card card, bool value)
    {
        var owner = OwnerOf(card);
        if (owner == EClass.pc) {
            EClass.player.invlunerable = value;
        } else if (owner is not null && StateOf(owner) is { } state) {
            state.Invulnerable = value;
        }
    }

    internal static bool TryAbort(Card card, bool immediate)
    {
        var owner = OwnerOf(card);
        if (owner == EClass.pc) {
            return EClass.player.TryAbortAutoCombat(immediate);
        }

        if (owner is null || NetSession.Instance.Connection is not ElinNetHost host ||
            host.ActiveRemoteCharas.FirstOrDefault(kv => kv.Value == owner) is not { Value: not null } peer) {
            return false;
        }

        // its game stops its auto combat and pays: the stamina of a player is its own game's
        host.SendDeltaTo(peer.Key, new AutoCombatDelta { Saved = true, Self = card == owner });
        return true;
    }

    [HarmonyTranspiler]
    [HarmonyPatch(typeof(Card), nameof(Card.DamageHP), typeof(long), typeof(int), typeof(int), typeof(AttackSource), typeof(Card),
        typeof(bool), typeof(Thing), typeof(Chara), typeof(int))]
    internal static IEnumerable<CodeInstruction> OnDamageHP(IEnumerable<CodeInstruction> instructions)
    {
        var getPc = AccessTools.PropertyGetter(typeof(EClass), nameof(EClass.pc));
        var getPlayer = AccessTools.PropertyGetter(typeof(EClass), nameof(EClass.player));
        var ai = AccessTools.Field(typeof(Chara), nameof(Chara.ai));
        var getStamina = AccessTools.PropertyGetter(typeof(Chara), nameof(Chara.stamina));
        var invulnerable = AccessTools.Field(typeof(Player), nameof(Player.invlunerable));
        var abort = AccessTools.Method(typeof(Player), nameof(Player.TryAbortAutoCombat));
        var list = instructions.ToList();
        var changed = 0;

        void Swap(int at, int remove, params CodeInstruction[] with)
        {
            with[0].labels.AddRange(list[at].labels);
            list.RemoveRange(at, remove);
            list.InsertRange(at, with);
            changed++;
        }

        CodeInstruction Me() => new(OpCodes.Ldarg_0);
        CodeInstruction Call(string name) => new(OpCodes.Call, AccessTools.Method(typeof(AutoCombatPerPlayerPatch), name));

        for (var i = 0; i < list.Count - 2; i++) {
            var next = list[i + 1];
            if (list[i].Calls(getPc)) {
                // EClass.pc.ai is / as GoalAutoCombat (not the practice dummy's)
                if (next.LoadsField(ai) && list[i + 2].opcode == OpCodes.Isinst && list[i + 2].operand as System.Type == typeof(GoalAutoCombat)) {
                    Swap(i, 2, Me(), Call(nameof(GoalOf)));
                } else if (next.LoadsConstant(135) || next.Calls(getStamina)) {
                    Swap(i, 1, Me(), Call(nameof(PlayerOf)));
                }
            } else if (list[i].Calls(getPlayer)) {
                if (next.LoadsField(invulnerable)) {
                    Swap(i, 2, Me(), Call(nameof(IsInvulnerable)));
                } else if (list[i + 2].StoresField(invulnerable)) {
                    Swap(i, 3, Me(), next, Call(nameof(SetInvulnerable)));
                } else if (list[i + 2].Calls(abort)) {
                    Swap(i, 3, Me(), next, Call(nameof(TryAbort)));
                }
            }
        }

        // two "auto combat", one "as", 135, two stamina, two reads and one write of invulnerable, the abort
        if (changed != 10) {
            EmpLog.Warning("Auto combat per player: {Changed} places of 10 found in DamageHP", changed);
        }

        return list;
    }
}
