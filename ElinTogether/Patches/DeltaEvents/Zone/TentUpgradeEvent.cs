using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     See <see cref="TentZoneDelta" />
/// </summary>
[HarmonyPatch(typeof(TraitWrench), nameof(TraitWrench.Upgrade))]
internal static class TentUpgradeEvent
{
    [HarmonyPostfix]
    internal static void OnUpgrade(Thing t, bool __result)
    {
        if (!__result || t?.trait is not TraitTent { zone: { } zone } || ElinDelta.IsRemoteStateLanding) {
            return;
        }

        var delta = TentZoneDelta.Of(zone);
        // alone on a map of its own: the host hears it, and tells the others
        QuestAwaySync.Send(delta);
        NetSession.Instance.Connection?.Delta.AddRemote(delta);
    }
}
