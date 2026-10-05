using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Helper.Extensions;
using ElinTogether.Models;
using ElinTogether.Net.Steam;
using UnityEngine;

namespace ElinTogether.Net;

/// <summary>
///     Shipping per player: the morning sale pays every player for the goods it put in the box. <br />
///     Only the money is personal: the shipping total and its bonus tiers are one progression for the world
///     (the bonus of a tier goes to the player whose sale reaches it), like the hearth experience of the base
/// </summary>
internal partial class ElinNetHost
{
    private const int AccountOwedMoney = 0;
    private const int AccountOwedBonus = 1;

    /// <summary>
    ///     Player chara uid -> money and bonus not handed over yet
    ///     (the player was a guest somewhere or offline when its goods were sold)
    /// </summary>
    [ElinGameIOProperty("shipping_owed")]
    private static Dictionary<int, long[]> ShippingAccounts
    {
        get => field ??= [];
        set;
    }

    private static long[] GetShippingAccount(int charaUid)
    {
        if (!ShippingAccounts.TryGetValue(charaUid, out var account) || account.Length < 2) {
            account = ShippingAccounts[charaUid] = new long[2];
        }

        return account;
    }

    /// <summary>
    ///     Zone session host: the shipping box here is a copy, the goods go to the real host
    /// </summary>
    internal bool ForwardShippingDeposit(Thing thing, int shipperUid)
    {
        return IsZoneSession && Session.Transport is ElinNetClient main && main.ForwardShippingDeposit(thing, shipperUid);
    }

    /// <summary>
    ///     Net event: a player away from the host map put an item in the shipping box
    /// </summary>
    private void OnShippingDeposit(ShippingDeposit deposit, ISteamNetPeer peer)
    {
        if (IsZoneSession || !SavedRemoteCharas.TryGetValue(peer.User, out var own)) {
            return;
        }

        // a player ships for itself, the owner of a zone for its guests too
        var forGuest = _guests.Any(kv => kv.Value.HolderId == peer.Id &&
                                         Socket.Peers.FirstOrDefault(p => p.Id == kv.Key) is { } guest &&
                                         SavedRemoteCharas.GetValueOrDefault(guest.User) == deposit.Shipper);
        var shipper = forGuest ? deposit.Shipper : own;

        var thing = deposit.Thing.Decompress<Thing>();
        // its uid comes from another world
        foreach (var card in thing.things.Flatten().Prepend(thing)) {
            game.cards.AssignUID(card);
        }

        CardCache.Add(thing);
        Delta.AddRemote(CardGenDelta.Create(thing));

        switch (deposit.Box) {
            case ShippingHelper.BoxDelivery:
                game.cards.container_deliver.AddThing(thing);
                break;
            case ShippingHelper.BoxBank:
                game.cards.container_deposit.AddThing(thing);
                break;
            default:
                ShippingHelper.ShipperOverride = shipper;
                try {
                    game.cards.container_shipping.AddThing(thing);
                } finally {
                    ShippingHelper.ShipperOverride = null;
                }

                break;
        }

        EmpLog.Debug("Player {@Peer} shipped {CardId} x{CardNum} from afar for chara {Uid}",
            peer, thing.id, thing.Num, shipper);
    }

    /// <summary>
    ///     Before the host sells the box (GameDate.ShipGoods): sell the goods of the other players for them
    /// </summary>
    internal void ShipPlayersGoods()
    {
        if (IsZoneSession || !Session.Rules.UsePlayerShipping || game.cards.container_shipping is not { } box) {
            return;
        }

        var zone = game.spatials.Find(player.uidLastShippedZone);
        if (zone?.branch is null) {
            zone = pc.homeZone;
        }

        if (zone?.branch is null) {
            return;
        }

        var players = SavedRemoteCharas.Values.Concat(PlayerRosters.Values.SelectMany(roster => roster)).ToHashSet();
        var goods = box.things
            .Where(t => t.trait.CanBeShipped && players.Contains(t.ShipperUid))
            .GroupBy(t => t.ShipperUid)
            .ToList();

        foreach (var group in goods) {
            ShipFor(group.Key, group.ToList(), zone);
        }
    }

    private void ShipFor(int shipperUid, List<Thing> goods, Zone zone)
    {
        var account = GetShippingAccount(shipperUid);
        var result = new ShippingResult {
            rawDate = world.date.GetRaw(),
            uidZone = zone.uid,
            total = player.stats.shipMoney,
            hearthLv = zone.branch.lv,
            hearthExp = zone.branch.exp,
        };

        long income = 0;
        var count = 0;
        var exp = 0;
        // the price reads "the player's" god (Card.GetPrice: Kumiromi, Ehekatl): the shipper's, not the host's
        var self = player.chara;
        Dictionary<Thing, int> prices;
        try {
            player.chara = game.cards.globalCharas.Find(shipperUid) ?? self;
            prices = goods.ToDictionary(t => t, t => t.GetPrice(CurrencyType.Money, true, PriceType.Shipping));
        } finally {
            player.chara = self;
        }

        foreach (var thing in goods) {
            // same numbers as GameDate.ShipGoods
            var price = prices[thing];
            var sum = (long)price * thing.Num;
            income += sum;
            count += thing.Num;
            exp += EClass.rndHalf(thing.Num * Mathf.Min(15 + price, 10000) / 100 + 1);
            result.items.Add(new() {
                text = thing.Name,
                income = sum,
            });
        }

        exp = zone.branch.policies.IsActive(2515) ? 0 : exp / 2 + 1;
        result.hearthExpGained = exp;

        // one shipping total for the world, the bonus of a tier goes to whoever reaches it
        var bonusBefore = player.stats.GetShippingBonus(player.stats.shipMoney);
        player.stats.shipNum += count;
        player.stats.shipMoney += income;
        var bonus = Math.Max(0, player.stats.GetShippingBonus(player.stats.shipMoney) - bonusBefore);

        foreach (var thing in goods) {
            thing.Destroy();
        }

        // the base is everyone's
        zone.branch.statistics.ship += income;
        zone.branch.ModExp(exp);

        account[AccountOwedMoney] += income;
        account[AccountOwedBonus] += bonus;

        EmpLog.Information("Shipped {ShipItemCount} goods of player chara {Uid} for {ShipIncome}, bonus {ShipBonus}",
            count, shipperUid, income, bonus);

        PayShipping(shipperUid, result);
    }

    /// <summary>
    ///     Hand over what a player earned: at once on this map or to a player simulating its own zone,
    ///     later (when it stands on this map again) to a guest or an offline player
    /// </summary>
    private void PayShipping(int shipperUid, ShippingResult? result = null)
    {
        if (IsZoneSession) {
            return;
        }

        var account = GetShippingAccount(shipperUid);
        var money = account[AccountOwedMoney];
        var bonus = account[AccountOwedBonus];
        if (money <= 0 && bonus <= 0 && result is null) {
            return;
        }

        var peer = Socket.Peers.FirstOrDefault(p => SavedRemoteCharas.GetValueOrDefault(p.User) == shipperUid);
        if (peer is null) {
            return;
        }

        var onMap = ActiveRemoteCharas.GetValueOrDefault(peer.Id) is { } chara && chara.uid == shipperUid;
        var simulatesItself = _departed.Contains(peer.Id) && !_guests.ContainsKey(peer.Id) &&
                              !_pendingGuests.ContainsKey(peer.Id) &&
                              _leases.TryGetValue(peer.Id, out var zones) && zones.Count > 0;
        if (!onMap && !simulatesItself) {
            // its character is in someone else's hands (or on its way), wait for it here
            return;
        }

        // the client adds the money itself: a player's currency is its own to change (CardModCurrencyDelta
        // brings it back here on this map, its uploads when it travels)
        account[AccountOwedMoney] = 0;
        account[AccountOwedBonus] = 0;

        result ??= new() {
            rawDate = world.date.GetRaw(),
            uidZone = pc.homeZone?.uid ?? 0,
            total = player.stats.shipMoney,
        };

        var zone = game.spatials.Find(result.uidZone);
        peer.Send(new ShippingPayout {
            Ints = [..result.ints],
            ItemStrs = [..result.items.Select(item => item._strs)],
            ShipNum = player.stats.shipNum,
            ShipMoney = player.stats.shipMoney,
            BranchLv = zone?.branch?.lv ?? 0,
            BranchExp = zone?.branch?.exp ?? 0,
            Money = money,
            Bonus = bonus,
        });

        EmpLog.Debug("Paid shipping of player {@Peer}: {ShipIncome}, bonus {ShipBonus}, on map {OnMap}",
            peer, money, bonus, onMap);
    }
}
