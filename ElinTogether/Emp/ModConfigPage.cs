using System.Linq;
using BepInEx.Configuration;
using ElinTogether.Components;

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

        package.onBuildConfig = Build;
        package.onResetConfig = EmpConfig.Reset;
        package.configPath = EmpMod.Instance.Config.ConfigFilePath;
    }

    private static void Build(UINote note)
    {
        note.AddHeader("emp_ui_sv_note_live".lang());

        foreach (var (section, options) in TabServerConfiguration.Sections()) {
            note.AddHeader($"emp_ui_sv_sec_{section}".lang());
            foreach (var (id, entry) in options) {
                Toggle(note, $"emp_ui_sv_cfg_{id}", $"emp_ui_sv_desc_{id}", entry);
            }
        }

        note.AddHeader("Client");
        Toggle(note, "emp_ui_cl_fetch_mods", "emp_ui_cl_desc_fetch_mods", EmpConfig.Client.FetchMods);
        Toggle(note, "emp_ui_cl_keep_mods", "emp_ui_cl_desc_keep_mods", EmpConfig.Client.KeepMods);
    }

    private static void Toggle(UINote note, string label, string desc, ConfigEntry<bool> entry)
    {
        note.AddToggle(label, entry.Value, value => entry.Value = value).SetTooltipLang(desc);
    }
}
