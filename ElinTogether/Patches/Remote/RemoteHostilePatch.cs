using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Hitting someone is "a hostile action", and the game's reaction to it is the local player's alone: a friend
///     struck once only frowns, a resident may call for help, the allies of the player join in. On the host the
///     blows of another player went through as a resident's: the friend turned hostile at once and nobody was
///     called. The host plays the action with that player standing in for "the player"; its own game says the
///     lines <br />
///     The game's loop over "the player's party" would give an enemy to every member, the host and the other
///     players included: only the companions of the one who struck keep it. Blows at another player (or a
///     companion of its own) stay as they were
/// </summary>
[HarmonyPatch(typeof(Chara), nameof(Chara.DoHostileAction))]
internal static class RemoteHostilePatch
{
    [HarmonyPrefix]
    internal static void OnDoHostileAction(Chara __instance, Card _tg, out ScopeExit? __state)
    {
        __state = null;

        // a blow that misses is still a fight: whoever attacks a monster is engaged with it, see PlayerCombatTime
        PlayerCombatTime.Struck(_tg, __instance);

        if (NetSession.Instance.Connection is not ElinNetHost || __instance is not { IsPC: false, IsRemotePlayer: true } ||
            __instance.party is not { } party || _tg is not Chara { IsPlayer: false } target) {
            return;
        }

        var others = party.members
            .Where(member => member is not null && member != __instance && member != target &&
                             !member.IsCompanionOf(__instance))
            .Select(member => (member, member.enemy))
            .ToList();
        var quiet = MsgRelayContext.Suppress();
        var standIn = RemoteCraft.AsCrafter(__instance);
        __state = new() {
            OnExit = () => {
                standIn.Dispose();
                quiet.Dispose();
                foreach (var (member, enemy) in others) {
                    member.enemy = enemy;
                }
            },
        };
    }

    [HarmonyFinalizer]
    internal static void OnDoHostileActionEnd(ScopeExit? __state)
    {
        __state?.Dispose();
    }
}
