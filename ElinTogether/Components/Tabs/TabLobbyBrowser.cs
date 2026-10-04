using ElinTogether.Common;
using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Net;
using HeathenEngineering.SteamworksIntegration;

namespace ElinTogether.Components;

internal class TabLobbyBrowser : TabEmpBase
{
    public override void OnLayout()
    {
        BuildNetButtons();
        BuildLobbyList();
    }

    private void BuildNetButtons()
    {
        var btnGroup = Horizontal();
        btnGroup.Layout.childForceExpandWidth = true;

        if (!EClass.core.IsGameStarted) {
            // the world kept in the depot: whoever comes first takes it and hosts it
            if (SaveDepot.Enabled) {
                btnGroup.Button(SaveDepot.HeldBy() is { } who ? "emp_ui_depot_held".Loc(who) : "emp_ui_depot_take".lang(), () => {
                    LayerElinTogether.Instance?.Close();
                    SaveDepot.Take();
                });
            }

            btnGroup.Header("emp_ui_unclaimed_zone");
            return;
        }

        if (NetSession.Instance.Transport == null) {
            btnGroup.Button("emp_ui_sv_start".lang(), StartServerFromPanel);
            if (SaveDepot.Enabled && Game.id != SaveDepot.WorldId) {
                btnGroup.Button("emp_ui_depot_put".lang(), SaveDepot.Put);
            }
        } else {
            btnGroup.Button("emp_ui_sv_invite".lang(), NetSession.Instance.Lobby.InviteSteamOverlay);
            btnGroup.Button("emp_ui_sv_dc".lang(), DisconnectFromPanel);
        }

#if DEBUG
        BuildBotButtons();
#endif
    }

#if DEBUG
    /// <summary>
    ///     A second game on this machine, which joins and plays by itself
    /// </summary>
    private void BuildBotButtons()
    {
        if (NetSession.Instance.Transport is ElinNetClient) {
            return;
        }

        var botGroup = Horizontal();
        botGroup.Layout.childForceExpandWidth = true;

        botGroup.Button("emp_ui_bot_add".lang(), () => {
            EmpBotLauncher.Launch();
            LayerElinTogether.Instance?.Reopen();
        });

        var running = EmpBotLauncher.Running;
        if (running > 0) {
            botGroup.Button("emp_ui_bot_stop".Loc(running), () => {
                EmpBotLauncher.StopAll();
                LayerElinTogether.Instance?.Reopen();
            });
        }

        Toggle("emp_ui_bot_all_actions", EmpConfig.Dev.BotAllActions.Value,
                value => EmpConfig.Dev.BotAllActions.Value = value)
            .SetTooltipLang(EmpConfig.Dev.BotAllActions.Description.Description);
    }
#endif

    private void BuildLobbyList()
    {
        Spacer(5);

        var totalPlayers = Header("");

        NetSession.Instance.Lobby.GetOnlineLobbies(SetupLobbyDisplay);

        return;

        void SetupLobbyDisplay(LobbyData[] lobbies)
        {
            if (this == null) {
                return;
            }

            var total = 0;
            foreach (var lobby in lobbies) {
                var count = lobby.MemberCount;
                total += count;

                HeaderCard("emp_ui_lobby_desc".Loc(lobby.Name, lobby.GameVersion, count, lobby[EmpLobbyData.CurrentZone]));
            }

            totalPlayers.text1.text = "emp_ui_lobby_tally".Loc(total);
        }
    }

    private void StartServerFromPanel()
    {
        NetSession.Instance.InitializeComponent<ElinNetHost>().StartServer();
        LayerElinTogether.Instance?.Reopen();
    }

    private void DisconnectFromPanel()
    {
        var isClient = NetSession.Instance.Transport is ElinNetClient;

        NetSession.Instance.ResetSession();
        LayerElinTogether.Instance?.Reopen();

        if (isClient) {
            EMono.scene.Init(Scene.Mode.Title);
        }
    }
}