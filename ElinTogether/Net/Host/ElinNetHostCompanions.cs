using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Helper.Extensions;
using ElinTogether.Models;
using ElinTogether.Patches;

namespace ElinTogether.Net;

/// <summary>
///     Companions of a player travel with it: off this map while it is away, back next to it when it returns
/// </summary>
internal partial class ElinNetHost
{
    /// <summary>
    ///     The player leaves this map (travelling alone, disconnecting): its companions go with it and stay
    ///     in the party, off map, until it comes back, see BringCompanions
    /// </summary>
    private void TakeCompanionsAlong(Chara player)
    {
        if (EClass.game?.player?.chara is null) {
            return;
        }

        foreach (var companion in CompanionHelper.CompanionsOf(player)) {
            if (companion.isDead || companion.currentZone is null) {
                continue;
            }

            companion.SetNoGoal();
            if (companion.parent is Zone zone) {
                zone.RemoveCard(companion);
            }

            companion.currentZone = null;

            Delta.AddRemote(new CharaRemoveFromGameDelta {
                Owner = companion,
            });

            EmpLog.Debug("Companion {Uid} leaves with player {OwnerUid}",
                companion.uid, player.uid);
        }
    }

    /// <summary>
    ///     The player stands on this map again, its companions join it
    /// </summary>
    /// <param name="keepSpot">back on the map they never really left: each where it stood, not around the player</param>
    private void BringCompanions(Chara player, bool keepSpot = false)
    {
        foreach (var companion in CompanionHelper.CompanionsOf(player)) {
            if (companion.isDead || companion.currentZone is not null) {
                continue;
            }

            // its mount, and what rides it, stand on the player's own tile, as the game keeps them
            var carried = companion == player.ride || companion == player.parasite;
            var near = keepSpot && companion.pos is { IsValid: true, IsInBounds: true } ? companion.pos : player.pos;
            var pos = carried ? player.pos.Copy() : near.GetNearestPoint(allowChara: false, allowInstalled: false) ?? near.Copy();

            // the game may already have laid it on the player's tile (Chara.SyncRide, when the player was put on the
            // map): laid a second time beside it, it stayed in the cell of the first for good
            if (companion.pos is { IsValid: true, IsInBounds: true }) {
                _map._RemoveCard(companion);
            }

            Delta.AddRemote(CardGenDelta.Create(companion));
            _zone.AddCard(companion, pos);

            CardCache.Add(companion);
            CardCache.CacheContainer(companion.things);

            // replicas dropped it from their party when it left
            Delta.AddRemote(new CharaMakeAllyDelta {
                Owner = companion,
                ShowMsg = false,
                TemporaryAllyName = companion.c_altName,
                OwnerUid = companion.CompanionOwnerUid,
            });

            EmpLog.Debug("Companion {Uid} back with player {OwnerUid} at {@Pos}",
                companion.uid, player.uid, pos);
        }
    }

    /// <summary>
    ///     Swap the host copies of the companions for the ones simulated by their travelling owner
    /// </summary>
    /// <param name="rebound">filled with the numbers given to their cards that waited for one: old -> new</param>
    private void ReplaceCompanions(List<LZ4Bytes>? companions, int ownerUid, Dictionary<int, int>? rebound = null)
    {
        if (ownerUid == 0) {
            return;
        }

        if (companions is null) {
            RebindRide(ownerUid);
            return;
        }

        var party = pc.party;
        var kept = new HashSet<int>();

        foreach (var data in companions) {
            var uploaded = data.Decompress<Chara>();
            var old = game.cards.globalCharas.Find(uploaded.uid);
            kept.Add(uploaded.uid);

            if (old is not null && old.parent is Zone && old.currentZone == _zone) {
                // never left this map with its owner, the host copy is the live one
                EmpLog.Warning("Companion {Uid} of player {OwnerUid} is on the host map, keeping host copy",
                    uploaded.uid, ownerUid);
                continue;
            }

            ForgetCachedCard(uploaded);
            if (old is not null) {
                ForgetCachedCard(old);
                game.cards.globalCharas.Remove(old);

                // branches hold object references
                if (old.homeBranch is { } branch && branch.members.IndexOf(old) is var index and >= 0) {
                    branch.members[index] = uploaded;
                }
            }

            uploaded.SetInt(CompanionHelper.OwnerKey, ownerUid);
            // off map until the owner comes back, see BringCompanions
            uploaded.currentZone = null;
            game.cards.globalCharas.Add(uploaded);

            // the uploaded copy carries its own copy of the party, rebuild members from the uids
            // died on the way: out of the party, dead, until someone revives it
            var member = !uploaded.isDead && uploaded.party?.uidMembers.Contains(uploaded.uid) is true;
            uploaded.party = member ? party : null;
            if (member && !party.uidMembers.Contains(uploaded.uid)) {
                party.uidMembers.Add(uploaded.uid);
            } else if (!member && party.uidMembers.Remove(uploaded.uid)) {
                EmpLog.Information("Companion {Uid} of player {OwnerUid} died while travelling",
                    uploaded.uid, ownerUid);
            }

            party.SetMembers();

            foreach (var thing in uploaded.things.Flatten().ToList()) {
                if (PendingUid.IsPending(thing.uid)) {
                    var pending = thing.uid;
                    game.cards.AssignUID(thing);
                    rebound?[pending] = thing.uid;
                }
            }

            EmpLog.Debug("Replaced companion {Uid} of player {OwnerUid}",
                uploaded.uid, ownerUid);
        }

        // let go while travelling (only those travelling with it, off map here)
        foreach (var gone in party.members.ToList()) {
            if (gone is null || gone.CompanionOwnerUid != ownerUid || kept.Contains(gone.uid) ||
                gone.currentZone is not null || gone.GetBool("remote_chara")) {
                continue;
            }

            EmpLog.Information("Companion {Uid} left player {OwnerUid} while travelling",
                gone.uid, ownerUid);

            party.RemoveMember(gone);
            gone.SetInt(CompanionHelper.OwnerKey, 0);
            if (gone.homeZone is { } home) {
                gone.MoveZone(home);
            }
        }

        RebindRide(ownerUid);
    }

    private static void RebindRide(int ownerUid)
    {
        if (game.cards.globalCharas.Find(ownerUid) is { } player) {
            CompanionHelper.RebindRide(player);
        }
    }
}
