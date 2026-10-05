using ElinTogether.Helper;
using ElinTogether.LangMod;
using UnityEngine;

namespace ElinTogether.Components;

internal class TabClientConfiguration : TabEmpBase
{
    public override void OnLayout()
    {
        var btnGroup = Horizontal();
        btnGroup.Layout.childForceExpandWidth = true;

        var pingKey = new EInput.KeyMap {
            action = EAction.None,
            key = KeyCode.P,
            required = true,
        };
        btnGroup.Button("emp_ui_ping_keymap".Loc(pingKey.key.ToString()), () => {
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
        btnGroup.Button("emp_ui_depot_folder".Loc(depot.Value.Length > 0 ? depot.Value : "-"), () => {
            Dialog.InputName("emp_ui_depot_folder_ask", depot.Value, (cancel, text) => {
                if (!cancel) {
                    depot.Value = text.Trim();
                    LayerElinTogether.Instance?.Reopen();
                }
            });
        }).SetTooltipLang(depot.Description.Description);

        var password = EmpConfig.Client.DepotPassword;
        btnGroup.Button("emp_ui_depot_password".Loc(password.Value.Length > 0 ? "***" : "-"), () => {
            // a password or an access key is never shown again: the box opens empty. Left empty, a GitHub key is
            // kept (a depot of Elin Together Server may have no password: there, empty removes it)
            Dialog.InputName("emp_ui_depot_password_ask", "", (cancel, text) => {
                if (!cancel && !(SaveDepot.GitHub && text.Trim().Length == 0)) {
                    password.Value = text.Trim();
                    LayerElinTogether.Instance?.Reopen();
                }
            });
        }).SetTooltipLang(password.Description.Description);

        // how a private GitHub repository becomes the depot, where it is set
        Text("emp_ui_depot_gh_help".lang());
    }
}