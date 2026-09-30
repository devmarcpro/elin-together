using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Models;
using ElinTogether.Net.Steam;

namespace ElinTogether.Net;

/// <summary>
///     Independent travel: a client leases a zone the host is not in, simulates it on its own,
///     and hands it back when leaving
/// </summary>
internal partial class ElinNetHost
{
    /// <summary>
    ///     Card uids reserved per lease, the client allocates above the host
    /// </summary>
    private const int LeaseUidReserve = 1_000_000;

    /// <summary>
    ///     Peer id -> leased zone uids <br />
    ///     Two while moving between zones: the next one is granted before the previous one is handed back
    /// </summary>
    private readonly Dictionary<int, HashSet<int>> _leases = [];

    private int _leaseUidCeiling;

    internal bool IsAway(ISteamNetPeer peer)
    {
        return _leases.TryGetValue(peer.Id, out var zones) && zones.Count > 0;
    }

    /// <summary>
    ///     Net event: Client wants to travel to a zone the host is not in
    /// </summary>
    private void OnZoneLeaseRequest(ZoneLeaseRequest request, ISteamNetPeer peer)
    {
        var zone = game.spatials.Find(request.ZoneUid);

        if (GetLeaseDenyReason(zone, request, peer) is { } reason) {
            EmpLog.Information("Denied zone lease {ZoneFullName} to {@Peer}: {Reason}",
                request.ZoneFullName, peer, reason);

            peer.Send(new ZoneLeaseDenied {
                ZoneUid = request.ZoneUid,
                Reason = reason,
            });
            return;
        }

        // the player leaves the host map but stays connected
        DepartRemotePlayer(peer);

        var rangeStart = Math.Max(game.cards.uidNext, _leaseUidCeiling) + LeaseUidReserve;
        _leaseUidCeiling = rangeStart;

        if (!_leases.TryGetValue(peer.Id, out var zones)) {
            zones = _leases[peer.Id] = [];
        }

        zones.Add(zone!.uid);

        var map = zone.IsRegion || !zone.isGenerated
            ? null
            : ZoneLeaseState.CollectMap(zone);

        EmpLog.Information("Leased zone {ZoneFullName} to {@Peer}, uid range from {UidRangeStart}, map {HasMap}",
            zone.ZoneFullName, peer, rangeStart, map is not null);

        peer.Send(new ZoneLeaseGrant {
            ZoneUid = zone.uid,
            UidRangeStart = rangeStart,
            ZoneState = ZoneLeaseState.GetState(zone),
            IdCurrentSubset = zone.idCurrentSubset,
            Map = map,
        });
    }

    /// <summary>
    ///     Net event: Client hands a leased zone back
    /// </summary>
    private void OnZoneLeaseRelease(ZoneLeaseRelease release, ISteamNetPeer peer)
    {
        if (_leases.TryGetValue(peer.Id, out var zones) && zones.Remove(release.ZoneUid)) {
            if (game.spatials.Find(release.ZoneUid) is { IsRegion: false } zone) {
                ApplyLeasedZone(zone, release);
            }
        } else {
            EmpLog.Warning("Player {@Peer} released zone {ZoneUid} without holding its lease, ignoring the zone",
                peer, release.ZoneUid);
        }

        game.cards.uidNext = Math.Max(game.cards.uidNext, release.UidNext);

        var chara = ReplaceRemoteChara(peer, release.Chara);

        if (!release.Rejoin) {
            return;
        }

        if (zones is { Count: > 0 }) {
            EmpLog.Warning("Player {@Peer} rejoins while still holding zones {ZoneUids}, dropping them",
                peer, zones);
            zones.Clear();
        }

        if (chara is not null) {
            EmpLog.Information("Player {@Peer} returns to the host zone",
                peer);

            SendSaveProbe(chara, peer);
        }
    }

    /// <summary>
    ///     Like a disconnect, without closing the connection
    /// </summary>
    private void DepartRemotePlayer(ISteamNetPeer peer)
    {
        PendingRebind.ReleasePeer(peer.Id);

        if (!States.Remove(peer.Id, out var state)) {
            // already away, moving between leased zones
            return;
        }

        if (ActiveRemoteCharas.Remove(peer.Id, out var remoteChara)) {
            RemoveRemoteChara(remoteChara);
        }

        Session.CurrentPlayers.Remove(state);

        Broadcast(SessionPlayersSnapshot.Create());
    }

    private void ApplyLeasedZone(Zone zone, ZoneLeaseRelease release)
    {
        if (zone == _zone) {
            // host walked in meanwhile and simulates it, host copy wins
            EmpLog.Warning("Zone {ZoneFullName} is active on host, discarding the client copy",
                zone.ZoneFullName);
            return;
        }

        if (release.Map is not null) {
            if (zone.map is not null) {
                // drop the stale in-memory copy, next activation loads the files
                zone.UnloadMap();
            }

            ZoneLeaseState.WriteMap(zone, release.Map);
        }

        ZoneLeaseState.ApplyState(zone, release.ZoneState, release.IdCurrentSubset);

        // the client just left, no catch-up simulation owed
        zone.lastActive = world.date.GetRaw();

        EmpLog.Information("Applied client copy of zone {ZoneFullName}, map {HasMap}, generated {IsGenerated}",
            zone.ZoneFullName, release.Map is not null, zone.isGenerated);
    }

    /// <summary>
    ///     Swap the host copy of the player character for the one simulated by the client
    /// </summary>
    private Chara? ReplaceRemoteChara(ISteamNetPeer peer, LZ4Bytes data)
    {
        if (!SavedRemoteCharas.TryGetValue(peer.User, out var uid)) {
            EmpLog.Warning("Player {@Peer} has no saved remote chara", peer);
            return null;
        }

        var old = game.cards.globalCharas.Find(uid);
        var uploaded = data.Decompress<Chara>();

        if (uploaded.uid != uid) {
            EmpLog.Warning("Player {@Peer} uploaded chara {UploadedUid}, expected {Uid}, keeping host copy",
                peer, uploaded.uid, uid);
            return old;
        }

        if (old is not null) {
            ForgetCachedCard(old);
            game.cards.globalCharas.Remove(old);
        }

        uploaded.SetBool(CINT.IsPC, false);
        // not in any host map until it rejoins, the zone it left must not pull it back in
        uploaded.currentZone = null;
        game.cards.globalCharas.Add(uploaded);

        EmpLog.Debug("Replaced remote chara {Uid} of player {@Peer}",
            uid, peer);

        return uploaded;
    }

    private static void ForgetCachedCard(Card card)
    {
        CardCache.Remove(card.uid);

        foreach (var thing in card.things) {
            ForgetCachedCard(thing);
        }
    }

    private string? GetLeaseDenyReason(Zone? zone, ZoneLeaseRequest request, ISteamNetPeer peer)
    {
        if (!EmpConfig.Server.IndependentTravel.Value) {
            return "emp_travel_disabled";
        }

        if (zone is null || zone.ZoneFullName != request.ZoneFullName) {
            return "emp_travel_invalid";
        }

        if (!ActiveRemoteCharas.ContainsKey(peer.Id) && !IsAway(peer)) {
            // not joined yet
            return "emp_travel_invalid";
        }

        if (zone == _zone) {
            return "emp_travel_host_zone";
        }

        // several players may roam the world map, each on a local copy
        if (!zone.IsRegion && _leases.Any(kv => kv.Key != peer.Id && kv.Value.Contains(zone.uid))) {
            return "emp_travel_occupied";
        }

        return null;
    }

    private void ReleaseLeaseOnDisconnect(ISteamNetPeer peer)
    {
        if (_leases.Remove(peer.Id, out var zones) && zones.Count > 0) {
            // TODO: periodic checkpoints, changes made in the zone are lost for now
            EmpLog.Warning("Player {@Peer} disconnected while away in zones {ZoneUids}, its changes are lost",
                peer, zones);
        }
    }
}
