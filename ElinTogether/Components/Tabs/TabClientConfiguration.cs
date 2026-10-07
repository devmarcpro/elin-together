using ElinTogether.Helper;
using ElinTogether.LangMod;
using UnityEngine;
using YKF;

namespace ElinTogether.Components;

internal class TabClientConfiguration : TabEmpBase
{
    public override void OnLayout()
    {
        var pingKey = new EInput.KeyMap {
            action = EAction.None,
            key = KeyCode.P,
            required = true,
        };
        Row().Button("emp_ui_ping_keymap".Loc(pingKey.key.ToString()), () => {
            var l = global::Layer.Create<Dialog>("DialogKeymap");
            l.textDetail.SetText("dialog_keymap".lang("emp_ui_ping_action".lang()));
            l.keymap = pingKey;
            l.SetOnKill(() => {
                EmpConfig.Client.PingKeybind.Value = pingKey.key;
                LayerElinTogether.Instance?.Reopen();
            });
            EMono.ui.AddLayer(l);
        }).SetTooltipLang(EmpConfig.Client.PingKeybind.Description.Description);

        var depot = EmpConfig.Client.DepotPath;
        Row().Button("emp_ui_depot_folder".lang(), () => {
            Dialog.InputName("emp_ui_depot_folder_ask", depot.Value, (cancel, text) => {
                if (!cancel) {
                    depot.Value = text.Trim();
                    LayerElinTogether.Instance?.Reopen();
                }
            }).input.field.characterLimit = 0;
        }).SetTooltipLang(depot.Description.Description);
        Text(depot.Value.Length > 0 ? depot.Value : "-");

        var password = EmpConfig.Client.DepotPassword;
        Row().Button("emp_ui_depot_password".lang(), () => {
            // a password or an access key is never shown again: the box opens empty. Left empty, a GitHub key is
            // kept (a depot of Elin Together Server may have no password: there, empty removes it)
            Dialog.InputName("emp_ui_depot_password_ask", "", (cancel, text) => {
                if (!cancel && !(SaveDepot.GitHub && text.Trim().Length == 0)) {
                    password.Value = text.Trim();
                    LayerElinTogether.Instance?.Reopen();
                }
            }).input.field.characterLimit = 0;
        }).SetTooltipLang(password.Description.Description);
        Text(password.Value.Length > 0 ? "***" : "-");

        // how a private GitHub repository becomes the depot, where it is set
        Text("emp_ui_depot_gh_help".lang());

        // the mods of the game joined, fetched without subscribing (ModFetch): this player's own choice
        var fetch = EmpConfig.Client.FetchMods;
        Toggle("emp_ui_cl_fetch_mods", fetch.Value, value => fetch.Value = value)
            .SetTooltipLang(fetch.Description.Description);
        TextSmall("        " + "emp_ui_cl_desc_fetch_mods".lang());
    }

    private YKHorizontal Row()
    {
        var row = Horizontal();
        row.Layout.childForceExpandWidth = true;
        return row;
    }
}