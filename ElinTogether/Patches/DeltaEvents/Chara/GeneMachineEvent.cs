using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     See <see cref="GeneMachineDelta" />: a guest's choices in the gene machine's windows go to the host
/// </summary>
[HarmonyPatch]
internal static class GeneMachineEvent
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        // the choice of a resident in the machine's list (a lambda of TraitGeneMachine.OnUse)
        return typeof(TraitGeneMachine).GetNestedTypes(AccessTools.all).SelectMany(AccessTools.GetDeclaredMethods)
            .Concat(AccessTools.GetDeclaredMethods(typeof(TraitGeneMachine)))
            .Where(m => m.Name.Contains("<OnUse>") && m.ReturnType == typeof(void) &&
                        m.GetParameters() is [{ ParameterType: var t }] && t == typeof(Chara));
    }

    // (a guest's game cannot lay the condition on a resident, the host's runs them: the game's lambda broke halfway
    // there. The host does all of it, the guest sees it come back)
    [HarmonyPrefix]
    internal static bool OnChosen(object __instance, Chara __0)
    {
        var machine = __instance as TraitGeneMachine ?? AccessTools.GetDeclaredFields(__instance.GetType())
            .Select(f => f.GetValue(__instance)).OfType<TraitGeneMachine>().FirstOrDefault();
        if (machine is null || NetSession.Instance.Connection is not ElinNetClient client || ElinDelta.IsApplying) {
            return true;
        }

        client.Delta.AddRemote(new GeneMachineDelta { Machine = machine.owner, Chara = __0 });
        return false;
    }

    // the host's own choice: the others learn the machine the resident lies in
    [HarmonyPostfix]
    internal static void OnChosenHere(object __instance, Chara __0, bool __runOriginal)
    {
        var machine = __instance as TraitGeneMachine ?? AccessTools.GetDeclaredFields(__instance.GetType())
            .Select(f => f.GetValue(__instance)).OfType<TraitGeneMachine>().FirstOrDefault();
        if (__runOriginal && machine is not null && NetSession.Instance.Connection is ElinNetHost host && !ElinDelta.IsApplying) {
            host.Delta.AddRemote(new GeneMachineDelta { Machine = machine.owner, Chara = __0 });
        }
    }
}

/// <summary>
///     The gene put into the resident lying in the machine
/// </summary>
[HarmonyPatch(typeof(InvOwnerGene), nameof(InvOwnerGene._OnProcess))]
internal static class GeneInsertEvent
{
    [HarmonyPostfix]
    internal static void OnInserted(InvOwnerGene __instance, Thing t)
    {
        // a guest asks the host; the host tells the others
        if (NetSession.Instance.Connection is { } connection && !ElinDelta.IsApplying && t.parent == __instance.tg) {
            connection.Delta.AddRemote(new GeneMachineDelta { Machine = __instance.owner, Chara = __instance.tg, Gene = t });
        }
    }
}
