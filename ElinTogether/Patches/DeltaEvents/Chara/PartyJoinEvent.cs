using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     Asking a resident of the base to join the party (its dialog, the list of residents) adds it to the party
///     without making it an ally again, so it never went through <see cref="CharaMakeAllyEvent" />: the join
///     stayed in the game of the player who asked, and the resident followed nobody. <br />
///     A client asks the host, the host adds it for that player and tells everyone
/// </summary>
[HarmonyPatch]
internal static class PartyJoinEvent
{
    private static int _makingAlly;

    // Chara.MakeAlly adds to the party itself and is told as a whole
    [HarmonyPrefix]
    [HarmonyPriority(Priority.First)]
    [HarmonyPatch(typeof(Chara), nameof(Chara.MakeAlly))]
    internal static void OnMakeAlly()
    {
        _makingAlly++;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(Chara), nameof(Chara.MakeAlly))]
    internal static void OnMakeAllyEnd()
    {
        _makingAlly--;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Party), nameof(Party.AddMemeber))]
    internal static bool OnAddMember(Party __instance, Chara c, bool showMsg)
    {
        if (c is null || c.party == __instance || c.IsPC || c.GetBool("remote_chara") || __instance != EClass.pc?.party) {
            return true;
        }

        var session = NetSession.Instance;

        // asked on our own (travelling alone, or holding a map): ours, not the host's
        if (session is { IsAway: true, Connection: not ElinNetClient } && !ElinDelta.IsApplying && c.CompanionOwnerUid == 0) {
            c.SetCompanionOwner(EClass.pc);
        }

        if (_makingAlly > 0 || ElinDelta.IsApplying) {
            return true;
        }

        switch (session.Connection) {
            case ElinNetHost host:
                host.Delta.AddRemote(new CharaMakeAllyDelta {
                    Owner = c,
                    ShowMsg = showMsg,
                    TemporaryAllyName = c.c_altName,
                    OwnerUid = c.CompanionOwnerUid,
                    JoinOnly = true,
                });
                return true;
            case ElinNetClient client when !PendingUid.IsPending(c.uid):
                // we are clients, drop the update and wait for delta
                client.Delta.AddRemote(new CharaMakeAllyRequestDelta {
                    Owner = c,
                    LocalCardId = null,
                    ShowMsg = showMsg,
                    JoinOnly = true,
                });
                return false;
            default:
                return true;
        }
    }
}
