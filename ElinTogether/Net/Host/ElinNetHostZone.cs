using System;
using ElinTogether.Common;
using ElinTogether.Elements;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net.Steam;
using ElinTogether.Patches;
using Serilog.Context;

namespace ElinTogether.Net;

internal partial class ElinNetHost
{
    /// <summary>
    ///     Send the player a map snapshot from given zone
    /// </summary>
    public void PropagateZoneChangeState(Zone zone, ISteamNetPeer? peer = null)
    {
        using var _ = LogContext.PushProperty("Zone", new { zone.ZoneFullName, ZoneUid = zone.uid }, true);

        EmpPop.Debug("emp_zone_change".lang());

        var packet = ZoneDataResponse.Create(zone);

        if (peer is not null) {
            EmpLog.Debug("Dispatching zone to player {@Peer}",
                peer);

            peer.Send(packet);
        } else {
            EmpLog.Debug("Dispatching zone to all players");

            Broadcast(packet);

            // after the zone change: the question is only asked while the host is known to be there
            InviteToQuestZone(zone);
        }

        // update lobby data
        Session.Lobby.Current[EmpLobbyData.CurrentZone] = zone.NameWithLevel;
    }

    /// <summary>
    ///     Net event: Send the clients a map snapshot
    /// </summary>
    private void OnMapDataRequest(MapDataRequest request, ISteamNetPeer peer)
    {
        using var _ = LogContext.PushProperty("Zone", request, true);

        EmpLog.Information("Received zone state request from player {@Peer}",
            peer);

        var zone = _zone;
        if (request.ZoneUid != -1) {
            zone = game.spatials.Find(request.ZoneUid) ??
                   ModUtil.FindZoneByFullName(request.ZoneFullName);
        }

        if (zone is not null) {
            PropagateZoneChangeState(zone, peer);
        } else {
            EmpLog.Warning("Player {@Peer} requested invalid zone state",
                peer);

            // gtfo
            Socket.Disconnect(peer, EmpDisconnectInfo.InvalidZone);
        }
    }

    /// <summary>
    ///     Net event: Clients have replicated the zone and map, ready to transition
    /// </summary>
    private void OnZoneDataReceivedResponse(ZoneDataReceivedResponse response, ISteamNetPeer peer)
    {
        EmpLog.Debug("Player {@Peer} has finished zone replication",
            peer);

        if (!ActiveRemoteCharas.TryGetValue(peer.Id, out var chara)) {
            EmpLog.Debug("Player {@Peer} has no registered chara yet, ignoring",
                peer);
            return;
        }

        // check if the received zone is still the current zone
        // in case clients have a high RTT and host fast fingered to another zone
        if (response.ZoneUid != _zone.uid) {
            EmpLog.Debug("...but the zone state is stale, switching to new zone state {@Zone}",
                new {
                    _zone.ZoneFullName,
                    ZoneUid = _zone.uid,
                });

            PropagateZoneChangeState(_zone, peer);
            return;
        }

        // we only move their characters to zone when they are ready
        Delta.AddRemote(CardGenDelta.Create(chara));

        // move instead of add. Next to us only when nothing tells where (it joins the game)
        var pos = _zone.IsRegion
            ? WorldMapTileNextToUs(chara)
            : pc.pos.GetNearestPoint(allowChara: false, allowInstalled: false) ?? pc.pos.Copy();

        // it was on this map all along (the one simulating it came or went, or the player dropped): it stands
        // where it stood, with its companions. Or it walks in: it arrives where the game puts a player alone
        var keepSpot = false;
        if (_returnSpots.Remove(peer.User, out var spot) && spot.ZoneUid == _zone.uid &&
            UnityEngine.Time.unscaledTime < spot.Until) {
            var at = spot.Arrival is { } arrival ? ArrivalPoint(chara, arrival) : spot.Pos;
            if (at is { IsInBounds: true }) {
                keepSpot = spot.Arrival is null && !spot.Stale;
                // that very tile when it is free: it may hold something to stand on (stairs, a bed)
                pos = _zone.IsRegion ? at.Copy() : at.GetNearestPoint(allowChara: false) ?? at.Copy();
            }
        }
        if (chara.IsInActiveMap && _map.charas.Contains(chara)) {
            if (chara.Stub_Move(pos, Card.MoveType.Force) != Card.MoveResult.Success) {
                pos = chara.pos.Copy();
            }
        } else {
            if (!chara.pos.IsValid) {
                chara.pos.Set(pos.x, pos.z);
            }

            _zone.AddCard(chara, pos);
        }

        if (chara.ai is not GoalRemote) {
            chara.SetAI(GoalRemote.Default);
        }

        BringCompanions(chara, keepSpot);
        // sales made while it was a guest somewhere or offline
        PayShipping(chara.uid);
        SweepStaleCellEntries();

        EmpLog.Debug("Assigned zone sync position to player {@Peer} at {@Pos}",
            peer, pos);

        // after that, their characters will always be party members
        peer.Send(new ZoneActivateResponse {
            ZoneUid = _zone.uid,
            Pos = pos,
        });

        MarkSettled(peer);
        SendPersonalState(peer, chara.uid);

        // the guards of this map may be after that one
        if (IsCriminal(chara)) {
            _zone.RefreshCriminal();
        }

        RemoveLeftOverCharas(null);
    }

    /// <summary>
    ///     As the game places the party on the world map (Zone.AddGlobalCharasOnActivate): a tile next to ours
    ///     it can walk to. The nearest free tile alone may be the sea: a tile that blocks is refused as the game
    ///     refuses the step (Chara.CanMoveTo), and so is water (EloMap.IsWater). Ours when there is none
    /// </summary>
    private static Point WorldMapTileNextToUs(Chara chara)
    {
        var pos = pc.pos.Copy();
        var elomap = scene.elomap;

        pc.pos.ForeachNearestPoint(p => {
            if (elomap.IsWater(p.x + elomap.minX, p.z + elomap.minY) ||
                !PathManager.Instance.IsPathClear(pc.pos, p, chara, 10)) {
                return false;
            }

            pos = p.Copy();
            return true;
        }, allowBlock: false, allowChara: false, allowInstalled: true, ignoreCenter: true, maxRange: 2);

        return pos;
    }

    /// <summary>
    ///     Where the game puts a player walking into this map alone: the stairs, the gate or the edge it comes by
    ///     (Zone.GetSpawnPos), on the world map the tile of the place it comes out of. Null when nothing tells
    /// </summary>
    private static Point? ArrivalPoint(Chara chara, ZoneArrival arrival)
    {
        if (_zone.IsRegion) {
            // that tile itself, as the game does: a neighbour of a harbour is the sea
            var top = game.spatials.Find(arrival.LastZoneUid)?.GetTopZone();
            return top is not null && _zone.GetZoneAt(top.x, top.y) is not null
                ? new Point(top.mapX, top.mapY)
                : null;
        }

        if (chara.global is not { } data) {
            return null;
        }

        try {
            data.transition = arrival.ToTransition();
            return _zone.GetSpawnPos(chara)?.Clamp(useBounds: true);
        } catch (Exception ex) {
            EmpLog.Warning(ex, "No arrival point for chara {Uid} in {ZoneFullName}", chara.uid, _zone.ZoneFullName);
            return null;
        } finally {
            data.transition = null;
        }
    }
}