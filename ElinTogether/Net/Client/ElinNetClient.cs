using System;
using ElinTogether.Common;
using ElinTogether.LangMod;
using ElinTogether.Models;
using ElinTogether.Net.Steam;
using HeathenEngineering.SteamworksIntegration;
using ReflexCLI.UI;

namespace ElinTogether.Net;

internal partial class ElinNetClient : ElinNetBase
{
    private DateTime _lastTimeout = DateTime.Now;

    public override bool IsHost => false;
    public ISteamNetPeer Host => Socket.FirstPeer;
    public bool IsJoiningLobby { get; private set; }

    /// <summary>
    ///     Connected through the local udp port instead of a steam lobby, for debugging
    /// </summary>
    public bool IsLocalConnection { get; private set; }

    public bool IsDirectConnection { get; private set; }

    protected override void Update()
    {
        base.Update();

        if (IsZoneSession) {
            // a crashed zone host only shows as a local timeout (no ClosedByPeer), fall back to the host link
            if (!IsConnected) {
                EmpLog.Warning("Lost the zone session host");
                EndSession(EmpDisconnectInfo.RemoteClosed);
            }

            return;
        }

        UpdateTravelCheckpoint();
        UpdateHandoffWait();
        UpdateQuestInvite();
        UpdateTransferLock();

        if (IsConnected) {
            _lastTimeout = DateTime.Now;
            return;
        }

        if (IsJoiningLobby && Session.Lobby.Current.HasServer) {
            if (long.TryParse(Session.Lobby.Current[$"connection_key_{UserData.Me}"], out var key) && key != 0L) {
                IsJoiningLobby = false;
                ConnectSteamUser(Session.Lobby.Current.GameServer.id);
            }
        }

#if !DEBUG
        var elapsed = DateTime.Now - _lastTimeout;
        if (elapsed.TotalSeconds > EmpConfig.Policy.Timeout.Value) {
            EmpPop.Information((IsDirectConnection ? "emp_ui_timeout" : "emp_ui_timeout_steam").lang());
            EndSession(EmpDisconnectInfo.Timeout);
        }
#endif
    }

    public void ConnectLocalPort(ushort port = EmpConstants.LocalPort)
    {
        Stop();
        IsLocalConnection = true;
        Socket.Connect(port);
    }

    /// <summary>
    ///     To a server by its address ("host:port"), as one joins a Minecraft server. Like a local connection
    ///     it does not go through the Steam lobby; players still reach each other's maps through Steam
    /// </summary>
    public void ConnectAddress(string address)
    {
        Stop();
        IsLocalConnection = false;
        IsDirectConnection = true;
        Socket.Connect(address);
    }

    public void ConnectSteamUser(UserData steamId)
    {
        Stop();
        IsLocalConnection = false;
        Socket.Connect(steamId);
    }

    protected override void RegisterPackets()
    {
        Router.ShouldReceivePacket = ShouldReceiveHostPacket;

        // delta
        Router.RegisterHandler<ZoneDataResponse>(OnZoneDataResponse);
        Router.RegisterHandler<ZoneActivateResponse>(OnZoneActivateResponse);
        Router.RegisterHandler<WorldStateSnapshot>(OnWorldStateSnapshot);
        Router.RegisterHandler<WorldStateDeltaList>(OnWorldStateDeltaResponse);

        // integrity
        Router.RegisterHandler<NetIntegrityRequest>(OnNetHandshakeRequest);
        Router.RegisterHandler<NetIntegrityRejected>(OnNetHandshakeRejected);

        // source validation
        Router.RegisterHandler<SourceValidationRequest>(OnSourceValidationRequest);
        Router.RegisterHandler<SourceValidationFailed>(OnSourceValidationFailed);

        // session
        Router.RegisterHandler<SessionNewPlayerRequest>(OnSessionNewPlayerRequest);
        Router.RegisterHandler<SessionCharaSelectRequest>(OnSessionCharaSelectRequest);
        Router.RegisterHandler<SaveDataProbe>(OnSaveDataProbe);
        Router.RegisterHandler<SteamLobbyRequest>(OnSteamLobbyRequest);
        Router.RegisterHandler<SessionPlayersSnapshot>(OnSessionStatesUpdate);
        Router.RegisterHandler<NetSessionRules>(OnSessionRulesUpdate);
        Router.RegisterHandler<SessionReconnectRequest>(OnSessionReconnectRequest);

        // independent travel
        Router.RegisterHandler<ZoneLeaseGrant>(OnZoneLeaseGrant);
        Router.RegisterHandler<ZoneLeaseDepart>(OnZoneLeaseDepart);
        Router.RegisterHandler<ZoneLeaseDenied>(OnZoneLeaseDenied);
        Router.RegisterHandler<ZoneLeaseRecall>(OnZoneLeaseRecall);
        Router.RegisterHandler<ZoneGuestRequest>(OnZoneGuestRequest);
        Router.RegisterHandler<ZoneGuestLeft>(OnZoneGuestLeft);
        Router.RegisterHandler<ShippingPayout>(OnShippingPayout);
    }

    internal override void Stop()
    {
        base.Stop();

        // a zone session closes, the game goes on with the host link
        if (!core.IsGameStarted || IsZoneSession) {
            return;
        }

        scene.Init(Scene.Mode.Title);
    }

#region Net Events

    /// <summary>
    ///     Net event: On connected to host
    /// </summary>
    protected override void OnPeerConnected(ISteamNetPeer host)
    {
        if (!host.IsConnected) {
            EmpPop.Information("emp_error_connection".lang());
            EndSession(EmpDisconnectInfo.RemoteClosed);
            return;
        }

        // reconnects
        BeginHandshake();

        EmpPop.Information("emp_connecting_host".lang(), Host);

        this.StartDeferredCoroutine(StartWorldStateUpdate, () => core.IsGameStarted);

#if DEBUG
        if (!IsDebugGuiActive) {
            StartDebugGui();
        }
#endif
    }

    /// <summary>
    ///     Net event: On disconnected from host.
    ///     Fully clean up resources and return to title.
    /// </summary>
    protected override void OnPeerDisconnected(ISteamNetPeer host, string disconnectInfo)
    {
        StopWorldStateUpdate();
        StopAllCoroutines();

        if (ReflexUIManager.IsConsoleOpen()) {
            ReflexUIManager.StaticClose();
        }

        EmpLog.Warning("Disconnected from host: {Reason}",
            disconnectInfo);

        if (IsZoneSession) {
            // the host link reacts, see ElinNetClient.OnZoneSessionEnded
            EndSession(disconnectInfo);
            return;
        }

        Session.ResetSession();

        EmpPop.Information("emp_disconnected_host".Loc(disconnectInfo));
    }

#endregion
}