using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Gamble chests are opened one by one on both sides: whoever simulates the map rolls what is won and uses
///     the chests up, the player's own game gives the lockpicking experience and takes the stamina <br />
///     The money is the host's to give, so are the lines that tell of it
/// </summary>
[HarmonyPatch(typeof(AI_OpenGambleChest), nameof(AI_OpenGambleChest.Run), MethodType.Enumerator)]
internal static class AIOpenGambleChestPatch
{
    [HarmonyPrefix]
    internal static void OnOpenTurn(object __instance, out (ElinDelta.PatchScope scope, ScopeExit? msg, bool muted) __state)
    {
        __state = default;

        if (NetSession.Instance.Connection is not { } connection ||
            Traverse.Create(__instance).Field("<>4__this").GetValue() is not AI_OpenGambleChest { owner: { } owner }) {
            return;
        }

        if (connection.IsHost) {
            if (owner.IsRemotePlayer) {
                // what it wins goes into its bag from here, and it reads the outcome
                __state = (ElinDelta.PatchScope.Simulate(), MsgRelayContext.RedirectTo(owner), false);
            }

            return;
        }

        // this game's own roll decides nothing
        __state = (default, null, !Msg.ignoreAll);
        Msg.ignoreAll = true;
    }

    [HarmonyFinalizer]
    internal static void OnOpenTurnEnd((ElinDelta.PatchScope scope, ScopeExit? msg, bool muted) __state)
    {
        __state.scope.Exit();
        __state.msg?.Dispose();

        if (__state.muted) {
            Msg.ignoreAll = false;
        }
    }
}
