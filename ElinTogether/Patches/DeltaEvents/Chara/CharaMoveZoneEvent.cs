using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Chara), nameof(Chara.MoveZone), typeof(Zone), typeof(ZoneTransition))]
internal class CharaMoveZoneEvent
{
    [HarmonyPrefix]
    internal static bool OnClientMoveZone(Chara __instance, Zone z, ZoneTransition transition)
    {
        // host may have to recall the zone from a client simulating it
        if (NetSession.Instance.Transport is ElinNetHost host) {
            return !__instance.IsPC || host.TryEnterZone(z, transition);
        }

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

    /// <summary>
    ///     Elin drags the party along for its leader only (the host): a player travelling alone takes its companions
    /// </summary>
    [HarmonyPostfix]
    internal static void OnTravelWithCompanions(Chara __instance, Zone z, bool __runOriginal)
    {
        if (!__runOriginal || !__instance.IsPC || __instance.party is not { } party || party.leader == __instance ||
            NetSession.Instance is not { IsAway: true, Connection: null }) {
            return;
        }

        foreach (var companion in CompanionHelper.CompanionsOf(__instance)) {
            if (!companion.isDead && companion.parent is Zone && companion.currentZone != z) {
                companion.MoveZone(z);
            }
        }
    }
}
