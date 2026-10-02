#if DEBUG
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using ElinTogether.Net;

namespace ElinTogether;

/// <summary>
///     Starts a second game on this machine that joins the local session and plays by itself (<see cref="EmpBot" />).
///     Elin refuses a second instance of itself, so this needs the copies made by _tools/make_lab.py, each with
///     its own test identity
/// </summary>
internal static class EmpBotLauncher
{
    private const string Window = "-screen-fullscreen 0 -screen-width 1280 -screen-height 720 -empmute -empbot";

    private const string KitKey = "emp_bot_kit";
    private const float KitWindow = 240f;

    /// <summary>
    ///     What a bot allowed to do everything needs to try it all: tools, things to place, food
    /// </summary>
    private static readonly string[] _kit = ["pickaxe", "shovel", "axe", "chest6", "torch", "log", "plank", "dish_soup"];

    private static readonly List<(Process Process, string Exe)> _bots = [];
    private static float _kitUntil;

    internal static int Running
    {
        get {
            _bots.RemoveAll(b => b.Process.HasExited);
            return _bots.Count;
        }
    }

    internal static bool Launch()
    {
        var session = NetSession.Instance;
        switch (session.Transport) {
            case null:
                // says why by itself when it cannot (no land claimed)
                session.InitializeComponent<ElinNetHost>().StartServer(true);
                if (session.Transport is null) {
                    return false;
                }

                break;
            case ElinNetHost { IsLocalServer: true }:
                break;
            default:
                // two games on one Steam account cannot meet through Steam
                EmpPop.Information("emp_ui_bot_need_local".lang());
                return false;
        }

        var exe = FindLauncher();
        if (exe is null) {
            EmpPop.Information("emp_ui_bot_no_launcher".lang());
            return false;
        }

        var folder = Path.GetDirectoryName(exe)!;
        var args = Window;
        if (EmpConfig.Dev.BotAllActions.Value) {
            args += " -empbotall";
        }

        // next to the logs of the test suites, when that folder is there
        var logs = Path.GetFullPath(Path.Combine(folder, "..", "..", "_shots"));
        if (Directory.Exists(logs)) {
            args += $" -logFile \"{Path.Combine(logs, Path.GetFileName(folder).ToLowerInvariant() + "-player.log")}\"";
        }

        var start = new ProcessStartInfo(exe, args) {
            WorkingDirectory = folder,
            UseShellExecute = false,
        };

        // the mod loader marks this process as done, a game inheriting the mark starts without any mod
        foreach (var name in start.EnvironmentVariables.Keys.Cast<string>().ToArray()) {
            if (name.StartsWith("DOORSTOP", StringComparison.OrdinalIgnoreCase)) {
                start.EnvironmentVariables.Remove(name);
            }
        }

        var process = Process.Start(start);
        if (process is null) {
            return false;
        }

        _bots.Add((process, exe));
        if (EmpConfig.Dev.BotAllActions.Value) {
            _kitUntil = UnityEngine.Time.unscaledTime + KitWindow;
        }
        EmpLog.Information("Bot: started {Exe} (pid {Pid})", exe, process.Id);
        EmpPop.Information("emp_ui_bot_started".lang());
        return true;
    }

    /// <summary>
    ///     Only the games started from here
    /// </summary>
    internal static void StopAll()
    {
        foreach (var (process, _) in _bots) {
            try {
                if (!process.HasExited) {
                    process.Kill();
                }
            } catch (Exception ex) {
                EmpLog.Warning(ex, "Bot: could not stop pid {Pid}", process.Id);
            }
        }

        _bots.Clear();
    }

    /// <summary>
    ///     A bot is a new player with empty hands, and a client cannot create things: the host hands the kit to
    ///     whoever joins in the minutes after a bot was started
    /// </summary>
    internal static void Tick()
    {
        if (UnityEngine.Time.unscaledTime > _kitUntil || Running == 0 ||
            NetSession.Instance.Transport is not ElinNetHost { IsZoneSession: false } host) {
            return;
        }

        foreach (var chara in host.ActiveRemoteCharas.Values) {
            if (chara.GetInt(KitKey) != 0 || !chara.IsAliveInCurrentZone) {
                continue;
            }

            chara.SetInt(KitKey, 1);
            foreach (var id in _kit) {
                if (chara.things.Find(id) is null) {
                    chara.AddThing(ThingGen.Create(id));
                }
            }

            EmpLog.Information("Bot: kit handed to player chara {Uid}", chara.uid);
        }
    }

    private static string? FindLauncher()
    {
        var busy = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var process in Process.GetProcessesByName("Elin")) {
            try {
                if (process.MainModule?.FileName is { } path) {
                    busy.Add(Path.GetFullPath(path));
                }
            } catch {
                // not ours to look at
            }
        }

        return Candidates().FirstOrDefault(exe => File.Exists(exe) && !busy.Contains(Path.GetFullPath(exe)));
    }

    private static IEnumerable<string> Candidates()
    {
        var configured = EmpConfig.Dev.BotLaunchers.Value
            .Split([';'], StringSplitOptions.RemoveEmptyEntries)
            .Select(path => path.Trim())
            .ToArray();
        if (configured.Length > 0) {
            return configured;
        }

        // where dev/_tools/make_lab.py put them: told by ELINTOGETHER_LAB, else the place they first lived in
        var lab = Environment.GetEnvironmentVariable("ELINTOGETHER_LAB") is { Length: > 0 } told
            ? told
            : Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "ElinMods", "_lab");
        return Directory.Exists(lab)
            ? Directory.GetDirectories(lab, "Elin*").OrderBy(dir => dir).Select(dir => Path.Combine(dir, "Elin.exe"))
            : [];
    }
}
#endif
