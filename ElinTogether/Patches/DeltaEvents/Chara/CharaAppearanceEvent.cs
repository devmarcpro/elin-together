using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(LayerEditPCC), nameof(LayerEditPCC.Apply))]
internal static class CharaAppearanceEvent
{
    [HarmonyPostfix]
    internal static void OnApplyLook(LayerEditPCC __instance)
    {
        // (the player's own look, or a resident's or a companion's from the list of the base; one the others know)
        if (NetSession.Instance.Connection is not { } connection ||
            __instance.chara is not { pccData: not null } chara || (!chara.IsPC && !CardCache.Contains(chara))) {
            return;
        }

        connection.Delta.AddRemote(CharaAppearanceDelta.Create(chara));
    }
}

/// <summary>
///     "Toggle PCC" of the list of the base gives a resident a random full look: told like an edited one
/// </summary>
[HarmonyPatch]
internal static class CharaTogglePccEvent
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        var create = AccessTools.Method(typeof(PCCData), nameof(PCCData.Create));
        return typeof(BaseListPeople).GetNestedTypes(AccessTools.all).SelectMany(AccessTools.GetDeclaredMethods)
            .Where(m => !m.IsAbstract && PatchProcessor.GetOriginalInstructions(m).Any(c => c.Calls(create)));
    }

    [HarmonyPostfix]
    internal static void OnToggle(object __instance)
    {
        var chara = CharaOf(__instance, 2);
        if (NetSession.Instance.Connection is { } connection && chara is { pccData: not null } && CardCache.Contains(chara)) {
            connection.Delta.AddRemote(CharaAppearanceDelta.Create(chara));
        }
    }

    // the resident, held by the closure or by the closure it was made in
    private static Chara? CharaOf(object? closure, int depth)
    {
        if (closure is Chara chara) {
            return chara;
        }

        if (closure is null || depth == 0 || closure is Card or Component) {
            return null;
        }

        return AccessTools.GetDeclaredFields(closure.GetType()).Where(f => !f.FieldType.IsValueType)
            .Select(f => CharaOf(f.GetValue(closure), depth - 1)).FirstOrDefault(c => c is not null);
    }
}
