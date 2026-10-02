using System.Collections.Generic;
using System.Linq;
using ElinTogether.Components;
using ElinTogether.LangMod;
using ElinTogether.Models;
using ElinTogether.Net;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     A trade between two players standing next to each other: each puts items and gold on its side of a window,
///     both confirm, and the exchange happens at once. <br />
///     Nothing is set aside while they talk it over: an offer is only a list of numbers. When both confirmed, the
///     game simulating the map (the host, or the player holding that map) checks everything again and moves the
///     real items, so nothing can be copied or lost on the way. Walking away, changing map or dropping out cancels
/// </summary>
public static class PlayerTrade
{
    public const int Invite_ = 0;
    public const int Accept_ = 1;
    public const int Decline_ = 2;
    public const int SetOffer_ = 3;
    public const int Confirm_ = 4;
    public const int Cancel_ = 5;

    public const int Invited = 0;
    public const int Open = 1;
    public const int Done = 2;
    public const int Cancelled = 3;

    private const int Reach = 3;
    private const float CheckInterval = 0.25f;

    private static readonly List<Session> _sessions = [];
    private static readonly List<TradeItem> _myItems = [];
    private static int _myGold;
    private static int _nextId = 1;
    private static float _nextCheck;

    /// <summary>
    ///     What the authority last said about the trade the local player is in
    /// </summary>
    public static TradeStateDelta? View { get; private set; }

    internal static bool Enabled => NetSession.Instance.Rules.AllowPlayerTrade;

    // ---------------------------------------------------------------- the local player

    public static void Invite(int partnerUid)
    {
        if (!Enabled || View is { Phase: Invited or Open }) {
            return;
        }

        _myItems.Clear();
        _myGold = 0;
        Send(new TradeIntentDelta {
            Kind = Invite_,
            PartnerUid = partnerUid,
        });
    }

    public static void Accept()
    {
        Answer(Accept_);
    }

    public static void Decline()
    {
        Answer(Decline_);
    }

    public static void Cancel()
    {
        Answer(Cancel_);
    }

    /// <summary>
    ///     Puts <paramref name="num" /> of that item on the table, 0 takes it back
    /// </summary>
    public static void Offer(int thingUid, int num)
    {
        _myItems.RemoveAll(i => i.Uid == thingUid);
        if (num > 0) {
            _myItems.Add(new() {
                Uid = thingUid,
                Num = num,
            });
        }

        SendOffer();
    }

    public static void SetGold(int gold)
    {
        _myGold = Mathf.Max(0, gold);
        SendOffer();
    }

    public static void Confirm()
    {
        if (View is not { Phase: Open } view) {
            return;
        }

        Send(new TradeIntentDelta {
            Kind = Confirm_,
            TradeId = view.TradeId,
            Revision = view.Revision,
        });
    }

    /// <summary>
    ///     For the test bridge: where the trade stands, in one line
    /// </summary>
    public static string Describe()
    {
        if (View is not { } view) {
            return "none";
        }

        var phase = view.Phase switch {
            Invited => "Invited",
            Open => "Open",
            Done => "Done",
            _ => "Cancelled",
        };
        return $"{phase} rev {view.Revision} A[{string.Join(",", view.ItemsA.Select(i => $"{i.Uid}x{i.Num}"))}]+{view.GoldA} " +
               $"ready={view.ReadyA} B[{string.Join(",", view.ItemsB.Select(i => $"{i.Uid}x{i.Num}"))}]+{view.GoldB} " +
               $"ready={view.ReadyB} {view.Reason}";
    }

    private static void Answer(int kind)
    {
        if (View is not { Phase: Invited or Open } view) {
            return;
        }

        Send(new TradeIntentDelta {
            Kind = kind,
            TradeId = view.TradeId,
        });
    }

    private static void SendOffer()
    {
        if (View is not { Phase: Open } view) {
            return;
        }

        Send(new TradeIntentDelta {
            Kind = SetOffer_,
            TradeId = view.TradeId,
            Items = _myItems.ToList(),
            Gold = _myGold,
        });
    }

    private static void Send(TradeIntentDelta intent)
    {
        switch (NetSession.Instance.Connection) {
            case ElinNetHost host:
                // this game simulates the map: the request is its own
                Handle(intent, EClass.pc, host);
                break;
            case ElinNetClient client:
                client.Delta.AddRemote(intent);
                break;
        }
    }

    /// <summary>
    ///     The authority tells where the trade stands
    /// </summary>
    internal static void Show(TradeStateDelta state)
    {
        var mine = EClass.pc.uid;
        if (state.UidA != mine && state.UidB != mine) {
            return;
        }

        var before = View;
        View = state;

        switch (state.Phase) {
            case Invited when state.UidB == mine && before?.TradeId != state.TradeId:
                _myItems.Clear();
                _myGold = 0;
                Dialog.YesNo("emp_trade_invite".Loc(NameOf(state.UidA)), Accept, Decline);
                break;
            case Open:
                LayerPlayerTrade.Refresh();
                break;
            case Done:
                LayerPlayerTrade.Dismiss();
                EmpPop.Information("emp_trade_done".lang());
                break;
            case Cancelled:
                LayerPlayerTrade.Dismiss();
                EmpPop.Information((string.IsNullOrEmpty(state.Reason) ? "emp_trade_cancelled" : state.Reason).lang());
                break;
        }
    }

    internal static string NameOf(int charaUid)
    {
        return EClass._map.charas.Find(c => c.uid == charaUid)?.Name ?? "?";
    }

    // ---------------------------------------------------------------- the game simulating the map

    internal static void Handle(TradeIntentDelta intent, Chara from, ElinNetHost host)
    {
        if (!Enabled) {
            return;
        }

        if (intent.Kind == Invite_) {
            Start(from, intent.PartnerUid, host);
            return;
        }

        var session = _sessions.Find(s => s.Id == intent.TradeId && (s.A == from || s.B == from));
        if (session is null) {
            return;
        }

        switch (intent.Kind) {
            case Accept_ when session.B == from && !session.IsOpen:
                session.IsOpen = true;
                Tell(session, host, Open);
                break;
            case Decline_ or Cancel_:
                End(session, host, Cancelled, "");
                break;
            case SetOffer_ when session.IsOpen:
                if (session.A == from) {
                    session.ItemsA = intent.Items ?? [];
                    session.GoldA = Mathf.Max(0, intent.Gold);
                } else {
                    session.ItemsB = intent.Items ?? [];
                    session.GoldB = Mathf.Max(0, intent.Gold);
                }

                // what was agreed on is not what is on the table anymore
                session.Revision++;
                session.ReadyA = session.ReadyB = false;
                Tell(session, host, Open);
                break;
            case Confirm_ when session.IsOpen && intent.Revision == session.Revision:
                if (session.A == from) {
                    session.ReadyA = true;
                } else {
                    session.ReadyB = true;
                }

                if (session is { ReadyA: true, ReadyB: true }) {
                    Commit(session, host);
                } else {
                    Tell(session, host, Open);
                }

                break;
        }
    }

    /// <summary>
    ///     A trade needs both players there: gone, dead or too far cancels it
    /// </summary>
    internal static void Update()
    {
        // alone again (travelling, back at the title screen): whatever trade was going on is over
        if (NetSession.Instance.Connection is null && (View is not null || _sessions.Count > 0)) {
            Clear();
            return;
        }

        if (_sessions.Count == 0 || Time.unscaledTime < _nextCheck) {
            return;
        }

        _nextCheck = Time.unscaledTime + CheckInterval;

        if (NetSession.Instance.Connection is not ElinNetHost host) {
            _sessions.Clear();
            return;
        }

        foreach (var session in _sessions.ToArray()) {
            if (!Present(session.A) || !Present(session.B)) {
                End(session, host, Cancelled, "");
            } else if (session.A.pos.Distance(session.B.pos) > Reach) {
                End(session, host, Cancelled, "emp_trade_far");
            }
        }
    }

    internal static void Clear()
    {
        _sessions.Clear();
        _myItems.Clear();
        _myGold = 0;
        View = null;
        LayerPlayerTrade.Dismiss();
    }

    private static bool Present(Chara chara)
    {
        return chara is { isDead: false, isDestroyed: false } && EClass._map.charas.Contains(chara);
    }

    private static void Start(Chara from, int partnerUid, ElinNetHost host)
    {
        var partner = EClass._map.charas.Find(c => c.uid == partnerUid);
        if (partner is null || partner == from || !partner.IsPlayer || !Present(from) || !Present(partner)) {
            return;
        }

        if (_sessions.Exists(s => s.A == from || s.B == from || s.A == partner || s.B == partner)) {
            TellOne(host, from, new() {
                Phase = Cancelled,
                UidA = from.uid,
                UidB = partner.uid,
                Reason = "emp_trade_busy",
            });
            return;
        }

        if (from.pos.Distance(partner.pos) > Reach) {
            TellOne(host, from, new() {
                Phase = Cancelled,
                UidA = from.uid,
                UidB = partner.uid,
                Reason = "emp_trade_far",
            });
            return;
        }

        var session = new Session {
            Id = _nextId++,
            A = from,
            B = partner,
        };
        _sessions.Add(session);
        Tell(session, host, Invited);
    }

    private static void Commit(Session session, ElinNetHost host)
    {
        var fromA = Resolve(session.A, session.ItemsA, session.GoldA);
        var fromB = Resolve(session.B, session.ItemsB, session.GoldB);
        if (fromA is null || fromB is null) {
            // something on the table is not there anymore (used, dropped, spent): no half trade
            End(session, host, Cancelled, "emp_trade_invalid");
            return;
        }

        // the real items change hands here; the host's own patches tell everyone, nothing is created
        using (ElinDelta.Simulate()) {
            Move(session.A, session.B, fromA, session.GoldA);
            Move(session.B, session.A, fromB, session.GoldB);
        }

        EmpLog.Information("Players {UidA} and {UidB} traded {CountA}+{GoldA} for {CountB}+{GoldB}",
            session.A.uid, session.B.uid, fromA.Count, session.GoldA, fromB.Count, session.GoldB);
        End(session, host, Done, "");
    }

    /// <summary>
    ///     The items of an offer as they are right now in their owner's bag, null if any of it does not hold
    /// </summary>
    private static List<(Thing Thing, int Num)>? Resolve(Chara owner, List<TradeItem> items, int gold)
    {
        if (gold > owner.GetCurrency()) {
            return null;
        }

        var resolved = new List<(Thing, int)>();
        foreach (var item in items) {
            var thing = owner.things.Find(item.Uid);
            if (thing is null || thing.isDestroyed || thing.GetRootCard() != owner || item.Num < 1 || thing.Num < item.Num ||
                thing.isEquipped || thing.c_isImportant || thing.trait is TraitAbility || thing.id is "money" ||
                (thing.IsContainer && thing.things.Count > 0) || resolved.Exists(r => r.Item1 == thing)) {
                return null;
            }

            resolved.Add((thing, item.Num));
        }

        return resolved;
    }

    private static void Move(Chara from, Chara to, List<(Thing Thing, int Num)> items, int gold)
    {
        foreach (var (thing, num) in items) {
            to.AddThing(thing.Num == num ? thing : thing.Split(num));
        }

        if (gold > 0) {
            from.ModCurrency(-gold);
            to.ModCurrency(gold);
        }
    }

    private static void End(Session session, ElinNetHost host, int phase, string reason)
    {
        _sessions.Remove(session);
        Tell(session, host, phase, reason);
    }

    private static void Tell(Session session, ElinNetHost host, int phase, string reason = "")
    {
        var state = new TradeStateDelta {
            TradeId = session.Id,
            Phase = phase,
            UidA = session.A.uid,
            UidB = session.B.uid,
            ItemsA = session.ItemsA.ToList(),
            ItemsB = session.ItemsB.ToList(),
            GoldA = session.GoldA,
            GoldB = session.GoldB,
            ReadyA = session.ReadyA,
            ReadyB = session.ReadyB,
            Revision = session.Revision,
            Reason = reason,
        };

        TellOne(host, session.A, state);
        TellOne(host, session.B, state);
    }

    private static void TellOne(ElinNetHost host, Chara chara, TradeStateDelta state)
    {
        if (chara == EClass.pc) {
            Show(state);
            return;
        }

        foreach (var (peerId, remote) in host.ActiveRemoteCharas) {
            if (remote == chara) {
                host.SendDeltaTo(peerId, state);
                return;
            }
        }
    }

    private sealed class Session
    {
        internal Chara A = null!;
        internal Chara B = null!;
        internal int GoldA;
        internal int GoldB;
        internal int Id;
        internal bool IsOpen;
        internal List<TradeItem> ItemsA = [];
        internal List<TradeItem> ItemsB = [];
        internal bool ReadyA;
        internal bool ReadyB;
        internal int Revision;
    }
}
