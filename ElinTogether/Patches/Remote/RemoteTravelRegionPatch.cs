using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Reflection.Emit;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using EModding.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A step on the world map. Council 10 (rule TimeJumpsTogether): it moves the date, three hours, only when
///     it is the host's and every player is on the world map; whoever steps always pays it with its own body, the
///     turns of hunger and conditions of its character and of its companions, as in a solo game. <br />
///     Rule off: only the game that simulates the map runs the step, and each one adds its hours for all
/// </summary>
[HarmonyPatch]
internal static class RemoteTravelRegionPatch
{
    // "your trip does not move the date" was said on this trip
    private static bool _told;

    /// <summary>
    ///     The turns of the step in progress are being played: those of this game's player and companions only
    /// </summary>
    internal static bool IsPayingStep { get; private set; }

    [HarmonyTranspiler]
    [HarmonyPatch(typeof(Chara), nameof(Chara._Move))]
    internal static IEnumerable<CodeInstruction> OnRegionTravelIl(IEnumerable<CodeInstruction> instructions)
    {
        var original = instructions.ToList();

        // a game that changed this function must not stop the patches after this one: all or nothing, with a warning
        var matcher = new CodeMatcher(original)
            .MatchEndForward(
                new OperandContains(OpCodes.Call, nameof(Chara.currentZone)),
                new OperandContains(OpCodes.Callvirt, nameof(Spatial.IsRegion)));
        if (matcher.IsInvalid) {
            return Unpatched(original, "Chara._Move currentZone.IsRegion");
        }

        matcher
            .Advance(1)
            .InsertAndAdvance(
                new CodeInstruction(OpCodes.Ldarg_0),
                Transpilers.EmitDelegate((bool isRegion, Chara chara) => {
                    if (!isRegion) {
                        _told = false;
                        return false;
                    }

                    var session = NetSession.Instance;
                    if (session.IsHost) {
                        return true;
                    }

                    // next to the one who simulates the map: its step is its own to pay too
                    if (session.Rules.TimeJumpsTogether) {
                        return chara.IsPC;
                    }

                    // client exp comp
                    if (chara.IsPC) {
                        EClass.player.distanceTravel++;
                    }

                    return false;
                }))
            .MatchStartForward(
                new OperandContains(OpCodes.Callvirt, nameof(GameDate.AdvanceMin)));
        if (matcher.IsInvalid) {
            return Unpatched(original, "Chara._Move date.AdvanceMin");
        }

        return matcher
            .SetAndAdvance(OpCodes.Call, AccessTools.Method(typeof(RemoteTravelRegionPatch), nameof(StepDate)))
            .InstructionEnumeration();
    }

    internal static IEnumerable<CodeInstruction> Unpatched(List<CodeInstruction> original, string what)
    {
        EmpLog.Warning("Travel on the world map: {What} not found in the game's code, the function is left as the " +
                       "game wrote it (travel moves the date for everyone)", what);
        return original;
    }

    // the step ended, or threw
    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Chara), nameof(Chara._Move))]
    internal static void OnMoveEnd(Chara __instance)
    {
        if (__instance.IsPC) {
            IsPayingStep = false;

            // the turns counted during the step go out, one message per character
            CharaTickConditionDelta.FlushStep(NetSession.Instance.Connection);
        }
    }

    /// <summary>
    ///     In place of the date.AdvanceMin of the step, right before its turns are played
    /// </summary>
    internal static void StepDate(GameDate date, int minutes)
    {
        var session = NetSession.Instance;
        IsPayingStep = session.Transport is not null && session.Rules.TimeJumpsTogether;

        if (DateMoves()) {
            date.AdvanceMin(minutes);
        } else {
            Tell();
        }
    }

    /// <summary>
    ///     Whether this game's travel (a step, an hour of the express travel) takes the date of the world along
    /// </summary>
    internal static bool DateMoves()
    {
        var session = NetSession.Instance;
        if (!session.Rules.TimeJumpsTogether) {
            return true;
        }

        return session.Transport switch {
            null => true,
            ElinNetHost host => host.AllOnWorldMap(),
            // ponytail: with the rule on, only the host's steps can move the date, as the council wrote it (the date
            // of a guest follows the host's). A guest does not know where the others are, so its own steps never
            // move it, next to the host or alone on its copy of the world map, and it says nothing about it (Tell).
            // Host/guest inequality that stays: everyone on the world map, the host steps: the date moves;
            // the guest steps: it does not. Telling the guest where everyone is would need one more message
            _ => false,
        };
    }

    /// <summary>
    ///     "Your friends are elsewhere": said only by the host, the one who knows it is true. A guest (next to the
    ///     host or alone on its copy of the map) cannot tell, so it stays silent
    /// </summary>
    internal static void Tell()
    {
        if (_told || NetSession.Instance.Transport is not ElinNetHost) {
            return;
        }

        _told = true;
        Msg.Say("emp_ui_travel_no_date".lang());
    }
}

/// <summary>
///     The turns a step on the world map costs are played for the whole party, which is everyone's here: only
///     the player who steps and its companions live them. The companions of a player next to the host are
///     simulated by the host, which is asked for each turn
/// </summary>
[HarmonyPatch(typeof(Chara), nameof(Chara.TickConditions))]
internal static class TravelStepTurnsPatch
{
    // before CharaTickConditionEvent, which drops what this game does not simulate
    [HarmonyPrefix]
    [HarmonyPriority(Priority.First)]
    internal static bool OnTickConditions(Chara __instance)
    {
        if (!RemoteTravelRegionPatch.IsPayingStep || __instance.IsPC) {
            return true;
        }

        if (!__instance.IsCompanionOf(EClass.pc)) {
            return false;
        }

        if (NetSession.Instance.Connection is not ElinNetClient client) {
            return true;
        }

        // counted with the step, sent when it ends. Harmony still runs CharaTickConditionEvent after this prefix
        // returned false, which skips its own message for a skipped original (__runOriginal)
        CharaTickConditionDelta.Emit(client, __instance);
        return false;
    }
}

/// <summary>
///     The express travel (LayerTravel) makes its hours pass by GameDate.AdvanceHour, one per image, from a
///     function the compiler generated: found by what it calls, nothing is patched when the game changes it. <br />
///     Same rule as a step: these hours pass for the world only when everyone travels. The traveller paid its
///     rations, the game asks nothing else of its body
/// </summary>
[HarmonyPatch]
internal static class TravelExpressPatch
{
    private static readonly MethodInfo AdvanceHour = AccessTools.Method(typeof(GameDate), nameof(GameDate.AdvanceHour));

    private static MethodBase? _target;

    private static MethodBase? FindTarget()
    {
        return typeof(LayerTravel)
            .GetNestedTypes(AccessTools.all)
            .SelectMany(type => AccessTools.GetDeclaredMethods(type))
            .FirstOrDefault(m => m.ReturnType == typeof(bool) && m.GetMethodBody() is not null &&
                                 PatchProcessor.ReadMethodBody(m).Any(il => Equals(il.Value, AdvanceHour)));
    }

    [HarmonyPrepare]
    private static bool Prepare()
    {
        _target ??= FindTarget();
        if (_target is null) {
            EmpLog.Warning("Express travel: no call to GameDate.AdvanceHour found in LayerTravel, " +
                           "its hours pass for everyone");
        }

        return _target is not null;
    }

    [HarmonyTargetMethod]
    private static MethodBase TargetMethod()
    {
        return _target ??= FindTarget()!;
    }

    [HarmonyTranspiler]
    private static IEnumerable<CodeInstruction> OnExpressHourIl(IEnumerable<CodeInstruction> instructions)
    {
        var original = instructions.ToList();

        var matcher = new CodeMatcher(original)
            .MatchStartForward(new CodeMatch(il => il.Calls(AdvanceHour)));
        if (matcher.IsInvalid) {
            return RemoteTravelRegionPatch.Unpatched(original, "LayerTravel date.AdvanceHour");
        }

        return matcher
            .SetAndAdvance(OpCodes.Call, AccessTools.Method(typeof(TravelExpressPatch), nameof(ExpressHour)))
            .InstructionEnumeration();
    }

    internal static void ExpressHour(GameDate date)
    {
        if (RemoteTravelRegionPatch.DateMoves()) {
            date.AdvanceHour();
        } else {
            RemoteTravelRegionPatch.Tell();
        }
    }
}
