using System.Collections.Generic;
using System.Reflection;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A use is run by the host, then by every client. These ones act on "the player" of whatever game runs
///     them, whoever asked: a window on the host's screen for a guest's bank, the host asked whether it wants to
///     hang itself with the guest's rope, the host sent away by the guest's waystone <br />
///     They only run in the game of the player who asked
/// </summary>
[HarmonyPatch]
internal class TraitOnUsePatch
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return [
            AccessTools.Method(typeof(TraitRecycle), nameof(TraitRecycle.OnUse), [typeof(Chara)]),
            // sets the local player to open the chests, whoever asked: the one who asked does it, from its own game
            AccessTools.Method(typeof(TraitGambleChest), nameof(TraitGambleChest.OnUse), [typeof(Chara)]),
            // windows
            AccessTools.Method(typeof(TraitBank), nameof(TraitBank.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitTaxChest), nameof(TraitTaxChest.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitPolicyBoard), nameof(TraitPolicyBoard.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitBJTable), nameof(TraitBJTable.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitSlotMachine), nameof(TraitSlotMachine.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitRadio), nameof(TraitRadio.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitJukeBox), nameof(TraitJukeBox.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitEditPlaylist), nameof(TraitEditPlaylist.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitBookResident), nameof(TraitBookResident.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitBookRoster), nameof(TraitBookRoster.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitDetector), nameof(TraitDetector.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitGeneratorWheel), nameof(TraitGeneratorWheel.OnUse), [typeof(Chara)]),
            // runes and plugs (TraitRune, TraitModRanged inherit it): the pick goes back by InvOwnerOnProcessDelta
            AccessTools.Method(typeof(TraitMod), nameof(TraitMod.OnUse), [typeof(Chara)]),
            // the action mode of the local player
            AccessTools.Method(typeof(TraitPainter), nameof(TraitPainter.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitViewMap), nameof(TraitViewMap.OnUse), [typeof(Chara)]),
            // a crafting tool used from the bag
            AccessTools.Method(typeof(TraitCrafter), nameof(TraitCrafter.OnUse), [typeof(Chara)]),
            // the local player, hanged or sent away
            AccessTools.Method(typeof(TraitRope), nameof(TraitRope.OnUse), [typeof(Chara)]),
            AccessTools.Method(typeof(TraitWaystone), nameof(TraitWaystone.OnUse), [typeof(Chara)]),
        ];
    }

    [HarmonyPrefix]
    internal static bool OnRemotePlayerUse(Trait __instance, Chara c)
    {
        if (!NetSession.Instance.HasActiveConnection || c is not { IsPC: false, IsRemotePlayer: true }) {
            return true;
        }

        // a client cannot use an item up: the stone of the one who leaves is used up here
        if (__instance is TraitWaystone && NetSession.Instance.Connection is ElinNetHost) {
            using var _ = ElinDelta.Simulate();
            __instance.owner.ModNum(-1);
        }

        return false;
    }
}
