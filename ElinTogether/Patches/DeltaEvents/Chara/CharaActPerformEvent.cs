using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal static class CharaActPerformEvent
{
    private static readonly HashSet<int> _alwaysSuccessfulActs = [
        // for some reason these return false
        ABILITY.ActRide,
        ABILITY.ActParasite,
    ];

    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return OverrideMethodComparer.FindAllOverrides(typeof(Act), nameof(Act.Perform))
            .Where(mi => mi.DeclaringType != typeof(DynamicAct) &&
                         mi.DeclaringType != typeof(DynamicAIAct) &&
                         mi.DeclaringType != typeof(ActQuickCraft));
    }

    [HarmonyPostfix]
    internal static void OnCharaActPerform(Act __instance, bool __result)
    {
        if (NetSession.Instance.Connection is not { } connection) {
            return;
        }

        // to save bandwidth, only propagate successful act perform events
        if (!__result && !_alwaysSuccessfulActs.Contains(__instance.id)) {
            return;
        }

        // perform throw via ActThrowEvent
        if (__instance is ActThrow and not ActRanged) {
            return;
        }

        // host propagates every act perform event
        // clients only propagate self
        if (connection.IsHost || Act.CC.IsPC) {
            var delta = CharaActPerformDelta.Create(__instance);

            // a blow struck inside another act (ActMeleeParry, ActMeleeCounter, each hit of a flurry) has no id to be
            // made again from: the replay of the act around it strikes its own, the damage comes as CardDamageHpDelta
            if (delta.ActId == 0 && delta.Tool is null) {
                return;
            }

            connection.Delta.AddRemote(delta);
            EmpLog.Debug("Act {ActId} by chara {OwnerUid} at {@Pos}, target {TargetUid}",
                delta.ActId, delta.Owner.Uid, delta.Pos, delta.TargetCard?.Uid);

            // a can is filled by setting its charges, which nothing else sends
            if (connection.IsHost && delta.Tool?.Find() is { isDestroyed: false } tool) {
                connection.Delta.AddRemote(new CardChargeDelta {
                    Card = tool,
                    Charges = tool.c_charges,
                });
            }
        }
    }
}