using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     On the host, the game's laws only know the local player. With karma per player (see
///     <see cref="PlayerKarma" />) they are told who did the deed, and whose karma the guards look at
/// </summary>
[HarmonyPatch]
internal static class PlayerKarmaPatch
{
    private static Chara? _combatSubject;
    private static (Chara? Dead, Card? Killer) _lastKill;

    private static ElinNetHost? Host =>
        PersonalQuests.Enabled && NetSession.Instance.Connection is ElinNetHost { ActiveRemoteCharas.Count: > 0 } host
            ? host
            : null;

    [HarmonyPrefix]
    [HarmonyPriority(Priority.First)]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Die))]
    internal static void OnDie(Chara __instance, Card? origin, out Card? __state)
    {
        __state = PlayerKarma.Killer;
        PlayerKarma.Killer = origin;
        _lastKill = (__instance, origin);
    }

    // the fighters' guild pays "the player" for a kill, right after the death is settled: on the host that was
    // always the host. The bounty goes to the player behind the one who killed (itself, or the owner of the
    // companion), told and paid from here, once. Council decision of 2026-10-04, see MODLOG
    [HarmonyPostfix]
    [HarmonyPatch(typeof(GuildFighter), nameof(GuildFighter.HasBounty))]
    internal static void OnHasBounty(Chara c, ref bool __result)
    {
        if (!__result || !c.isDead || _lastKill.Dead != c) {
            return;
        }

        switch (NetSession.Instance.Connection) {
            // a kill settled elsewhere, played again here: paid from there
            case ElinNetClient when ElinDelta.IsApplying:
                __result = false;
                break;
            case ElinNetHost when PlayerKarma.PlayerBehind(_lastKill.Killer) is { IsRemotePlayer: true } player:
                var gold = EClass.rndHalf(200 + EClass.curve(c.LV, 20, 15) * 20);
                using (MsgRelayContext.RedirectTo(player)) {
                    Msg.Say("bounty", c, gold.ToString());
                }

                using (ElinDelta.Simulate()) {
                    player.ModCurrency(gold);
                }

                __result = false;
                break;
        }
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Die))]
    internal static void OnDieEnd(Card? __state)
    {
        PlayerKarma.Killer = __state;
    }

    // a guard looks at someone: whether "the player" is a criminal is asked about that one
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.IsHostile), typeof(Chara))]
    internal static void OnIsHostile(Chara __instance, Chara c)
    {
        PlayerKarma.Subject = __instance.trait is TraitGuard ? c : null;
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.IsHostile), typeof(Chara))]
    internal static void OnIsHostileEnd()
    {
        PlayerKarma.Subject = null;
    }

    // a guard fighting someone of the party keeps at it while "the player" is a criminal
    [HarmonyPrefix]
    [HarmonyPatch(typeof(AIAct), nameof(AIAct.Tick))]
    internal static void OnCombatTick(AIAct __instance)
    {
        if (__instance is GoalCombat { owner.trait: TraitGuard } combat) {
            _combatSubject = combat.owner.enemy;
        }
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(AIAct), nameof(AIAct.Tick))]
    internal static void OnCombatTickEnd(AIAct __instance)
    {
        if (__instance is GoalCombat) {
            _combatSubject = null;
        }
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Zone), nameof(Zone.RefreshCriminal))]
    internal static void OnRefreshCriminal()
    {
        PlayerKarma.AnyPlayer = true;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Zone), nameof(Zone.RefreshCriminal))]
    internal static void OnRefreshCriminalEnd()
    {
        PlayerKarma.AnyPlayer = false;
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Player), nameof(Player.IsCriminal), MethodType.Getter)]
    internal static void OnIsCriminal(ref bool __result)
    {
        if (Host is not { } host) {
            return;
        }

        if (PlayerKarma.AnyPlayer) {
            __result = __result || host.HasCriminalHere();
            return;
        }

        if (PlayerKarma.PlayerBehind(PlayerKarma.Subject ?? _combatSubject) is { IsRemotePlayer: true } player) {
            __result = host.IsCriminal(player);
        }
    }

    // digging up the street, picking a lock: a crime for any player, as for the local one
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Zone), nameof(Zone.IsCrime))]
    internal static void OnIsCrime(Zone __instance, Chara c, Act act, ref bool __result)
    {
        if (__result || Host is null || c is null || !c.IsRemotePlayer) {
            return;
        }

        __result = act.IsHostileAct && __instance.HasLaw && !__instance.IsPCFaction;
    }

    // taking what belongs to a resident: its game takes the karma, the witnesses are here
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.HoldCard))]
    internal static void OnHoldCard(Chara __instance, Card t)
    {
        if (Host is null || t is not { isNPCProperty: true, isDestroyed: false } || __instance.held == t || !__instance.IsRemotePlayer) {
            return;
        }

        t.isNPCProperty = false;
        if (!t.GetBool(128)) {
            __instance.pos.TryWitnessCrime(__instance);
        }
    }
}
