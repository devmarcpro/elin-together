using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using ElinTogether.Common;
using ElinTogether.Models;
using ElinTogether.Net.Steam;
using HeathenEngineering.SteamworksIntegration;

namespace ElinTogether.Net;

internal partial class ElinNetHost : ElinNetBase
{
    internal readonly Dictionary<int, NetPeerState> States = [];

    public override bool IsHost => true;

    /// <summary>
    ///     Listening on the local udp port: what a second game on this machine can join
    /// </summary>
    internal bool IsLocalServer => Socket.IsLocalUdp;

    internal void StartServer(bool localUdp = false)
    {
        Stop();
        StopWorldStateUpdate();

        if (!core.IsGameStarted || player?.chara?.homeBranch?.owner is null) {
            EmpLog.Warning("Cannot start server: game not started or no land claimed");
            EmpPop.Debug("emp_ui_unclaimed_zone".lang());
            Session.ResetSession();
            return;
        }

        Session.Lobby.CreateLobby();

        try {
            if (localUdp) {
                Socket.StartServerUdp();
            } else {
                Socket.StartServerSdr();
            }
        } catch {
            Session.ResetSession();
            throw;
        }

        Scheduler.Subscribe(DisconnectInactive, 1);
        Scheduler.Subscribe(RemoveStaleIntegrityCheck, 2);

        // host also registers self state
        var selfState = States[0] = new() {
            Index = 0,
            User = UserData.Me,
            CharaUid = player.uidChara,
        };

        // setup session states
        Session.Player = pc;
        Session.Self = selfState;
        Session.CurrentPlayers.Add(selfState);
        Session.SharedSpeed = NetSession.Instance.Rules.UseSharedSpeed
            ? SharedSpeed
            : -1;

        EmpPop.Information("emp_server_started".lang());

        CardCache.CacheCurrentZone();

        StartWorldStateUpdate();
    }

    protected override void RegisterPackets()
    {
        Router.ShouldReceivePacket = ShouldReceivePeerPacket;

        Router.RegisterHandler<NetIntegrityResponse>(OnNetHandshakeResponse);

        Router.RegisterHandler<SessionNewPlayerResponse>(OnSessionNewPlayerResponse);
        Router.RegisterHandler<SessionCharaSelectResponse>(OnSessionCharaSelectResponse);
        Router.RegisterHandler<MapDataRequest>(OnMapDataRequest);
        Router.RegisterHandler<ZoneDataReceivedResponse>(OnZoneDataReceivedResponse);
        Router.RegisterHandler<WorldStateRequest>(OnWorldStateRequest);
        Router.RegisterHandler<WorldStateDeltaList>(OnWorldStateDeltaResponse);
        Router.RegisterHandler<CharaStateSnapshot>(OnClientRemoteCharaSnapshot);

        // independent travel
        Router.RegisterHandler<ZoneLeaseRequest>(OnZoneLeaseRequest);
        Router.RegisterHandler<ZoneLeaseAck>(OnZoneLeaseAck);
        Router.RegisterHandler<ZoneLeaseRelease>(OnZoneLeaseRelease);
        Router.RegisterHandler<ZoneGuestReady>(OnZoneGuestReady);
        Router.RegisterHandler<ZoneGuestLeave>(OnZoneGuestLeave);
        Router.RegisterHandler<ShippingDeposit>(OnShippingDeposit);

        // source validation
        Router.RegisterHandler<SourceValidationResponse>(OnSourceValidationResponse);
        Router.RegisterHandler<SourceValidationContinue>(OnSourceValidationContinue);
    }

    private void Broadcast<T>(T packet)
    {
        Socket.Broadcast.Send(packet);
    }

    protected void DisconnectInactive()
    {
        foreach (var peer in Socket.Peers) {
            if (IsAway(peer)) {
                // away players have no tick state, drop them as soon as the transport is gone
                if (!peer.IsConnected) {
                    Socket.Disconnect(peer, EmpDisconnectInfo.InactivePeer);
                }

                continue;
            }

            if (!States.TryGetValue(peer.Id, out var state)) {
                continue;
            }

            if (state.LastReceivedTick == -1) {
                continue;
            }

            // client has not been responding after 25 ticks
            if (!peer.IsConnected && Session.Tick - state.LastReceivedTick > 25) {
                Socket.Disconnect(peer, EmpDisconnectInfo.InactivePeer);
            }
        }

        // remove all left over chara
        // (not ourselves: a client hosting a zone session is a remote chara in the world it copied)
        foreach (var chara in _map.charas.ToArray()) {
            if (chara != pc && chara.GetBool("remote_chara") && !ActiveRemoteCharas.Values.Contains(chara)) {
                RemoveRemoteChara(chara);
            }
        }
    }

#region Net Events

    protected override void OnPeerConnected(ISteamNetPeer peer)
    {
        var sw = Stopwatch.StartNew();
        while (peer.User.Name is null && sw.ElapsedMilliseconds <= 500) {
            // do a spin wait to pin the username
        }

        EmpPop.Information("emp_player_connected".lang(), peer);

        // shou lai
        BeginHandshake(peer);

#if DEBUG
        if (!IsDebugGuiActive) {
            StartDebugGui();
        }
#endif
    }

    protected override void OnPeerDisconnected(ISteamNetPeer peer, string disconnectInfo)
    {
        EmpPop.Information("emp_player_disconnected".lang(), peer, disconnectInfo);

        _handshakes.Remove(peer.Id);
        PendingRebind.ReleasePeer(peer.Id);

        if (IsZoneSession) {
            OnZoneGuestDisconnecting(peer);
        } else {
            ReleaseLeaseOnDisconnect(peer);
        }

        if (States.Remove(peer.Id, out var state)) {
            // Fully remove remote chara from the map (saved chara remains via ElinGameIOProperty)
            if (ActiveRemoteCharas.Remove(peer.Id, out var remoteChara)) {
                RemoveRemoteChara(remoteChara);
                TakeCompanionsAlong(remoteChara);
                EmpLog.Information("Player {PlayerName} remote chara {Uid} removed from map. " +
                                   "Saved chara retained for future new connections.",
                    state.User.Name, remoteChara.uid);
            }

            Session.CurrentPlayers.Remove(state);
        }

        EmpLog.Debug("Player {PlayerName} disconnected. {Remaining} players remaining",
            state?.User.Name ?? "unknown", States.Count);

        Broadcast(SessionPlayersSnapshot.Create());

        // keep ticking but no update
        if (States.Count == 0) {
            PauseWorldStateUpdate();
            StopDebugGui();
        }

        if (IsZoneSession) {
            CloseZoneSessionIfEmpty(peer);
        }
    }

#endregion
}