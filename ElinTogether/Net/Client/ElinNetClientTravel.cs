using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Models;
using UnityEngine;

namespace ElinTogether.Net;

/// <summary>
///     Independent travel: go to a zone the host is not in, simulate it locally, hand it back when leaving
/// </summary>
internal partial class ElinNetClient
{
    private (Zone Zone, ZoneTransition Transition)? _pendingTravel;

    /// <summary>
    ///     Lease granted while on the host map, waiting for <see cref="ZoneLeaseDepart" />
    /// </summary>
    private ZoneLeaseGrant? _pendingGrant;

    /// <summary>
    ///     Zones this client created itself (world map fields, dungeon floors...), unknown to the host until leased
    /// </summary>
    private readonly HashSet<Zone> _localZones = [];

    private float _nextCheckpoint;

    internal void OnLocalZoneCreated(Zone zone)
    {
        _localZones.Add(zone);
    }

    /// <summary>
    ///     Away zone handed back, waiting for the host save probe
    /// </summary>
    private bool _rejoining;

    /// <summary>
    ///     The local player moves to a zone other than the one it replicates from the host <br />
    ///     Returns true to let the move happen now
    /// </summary>
    internal bool TryTravel(Zone zone, ZoneTransition transition)
    {
        // moving into the zone just granted
        if (Session.AwayZone == zone && !_rejoining) {
            return true;
        }

        if (!Session.IsAway && (pc.isDead || player.deathZoneMove)) {
            // the host revives remote players where they fell, see CharaReviveEvent
            return false;
        }

        // leaving an instance, Elin sends the player back where it started, see Chara.MoveZone
        if (pc.currentZone?.instance is { } instance) {
            zone = game.spatials.Find(instance.uidZone) ?? pc.homeZone;
        }

        if (!Session.Rules.AllowIndependentTravel) {
            EmpPop.Debug("emp_party_gather".lang());
            return false;
        }

        if (_pendingTravel is not null || _rejoining) {
            // a request is in flight
            return false;
        }

        if (Session.IsAway && zone == Session.CurrentZone) {
            EmpLog.Information("Returning from {AwayZone} to host zone {ZoneFullName}",
                Session.AwayZone!.ZoneFullName, zone.ZoneFullName);

            SendRejoin();
            EmpPop.Debug("emp_travel_returning".lang());
            return false;
        }

        EmpLog.Information("Requesting zone lease {ZoneFullName}",
            zone.ZoneFullName);

        _pendingTravel = (zone, transition);
        Host.Send(ZoneLeaseRequest.Create(zone, _localZones.Contains(zone)));
        EmpPop.Debug("emp_travel_requesting".lang());
        return false;
    }

    /// <summary>
    ///     Net event: Travel accepted, this client simulates the zone from now on
    /// </summary>
    private void OnZoneLeaseGrant(ZoneLeaseGrant grant)
    {
        if (_pendingTravel is not { } travel || travel.Zone.uid != grant.RequestedUid) {
            EmpLog.Warning("Received unexpected lease for zone {ZoneUid}", grant.RequestedUid);
            return;
        }

        AdoptHostUid(travel.Zone, grant.ZoneUid);

        if (Session.IsAway) {
            _pendingTravel = null;

            // hand back the zone we are leaving, while it is still active
            Host.Send(CreateLeaseRelease(false));
            TravelTo(travel.Zone, travel.Transition, grant);
            return;
        }

        // leaving the host map: everything done there reaches the host first, then we wait for
        // the results of those actions before going, see ZoneLeaseDepart
        FlushDeltasNow();
        Host.Send(new ZoneLeaseAck {
            ZoneUid = grant.ZoneUid,
        });
        _pendingGrant = grant;
    }

    /// <summary>
    ///     Net event: The host applied our last actions on its map and sent their results, now we go
    /// </summary>
    private void OnZoneLeaseDepart(ZoneLeaseDepart depart)
    {
        if (_pendingTravel is not { } travel || _pendingGrant is not { } grant || grant.ZoneUid != depart.ZoneUid) {
            EmpLog.Warning("Received unexpected departure for zone {ZoneUid}", depart.ZoneUid);
            return;
        }

        _pendingTravel = null;
        _pendingGrant = null;

        // the results arrived right before this packet, apply them while still synced
        WorldStateDeltaProcess();

        TravelTo(travel.Zone, travel.Transition, grant);
    }

    /// <summary>
    ///     A zone created here gets the uid the host assigned, nothing refers to it by uid yet
    /// </summary>
    private void AdoptHostUid(Zone zone, int uid)
    {
        _localZones.Remove(zone);

        if (zone.uid == uid) {
            return;
        }

        var spatials = game.spatials;
        spatials.uidNext = Math.Max(spatials.uidNext, uid + 1);

        if (spatials.map.TryGetValue(uid, out var other) && other != zone) {
            spatials.map.Remove(uid);

            if (other.id == zone.id && other.x == zone.x && other.y == zone.y) {
                // host copy announced through SpatialGenDelta before the grant
                other.parent?.RemoveChild(other);
            } else {
                // another zone created here took that uid
                spatials.AssignUID(other);
            }
        }

        EmpLog.Debug("Zone {ZoneFullName} created locally as {LocalUid}, host uid {ZoneUid}",
            zone.ZoneFullName, zone.uid, uid);

        spatials.map.Remove(zone.uid);
        zone.uid = uid;
        spatials.map[uid] = zone;

        if (zone.parent is Region region) {
            region.elomap.SetZone(zone.x, zone.y, zone, true);
        }
    }

    private void TravelTo(Zone zone, ZoneTransition transition, ZoneLeaseGrant grant)
    {
        if (grant.Map is not null) {
            if (zone.map is not null) {
                // stale copy from an earlier visit alongside the host
                zone.UnloadMap();
            }

            ZoneLeaseState.WriteMap(zone, grant.Map);
        }

        ZoneLeaseState.ApplyState(zone, grant.ZoneState, grant.IdCurrentSubset);

        // cards created here get uids the host does not use
        game.cards.uidNext = Math.Max(game.cards.uidNext, grant.UidRangeStart);

        EnterAway(zone);

        EmpLog.Information("Leased zone {ZoneFullName}, uid range from {UidRangeStart}, map {HasMap}",
            zone.ZoneFullName, grant.UidRangeStart, grant.Map is not null);

        pc.MoveZone(zone, transition);
    }

    /// <summary>
    ///     Net event: Travel refused, stay where we are
    /// </summary>
    private void OnZoneLeaseDenied(ZoneLeaseDenied denied)
    {
        EmpLog.Information("Zone lease {ZoneUid} denied: {Reason}",
            denied.ZoneUid, denied.Reason);

        _pendingTravel = null;
        EmpPop.Information(denied.Reason.lang());
    }

    /// <summary>
    ///     Net event: The host wants to enter our zone, hand it back and rejoin the host
    /// </summary>
    private void OnZoneLeaseRecall(ZoneLeaseRecall recall)
    {
        if (Session.AwayZone?.uid != recall.ZoneUid) {
            // already handed back
            return;
        }

        if (_pendingTravel is not null) {
            // leaving already, the zone is released as soon as the next one is granted
            return;
        }

        EmpLog.Information("Host recalls zone {ZoneFullName}, rejoining",
            Session.AwayZone.ZoneFullName);

        SendRejoin();
        EmpPop.Information("emp_travel_recalled".lang());
    }

    /// <summary>
    ///     Host zone change while away, rejoin if the host arrived in our zone anyway
    /// </summary>
    private void OnHostZoneChangedWhileAway(int zoneUid)
    {
        if (Session.AwayZone?.uid != zoneUid || _pendingTravel is not null) {
            return;
        }

        EmpLog.Warning("Host entered away zone {ZoneFullName} without recall, rejoining",
            Session.AwayZone.ZoneFullName);

        SendRejoin();
    }

    /// <summary>
    ///     Hand the away zone back and return to the host <br />
    ///     The host answers with a save probe, which rebuilds the game in the host zone
    /// </summary>
    private void SendRejoin()
    {
        if (_rejoining) {
            return;
        }

        _rejoining = true;
        Host.Send(CreateLeaseRelease(true));
    }

    private void EnterAway(Zone zone)
    {
        var wasAway = Session.IsAway;

        // from now on the game runs as single player, see NetSession.Connection
        Session.AwayZone = zone;

        if (wasAway) {
            return;
        }

        _nextCheckpoint = Time.realtimeSinceStartup + Session.Rules.TravelCheckpointSeconds;
        StopWorldStateUpdate();
        Delta.ClearOut();
        Delta.ClearIn();

        // other players stay with the host
        foreach (var member in pc.party.members.ToList()) {
            if (member != pc && Session.CurrentPlayers.Any(p => p.CharaUid == member.uid)) {
                pc.party.RemoveMember(member);
            }
        }
    }

    private void FlushDeltasNow()
    {
        Delta.RefreshBuffer();

        // second pass sends what was deferred by the first
        for (var i = 0; i < 3 && Delta.HasPendingOut; i++) {
            if (Delta.FlushOutBuffer() is { Count: > 0 } deltaList) {
                Host.Send(new WorldStateDeltaList {
                    DeltaList = deltaList,
                });
            }
        }
    }

    private ZoneLeaseRelease CreateLeaseRelease(bool rejoin, bool checkpoint = false)
    {
        var zone = Session.AwayZone!;

        return new() {
            ZoneUid = zone.uid,
            ZoneState = ZoneLeaseState.GetState(zone),
            IdCurrentSubset = zone.idCurrentSubset,
            // the world map is a local copy for everyone
            Map = zone.IsRegion ? null : ZoneLeaseState.CollectMap(zone),
            Chara = LZ4Bytes.Create(pc),
            UidNext = game.cards.uidNext,
            Rejoin = rejoin,
            Checkpoint = checkpoint,
        };
    }

    internal void SendChatWhileAway(MsgSayDelta delta)
    {
        Host.Send(new WorldStateDeltaList {
            DeltaList = [delta],
        });
    }

    /// <summary>
    ///     Delta lists reaching an away client are about the host map, except chat
    /// </summary>
    private void ApplyChatWhileAway(WorldStateDeltaList response)
    {
        foreach (var delta in response.DeltaList) {
            if (delta is MsgSayDelta) {
                // the regular delta loop does not run while away, see CoreSynchronizationContext
                delta.Apply(this);
            }
        }
    }

    /// <summary>
    ///     Regular progress save while away, so a disconnect only loses what happened since
    /// </summary>
    private void UpdateTravelCheckpoint()
    {
        var interval = Session.Rules.TravelCheckpointSeconds;
        if (!Session.IsAway || interval <= 0 || _pendingTravel is not null || _rejoining ||
            !core.IsGameStarted || _zone != Session.AwayZone) {
            return;
        }

        if (Time.realtimeSinceStartup < _nextCheckpoint) {
            return;
        }

        _nextCheckpoint = Time.realtimeSinceStartup + interval;
        SendTravelCheckpoint();
    }

    internal void SendTravelCheckpoint()
    {
        Host.Send(CreateLeaseRelease(false, true));
        EmpLog.Debug("Sent checkpoint of zone {ZoneFullName}", Session.AwayZone!.ZoneFullName);
    }

    /// <summary>
    ///     Only lease traffic and session control reach an away client, the rest is about the host map
    /// </summary>
    private static bool ShouldReceiveWhileAway(object packet)
    {
        return packet is ZoneLeaseGrant or
            WorldStateDeltaList or
            ZoneLeaseDepart or
            ZoneLeaseDenied or
            ZoneLeaseRecall or
            ZoneDataResponse or
            SaveDataProbe or
            SessionPlayersSnapshot or
            NetSessionRules or
            NetIntegrityRejected;
    }
}
