using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal static class AIPassTimePatch
{
    /// <summary>
    ///     True while the local player's rest runs its turn, see SleepSynchronizationContext.AllowPartySleep
    /// </summary>
    internal static bool IsResting { get; private set; }

    /// <summary>
    ///     Resting gives hit points back, and those are the host's to give: a client's rest was not sent at all,
    ///     it healed in its own game only and the host's value came back a moment later <br />
    ///     The game's own loop is the local player's, it heals "the player's group" with "the player's" skill.
    ///     Whoever simulates the map runs the rest of another player with that player's skill; everywhere else
    ///     someone else's rest only passes turns
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(AI_PassTime), nameof(AI_PassTime.Run))]
    internal static bool OnRest(AI_PassTime __instance, ref IEnumerable<AIAct.Status> __result)
    {
        if (NetSession.Instance.Connection is not { } connection ||
            __instance.owner is not { IsPC: false } owner || !owner.IsRemotePlayer) {
            return true;
        }

        __result = Run(__instance, connection.IsHost);
        return false;
    }

    private static IEnumerable<AIAct.Status> Run(AI_PassTime act, bool heals)
    {
        for (var i = 0; i < act.turns; i++) {
            if (act.owner is not { isDead: false } owner) {
                yield break;
            }

            if (heals) {
                Heal(owner);

                if (i == 50 && owner.pos.IsHotSpring && (!owner.IsPCC || owner.pccData.state == PCCState.Undie)) {
                    // the game gives it to the whole group of "the player": here the player and its companions
                    var power = EClass._zone.elements.Has(3701) ? 150 : 100;
                    foreach (var member in CompanionHelper.CompanionsOf(owner).Prepend(owner)) {
                        member.AddCondition<ConHotspring>(power)?.SetPerfume();
                    }
                }
            }

            yield return act.KeepRunning();
        }
    }

    /// <summary>
    ///     As the game does for the local player: the one resting, and twice as much for the rest of its group <br />
    ///     Mana is each player's own, its game gives it back
    /// </summary>
    private static void Heal(Chara owner)
    {
        var amount = 1 + owner.Evalue(ABILITY.AI_Meditate) / 5;
        IEnumerable<Chara> group = owner.party?.members is { } members ? [..members] : [owner];

        foreach (var member in group) {
            if (member.isDead || member.conditions.Any(condition => condition.PreventRegen)) {
                continue;
            }

            var share = amount * (member == owner ? 1 : 2);
            if (EClass.rnd(3) == 0) {
                member.HealHP(share);
            }

            if (!member.IsPlayer) {
                member.mana.Mod(share);
            }
        }
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(AI_PassTime), nameof(AI_PassTime.Run), MethodType.Enumerator)]
    internal static void OnRestTurn()
    {
        IsResting = true;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(AI_PassTime), nameof(AI_PassTime.Run), MethodType.Enumerator)]
    internal static void OnRestTurnEnd()
    {
        IsResting = false;
    }
}
