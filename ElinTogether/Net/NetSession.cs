using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Net.Steam;
using Object = UnityEngine.Object;

namespace ElinTogether.Net;

public class NetSession : EClass
{
    public enum Mode : byte
    {
        None = 0,

        /// <summary>
        ///     player in the map alone, simulates <br />
        ///     TODO: full sync for now
        /// </summary>
        PartialSync,

        /// <summary>
        ///     players share the same map, first player simulates
        ///     host takes over whenever possible
        /// </summary>
        FullSync,
    }

    private bool _resetting;

    public static NetSession Instance => field ??= new();

    public Mode SyncMode { get; private set; } = Mode.None;

    /// <summary>
    ///     The connection gameplay code synchronizes through <br />
    ///     null while the local player simulates an away zone, so the game runs as single player there
    /// </summary>
    public ElinNetBase? Connection => IsAway ? null : Transport;

    /// <summary>
    ///     The network component itself, regardless of away state
    /// </summary>
    public ElinNetBase? Transport { get; private set; }

    /// <summary>
    ///     Zone this client is leased and simulates on its own, away from the host
    /// </summary>
    public Zone? AwayZone { get; internal set; }

    public bool IsAway => AwayZone is not null;

    public Chara? Player { get; internal set; }
    public int SharedSpeed { get; internal set; }
    public Zone? CurrentZone { get; internal set; }
    public int Tick { get; internal set; }

    // currently, this is Steam LobbyData
    public ulong SessionId { get; internal set; }
    public NetSessionRules Rules { get; internal set; } = NetSessionRules.Default;

    public List<NetPeerState> CurrentPlayers => field ??= [];
    public SteamNetLobbyManager Lobby => field ??= new();
    public NetPeerState? Self { get; internal set; }

    public bool HasActiveConnection => Transport != null && Transport.IsConnected;
    public bool IsHost => Connection?.IsHost is not false;
    public bool IsClient => !IsHost;
    public bool ShouldSimulate => IsHost || SyncMode == Mode.PartialSync;

    public void RemoveComponent()
    {
        AwayZone = null;

        if (Transport != null) {
            if (!Transport.IsHost && core.IsGameStarted) {
                ui.hud?.SetDragImage(null);
                ui.RemoveLayers();
                game.Kill();
                scene.Init(Scene.Mode.Title);
            }

            Object.Destroy(Transport);

            EmpLog.Debug("Removed connection component of {ConnectionType}",
                Transport.GetType().Name);
        }

        Transport = null;

        EmpLog.Information("Connection component removed");
    }

    public void ResetSession()
    {
        if (_resetting) {
            return;
        }

        _resetting = true;
        try {
            RemoveComponent();

            Tick = 0;
            Self = null;
            CurrentPlayers.Clear();
            Lobby.LeaveLobby();

            ResourceFetch.InvalidateTemp();

            SwitchSyncMode(Mode.None);

            EmpLog.Information("Session reset to None");
        } finally {
            _resetting = false;
        }
    }

    public T InitializeComponent<T>() where T : ElinNetBase
    {
        RemoveComponent();

        Lobby.Reset();

        Transport = EmpMod.Instance.gameObject.AddComponent<T>();

        EmpLog.Debug("Initialized new connection component of {ConnectionType}",
            typeof(T).Name);

        return (Transport as T)!;
    }

    public void SwitchSyncMode(Mode mode)
    {
        if (SyncMode == mode) {
            return;
        }

        EmpLog.Debug("Switched SyncMode to {SyncMode}", mode);

        SyncMode = mode;
    }
}