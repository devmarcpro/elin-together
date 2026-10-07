using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Council 10, bills: the game's own <c>PayBill</c> reads the host's counters, which a guest's copy never has, and
///     answers "bad idea". A player of the host's map asks the host instead (see <see cref="BillPayDelta" />): its own
///     gold pays, the host's counter goes down once. The tax chest is also replayed in every game by
///     <see cref="InvOwnerOnProcessDelta" />: for a bill that replay is skipped (the host's would pay with nobody's gold,
///     another guest's would pay with its own). The host's own payment is told to everyone. Paid by the bank
///     (<c>fromBank</c>) or not a tax or delivery bill: the game's own
/// </summary>
[HarmonyPatch(typeof(InvOwnerDeliver), nameof(InvOwnerDeliver.PayBill))]
internal static class GuestPaysBillPatch
{
    private static bool IsBill(Thing t) => t.id is "bill_tax" or "bill";

    [HarmonyPrefix]
    internal static bool OnPayBill(Thing t, bool fromBank)
    {
        if (fromBank || !IsBill(t)) {
            return true;
        }

        // a player's own drop ends inside the answer to its item request (InvTransactionEvent): that one is its
        // gesture, not a replay, or a guest's bill was never paid
        if (ElinDelta.IsRemoteStateLanding) {
            return false;
        }

        if (NetSession.Instance.Connection is not ElinNetClient { IsZoneSession: false }) {
            return true;
        }

        BillPayDelta.Send(t);
        return false;
    }

    [HarmonyPostfix]
    internal static void OnPaid(Thing t, bool fromBank)
    {
        // a bill is destroyed only when paid: "bad idea" and "not enough gold" leave it
        if (fromBank || !IsBill(t) || !t.isDestroyed || ElinDelta.IsApplying) {
            return;
        }

        if (NetSession.Instance.Connection is ElinNetHost { IsZoneSession: false } host) {
            BillPayDelta.Tell(host, EClass.pc.NameSimple, t.id, t.c_bill);
        } else {
            // alone on another map the game paid by itself: the host's counter is still to lower
            BillPayDelta.SendAway(t);
        }
    }
}
