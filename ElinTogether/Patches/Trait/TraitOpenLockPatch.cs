using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The host rolls the lock another player picks, and the game gave it the rules of a resident: no refusal for a
///     lock too hard, one more chance in twenty, no karma for a lost property. It picks as the local player, which
///     keeps the karma for its player (see <see cref="PlayerStandIn" />). The lockpick is used up in the player's own
///     game, whose bag is authoritative: the host's copy keeps its charges (both games used it up)
/// </summary>
[HarmonyPatch]
internal static class TraitOpenLockPatch
{
    private static Chara? _picker;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Trait), nameof(Trait.TryOpenLock))]
    internal static void OnTryOpenLock(Chara cc, out (ScopeExit? standIn, ScopeExit? msg, Chara? picker) __state)
    {
        __state = default;

        if (NetSession.Instance.Connection is not ElinNetHost host || PlayerStandIn.IsActive ||
            host.ActiveRemoteCharas.FirstOrDefault(p => p.Value == cc) is not { Value: not null } peer) {
            return;
        }

        __state = (PlayerStandIn.For(host, peer.Key, cc), MsgRelayContext.RedirectTo(cc), _picker);
        _picker = cc;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Trait), nameof(Trait.TryOpenLock))]
    internal static void OnTryOpenLockEnd((ScopeExit? standIn, ScopeExit? msg, Chara? picker) __state)
    {
        if (__state.standIn is null) {
            return;
        }

        _picker = __state.picker;
        __state.msg?.Dispose();
        __state.standIn.Dispose();
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.ModCharge))]
    internal static bool OnModCharge(Card __instance)
    {
        return _picker is null || __instance.trait is not TraitLockpick || __instance.GetRootCard() != _picker;
    }
}
