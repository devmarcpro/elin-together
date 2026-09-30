using System;
using System.Linq;
using ElinTogether.Models;

namespace ElinTogether.Net;

/// <summary>
///     Independent travel: go to a zone the host is not in, simulate it locally, hand it back when leaving
/// </summary>
internal partial class ElinNetClient
{
    private (Zone Zone, ZoneTransition Transition)? _pendingTravel;

    /// <summary>
    ///     The local player moves to a zone other than the one it replicates from the host <br />
    ///     Returns true to let the move happen now
    /// </summary>
    internal bool TryTravel(Zone zone, ZoneTransition transition)
    {
        // moving into the zone just granted
        if (Session.AwayZone == zone) {
            return true;
        }

        if (!Session.Rules.AllowIndependentTravel) {
            EmpPop.Debug("emp_party_gather".lang());
            return false;
        }

        if (_pendingTravel is not null) {
            // a request is in flight
            return false;
        }

        if (Session.IsAway && zone == Session.CurrentZone) {
            EmpLog.Information("Returning from {AwayZone} to host zone {ZoneFullName}",
                Session.AwayZone!.ZoneFullName, zone.ZoneFullName);

            // the host answers with a save probe, which rebuilds the game in the host zone
            Host.Send(CreateLeaseRelease(true));
            EmpPop.Debug("emp_travel_returning".lang());
            return false;
        }

        EmpLog.Information("Requesting zone lease {ZoneFullName}",
            zone.ZoneFullName);

        _pendingTravel = (zone, transition);
        Host.Send(ZoneLeaseRequest.Create(zone));
        EmpPop.Debug("emp_travel_requesting".lang());
        return false;
    }

    /// <summary>
    ///     Net event: Travel accepted, this client simulates the zone from now on
    /// </summary>
    private void OnZoneLeaseGrant(ZoneLeaseGrant grant)
    {
        if (_pendingTravel is not { } travel || travel.Zone.uid != grant.ZoneUid) {
            EmpLog.Warning("Received unexpected lease for zone {ZoneUid}", grant.ZoneUid);
            return;
        }

        _pendingTravel = null;
        var (zone, transition) = travel;

        // hand back the zone we are leaving, while it is still active
        if (Session.IsAway) {
            Host.Send(CreateLeaseRelease(false));
        }

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

    private void EnterAway(Zone zone)
    {
        var wasAway = Session.IsAway;

        // from now on the game runs as single player, see NetSession.Connection
        Session.AwayZone = zone;

        if (wasAway) {
            return;
        }

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

    private ZoneLeaseRelease CreateLeaseRelease(bool rejoin)
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
        };
    }

    /// <summary>
    ///     Only lease traffic and session control reach an away client, the rest is about the host map
    /// </summary>
    private static bool ShouldReceiveWhileAway(object packet)
    {
        return packet is ZoneLeaseGrant or
            ZoneLeaseDenied or
            ZoneDataResponse or
            SaveDataProbe or
            SessionPlayersSnapshot or
            NetSessionRules or
            NetIntegrityRejected;
    }
}
