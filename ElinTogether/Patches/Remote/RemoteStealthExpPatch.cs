using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Stealth is trained when a monster fails to notice a sneaking player (Chara.FindNewEnemy), code that only the
///     host runs: on a guest's character it landed on a copy whose element changes are ignored, so the skill never
///     rose. The host tells the guest's game, which gives it as its own gain (see <see cref="PartyExpDelta" />)
/// </summary>
[HarmonyPatch(typeof(Card), nameof(Card.ModExp), typeof(int), typeof(int))]
internal static class RemoteStealthExpPatch
{
    [HarmonyPrefix]
    internal static void OnModExp(Card __instance, int ele, int a)
    {
        // only a game decision made here: what a guest's act replays on the host is gained in the guest's own game
        if (ele != 152 || a <= 0 || ElinDelta.IsApplying || NetSession.Instance.Connection is not ElinNetHost host ||
            __instance is not Chara chara) {
            return;
        }

        foreach (var (peerId, remote) in host.ActiveRemoteCharas) {
            if (remote == chara) {
                host.SendDeltaTo(peerId, new PartyExpDelta { Element = ele, Amount = a });
                return;
            }
        }
    }
}
