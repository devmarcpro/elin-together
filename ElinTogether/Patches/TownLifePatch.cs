using System.Collections.Generic;
using System.Reflection;
using System.Reflection.Emit;
using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Council 2026-10-23 (4), town life: in the host's game an NPC's idle life (AI_Idle) chats, greets, gossips and
///     stones only near the host's screen (isSynced, IsInMutterDistance) and always about the host's character and
///     karma. With company and the box ticked, it also runs near every other player on the map, and the greeting /
///     rumour / stone branch is about the nearest player, with that player's own karma. Only the AI's decision
///     changes: the host's renderer draws nothing for an NPC it does not see, its bubble goes to the guests only.
///     Without another player near, every helper answers what the game reads
/// </summary>
[HarmonyPatch]
internal static class TownLifePatch
{
    // about a screen around a player the host's game does not draw
    private const int NearTiles = 15;

    // the player the greeting branch of this idle step is about (null: the game's "the player")
    private static Chara? _target;

    // the NPC of this idle step, when it talks only because another player is near it
    private static Card? _speaker;

    private static ElinNetHost? Host =>
        NetSession.Instance.Connection is ElinNetHost host && EmpConfig.Server.TownLife.Value && NetCompany.HasCompany
            ? host
            : null;

    [HarmonyTranspiler]
    [HarmonyPatch(typeof(AI_Idle), nameof(AI_Idle.Run), MethodType.Enumerator)]
    internal static IEnumerable<CodeInstruction> OnRun(IEnumerable<CodeInstruction> instructions)
    {
        var codes = new List<CodeInstruction>(instructions);
        var isSynced = AccessTools.PropertyGetter(typeof(Card), nameof(Card.isSynced));
        var isSyncedChara = AccessTools.PropertyGetter(typeof(Chara), nameof(Chara.isSynced));
        var mutter = AccessTools.Method(typeof(Card), nameof(Card.IsInMutterDistance));
        var getPc = AccessTools.PropertyGetter(typeof(EClass), nameof(EClass.pc));
        var karma = AccessTools.Field(typeof(Player), nameof(Player.karma));
        var lastSeen = AccessTools.Field(typeof(Chara), nameof(Chara.turnLastSeen));

        // the 7 reads of the game version this was written for: the 1st (chat), 2nd (greeting branch) and 3rd (idle
        // talk) are the ones to widen; the others (drunk, the host's party feat, insanity) stay the host's
        var synced = codes.FindAll(c => c.Calls(isSynced) || c.Calls(isSyncedChara));
        if (synced.Count != 7) {
            EmpLog.Warning("Town life: AI_Idle reads isSynced {Count} times, not 7: left as the game has it", synced.Count);
            return codes;
        }

        var inGreeting = false;
        foreach (var code in codes) {
            if (code == synced[0] || code == synced[2]) {
                code.opcode = OpCodes.Call;
                code.operand = AccessTools.Method(typeof(TownLifePatch), nameof(Seen));
            } else if (code == synced[1]) {
                code.opcode = OpCodes.Call;
                code.operand = AccessTools.Method(typeof(TownLifePatch), nameof(Greets));
                inGreeting = true;
            } else if (inGreeting && code.Calls(getPc)) {
                code.operand = AccessTools.Method(typeof(TownLifePatch), nameof(Target));
            } else if (inGreeting && code.LoadsField(karma)) {
                code.opcode = OpCodes.Call;
                code.operand = AccessTools.Method(typeof(TownLifePatch), nameof(Karma));
            } else if (inGreeting && code.StoresField(lastSeen)) {
                inGreeting = false;
            } else if (code.Calls(mutter) && codes.IndexOf(code) is > 0 and var at && codes[at - 1].LoadsConstant(10)) {
                // the mutter at 10 tiles; the ambience sound at 15 stays around the host, it is played there
                code.opcode = OpCodes.Call;
                code.operand = AccessTools.Method(typeof(TownLifePatch), nameof(Mutters));
            }
        }

        return codes;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(AI_Idle), nameof(AI_Idle.Run), MethodType.Enumerator)]
    internal static void OnStep(out (Chara?, Card?) __state)
    {
        __state = (_target, _speaker);
        _target = null;
        _speaker = null;
    }

    // in a finalizer: nothing of a step leaks into the next one, even if the game's own code throws
    [HarmonyFinalizer]
    [HarmonyPatch(typeof(AI_Idle), nameof(AI_Idle.Run), MethodType.Enumerator)]
    internal static void OnStepEnd((Chara?, Card?) __state)
    {
        (_target, _speaker) = __state;
    }

    /// <summary>
    ///     Seen by the host's screen, or near another player
    /// </summary>
    internal static bool Seen(Card owner)
    {
        if (owner.isSynced) {
            return true;
        }

        if (NearestOther(owner, NearTiles) is null) {
            return false;
        }

        _speaker = owner;
        return true;
    }

    internal static bool Mutters(Card owner, int distance)
    {
        if (owner.IsInMutterDistance(distance)) {
            return true;
        }

        if (NearestOther(owner, distance) is null) {
            return false;
        }

        _speaker = owner;
        return true;
    }

    /// <summary>
    ///     The greeting branch: about the nearest of the players who would see it
    /// </summary>
    internal static bool Greets(Card owner)
    {
        var synced = owner.isSynced;
        if (NearestOther(owner, NearTiles) is not { } other) {
            return synced;
        }

        if (synced && owner.Dist(EClass.pc) <= owner.Dist(other)) {
            return true;
        }

        _target = other;
        if (!synced) {
            _speaker = owner;
        }

        return true;
    }

    internal static Chara Target()
    {
        return _target ?? EClass.pc;
    }

    internal static int Karma(Player player)
    {
        // without personal karma, the host's is everyone's
        return _target is not null && PersonalQuests.Enabled && Host is { } host ? host.KarmaOf(_target) : player.karma;
    }

    private static Chara? NearestOther(Card owner, int distance)
    {
        if (Host is not { } host) {
            return null;
        }

        Chara? nearest = null;
        foreach (var chara in host.ActiveRemoteCharas.Values) {
            if (chara.IsAliveInCurrentZone && owner.pos.Distance(chara.pos) < distance &&
                (nearest is null || owner.Dist(chara) < owner.Dist(nearest))) {
                nearest = chara;
            }
        }

        return nearest;
    }

    /// <summary>
    ///     The game's talk returns at once for an NPC off the host's screen: it goes on for the one near another
    ///     player, so its bubble and line reach the guests (ChatBubbleEvent, MsgSaySynchronizationContext)
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.Talk))]
    internal static void OnTalk(Card __instance, ref bool forceSync)
    {
        if (_speaker is not null && ReferenceEquals(__instance, _speaker)) {
            forceSync = true;
        }
    }

    [HarmonyTranspiler]
    [HarmonyPatch(typeof(Chara), nameof(Chara.TalkTopic))]
    internal static IEnumerable<CodeInstruction> OnTalkTopic(IEnumerable<CodeInstruction> instructions)
    {
        var isSynced = AccessTools.PropertyGetter(typeof(Card), nameof(Card.isSynced));
        var isSyncedChara = AccessTools.PropertyGetter(typeof(Chara), nameof(Chara.isSynced));
        var speaks = AccessTools.Method(typeof(TownLifePatch), nameof(Speaks));
        foreach (var code in instructions) {
            if (code.Calls(isSynced) || code.Calls(isSyncedChara)) {
                code.opcode = OpCodes.Call;
                code.operand = speaks;
            }

            yield return code;
        }
    }

    internal static bool Speaks(Card card)
    {
        return card.isSynced || (_speaker is not null && ReferenceEquals(card, _speaker));
    }

    /// <summary>
    ///     The host's renderer of an NPC it does not see draws no bubble (ChatBubbleEvent has sent it already)
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPriority(Priority.Last)]
    [HarmonyPatch(typeof(CardRenderer), nameof(CardRenderer.Say))]
    internal static bool OnSay(CardRenderer __instance)
    {
        return _speaker is null || __instance.isSynced ||
               !ReferenceEquals(ChatBubbleEvent.TalkSpeakerContext.Speaker ?? __instance.owner, _speaker);
    }
}
