using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Helper.Extensions;
using ElinTogether.Models;
using ElinTogether.Net.Steam;
using HeathenEngineering.SteamworksIntegration;

namespace ElinTogether.Net;

/// <summary>
///     Independent travel: a client leases a zone the host is not in, simulates it on its own,
///     and hands it back when leaving
/// </summary>
internal partial class ElinNetHost
{
    /// <summary>
    ///     Headroom between the host uid counter and a client range, the host keeps allocating below it
    ///     during the lease. The counter only jumps past a range the client actually used
    /// </summary>
    private const int LeaseUidHeadroom = 50_000;

    /// <summary>
    ///     Peer id -> leased zone uid -> first card uid reserved for it <br />
    ///     Two zones while moving between them: the next one is granted before the previous one is handed back
    /// </summary>
    private readonly Dictionary<int, Dictionary<int, int>> _leases = [];

    /// <summary>
    ///     Peers that left the host map, see <see cref="ZoneLeaseAck" />
    /// </summary>
    private readonly HashSet<int> _departed = [];

    /// <summary>
    ///     Guest peer id -> zone it joins and the peer holding it, before and after the holder expects it
    /// </summary>
    private readonly Dictionary<int, (int ZoneUid, int HolderId)> _pendingGuests = [];

    private readonly Dictionary<int, (int ZoneUid, int HolderId)> _guests = [];

    /// <summary>
    ///     Peer id -> card uid counter of its last checkpoint
    /// </summary>
    private readonly Dictionary<int, int> _checkpointUidNext = [];

    /// <summary>
    ///     Host move into a leased zone, performed once the client hands it back
    /// </summary>
    private (Zone Zone, ZoneTransition Transition)? _pendingHostMove;

    internal bool IsAway(ISteamNetPeer peer)
    {
        // zone session: a leaving guest already handed its character to its host link
        return _departed.Contains(peer.Id) || _leavingGuests.Contains(peer.Id);
    }

    /// <summary>
    ///     The host player moves into a zone <br />
    ///     Returns true to let the move happen now, otherwise the zone is recalled from the client holding it
    /// </summary>
    internal bool TryEnterZone(Zone zone, ZoneTransition transition)
    {
        if (zone.IsRegion) {
            return true;
        }

        var holder = _leases.FirstOrDefault(kv => kv.Value.ContainsKey(zone.uid));
        if (holder.Value is null) {
            return true;
        }

        var peer = Socket.Peers.FirstOrDefault(p => p.Id == holder.Key);
        if (peer is null) {
            _leases.Remove(holder.Key);
            return true;
        }

        // entering now would load the host copy and lose what the client did there
        EmpLog.Information("Recalling zone {ZoneFullName} from {@Peer} before entering",
            zone.ZoneFullName, peer);

        _pendingHostMove = (zone, transition);
        peer.Send(new ZoneLeaseRecall {
            ZoneUid = zone.uid,
        });
        EmpPop.Information("emp_travel_recalling".lang(), peer);
        return false;
    }

    /// <summary>
    ///     Net event: Client wants to travel to a zone the host is not in
    /// </summary>
    private void OnZoneLeaseRequest(ZoneLeaseRequest request, ISteamNetPeer peer)
    {
        var zone = request.Blueprint is { } blueprint && GetPeerDenyReason(peer) is null
            ? CreateClientZone(blueprint)
            : game.spatials.Find(request.ZoneUid);

        // another player simulates the zone: join it as a guest of its zone session
        if (zone is { IsRegion: false } && GetPeerDenyReason(peer) is null && zone != _zone &&
            FindZoneHolder(zone.uid, peer) is { } holder) {
            GrantGuestLease(zone, request, peer, holder);
            return;
        }

        if ((GetPeerDenyReason(peer) ?? GetLeaseDenyReason(zone, request, peer)) is { } reason) {
            EmpLog.Information("Denied zone lease {ZoneFullName} to {@Peer}: {Reason}",
                request.ZoneFullName, peer, reason);

            peer.Send(new ZoneLeaseDenied {
                ZoneUid = request.ZoneUid,
                Reason = reason,
            });
            return;
        }

        // a guest moving on is no longer one, see HandOverZone
        _guests.Remove(peer.Id);
        var rangeStart = ReserveLease(peer, zone!);

        var map = zone.IsRegion || !zone.isGenerated
            ? null
            : ZoneLeaseState.CollectMap(zone);

        EmpLog.Information("Leased zone {ZoneFullName} to {@Peer}, uid range from {UidRangeStart}, map {HasMap}",
            zone.ZoneFullName, peer, rangeStart, map is not null);

        peer.Send(new ZoneLeaseGrant {
            ZoneUid = zone.uid,
            RequestedUid = request.ZoneUid,
            UidRangeStart = rangeStart,
            ZoneState = ZoneLeaseState.GetState(zone),
            IdCurrentSubset = zone.idCurrentSubset,
            Map = map,
        });
    }

    /// <summary>
    ///     Net event: Client flushed its last actions on the host map and left it
    /// </summary>
    private void OnZoneLeaseAck(ZoneLeaseAck ack, ISteamNetPeer peer)
    {
        if (_pendingGuests.TryGetValue(peer.Id, out var guest) && guest.ZoneUid == ack.ZoneUid) {
            DepartFromHostMap(peer);
            SendGuestRequest(peer, guest.ZoneUid, guest.HolderId);
            return;
        }

        if (!_leases.TryGetValue(peer.Id, out var zones) || !zones.ContainsKey(ack.ZoneUid)) {
            EmpLog.Warning("Player {@Peer} acknowledged zone {ZoneUid} without holding its lease",
                peer, ack.ZoneUid);
            return;
        }

        if (!DepartFromHostMap(peer)) {
            return;
        }

        peer.Send(new ZoneLeaseDepart {
            ZoneUid = ack.ZoneUid,
        });
    }

    /// <summary>
    ///     Take the player off the host map, false if it already left
    /// </summary>
    private bool DepartFromHostMap(ISteamNetPeer peer)
    {
        if (!_departed.Add(peer.Id)) {
            return false;
        }

        // apply the player's last actions on the host map now and send their results back
        // (stack merges, rebinds...) before it stops listening, see ZoneLeaseDepart
        WorldStateDeltaProcess();
        Delta.RefreshBuffer();
        WorldStateDeltaUpdate();

        // like a disconnect, without closing the connection
        PendingRebind.ReleasePeer(peer.Id);

        if (States.Remove(peer.Id, out var state)) {
            Session.CurrentPlayers.Remove(state);
        }

        if (ActiveRemoteCharas.Remove(peer.Id, out var remoteChara)) {
            RemoveRemoteChara(remoteChara);
            TakeCompanionsAlong(remoteChara);
        }

        Broadcast(SessionPlayersSnapshot.Create());

        EmpLog.Information("Player {@Peer} left the host map",
            peer);
        return true;
    }

    /// <summary>
    ///     The client holding the zone, if another connected player
    /// </summary>
    private ISteamNetPeer? FindZoneHolder(int zoneUid, ISteamNetPeer asking)
    {
        foreach (var (peerId, zones) in _leases) {
            if (peerId != asking.Id && zones.ContainsKey(zoneUid)) {
                return Socket.Peers.FirstOrDefault(p => p.Id == peerId);
            }
        }

        return null;
    }

    /// <summary>
    ///     Lease the zone to the player, returns the first card uid it may allocate
    /// </summary>
    private int ReserveLease(ISteamNetPeer peer, Zone zone)
    {
        // above the host counter and above any range handed out and still in use
        var floor = _leases.Values.SelectMany(z => z.Values).DefaultIfEmpty(0).Max();
        var rangeStart = Math.Max(game.cards.uidNext, floor) + LeaseUidHeadroom;

        if (!_leases.TryGetValue(peer.Id, out var zones)) {
            zones = _leases[peer.Id] = [];
        }

        zones[zone.uid] = rangeStart;
        return rangeStart;
    }

    /// <summary>
    ///     The owner of a zone left it or dropped: the players visiting it stay, the first one simulates it
    ///     from now on and the others join its zone session. Unless the host is on its way in, then they come back
    /// </summary>
    private void HandOverZone(int zoneUid, int holderId)
    {
        var guests = new List<ISteamNetPeer>();
        foreach (var (guestId, at) in _guests.ToList()) {
            if (at.ZoneUid != zoneUid || at.HolderId != holderId) {
                continue;
            }

            _guests.Remove(guestId);
            if (_departed.Contains(guestId) && Socket.Peers.FirstOrDefault(p => p.Id == guestId) is { } guest) {
                guests.Add(guest);
            }
        }

        // on their way to the old owner, it will not expect them anymore
        foreach (var (guestId, at) in _pendingGuests.ToList()) {
            if (at.ZoneUid == zoneUid && at.HolderId == holderId &&
                Socket.Peers.FirstOrDefault(p => p.Id == guestId) is { } guest) {
                RefuseGuest(guest, zoneUid);
            }
        }

        if (guests.Count == 0) {
            return;
        }

        if (_pendingHostMove?.Zone.uid == zoneUid || game.spatials.Find(zoneUid) is not { } zone) {
            foreach (var guest in guests) {
                guest.Send(new ZoneLeaseRecall {
                    ZoneUid = zoneUid,
                });
            }

            return;
        }

        var heir = guests[0];
        var rangeStart = ReserveLease(heir, zone);

        EmpLog.Information("Zone {ZoneFullName} handed over to {@Peer}, uid range from {UidRangeStart}",
            zone.ZoneFullName, heir, rangeStart);

        // its copy of the zone is live, no map
        heir.Send(new ZoneLeaseGrant {
            ZoneUid = zoneUid,
            RequestedUid = zoneUid,
            UidRangeStart = rangeStart,
            ZoneState = ZoneLeaseState.GetState(zone),
            IdCurrentSubset = zone.idCurrentSubset,
            Handoff = true,
        });

        foreach (var guest in guests.Skip(1)) {
            _pendingGuests[guest.Id] = (zoneUid, heir.Id);
            SendGuestRequest(guest, zoneUid, heir.Id);
        }
    }

    private void GrantGuestLease(Zone zone, ZoneLeaseRequest request, ISteamNetPeer peer, ISteamNetPeer holder)
    {
        _guests.Remove(peer.Id);
        _pendingGuests[peer.Id] = (zone.uid, holder.Id);

        EmpLog.Information("Player {@Peer} joins zone {ZoneFullName} held by {@Holder}",
            peer, zone.ZoneFullName, holder);

        // the guest leaves its current place first (ack or release), then the holder expects it
        peer.Send(new ZoneLeaseGrant {
            ZoneUid = zone.uid,
            RequestedUid = request.ZoneUid,
            UidRangeStart = 0,
            ZoneState = ZoneLeaseState.GetState(zone),
            IdCurrentSubset = zone.idCurrentSubset,
            Guest = true,
        });
    }

    private void SendGuestRequest(ISteamNetPeer guest, int zoneUid, int holderId)
    {
        var holder = Socket.Peers.FirstOrDefault(p => p.Id == holderId);
        var chara = SavedRemoteCharas.TryGetValue(guest.User, out var uid) ? game.cards.globalCharas.Find(uid) : null;

        if (holder is null || chara is null) {
            RefuseGuest(guest, zoneUid);
            return;
        }

        holder.Send(new ZoneGuestRequest {
            ZoneUid = zoneUid,
            GuestUser = guest.User,
            Chara = LZ4Bytes.Create(chara),
            Companions = CompanionHelper.CompanionsOf(chara).Select(c => LZ4Bytes.Create(c)).ToList(),
        });
    }

    /// <summary>
    ///     Net event: the zone holder expects the guest, or refuses it
    /// </summary>
    private void OnZoneGuestReady(ZoneGuestReady ready, ISteamNetPeer holder)
    {
        var guest = Socket.Peers.FirstOrDefault(p =>
            (ulong)p.User == ready.GuestUser &&
            _pendingGuests.TryGetValue(p.Id, out var pending) && pending.ZoneUid == ready.ZoneUid);

        if (guest is null) {
            EmpLog.Warning("Zone guest {RemoteIdentity} is gone", ready.GuestUser);
            return;
        }

        if (!ready.Accepted) {
            RefuseGuest(guest, ready.ZoneUid);
            return;
        }

        _guests[guest.Id] = _pendingGuests[guest.Id];
        _pendingGuests.Remove(guest.Id);

        guest.Send(new ZoneLeaseDepart {
            ZoneUid = ready.ZoneUid,
            Guest = new() {
                HostUser = holder.User,
                Port = ready.Port,
            },
        });

        EmpLog.Information("Player {@Peer} joins the zone session of {@Holder}",
            guest, holder);
    }

    /// <summary>
    ///     The guest already left its place, it comes back to the host
    /// </summary>
    private void RefuseGuest(ISteamNetPeer guest, int zoneUid)
    {
        _pendingGuests.Remove(guest.Id);

        EmpLog.Information("Zone {ZoneUid} refused player {@Peer}, it returns to the host",
            zoneUid, guest);

        guest.Send(new ZoneLeaseDenied {
            ZoneUid = zoneUid,
            Reason = "emp_travel_occupied",
        });
    }

    /// <summary>
    ///     Net event: Client hands a leased zone back
    /// </summary>
    private void OnZoneLeaseRelease(ZoneLeaseRelease release, ISteamNetPeer peer)
    {
        if (!_departed.Contains(peer.Id)) {
            // stale or repeated release, the player is already back on the host map
            EmpLog.Warning("Player {@Peer} released zone {ZoneUid} while not away, ignoring",
                peer, release.ZoneUid);
            return;
        }

        if (release.Checkpoint) {
            ApplyCheckpoint(release, peer);
            return;
        }

        var handedBack = false;
        if (_leases.TryGetValue(peer.Id, out var zones) && zones.Remove(release.ZoneUid, out var rangeStart)) {
            handedBack = true;

            if (game.spatials.Find(release.ZoneUid) is { IsRegion: false } zone) {
                ApplyLeasedZone(zone, release);
            }

            // only a range the client allocated in pushes the host counter
            if (release.UidNext > rangeStart) {
                game.cards.uidNext = Math.Max(game.cards.uidNext, release.UidNext);
            }
        } else if (release.ZoneUid != -1) {
            EmpLog.Warning("Player {@Peer} released zone {ZoneUid} without holding its lease, ignoring the zone",
                peer, release.ZoneUid);
        }

        // a guest hands nothing back, it is only leaving
        _guests.Remove(peer.Id);

        var chara = ReplaceRemoteChara(peer.User, release.Chara);
        ReplaceCompanions(release.Companions, SavedRemoteCharas.TryGetValue(peer.User, out var ownerUid) ? ownerUid : 0);
        ReplaceGuestCharas(release, peer);

        if (handedBack) {
            HandOverZone(release.ZoneUid, peer.Id);
        }

        if (release.Rejoin) {
            if (zones is { Count: > 0 }) {
                EmpLog.Warning("Player {@Peer} rejoins while still holding zones {ZoneUids}, dropping them",
                    peer, zones.Keys);
            }

            _leases.Remove(peer.Id);
            _departed.Remove(peer.Id);
            _checkpointUidNext.Remove(peer.Id);

            if (chara is not null) {
                EmpLog.Information("Player {@Peer} returns to the host zone",
                    peer);

                SendSaveProbe(chara, peer);
            }

            // the zone files are already in the save folder, keep game.txt consistent with them
            if (!EClass.debug.ignoreAutoSave) {
                game.Save(isAutoSave: true);
            }
        }

        ResumePendingHostMove();
    }

    /// <summary>
    ///     Progress of a client still away: its zone and character, the lease stays
    /// </summary>
    private void ApplyCheckpoint(ZoneLeaseRelease checkpoint, ISteamNetPeer peer)
    {
        if (!_leases.TryGetValue(peer.Id, out var zones) || !zones.ContainsKey(checkpoint.ZoneUid)) {
            EmpLog.Warning("Player {@Peer} sent a checkpoint for zone {ZoneUid} it does not hold",
                peer, checkpoint.ZoneUid);
            return;
        }

        if (game.spatials.Find(checkpoint.ZoneUid) is { IsRegion: false } zone) {
            ApplyLeasedZone(zone, checkpoint);
        }

        // the client keeps allocating in its range, the host counter only moves on release or disconnect
        _checkpointUidNext[peer.Id] = checkpoint.UidNext;

        ReplaceRemoteChara(peer.User, checkpoint.Chara);
        ReplaceCompanions(checkpoint.Companions, SavedRemoteCharas.TryGetValue(peer.User, out var ownerUid) ? ownerUid : 0);
        ReplaceGuestCharas(checkpoint, peer);

        EmpLog.Debug("Checkpoint of player {@Peer} in zone {ZoneUid}",
            peer, checkpoint.ZoneUid);
    }

    private void ResumePendingHostMove()
    {
        if (_pendingHostMove is not { } move || _leases.Values.Any(z => z.ContainsKey(move.Zone.uid))) {
            return;
        }

        _pendingHostMove = null;

        EmpLog.Information("Zone {ZoneFullName} handed back, host enters",
            move.Zone.ZoneFullName);

        pc.MoveZone(move.Zone, move.Transition);
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
                // its cards leave the cache too, the client copies carry the same uids
                ForgetCachedMap(zone.map);
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
    /// <param name="register">zone session: take the uploaded uid as the saved chara of that player</param>
    private Chara? ReplaceRemoteChara(UserData user, LZ4Bytes data, bool register = false)
    {
        var uploaded = data.Decompress<Chara>();

        if (register) {
            SavedRemoteCharas[user] = uploaded.uid;
        }

        if (!SavedRemoteCharas.TryGetValue(user, out var uid)) {
            EmpLog.Warning("Player {RemoteIdentity} has no saved remote chara", user);
            return null;
        }

        var old = game.cards.globalCharas.Find(uid);

        if (uploaded.uid != uid) {
            EmpLog.Warning("Player {RemoteIdentity} uploaded chara {UploadedUid}, expected {Uid}, keeping host copy",
                user, uploaded.uid, uid);
            return old;
        }

        // stale entries at its uids (copies received earlier) would get it renumbered when cached again
        ForgetCachedCard(uploaded);

        if (old is not null) {
            ForgetCachedCard(old);
            // branches hold object references, the new copy joins again through MakeAlly
            EClass.Home.FindBranch(old)?.RemoveMemeber(old);
            game.cards.globalCharas.Remove(old);
        }

        uploaded.SetBool(CINT.IsPC, false);
        // not in any host map until it rejoins, the zone it left must not pull it back in
        uploaded.currentZone = null;
        game.cards.globalCharas.Add(uploaded);

        // client side ability tokens and cards still waiting for a host uid are not real host cards
        InvPlaceAbilityDelta.InvalidateFakeAbilityCard(uploaded);
        foreach (var thing in uploaded.things.Flatten().ToList()) {
            if (PendingUid.IsPending(thing.uid)) {
                game.cards.AssignUID(thing);
            }
        }

        EmpLog.Debug("Replaced remote chara {Uid} of player {RemoteIdentity}",
            uid, user);

        return uploaded;
    }

    /// <summary>
    ///     Players visiting the zone are simulated by its owner, their characters come with its uploads
    /// </summary>
    private void ReplaceGuestCharas(ZoneLeaseRelease release, ISteamNetPeer holder)
    {
        foreach (var (user, chara) in release.GuestCharas ?? []) {
            // a guest that left since (back here or elsewhere) brought a newer copy itself
            if (Socket.Peers.FirstOrDefault(p => (ulong)p.User == user) is { } guest &&
                (!_guests.TryGetValue(guest.Id, out var at) || at.HolderId != holder.Id)) {
                continue;
            }

            ReplaceRemoteChara(user, chara);

            if (release.GuestCompanions?.TryGetValue(user, out var companions) is true &&
                SavedRemoteCharas.TryGetValue(user, out var ownerUid)) {
                ReplaceCompanions(companions, ownerUid);
            }
        }
    }

    private static void ForgetCachedCard(Card card)
    {
        CardCache.Remove(card.uid);

        foreach (var thing in card.things) {
            ForgetCachedCard(thing);
        }
    }

    private static void ForgetCachedMap(Map map)
    {
        foreach (var thing in map.things) {
            ForgetCachedCard(thing);
        }

        foreach (var chara in map.charas) {
            if (!chara.IsGlobal) {
                ForgetCachedCard(chara);
            }
        }
    }

    /// <summary>
    ///     Zone created on the client (world map field, dungeon floor...): create it here too,
    ///     the host assigns the uid and the client renumbers its copy
    /// </summary>
    private Zone? CreateClientZone(LeaseZoneBlueprint blueprint)
    {
        var parent = game.spatials.Find(blueprint.ParentUid);
        if (parent is null || !sources.zones.map.ContainsKey(blueprint.Id)) {
            EmpLog.Warning("Cannot create client zone {ZoneId}, parent {ParentUid} unknown",
                blueprint.Id, blueprint.ParentUid);
            return null;
        }

        if (SpatialGen.Create(blueprint.Id, parent, true, blueprint.X, blueprint.Y, blueprint.Icon) is not Zone zone) {
            return null;
        }

        ZoneLeaseState.ApplyState(zone, blueprint.ZoneState, blueprint.IdCurrentSubset);

        if (parent is Region region) {
            region.elomap.SetZone(zone.x, zone.y, zone, true);
        }

        EmpLog.Information("Created client zone {ZoneFullName} as uid {ZoneUid}",
            zone.ZoneFullName, zone.uid);

        return zone;
    }

    private string? GetPeerDenyReason(ISteamNetPeer peer)
    {
        if (!EmpConfig.Server.IndependentTravel.Value) {
            return "emp_travel_disabled";
        }

        if (!ActiveRemoteCharas.ContainsKey(peer.Id) && !IsAway(peer)) {
            // not joined yet
            return "emp_travel_invalid";
        }

        return null;
    }

    private string? GetLeaseDenyReason(Zone? zone, ZoneLeaseRequest request, ISteamNetPeer peer)
    {
        if (zone is null || zone.ZoneFullName != request.ZoneFullName) {
            return "emp_travel_invalid";
        }

        if (zone == _zone) {
            return "emp_travel_host_zone";
        }

        // several players may roam the world map, each on a local copy
        if (!zone.IsRegion && _leases.Any(kv => kv.Key != peer.Id && kv.Value.ContainsKey(zone.uid))) {
            return "emp_travel_occupied";
        }

        return null;
    }

    private void ReleaseLeaseOnDisconnect(ISteamNetPeer peer)
    {
        _departed.Remove(peer.Id);
        _pendingGuests.Remove(peer.Id);
        _guests.Remove(peer.Id);

        // cards of the last checkpoint are in the save now, the host must not allocate their uids
        if (_checkpointUidNext.Remove(peer.Id, out var uidNext)) {
            game.cards.uidNext = Math.Max(game.cards.uidNext, uidNext);
        }

        if (_leases.Remove(peer.Id, out var zones) && zones.Count > 0) {
            EmpLog.Warning("Player {@Peer} disconnected while away in zones {ZoneUids}, " +
                           "keeping its last checkpoint",
                peer, zones.Keys);

            foreach (var zoneUid in zones.Keys) {
                HandOverZone(zoneUid, peer.Id);
            }

            if (!EClass.debug.ignoreAutoSave) {
                game.Save(isAutoSave: true);
            }
        }

        ResumePendingHostMove();
    }
}
