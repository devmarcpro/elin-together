using System;
using ElinTogether.Helper;
using ElinTogether.Net;
using UnityEngine;

namespace ElinTogether;

/// <summary>
///     A game started with `-empserver &lt;save id&gt;` is a server, as one runs a Minecraft server: it loads that
///     save and opens the session by itself, nobody plays it, the players join by address
///     (`&lt;this machine&gt;:55556`) whenever they want. `-empserver world_depot` takes the world from the
///     save depot when one is set (see SaveDepot)
/// </summary>
internal static class EmpServer
{
    private const float SaveSeconds = 300f;

    private static readonly string? _save = Arg("-empserver");

    private static float _next;
    private static bool _loading;

    internal static bool Requested => _save is not null;

    private static string? Arg(string name)
    {
        var args = Environment.GetCommandLineArgs();
        var at = Array.IndexOf(args, name);
        return at >= 0 && at + 1 < args.Length ? args[at + 1] : null;
    }

    /// <summary>
    ///     Called every frame
    /// </summary>
    internal static void Update()
    {
        if (!Requested || Time.unscaledTime < _next) {
            return;
        }

        _next = Time.unscaledTime + 2f;
        AudioListener.volume = 0f;

        var session = NetSession.Instance;
        if (!EClass.core.IsGameStarted) {
            // (the title has its own layers open: no waiting for an idle interface)
            if (_loading || EClass.scene.mode != Scene.Mode.Title) {
                return;
            }

            _loading = true;
            EmpLog.Information("Server: loading {Save}", _save);
            if (_save == SaveDepot.WorldId && SaveDepot.Enabled) {
                SaveDepot.Take();
            } else {
                // "cloud:<id>" for a Steam Cloud save, as the game's own list loads them
                var cloud = _save!.StartsWith("cloud:");
                Game.Load(cloud ? _save.Substring(6) : _save, cloud);
            }

            return;
        }

        if (EClass.pc is null || EClass._map is null) {
            return;
        }

        if (session.Transport is null) {
            // a question left open by the load (a mod the save knew is missing) would hold the world
            foreach (var dialog in EClass.ui.layers.FindAll(l => l is Dialog)) {
                dialog.Close();
            }

            EmpLog.Information("Server: opening the session on port {Port}", Common.EmpConstants.LocalPort);
            session.InitializeComponent<ElinNetHost>().StartServer(true);
            _next = Time.unscaledTime + SaveSeconds;
            return;
        }

        // nobody is there to save: the server does, while someone plays
        if (session.CurrentPlayers.Count > 1) {
            EClass.game.Save(true, true);
        }

        _next = Time.unscaledTime + SaveSeconds;
    }
}
