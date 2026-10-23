using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Card), nameof(Card.ModCharge))]
internal static class CardChargeEvent
{
    [HarmonyPostfix]
    internal static void OnModCharge(Card __instance, int a)
    {
        if (a == 0) {
            return;
        }

        if (NetSession.Instance.Connection is not { } connection) {
            return;
        }

        if (__instance.isDestroyed || !CardCache.Contains(__instance)) {
            return;
        }

        // a guest's game owns its bag: what its own code does to the charges there (lockpick, tools, books) is
        // sent to the host, which sets it and passes it on. The value is absolute, the host's own copy of the same
        // change lands on the same number.
        if (!connection.IsHost) {
            if (__instance.GetRootCard() == EClass.pc && !PendingUid.IsPending(__instance.uid)) {
                connection.Delta.AddRemote(new CardChargeDelta {
                    Card = __instance,
                    Charges = __instance.c_charges,
                });
            }

            return;
        }

        // client will accept later
        connection.Delta.AddRemote(new CardChargeDelta {
            Card = __instance,
            Charges = __instance.c_charges,
        });
    }
}