using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     One affinity per resident for the whole group. The game of the player who acts (a gift, a chat) rolls the
///     dice; the host adds the result to its value and tells everyone. A game that only replays someone else's
///     action does not roll its own
/// </summary>
[HarmonyPatch(typeof(Chara), nameof(Chara.ModAffinity))]
internal static class CharaAffinityPatch
{
    [HarmonyPrefix]
    internal static void OnModAffinity(Chara __instance, out int __state)
    {
        __state = __instance._affinity;
    }

    [HarmonyPostfix]
    internal static void OnModAffinityEnd(Chara __instance, int __state)
    {
        var change = __instance._affinity - __state;
        if (change == 0 || __instance.IsPC) {
            return;
        }

        switch (NetSession.Instance.Connection) {
            case ElinNetClient client when !ElinDelta.IsApplying:
                client.Delta.AddRemote(new CharaAffinityDelta {
                    Owner = __instance,
                    Value = change,
                    Relative = true,
                });
                break;
            case ElinNetHost host when !ElinDelta.IsApplying:
                host.Delta.AddRemote(new CharaAffinityDelta {
                    Owner = __instance,
                    Value = __instance._affinity,
                });
                break;
            case not null:
                // replaying what another player did: that player's game rolled, the host will say the result
                __instance._affinity = __state;
                break;
        }
    }
}
