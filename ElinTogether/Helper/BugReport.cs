using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using ElinTogether.Net;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     One zip a player can send when something goes wrong: the game's own log (where the game writes its
///     exceptions, which the mod's log does not have), the last logs of the mod, and a short note of the
///     situation. Until now reports came as screenshots, or with the one log that did not hold the error <br />
///     Never in it: the saves, and the settings file (it holds the depot's password or access key)
/// </summary>
internal static class BugReport
{
    private const int ModLogs = 4;

    /// <returns>the zip written, or null with the reason logged</returns>
    internal static string? Make()
    {
        try {
            var data = Application.persistentDataPath;
            var desktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
            var folder = Directory.Exists(desktop) ? desktop : data;
            var path = Path.Combine(folder, $"ElinTogether-rapport-{DateTime.Now:yyyyMMdd-HHmmss}.zip");

            using (var file = new FileStream(path, FileMode.Create))
            using (var zip = new ZipArchive(file, ZipArchiveMode.Create)) {
                Add(zip, "info.txt", Encoding.UTF8.GetBytes(Describe()));
                foreach (var name in new[] { "Player.log", "Player-prev.log" }) {
                    AddFile(zip, Path.Combine(data, name), name);
                }

                var logs = Path.Combine(data, "ElinMP", "Logs");
                if (Directory.Exists(logs)) {
                    foreach (var log in new DirectoryInfo(logs).GetFiles("*.log").OrderByDescending(f => f.LastWriteTimeUtc).Take(ModLogs)) {
                        AddFile(zip, log.FullName, "ElinMP/" + log.Name);
                    }
                }
            }

            EmpLog.Information("Bug report written to {Path}", path);
            return path;
        } catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or NotSupportedException) {
            EmpLog.Warning(ex, "The bug report could not be written");
            return null;
        }
    }

    private static string Describe()
    {
        var session = NetSession.Instance;
        var text = new StringBuilder();
        text.AppendLine($"Elin Together {ModInfo.BuildVersion}");
        text.AppendLine($"Elin {EClass.core.version.GetText()}");
        text.AppendLine($"Written {DateTime.Now:yyyy-MM-dd HH:mm:ss} (local), {DateTime.UtcNow:HH:mm:ss} UTC");
        text.AppendLine($"Role: {(session.Transport is null ? "no session" : session.Transport.GetType().Name)}, away: {session.IsAway}, guest: {session.IsGuest}");
        text.AppendLine($"Players: {session.CurrentPlayers.Count}");
        if (EClass.core.IsGameStarted) {
            text.AppendLine($"Zone: {EClass._zone?.id} #{EClass._zone?.uid}, date raw {EClass.world.date.GetRaw()}");
        }

        try {
            text.AppendLine("Mods: " + string.Join(", ", EClass.core.mods.packages.Where(p => p.activated).Select(p => p.id)));
        } catch (Exception) {
            // (the list of mods is not worth losing the report for)
        }

        return text.ToString();
    }

    private static void Add(ZipArchive zip, string name, byte[] bytes)
    {
        using var entry = zip.CreateEntry(name, System.IO.Compression.CompressionLevel.Optimal).Open();
        entry.Write(bytes, 0, bytes.Length);
    }

    // (the game and the mod keep their logs open: read without asking for them alone)
    private static void AddFile(ZipArchive zip, string path, string name)
    {
        if (!File.Exists(path)) {
            return;
        }

        try {
            using var source = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
            using var entry = zip.CreateEntry(name, System.IO.Compression.CompressionLevel.Optimal).Open();
            source.CopyTo(entry);
        } catch (IOException) {
            // noexcept
        }
    }
}
