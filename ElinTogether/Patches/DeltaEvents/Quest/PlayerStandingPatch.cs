using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Fame and karma earned in a quest step the host runs for another player are that player's, and so is
///     what a deed costs (see <see cref="PlayerKarma" />)
/// </summary>
[HarmonyPatch(typeof(Player))]
internal static class PlayerStandingPatch
{
    [HarmonyPrefix]
    [HarmonyPatch(nameof(Player.ModFame))]
    internal static bool OnModFame(int a)
    {
        return !PlayerStandIn.Redirect(a, 0);
    }

    [HarmonyPrefix]
    [HarmonyPatch(nameof(Player.ModKarma))]
    internal static bool OnModKarma(int a)
    {
        return !PlayerStandIn.Redirect(0, a) && !PlayerKarma.Reroute(a);
    }
}
