using System;
using ElinTogether.Elements;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Chara), nameof(Chara.Speed), MethodType.Getter)]
internal static class RemoteSharedSpeedPatch
{
    [HarmonyPrefix]
    internal static bool OnGetSpeed(Chara __instance, ref int __result)
    {
        if (!NetCompany.HasCompany) {
            return true;
        }

        // the host's copy of another player is no "player" for the game: its speed took the branches of a
        // monster (an overloaded copy lost all its speed where the player loses half, no penalty for stamina,
        // sleepiness or hunger), and the turn-based combat timed that player's turns by it (audit 2026-10-23).
        // It goes by what its own game says: the shared speed as the host's own player, else the speed it reports
        var remote = !__instance.IsPC && __instance.ai is GoalRemote && NetSession.Instance.Connection is ElinNetHost;
        if (!__instance.IsPC && !remote) {
            return true;
        }

        // use shared speed if server has a meaningful value
        var sharedSpeed = NetSession.Instance.SharedSpeed;
        if (sharedSpeed > 0) {
            __result = sharedSpeed;
            return false;
        }

        if (remote && __instance.RemoteState is { Speed: > 0 } reported) {
            __result = reported.Speed;
            return false;
        }

        return true;
    }

    extension(Chara chara)
    {
        [HarmonyReversePatch(HarmonyReversePatchType.Snapshot)]
        internal int Stub_get_Speed()
        {
            throw new NotImplementedException("Chara.get_Speed");
        }
    }
}