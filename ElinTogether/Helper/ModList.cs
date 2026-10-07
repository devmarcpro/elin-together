using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using ElinTogether.LangMod;
using Mod = ElinTogether.Helper.ModListFile.Mod;

namespace ElinTogether.Helper;

/// <summary>
///     The mods this game runs with, as a text a player can read and click: one line a mod, its Workshop page
///     when it has one. Written next to the world in its depot (modlist.txt) each time the world is sent there,
///     so that whoever takes the world knows what to install. <br />
///     Read back (ModListFile), that text is the list of the world: the host publishes it (Steam lobby, handshake)
///     and whoever takes the world or joins compares it with the mods loaded here. This fork is never in it
/// </summary>
internal static class ModList
{
    /// <summary>
    ///     A Workshop mod fetched for one session is seen by the game as a local mod in a folder of this name
    ///     followed by its Workshop number (ModFetch)
    /// </summary>
    internal const string SessionFolder = "EmpSession_";

    private static string? _text;
    private static List<Mod>? _here;

    /// <summary>
    ///     Built once: the game activates its mods at startup and never again
    /// </summary>
    internal static string Text => _text ??= Build();

    /// <summary>
    ///     The mods active in this game, this fork left out
    /// </summary>
    internal static List<Mod> Here => _here ??= Active()
        .Where(p => p.id != ModInfo.Guid)
        .Select(p => new Mod(p.id ?? "", WorkshopOf(p), ModListFile.Clean(p.title ?? "")))
        .ToList();

    /// <summary>
    ///     modlist.txt of the depot the world was taken from. Null: the depot has none
    /// </summary>
    internal static string? World { get; set; }

#if DEBUG
    /// <summary>
    ///     The bench gives the list a window publishes: two windows of one PC have the same mods
    /// </summary>
    internal static string? Bench { get; set; }
#endif

    /// <summary>
    ///     What the host publishes: the list of the world when it came from a depot, else the mods of this game
    /// </summary>
    internal static string Reference =>
#if DEBUG
        Bench ??
#endif
        (SaveDepot.Taken && World is { Length: > 0 and < 32768 } world ? world : Text);

    /// <summary>
    ///     The reference for the Steam lobby, read before joining: "mods without a Workshop number;Workshop
    ///     numbers". All the data of a lobby is about 8 KB: a list too long is only counted ("*count")
    /// </summary>
    internal static string Compact
    {
        get {
            var mods = ModListFile.Parse(Reference);
            var ids = string.Join(",", mods.Where(m => m.Workshop.Length > 0).Select(m => m.Workshop));
            var hand = mods.Count(m => m.Workshop.Length == 0);
            return ids.Length > 4000 ? $"{hand};*{mods.Count - hand}" : $"{hand};{ids}";
        }
    }

    /// <summary>
    ///     From the data of a lobby: how many mods that game has and how many of its Workshop mods are not active
    ///     here (-1: not said). Null: that host publishes no list
    /// </summary>
    internal static (int Count, int Missing)? Summary(string? compact)
    {
        var parts = (compact ?? "").Split(';');
        if (parts.Length != 2 || !int.TryParse(parts[0], out var hand)) {
            return null;
        }

        if (parts[1].StartsWith("*")) {
            return int.TryParse(parts[1].Substring(1), out var count) ? (count + hand, -1) : null;
        }

        var ids = parts[1].Split([','], StringSplitOptions.RemoveEmptyEntries);
        var here = new HashSet<string>(Here.Select(m => m.Workshop));
        return (ids.Length + hand, ids.Count(id => !here.Contains(id)));
    }

    /// <summary>
    ///     The reference against the mods active here, with one line in the log
    /// </summary>
    internal static Diff Compare(List<Mod> reference, string source)
    {
        reference = reference.Where(m => Norm(m.Id) != ModInfo.Guid).ToList();
        var here = Here;
        var workshops = new HashSet<string>(here.Where(m => m.Workshop.Length > 0).Select(m => m.Workshop));
        var ids = new HashSet<string>(here.Select(m => Norm(m.Id)));
        var wanted = new HashSet<string>(reference.Where(m => m.Workshop.Length > 0).Select(m => m.Workshop));
        var wantedIds = new HashSet<string>(reference.Where(m => m.Id.Length > 0).Select(m => Norm(m.Id)));

        var diff = new Diff(
            reference.Where(m => m.Workshop.Length > 0 && !workshops.Contains(m.Workshop)).ToList(),
            reference.Where(m => m.Workshop.Length == 0 && (m.Id.Length == 0 || !ids.Contains(Norm(m.Id)))).ToList(),
            here.Where(m => !wanted.Contains(m.Workshop) && !wantedIds.Contains(Norm(m.Id))).ToList());

        EmpLog.Information(
            "Mods compared with {Source} ({Count} mods there, {Here} here): missing here {Missing}, " +
            "cannot be fetched {Unfetchable}, extra here {Extra}",
            source, reference.Count, here.Count, diff.Missing.Select(Describe).ToList(), diff.Unfetchable.Select(Describe).ToList(),
            diff.Extra.Select(Describe).ToList());
        return diff;
    }

    /// <summary>
    ///     The world just taken lists mods that are not loaded here: one line on screen, the list is in the log
    /// </summary>
    internal static void Tell(Diff diff)
    {
        var absent = diff.Missing.Concat(diff.Unfetchable).ToList();
        if (absent.Count > 0) {
            EmpPop.Information("emp_ui_mods_world".Loc(absent.Count, Names(absent)));
        }
    }

    /// <summary>
    ///     For the window of a refused join: what differs, by name
    /// </summary>
    internal static string Lines(Diff diff)
    {
        var text = new StringBuilder();
        Line("emp_ui_mods_missing", diff.Missing);
        Line("emp_ui_mods_hand", diff.Unfetchable);
        Line("emp_ui_mods_extra", diff.Extra);
        return text.ToString();

        void Line(string id, List<Mod> mods)
        {
            if (mods.Count > 0) {
                text.AppendLine(id.Loc(mods.Count, Names(mods)));
            }
        }
    }

    internal static string Name(Mod mod)
    {
        return mod.Title.Length > 0 ? mod.Title : mod.Workshop.Length > 0 ? mod.Workshop : mod.Id;
    }

    /// <summary>
    ///     The Workshop number of a package: its folder in the Workshop, or the link made for a session
    /// </summary>
    internal static string WorkshopOf(BaseModPackage package)
    {
        var workshop = (package as EMod)?.workshopId?.Trim() ?? "";
        var folder = package.dirInfo?.Name ?? "";
        return workshop.Length > 0 ? workshop :
            folder.StartsWith(SessionFolder, StringComparison.OrdinalIgnoreCase) ? folder.Substring(SessionFolder.Length) : "";
    }

    private static string Names(List<Mod> mods)
    {
        var names = string.Join(", ", mods.Take(4).Select(Name));
        return mods.Count > 4 ? names + ", ..." : names;
    }

    private static string Describe(Mod mod)
    {
        return mod.Workshop.Length > 0 ? $"{Name(mod)} {ModListFile.Page}{mod.Workshop}" : $"{Name(mod)} (id {mod.Id})";
    }

    private static string Norm(string id)
    {
        return id.Trim().ToLowerInvariant();
    }

    private static List<BaseModPackage> Active()
    {
        try {
            return EClass.core.mods.packages.Where(p => p is { activated: true, builtin: false }).ToList();
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Mod list could not be read");
            return [];
        }
    }

    private static string Build()
    {
        var text = new StringBuilder();
        text.Append("# Mods of this world (written by Elin Together ").Append(ModInfo.BuildVersion).Append(", game ")
            .Append(EClass.core.version.GetText()).Append(")\n");
        text.Append("# One line a mod: title, then its Steam Workshop page. Subscribe to each page, then restart Elin.\n\n");

        foreach (var mod in Active().OrderBy(p => p.title, StringComparer.OrdinalIgnoreCase)) {
            var workshop = WorkshopOf(mod);
            text.Append(mod.title).Append("\n    ");
            if (mod.id == ModInfo.Guid) {
                // this fork is not the Workshop item it shares its id with
                text.Append("https://github.com/devmarcpro/elin-together/releases (not the Workshop version: same version for every player)");
            } else if (!string.IsNullOrEmpty(workshop)) {
                text.Append(ModListFile.Page).Append(workshop);
            } else {
                text.Append("(installed by hand, not on the Workshop: ask the player who hosts) id ").Append(mod.id);
            }

            text.Append("\n");
        }

        return text.ToString();
    }

    /// <param name="Missing">in the reference with a Workshop number, not active here</param>
    /// <param name="Unfetchable">in the reference without a Workshop number, not active here</param>
    /// <param name="Extra">active here, not in the reference</param>
    internal sealed record Diff(List<Mod> Missing, List<Mod> Unfetchable, List<Mod> Extra);
}
