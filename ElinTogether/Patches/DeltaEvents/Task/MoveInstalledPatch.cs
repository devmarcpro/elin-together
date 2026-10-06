using System.Linq;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;
using MessagePack;

namespace ElinTogether.Patches;

/// <summary>
///     Moving installed furniture in build mode (AM_Inspect): where it lands and its direction already reach the
///     others as cards, its height and free position did not, see <see cref="CardPoseDelta" />
/// </summary>
[HarmonyPatch(typeof(AM_MoveInstalled), nameof(AM_MoveInstalled.OnProcessTiles))]
internal static class MoveInstalledPatch
{
    // nothing is sent until the delta has its number in ElinDelta
    private static readonly bool Registered = typeof(ElinDelta)
        .GetCustomAttributes(typeof(UnionAttribute), false)
        .Cast<UnionAttribute>()
        .Any(union => union.SubType == typeof(CardPoseDelta));

    // the mode forgets its target once it is put down
    [HarmonyPrefix]
    internal static void OnMove(AM_MoveInstalled __instance, out Card? __state)
    {
        __state = __instance.target;
    }

    [HarmonyPostfix]
    internal static void OnMoved(Card? __state)
    {
        if (!Registered || ElinDelta.IsApplying || NetSession.Instance.Connection is not { } connection ||
            __state is not { isDestroyed: false, ExistsOnMap: true } card) {
            return;
        }

        connection.Delta.AddRemote(CardPoseDelta.Create(card));
    }
}
