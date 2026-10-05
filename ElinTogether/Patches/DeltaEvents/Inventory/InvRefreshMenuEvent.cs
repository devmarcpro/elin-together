using System;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(UIInventory), nameof(UIInventory.RefreshMenu))]
internal class InvRefreshMenuEvent
{
    // the last menu's "send if the rules changed", for the filter dialog that its button opens after the menu is gone
    internal static Action? Resend;

    [HarmonyPostfix]
    internal static void OnRefreshMenu(UIInventory __instance)
    {
        // sort and layout of a window are the screen of this player; what the sort button's menu changes of the rules is
        // sent when it closes (after the game's own listener, which builds the menu)
        __instance.window.buttonShared.onClick.AddListener(PropagateSharedType);
        if (__instance.window.buttonSort != null) {
            __instance.window.buttonSort.onClick.AddListener(WatchMenu);
        }

        return;

        void WatchMenu()
        {
            Resend = null;
            // a bag, an ally, a shop and what a character carries belong to that player, not to the map
            if (__instance.owner.Container is not { } container || container.GetRootCard() is Chara ||
                __instance.window.saveData is not { } data || !EClass.ui.contextMenu.isActive) {
                return;
            }

            var before = InvSaveDataDelta.Rules(data);
            EClass.ui.contextMenu.currentMenu.onDestroy += () => {
                // the menu's buttons close it before they act (autodump, paste): look again next frame
                Resend = Send;
                EClass.core.actionsNextFrame.Add(Send);
            };
            return;

            void Send()
            {
                var now = InvSaveDataDelta.Rules(data);
                if (NetSession.Instance.Connection is not { } connection || now == before) {
                    return;
                }

                before = now;
                connection.Delta.AddRemote(new InvSaveDataDelta {
                    WindowId = __instance.window.idWindow,
                    Data = LZ4Bytes.Create(data),
                    IsShop = false,
                    Container = container,
                });
            }
        }

        void PropagateSharedType()
        {
            if (NetSession.Instance.Connection is not { } connection) {
                return;
            }

            // a bag, an ally, a shop and what a character carries belong to that player, not to the map
            var container = __instance.owner.Container;
            if (container.GetRootCard() is Chara) {
                return;
            }

            connection.Delta.AddRemote(new InvSaveDataDelta {
                WindowId = __instance.window.idWindow,
                Data = LZ4Bytes.Create(__instance.window.saveData),
                IsShop = false,
                Container = container,
            });
        }
    }
}

/// <summary>
///     The "filter" button of the menu closes it, then asks the text in a dialog: the change comes after the menu is gone
/// </summary>
[HarmonyPatch(typeof(Dialog), nameof(Dialog.InputName))]
internal class InvFilterDialogEvent
{
    [HarmonyPrefix]
    internal static void OnInputName(Dialog.InputType inputType, ref Action<bool, string> onClose)
    {
        if (inputType != Dialog.InputType.DistributionFilter || InvRefreshMenuEvent.Resend is not { } resend) {
            return;
        }

        var close = onClose;
        onClose = (cancel, text) => {
            close(cancel, text);
            resend();
        };
    }
}
