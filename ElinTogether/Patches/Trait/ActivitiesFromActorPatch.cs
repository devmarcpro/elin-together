using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     What happens on its own in the game that keeps the map, with nobody acting, asked "the player" for its skills:
///     always this game's own character, the host's (audit 2026-10-23). The player it is about stands in instead
/// </summary>
internal static class ActivitiesFromActor
{
    internal static bool Enabled => EmpConfig.Server.ActivitiesFromActor.Value;

    /// <summary>
    ///     The player standing nearest to a point of this map, null when it is this game's own (nothing to change)
    /// </summary>
    internal static Chara? NearestRemotePlayer(ElinNetHost host, Point pos)
    {
        Chara? best = EClass.pc is { isDead: false, IsAliveInCurrentZone: true } ? EClass.pc : null;
        var bestDist = best is null ? int.MaxValue : best.pos.Distance(pos);
        foreach (var chara in host.ActiveRemoteCharas.Values) {
            if (chara is not { isDead: false, IsAliveInCurrentZone: true }) {
                continue;
            }

            var dist = chara.pos.Distance(pos);
            if (dist < bestDist) {
                best = chara;
                bestDist = dist;
            }
        }

        return best is { IsPC: false } ? best : null;
    }
}

/// <summary>
///     A barrel turns what ripens in it into ale or wine with the skills and fame of "the player" (CraftUtil.
///     MixIngredients). Nothing says who filled it: the player nearest to the barrel when it is ready stands in
/// </summary>
[HarmonyPatch(typeof(TraitBrewery), nameof(TraitBrewery.OnChildDecay))]
internal static class TraitBreweryActorPatch
{
    [HarmonyPrefix]
    internal static void OnChildDecay(TraitBrewery __instance, out ScopeExit? __state)
    {
        __state = null;
        if (NetSession.Instance.Connection is not ElinNetHost host || !ActivitiesFromActor.Enabled ||
            __instance.owner.GetRootCard() is not { pos.IsValid: true } root) {
            return;
        }

        // (a barrel carried by a player is that player's)
        var actor = root is Chara { IsRemotePlayer: true } holder
            ? holder
            : ActivitiesFromActor.NearestRemotePlayer(host, root.pos);
        if (actor is not null) {
            __state = RemoteCraft.AsCrafter(actor);
        }
    }

    [HarmonyFinalizer]
    internal static void OnChildDecayEnd(ScopeExit? __state)
    {
        __state?.Dispose();
    }
}

/// <summary>
///     A baby pet drinking its mother's milk grows up to a level capped by the taming of its master, or of "the
///     player" when it has none, who also learns taming from it. A player's pet drinks in the game that keeps the
///     map: the host's taming capped it and the host learnt. Its owner stands in, and is told what it learnt
/// </summary>
[HarmonyPatch(typeof(TraitDrinkMilkMother), nameof(TraitDrinkMilkMother.OnDrink))]
internal static class TraitDrinkMilkMotherActorPatch
{
    private const int Taming = 237;

    [HarmonyPrefix]
    internal static void OnDrink(Chara c, out (ScopeExit StandIn, int PeerId)? __state)
    {
        __state = null;
        if (NetSession.Instance.Connection is not ElinNetHost host || !ActivitiesFromActor.Enabled ||
            c.Evalue(1232) <= 0 || (c.master ?? CompanionHelper.OwnerOf(c)) is not { IsRemotePlayer: true } owner) {
            return;
        }

        var peerId = host.ActiveRemoteCharas.First(kv => kv.Value == owner).Key;
        __state = (RemoteCraft.AsCrafter(owner), peerId);
    }

    [HarmonyFinalizer]
    internal static void OnDrinkEnd((ScopeExit StandIn, int PeerId)? __state)
    {
        if (__state is not { } state) {
            return;
        }

        state.StandIn.Dispose();
        // the host's copy of a player is not that player: its own game gives it the taming it learnt
        if (NetSession.Instance.Connection is ElinNetHost host) {
            host.SendDeltaTo(state.PeerId, new PartyExpDelta {
                Element = Taming,
                Amount = 100,
            });
        }
    }
}
