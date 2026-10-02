using System.Collections.Generic;
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
[HarmonyPatch]
internal static class AIOpenGambleChestPatch
{
    /// <summary>
    ///     Steps the host keeps a finished opening alive for, see <see cref="UntilThePlayerIsDone" />
    /// </summary>
    private const int LingerSteps = 8;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(AI_OpenGambleChest), nameof(AI_OpenGambleChest.Run), MethodType.Enumerator)]
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
    [HarmonyPatch(typeof(AI_OpenGambleChest), nameof(AI_OpenGambleChest.Run), MethodType.Enumerator)]
    internal static void OnOpenTurnEnd((ElinDelta.PatchScope scope, ScopeExit? msg, bool muted) __state)
    {
        __state.scope.Exit();
        __state.msg?.Dispose();

        if (__state.muted) {
            Msg.ignoreAll = false;
        }
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(AI_OpenGambleChest), nameof(AI_OpenGambleChest.Run))]
    internal static void OnOpen(AI_OpenGambleChest __instance, ref IEnumerable<AIAct.Status> __result)
    {
        if (NetSession.Instance.Connection is ElinNetHost && __instance.owner is { } owner && owner.IsRemotePlayer) {
            __result = UntilThePlayerIsDone(__instance, __result);
        }
    }

    /// <summary>
    ///     A client's time comes from the host, and the host stops the world once nobody is busy. The host uses
    ///     up the last chest a step before the player's own game sees it gone: with the host idle, the world
    ///     stopped there and the player stayed busy opening nothing, with no way to cancel <br />
    ///     The host's side stays busy until the player reports it is done, or a few steps at most
    /// </summary>
    private static IEnumerable<AIAct.Status> UntilThePlayerIsDone(AI_OpenGambleChest act, IEnumerable<AIAct.Status> opening)
    {
        foreach (var status in opening) {
            yield return status;
        }

        for (var i = 0; i < LingerSteps && act.owner is not null; i++) {
            yield return act.KeepRunning();
        }
    }
}
