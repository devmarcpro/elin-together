using System;
using System.Collections.Generic;
using System.Diagnostics;
using ElinTogether.Helper;
using ElinTogether.Helper.Extensions;
using ElinTogether.Models;
using MessagePack;
using UnityEngine;

namespace ElinTogether.Net;

/// <summary>
///     A few numbers about the active map, computed the same way by the game that keeps it and by every game
///     standing on it, see <see cref="NetDesync" />
/// </summary>
[MessagePackObject]
public class MapSums
{
    [Key(0)]
    public int ZoneUid { get; init; }

    [Key(1)]
    public int Charas { get; init; }

    [Key(2)]
    public int CharaMix { get; init; }

    [Key(3)]
    public int Things { get; init; }

    [Key(4)]
    public int ThingMix { get; init; }

    /// <summary>
    ///     Player chara uid -> mix of its bag and equipment
    /// </summary>
    [Key(5)]
    public Dictionary<int, int>? Bags { get; init; }
}

/// <summary>
///     Guest -> the game that keeps its map: its copy of the map differs, so that this journal says it too.
///     With <see cref="Resync" /> the guest asks for the map again right after
/// </summary>
[MessagePackObject]
public class DesyncReportDelta : ElinDelta
{
    [Key(0)]
    public string? ZoneFullName { get; init; }

    [Key(1)]
    public string? Detail { get; init; }

    [Key(2)]
    public bool Resync { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host) {
            return;
        }

        // text written by another game: cut before it reaches this journal
        EmpLog.Warning("Player {PeerIndex} reports a map checksum that differs on {ZoneFullName} (there/here): {Detail}, reload {Resync}",
            OriginPeer, Cut(ZoneFullName), Cut(Detail), Resync);

        if (Resync) {
            host.KeepSpotForResync(OriginPeer);
        }
    }

    private static string? Cut(string? text)
    {
        return text is { Length: > 200 } ? text.Substring(0, 200) : text;
    }
}

/// <summary>
///     Map checksum: nothing ever resends an item or a character a game missed, a gap lasts until the next map
///     load. The game that keeps the map sends its numbers with the player list every 2 seconds
///     (<see cref="SessionPlayersSnapshot" />), the others compare with theirs. A difference only counts when both
///     sides stood still on it for 3 comparisons in a row: what is on its way (a move, a pickup) changes the numbers
///     of one side between two comparisons. Then a warning in both journals, and with the host rule AutoResync the
///     map is asked again, or the one character whose bag differs (<see cref="CharaBagDelta" />) <br />
///     Left out on purpose: where characters stand (the snapshot allows 2 tiles), where items lie (what is thrown
///     or scattered lands by the dice of each game), dead characters, cards waiting for their number
///     (<see cref="PendingUid" />), ability tokens, what chests hold, the world map
/// </summary>
internal static class NetDesync
{
    private const int Strikes = 3;

    // two lists sent closer than that (a player left) count as one comparison
    private const float MinGap = 1.5f;

    // after a map load, before comparing again
    private const float LoadGrace = 6f;

    private const float Cooldown = 30f;
    private const int MaxFruitless = 3;

    // reloads of one map during one stay on it, whatever they brought
    private const int MaxRepairs = 5;
    private const int CombatRange = 8;

    private static WeakReference<Map>? _seenMap;
    private static float _nextCompare;
    private static float _quietUntil;
    private static float _nextRepair;
    private static int _zoneUid;
    private static int _mapKey;
    private static int _mapStrikes;
    private static int _bagKey;
    private static int _bagStrikes;
    private static int _repairs;
    private static int _fruitless;
    private static bool _gaveUp;

    /// <summary>
    ///     Sub-option, off: also bring the bag of OUR OWN character to the keeper's copy. The bags of the other
    ///     players are copies nobody saves, ours is the one we play with: never played, see BagRepairRefused
    /// </summary>
    internal static bool RepairOwnBag;

    /// <summary>
    ///     Asking again for a bag that differs: written, never played, off until it has been seen running
    /// </summary>
    internal static bool RepairBags;

    // player chara uid -> next time its bag may be asked again, how often it was, what was compared then
    private static readonly Dictionary<int, float> _nextBagAsk = [];
    private static readonly Dictionary<int, int> _bagAsks = [];

    // how often each bag was asked during this stay on the map, whatever came of it: no more after MaxBagAsks
    private const int MaxBagAsks = 3;
    private static readonly Dictionary<int, int> _bagAsksOnMap = [];
    private static readonly Dictionary<int, (int Ours, int Theirs, float At)> _askedBags = [];

    // an answer older than that is about a bag that had time to change
    private const float BagAnswerWait = 10f;

    private static MapSums? _lastLocal;
    private static MapSums? _lastHost;
    private static string _lastWarning = "none";
    private static double _lastCostMs;

    /// <summary>
    ///     The numbers of the active map as this game holds it, null when there is nothing to compare
    /// </summary>
    internal static MapSums? Collect()
    {
        try {
            if (!EClass.core.IsGameStarted || EClass._zone is not { IsRegion: false } zone || EClass._map is not { } map) {
                return null;
            }

            var watch = Stopwatch.StartNew();

            var players = new HashSet<int>();
            foreach (var state in NetSession.Instance.CurrentPlayers) {
                players.Add(state.CharaUid);
            }

            var bags = new Dictionary<int, int>();
            int charas = 0, charaMix = 0, things = 0, thingMix = 0;

            unchecked {
                foreach (var chara in map.charas) {
                    if (chara.isDead || !chara.IsInActiveMap || PendingUid.IsPending(chara.uid)) {
                        continue;
                    }

                    charas++;
                    charaMix += Mix(chara.uid, 0, 0, 0);

                    if (players.Contains(chara.uid)) {
                        bags[chara.uid] = Bag(chara);
                    }
                }

                foreach (var thing in map.things) {
                    if (Skipped(thing)) {
                        continue;
                    }

                    things++;
                    // not its tile: a thrown item, an arrow, scattered loot land by the dice of each game
                    thingMix += Mix(thing.uid, thing.Num, 0, 0);
                }
            }

            _lastCostMs = watch.Elapsed.TotalMilliseconds;

            return new() {
                ZoneUid = zone.uid,
                Charas = charas,
                CharaMix = charaMix,
                Things = things,
                ThingMix = thingMix,
                Bags = bags,
            };
        } catch (Exception ex) {
            EmpLog.Debug(ex, "Map checksum not computed");
            return null;
        }
    }

    /// <summary>
    ///     The numbers of the game that keeps the map arrived: compare, warn, repair
    /// </summary>
    internal static void Compare(MapSums? host)
    {
        try {
            CompareCore(host);
        } catch (Exception ex) {
            EmpLog.Debug(ex, "Map checksum not compared");
        }
    }

    private static void CompareCore(MapSums? host)
    {
        var session = NetSession.Instance;
        if (host is null || session.Connection is not ElinNetClient client) {
            return;
        }

        var now = Time.unscaledTime;
        if (now < _nextCompare) {
            return;
        }

        _nextCompare = now + MinGap;

        // not on that map (yet)
        if (!EClass.core.IsGameStarted || EClass._zone?.uid != host.ZoneUid || EClass._map is not { } map) {
            _mapStrikes = _bagStrikes = 0;
            return;
        }

        if (host.ZoneUid != _zoneUid) {
            _zoneUid = host.ZoneUid;
            _repairs = _fruitless = 0;
            _gaveUp = false;
            _bagAsksOnMap.Clear();
        }

        // a map just loaded: what the host did meanwhile is still on its way
        if (_seenMap is null || !_seenMap.TryGetTarget(out var seen) || !ReferenceEquals(seen, map)) {
            _seenMap = new(map);
            _quietUntil = now + LoadGrace;
        }

        if (now < _quietUntil) {
            _mapStrikes = _bagStrikes = 0;
            return;
        }

        if (Collect() is not { } local) {
            return;
        }

        _lastLocal = local;
        _lastHost = host;

        // a strike only when neither side moved since the last comparison
        var mapDiffers = local.Charas != host.Charas || local.CharaMix != host.CharaMix ||
                         local.Things != host.Things || local.ThingMix != host.ThingMix;
        var mapKey = Mix(Mix(local.Charas, local.CharaMix, local.Things, local.ThingMix),
            Mix(host.Charas, host.CharaMix, host.Things, host.ThingMix), 0, 0);
        _mapStrikes = !mapDiffers ? 0 : mapKey == _mapKey ? _mapStrikes + 1 : 1;
        _mapKey = mapKey;

        List<int>? bags = null;
        var bagKey = 0;
        foreach (var (uid, theirs) in host.Bags ?? []) {
            if (!local.Bags!.TryGetValue(uid, out var ours)) {
                continue;
            }

            if (ours == theirs) {
                _bagAsks.Remove(uid);
                continue;
            }

            (bags ??= []).Add(uid);
            unchecked {
                bagKey += Mix(uid, ours, theirs, 0);
            }
        }

        _bagStrikes = bags is null ? 0 : bagKey == _bagKey ? _bagStrikes + 1 : 1;
        _bagKey = bagKey;

        if (!mapDiffers) {
            _fruitless = 0;
            _gaveUp = _repairs >= MaxRepairs;
        }

        var warn = _mapStrikes == Strikes || _bagStrikes == Strikes;
        var gaveUp = false;
        var repair = _mapStrikes >= Strikes && ShouldRepair(session, client, now, out gaveUp);

        // not while the map is asked again: the answer would land in the middle of its load
        if (RepairBags && !repair && bags is not null && _bagStrikes >= Strikes) {
            AskBags(session, client, now, local, host, bags);
        }

        if (!warn && !repair && !gaveUp) {
            return;
        }

        var zoneName = EClass._zone.ZoneFullName;
        var detail = Detail(local, host, _mapStrikes >= Strikes, _bagStrikes >= Strikes ? bags : null);

        if (warn) {
            _lastWarning = $"{DateTime.Now:HH:mm:ss} {zoneName}: {detail}";
            EmpLog.Warning("Map checksum differs on {ZoneFullName} (here/host): {Detail}",
                zoneName, detail);
        }

        if (gaveUp) {
            detail = $"persistent after {_repairs} reloads, {detail}";
            _lastWarning = $"{DateTime.Now:HH:mm:ss} {zoneName}: {detail}";
            EmpLog.Warning("Map checksum still differs on {ZoneFullName} after {Repairs} reloads, no more reload of this map: {Detail}",
                zoneName, _repairs, detail);
        }

        if (repair) {
            EmpLog.Information("Reloading {ZoneFullName} to repair it, attempt {Repairs}",
                zoneName, _repairs);
            EmpPop.Information("emp_ui_resync".lang());

            _mapStrikes = 0;
            _quietUntil = now + LoadGrace + LoadGrace;
        }

        // before the request: the host notes where we stand before it answers the map
        client.Host.Send(new WorldStateDeltaList {
            DeltaList = [
                new DesyncReportDelta {
                    ZoneFullName = zoneName,
                    Detail = detail,
                    Resync = repair,
                },
            ],
        });

        if (repair) {
            client.RequestZoneState(MapDataRequest.CurrentRemoteZone);
        }
    }

    /// <summary>
    ///     The reload drops what happens to the map while it loads and takes the screen for a moment: only when the
    ///     player does nothing, at most once per <see cref="Cooldown" /> (doubled after each one on the same map),
    ///     and no more after <see cref="MaxFruitless" /> reloads that never brought the numbers together or
    ///     <see cref="MaxRepairs" /> reloads of the same map
    /// </summary>
    private static bool ShouldRepair(NetSession session, ElinNetClient client, float now, out bool gaveUp)
    {
        gaveUp = false;

        if (!session.Rules.AutoResync || _gaveUp || now < _nextRepair) {
            return false;
        }

        if (_fruitless >= MaxFruitless || _repairs >= MaxRepairs) {
            gaveUp = _gaveUp = true;
            return false;
        }

        if (!client.IsQuietForResync || (session.Transport as ElinNetClient)?.IsQuietForResync == false || Busy()) {
            return false;
        }

        _fruitless++;
        _nextRepair = now + Cooldown * (1 << Math.Min(_repairs++, 4));
        return true;
    }

    /// <summary>
    ///     A bag that stood different for <see cref="Strikes" /> comparisons: ask its keeper for that character in
    ///     full (<see cref="CharaBagDelta" />), at most once per <see cref="Cooldown" /> and per character (doubled
    ///     each time until that bag is the same again) and at most <see cref="MaxBagAsks" /> times per stay on a map,
    ///     under the rule and the stillness a map reload needs
    /// </summary>
    private static void AskBags(NetSession session, ElinNetClient client, float now, MapSums local, MapSums host, List<int> bags)
    {
        if (!session.Rules.AutoResync || !Quiet(session, client)) {
            return;
        }

        foreach (var uid in bags) {
            var own = EClass.pc.uid == uid;
            if ((own && !RepairOwnBag) || (_nextBagAsk.TryGetValue(uid, out var next) && now < next) ||
                _bagAsksOnMap.GetValueOrDefault(uid) >= MaxBagAsks) {
                continue;
            }

            _bagAsksOnMap[uid] = _bagAsksOnMap.GetValueOrDefault(uid) + 1;
            var asks = _bagAsks.GetValueOrDefault(uid);
            _bagAsks[uid] = asks + 1;
            _nextBagAsk[uid] = now + Cooldown * (1 << Math.Min(asks, 4));
            if (own) {
                _askedBags[uid] = (local.Bags![uid], host.Bags![uid], now);
            }

            EmpLog.Information("Asking for the bag of {Uid} again, ours {Own}, attempt {Asks} (here {Local:X8} | host {Host:X8})",
                uid, own, asks + 1, local.Bags![uid], host.Bags![uid]);

            client.Host.Send(new WorldStateDeltaList {
                DeltaList = [
                    new CharaBagDelta {
                        Uid = uid,
                        Mix = host.Bags[uid],
                    },
                ],
            });
        }
    }

    /// <summary>
    ///     The keeper's copy of a bag arrived (<paramref name="theirs" />) and ours differs (<paramref name="ours" />):
    ///     why it must stay as it is, null to replace it. <br />
    ///     Someone else's bag is a copy nobody saves: replaced whenever this player does nothing. Our own is the
    ///     one we act on, and what we do to it shows here before the keeper hears of it: only behind
    ///     <see cref="RepairOwnBag" />, only the answer to our own request, and only if neither side moved since
    ///     the comparisons that led to it
    /// </summary>
    internal static string? BagRepairRefused(Chara chara, int ours, int theirs)
    {
        var session = NetSession.Instance;
        if (session.Connection is not ElinNetClient client || !session.Rules.AutoResync) {
            return "rule off";
        }

        if (!Quiet(session, client)) {
            return "busy";
        }

        if (!chara.IsPC) {
            return null;
        }

        if (!RepairOwnBag) {
            return "our own bag, sub-option off";
        }

        if (!_askedBags.Remove(chara.uid, out var asked) || Time.unscaledTime - asked.At > BagAnswerWait) {
            return "not asked by us";
        }

        return asked.Ours != ours || asked.Theirs != theirs ? "it moved since we asked" : null;
    }

    private static bool Quiet(NetSession session, ElinNetClient client)
    {
        return client.IsQuietForResync && (session.Transport as ElinNetClient)?.IsQuietForResync != false && !Busy();
    }

    private static bool Busy()
    {
        var pc = EClass.pc;
        if (pc is null || pc.isDead || !pc.HasNoGoal || pc.enemy is not null ||
            EClass.ui.IsActive || EClass.ui.IsDragging ||EClass.scene.mode != Scene.Mode.Zone) {
            return true;
        }

        foreach (var chara in EClass._map.charas) {
            if (!chara.isDead && chara.IsHostile() && chara.pos.Distance(pc.pos) <= CombatRange) {
                return true;
            }
        }

        return false;
    }

    private static string Detail(MapSums local, MapSums host, bool mapDiffers, List<int>? bags)
    {
        var parts = new List<string>();

        if (mapDiffers && (local.Charas != host.Charas || local.CharaMix != host.CharaMix)) {
            parts.Add($"charas {local.Charas}/{host.Charas}" + (local.Charas == host.Charas ? " (not the same ones)" : ""));
        }

        if (mapDiffers && (local.Things != host.Things || local.ThingMix != host.ThingMix)) {
            parts.Add($"things {local.Things}/{host.Things}" +
                      (local.Things == host.Things ? " (not the same ones or amounts)" : ""));
        }

        if (bags is not null) {
            parts.Add($"bags of {string.Join(",", bags)}");
        }

        return string.Join(", ", parts);
    }

    internal static bool Skipped(Thing thing)
    {
        return thing.isDestroyed || PendingUid.IsPending(thing.uid) || thing.trait is TraitAbility;
    }

    internal static int Bag(Chara chara)
    {
        var mix = 0;
        foreach (var thing in chara.things.Flatten()) {
            if (Skipped(thing)) {
                continue;
            }

            unchecked {
                mix += Mix(thing.uid, thing.Num, thing.c_equippedSlot != 0 ? 1 : 0, 0);
            }
        }

        return mix;
    }

    // summed over the cards: the order of the lists does not matter, and two equal cards do not cancel out
    private static int Mix(int a, int b, int c, int d)
    {
        unchecked {
            var h = (uint)a * 0x9E3779B1u;
            h = (h ^ (uint)b) * 0x85EBCA6Bu;
            h = (h ^ (uint)c) * 0xC2B2AE35u;
            h = (h ^ (uint)d) * 0x27D4EB2Fu;
            return (int)(h ^ (h >> 15));
        }
    }

    /// <summary>
    ///     For emp.desync and the test bench
    /// </summary>
    internal static string Describe()
    {
        var local = Collect();
        var cost = _lastCostMs;

        return $"here: {Line(local)}, computed in {cost:F2} ms\n" +
               $"last compared: here {Line(_lastLocal)} | host {Line(_lastHost)}\n" +
               $"strikes: map {_mapStrikes}, bags {_bagStrikes}; reloads {_repairs}, fruitless {_fruitless}, gave up {_gaveUp}; " +
               $"bags asked {string.Join(" ", _bagAsks)}, own bag repair {RepairOwnBag}\n" +
               $"last warning: {_lastWarning}";
    }

    private static string Line(MapSums? sums)
    {
        if (sums is null) {
            return "nothing";
        }

        var bags = new List<string>();
        foreach (var (uid, mix) in sums.Bags ?? []) {
            bags.Add($"{uid}:{mix:X8}");
        }

        return $"zone {sums.ZoneUid} charas {sums.Charas}:{sums.CharaMix:X8} things {sums.Things}:{sums.ThingMix:X8} " +
               $"bags {string.Join(" ", bags)}";
    }
}

internal partial class ElinNetHost
{
    /// <summary>
    ///     A player loads this map again to repair its copy: it stays where it stands, not next to us, see
    ///     OnZoneDataReceivedResponse
    /// </summary>
    internal void KeepSpotForResync(int peerId)
    {
        if (States.TryGetValue(peerId, out var state) && ActiveRemoteCharas.TryGetValue(peerId, out var chara) &&
            chara.pos is { IsValid: true } stood && _zone is { } zone) {
            _returnSpots[state.User] = (zone.uid, stood.Copy(), null, Time.unscaledTime + 30f, false);
        }
    }
}

internal partial class ElinNetClient
{
    /// <summary>
    ///     Nothing of ours is between two maps: no travel asked or granted, no map being loaded
    /// </summary>
    internal bool IsQuietForResync =>
        IsConnected && _pendingTravel is null && _pendingGrant is null && !_rejoining && _awaitingActivation == 0 && !IsInTransfer;
}
