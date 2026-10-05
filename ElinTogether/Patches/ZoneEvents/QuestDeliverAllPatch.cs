using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The "deliver all" button of the chest of a harvest. The game's own only looks for the quest in the local
///     quest log and destroys the crops there: with two players in the zone, the one without the quest in its log
///     (who came along) delivers nothing, and a client destroys crops on its screen only. <br />
///     Here each crop goes the way a crop dropped on the chest goes: replayed in every game (see
///     InvOwnerOnProcessEvent), counted by the one that has the quest
/// </summary>
[HarmonyPatch(typeof(LayerDragGrid), nameof(LayerDragGrid.SetInv))]
internal static class QuestDeliverAllPatch
{
    [HarmonyPostfix]
    internal static void OnSetInv(LayerDragGrid __instance)
    {
        // nothing of this outside of a session
        if (NetSession.Instance.Connection is not { } connection) {
            return;
        }

        if (__instance.owner is not InvOwnerDeliver { mode: InvOwnerDeliver.Mode.Crop } deliver) {
            return;
        }

        // the game's own button is right where the quest is in this game's log and this game runs the zone
        if (connection.IsHost && EClass.game.quests.Get<QuestHarvest>() is not null) {
            return;
        }

        __instance.buttonDeliver.SetOnClick(() => {
            var crops = EClass.pc.things.List(t => deliver.ShouldShowGuide(t));
            foreach (var crop in crops) {
                // one the host does not know yet: counted here and kept there, it could be delivered again
                if (connection.IsClient && (PendingUid.IsPending(crop.uid) || !CardCache.Contains(crop))) {
                    continue;
                }

                InvOwnerOnProcessEvent.OnProcess(deliver, crop);
                deliver._OnProcess(crop);
            }

            if (crops.Count > 0) {
                SE.Pick();
            } else {
                SE.BeepSmall();
            }

            __instance.Close();
        });
    }
}
