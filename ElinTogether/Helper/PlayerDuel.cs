using System.Collections.Generic;
using ElinTogether.LangMod;
using ElinTogether.Models;
using ElinTogether.Net;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     A duel between two players, where they stand: one challenges the other from its menu, the other has 15
///     seconds to say yes, a short countdown, then they fight. Nobody dies of it: the blow of one duellist that
///     would kill the other is stopped at 0 hit points (RemotePlayerKillPatch) and ends the duel, both are healed
///     and nothing is lost. What follows a duellist does not die of the other side either. <br />
///     The game simulating the map keeps who duels who. Leaving the map, dropping out or dying of something
///     else ends the duel without a winner. What was drunk, shot or used up during the duel stays spent
/// </summary>
public static class PlayerDuel
{
    public const int Challenge_ = 0;
    public const int Accept_ = 1;
    public const int Decline_ = 2;

    public const int Invited = 0;
    public const int Countdown = 1;
    public const int Fighting = 2;
    public const int Won = 3;
    public const int Cancelled = 4;

    /// <summary>
    ///     How long the challenge stays open, no answer is a no
    /// </summary>
    private const float AnswerSeconds = 15f;

    /// <summary>
    ///     Said in emp_duel_countdown
    /// </summary>
    private const float CountdownSeconds = 3f;

    private static readonly List<Session> _sessions = [];
    private static readonly List<DuelStateDelta> _fights = [];
    private static int _nextId = 1;
    private static Dialog? _box;

    /// <summary>
    ///     What the authority last said about the duel the local player is in
    /// </summary>
    public static DuelStateDelta? View { get; private set; }

    internal static bool Enabled => NetSession.Instance.Rules.AllowDuels;

    // ---------------------------------------------------------------- the local player

    public static void Challenge(int partnerUid)
    {
        if (Enabled) {
            Send(new() {
                Kind = Challenge_,
                PartnerUid = partnerUid,
            });
        }
    }

    /// <summary>
    ///     For the test bridge: where the duel stands, in one line
    /// </summary>
    public static string Describe()
    {
        if (View is not { } view) {
            return "none";
        }

        var phase = view.Phase switch {
            Invited => "Invited",
            Countdown => "Countdown",
            Fighting => "Fighting",
            Won => "Won",
            _ => "Cancelled",
        };
        return $"{phase} {view.UidA} vs {view.UidB} winner {view.WinnerUid} {view.Reason}";
    }

    private static void Answer(int duelId, int kind)
    {
        _box = null;
        Send(new() {
            Kind = kind,
            DuelId = duelId,
        });
    }

    private static void Send(DuelIntentDelta intent)
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
    ///     The authority tells where a duel stands
    /// </summary>
    internal static void Show(DuelStateDelta state)
    {
        _fights.RemoveAll(f => f.DuelId == state.DuelId);
        if (state.Phase == Fighting) {
            _fights.Add(state);
        }

        var mine = EClass.pc.uid;
        if (state.UidA != mine && state.UidB != mine) {
            return;
        }

        // refused before it existed: the duel we may be in goes on
        if (state.DuelId == 0) {
            EmpPop.Information(state.Reason.lang());
            return;
        }

        View = state;
        var a = PlayerTrade.NameOf(state.UidA);
        var b = PlayerTrade.NameOf(state.UidB);

        switch (state.Phase) {
            case Invited when state.UidB == mine:
                var challenge = state.DuelId;
                _box = Dialog.YesNo("emp_duel_invite".Loc(a),
                    () => Answer(challenge, Accept_),
                    () => Answer(challenge, Decline_));
                break;
            case Invited:
                EmpPop.Information("emp_duel_asked".Loc(b));
                break;
            case Countdown:
                EmpPop.Information("emp_duel_countdown".Loc(a, b));
                break;
            case Fighting:
                EmpPop.Information("emp_duel_fight".lang());
                break;
            case Won:
                // mana and stamina are each player's own, its game gives them back
                var pc = EClass.pc;
                pc.hp = pc.MaxHP;
                pc.mana.value = pc.mana.max;
                pc.stamina.value = pc.stamina.max;
                EmpPop.Information(state.WinnerUid == state.UidA ? "emp_duel_won".Loc(a, b) : "emp_duel_won".Loc(b, a));
                break;
            case Cancelled:
                CloseBox();
                EmpPop.Information(state.Reason.lang());
                break;
        }
    }

    /// <summary>
    ///     Whether this character is in a duel being fought, as a duellist or as what follows one: the other
    ///     side cannot kill it, whatever the host allows outside a duel
    /// </summary>
    internal static bool Protects(Chara target)
    {
        if (_fights.Count == 0) {
            return false;
        }

        var uid = target.uid;
        var owner = CompanionHelper.OwnerOf(target)?.uid ?? 0;
        return _fights.Exists(f => f.UidA == uid || f.UidB == uid || f.UidA == owner || f.UidB == owner);
    }

    /// <summary>
    ///     Another connection or another world (see PlayerTrade.WatchSession): whatever duel was going on is over
    /// </summary>
    internal static void Clear()
    {
        _sessions.Clear();
        _fights.Clear();
        View = null;
        CloseBox();
    }

    private static void CloseBox()
    {
        if (_box != null) {
            _box.Close();
        }

        _box = null;
    }

    // ---------------------------------------------------------------- the game simulating the map

    internal static void Handle(DuelIntentDelta intent, Chara from, ElinNetHost host)
    {
        if (intent.Kind == Challenge_) {
            Start(from, intent.PartnerUid, host);
            return;
        }

        // only the challenged player answers, once
        var session = _sessions.Find(s => s.Id == intent.DuelId && s.B == from && s.Phase == Invited);
        if (session is null) {
            return;
        }

        if (intent.Kind == Accept_) {
            session.Phase = Countdown;
            session.Deadline = Time.unscaledTime + CountdownSeconds;
            Tell(session, host);
        } else {
            End(session, host, "emp_duel_declined");
        }
    }

    /// <summary>
    ///     A blow that was stopped at 0 hit points: when it is one duellist's on the other, the duel is lost.
    ///     Settled on the next frame, outside the game's damage code
    /// </summary>
    internal static void Struck(Card target, Card? origin)
    {
        if (_sessions.Count == 0 || target.hp > 0) {
            return;
        }

        // whoever dealt it (the duellist, its companion): the one left at 0 has lost
        var session = _sessions.Find(s => s.Phase == Fighting && (s.A == target || s.B == target));
        if (session is not null) {
            session.Winner ??= session.A == target ? session.B : session.A;
        }
    }

    /// <summary>
    ///     A duel needs both players there: gone or dead of something else ends it without a winner
    /// </summary>
    internal static void Update()
    {
        if (_sessions.Count == 0) {
            return;
        }

        if (NetSession.Instance.Connection is not ElinNetHost host) {
            _sessions.Clear();
            return;
        }

        foreach (var session in _sessions.ToArray()) {
            if (!Present(session.A) || !Present(session.B)) {
                End(session, host, "emp_duel_over");
            } else if (session.Winner is { } winner) {
                // the host is right about hit points; the rest is given back by each duellist's own game
                session.A.hp = session.A.MaxHP;
                session.B.hp = session.B.MaxHP;
                session.Phase = Won;
                _sessions.Remove(session);
                Tell(session, host, winner.uid);
                EmpLog.Information("Player {Winner} won a duel against {Loser}",
                    winner.uid, (winner == session.A ? session.B : session.A).uid);
            } else if (session.Phase != Fighting && Time.unscaledTime >= session.Deadline) {
                if (session.Phase == Invited) {
                    End(session, host, "emp_duel_noanswer");
                } else {
                    session.Phase = Fighting;
                    Tell(session, host);
                }
            }
        }
    }

    private static bool Present(Chara chara)
    {
        // IsPlayer: the character of a player who dropped out is not one anymore
        return chara is { isDead: false, isDestroyed: false, IsPlayer: true } && EClass._map.charas.Contains(chara);
    }

    private static void Start(Chara from, int partnerUid, ElinNetHost host)
    {
        var partner = EClass._map.charas.Find(c => c.uid == partnerUid);
        if (!Enabled || partner is null || partner == from || !Present(from) || !Present(partner)) {
            return;
        }

        // one thing at a time: a second challenge is refused and the duel going on is left alone
        if (_sessions.Exists(s => s.A == from || s.B == from || s.A == partner || s.B == partner) ||
            PlayerTrade.Busy(from) || PlayerTrade.Busy(partner)) {
            TellOne(host, from, new() {
                Phase = Cancelled,
                UidA = from.uid,
                UidB = partner.uid,
                Reason = "emp_duel_busy",
            });
            return;
        }

        var session = new Session {
            Id = _nextId++,
            A = from,
            B = partner,
            Deadline = Time.unscaledTime + AnswerSeconds,
        };
        _sessions.Add(session);
        Tell(session, host);
    }

    private static void End(Session session, ElinNetHost host, string reason)
    {
        _sessions.Remove(session);
        session.Phase = Cancelled;
        Tell(session, host, 0, reason);
    }

    private static void Tell(Session session, ElinNetHost host, int winnerUid = 0, string reason = "")
    {
        var state = new DuelStateDelta {
            DuelId = session.Id,
            Phase = session.Phase,
            UidA = session.A.uid,
            UidB = session.B.uid,
            WinnerUid = winnerUid,
            Reason = reason,
        };

        Show(state);
        if (state.Phase == Won) {
            // behind the blow that ended it, which leaves one flush later: sent at once, the loser's game was
            // healed first and then given the hit points of that blow
            host.Delta.DeferRemote(state);
        } else {
            host.SendDeltaToAllExcept(-1, state);
        }
    }

    private static void TellOne(ElinNetHost host, Chara chara, DuelStateDelta state)
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
        internal float Deadline;
        internal int Id;
        internal int Phase;
        internal Chara? Winner;
    }
}
