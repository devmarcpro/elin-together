using System.Linq;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The policy window redraws its icons when it opens and after each switch: what is on then is compared with
///     what was on before, and told to the others when the player changed it, see <see cref="PolicyStateDelta" />
/// </summary>
[HarmonyPatch(typeof(LayerPolicy), nameof(LayerPolicy.RefreshPolicyIcons))]
internal static class PolicyStateEvent
{
    private static LayerPolicy? _window;
    private static int[] _shown = [];

    [HarmonyPostfix]
    internal static void OnRefreshIcons(LayerPolicy __instance)
    {
        if (NetSession.Instance.Connection is not { } connection || EClass._zone?.branch is not { } branch) {
            return;
        }

        var active = PolicyStateDelta.Read(branch);
        var changed = _window == __instance && !active.SequenceEqual(_shown);
        _window = __instance;
        _shown = active;

        // opening the window, or a set that came from someone else
        if (!changed || ElinDelta.IsApplying) {
            return;
        }

        RemoteBasePaidPatch.WarnHostOnly();
        connection.Delta.AddRemote(new PolicyStateDelta {
            Active = active,
        });
    }
}
