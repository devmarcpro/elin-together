using System.Linq;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(GameDate), nameof(GameDate.ShipGoods))]
internal static class WorldShipGoodsEvent
{
    [HarmonyPrefix]
    internal static bool OnShipGoods(ref ShippingResult? __state)
    {
        __state = EClass.player.shippingResults.LastItem();
        // client can't initiate this, nor an away client in its copy of the world: the host ships the box,
        // a copy would sell the same goods again
        if (NetSession.Instance.Connection is ElinNetClient || NetSession.Instance.IsAway) {
            return false;
        }

        // every player is paid for its own goods, what is left in the box is the host's
        (NetSession.Instance.Connection as ElinNetHost)?.ShipPlayersGoods();
        return true;
    }


    [HarmonyPostfix]
    internal static void OnAfterShipGoods(ShippingResult? __state)
    {
        if (NetSession.Instance.Connection is not ElinNetHost host) {
            return;
        }

        if (EClass.player.shippingResults.LastItem() is not { } result || result == __state) {
            return;
        }

        var zone = EClass.game.spatials.Find(result.uidZone);
        host.Delta.AddRemote(new ShippingResultDelta {
            Ints = [..result.ints],
            ItemStrs = [..result.items.Select(item => item._strs)],
            ShipNum = EClass.player.stats.shipNum,
            ShipMoney = EClass.player.stats.shipMoney,
            BranchLv = zone?.branch?.lv ?? 0,
            BranchExp = zone?.branch?.exp ?? 0,
        });

        EmpLog.Debug("Shipping result {ShipIncome} {ShipItemCount} {ZoneUid}",
            result.GetIncome(), result.items.Count, result.uidZone);
    }
}

/// <summary>
///     Morning deliveries are the host world's too, an away copy would deliver them again
/// </summary>
[HarmonyPatch(typeof(GameDate), nameof(GameDate.ShipPackages))]
internal static class WorldShipPackagesEvent
{
    [HarmonyPrefix]
    internal static bool OnShipPackages()
    {
        return NetSession.Instance.Connection is not ElinNetClient && !NetSession.Instance.IsAway;
    }
}
