using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Common;
using ElinTogether.Helper;
using ElinTogether.Helper.Extensions;
using ElinTogether.Models;
using ElinTogether.Patches;
using UnityEngine;

namespace ElinTogether.Net;

/// <summary>
///     Council 11, host rule SoftRecall: the host walks onto the map we hold alone. We hand the map and our
///     character back as always, but keep our game and our scene, and become a client of the host again in place:
///     the mirror of TakeOverZone / EnterAway. See ElinNetHost.CompleteSoftRejoin for the other side. <br />
///     Whatever does not go as expected ends with the copy of the world, as without the rule (AskWorldCopy)
/// </summary>
internal partial class ElinNetClient
{
    /// <summary>
    ///     How long we wait for <see cref="ZoneSoftRejoin" /> (or the world) after a release marked Soft: the
    ///     host saves, walks in and loads the map first
    /// </summary>
    private const float SoftRejoinWaitSeconds = 20f;

    private float _softRejoinDeadline;

    /// <summary>
    ///     The world was asked for (AskWorldCopy): should it never come, the link is closed as a lost one and the
    ///     game joins again by itself, as RetryZoneSync does
    /// </summary>
    private const float WorldAskWaitSeconds = 20f;

    private float _worldAskDeadline;

    /// <summary>
    ///     The map we stayed on: the placement the host sends next for it only confirms our tile, no map follows
    /// </summary>
    private int _softPlaced;

    /// <summary>
    ///     Our character and our map are with the host, its answer is not here yet: nothing moves in this game
    ///     meanwhile (see PauseGame), what would happen now is in neither copy
    /// </summary>
    internal bool IsAwaitingSoftRejoin => _softRejoinDeadline > 0;

    /// <summary>
    ///     We hold that map alone, stand on it alive, and nothing else is going on
    /// </summary>
    private bool CanRejoinSoftly()
    {
        return Session.Rules.SoftRecall && core.IsGameStarted && Session.IsZoneAuthority && Session.ZoneSession is null &&
               Session.AwayZone is { IsRegion: false, IsInstance: false } away && _zone == away && _map is not null &&
               pc is { isDead: false } && _pendingTravel is null && _pendingGrant is null && !_rejoining &&
               _handoffDeadline <= 0 && !HasBusyWindow();
    }

    /// <summary>
    ///     A dialogue or a trade holds the character it talks to: the switch replaces our stale copies of the
    ///     world's characters by the host's (AdoptHostCharas), the window would keep the old one, and what is sold
    ///     or given through it would be gone or exist twice. The world copy closes everything: that path then
    /// </summary>
    private static bool HasBusyWindow()
    {
        return LayerDrama.IsActive() || ui.GetLayer<LayerDragGrid>() is not null || LayerInventory.listInv.Any(inv =>
            inv.invs.Count > 0 && inv.invs[0].owner is { } owner && owner.Container != pc && owner.Container.GetRootCard() != pc);
    }

    private void UpdateSoftRejoinWait()
    {
        if (_worldAskDeadline > 0 && Time.realtimeSinceStartup >= _worldAskDeadline) {
            _worldAskDeadline = 0;
            EmpLog.Warning("No world {Seconds:F0}s after asking for it, joining the game again", WorldAskWaitSeconds);
            if (Host is not null) {
                Socket.Disconnect(Host, EmpDisconnectInfo.RemoteClosed);
            }

            return;
        }

        if (_softRejoinDeadline <= 0 || Time.realtimeSinceStartup < _softRejoinDeadline) {
            return;
        }

        AskWorldCopy(Session.AwayZone?.uid ?? -1, $"no answer after {SoftRejoinWaitSeconds:F0}s");
    }

    /// <summary>
    ///     Never a question to the player: the host sends the world and its map, which replace this game whatever
    ///     state it is in (OnSaveDataProbe, as a player coming back without the rule)
    /// </summary>
    private void AskWorldCopy(int zoneUid, string reason)
    {
        EmpLog.Warning("Soft rejoin of {ZoneUid} given up ({Reason}), asking the host for the world",
            zoneUid, reason);

        _softRejoinDeadline = 0;
        _softPlaced = 0;
        _worldAskDeadline = Time.realtimeSinceStartup + WorldAskWaitSeconds;

        // away again if the switch was made: nothing about the host map is taken until its world is here
        if (!Session.IsAway && _zone is { } here) {
            Session.AwayZone = here;
        }

        _rejoining = true;
        StopWorldStateUpdate();
        Delta.ClearOut();
        Delta.ClearIn();

        // link gone meanwhile: the lost link is handled where every lost link is
        Host?.Send(new ZoneSoftRejoinFailed {
            ZoneUid = zoneUid,
            Reason = reason,
        });
    }

    /// <summary>
    ///     Net event: the host stands on the map we handed back and runs it from now on
    /// </summary>
    private void OnZoneSoftRejoin(ZoneSoftRejoin rejoin)
    {
        if (_softRejoinDeadline <= 0) {
            // given up meanwhile: the host was told and sends the world
            EmpLog.Debug("Soft rejoin of {ZoneUid} arrives after we gave it up", rejoin.ZoneUid);
            return;
        }

        if (!_rejoining || !core.IsGameStarted || Session.AwayZone is not { } zone || zone.uid != rejoin.ZoneUid ||
            _zone != zone || _map is null || pc.isDead) {
            AskWorldCopy(rejoin.ZoneUid, "not standing on that map as we left it");
            return;
        }

        try {
            if (ApplySoftRejoin(zone, rejoin) is { } refused) {
                AskWorldCopy(rejoin.ZoneUid, refused);
            }
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Soft rejoin of {ZoneFullName} could not be applied", zone.ZoneFullName);
            AskWorldCopy(rejoin.ZoneUid, $"{ex.GetType().Name}: {ex.Message}");
        }
    }

    /// <returns>why the copy of the world is needed after all, null when we are a client of the host again</returns>
    private string? ApplySoftRejoin(Zone zone, ZoneSoftRejoin rejoin)
    {
        var companions = CompanionHelper.TravellingWith(pc);
        var own = pc.things.Flatten().Concat(companions.SelectMany(c => c.things.Flatten())).ToList();

        // the cards that waited for a number of the host take the one it gave their copy there. The only step that
        // can make a thing exist twice (two numbers for one card): every one of them is found before any is touched
        var renumbered = new List<(Thing Thing, int Uid)>();
        foreach (var (pending, real) in rejoin.Rebinds ?? []) {
            if (own.Find(t => t.uid == pending) is not { } thing) {
                return $"card {pending} the host renumbered {real} is not ours";
            }

            if (own.Exists(t => t.uid == real)) {
                return $"number {real} given by the host is taken here";
            }

            renumbered.Add((thing, real));
        }

        // (ability tokens are each game's own, the host drops them from its copy)
        if (own.Find(t => PendingUid.IsPending(t.uid) && t.trait is not TraitAbility &&
                          rejoin.Rebinds?.ContainsKey(t.uid) is not true) is { } unnumbered) {
            return $"card {unnumbered.uid} waits for a number the host did not give";
        }

        foreach (var (thing, uid) in renumbered) {
            thing.uid = uid;
        }

        // what we carry, as the host holds it since our release: nothing moved here meanwhile (IsAwaitingSoftRejoin)
        var bag = NetDesync.Bag(pc);
        if (bag != rejoin.BagMix) {
            return $"bag differs (here {bag:X8}, host {rejoin.BagMix:X8})";
        }

        var ours = ZoneLeaseState.Sums(_map);
        var sameMap = rejoin.MapSums is { } theirs && ZoneLeaseState.SameFloor(ours, theirs);
        if (sameMap && !ours.SequenceEqual(rejoin.MapSums!)) {
            // as when a map changes hands (AdoptHostCopy): told, not a reason to load the map under the player
            EmpLog.Information("Soft rejoin of {ZoneFullName}: the content of a container differs, our copy is kept (here {Local} | host {Host})",
                zone.ZoneFullName, ZoneLeaseState.TellSums(ours), ZoneLeaseState.TellSums(rejoin.MapSums!));
        }

        // still away from here to the switch: nothing of what follows is told to the host as an action of ours
        FillWorldBoxes(rejoin.Boxes);

        if (rejoin.GameDate is { } date) {
            WorldDateAdvanceDelta.SetClientDate(date);
        }

        var arrived = AdoptHostCharas(rejoin.Charas);

        // ponytail: our running task is stopped as by hand, nothing used up (lost today too, with the whole scene).
        // The host knows nothing of it and a client's progress is held by the game that keeps the map
        // (PendingOnHost). Kept when seen missing: start it again through the client's own path once switched
        if (pc.ai is { IsRunning: true } task && !pc.HasNoGoal) {
            EmpLog.Information("Soft rejoin of {ZoneFullName}: {ActType} is stopped", zone.ZoneFullName, task.GetType().Name);
            pc.Say("cancel_act_pc", pc);
            task.Stub_Cancel();
        }

        // the switch, mirror of EnterAway: from now on the host simulates this map (NetSession.Connection is the
        // host link again: only our own character ticks here, see CharaTickEvent) and its deltas are taken
        Session.IsGuest = false;
        Session.AwayZone = null;
        Session.CurrentZone = zone;
        _pendingTravel = null;
        _pendingGrant = null;
        _rejoining = false;
        _handoffDeadline = 0;
        _awaitingActivation = 0;
        _softRejoinDeadline = 0;
        _softPlaced = zone.uid;
        ReportReturn(0);

        // as the host's uid counter: a client takes it from every snapshot (WorldStateSnapshot)
        game.cards.uidNext = rejoin.UidNext;

        // nothing of this game was a host card while we were alone: every card of the map, of our bag and of the
        // boxes is one now, under the number both games have
        CardCache.Reset();
        CardCache.CacheCurrentZone();
        foreach (var chara in arrived) {
            CardCache.Add(chara);
            CardCache.CacheContainer(chara.things);
        }

        // ability tokens are no host cards: ours are told to the host as a client tells them
        foreach (var token in pc.things.Where(t => t.trait is TraitAbility).ToList()) {
            CardCache.Remove(token.uid);
        }

        CardAddThingEvent.AbilityLayoutDirty = true;

        Delta.ClearOut();
        Delta.ClearIn();
        // not compared during the switch: the first numbers of the host land with the list of players
        NetDesync.HoldOff();
        StartWorldStateUpdate();

        EmpLog.Information("Soft rejoin of {ZoneFullName}: client of the host again in place, no world copy ({Renumbered} card(s) renumbered, {Charas} character(s) taken, map {Sums}, same as the host's {SameMap})",
            zone.ZoneFullName, renumbered.Count, arrived.Count, ZoneLeaseState.TellSums(ours), sameMap);

        if (!sameMap) {
            // the map alone, loaded under our feet as NetDesync repairs one: still no copy of the world
            EmpLog.Warning("Soft rejoin of {ZoneFullName}: our copy of the map differs, asking for the map alone (here {Local} | host {Host})",
                zone.ZoneFullName, ZoneLeaseState.TellSums(ours), ZoneLeaseState.TellSums(rejoin.MapSums ?? []));

            // before the request: the host notes where we stand before it answers the map
            Host.Send(new WorldStateDeltaList {
                DeltaList = [
                    new DesyncReportDelta {
                        ZoneFullName = zone.ZoneFullName,
                        Detail = "soft rejoin, map numbers differ",
                        Resync = true,
                    },
                ],
            });
            RequestZoneState(MapDataRequest.CurrentRemoteZone);
        }

        return null;
    }

    /// <summary>
    ///     The host placed our character on the map we stayed on (ElinNetHost.OnZoneDataReceivedResponse, with the
    ///     tile our release told): our own tile, unless it could not have it there
    /// </summary>
    private void ConfirmSoftPlacement(ZoneActivateResponse response)
    {
        EmpLog.Debug("Soft rejoin of {ZoneUid}: the host holds us at {@Pos}", response.ZoneUid, response.Pos);

        if (pc.isDead || _zone?.uid != response.ZoneUid || !response.Pos.IsInActiveMapBounds ||
            (pc.pos.x == response.Pos.X && pc.pos.z == response.Pos.Z)) {
            return;
        }

        pc.Stub_Move(response.Pos, Card.MoveType.Force);
        pc.SetDir(pc.dir);
    }

    /// <summary>
    ///     The boxes of the world were emptied when we went away (EmptyWorldContainers) and only showed pictures
    ///     since (ShippingHelper.MirrorKey): they hold what the host's hold again, under the host's numbers
    /// </summary>
    private static void FillWorldBoxes(List<LZ4Bytes>? boxes)
    {
        if (boxes is null) {
            return;
        }

        ShippingHelper.FillingMirror = true;
        try {
            for (var box = 0; box < boxes.Count; box++) {
                if (ShippingHelper.WorldBox(box) is not { } container) {
                    continue;
                }

                EmptyWorldContainer(container);
                foreach (var thing in boxes[box].Decompress<List<Thing>>()) {
                    container.AddThing(thing, false);
                }
            }
        } finally {
            ShippingHelper.FillingMirror = false;
        }

        LayerInventory.SetDirtyAll();
    }

    /// <summary>
    ///     The characters of the world standing on the host's map (the host, other players, companions) replace
    ///     the copies of our last world, as ElinNetHost.ReplaceCompanions does there. Off map here: the positions
    ///     the host sends put them on it (CharaStateSnapshot.ApplyReconciliation)
    /// </summary>
    private static List<Chara> AdoptHostCharas(List<LZ4Bytes>? charas)
    {
        var adopted = new List<Chara>();
        var party = pc.party;

        foreach (var data in charas ?? []) {
            var fresh = data.Decompress<Chara>();
            // ours are the ones we play and just handed over
            if (fresh.uid == pc.uid || fresh.CompanionOwnerUid == pc.uid) {
                continue;
            }

            if (game.cards.globalCharas.Find(fresh.uid) is { } old) {
                if (_map.charas.Contains(old)) {
                    _zone.RemoveCard(old);
                }

                game.cards.globalCharas.Remove(old);

                // branches hold object references
                if (old.homeBranch is { } branch && branch.members.IndexOf(old) is var index and >= 0) {
                    branch.members[index] = fresh;
                }
            }

            fresh.currentZone = null;
            game.cards.globalCharas.Add(fresh);

            // the copy carries its own copy of the party, rebuild members from the uids
            if (party is not null) {
                var member = !fresh.isDead && fresh.party?.uidMembers.Contains(fresh.uid) is true;
                fresh.party = member ? party : null;
                if (member && !party.uidMembers.Contains(fresh.uid)) {
                    party.uidMembers.Add(fresh.uid);
                } else if (!member) {
                    party.uidMembers.Remove(fresh.uid);
                }

                if (party.uidLeader == fresh.uid) {
                    party.leader = fresh;
                }

                party.SetMembers();
            }

            adopted.Add(fresh);
        }

        return adopted;
    }
}
