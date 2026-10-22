using ElinTogether.LangMod;
using System.Collections.Generic;
using BepInEx.Configuration;
using ElinTogether.Helper;
using ElinTogether.Net;
using UnityEngine.UI;
using YKF;

namespace ElinTogether.Components;

/// <summary>
///     The rules of the host, by subject: players and where they go, what is each player's own, how time and
///     combat run, and at the bottom what a joining player's game has to match
/// </summary>
internal class TabServerConfiguration : TabEmpBase
{
    /// <summary>
    ///     The host's checkbox rules by section: shared by this tab and the game's own mod config page (ModConfigPage)
    /// </summary>
    internal static IEnumerable<(string Section, (string Id, ConfigEntry<bool> Entry)[] Options)> Sections()
    {
        yield return ("players", [
            ("independent_travel", EmpConfig.Server.IndependentTravel),
            ("choose_chara", EmpConfig.Server.ChooseCharacter),
            ("import_chara", EmpConfig.Server.ImportCharacter),
            ("delete_chara", EmpConfig.Server.DeleteCharacter),
            ("auto_reconnect", EmpConfig.Server.AutoReconnect),
            ("auto_resync", EmpConfig.Server.AutoResync),
            ("soft_recall", EmpConfig.Server.SoftRecall),
            ("auto_host", EmpConfig.Server.AutoHost),
            ("auto_save", EmpConfig.Server.AutoSave),
            ("world_copy", EmpConfig.Server.WorldCopy),
            ("takeover", EmpConfig.Server.Takeover),
            ("same_game_version", EmpConfig.Server.SameGameVersion),
            ("publish_mods", EmpConfig.Server.PublishMods),
        ]);
        yield return ("own", [
            ("personal_quests", EmpConfig.Server.PersonalQuests),
            ("player_shipping", EmpConfig.Server.PlayerShipping),
            ("player_trade", EmpConfig.Server.PlayerTrade),
            ("guest_build", EmpConfig.Server.GuestBuild),
            ("player_kill", EmpConfig.Server.PlayerKill),
            ("own_sleep", EmpConfig.Server.OwnSleep),
            ("time_jumps_together", EmpConfig.Server.TimeJumpsTogether),
            ("dump_spares_belt", EmpConfig.Server.DumpSparesBelt),
            ("shared_tax", EmpConfig.Server.SharedTax),
            ("once_per_player", EmpConfig.Server.OncePerPlayer),
            ("host_manages_base", EmpConfig.Server.HostManagesBase),
            ("duels", EmpConfig.Server.Duels),
            ("auto_combat_per_player", EmpConfig.Server.AutoCombatPerPlayer),
        ]);
        yield return ("time", [
            ("combat_time", EmpConfig.Server.PlayerCombatTime),
            ("player_clock", EmpConfig.Server.PlayerClock),
            ("step_pace", EmpConfig.Server.PlayerStepPace),
            ("world_time", EmpConfig.Server.SharedWorldTime),
            ("world_keeper", EmpConfig.Server.WorldKeeper),
            ("turn_combat", EmpConfig.Server.TurnBasedCombat),
            ("shared_speed", EmpConfig.Server.SharedAverageSpeed),
        ]);
    }

    public override void OnLayout()
    {
        TextSmall("emp_ui_sv_note_live".lang());

        foreach (var (id, options) in Sections()) {
            var card = Section(id);
            foreach (var (option, entry) in options) {
                Option(card, option, entry);
            }
        }

        // the count of unpaid tax bills against the bills that exist (ElinNetHost.RepairBillCount), for a host in game
        if (EClass.core.IsGameStarted && NetSession.Instance.Transport is ElinNetHost) {
            var (count, found) = (EClass.player.taxBills, ElinNetHost.CountTaxBills());
            Button("emp_ui_sv_bills".Loc(count, found), () => {
                var off = ElinNetHost.RepairBillCount(true);
                EmpPop.Information((off > 0 ? "emp_ui_sv_bills_done" : "emp_ui_sv_bills_none").Loc(off));
                LayerElinTogether.Instance?.Reopen();
            });
            TextSmall("emp_ui_sv_bills_desc".lang());
        }

        BuildValidationSets();
    }

    private YKVertical Section(string id)
    {
        var card = this.MakeCard();
        card.Layout.padding = new(20, 20, 8, 10);
        card.HeaderSmall($"emp_ui_sv_sec_{id}".lang());
        return card;
    }

    /// <summary>
    ///     A checkbox and, under it, what it does when on and off in one line
    /// </summary>
    private static void Option(YKVertical card, string id, ConfigEntry<bool> entry)
    {
        card.Toggle($"emp_ui_sv_cfg_{id}", entry.Value, value => entry.Value = value)
            .SetTooltipLang($"emp_ui_sv_desc_{id}");
    }

    private void BuildValidationSets()
    {
        var sets = Section("checks");

        sets.TextSmall("emp_ui_sv_desc_validation".lang());

        var list = sets.Grid()
            .WithConstraintCount(4);
        list.Fitter.horizontalFit = ContentSizeFitter.FitMode.Unconstrained;
        list.Layout.cellSize = FitCell(4);

        var options = new List<string> {
            "none",
            "sources",
            "plugins",
            "all",
        };

        foreach (var option in options) {
            list.Toggle($"emp_validation_{option}", EmpConfig.Server.SourceValidationSet.Value.Contains(option), value => {
                var raw = EmpConfig.Server.SourceValidationSet.Value;
                raw = raw.Replace($"{option},", "").Replace(option, "");
                if (value) {
                    raw = $"{option},{raw}";
                }
                EmpConfig.Server.SourceValidationSet.Value = raw;
                NetSession.Instance.Transport?.CreateValidation();
            });
        }
    }
}
