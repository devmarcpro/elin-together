using System.Collections.Generic;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The experience and stamina of a guest's throw are those of the game that plays it, the host's: noted there
///     and sent to that player (<see cref="ThrowGrowthDelta" />). The replay of its own throw in the guest's game,
///     which hits or misses by its own dice, teaches nothing and costs nothing, or it would count twice
/// </summary>
[HarmonyPatch]
internal static class ThrowGrowthPatch
{
    private static Chara? _thrower;
    private static bool _replay;
    private static readonly List<int> _elements = [];
    private static readonly List<int> _amounts = [];

    /// <summary>
    ///     Around the throw of an ActThrowDelta: on the host for another player, in a guest's game for its own
    /// </summary>
    internal static void Throw(ElinNetBase net, ElinDelta delta, Card card, System.Action throwIt)
    {
        if (card is not Chara thrower || _thrower is not null ||
            (net is ElinNetHost host
                ? !host.ActiveRemoteCharas.TryGetValue(delta.OriginPeer, out var sender) || sender != thrower
                : !thrower.IsPC)) {
            throwIt();
            return;
        }

        _thrower = thrower;
        _replay = !net.IsHost;
        _elements.Clear();
        _amounts.Clear();
        var stamina = thrower.stamina.value;
        try {
            throwIt();
        } finally {
            _thrower = null;
        }

        if (_replay) {
            thrower.stamina.value = stamina;
            return;
        }

        var spent = thrower.stamina.value - stamina;
        if (_elements.Count > 0 || spent < 0) {
            ((ElinNetHost)net).SendDeltaTo(delta.OriginPeer, new ThrowGrowthDelta {
                Elements = _elements.ToArray(),
                Amounts = _amounts.ToArray(),
                Stamina = spent,
            });
        }
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.ModExp), typeof(int), typeof(int))]
    internal static bool OnModExp(Card __instance, int ele, int a)
    {
        if (_thrower is null || __instance != _thrower) {
            return true;
        }

        if (_replay) {
            return false;
        }

        _elements.Add(ele);
        _amounts.Add(a);
        return true;
    }
}
