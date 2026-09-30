using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Chara), nameof(Chara.MoveZone), typeof(Zone), typeof(ZoneTransition))]
internal class CharaMoveZoneEvent
{
    [HarmonyPrefix]
    internal static bool OnClientMoveZone(Chara __instance, Zone z, ZoneTransition transition)
    {
        // checked first: an away client reads as host, see NetSession.Connection
        if (NetSession.Instance.Transport is not ElinNetClient client) {
            return true;
        }

        if (!__instance.IsPC) {
            return true;
        }

        if (NetSession.Instance.IsAway) {
            return client.TryTravel(z, transition);
        }

        // remote has been updated, okay to proceed
        if (z == NetSession.Instance.CurrentZone) {
            return true;
        }

        // remote characters do not trigger scene change
        // clients do not post move zone delta, they lease the zone to travel alone
        return client.TryTravel(z, transition);
    }
}
