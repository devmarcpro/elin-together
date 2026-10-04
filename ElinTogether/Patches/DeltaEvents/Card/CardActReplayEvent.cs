using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The actions of these items and furniture are lambdas that only ran in the client's game, where it cannot give
///     itself a condition, change a stack or a charge, or keep what it creates: injecting did nothing and kept the
///     syringe, a furniture ticket gave the furniture for free, a well never ran dry <br />
///     The entry the client picks is a request, the host runs it for the client's character <br />
///     Closed list: another trait goes through here only after its window and its "player" are looked at, as for
///     <c>CardOnUseDelta</c>
/// </summary>
[HarmonyPatch]
internal static class CardActReplayEvent
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        foreach (var type in new[] {
                     typeof(TraitTicketFurniture), typeof(TraitSyringeBlood), typeof(TraitSyringeGene),
                     typeof(TraitSyringeHeaven), typeof(TraitSyringeUnicorn), typeof(TraitStethoscope), typeof(TraitLeash),
                 }) {
            yield return AccessTools.DeclaredMethod(type, nameof(Trait.TrySetHeldAct));
        }

        yield return AccessTools.DeclaredMethod(typeof(TraitWell), nameof(Trait.TrySetAct));
    }

    [HarmonyPrefix]
    internal static void Before(ActPlan p, out ActPlan.Item[] __state)
    {
        __state = p.list.ToArray();
    }

    [HarmonyPostfix]
    internal static void After(Trait __instance, ActPlan p, ActPlan.Item[] __state)
    {
        if (NetSession.Instance.Connection is not ElinNetClient client || ElinDelta.IsApplying) {
            return;
        }

        // the entries this trait just added, in the order the host will build them
        var index = 0;
        foreach (var item in p.list.Where(i => !__state.Contains(i)).ToArray()) {
            if (item.act is DynamicAct act) {
                var (rank, own) = (index, act.onPerform);
                act.onPerform = () => Request(client, __instance, item, act, rank, own);
            }

            index++;
        }
    }

    private static bool Request(ElinNetClient client, Trait trait, ActPlan.Item item, DynamicAct act, int index,
        Func<bool>? own)
    {
        var card = trait.owner;
        if (!CardCache.Contains(card)) {
            return false;
        }

        client.Delta.AddRemote(new CardActReplayDelta {
            Card = card,
            RootCard = card.GetRootCard(),
            User = EClass.pc,
            Held = trait is not TraitWell,
            Pos = item.pos,
            Target = item.tc,
            Index = index,
            Id = act.id,
            Leashed = (trait is TraitLeash && item.tc is Chara companion) ? !companion.isLeashed : null,
        });

        // the scope opens its window and the leash flips its bit here, where the player is: the request only keeps the
        // host's part in step. For the others the host does it all, and ends the turn as the lambda did
        if (trait is TraitLeash or TraitStethoscope) {
            return own?.Invoke() ?? false;
        }

        return trait is not TraitTicketFurniture;
    }
}

/// <summary>
///     A leash tugs the companion toward the player who walks, as the game does for "the player" <br />
///     A guest's companion keeps its leash in a key of its own: the game's bit would make the host's own steps tug it
///     toward the host
/// </summary>
internal static class GuestLeash
{
    internal const string Key = "emp_leash";

    /// <summary>
    ///     After a guest's step on the host: its leashed companions that are left behind follow (Chara.cs, the move of
    ///     the player)
    /// </summary>
    internal static void Follow(Chara player)
    {
        if (!player.IsRemotePlayer || !EClass._zone.PetFollow || EClass._zone.IsRegion ||
            (EClass._zone.KeepAllyDistance && EClass.game.config.tactics.allyKeepDistance)) {
            return;
        }

        foreach (var member in CompanionHelper.CompanionsOf(player)) {
            if (member.GetInt(Key) != 0 && member.host == null && !member.IsDisabled &&
                !member.HasCondition<ConEntangle>() && !member.IsInCombat && member.Dist(player) > 1) {
                member.TryMoveTowards(player.pos);
            }
        }
    }
}
