using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Player.Flags), nameof(Player.Flags.OnLeaveZone))]
internal static class ClientMainStoryPatch
{
    /// <summary>
    ///     The main quest belongs to the host. Its early story plays on every zone exit while the quest
    ///     waits at phase 700, a client travelling alone would get it each time from its copy of the host world
    /// </summary>
    [HarmonyPrefix]
    internal static bool OnLeaveZone()
    {
        return NetSession.Instance.Transport is not ElinNetClient;
    }
}
