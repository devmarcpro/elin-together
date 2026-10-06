using System;
using System.Diagnostics;
using ElinTogether.Net;
using UnityEngine;

namespace ElinTogether;

/// <summary>
///     What a player who hosts no longer does by hand: the session opens with the world, and the world is saved
///     every 2 minutes while someone else plays in it, so that a crash of the host costs everyone 2 minutes at
///     most. Not for a server (-empserver): EmpServer opens and saves by itself
/// </summary>
internal static class EmpAutoHost
{
    private const float SaveSeconds = 120f;
    private const float SlowSaveSeconds = 300f;
    private const float RetrySeconds = 10f;
    private const long SlowSaveMs = 500;
    private const float BackupSeconds = 3600f;

    private static float _nextSave;
    private static bool _guests;
    private static bool _owed;
    private static bool _slow;
    private static string? _backupId;
    private static float _nextBackup;

#if DEBUG
    // the windows of the bench (-empmute) open their session themselves, on the local port a second window can
    // join: nothing opens by itself there unless the bench asks (emp.auto_open 1), and then on that port
    private static readonly bool _bench = Array.IndexOf(Environment.GetCommandLineArgs(), "-empmute") >= 0;
    private static float _benchSeconds;

    internal static bool BenchOpens { get; set; }

    internal static void SaveEvery(float seconds)
    {
        _benchSeconds = seconds;
        _nextSave = Time.unscaledTime + Interval;
    }
#endif

    private static float Interval =>
#if DEBUG
        _benchSeconds > 0f ? _benchSeconds :
#endif
        _slow ? SlowSaveSeconds : SaveSeconds;

    /// <summary>
    ///     One frame after a world is loaded, once the local character is the right one (see
    ///     ElinNetHost.RemoveLeftOverCharas): what "Start Server" does, without the click
    /// </summary>
    internal static void OpenSession()
    {
        var local = false;
#if DEBUG
        if (_bench) {
            if (!BenchOpens) {
                return;
            }

            local = true;
        }
#endif

        if (!EmpConfig.Server.AutoHost.Value || NetSession.Instance.Transport is not null) {
            return;
        }

        // StartServer refuses these with a window: nobody clicked, so only the log says it
        if (!EClass.core.IsGameStarted || EClass.scene.mode == Scene.Mode.Title ||
            EClass.player?.chara?.homeBranch?.owner is null) {
            EmpLog.Information("Session not opened by itself: no game or no land claimed");
            return;
        }

        // a world nobody else plays in stays a solo game: a session changes rules of the game (no pause in menus,
        // the turns of a fight) that a player alone never asked for. The first session of a world is opened by hand
        if (!ElinNetHost.IsSharedWorld) {
            return;
        }

        try {
            NetSession.Instance.InitializeComponent<ElinNetHost>().StartServer(local, true);
        } catch (Exception ex) {
            EmpLog.Warning(ex, "The session could not be opened by itself");
            // StartServer may throw half way (Steam away): no host component left behind
            NetSession.Instance.ResetSession();
        }
    }

    /// <summary>
    ///     Called every frame
    /// </summary>
    internal static void Update()
    {
#if DEBUG
        // a window of the bench saves by itself only once its test asked (emp.autosave_every): the suites written
        // before this count on a world that is not saved behind their back
        if (_bench && _benchSeconds <= 0f) {
            return;
        }
#endif

        var session = NetSession.Instance;
        if (EmpServer.Requested || session.Transport is not ElinNetHost || !EClass.core.IsGameStarted ||
            !EmpConfig.Server.AutoSave.Value) {
            _guests = _owed = false;
            return;
        }

        var now = Time.unscaledTime;
        var guests = session.CurrentPlayers.Count > 1;
        if (guests != _guests) {
            // the first player in starts the clock; the last one out is saved at once: what it did is in the world
            _guests = guests;
            _owed = !guests;
            _nextSave = guests ? now + Interval : now;
        }

        if ((!guests && !_owed) || now < _nextSave) {
            return;
        }

        if (!CanSave()) {
            _nextSave = now + RetrySeconds;
            return;
        }

        _owed = false;
        Save();
        _nextSave = Time.unscaledTime + Interval;
    }

    /// <summary>
    ///     Where the game's own quick save key would save, and nothing the save would take from the player's hands
    /// </summary>
    private static bool CanSave()
    {
        var pc = EClass.pc;
        return EClass.scene.mode == Scene.Mode.Zone
               && !EClass.game.isLoading
               && pc is { isDead: false, HasNoGoal: true, IsInActiveZone: true }
               && ActionMode.AdvOrRegion.IsActive
               // a dialog, a menu, the end screen; Game.Save also cancels a drag in progress
               && !EClass.ui.IsActive
               && !EClass.ui.IsDragging
               // ponytail: "in a fight" is "something here is after us", a lingering target would hold the save for good
               && !EClass._map.charas.Exists(c => c.enemy == pc && !c.isDead);
    }

    private static void Save()
    {
        var game = EClass.game;
        // these saves overwrite the only folder of the world: the save as it is on disk goes to the game's backups
        // first, once per world and then once an hour (the game's own backup timer, 4 hours unless changed, or
        // off, still runs on top). Never one per save
        if (Game.id != _backupId || Time.unscaledTime >= _nextBackup) {
            _backupId = Game.id;
            _nextBackup = Time.unscaledTime + BackupSeconds;
            try {
                GameIO.MakeBackup(new GameIndex { id = Game.id, cloud = game.isCloud });
            } catch (Exception ex) {
                EmpLog.Warning(ex, "Autosave: no backup of the save before it");
            }
        }

        var watch = Stopwatch.StartNew();
        var saved = game.Save(true, true);
        watch.Stop();
        EmpLog.Information("Autosave: {Result} in {Ms} ms", saved ? "saved" : "failed", watch.ElapsedMilliseconds);

        // the save runs in the game and freezes it meanwhile: a heavy world is saved less often
        if (watch.ElapsedMilliseconds > SlowSaveMs && !_slow) {
            _slow = true;
            EmpLog.Information("Autosave: over {Limit} ms, every {Seconds} s from now on", SlowSaveMs, SlowSaveSeconds);
        }
    }
}
