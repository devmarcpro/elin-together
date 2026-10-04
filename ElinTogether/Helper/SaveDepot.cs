using System;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;
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
///     application of dev/server: it keeps the world as one archive and holds a real lock), or a folder every
///     player can reach (`world/` and `host.txt`, a lock by file date)
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

    private static float _nextBeat;
    private static string _refused = "";

    private static string Root => EmpConfig.Client.DepotPath.Value.Trim();
    private static string World => Path.Combine(Root, "world");
    private static string LockFile => Path.Combine(Root, "host.txt");
    private static string Local => CorePath.RootSave + WorldId;

    /// <summary>
    ///     The depot is the server application, not a folder
    /// </summary>
    private static bool Remote => Regex.IsMatch(Root, @"^[^\\/\s]+:\d+$");

    /// <summary>
    ///     This game, among the ones that share the depot (two games of one machine are two)
    /// </summary>
    private static string Me { get; } = $"{Environment.MachineName}:{Process.GetCurrentProcess().Id}";

    private static string MyName => EClass.core.IsGameStarted ? EClass.pc.Name : Environment.UserName;

    internal static bool Enabled => Root.Length > 0 && (Remote || Directory.Exists(Root));

    private static bool Holding => Enabled && EClass.core.IsGameStarted && Game.id == WorldId &&
                                   NetSession.Instance.Transport is not ElinNetClient;

    /// <summary>
    ///     The player hosting the depot's world right now, null when it is free (or ours)
    /// </summary>
    internal static string? HeldBy()
    {
        try {
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
        if (HeldBy() is { } who) {
            Dialog.Ok("emp_ui_depot_held".Loc(who));
            return;
        }

        try {
            if (Remote) {
                var reply = Ask("TAKE");
                if (!reply.Ok) {
                    Dialog.Ok(reply.Text == "empty" ? "emp_ui_depot_empty" : Refusal(reply.Text));
                    return;
                }

                IO.DeleteDirectory(Local);
                Unzip(reply.Body!, Local);
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
            Dialog.Ok("emp_ui_depot_fail");
            return;
        }

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
        try {
            if (!Remote) {
                throw new IOException("not an address");
            }

            Ask("WHO");
        } catch (Exception) {
            depot.Value = before;
            return false;
        }

        Take();
        return true;
    }

    /// <summary>
    ///     Puts the save being played in the depot, as its world
    /// </summary>
    internal static void Put()
    {
        if (HeldBy() is { } who) {
            Dialog.Ok("emp_ui_depot_held".Loc(who));
            return;
        }

        if (!EClass.game.Save(silent: true)) {
            return;
        }

        Dialog.Ok(Copy(CorePath.RootSave + Game.id) ? "emp_ui_depot_put_done" : Refusal(_refused));
    }

    private static string Refusal(string why)
    {
        return why == "password" ? "emp_ui_depot_password_wrong" : "emp_ui_depot_fail";
    }

    /// <summary>
    ///     The save folder replaces the depot's world. The folder is written beside it, then swapped, so a copy
    ///     cut short never leaves half a world; the server does the same with its archive
    /// </summary>
    private static bool Copy(string save)
    {
        try {
            if (Remote) {
                var reply = Ask("PUT", Zip(save));
                _refused = reply.Text;
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
                Directory.Move(World, old);
            }

            Directory.Move(incoming, World);
            IO.DeleteDirectory(old);
            EmpLog.Information("World sent to the depot {Root}", Root);
            return true;
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not send the world to the depot {Root}", Root);
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

                using var from = File.OpenRead(file);
                using var to = zip.CreateEntry(name).Open();
                from.CopyTo(to);
            }
        }

        return bytes.ToArray();
    }

    private static void Unzip(byte[] world, string folder)
    {
        var root = Path.GetFullPath(folder) + Path.DirectorySeparatorChar;
        using var zip = new ZipArchive(new MemoryStream(world), ZipArchiveMode.Read);
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
    private static (bool Ok, string Text, byte[]? Body) Ask(string command, byte[]? body = null)
    {
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

    private static void Beat()
    {
        _nextBeat = Time.unscaledTime + BeatSeconds;
        if (Remote) {
            Ask("BEAT");
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

        if (Copy(Local) && !Remote) {
            Beat();
        }
    }

    /// <summary>
    ///     Called every frame: the holder says it is still there
    /// </summary>
    internal static void Update()
    {
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
            if (Remote) {
                Ask("RELEASE");
            } else if (File.Exists(LockFile) && File.ReadAllLines(LockFile) is { Length: > 0 } lines && lines[0] == Me) {
                File.Delete(LockFile);
            }
        } catch (Exception ex) when (ex is IOException or SocketException or AggregateException) {
            // it expires by itself
        }
    }
}
