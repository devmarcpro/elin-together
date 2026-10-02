using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A wish is answered in the game of the one who makes it: the host has no dialog for another player. What a
///     client's game creates is gone at the end of the frame, the wish with it: what is wished for goes to the
///     host as a story gift does, see ZoneAddCardEvent
/// </summary>
[HarmonyPatch(typeof(ActEffect), nameof(ActEffect.Wish))]
internal static class ActEffectWishPatch
{
    internal static bool IsWishing { get; private set; }

    [HarmonyPrefix]
    internal static void OnWish()
    {
        IsWishing = NetSession.Instance.Connection is ElinNetClient;
    }

    [HarmonyFinalizer]
    internal static void OnWishEnd()
    {
        IsWishing = false;
    }
}
