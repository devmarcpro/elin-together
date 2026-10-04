using System;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Chara), nameof(Chara.AddCondition), typeof(Condition), typeof(bool))]
internal static class CharaAddConditionEvent
{
    [HarmonyPostfix]
    internal static void OnCharaAddCondition(Chara __instance, Condition? __result, Condition c, bool force)
    {
        // only propagate successful add condition events
        if (__result is null) {
            return;
        }

        if (NetSession.Instance.Connection is not ElinNetHost host) {
            return;
        }

        host.Delta.AddRemote(new CharaAddConditionDelta {
            Owner = __instance,
            ConditionId = __result.id,
            Power = __result.power,
            Force = force,
        });
    }

    [HarmonyPrefix]
    internal static bool OnClientAddCondition(Chara __instance, Condition c, bool force)
    {
        // clients cannot add conditions normally
        if (NetSession.Instance.IsHost) {
            return true;
        }

        // the trap this game's player walked on is rolled here only (RemoteTrapPatch): what it does to it is
        // asked of the game that simulates the map
        if (RemoteTrapPatch.IsOwnStep && __instance.IsPC && CharaAddConditionDelta.IsTrapCondition(c.source.alias) &&
            NetSession.Instance.Connection is ElinNetClient client) {
            client.Delta.AddRemote(new CharaAddConditionDelta {
                Owner = __instance,
                ConditionId = c.id,
                Power = c.power,
                Force = force,
            });
        }

        return false;
    }

    extension(Chara chara)
    {
        [HarmonyReversePatch(HarmonyReversePatchType.Snapshot)]
        internal Condition Stub_AddCondition(Condition condition, bool force)
        {
            throw new NotImplementedException("Chara.AddCondition");
        }
    }
}