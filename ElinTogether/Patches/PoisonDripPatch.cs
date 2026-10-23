using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The poisoner's feat swaps a picked potion for a poison. A client cannot create things (its copy vanishes at the
///     end of the frame, and the potion it destroyed is lost): the host does the swap when it replays the pick for
///     that player (CharaPickThingDelta) and tells every game, with its own roll
/// </summary>
[HarmonyPatch(typeof(Chara), nameof(Chara.TryPoisonPotion))]
internal static class PoisonDripPatch
{
    [HarmonyPrefix]
    internal static bool OnTryPoisonPotion(Thing t, ref Thing __result)
    {
        if (NetSession.Instance.Connection is not ElinNetClient) {
            return true;
        }

        __result = t;
        return false;
    }
}
