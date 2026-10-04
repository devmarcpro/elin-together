using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal static class CharaFaithEvent
{
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Religion), nameof(Religion.JoinFaith))]
    internal static void OnJoinFaith(Religion __instance, Chara c, Religion.ConvertType type)
    {
        if (NetSession.Instance.Connection is not { } connection) {
            return;
        }

        // only report self
        if (!c.IsPC) {
            return;
        }

        if (ElinDelta.IsRemoteStateLanding) {
            return;
        }

        connection.Delta.AddRemote(new CharaFaithDelta {
            Owner = c,
            FaithId = __instance.id,
            Campaign = type == Religion.ConvertType.Campaign,
        });
    }
}