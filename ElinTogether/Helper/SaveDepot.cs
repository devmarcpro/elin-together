using System;
using System.Diagnostics;
using System.IO;
using ElinTogether.LangMod;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     A server that is only the save: a folder every player can reach (a shared or synced folder) keeps the
///     world. Whoever comes first takes the world from it and hosts it with the mod as it is, the others join
///     that player, every save goes back to the folder, and when the host leaves the next one can take over. <br />
///     Depot folder: `world/` (a save folder) and `host.txt` (who hosts it now)
/// </summary>
[HarmonyPatch]
internal static class SaveDepot
{
    /// <summary>
    ///     The local save the depot's world is played from
    /// </summary>
    internal const string WorldId = "world_depot";

    // ponytail: a lock by file date, on a folder that may sync late: two players taking the world in the same
    // minute both get it and the last save wins. A real lock needs the depot to be a program that answers.
    private static readonly TimeSpan _lockLife = TimeSpan.FromMinutes(3);
    private const float BeatSeconds = 60f;

    private static float _nextBeat;

    private static string Root => EmpConfig.Client.DepotPath.Value.Trim();
    private static string World => Path.Combine(Root, "world");
    private static string LockFile => Path.Combine(Root, "host.txt");
    private static string Local => CorePath.RootSave + WorldId;

    /// <summary>
    ///     This game, among the ones that share the depot (two games of one machine are two)
    /// </summary>
    private static string Me { get; } = $"{Environment.MachineName}:{Process.GetCurrentProcess().Id}";

    internal static bool Enabled => Root.Length > 0 && Directory.Exists(Root);

    internal static bool HasWorld => Enabled && File.Exists(Path.Combine(World, "game.txt"));

    private static bool Holding => Enabled && EClass.core.IsGameStarted && Game.id == WorldId &&
                                   NetSession.Instance.Transport is not ElinNetClient;

    /// <summary>
    ///     The player hosting the depot's world right now, null when it is free (or ours)
    /// </summary>
    internal static string? HeldBy()
    {
        try {
            if (!File.Exists(LockFile) || DateTime.UtcNow - File.GetLastWriteTimeUtc(LockFile) > _lockLife) {
                return null;
            }

            var lines = File.ReadAllLines(LockFile);
            return lines.Length < 2 || lines[0] == Me ? null : lines[1];
        } catch (IOException) {
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

        if (!HasWorld) {
            Dialog.Ok("emp_ui_depot_empty");
            return;
        }

        try {
            IO.DeleteDirectory(Local);
            IO.CopyDir(World, Local);
            Beat();
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not take the world from the depot {Root}", Root);
            Dialog.Ok("emp_ui_depot_fail");
            return;
        }

        EmpLog.Information("Took the world from the depot {Root}", Root);
        Game.Load(WorldId, false);
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

        Dialog.Ok(Copy(CorePath.RootSave + Game.id) ? "emp_ui_depot_put_done" : "emp_ui_depot_fail");
    }

    /// <summary>
    ///     The save folder replaces the depot's world: written beside it, then swapped, so a copy cut short
    ///     never leaves half a world
    /// </summary>
    private static bool Copy(string save)
    {
        try {
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

    private static void Beat()
    {
        File.WriteAllLines(LockFile, [Me, EClass.core.IsGameStarted ? EClass.pc.Name : Environment.UserName]);
        _nextBeat = Time.unscaledTime + BeatSeconds;
    }

    // every save of the depot's world by the player who took it goes back to the depot
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Game), nameof(Game.Save))]
    private static void OnSaved(bool __result)
    {
        if (!__result || !Holding) {
            return;
        }

        if (Copy(Local)) {
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
        } catch (IOException) {
            _nextBeat = Time.unscaledTime + BeatSeconds;
        }
    }

    [ElinPostSceneInit]
    private static void ReleaseAtTitle(Scene.Mode mode)
    {
        if (mode != Scene.Mode.Title || !Enabled) {
            return;
        }

        try {
            if (File.Exists(LockFile) && File.ReadAllLines(LockFile) is { Length: > 0 } lines && lines[0] == Me) {
                File.Delete(LockFile);
            }
        } catch (IOException) {
            // it expires by itself
        }
    }
}
