using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(UIInventory), nameof(UIInventory.RefreshMenu))]
internal class InvRefreshMenuEvent
{
    [HarmonyPostfix]
    internal static void OnRefreshMenu(UIInventory __instance)
    {
        // the sort button is not here: sort and layout of a window are the screen of this player
        __instance.window.buttonShared.onClick.AddListener(PropagateSharedType);

        return;

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
