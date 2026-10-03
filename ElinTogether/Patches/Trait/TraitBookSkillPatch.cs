using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A plan teaches the base, an ability book its reader, only when "the player" reads them. The end of another
///     player's reading is played by the host for a resident: the base learnt nothing, and neither book was used
///     up. That player stands in for the end of the reading; its own game says the lines
/// </summary>
[HarmonyPatch(typeof(TraitBookSkill), nameof(TraitBookSkill.OnRead))]
internal static class TraitBookSkillPatch
{
    [HarmonyPrefix]
    internal static void OnRead(TraitBookSkill __instance, Chara c, out ScopeExit? __state)
    {
        __state = null;
        if (NetSession.Instance.Connection is not ElinNetHost || c is not { IsPC: false, IsRemotePlayer: true } ||
            !(__instance.IsPlan || __instance.IsOnlyUsableByPc)) {
            return;
        }

        var quiet = MsgRelayContext.Suppress();
        var standIn = RemoteCraft.AsCrafter(c);
        __state = new() {
            OnExit = () => {
                standIn.Dispose();
                quiet.Dispose();
            },
        };
    }

    [HarmonyFinalizer]
    internal static void OnReadEnd(ScopeExit? __state)
    {
        __state?.Dispose();
    }
}
