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
    public override void OnLayout()
    {
        TextSmall("emp_ui_sv_note_live".lang());

        var players = Section("players");
        Option(players, "independent_travel", EmpConfig.Server.IndependentTravel);
        Option(players, "choose_chara", EmpConfig.Server.ChooseCharacter);
        Option(players, "import_chara", EmpConfig.Server.ImportCharacter);
        Option(players, "auto_reconnect", EmpConfig.Server.AutoReconnect);
        Option(players, "auto_resync", EmpConfig.Server.AutoResync);
        Option(players, "auto_host", EmpConfig.Server.AutoHost);
        Option(players, "auto_save", EmpConfig.Server.AutoSave);
        Option(players, "world_copy", EmpConfig.Server.WorldCopy);
        Option(players, "same_game_version", EmpConfig.Server.SameGameVersion);

        var own = Section("own");
        Option(own, "personal_quests", EmpConfig.Server.PersonalQuests);
        Option(own, "player_shipping", EmpConfig.Server.PlayerShipping);
        Option(own, "player_trade", EmpConfig.Server.PlayerTrade);
        Option(own, "guest_build", EmpConfig.Server.GuestBuild);
        Option(own, "player_kill", EmpConfig.Server.PlayerKill);
        Option(own, "own_sleep", EmpConfig.Server.OwnSleep);
        Option(own, "time_jumps_together", EmpConfig.Server.TimeJumpsTogether);
        Option(own, "dump_spares_belt", EmpConfig.Server.DumpSparesBelt);
        Option(own, "shared_tax", EmpConfig.Server.SharedTax);
        Option(own, "host_manages_base", EmpConfig.Server.HostManagesBase);
        Option(own, "duels", EmpConfig.Server.Duels);

        var time = Section("time");
        Option(time, "combat_time", EmpConfig.Server.PlayerCombatTime);
        Option(time, "player_clock", EmpConfig.Server.PlayerClock);
        Option(time, "step_pace", EmpConfig.Server.PlayerStepPace);
        Option(time, "world_time", EmpConfig.Server.SharedWorldTime);
        Option(time, "world_keeper", EmpConfig.Server.WorldKeeper);
        Option(time, "turn_combat", EmpConfig.Server.TurnBasedCombat);
        Option(time, "shared_speed", EmpConfig.Server.SharedAverageSpeed);

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
            .SetTooltipLang(entry.Description.Description);
        card.TextSmall("        " + $"emp_ui_sv_desc_{id}".lang());
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
