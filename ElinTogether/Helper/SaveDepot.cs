using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;
using Tasks = System.Threading.Tasks; // (the game has a Task of its own)
using ElinTogether.Components;
using ElinTogether.LangMod;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     A server that is only the save. The depot keeps the world; whoever comes first takes the world from it
///     and hosts it with the mod as it is, the others join that player, every save goes back to the depot, and
///     when the host leaves the next one can take over. No game runs at the depot. <br />
///     The depot (client setting DepotPath) is either the address of Elin Together Server, "host:port" (the
///     application of dev/server: it keeps the world as one archive and holds a real lock), a private GitHub
///     repository, "github:owner/repository" (GitHubDepot: the same requests, the access key in DepotPassword),
///     or a folder every player can reach (`world/` and `host.txt`, a lock by file date)
/// </summary>
[HarmonyPatch]
internal static class SaveDepot
{
    /// <summary>
    ///     The local save the depot's world is played from
    /// </summary>
    internal const string WorldId = "world_depot";

    // ponytail: the folder's lock is a file date, on a folder that may sync late: two players taking the world
    // in the same minute both get it and the last save wins. The server application has a real lock.
    private static readonly TimeSpan _lockLife = TimeSpan.FromMinutes(3);
    private const float BeatSeconds = 60f;
    private const long MaxUnzipped = 2L * 1024 * 1024 * 1024;

    // GitHub keeps every world it receives and asks not to be written too often
    private const float SendSeconds = 300f;

    // what GitHub is asked in the background, one request after the other, and the answers for the game's thread
    private static readonly ConcurrentQueue<Action> _answered = new();
    private static Tasks.Task _asking = Tasks.Task.CompletedTask;

    // a save of the depot's world that GitHub has not been sent yet
    private static bool _unsent;

    // the saves made, and the version of the depot's world the local copy descends from: written in the marker,
    // so that a save kept from an earlier session never replaces a world it does not come from. Both are read
    // where the answer of GitHub arrives, in the background: under the lock
    private static readonly object _markGate = new();
    private static int _saves;
    private static string? _descends;
    private static float _nextSend;
    private static string? _who;
    private static float _whoAt = -60f;

    private static float _nextBeat;
    private static string _refused = "";
    private static bool _lostTold;

    private static string Root => EmpConfig.Client.DepotPath.Value.Trim();
    private static string World => Path.Combine(Root, "world");
    private static string LockFile => Path.Combine(Root, "host.txt");
    private static string Local => CorePath.RootSave + WorldId;

    /// <summary>
    ///     Left beside the local copy while the depot has not received its last save
    /// </summary>
    private static string Unsent => Local + ".unsent";

    /// <summary>
    ///     The depot is the server application, not a folder
    /// </summary>
    private static bool Remote => Regex.IsMatch(Root, @"^[^\\/\s]+:\d+$");

    /// <summary>
    ///     The depot is a private GitHub repository
    /// </summary>
    internal static bool GitHub => Root.StartsWith("github:", StringComparison.OrdinalIgnoreCase);

    /// <summary>
    ///     The depot is asked (Ask), it is not a folder
    /// </summary>
    private static bool Asked => Remote || GitHub;

    /// <summary>
    ///     This game, among the ones that share the depot (two games of one machine are two)
    /// </summary>
    private static string Me { get; } = $"{Environment.MachineName}:{Process.GetCurrentProcess().Id}";

    private static string MyName => EClass.core.IsGameStarted ? EClass.pc.Name : Environment.UserName;

    internal static bool Enabled => Root.Length > 0 && (Asked || Directory.Exists(Root));

    private static bool Holding => Enabled && EClass.core.IsGameStarted && Game.id == WorldId &&
                                   NetSession.Instance.Transport is not ElinNetClient;

    /// <summary>
    ///     The game closes without going through the title screen: the last save still goes to GitHub and the world
    ///     is freed, the time it takes. Called while the game is still whole (NetShutdown): later, at
    ///     Application.quitting, its objects are gone and nothing here can be read
    /// </summary>
    internal static void OnQuit()
    {
        try {
            if (GitHub && Holding) {
                ReleaseAtTitle(Scene.Mode.Title);
            }

            _asking.Wait(30000);
        } catch (Exception ex) {
            // the save is on this PC, and the lock expires by itself
            EmpLog.Warning(ex, "Could not free the depot at the exit");
        }
    }

    /// <summary>
    ///     The player hosting the depot's world right now, null when it is free (or ours)
    /// </summary>
    internal static string? HeldBy()
    {
        try {
            if (GitHub) {
                // the Lobby tab asks each time it opens: GitHub is asked in the background, the tab redrawn
                if (Time.unscaledTime - _whoAt > 15f) {
                    _whoAt = Time.unscaledTime;
                    Later("WHO", null, reply => {
                        var who = reply.Ok && reply.Text.Length > 0 ? reply.Text : null;
                        if (who != _who) {
                            _who = who;
                            if (!EClass.core.IsGameStarted) {
                                LayerElinTogether.Instance?.Reopen();
                            }
                        }
                    });
                }

                return _who;
            }

            if (Remote) {
                var reply = Ask("WHO");
                return reply.Ok && reply.Text.Length > 0 ? reply.Text : null;
            }

            if (!File.Exists(LockFile) || DateTime.UtcNow - File.GetLastWriteTimeUtc(LockFile) > _lockLife) {
                return null;
            }

            var lines = File.ReadAllLines(LockFile);
            return lines.Length < 2 || lines[0] == Me ? null : lines[1];
        } catch (Exception ex) when (ex is IOException or SocketException) {
            return null;
        }
    }

    /// <summary>
    ///     Takes the world from the depot and loads it. The player then opens the session as with any save
    /// </summary>
    internal static void Take()
    {
        // (GitHub says who hosts when the world is asked for; what was sent in the background arrives first)
        if (GitHub) {
            Settle();
        } else if (HeldBy() is { } who) {
            Dialog.Ok("emp_ui_depot_held".Loc(who));
            return;
        }

        if (File.Exists(Unsent) && File.Exists(Path.Combine(Local, "game.txt"))) {
            // (GitHub: never without asking, another player may have hosted since)
            if (EmpServer.Requested && !GitHub) {
                SendUnsent();
            } else {
                Dialog.YesNo("emp_ui_depot_unsent", SendUnsent, () => {
                    File.Delete(Unsent);
                    Take();
                });
            }

            return;
        }

        try {
            if (Asked) {
                var reply = Ask("TAKE");
                if (!reply.Ok) {
                    Dialog.Ok(reply.Text == "empty" ? "emp_ui_depot_empty" : Refusal(reply.Text));
                    return;
                }

                // beside the local copy, then swapped: an archive cut short leaves it as it was
                var incoming = Local + ".new";
                IO.DeleteDirectory(incoming);
                Unzip(reply.Body!, incoming);
                IO.DeleteDirectory(Local);
                Directory.Move(incoming, Local);
                Descends(GitHubDepot.WorldSha);
            } else {
                if (!File.Exists(Path.Combine(World, "game.txt"))) {
                    Dialog.Ok("emp_ui_depot_empty");
                    return;
                }

                IO.DeleteDirectory(Local);
                IO.CopyDir(World, Local);
                Beat();
            }
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not take the world from the depot {Root}", Root);
            Dialog.Ok(Refusal(""));
            return;
        }

        _lostTold = _unsent = false;
        _nextSend = 0f;
        EmpLog.Information("Took the world from the depot {Root}", Root);
        Game.Load(WorldId, false);
    }

    /// <summary>
    ///     "Join by address" given the address of Elin Together Server: it becomes the depot and its world is
    ///     taken. False when no depot answers there (a game server, or nothing)
    /// </summary>
    // ponytail: the game waits up to 5 s when the machine drops the connection without refusing it; a thread
    // if that wait bothers someone.
    internal static bool TakeFrom(string address)
    {
        var depot = EmpConfig.Client.DepotPath;
        var before = depot.Value;
        depot.Value = address;
        string? refusal = null;
        try {
            if (!Asked) {
                throw new IOException("not an address");
            }

            var reply = Ask("WHO");
            if (GitHub && !reply.Ok) {
                refusal = Refusal(reply.Text);
            }
        } catch (Exception) when (!GitHub) {
            depot.Value = before;
            return false;
        } catch (Exception) {
            refusal = Refusal("");
        }

        // a GitHub depot that cannot be used is said, and the depot set before stays
        if (refusal is not null) {
            depot.Value = before;
            Dialog.Ok(refusal);
            return true;
        }

        Take();
        return true;
    }

    /// <summary>
    ///     The local copy holds a save the depot never received: it goes there now. What the depot holds at
    ///     that moment (another player may have played since) is kept aside, never thrown away
    /// </summary>
    private static void SendUnsent()
    {
        // (the marker says which world of the depot this save was played from)
        try {
            var from = File.ReadAllText(Unsent).Trim();
            _descends = from.Length == 40 ? from : null;
        } catch (Exception ex) when (ex is IOException or UnauthorizedAccessException) {
            _descends = null;
        }

        if (Copy(Local, true)) {
            Take();
        } else {
            Dialog.Ok(Refusal(_refused));
        }
    }

    /// <summary>
    ///     Puts the save being played in the depot, as its world
    /// </summary>
    internal static void Put()
    {
        if (!GitHub && HeldBy() is { } who) {
            Dialog.Ok("emp_ui_depot_held".Loc(who));
            return;
        }

        if (!EClass.game.Save(silent: true)) {
            return;
        }

        if (!Copy(CorePath.RootSave + Game.id, true)) {
            Dialog.Ok(Refusal(_refused));
            return;
        }

        // (an older unsent copy of the depot's world must not come back over the world just put)
        File.Delete(Unsent);

        // the save now lives in the depot: it is played from there, so that every later save goes back to it
        // (played on under its own name, it would never reach the depot again)
        EmpPop.Information("emp_ui_depot_put_done".lang());
        EClass.scene.Init(Scene.Mode.Title);
        EClass.core.actionsNextFrame.Add(Take);
    }

    private static string Refusal(string why)
    {
        return why.StartsWith("held ") ? "emp_ui_depot_held".Loc(why.Substring(5)) :
            !GitHub ? why == "password" ? "emp_ui_depot_password_wrong" : "emp_ui_depot_fail" :
            why switch {
                "password" => "emp_ui_depot_gh_key",
                "missing" => "emp_ui_depot_gh_missing",
                "public" => "emp_ui_depot_gh_public",
                "too big" => "emp_ui_depot_gh_big",
                "changed" => "emp_ui_depot_gh_changed",
                _ => "emp_ui_depot_gh_down",
            };
    }

    /// <summary>
    ///     The save folder replaces the depot's world. The folder is written beside it, then swapped, so a copy
    ///     cut short never leaves half a world; the server does the same with its archive
    /// </summary>
    private static bool Copy(string save, bool replaces = false)
    {
        var sent = CopyTo(save, replaces);
        if (save == Local) {
            Mark(!sent);
        }

        return sent;
    }

    private static void Mark(bool unsent)
    {
        Marker(!unsent ? null : GitHub ? _descends ?? "" : _refused);
    }

    /// <param name="text">null: no marker</param>
    private static void Marker(string? text)
    {
        try {
            if (text is null) {
                File.Delete(Unsent);
            } else {
                File.WriteAllText(Unsent, text);
            }
        } catch (Exception ex) when (ex is IOException or UnauthorizedAccessException) {
            // the marker is a courtesy: the save itself is on this PC either way
        }
    }

    /// <summary>
    ///     The local copy now descends from this version of the depot's world (taken, or just sent)
    /// </summary>
    private static void Descends(string? sha)
    {
        if (sha is not null) {
            _descends = sha;
        }
    }

    /// <param name="replaces">the folder depot keeps the world it held aside (the server decides by itself)</param>
    private static bool CopyTo(string save, bool replaces)
    {
        _refused = "";
        try {
            if (Asked) {
                var reply = Ask("PUT", Zip(save), save == Local ? _descends : null);
                _refused = reply.Text;
                if (reply.Ok && GitHub) {
                    Descends(GitHubDepot.WorldSha);
                }

                if (!reply.Ok) {
                    EmpLog.Warning("The depot {Root} refused the world: {Reason}", Root, reply.Text);
                }

                return reply.Ok;
            }

            var incoming = World + ".new";
            var old = World + ".old";
            IO.DeleteDirectory(incoming);
            IO.CopyDir(save, incoming, name => name == "Temp");
            IO.DeleteDirectory(old);
            if (Directory.Exists(World)) {
                Directory.Move(World, replaces ? World + ".replaced-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") : old);
            }

            Directory.Move(incoming, World);
            IO.DeleteDirectory(old);
            EmpLog.Information("World sent to the depot {Root}", Root);
            return true;
        } catch (Exception ex) {
            EmpLog.Warning("Could not send the world to the depot {Root}: {Why}", Root, ex.GetBaseException().Message);
            return false;
        }
    }

    private static byte[] Zip(string save)
    {
        using var bytes = new MemoryStream();
        using (var zip = new ZipArchive(bytes, ZipArchiveMode.Create, true)) {
            foreach (var file in Directory.GetFiles(save, "*", SearchOption.AllDirectories)) {
                var name = file.Substring(save.Length).TrimStart('\\', '/').Replace('\\', '/');
                if (name.StartsWith("Temp/")) {
                    continue;
                }

                // (the date of the file, not of the archive: the same save makes the same archive, which is how
                // GitHub is known to have it already when its answer was lost)
                var entry = zip.CreateEntry(name);
                entry.LastWriteTime = File.GetLastWriteTime(file);
                using var from = File.OpenRead(file);
                using var to = entry.Open();
                from.CopyTo(to);
            }
        }

        return bytes.ToArray();
    }

    private static void Unzip(byte[] world, string folder)
    {
        var root = Path.GetFullPath(folder) + Path.DirectorySeparatorChar;
        using var zip = new ZipArchive(new MemoryStream(world), ZipArchiveMode.Read);
        long size = 0;
        foreach (var entry in zip.Entries) {
            size += entry.Length;
        }

        // (a small archive that unfolds into a full disk is not a world)
        if (size > MaxUnzipped) {
            throw new IOException("the depot sent a world too big once unzipped");
        }

        foreach (var entry in zip.Entries) {
            // (archives made by Windows write their folders with backslashes)
            var name = entry.FullName.Replace('\\', '/');
            var path = Path.GetFullPath(Path.Combine(root, name));
            // what comes from the network stays inside the save folder
            if (!path.StartsWith(root, StringComparison.OrdinalIgnoreCase)) {
                throw new IOException("the depot sent a file outside the save: " + entry.FullName);
            }

            if (name.EndsWith("/")) {
                Directory.CreateDirectory(path);
                continue;
            }

            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            using var from = entry.Open();
            using var to = File.Create(path);
            from.CopyTo(to);
        }
    }

    /// <summary>
    ///     One request to the server application: password, command and who asks on the first lines, then the
    ///     length and the bytes of a world when one is sent. The answer has the same shape
    /// </summary>
    // ponytail: on the game's thread, the game waits while a world of a few megabytes travels; a thread when
    // worlds get big or the link slow.
    private static (bool Ok, string Text, byte[]? Body) Ask(string command, byte[]? body = null, string? descends = null)
    {
        if (GitHub) {
            // ponytail: here too the game waits (Take, Put, "Join by address": the player just clicked), a few
            // seconds with GitHub, seven for the first request, and up to a minute behind a save still going
            Settle();
            return GitHubDepot.Ask(Root.Substring(7), EmpConfig.Client.DepotPassword.Value, command, Me, MyName, body,
                descends);
        }

        var at = Root.LastIndexOf(':');
        using var client = new TcpClient();
        if (!client.ConnectAsync(Root.Substring(0, at), int.Parse(Root.Substring(at + 1))).Wait(5000)) {
            throw new IOException("the depot does not answer");
        }

        using var stream = client.GetStream();
        stream.ReadTimeout = stream.WriteTimeout = 60000;
        var head = $"{EmpConfig.Client.DepotPassword.Value}\n{command}\n{Me}\n{MyName}\n{body?.Length ?? 0}\n";
        var bytes = Encoding.UTF8.GetBytes(head);
        stream.Write(bytes, 0, bytes.Length);
        if (body is not null) {
            stream.Write(body, 0, body.Length);
        }

        var status = ReadLine(stream);
        var length = int.Parse(ReadLine(stream));
        byte[]? answer = null;
        if (length > 0) {
            answer = new byte[length];
            for (var read = 0; read < length;) {
                var n = stream.Read(answer, read, length - read);
                if (n <= 0) {
                    throw new IOException("the depot stopped answering");
                }

                read += n;
            }
        }

        return (status.StartsWith("OK"), status.Length > 3 ? status.Substring(3) : "", answer);
    }

    private static string ReadLine(Stream stream)
    {
        var line = new MemoryStream();
        for (var b = stream.ReadByte(); b != '\n'; b = stream.ReadByte()) {
            if (b < 0) {
                throw new IOException("the depot stopped answering");
            }

            line.WriteByte((byte)b);
        }

        return Encoding.UTF8.GetString(line.ToArray());
    }

    /// <summary>
    ///     GitHub answers in a second or more (seven for the first request of the game): what happens while
    ///     playing is asked in the background, in order, and the answer is given on the game's thread (Update)
    /// </summary>
    /// <param name="sent">called in the background as soon as GitHub accepted (the game may be closing)</param>
    private static void Later(string command, byte[]? body, Action<(bool Ok, string Text, byte[]? Body)> then,
        Action? sent = null)
    {
        var (root, key, name) = (Root, EmpConfig.Client.DepotPassword.Value, MyName);
        _asking = _asking.ContinueWith(_ => {
            (bool Ok, string Text, byte[]? Body) reply;
            try {
                reply = GitHubDepot.Ask(root.Substring(7), key, command, Me, name, body);
                if (reply.Ok) {
                    sent?.Invoke();
                }
            } catch (Exception ex) {
                EmpLog.Warning("The depot {Root} did not answer {Command}: {Why}", root, command, ex.Message);
                reply = (false, "", null);
            }

            _answered.Enqueue(() => then(reply));
        }, Tasks.TaskScheduler.Default);
    }

    /// <summary>
    ///     Waits for what was asked in the background, and gives the answers
    /// </summary>
    private static void Settle()
    {
        _asking.Wait(60000);
        while (_answered.TryDequeue(out var then)) {
            then();
        }
    }

    /// <summary>
    ///     The last save of the depot's world goes to GitHub, in the background
    /// </summary>
    private static void SendLater()
    {
        _unsent = false;
        _nextSend = Time.unscaledTime + SendSeconds;
        var saved = _saves;
        byte[] world;
        try {
            world = Zip(Local);
        } catch (Exception ex) when (ex is IOException or UnauthorizedAccessException) {
            _unsent = true;
            return;
        }

        Later("PUT", world, reply => {
            _refused = reply.Text;
            if (reply.Ok) {
                EmpLog.Information("World sent to the depot {Root}", Root);
                return;
            }

            EmpLog.Warning("The depot {Root} did not take the world: {Reason}", Root, reply.Text);
            if (Lost(reply.Text)) {
                return;
            }

            // it goes again at the next sending; meanwhile the player knows, and why
            _unsent = true;
            EmpPop.Information(Refusal(reply.Text).lang() + " " + "emp_ui_depot_unsaved".lang());
        }, () => {
            // GitHub has this save: no marker, unless the game saved again meanwhile. Done here and not on the
            // game's thread, which no longer runs when the game is closing
            lock (_markGate) {
                Descends(GitHubDepot.WorldSha);
                Marker(saved == _saves ? null : _descends);
            }
        });
    }

    private static void Beat()
    {
        _nextBeat = Time.unscaledTime + BeatSeconds;
        if (GitHub) {
            Later("BEAT", null, reply => Lost(reply.Text));
        } else if (Remote) {
            Lost(Ask("BEAT").Text);
        } else {
            File.WriteAllLines(LockFile, [Me, MyName]);
        }
    }

    // every save of the depot's world by the player who took it goes back to the depot
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Game), nameof(Game.Save))]
    private static void OnSaved(bool __result)
    {
        if (!__result || !Holding) {
            return;
        }

        if (GitHub) {
            // the marker first: a game that closes before GitHub has the save offers to send it next time
            lock (_markGate) {
                _saves++;
                _unsent = true;
                Mark(true);
            }

            return;
        }

        if (Copy(Local)) {
            if (!Remote) {
                Beat();
            }
        } else if (!Lost(_refused)) {
            EmpPop.Information("emp_ui_depot_unsaved".lang());
        }
    }

    /// <summary>
    ///     The depot answered that another player hosts the world: this game was cut off long enough for the
    ///     lock to pass on. Said once, in a dialog: nothing played from here on reaches the depot
    /// </summary>
    private static bool Lost(string why)
    {
        if (why != "changed" && !why.StartsWith("held ")) {
            return false;
        }

        if (!_lostTold) {
            _lostTold = true;
            Dialog.Ok(why == "changed" ? "emp_ui_depot_gh_changed" : "emp_ui_depot_lost".Loc(why.Substring(5)));
        }

        return true;
    }

    /// <summary>
    ///     Called every frame: the holder says it is still there
    /// </summary>
    internal static void Update()
    {
        while (_answered.TryDequeue(out var then)) {
            then();
        }

        // at most one world every five minutes goes to GitHub: the last one saved, and always the one at the exit
        if (_unsent && Time.unscaledTime >= _nextSend && Holding) {
            SendLater();
        }

        if (Time.unscaledTime < _nextBeat || !Holding) {
            return;
        }

        try {
            Beat();
        } catch (Exception ex) when (ex is IOException or SocketException or AggregateException) {
            // next minute
        }
    }

    [ElinPostSceneInit]
    private static void ReleaseAtTitle(Scene.Mode mode)
    {
        if (mode != Scene.Mode.Title || !Enabled) {
            return;
        }

        try {
            if (GitHub) {
                if (_unsent) {
                    SendLater();
                }

                Later("RELEASE", null, _ => { });
            } else if (Remote) {
                Ask("RELEASE");
            } else if (File.Exists(LockFile) && File.ReadAllLines(LockFile) is { Length: > 0 } lines && lines[0] == Me) {
                File.Delete(LockFile);
            }
        } catch (Exception ex) when (ex is IOException or SocketException or AggregateException) {
            // it expires by itself
        }
    }
}
