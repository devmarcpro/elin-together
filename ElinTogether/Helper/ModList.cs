using System;
using System.Linq;
using System.Text;

namespace ElinTogether.Helper;

/// <summary>
///     The mods this game runs with, as a text a player can read and click: one line a mod, its Workshop page
///     when it has one. Written next to the world in its depot (modlist.txt) each time the world is sent there,
///     so that whoever takes the world knows what to install
/// </summary>
internal static class ModList
{
    private const string Page = "https://steamcommunity.com/sharedfiles/filedetails/?id=";

    private static string? _text;

    /// <summary>
    ///     Built once: the game activates its mods at startup and never again
    /// </summary>
    internal static string Text => _text ??= Build();

    private static string Build()
    {
        var text = new StringBuilder();
        text.Append("# Mods of this world (written by Elin Together ").Append(ModInfo.BuildVersion).Append(", game ")
            .Append(EClass.core.version.GetText()).Append(")\n");
        text.Append("# One line a mod: title, then its Steam Workshop page. Subscribe to each page, then restart Elin.\n\n");

        try {
            var mods = EClass.core.mods.packages
                .Where(p => p is { activated: true, builtin: false })
                .OrderBy(p => p.title, StringComparer.OrdinalIgnoreCase)
                .ToList();

            foreach (var mod in mods) {
                var workshop = (mod as EMod)?.workshopId;
                text.Append(mod.title).Append("\n    ");
                if (mod.id == ModInfo.Guid) {
                    // this fork is not the Workshop item it shares its id with
                    text.Append("https://github.com/devmarcpro/elin-together/releases (not the Workshop version: same version for every player)");
                } else if (!string.IsNullOrEmpty(workshop)) {
                    text.Append(Page).Append(workshop);
                } else {
                    text.Append("(installed by hand, not on the Workshop: ask the player who hosts) id ").Append(mod.id);
                }

                text.Append("\n");
            }
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Mod list could not be read");
            text.Append("(the list could not be read)\n");
        }

        return text.ToString();
    }
}
