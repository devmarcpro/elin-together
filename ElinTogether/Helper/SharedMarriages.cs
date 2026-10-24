using System;
using System.Collections.Generic;
using ElinTogether.LangMod;
using ElinTogether.Models;
using ElinTogether.Net;
using ElinTogether.Patches;
using HarmonyLib;

namespace ElinTogether.Helper;

/// <summary>
///     Council 2026-10-24, host option "Shared marriages": a resident is the spouse of the character who married it,
///     the host keeps who (<see cref="ElinNetHost.Spouses" />). A guest's proposal and wedding are requests the host
///     runs for it, first come first served; the divorce and lost ring deeds go through
///     <see cref="CardActReplayEvent" />. Everyone sees the resident married (IsMarried), the wedding choice and the
///     deeds are for its spouse only. Off: as before, a guest's marriage stays in its own game
/// </summary>
[HarmonyPatch]
internal static class SharedMarriages
{
    private const int FeatMarried = 1275;

    internal static bool Enabled => NetSession.Instance.Rules.SharedMarriages;

    // a guest's copy of the host's list
    private static Dictionary<int, int> _known = [];

    // the host replays a guest's divorce deed: the guest already said yes in its own game
    private static bool _saidYes;

    [ElinPreLoad]
    private static void Forget(GameIOContext context)
    {
        _known = [];
    }

    /// <summary>
    ///     The player character this resident is married to. On the host a married one without a record is the
    ///     host's character (an old save)
    /// </summary>
    internal static int SpouseOf(Chara npc)
    {
        if (NetSession.Instance.Connection is ElinNetClient) {
            return _known.GetValueOrDefault(npc.uid);
        }

        return ElinNetHost.Spouses.TryGetValue(npc.uid, out var uid) ? uid : npc.IsMarried ? EClass.player.uidChara : 0;
    }

    /// <summary>
    ///     "The player" (the one standing in on the host) is this resident's spouse
    /// </summary>
    internal static bool IsMine(Chara npc)
    {
        return !Enabled || !npc.IsMarried || SpouseOf(npc) == EClass.pc.uid;
    }

    internal static ScopeExit SaidYes()
    {
        _saidYes = true;
        return new() {
            OnExit = () => _saidYes = false,
        };
    }

    /// <summary>
    ///     A guest's proposal, as the dialog would have run it in the host's game with the guest as the player
    /// </summary>
    internal static void MarryFor(ElinNetHost host, int peerId, Chara sender, Chara npc)
    {
        if (npc.IsMarried) {
            host.SendDeltaTo(peerId, StateOf(npc, MarriageDelta.Step.Refused, sender.uid));
            return;
        }

        using (ElinDelta.Simulate())
        using (MsgRelayContext.RedirectTo(sender))
        using (RemoteCraft.AsCrafter(sender)) {
            StoryOutcomeDelta.RunGameOutcome(nameof(DramaOutcome.marry), npc);
        }
    }

    internal static void WedFor(ElinNetHost host, Chara sender, Chara npc)
    {
        if (SpouseOf(npc) != sender.uid || npc.c_love is not { } love) {
            return;
        }

        love.dateWedding = EClass.world.date.GetRaw();
        host.Delta.AddRemote(StateOf(npc, MarriageDelta.Step.State, 0));
    }

    private static MarriageDelta StateOf(Chara npc, MarriageDelta.Step kind, int told)
    {
        return new() {
            Kind = kind,
            Npc = npc,
            Spouse = npc.IsMarried ? SpouseOf(npc) : 0,
            DateMarriage = npc.c_love?.dateMarriage ?? 0,
            DateWedding = npc.c_love?.dateWedding ?? 0,
            UidZone = npc.c_love?.uidZoneMarriage ?? 0,
            NameZone = npc.c_love?.nameZoneMarriage,
            Feat = npc.elements.ValueWithoutLink(FeatMarried),
            Told = told,
        };
    }

    /// <summary>
    ///     A guest learns what the host decided
    /// </summary>
    internal static void Learn(MarriageDelta delta)
    {
        if (delta.Spouses is { } all) {
            _known = new(all);
            return;
        }

        if (delta.Npc is null) {
            return;
        }

        if (delta.Spouse != 0) {
            _known[delta.Npc.Uid] = delta.Spouse;
        } else {
            _known.Remove(delta.Npc.Uid);
        }

        if (delta.Npc.Find() is Chara npc) {
            npc.c_love ??= new();
            npc.c_love.dateMarriage = delta.DateMarriage;
            npc.c_love.dateWedding = delta.DateWedding;
            npc.c_love.uidZoneMarriage = delta.UidZone;
            npc.c_love.nameZoneMarriage = delta.NameZone;
            npc.SetFeat(FeatMarried, delta.Feat);
        }

        if (delta.Told != EClass.pc.uid) {
            return;
        }

        // the count of the player who married or divorced, in its own game only
        switch (delta.Kind) {
            case MarriageDelta.Step.Marry:
                EClass.player.stats.married++;
                break;
            case MarriageDelta.Step.Divorced:
                EClass.player.stats.divorced++;
                break;
            case MarriageDelta.Step.Refused:
                Msg.Say("emp_marriage_taken".Loc((delta.Npc.Find() as Chara)?.NameBraced ?? "?"));
                break;
        }
    }

    /// <summary>
    ///     A guest's proposal asks the host, nothing happens in its game. The host turns down one for a resident
    ///     already married (someone was first)
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(DramaOutcome), nameof(DramaOutcome.marry))]
    internal static bool OnMarryOutcome(DramaOutcome __instance)
    {
        if (!Enabled || ElinDelta.IsApplying || __instance.manager?.tg?.chara is not { } npc) {
            return true;
        }

        switch (NetSession.Instance.Connection) {
            case ElinNetClient client:
                client.Delta.AddRemote(new MarriageDelta {
                    Kind = MarriageDelta.Step.Marry,
                    Npc = npc,
                });
                return false;
            case ElinNetHost when npc.IsMarried:
                Msg.Say("emp_marriage_taken".Loc(npc.NameBraced));
                return false;
        }

        return true;
    }

    /// <summary>
    ///     On the host: who married whom goes in the list and to everyone; only the one who married counts it
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Marry))]
    internal static void OnMarried(Chara __instance, Chara c)
    {
        if (!Enabled || ElinDelta.IsApplying ||
            NetSession.Instance.Connection is not ElinNetHost { IsZoneSession: false } host) {
            return;
        }

        ElinNetHost.Spouses[__instance.uid] = c.uid;
        if (c.uid != EClass.player.uidChara) {
            EClass.player.stats.married--;
        }

        host.Delta.AddRemote(StateOf(__instance, MarriageDelta.Step.Marry, c.uid));
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Divorce))]
    internal static void OnDivorce(Chara __instance, out bool __state)
    {
        __state = __instance.IsMarried;
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Divorce))]
    internal static void OnDivorced(Chara __instance, Chara c, bool __state)
    {
        if (!__state || !Enabled || ElinDelta.IsApplying ||
            NetSession.Instance.Connection is not ElinNetHost { IsZoneSession: false } host) {
            return;
        }

        ElinNetHost.Spouses.Remove(__instance.uid);
        if (c.uid != EClass.player.uidChara) {
            EClass.player.stats.divorced--;
        }

        host.Delta.AddRemote(StateOf(__instance, MarriageDelta.Step.Divorced, c.uid));
    }

    /// <summary>
    ///     The wedding is accepted (the game sets dateWedding right after this line): a guest asks the host, the host
    ///     tells everyone
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(DramaCustomSequence), nameof(DramaCustomSequence.GetTopic))]
    internal static void OnTopic(Chara c, string idTopic)
    {
        if (idTopic != "wedding_accept" || !Enabled || ElinDelta.IsApplying || c.c_love is null) {
            return;
        }

        switch (NetSession.Instance.Connection) {
            case ElinNetClient client:
                client.Delta.AddRemote(new MarriageDelta {
                    Kind = MarriageDelta.Step.Wed,
                    Npc = c,
                });
                break;
            case ElinNetHost host:
                c.c_love.dateWedding = EClass.world.date.GetRaw();
                host.Delta.AddRemote(StateOf(c, MarriageDelta.Step.State, 0));
                break;
        }
    }

    /// <summary>
    ///     "Wedding" in the dialog of a married resident: for its spouse only
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(DramaCustomSequence), nameof(DramaCustomSequence.Choice), typeof(string), typeof(string), typeof(bool))]
    internal static bool OnChoice(DramaCustomSequence __instance, string lang, string idJump, ref DramaChoice __result)
    {
        if (idJump != "_wed" || __instance.manager?.tg?.chara is not { } npc || IsMine(npc)) {
            return true;
        }

        // never shown
        __result = new(lang.lang(), idJump);
        return false;
    }

    /// <summary>
    ///     The divorce and lost ring deeds target the holder's spouse only. First, before the replay of
    ///     CardActReplayEvent counts the entries
    /// </summary>
    [HarmonyPostfix]
    [HarmonyPriority(Priority.First)]
    [HarmonyPatch(typeof(TraitDeedDivorce), nameof(Trait.TrySetHeldAct))]
    internal static void OnDivorceDeed(ActPlan p)
    {
        KeepSpouseOnly(p);
    }

    [HarmonyPostfix]
    [HarmonyPriority(Priority.First)]
    [HarmonyPatch(typeof(TraitDeedLostRing), nameof(Trait.TrySetHeldAct))]
    internal static void OnLostRingDeed(ActPlan p)
    {
        KeepSpouseOnly(p);
    }

    private static void KeepSpouseOnly(ActPlan p)
    {
        p.list.RemoveAll(i => i.act is DynamicAct { id: "actDivorce" or "actReissue" } && i.tc is Chara npc && !IsMine(npc));
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Dialog), nameof(Dialog.YesNo))]
    internal static bool OnYesNo(Action actionYes, ref Dialog? __result)
    {
        if (!_saidYes) {
            return true;
        }

        __result = null;
        actionYes();
        return false;
    }
}
