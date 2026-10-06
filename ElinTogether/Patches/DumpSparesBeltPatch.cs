using System.Collections.Generic;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Council 10: in a session, auto-dump leaves the item in hand and the tool belt's content, as the game already
///     leaves the hotbar. Without a session, or with the rule off, it is the game's own dump
/// </summary>
[HarmonyPatch]
internal static class DumpSparesBeltPatch
{
    [HarmonyPostfix]
    [HarmonyPatch(typeof(TaskDump), nameof(TaskDump.ListThingsToPut))]
    private static void OnList(List<Thing> __result)
    {
        if (NetSession.Instance.Transport is not null && NetSession.Instance.Rules.DumpSparesBelt) {
            __result.RemoveAll(t => t == EClass.pc.held || (t.parent as Thing)?.trait is TraitToolBelt);
        }
    }
}
