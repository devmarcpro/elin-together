using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net.Steam;
using UnityEngine;

namespace ElinTogether.Net;

internal partial class ElinNetHost
{
    public readonly Dictionary<int, Chara> ActiveRemoteCharas = [];

    /// <summary>
    ///     A combination of all remote chara's act states
    /// </summary>
    public int SharedActState => States.Values.Sum(s => s.LastAct);

    /// <summary>
    ///     Shared speed of all players
    /// </summary>
    public int SharedSpeed => (int)States.Values.Average(s => s.Speed);

    [ElinGameIOProperty("remote_chara")]
    private static Dictionary<ulong, int> SavedRemoteCharas
    {
        get => field ??= [];
        set;
    }

    /// <summary>
    ///     Every character a player made in this world. <see cref="SavedRemoteCharas" /> holds the one it plays
    /// </summary>
    [ElinGameIOProperty("remote_chara_roster")]
    private static Dictionary<ulong, List<int>> PlayerRosters
    {
        get => field ??= [];
        set;
    }

    public static void RemoveRemoteChara(Chara remoteChara, bool broadcast = true)
    {
        if (!core.IsGameStarted) {
            return;
        }

        remoteChara.SetNoGoal();

        pc.party.RemoveMember(remoteChara);

        if (remoteChara.currentZone == _zone && _map.charas.Contains(remoteChara)) {
            _zone.RemoveCard(remoteChara);
        } else {
            // a player on another map keeps its position there, which may not exist on this one
            remoteChara.parent = null;
            remoteChara.currentZone = null;
        }

        if (broadcast && NetSession.Instance.Connection is ElinNetHost host) {
            host.Delta.AddRemote(new CharaRemoveFromGameDelta {
                Owner = remoteChara,
            });
        }
    }

    /// <summary>
    ///     PeerConnect -> Prepare -> MoveZone -> SaveProbe
    /// </summary>
    public void PreparePlayerJoin(ISteamNetPeer peer, string? notice = null)
    {
        EmpLog.Information("Preparing player {@Peer} for joining",
            peer);

        if (!IsZoneSession) {
            GiveOrphanTo(peer.User);
        }

        var roster = RosterOf(peer.User);
        // not for the guests of a zone hosted by a player: they come with the character they are playing
        var choose = EmpConfig.Server.ChooseCharacter.Value;
        var import = EmpConfig.Server.ImportCharacter.Value;
        // bringing a character alone (no choice of character): asked once, when the player has nobody here yet.
        // Afterwards it gets the character it played last without a question at every connection
        var known = SavedRemoteCharas.TryGetValue(peer.User, out var played) && game.cards.globalCharas.Find(played) is not null;
        if (!IsZoneSession && ((roster.Count > 0 && choose) || (import && (choose || !known)))) {
            // without the choice of character, only the one it played last
            if (!choose) {
                roster = roster.Where(c => SavedRemoteCharas.TryGetValue(peer.User, out var last) && c.uid == last).ToList();
            }

            // the player picks who to play, brings someone from its own saves, or makes someone new
            peer.Send(new SessionCharaSelectRequest {
                AllowImport = import,
                Notice = notice,
                Charas = roster
                    .Select(c => new SessionCharaEntry {
                        Uid = c.uid,
                        Label = $"{c.Name} - {c.race.GetName()} {c.job.GetName()}, Lv {c.LV}",
                    })
                    .ToList(),
            });
            return;
        }

        if (!SavedRemoteCharas.TryGetValue(peer.User, out var charaUid) ||
            game.cards.globalCharas.Find(charaUid) is not { } chara) {
            EmpLog.Debug("Remote character does not exist, request for new character generation");
            peer.Send(new SessionNewPlayerRequest());
        } else {
            // remote character exists
            SendSaveProbe(chara, peer);
        }
    }

    /// <summary>
    ///     The characters of a player in this world nobody is playing right now
    /// </summary>
    private List<Chara> RosterOf(ulong user)
    {
        if (!PlayerRosters.TryGetValue(user, out var uids)) {
            uids = PlayerRosters[user] = [];
        }

        // worlds from before the roster only know the one character
        if (SavedRemoteCharas.TryGetValue(user, out var current) && !uids.Contains(current)) {
            uids.Add(current);
        }

        return uids
            .Select(uid => game.cards.globalCharas.Find(uid))
            .Where(c => c is not null && !ActiveRemoteCharas.ContainsValue(c))
            .ToList();
    }

    /// <summary>
    ///     Net event: the player picked a character, or asks for a new one
    /// </summary>
    private void OnSessionCharaSelectResponse(SessionCharaSelectResponse response, ISteamNetPeer peer)
    {
        if (ActiveRemoteCharas.ContainsKey(peer.Id)) {
            return;
        }

        if (response.Uid == 0) {
            EmpLog.Debug("Player {@Peer} asks for a new character", peer);
            peer.Send(new SessionNewPlayerRequest());
            return;
        }

        if (RosterOf(peer.User).Find(c => c.uid == response.Uid) is not { } chara) {
            EmpLog.Warning("Player {@Peer} picked chara {Uid} which is not one of its own", peer, response.Uid);
            PreparePlayerJoin(peer);
            return;
        }

        SavedRemoteCharas[peer.User] = chara.uid;
        SendSaveProbe(chara, peer);
    }

    /// <summary>
    ///     Net event: the player brings the character of one of its own saves
    /// </summary>
    private void OnSessionCharaImportResponse(SessionCharaImportResponse response, ISteamNetPeer peer)
    {
        if (ActiveRemoteCharas.ContainsKey(peer.Id)) {
            return;
        }

        if (IsZoneSession || !EmpConfig.Server.ImportCharacter.Value) {
            EmpLog.Warning("Player {@Peer} sent a character while bringing one is not allowed", peer);
            PreparePlayerJoin(peer);
            return;
        }

        // one copy of a save's character per player: a second one would be the same items twice
        RosterOf(peer.User);
        if (PlayerRosters[peer.User].Any(uid =>
                game.cards.globalCharas.Find(uid)?.GetStr(CharaImport.SourceKey) == response.Source)) {
            EmpLog.Information("Player {@Peer} already brought the character of {Source}", peer, response.Source);
            PreparePlayerJoin(peer, "emp_ui_chara_import_twice");
            return;
        }

        Chara chara;
        try {
            chara = response.Chara.Decompress<Chara>();
            CharaImport.Adopt(chara, response.Source);
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not take in the character brought by player {@Peer}", peer);
            PreparePlayerJoin(peer, "emp_ui_chara_import_fail");
            return;
        }

        EmpLog.Information("Player {@Peer} brings {Name} (Lv {Level}) from its save {Source}",
            peer, chara.Name, chara.LV, response.Source);

        // before the save probe, which hands a missing standing the one of a new player
        PlayerStandings[chara.uid] = [response.Fame, response.Karma];
        SavedRemoteCharas[peer.User] = chara.uid;
        // adds the character now played to the roster
        RosterOf(peer.User);

        SendSaveProbe(chara, peer);
    }

    /// <summary>
    ///     Send a save snapshot for replication
    /// </summary>
    public void SendSaveProbe(Chara chara, ISteamNetPeer peer)
    {
        EmpLog.Information("Sending save probe to player {@Peer} for replication",
            peer);

        // register before any SetAI
        ActiveRemoteCharas[peer.Id] = chara;

        chara.MakeAlly();
        chara.MoveZone(pc.currentZone);
        chara.SetBool("remote_chara", true);
        GiveAxeToRemotePlayer(chara);

        var state = States[peer.Id] = new() {
            Index = peer.Id,
            User = peer.User,
            CharaUid = chara.uid,
        };

        CardCache.Add(chara);
        CardCache.CacheContainer(chara.things);

        Session.CurrentPlayers.Add(state);

        peer.Send(NetSession.Instance.Rules);
        peer.Send(SaveDataProbe.Create(chara.uid));
    }

    /// <summary>
    ///     Net event: Client finished character generation and is ready for save probe
    /// </summary>
    private void OnSessionNewPlayerResponse(SessionNewPlayerResponse response, ISteamNetPeer peer)
    {
        EmpLog.Information("Received remote chara creation from player {@Peer}",
            peer);

        var chara = response.Chara.Decompress<Chara>();
        AdoptNewPlayerChara(chara);

        SavedRemoteCharas[peer.User] = chara.uid;
        // adds the character now played to the roster
        RosterOf(peer.User);

        SendSaveProbe(chara, peer);
    }

    /// <summary>
    ///     A character just made on the creation screen of another game becomes a character of this world, with what
    ///     a new game gives its player
    /// </summary>
    private static void AdoptNewPlayerChara(Chara chara)
    {
        chara.SetBool(CINT.IsPC, false);
        chara.SetBool("emp_creating", true);
        game.cards.AssignUID(chara);

        var host = pc;
        try {
            player.chara = chara;

            chara.hp = chara.MaxHP;
            chara.SetFaith(game.religions.list[0]);
            chara.elements.SetBase(SKILL.strategy, 1);
            chara.elements.SetBase(ABILITY.AI_Meditate, 1);
            chara.elements.SetBase(ABILITY.ActQuickCraft, 1);
            chara.elements.SetBase(ABILITY.AI_SelfHarm, 1);
            chara.elements.SetBase(ABILITY.ActPray, 1);
            foreach (var e in chara.elements.dict.Values.ToList()) {
                if (e.Value == 0) {
                    chara.elements.Remove(e.id);
                    continue;
                }
                if (e.HasTag("primary")) {
                    e.vTempPotential = Mathf.Max(30, (e.ValueWithoutLink - 8) * 7);
                }
            }

            foreach (var slot in chara.body.slots) {
                chara.body.Unequip(slot);
            }
            chara.things.DestroyAll();
            chara.elements.CheckSkillActions();
            chara.hunger.value = 30;
            chara.CalculateMaxStamina();
            chara.stamina.Set(chara.stamina.max / 2);
            chara.Refresh();

            player.CreateEquip();
            chara.AddThing("purse");
        } finally {
            chara.SetBool("emp_creating", false);
            player.chara = host;
        }
    }

    /// <summary>
    ///     Request a specific client to reconnect for full synchronization
    /// </summary>
    public void RequestClientReconnect(int peerIndex)
    {
        if (!States.ContainsKey(peerIndex)) {
            EmpLog.Warning("Cannot request reconnect: peer {PeerIndex} not found",
                peerIndex);
            return;
        }

        foreach (var peer in Socket.Peers) {
            if (peer.Id == peerIndex) {
                EmpLog.Information("Requesting reconnect for peer {@Peer}",
                    peer);
                peer.Send(SessionReconnectRequest.Current);
                return;
            }
        }

        EmpLog.Warning("Cannot request reconnect: peer {PeerIndex} not connected",
            peerIndex);
    }

    private static void GiveAxeToRemotePlayer(Chara chara)
    {
        if (!chara.GetBool("remote_axe_given")) {
            try {
                chara.SetBool("emp_creating", true);
                chara.AddThing("axe");
            } finally {
                chara.SetBool("emp_creating", false);
            }
            chara.SetBool("remote_axe_given", true);
        }
    }

    [ElinPostLoad]
    private static void RemoveLeftOverCharas(GameIOContext? context)
    {
        // a world taken over from another player: our own character first, then the game starts again from that save.
        // One frame later: the tables of the save (who plays whom) are read after this hook, here they are still
        // those of the game played before. Never on a server nobody plays at, never for a client
        if (Session.Transport is null && !EmpServer.Requested) {
            var loaded = game;
            core.actionsNextFrame.Add(() => {
                if (core.game != loaded || Session.Transport is not null || !TakeOverPc()) {
                    return;
                }

                // not saved: played as it is, loading again would exchange again
                var (id, cloud) = (Game.id, game.isCloud);
                if (game.Save(false, true)) {
                    core.actionsNextFrame.Add(() => Game.Load(id, cloud));
                }
            });
        }

        IEnumerable<Chara> excluded = Session.Connection is ElinNetHost host
            ? host.ActiveRemoteCharas.Values
            : [];

        // not ourselves: a client hosting a zone session is a remote chara in the world it copied
        var currentRemoteCharas = game.cards.globalCharas.Values
            .Where(c => c != pc && c.GetBool("remote_chara"));

        foreach (var chara in currentRemoteCharas.Except(excluded)) {
            RemoveRemoteChara(chara);
        }

        pc.party?.members.RemoveAll(c => c is null);
        pc.party?.uidMembers.RemoveAll(uid => pc.party?.members.Find(c => c.uid == uid) is null);
    }
}