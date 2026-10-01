using ElinTogether.Models;

namespace ElinTogether.Net;

/// <summary>
///     Shipping per player, see ElinNetHostShipping
/// </summary>
internal partial class ElinNetClient
{
    /// <summary>
    ///     Travelling alone (or hosting a zone): the shipping box here is a copy, the goods go to the real host
    /// </summary>
    internal bool ForwardShippingDeposit(Thing thing, int shipperUid)
    {
        if (!Session.IsAway || IsZoneSession) {
            return false;
        }

        Host.Send(new ShippingDeposit {
            Thing = LZ4Bytes.Create(thing),
            Shipper = shipperUid,
        });

        EmpLog.Debug("Sent {CardId} x{CardNum} to the shipping box of the host for chara {Uid}",
            thing.id, thing.Num, shipperUid);

        // it is in the box of the host now
        thing.Destroy();
        return true;
    }

    /// <summary>
    ///     The boxes shared by the whole world (shipping, deliveries, bank) are the host's: empty in the copy
    ///     of a travelling player, taking from a copy would duplicate what the host still has
    /// </summary>
    private static void EmptyWorldContainers()
    {
        Thing?[] containers = [
            game.cards.container_shipping,
            game.cards.container_deliver,
            game.cards.container_deposit,
        ];

        foreach (var container in containers) {
            if (container is null) {
                continue;
            }

            foreach (var thing in container.things.ToArray()) {
                thing.Destroy();
            }
        }
    }

    /// <summary>
    ///     Net event: the morning sale of our goods
    /// </summary>
    private void OnShippingPayout(ShippingPayout payout)
    {
        if (IsZoneSession) {
            return;
        }

        // right after arriving on the host map the zone may still be loading
        this.StartDeferredCoroutine(() => ApplyShippingPayout(payout),
            () => core.IsGameStarted && game.activeZone?.map is not null && pc is not null);
    }

    private void ApplyShippingPayout(ShippingPayout payout)
    {
        var result = new ShippingResult {
            ints = [..payout.Ints],
        };
        foreach (var strs in payout.ItemStrs) {
            result.items.Add(new() {
                _strs = strs,
            });
        }

        player.shippingResults.Add(result);
        while (player.shippingResults.Count > 10) {
            player.shippingResults.RemoveAt(0);
        }

        player.stats.shipNum = (int)System.Math.Min(payout.ShipNum, int.MaxValue);
        player.stats.shipMoney = payout.ShipMoney;

        if (!Session.IsAway && payout.BranchLv > 0 && (game.spatials.Find(result.uidZone) ?? pc.homeZone)?.branch is { } branch) {
            branch.lv = payout.BranchLv;
            branch.exp = payout.BranchExp;
        }

        // our currency is ours to change, wherever we are (on the host map the host hears of it,
        // see CardModCurrencyEvent)
        AddCurrencyLocal("money", payout.Money);
        AddCurrencyLocal("money2", payout.Bonus);

        if (result.items.Count > 0) {
            player.showShippingResult = core.config.game.showShippingResult;
        }

        EmpLog.Information("Shipping paid {ShipIncome} for {ShipItemCount} goods, received here {ShipLocal}",
            result.GetIncome(), result.items.Count, payout.Money);
    }

    private static void AddCurrencyLocal(string id, long amount)
    {
        while (amount > 0) {
            var part = (int)System.Math.Min(amount, int.MaxValue);
            amount -= part;
            pc.ModCurrency(part, id);
        }
    }
}
