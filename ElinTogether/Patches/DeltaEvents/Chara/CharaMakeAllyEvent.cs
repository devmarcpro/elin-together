using System;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Chara), nameof(Chara.MakeAlly))]
internal static class CharaMakeAllyEvent
{
    private static Chara? _giftFor;

    /// <summary>
    ///     The remote player the host is acting for right now (applying what it sent), see ElinDelta.Apply
    /// </summary>
    internal static Chara? Actor { get; set; }

    /// <summary>
    ///     Host side: the player an ally made at this instant follows, when nothing said so already. The one a
    ///     gift is for, the one whose delta is being applied, or the one whose task the host just completed
    ///     (taming with a brush runs here, on the host's copy of that player)
    /// </summary>
    internal static Chara? Recruiter(Chara ally)
    {
        if (NetSession.Instance.Connection is not ElinNetHost) {
            return null;
        }

        var player = _giftFor ?? Actor ??
                     (CharaProgressCompleteEvent.Chara is { IsRemotePlayer: true } worker ? worker : null) ??
                     (ActingRemotePlayer is { IsRemotePlayer: true, isDead: false } acting ? acting : null);
        return player is not null && player != ally && !player.IsPC ? player : null;
    }

    /// <summary>
    ///     The host's copy of a remote player whose turn is running (its mirrored task ticks here)
    /// </summary>
    internal static Chara? ActingRemotePlayer { get; set; }

    /// <summary>
    ///     An ally given during this scope (a gift pack) follows that player, not the party leader
    /// </summary>
    internal static ScopeExit GiftsFor(Chara player)
    {
        var previous = _giftFor;
        _giftFor = player;
        return new() {
            OnExit = () => _giftFor = previous,
        };
    }

    [HarmonyPrefix]
    internal static bool OnMakeAlly(Chara __instance, bool msg)
    {
        if (__instance.CompanionOwnerUid == 0 && !__instance.IsPCFaction && Recruiter(__instance) is { } recruiter) {
            __instance.SetCompanionOwner(recruiter);
        } else if (_giftFor is { } receiver && __instance != receiver && __instance.CompanionOwnerUid == 0) {
            __instance.SetCompanionOwner(receiver);
        }

        // recruited on our own (travelling alone, or hosting a zone): ours, not the host's
        if (NetSession.Instance is { IsAway: true, Connection: not ElinNetClient } && !ElinDelta.IsApplying &&
            __instance.CompanionOwnerUid == 0) {
            __instance.SetCompanionOwner(EClass.pc);
        }

        switch (NetSession.Instance.Connection) {
            case ElinNetHost host:
                host.Delta.AddRemote(new CharaMakeAllyDelta {
                    Owner = __instance,
                    ShowMsg = msg,
                    TemporaryAllyName = __instance.c_altName,
                    OwnerUid = __instance.CompanionOwnerUid,
                });
                return true;
            case ElinNetClient client:
                // we are clients, drop the update and wait for delta
                if (!ElinDelta.IsApplying) {
                    var request = CharaMakeAllyRequestDelta.Create(__instance, msg);
                    client.Delta.AddRemote(request);
                    // sent whole: it comes back from the host under a uid of the world, the local one would
                    // stay next to it as a double nobody else sees
                    if (request.Data is not null) {
                        __instance.Destroy();
                    }
                }
                return false;
            default:
                return true;
        }
    }

    extension(Chara chara)
    {
        [HarmonyReversePatch(HarmonyReversePatchType.Snapshot)]
        internal void Stub_MakeAlly(bool msg)
        {
            throw new NotImplementedException("Chara.MakeAlly");
        }
    }
}