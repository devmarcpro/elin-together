using System.Linq;
using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The interaction menu on another player's character: the game offers to open its bag as it does for an
///     ally (and the host could then help itself). Between players it is a trade both agree to
/// </summary>
[HarmonyPatch(typeof(ActPlan), nameof(ActPlan._Update))]
internal static class PlayerTradePatch
{
    [HarmonyPostfix]
    internal static void OnUpdatePlan(ActPlan __instance)
    {
        if (!PlayerTrade.Enabled) {
            return;
        }

        foreach (var item in __instance.list.ToArray()) {
            if (item.act is not DynamicAct { id: "actTrade" } || item.tc is not Chara { IsRemotePlayer: true } other) {
                continue;
            }

            __instance.list.Remove(item);
            __instance.TrySetAct("emp_act_trade", () => {
                PlayerTrade.Invite(other.uid);
                return false;
            }, other, null, 2);
        }
    }
}
