using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Removing a bridge or a sky floor drops the materials at the feet of "the player" and kicks it off the
///     removed tile (Map.MineFloor). For another player digging on this map that was this game's player: its
///     materials fell at our feet and we were the one who fell. The one who digs stands in as "the player" for
///     the call (the game it plays on makes its own drop too, which is not kept: only this game creates cards)
/// </summary>
[HarmonyPatch(typeof(Map), nameof(Map.MineFloor))]
internal static class RemoteMineFloorPatch
{
    [HarmonyPrefix]
    internal static void OnMineFloor(Chara? c, out Chara? __state)
    {
        __state = null;
        if (c is not { IsActiveRemoteChara: true } || EClass.player.chara == c) {
            return;
        }

        __state = EClass.player.chara;
        EClass.player.chara = c;
    }

    [HarmonyFinalizer]
    internal static void OnDone(Chara? __state)
    {
        if (__state is not null) {
            EClass.player.chara = __state;
        }
    }
}
