using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Models;
using UnityEngine;
using YKF;

namespace ElinTogether.Components;

/// <summary>
///     The trade window: what I offer, what the other player offers, confirm or cancel. Rebuilt each time the
///     table changes (see <see cref="PlayerTrade" />)
/// </summary>
internal class LayerPlayerTrade : YKLayer<object>
{
    private static bool _refreshing;

    public override string Title => "emp_ui_trade".lang();

    public override Rect Bound => new(Vector2.zero, new Vector2(Screen.width / 2f, Screen.height / 1.6f) / ui.canvasScaler.scaleFactor);

    private static LayerPlayerTrade? Instance { get; set; }

    public override void OnLayout()
    {
        Instance = this;
        CreateTab<TabPlayerTrade>("emp_ui_trade", "emp_tab_trade");
    }

    public override void OnKill()
    {
        Instance = null;

        // closed by the player, not rebuilt: the trade is off
        if (!_refreshing) {
            PlayerTrade.Cancel();
        }
    }

    internal static void Refresh()
    {
        Dismiss();
        YK.CreateLayer<LayerPlayerTrade>();
    }

    internal static void Dismiss()
    {
        if (Instance is not { } layer) {
            return;
        }

        _refreshing = true;
        try {
            ui.RemoveLayer(layer);
        } finally {
            _refreshing = false;
        }
    }
}

internal class TabPlayerTrade : YKLayout<object>
{
    public override void OnLayout()
    {
        if (PlayerTrade.View is not { } view) {
            return;
        }

        var iAmA = view.UidA == EClass.pc.uid;
        var mine = iAmA ? view.ItemsA : view.ItemsB;
        var theirs = iAmA ? view.ItemsB : view.ItemsA;
        var myGold = iAmA ? view.GoldA : view.GoldB;
        var theirGold = iAmA ? view.GoldB : view.GoldA;
        var iAmReady = iAmA ? view.ReadyA : view.ReadyB;
        var theyAreReady = iAmA ? view.ReadyB : view.ReadyA;
        var partner = EClass._map.charas.Find(c => c.uid == (iAmA ? view.UidB : view.UidA));

        Header("emp_trade_you_offer".lang());
        ListOffer(EClass.pc, mine, myGold);

        var edit = Horizontal();
        edit.Layout.childForceExpandWidth = true;
        edit.Button("emp_trade_add".lang(), PickItem);
        edit.Button("emp_trade_gold".Loc(myGold), PickGold);
        if (mine.Count > 0) {
            edit.Button("emp_trade_clear".lang(), () => {
                foreach (var item in mine.ToArray()) {
                    PlayerTrade.Offer(item.Uid, 0);
                }
            });
        }

        Spacer(8);
        Header("emp_trade_they_offer".Loc(partner?.Name ?? "?"));
        ListOffer(partner, theirs, theirGold);

        Spacer(8);
        Text((iAmReady ? "emp_trade_you_ready" : "emp_trade_you_wait").lang() + "  /  " +
             (theyAreReady ? "emp_trade_they_ready" : "emp_trade_they_wait").lang());

        var actions = Horizontal();
        actions.Layout.childForceExpandWidth = true;
        if (!iAmReady) {
            actions.Button("emp_trade_confirm".lang(), PlayerTrade.Confirm);
        }

        actions.Button("emp_trade_cancel".lang(), PlayerTrade.Cancel);
    }

    private void ListOffer(Chara? owner, List<TradeItem> items, int gold)
    {
        if (items.Count == 0 && gold == 0) {
            Text("emp_trade_nothing".lang());
            return;
        }

        foreach (var item in items) {
            var thing = owner?.things.Find(item.Uid);
            Text(thing is null ? $"? x{item.Num}" : $"{thing.GetName(NameStyle.Full, item.Num)}");
        }

        if (gold > 0) {
            Text("emp_trade_gold".Loc(gold));
        }
    }

    private static void PickItem()
    {
        // the same rule as when both confirm, so nothing is offered that would be refused then
        var things = EClass.pc.things.Where(t => PlayerTrade.Refuse(t) is null).ToList();
        if (things.Count == 0) {
            EmpPop.Information("emp_trade_nothing_to_offer".lang());
            return;
        }

        Dialog.List("emp_trade_pick".lang(), things, t => t.Name, (index, _) => {
            var thing = things[index];
            if (thing.Num <= 1) {
                PlayerTrade.Offer(thing.uid, 1);
                return true;
            }

            Dialog.InputName("emp_trade_howmany", thing.Num.ToString(), (cancel, text) => {
                if (!cancel && int.TryParse(text, out var num)) {
                    PlayerTrade.Offer(thing.uid, Mathf.Clamp(num, 0, thing.Num));
                }
            });
            return true;
        }, true);
    }

    private static void PickGold()
    {
        Dialog.InputName("emp_trade_howmuch", "0", (cancel, text) => {
            if (!cancel && int.TryParse(text, out var gold)) {
                PlayerTrade.SetGold(Mathf.Clamp(gold, 0, EClass.pc.GetCurrency()));
            }
        });
    }
}
