using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Card), nameof(Card.TryStackTo))]
internal static class CardTryStackEvent
{
    [HarmonyPrefix]
    internal static bool OnCardTryStackTo(Card __instance, Thing to, ref bool __result)
    {
        if (NetSession.Instance.Connection is not ElinNetClient client) {
            return true;
        }

        if (PendingSplit.Resolve(__instance.uid) == to.uid) {
            return true;
        }

        if (to.IsHostOwned != __instance.IsHostOwned) {
            return false;
        }

        if (!to.IsHostOwned) {
            return true;
        }

        if (!__instance.CanStackTo(to)) {
            return false;
        }

        // state landing from the network stacks here. The player's own take out of a chest, a shop or the bank
        // (resumed inside the answer to its item request) is asked like a pick-up from the ground: the host
        // replays the pick for a character that is not its own, at the root of the bag, and never found the
        // stack of a purse or a sub-bag: the gold a guest took out of the bank was missing in its own game
        if (ElinDelta.IsRemoteStateLanding) {
            return true;
        }

        __result = true;
        client.Delta.AddRemote(new CardTryStackToDelta {
            Card = __instance,
            To = to,
            Parent = to.parent as Card,
        });

        return false;
    }
}