using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Helper.Extensions;
using ElinTogether.Models;
using UnityEngine;

namespace ElinTogether.Net;

/// <summary>
///     Independent travel: go to a zone the host is not in, simulate it locally, hand it back when leaving <br />
///     A zone another player simulates is joined as a guest of its zone session, see NetSession.ZoneSession
/// </summary>
internal partial class ElinNetClient
{
    private (Zone Zone, ZoneTransition Transition)? _pendingTravel;

    /// <summary>
    ///     Lease granted while on the host map (or as a guest), waiting for <see cref="ZoneLeaseDepart" />
    /// </summary>
    private ZoneLeaseGrant? _pendingGrant;

    /// <summary>
    ///     Zones this client created itself (world map fields, dungeon floors...), unknown to the host until leased
    /// </summary>
    private readonly HashSet<Zone> _localZones = [];

    private float _nextCheckpoint;

    /// <summary>
    ///     Zone of the host while away, kept up to date from its zone changes
    /// </summary>
    private int _hostZoneUid = -1;

    internal void OnLocalZoneCreated(Zone zone)
    {
        _localZones.Add(zone);
    }

    /// <summary>
    ///     Away zone handed back, waiting for the host save probe
    /// </summary>
    private bool _rejoining;

    /// <summary>
    ///     Guest whose zone owner left: how long we wait for the host to hand the zone over before going back
    /// </summary>
    private const float HandoffWaitSeconds = 30f;

    private float _handoffDeadline;

    /// <summary>
    ///     Zone the host moved to while we were leaving its map to stay behind, see StayAsGuest
    /// </summary>
    private int? _hostZoneAfterDeparture;

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

        // a guest leaves the zone session first, its owner applies our last actions, see OnGuestLeftZone
        if (Session.IsGuest && Session.ZoneSession is ElinNetClient zoneClient) {
            _pendingTravel = (zone, transition);
            zoneClient.LeaveZoneSession(Session.AwayZone!.uid);
            EmpPop.Debug("emp_travel_requesting".lang());
            return false;
        }

        if (Session.IsAway && zone.uid == _hostZoneUid) {
            EmpLog.Information("Returning from {AwayZone} to host zone {ZoneFullName}",
                Session.AwayZone!.ZoneFullName, zone.ZoneFullName);

            SendRejoin();
            EmpPop.Debug("emp_travel_returning".lang());
            return false;
        }

        RequestLease(zone, transition);
        return false;
    }

    private void RequestLease(Zone zone, ZoneTransition transition)
    {
        EmpLog.Information("Requesting zone lease {ZoneFullName}",
            zone.ZoneFullName);

        _pendingTravel = (zone, transition);
        Host.Send(ZoneLeaseRequest.Create(zone, _localZones.Contains(zone)));
        EmpPop.Debug("emp_travel_requesting".lang());
    }

    /// <summary>
    ///     Net event: Travel accepted, this client simulates the zone from now on (or joins its owner)
    /// </summary>
    private void OnZoneLeaseGrant(ZoneLeaseGrant grant)
    {
        if (grant.Handoff) {
            TakeOverZone(grant);
            return;
        }

        if (_pendingTravel is not { } travel || travel.Zone.uid != grant.RequestedUid) {
            EmpLog.Warning("Received unexpected lease for zone {ZoneUid}", grant.RequestedUid);
            return;
        }

        AdoptHostUid(travel.Zone, grant.ZoneUid);

        if (grant.Guest) {
            // leave where we are (handing our zone back if we hold one), then the owner of the zone
            // expects us, see ZoneLeaseDepart
            if (Session.IsZoneAuthority) {
                HandBackAwayZone(false);
            } else if (!Session.IsAway) {
                FlushDeltasNow();
            }

            Host.Send(new ZoneLeaseAck {
                ZoneUid = grant.ZoneUid,
            });
            _pendingGrant = grant;
            StopWorldStateUpdate();
            return;
        }

        if (Session.IsAway) {
            _pendingTravel = null;

            // hand back the zone we are leaving, while it is still active (a guest that left holds none)
            if (Session.IsZoneAuthority) {
                HandBackAwayZone(false);
            }

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
        StopWorldStateUpdate();
    }

    /// <summary>
    ///     Acknowledged a departure: the host already took us off its map and its player list,
    ///     only the results of our last actions still matter until ZoneLeaseDepart
    /// </summary>
    private bool IsAwaitingDeparture => _pendingGrant is not null && !Session.IsAway;

    /// <summary>
    ///     Net event: The host applied our last actions on its map and sent their results, now we go
    /// </summary>
    private void OnZoneLeaseDepart(ZoneLeaseDepart depart)
    {
        // the zone we visit changed hands, its new owner expects us, see HandOverZone
        if (_pendingTravel is null && _pendingGrant is null && depart.Guest is { } moved &&
            Session.IsGuest && Session.AwayZone is { } here && here.uid == depart.ZoneUid) {
            _handoffDeadline = 0;
            JoinZoneSession(here, moved);
            return;
        }

        if (_pendingTravel is not { } travel || _pendingGrant is not { } grant || grant.ZoneUid != depart.ZoneUid) {
            EmpLog.Warning("Received unexpected departure for zone {ZoneUid}", depart.ZoneUid);
            return;
        }

        _pendingTravel = null;
        _pendingGrant = null;

        // the results arrived right before this packet, apply them while still synced
        WorldStateDeltaProcess();

        if (depart.Guest is { } address) {
            JoinZoneSession(travel.Zone, address);
            return;
        }

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
        AdoptQuestUidRange(grant);

        EnterAway(zone);
        Session.IsGuest = false;

        EmpLog.Information("Leased zone {ZoneFullName}, uid range from {UidRangeStart}, map {HasMap}",
            zone.ZoneFullName, grant.UidRangeStart, grant.Map is not null);

        pc.MoveZone(zone, transition);
    }

    /// <summary>
    ///     Quests created here (residents of the zone we simulate) get uids the host does not use
    /// </summary>
    private static void AdoptQuestUidRange(ZoneLeaseGrant grant)
    {
        if (grant.QuestUidRangeStart > 0) {
            game.quests.uid = Math.Max(game.quests.uid, grant.QuestUidRangeStart);
        }
    }

    /// <summary>
    ///     Another player simulates the zone: connect to its zone session, it sends its world and the zone
    /// </summary>
    private void JoinZoneSession(Zone zone, ZoneGuestAddress address)
    {
        EnterAway(zone);
        Session.IsGuest = true;

        EmpLog.Information("Joining the zone session of {RemoteIdentity} in {ZoneFullName}",
            address.HostUser, zone.ZoneFullName);

        var session = Session.InitializeZoneSession<ElinNetClient>();
        if (IsLocalConnection) {
            session.ConnectLocalPort((ushort)address.Port);
        } else {
            session.ConnectSteamUser(address.HostUser);
        }
    }

    /// <summary>
    ///     Zone session client: leaving the zone, send our last actions and wait for their results
    /// </summary>
    internal void LeaveZoneSession(int zoneUid)
    {
        FlushDeltasNow();
        Host.Send(new ZoneGuestLeave {
            ZoneUid = zoneUid,
        });
    }

    /// <summary>
    ///     Zone session client, net event: the owner applied our last actions, we may go
    /// </summary>
    private void OnZoneGuestLeft(ZoneGuestLeft left)
    {
        if (!IsZoneSession) {
            return;
        }

        WorldStateDeltaProcess();
        (Session.Transport as ElinNetClient)?.OnGuestLeftZone();
    }

    /// <summary>
    ///     Out of the zone session, go on with the travel that started it
    /// </summary>
    internal void OnGuestLeftZone()
    {
        Session.RemoveZoneSession();

        if (_pendingTravel is not { } travel) {
            return;
        }

        if (travel.Zone.uid == _hostZoneUid) {
            _pendingTravel = null;
            SendRejoin();
            return;
        }

        RequestLease(travel.Zone, travel.Transition);
    }

    /// <summary>
    ///     The zone session ended on its own: the zone owner left or dropped, back to the host
    /// </summary>
    internal void OnZoneSessionEnded(ElinNetBase session, string reason)
    {
        if (session is not ElinNetClient || !Session.IsGuest) {
            return;
        }

        // meanwhile we play on alone: the host gives the zone to one of us (or calls us back),
        // see TakeOverZone, and only if it stays silent we go back
        EmpLog.Warning("Zone session ended ({Reason}), waiting for the host to hand the zone over",
            reason);

        _pendingTravel = null;
        _handoffDeadline = Time.realtimeSinceStartup + HandoffWaitSeconds;
    }

    private void UpdateHandoffWait()
    {
        if (_handoffDeadline <= 0 || Time.realtimeSinceStartup < _handoffDeadline) {
            return;
        }

        _handoffDeadline = 0;

        if (!Session.IsGuest || Session.ZoneSession is not null || _rejoining) {
            return;
        }

        EmpLog.Warning("Nobody took the zone over, returning to the host");
        EmpPop.Information("emp_travel_zone_closed".lang());
        SendRejoin();
    }

    /// <summary>
    ///     Net event: the owner of the zone we visit left it, we simulate it from now on, as it is here
    /// </summary>
    private void TakeOverZone(ZoneLeaseGrant grant)
    {
        // either we visit the zone of a player who left it, or we stand on the host map and the host leaves it
        var visiting = Session.IsGuest && Session.AwayZone is { } away && away.uid == grant.ZoneUid && _zone == away;
        var withHost = !Session.IsAway && _zone?.uid == grant.ZoneUid;

        if (withHost && grant.Guest) {
            StayAsGuest(grant);
            return;
        }

        if ((!visiting && !withHost) || _rejoining) {
            // gone meanwhile, the host drops that lease when we rejoin
            EmpLog.Warning("Handed zone {ZoneUid} while not in it", grant.ZoneUid);
            return;
        }

        if (_zone is not { } zone) {
            return;
        }

        // everyone else leaves this copy of the map: the players (with the host), their companions,
        // those staying join us again with theirs. Listed while the party and the player list still stand
        var players = Session.CurrentPlayers.Where(p => p is not null).Select(p => p.CharaUid).ToHashSet();
        var leaving = _map.charas
            .Where(c => c != pc && (players.Contains(c.uid) || c.GetBool("remote_chara") ||
                                    (c.party is not null && c.party == pc.party && !c.IsCompanionOf(pc)) ||
                                    (c.CompanionOwnerUid != 0 && c.CompanionOwnerUid != pc.uid)))
            .ToList();

        if (withHost) {
            // the results of our last actions on the host map arrived right before this packet
            WorldStateDeltaProcess();
            EnterAway(zone);
        } else {
            // still open if the owner has not closed it yet
            Session.RemoveZoneSession();
        }

        Session.IsGuest = false;
        _pendingTravel = null;
        _handoffDeadline = 0;
        _nextCheckpoint = Time.realtimeSinceStartup + Session.Rules.TravelCheckpointSeconds;

        // cards created here get uids the host does not use, those still waiting for one from the owner too
        game.cards.uidNext = Math.Max(game.cards.uidNext, grant.UidRangeStart);
        AdoptQuestUidRange(grant);
        foreach (var card in _map.things.Concat<Card>(_map.charas).ToList()) {
            if (PendingUid.IsPending(card.uid)) {
                game.cards.AssignUID(card);
            }

            foreach (var thing in card.things.Flatten()) {
                if (PendingUid.IsPending(thing.uid)) {
                    game.cards.AssignUID(thing);
                }
            }
        }

        foreach (var chara in leaving) {
            if (chara.party is { } party && party.members.Contains(chara)) {
                party.RemoveMember(chara);
            }

            if (chara.parent is Zone) {
                zone.RemoveCard(chara);
            }
        }

        EmpLog.Information("Took over zone {ZoneFullName}, uid range from {UidRangeStart}, from the host {WithHost}",
            zone.ZoneFullName, grant.UidRangeStart, withHost);
        EmpPop.Information("emp_travel_handoff".lang());
    }

    /// <summary>
    ///     The host leaves the map we stand on and another player takes it over: we stay, as its guest.
    ///     Same path as asking to join a zone someone simulates, see OnZoneLeaseDepart
    /// </summary>
    private void StayAsGuest(ZoneLeaseGrant grant)
    {
        if (_pendingTravel is not null || _rejoining) {
            return;
        }

        WorldStateDeltaProcess();

        _pendingTravel = (_zone, new ZoneTransition());
        _pendingGrant = grant;
        StopWorldStateUpdate();

        Host.Send(new ZoneLeaseAck {
            ZoneUid = grant.ZoneUid,
        });
    }

    /// <summary>
    ///     Net event: another player joins the zone we simulate, host it in a zone session
    /// </summary>
    private void OnZoneGuestRequest(ZoneGuestRequest request)
    {
        var accepted = Session.IsZoneAuthority && Session.AwayZone?.uid == request.ZoneUid &&
                       _zone == Session.AwayZone && _pendingTravel is null && !_rejoining;

        if (accepted) {
            var zoneHost = Session.ZoneSession as ElinNetHost ?? StartZoneSession();
            zoneHost.RegisterGuest(request.GuestUser, request.Chara, request.Companions);
        }

        EmpLog.Information("Guest {RemoteIdentity} for zone {ZoneUid}: {Accepted}",
            request.GuestUser, request.ZoneUid, accepted);

        Host.Send(new ZoneGuestReady {
            ZoneUid = request.ZoneUid,
            GuestUser = request.GuestUser,
            Accepted = accepted,
            Port = ElinNetHost.ZoneSessionPort,
        });
    }

    private ElinNetHost StartZoneSession()
    {
        var zoneHost = Session.InitializeZoneSession<ElinNetHost>();
        zoneHost.StartZoneServer(IsLocalConnection);
        return zoneHost;
    }

    /// <summary>
    ///     Net event: Travel refused, stay where we are
    /// </summary>
    private void OnZoneLeaseDenied(ZoneLeaseDenied denied)
    {
        EmpLog.Information("Zone lease {ZoneUid} denied: {Reason}",
            denied.ZoneUid, denied.Reason);

        // the host stands there (we had not heard yet that it moved): going there is rejoining it
        if (denied.Reason == "emp_travel_host_zone" && Session.IsAway && _pendingGrant is null && !_rejoining) {
            _pendingTravel = null;
            _hostZoneUid = denied.ZoneUid;
            SendRejoin();
            EmpPop.Debug("emp_travel_returning".lang());
            return;
        }

        _pendingTravel = null;
        EmpPop.Information(denied.Reason.lang());

        // refused after leaving our place to join another player: back to the host
        if (_pendingGrant is not null) {
            _pendingGrant = null;
            SendRejoin();
        }
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
        _hostZoneUid = zoneUid;

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
        HandBackAwayZone(true);
    }

    /// <summary>
    ///     Leaving the zone: hand it back (our guests stay, the host gives it to one of them, see HandOverZone)
    /// </summary>
    private void HandBackAwayZone(bool rejoin)
    {
        Host.Send(CreateLeaseRelease(rejoin));

        if (Session.ZoneSession is ElinNetHost) {
            Session.RemoveZoneSession();
        }
    }

    private void EnterAway(Zone zone)
    {
        var wasAway = Session.IsAway;

        // from now on the game runs as single player, see NetSession.Connection
        Session.AwayZone = zone;

        if (wasAway) {
            return;
        }

        // the host may already have told us where it went (it left the map we stay on)
        _hostZoneUid = _hostZoneAfterDeparture ?? Session.CurrentZone?.uid ?? -1;
        _hostZoneAfterDeparture = null;
        _nextCheckpoint = Time.realtimeSinceStartup + Session.Rules.TravelCheckpointSeconds;
        StopWorldStateUpdate();
        Delta.ClearOut();
        Delta.ClearIn();
        EmptyWorldContainers();

        // other players stay with the host (party lists may hold empty slots)
        foreach (var member in pc.party?.members.ToList() ?? []) {
            if (member is not null && member != pc && Session.CurrentPlayers.Any(p => p?.CharaUid == member.uid)) {
                pc.party!.RemoveMember(member);
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
        if (!Session.IsZoneAuthority || Session.AwayZone is not { } zone) {
            // a guest (or a player refused on its way) holds no zone, it only brings its character
            return new() {
                ZoneUid = -1,
                ZoneState = [],
                Chara = LZ4Bytes.Create(pc),
                Companions = CollectCompanions(),
                UidNext = game.cards.uidNext,
                Rejoin = rejoin,
                Checkpoint = checkpoint,
            };
        }

        return new() {
            ZoneUid = zone.uid,
            ZoneState = ZoneLeaseState.GetState(zone),
            IdCurrentSubset = zone.idCurrentSubset,
            // the world map is a local copy for everyone
            Map = zone.IsRegion ? null : ZoneLeaseState.CollectMap(zone),
            Chara = LZ4Bytes.Create(pc),
            Companions = CollectCompanions(),
            UidNext = game.cards.uidNext,
            Rejoin = rejoin,
            Checkpoint = checkpoint,
            GuestCharas = (Session.ZoneSession as ElinNetHost)?.CollectGuestCharas(),
            GuestCompanions = (Session.ZoneSession as ElinNetHost)?.CollectGuestCompanions(),
        };
    }

    private static List<LZ4Bytes> CollectCompanions()
    {
        return CompanionHelper.TravellingWith(pc).Select(c => LZ4Bytes.Create(c)).ToList();
    }

    internal void SendChatWhileAway(MsgSayDelta delta)
    {
        SendWhileAway(delta);
    }

    /// <summary>
    ///     What an away player still shares with the world: chat, the quest log
    /// </summary>
    internal void SendWhileAway(ElinDelta delta)
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
            // chat and the quest log are the world's, the rest is about the host map
            if (delta is MsgSayDelta or QuestStartDelta or QuestCompleteDelta or QuestChangePhaseDelta or DialogFlagDelta or QuestFailDelta or QuestUpdateDelta or PersonalStateDelta or PlayerStandingDelta) {
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
        if (!Session.IsZoneAuthority || interval <= 0 || _pendingTravel is not null || _rejoining ||
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
            ZoneGuestRequest or
            ShippingPayout or
            ZoneDataResponse or
            SaveDataProbe or
            NetSessionRules or
            NetIntegrityRejected;
        // not SessionPlayersSnapshot: the players of a zone session are ours, the host list is about its map
    }
}
