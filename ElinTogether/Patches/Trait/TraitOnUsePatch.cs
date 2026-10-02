using System.Collections.Generic;
using System.Reflection;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal class TraitOnUsePatch
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return [
            AccessTools.Method(typeof(TraitRecycle), nameof(TraitRecycle.OnUse), [typeof(Chara)]),
            // sets the local player to open the chests, whoever asked: the one who asked does it, from its own game
            AccessTools.Method(typeof(TraitGambleChest), nameof(TraitGambleChest.OnUse), [typeof(Chara)]),
        ];
    }

    [HarmonyPrefix]
    internal static bool OnRemotePlayerUse(Chara c)
    {
        return !NetSession.Instance.HasActiveConnection || c is not { IsPC: false, IsRemotePlayer: true };
    }
}