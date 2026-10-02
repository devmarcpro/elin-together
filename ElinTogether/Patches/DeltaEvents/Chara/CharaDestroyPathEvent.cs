using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Chara), nameof(Chara.DestroyPath))]
internal static class CharaDestroyPathEvent
{
    [HarmonyPrefix]
    internal static void OnDestroyPath(Chara __instance, Point pos)
    {
        if (NetSession.Instance.Connection is not ElinNetHost host || ElinDelta.IsApplying) {
            return;
        }

        // big creatures call this at every step: only when terrain is about to go
        var breaks = false;
        pos.ForeachMultiSize(__instance.W, __instance.H, (p, _) => {
            breaks |= p.IsValid && (p.HasBlock || (p.HasObj && p.IsBlocked));
        });

        if (!breaks) {
            return;
        }

        host.Delta.AddRemote(new CharaDestroyPathDelta {
            Owner = __instance,
            Pos = pos,
        });
    }
}
