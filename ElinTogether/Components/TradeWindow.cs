using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Models;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Components;

/// <summary>
///     The trade window, in the game's own container windows (user, 2026-10-22: like Dofus 3, and like the game):
///     "my offer", where the player drags things from its backpack, and the other player's offer, which can be
///     looked at but not taken. A thing dragged in stays in the backpack: it is only put on the table
///     (<see cref="PlayerTrade" />, nothing moves until both validate). What the windows show are copies made in
///     this game only, never part of the world
/// </summary>
public static class TradeWindow
{
    private static LayerInventory? _mine;
    private static LayerInventory? _theirs;
    private static Thing? _holdMine;
    private static Thing? _holdTheirs;
    private static bool _closing;

    // closed by the player: not opened again by a state already on its way, before the cancel comes back
    private static int _closedTrade = -1;
    private static TradeStateDelta? _last;
    private static UIButton? _confirm;
    private static UIButton? _gold;
    private static UIButton? _status;

    // copy shown -> the real thing it stands for
    private static readonly Dictionary<int, int> Origins = [];

    public static int OriginOf(Card copy)
    {
        return Origins.TryGetValue(copy.uid, out var uid) ? uid : 0;
    }

    internal static void Refresh()
    {
        if (PlayerTrade.View is not { } view) {
            return;
        }

        var iAmA = view.UidA == EClass.pc.uid;
        var partner = EClass._map.charas.Find(c => c.uid == (iAmA ? view.UidB : view.UidA));
        if (partner is null) {
            return;
        }

        if (view.TradeId == _closedTrade) {
            return;
        }

        // (Unity: a closed window compares equal to null)
        if (_mine == null || _theirs == null) {
            Open(partner);
        }

        var theirs = iAmA ? view.ItemsB : view.ItemsA;
        Tell(partner, theirs, iAmA ? view.GoldB : view.GoldA);

        Fill(_holdMine!, EClass.pc, iAmA ? view.ItemsA : view.ItemsB);
        Fill(_holdTheirs!, partner, theirs);
        Caption(view, partner, iAmA);
        LayerInventory.SetDirtyAll(true);
        _last = view;
    }

    /// <summary>
    ///     Trades are numbered by each host from 1: a window closed in one session says nothing about the next
    /// </summary>
    internal static void ForgetClosed()
    {
        _closedTrade = -1;
    }

    internal static void Dismiss()
    {
        _closing = true;
        try {
            foreach (var layer in new[] { _mine, _theirs }) {
                if (layer != null) {
                    layer.Close();
                }
            }
        } finally {
            _closing = false;
        }

        using (ElinDelta.Quiet()) {
            _holdMine?.Destroy();
            _holdTheirs?.Destroy();
        }

        _mine = _theirs = null;
        _holdMine = _holdTheirs = null;
        _last = null;
        Origins.Clear();
    }

    private static void Open(Chara partner)
    {
        Dismiss();
        using (ElinDelta.Quiet()) {
            _holdTheirs = Keep(ThingGen.Create("chest3"));
            _holdMine = Keep(ThingGen.Create("chest3"));
        }

        // theirs first: the last one opened is where a click in the backpack sends a thing
        _theirs = Create(new InvOwnerTradeTheirs(partner, _holdTheirs, CurrencyType.None), _holdTheirs, 170f);
        _mine = Create(new InvOwnerTradeMine(EClass.pc, _holdMine, CurrencyType.None), _holdMine, -40f);

        // what the other player offers in gold and whether it validated: the bottom of its window
        _status = _theirs.windows[0].AddBottomButton("emp_trade_they_wait", () => { });

        var window = _mine.windows[0];
        _confirm = window.AddBottomButton("emp_trade_confirm", () => {
            if (PlayerTrade.IsLocked) {
                SE.BeepSmall();
                Msg.Say("emp_trade_locked".lang());
                return;
            }

            PlayerTrade.Confirm();
        });
        _gold = window.AddBottomButton("emp_trade_gold_button", PickGold);
        window.AddBottomButton("emp_trade_cancel", PlayerTrade.Cancel);

        _mine.SetOnKill(OnClosed);
        _theirs.SetOnKill(OnClosed);
    }

    /// <summary>
    ///     A guest's game destroys at once what it makes itself (only the host makes things): not these
    /// </summary>
    private static Thing Keep(Thing thing)
    {
        CardCache.UndoDestroy(thing);
        return thing;
    }

    /// <summary>
    ///     A container window of the game in its "trade" mode (the "buy" mode of CreateContainer adds a shop's restock
    ///     button). The two offers one above the other on the left of the middle, clear of the backpack on the right
    /// </summary>
    private static LayerInventory Create(InvOwner owner, Thing holder, float y)
    {
        var layer = LayerInventory._Create();
        layer.SetInv().AddTab(owner, UIInventory.Mode.Trade).dest = EClass.pc;
        holder.c_windowSaveData = new() { useBG = true };
        layer.windows[0].saveData = holder.c_windowSaveData;
        EClass.ui.AddLayer(layer);
        if (layer.windows[0].transform is RectTransform rect) {
            rect.anchoredPosition = new(-300f, y);
        }

        return layer;
    }

    private static void OnClosed()
    {
        if (!_closing) {
            EmpLog.Debug("Trade window closed by the player: trade cancelled");
            _closedTrade = PlayerTrade.View?.TradeId ?? -1;
            PlayerTrade.Cancel();
            Dismiss();
        }
    }

    private static void Fill(Thing holder, Chara owner, List<TradeItem> items)
    {
        using (ElinDelta.Quiet()) {
            foreach (var shown in holder.things.ToList()) {
                Origins.Remove(shown.uid);
                shown.Destroy();
            }

            foreach (var item in items) {
                if (owner.things.Find(item.Uid) is not { } thing) {
                    continue;
                }

                var copy = holder.AddThing(Keep(thing.Duplicate(item.Num)), false);
                Origins[copy.uid] = thing.uid;
            }
        }
    }

    private static void Caption(TradeStateDelta view, Chara partner, bool iAmA)
    {
        var iAmReady = iAmA ? view.ReadyA : view.ReadyB;
        var theyAreReady = iAmA ? view.ReadyB : view.ReadyA;
        var myGold = iAmA ? view.GoldA : view.GoldB;
        var theirGold = iAmA ? view.GoldB : view.GoldA;

        _confirm?.mainText.SetText((iAmReady ? "emp_trade_you_ready" : "emp_trade_confirm").lang());
        _gold?.mainText.SetText("emp_trade_gold".Loc(myGold));
        _status?.mainText.SetText("emp_trade_status".Loc(partner.Name, theirGold, (theyAreReady ? "emp_trade_they_ready" : "emp_trade_they_wait").lang()));
    }

    /// <summary>
    ///     What the other player just put on the table or took back, a line of the message log (what Dofus shows, so a
    ///     swap at the last second is seen)
    /// </summary>
    private static void Tell(Chara partner, List<TradeItem> theirs, int theirGold)
    {
        if (_last is null) {
            return;
        }

        var before = _last.UidA == EClass.pc.uid ? _last.ItemsB : _last.ItemsA;
        var goldBefore = _last.UidA == EClass.pc.uid ? _last.GoldB : _last.GoldA;
        foreach (var item in theirs.Where(i => !before.Exists(b => b.Uid == i.Uid && b.Num == i.Num))) {
            var name = partner.things.Find(item.Uid)?.GetName(NameStyle.Full, item.Num) ?? "?";
            Msg.Say("emp_trade_log_add".Loc(partner.Name, name));
        }

        foreach (var item in before.Where(b => !theirs.Exists(i => i.Uid == b.Uid))) {
            var name = partner.things.Find(item.Uid)?.GetName(NameStyle.Full, item.Num) ?? "?";
            Msg.Say("emp_trade_log_remove".Loc(partner.Name, name));
        }

        if (theirGold != goldBefore) {
            Msg.Say("emp_trade_log_gold".Loc(partner.Name, theirGold));
        }
    }

    private static void PickGold()
    {
        Dialog.InputName("emp_trade_howmuch", PlayerTrade.MyGold.ToString(), (cancel, text) => {
            if (!cancel && int.TryParse(text, out var gold)) {
                PlayerTrade.SetGold(Mathf.Clamp(gold, 0, EClass.pc.GetCurrency()));
            }
        });
    }

    /// <summary>
    ///     A thing dragged (or clicked) from the backpack to "my offer" is put on the table, not moved; nothing leaves
    ///     the trade windows for a bag
    /// </summary>
    [HarmonyPatch(typeof(InvOwner.Transaction), nameof(InvOwner.Transaction.Process))]
    internal static class TransferPatch
    {
        // (first: the mod's own transaction event would ask the host to move the thing)
        [HarmonyPrefix]
        [HarmonyPriority(Priority.First)]
        internal static bool OnProcess(InvOwner.Transaction __instance, ref bool __result)
        {
            switch (__instance.inv) {
                case InvOwnerTradeMine when __instance.thing is { } shown:
                    // taken back out of my offer
                    if (OriginOf(shown) is var uid and > 0) {
                        PlayerTrade.Offer(uid, 0);
                    }

                    __result = false;
                    return false;
                case InvOwnerTradeTheirs:
                    __result = false;
                    return false;
            }

            switch (__instance.destInv) {
                case InvOwnerTradeMine when __instance.thing is { } thing:
                    __result = Put(thing, __instance.num);
                    return false;
                case InvOwnerTradeTheirs:
                    __result = false;
                    return false;
            }

            return true;
        }
    }

    /// <summary>
    ///     A thing of the backpack put on the table (dropped in, or sent with Shift): the more of the pile
    /// </summary>
    private static bool Put(Thing thing, int num)
    {
        // (from the backpack only: not from a chest open beside it)
        if (thing.GetRootCard() != EClass.pc || PlayerTrade.Refuse(thing) is not null) {
            SE.BeepSmall();
            Msg.Say("emp_trade_cant_offer".Loc(thing.Name));
            return false;
        }

        var offered = PlayerTrade.MyItems.FirstOrDefault(i => i.Uid == thing.uid)?.Num ?? 0;
        PlayerTrade.Offer(thing.uid, Mathf.Min(thing.Num, offered + Mathf.Max(1, num)));
        thing.PlaySoundDrop(false);
        return true;
    }

    /// <summary>
    ///     Shift + click (or right click) sends a thing to the window open beside: the game adds it to that window's
    ///     container at once, not through a transaction. Into "my offer": put on the table; out of it: taken back;
    ///     the other's offer: nothing
    /// </summary>
    [HarmonyPatch(typeof(InvOwner), nameof(InvOwner.OnShiftClick))]
    internal static class ShiftClickPatch
    {
        [HarmonyPrefix]
        [HarmonyPriority(Priority.First)]
        internal static bool OnShiftClick(InvOwner __instance, ButtonGrid b, bool rightMouse)
        {
            if (b.card is not Thing thing) {
                return true;
            }

            switch (__instance) {
                case InvOwnerTradeMine:
                    if (OriginOf(thing) is var uid and > 0) {
                        SE.Equip();
                        PlayerTrade.Offer(uid, 0);
                    }

                    return false;
                case InvOwnerTradeTheirs:
                    return false;
            }

            switch (__instance.GetShitDestOwner(b, rightMouse)) {
                case InvOwnerTradeMine:
                    Put(thing, thing.Num);
                    return false;
                case InvOwnerTradeTheirs:
                    return false;
            }

            return true;
        }
    }
}

/// <summary>
///     My side of the trade window: things are dropped in from the backpack, a click takes one back
/// </summary>
public class InvOwnerTradeMine(Card owner, Card container, CurrencyType currency) : InvOwner(owner, container, currency)
{
    public override bool AllowTransfer => true;

    public override bool AllowAutouse => false;

    public override bool AllowContext => false;

    public override bool UseGuide => true;

    public override bool AllowHold(Thing t)
    {
        return false;
    }

    public override bool ShouldShowGuide(Thing t)
    {
        return t.GetRootCard() == EClass.pc && PlayerTrade.Refuse(t) is null;
    }

    public override void OnClick(ButtonGrid button)
    {
        if (button.card is { } shown && TradeWindow.OriginOf(shown) is var uid and > 0) {
            SE.Equip();
            PlayerTrade.Offer(uid, 0);
        }
    }

    public override void OnRightClick(ButtonGrid button)
    {
        OnClick(button);
    }
}

/// <summary>
///     The other player's side: to look at (the tooltip tells everything about a thing), nothing to take
/// </summary>
public class InvOwnerTradeTheirs(Card owner, Card container, CurrencyType currency) : InvOwner(owner, container, currency)
{
    public override bool AllowTransfer => false;

    public override bool AllowAutouse => false;

    public override bool AllowContext => false;

    public override bool AllowHold(Thing t)
    {
        return false;
    }

    public override void OnClick(ButtonGrid button)
    {
    }

    public override void OnRightClick(ButtonGrid button)
    {
    }
}
