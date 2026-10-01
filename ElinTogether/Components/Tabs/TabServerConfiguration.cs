using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Net;
using UnityEngine.UI;
using YKF;

namespace ElinTogether.Components;

internal class TabServerConfiguration : TabEmpBase
{
    public override void OnLayout()
    {
        BuildValidationSets();

        BuildSyncMode();
    }

    private void BuildValidationSets()
    {
        var sets = this.MakeCard();

        sets.TextFlavor("emp_ui_sv_cfg_validation_sets");

        var list = sets.Grid()
            .WithConstraintCount(2);
        list.Fitter.horizontalFit = ContentSizeFitter.FitMode.Unconstrained;
        list.Layout.cellSize = FitCell(2);

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

    private void BuildSyncMode()
    {
        var modes = this.MakeCard();

        modes.Toggle("emp_ui_sv_cfg_shared_speed", EmpConfig.Server.SharedAverageSpeed.Value,
                value => EmpConfig.Server.SharedAverageSpeed.Value = value)
            .SetTooltipLang(EmpConfig.Server.SharedAverageSpeed.Description.Description);

        modes.Toggle("emp_ui_sv_cfg_turn_combat", EmpConfig.Server.TurnBasedCombat.Value,
                value => EmpConfig.Server.TurnBasedCombat.Value = value)
            .SetTooltipLang(EmpConfig.Server.TurnBasedCombat.Description.Description);

        modes.Toggle("emp_ui_sv_cfg_combat_time", EmpConfig.Server.PlayerCombatTime.Value,
                value => EmpConfig.Server.PlayerCombatTime.Value = value)
            .SetTooltipLang(EmpConfig.Server.PlayerCombatTime.Description.Description);

        // off: everyone stays on the map of the host, as before
        modes.Toggle("emp_ui_sv_cfg_independent_travel", EmpConfig.Server.IndependentTravel.Value,
                value => EmpConfig.Server.IndependentTravel.Value = value)
            .SetTooltipLang(EmpConfig.Server.IndependentTravel.Description.Description);

        modes.Toggle("emp_ui_sv_cfg_player_shipping", EmpConfig.Server.PlayerShipping.Value,
                value => EmpConfig.Server.PlayerShipping.Value = value)
            .SetTooltipLang(EmpConfig.Server.PlayerShipping.Description.Description);

        // off: one quest log and one fame for the whole group
        modes.Toggle("emp_ui_sv_cfg_personal_quests", EmpConfig.Server.PersonalQuests.Value,
                value => EmpConfig.Server.PersonalQuests.Value = value)
            .SetTooltipLang(EmpConfig.Server.PersonalQuests.Description.Description);

        // off: a player always gets the character it played last
        modes.Toggle("emp_ui_sv_cfg_choose_chara", EmpConfig.Server.ChooseCharacter.Value,
                value => EmpConfig.Server.ChooseCharacter.Value = value)
            .SetTooltipLang(EmpConfig.Server.ChooseCharacter.Description.Description);
    }
}