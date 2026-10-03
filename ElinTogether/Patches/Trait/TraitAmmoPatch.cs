using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Reloading from the bag fills "the player's" weapon, with whoever acted last as the one who reloads. For
///     another player the host filled its own weapon with that player's ammunition. The one who uses it reloads,
///     its own weapon, in every game
/// </summary>
[HarmonyPatch(typeof(TraitAmmo), nameof(TraitAmmo.OnUse))]
internal static class TraitAmmoPatch
{
    [HarmonyPrefix]
    internal static bool OnReload(TraitAmmo __instance, Chara c, ref bool __result, out Chara? __state)
    {
        __state = Act.CC;
        Act.CC = c;

        if (NetSession.Instance.Connection is not ElinNetHost || c is not { IsPC: false, IsRemotePlayer: true }) {
            return true;
        }

        __result = false;
        if (c.HasCondition<ConReload>()) {
            return false;
        }

        // its weapon in hand first, as the game takes the player's current tool
        var weapon = (c.NetProfile.RemoteMainHand.TryGetTarget(out var held) ? held.trait : null) as TraitToolRange ??
                     c.body.slots.Select(s => s.thing?.trait).OfType<TraitToolRange>().FirstOrDefault();
        if (weapon is null || __instance.owner is not Thing ammo || !weapon.IsAmmo(ammo)) {
            return false;
        }

        // inside the replay of that player's use: what moves must reach everyone, the lines that player
        using var simulate = ElinDelta.Simulate();
        using var told = MsgRelayContext.RedirectTo(c);
        __result = ActRanged.TryReload(weapon.owner.Thing, ammo);
        return false;
    }

    [HarmonyFinalizer]
    internal static void OnReloadEnd(Chara? __state)
    {
        Act.CC = __state;
    }
}
