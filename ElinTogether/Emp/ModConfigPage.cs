using System.Linq;
using BepInEx.Configuration;
using ElinTogether.Components;
using ElinTogether.Net;

namespace ElinTogether;

/// <summary>
///     The settings as the game's own mod config page (mod list, "Config" button): the host's rules and the
///     client's simple options. What needs a dialog (depot, keymap) stays in the mod's own window
/// </summary>
internal static class ModConfigPage
{
    internal static void Register()
    {
        var package = EClass.core.mods.packages.OfType<ModPackage>()
            .FirstOrDefault(p => BaseModPackage.NormalizeId(p.id) == BaseModPackage.NormalizeId(ModInfo.Guid));
        if (package == null) {
            return;
        }

        _package = package;
        package.onBuildConfig = Build;
        package.onResetConfig = EmpConfig.Reset;
        package.configPath = EmpMod.Instance.Config.ConfigFilePath;
        SettingsTable.Watch();
    }

    private static ModPackage? _package;

    /// <summary>
    ///     Drawn again (greyed boxes, choices) when a rule changes while the page is open
    /// </summary>
    internal static void Refresh()
    {
        if (EClass.ui?.GetLayer<LayerModConfig>() is { } layer && layer.current == _package && _package is not null) {
            layer.Show(_package);
        }
    }

    private static void Build(UINote note)
    {
        // the host's rules: not while playing in someone else's game, where the host's apply (the mod's own window
        // shows them only to the host too)
        if (NetSession.Instance.Transport is not ElinNetClient) {
            note.AddHeader("emp_ui_sv_note_live".lang());
            foreach (var (section, options) in TabServerConfiguration.Sections()) {
                note.AddHeader($"emp_ui_sv_sec_{section}".lang());
                foreach (var (id, entry) in options) {
                    var toggle = Toggle(note, $"emp_ui_sv_cfg_{id}", $"emp_ui_sv_desc_{id}", entry);
                    if (SettingsTable.Rows().FirstOrDefault(r => r.Id == id)?.Requires is { } requires) {
                        toggle.interactable = requires();
                    }
                }

                if (section == "time") {
                    UIButton? button = null;
                    button = note.AddButton(TabServerConfiguration.WorldMapTimeLabel(), () => {
                        TabServerConfiguration.NextWorldMapTime();
                        button!.mainText.text = TabServerConfiguration.WorldMapTimeLabel();
                    });
                    button.SetTooltipLang("emp_ui_sv_desc_world_map_time");
                }
            }
        }

        note.AddHeader("emp_ui_tab_client".lang());
        Toggle(note, "emp_ui_cl_fetch_mods", "emp_ui_cl_desc_fetch_mods", EmpConfig.Client.FetchMods);
        Toggle(note, "emp_ui_cl_keep_mods", "emp_ui_cl_desc_keep_mods", EmpConfig.Client.KeepMods).interactable =
            EmpConfig.Client.FetchMods.Value;
    }

    private static UIButton Toggle(UINote note, string label, string desc, ConfigEntry<bool> entry)
    {
        var toggle = note.AddToggle(label, entry.Value, value => entry.Value = value);
        toggle.SetTooltipLang(desc);
        // (no tooltip on a controller: the text under the box)
        note.AddText(desc);
        return toggle;
    }
}
