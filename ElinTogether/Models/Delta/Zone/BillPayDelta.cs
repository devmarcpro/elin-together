using System;
using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

public enum BillAnswer : byte
{
    /// <summary>
    ///     A request, client to host
    /// </summary>
    None,

    /// <summary>
    ///     Paid, told to everyone: Payer, Id and Amount say what
    /// </summary>
    Done,

    /// <summary>
    ///     The bill is already paid, or not the sender's to pay
    /// </summary>
    Gone,

    /// <summary>
    ///     The sender's gold no longer covers it
    /// </summary>
    Poor,
}

/// <summary>
///     A bill (tax or delivery) put in the tax chest by a player who is not the host: the counters of the bills
///     (<c>player.taxBills</c>, <c>unpaidBill</c>) are the host's, a guest's copy of the world never has them. The guest
///     asks, the host reads the bill and the gold again, takes the gold of the sender, lowers its counter once and
///     tells everyone. A second request for the same bill finds it destroyed and is answered <see cref="BillAnswer.Gone" />,
///     before any gold moves
/// </summary>
[MessagePackObject]
public class BillPayDelta : ElinDelta
{
    // the last line shown, for the test bench
    internal static string LastLine = "";

    [Key(0)]
    public RemoteCard? Bill { get; init; }

    [Key(1)]
    public BillAnswer Answer { get; init; }

    [Key(2)]
    public string? Payer { get; init; }

    [Key(3)]
    public string? Id { get; init; }

    [Key(4)]
    public int Amount { get; init; }

    internal static void Send(Thing bill)
    {
        if (NetSession.Instance.Connection is ElinNetClient client) {
            client.Delta.AddRemote(new BillPayDelta { Bill = bill });
        }
    }

    /// <summary>
    ///     The host paid, or served a payment: the line is shown here and sent to every player
    /// </summary>
    internal static void Tell(ElinNetHost host, string payer, string id, int amount)
    {
        EmpLog.Information("Bill {Id} of {Amount} paid by {Payer}", id, amount, payer);
        host.SendDeltaToAllExcept(-1, new BillPayDelta { Answer = BillAnswer.Done, Payer = payer, Id = id, Amount = amount });
        Show(payer, id, amount);
    }

    private static void Show(string payer, string id, int amount)
    {
        var name = sources.things.map.TryGetValue(id, out var row) ? row.GetName() : id;
        Msg.Say(LastLine = "emp_ui_bill_paid".Loc(payer, name, Lang._currency(amount, "money")));
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Answer != BillAnswer.None) {
            if (net.IsClient) {
                OnAnswer();
            }

            return;
        }

        if (net is not ElinNetHost { IsZoneSession: false } host) {
            return;
        }

        // as the host's own gesture, so that the gold and the bill reach the players like any change made here
        using var simulate = Simulate();
        var sender = host.ActiveRemoteCharas.GetValueOrDefault(OriginPeer);
        var answer = sender is null || host.IsAwayPeer(OriginPeer) ? BillAnswer.Gone : Pay(host, sender);
        if (answer != BillAnswer.Done) {
            host.SendDeltaTo(OriginPeer, new BillPayDelta { Answer = answer });
        }
    }

    // all of it is read again from this game, whatever the sender believed
    private BillAnswer Pay(ElinNetHost host, Chara sender)
    {
        if (Bill?.Find() is not Thing { isDestroyed: false } bill || bill.id is not ("bill_tax" or "bill") || bill.c_bill <= 0 ||
            (bill.GetRootCard() is Chara { IsPlayer: true } holder && holder != sender)) {
            return BillAnswer.Gone;
        }

        var tax = bill.id == "bill_tax";
        if (tax && player.taxBills <= 0) {
            return BillAnswer.Gone;
        }

        var amount = bill.c_bill;
        if (sender.GetCurrency() < amount) {
            return BillAnswer.Poor;
        }

        sender.ModCurrency(-amount);
        if (tax) {
            player.stats.taxBillsPaid += amount;
            player.taxBills = Math.Max(0, player.taxBills - 1);
            // what the game gives back for the extra tax (InvOwnerDeliver.PayBill)
            if (bill.GetInt(35) / 1000 is > 0 and var gift) {
                world.SendPackage(ThingGen.CreateParcel("parcel_mysiliaGift", ThingGen.Create("money2", "copper").SetNum(gift)));
            }
        } else {
            player.unpaidBill -= amount;
        }

        bill.Destroy();
        Tell(host, sender.NameSimple, bill.id, amount);
        return BillAnswer.Done;
    }

    private void OnAnswer()
    {
        if (Answer == BillAnswer.Done) {
            SE.Pay();
            Show(Payer ?? "", Id ?? "", Amount);
            return;
        }

        SE.Beep();
        Msg.Say(Answer == BillAnswer.Poor ? "notEnoughMoney" : "emp_ui_bill_already_paid".Loc());
    }
}
