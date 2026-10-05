using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Four things of the base are paid for and then made in this game's own copy of the base, which the host never
///     sees: the research board (knowledge), the plans sold by a merchant (the base's money), the hearth upgrade
///     (the player's gold) and the skills of the hearth (platinum). The payment reaches the host, the effect does not:
///     the player pays for nothing. Until they are real requests to the host (step 2), a client says "only the host
///     can do this for now" and nothing is paid, nothing is made <br />
///     "Client" is <c>Connection is ElinNetClient</c>: a player on the host's map, and the host itself visiting a zone
///     simulated by a guest (its zone session is a client one, the guest's game is the one that keeps the zone: same
///     rule). Null while alone in an away zone (the game runs as single player there) and a host session otherwise:
///     the game runs as it always did
/// </summary>
[HarmonyPatch]
internal static class RemoteBasePaidPatch
{
    // ItemResearch.SetPlan asks CanCompletePlan to colour the price: the refusal is for the click only
    private static bool _listing;

    private static bool IsClient => NetSession.Instance.Connection is ElinNetClient && !ElinDelta.IsApplying;

    private static void Refuse(bool beep)
    {
        if (beep) {
            SE.Beep();
        }

        EmpPop.Information("emp_base_host_only".lang());
    }

    /// <summary>
    ///     Research: the click of a plan asks CanCompletePlan before it opens the "buy" menu, whose button takes the
    ///     knowledge and completes the plan. Said no here, the menu never opens (the game beeps by itself)
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(ItemResearch), nameof(ItemResearch.SetPlan))]
    private static void OnListing()
    {
        _listing = true;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(ItemResearch), nameof(ItemResearch.SetPlan))]
    private static void OnListed()
    {
        _listing = false;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(ResearchManager), nameof(ResearchManager.CanCompletePlan))]
    private static bool OnCanCompletePlan(ref bool __result)
    {
        if (_listing || !IsClient) {
            return true;
        }

        Refuse(false);
        __result = false;
        return false;
    }

    /// <summary>
    ///     Plans of the merchant and hearth upgrade: both are steps of the dialog (the payment is in the step, the
    ///     choice only jumps to it). A client jumping to one is sent back to the step it came from, which is
    ///     shown again as for any other "back"
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(DramaSequence), nameof(DramaSequence.Play), typeof(string))]
    private static void OnPlayStep(DramaSequence __instance, ref string id)
    {
        if (id is not ("_buyPlan" or "_upgradeHearth") || !IsClient) {
            return;
        }

        Refuse(true);
        id = __instance.lastStep ?? "";
    }

    /// <summary>
    ///     Skills of the hearth: the click reads its callback from the list at each click, so it is wrapped there
    ///     (the click does the check of the price, the yes/no box, the payment and the new level)
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(LayerHome), nameof(LayerHome.RefreshFeat))]
    private static void OnRefreshFeat(LayerHome __instance)
    {
        if (__instance.listFeat.callbacks is not UIList.Callback<Element, ButtonElement> { onClick: { } original } callbacks) {
            return;
        }

        callbacks.onClick = (element, button) => {
            if (IsClient) {
                Refuse(true);
            } else {
                original(element, button);
            }
        };
    }
}
