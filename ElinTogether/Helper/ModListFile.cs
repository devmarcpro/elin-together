using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace ElinTogether.Helper;

/// <summary>
///     modlist.txt read back: the text ModList writes, or the same file changed by hand in the depot. Nothing of
///     the game in here (dev/_tools/github_depot_cli compiles this file too, for depot_github_test.py)
/// </summary>
internal static class ModListFile
{
    /// <summary>
    ///     The Workshop item this fork shares its id with: never fetched, never compared (the handshake checks
    ///     the version of the mod itself)
    /// </summary>
    internal const string Original = "3773298709";

    internal const string Page = "https://steamcommunity.com/sharedfiles/filedetails/?id=";

    private static readonly Regex _link = new(@"filedetails/\?id=(\d{1,20})", RegexOptions.IgnoreCase);
    private static readonly Regex _hand = new(@"\bid\s+(\S+)\s*$");
    private static readonly Regex _unsafe = new(@"[<>{}\x00-\x1f]");

    /// <param name="Id">the id of its package.xml, empty when the file does not say</param>
    /// <param name="Workshop">its Workshop number, empty for a mod installed by hand: that one cannot be fetched</param>
    internal readonly record struct Mod(string Id, string Workshop, string Title);

    /// <summary>
    ///     Any line with a Workshop page is a mod, named by the line before it (or by what precedes the link on
    ///     its own line); "#" starts a comment; "installed by hand" lines are mods without a Workshop number; the
    ///     line of this fork is left out
    /// </summary>
    internal static List<Mod> Parse(string? text)
    {
        var mods = new List<Mod>();
        var seen = new HashSet<string>();
        var title = "";
        foreach (var raw in (text ?? "").Split('\n')) {
            var line = raw.Trim().Trim('﻿').Trim();
            if (line.Length == 0 || line[0] == '#') {
                continue;
            }

            var link = _link.Match(line);
            if (link.Success) {
                var at = line.LastIndexOfAny([' ', '\t'], link.Index) + 1;
                var before = line.Substring(0, at).Trim(' ', '\t', '-', '*', ':');
                var workshop = link.Groups[1].Value.TrimStart('0');
                if (ulong.TryParse(workshop, out var number) && number != 0 && workshop != Original && seen.Add(workshop)) {
                    mods.Add(new("", workshop, Clean(before.Length > 0 ? before : title)));
                }

                title = "";
            } else if (line.IndexOf("elin-together/releases", StringComparison.OrdinalIgnoreCase) >= 0) {
                title = "";
            } else if (line.StartsWith("(installed by hand", StringComparison.OrdinalIgnoreCase)) {
                var id = _hand.Match(line);
                mods.Add(new(id.Success ? id.Groups[1].Value : "", "", Clean(title)));
                title = "";
            } else {
                title = line;
            }
        }

        return mods;
    }

    /// <summary>
    ///     A title comes from another player's file: nothing in it is markup, and it stays one short line
    /// </summary>
    internal static string Clean(string title)
    {
        title = _unsafe.Replace(title, "").Trim();
        return title.Length > 60 ? title.Substring(0, 60) : title;
    }
}
