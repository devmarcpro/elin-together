using System.Collections.Generic;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     How far what a player carries has gone off, as the host counts it each hour (RemoteDecayPatch): that player's
///     own game ages its copy on its own clock and misses the hours the world jumps
/// </summary>
[MessagePackObject]
public class CardDecayDelta : ElinDelta
{
    [Key(0)]
    public required int[] Uids { get; init; }

    [Key(1)]
    public required int[] Decay { get; init; }

    internal static CardDecayDelta? Create(Chara player)
    {
        var uids = new List<int>();
        var decay = new List<int>();
        player.things.Foreach(thing => {
            if (thing.decay != 0) {
                uids.Add(thing.uid);
                decay.Add(thing.decay);
            }
        }, false);

        return uids.Count == 0 ? null : new() { Uids = [..uids], Decay = [..decay] };
    }

    /// <summary>
    ///     Decay of every thing lying on the map (floor, fridges, containers), by uid; the host's hourly simulation of
    ///     the map is the only one that ages them
    /// </summary>
    internal static Dictionary<int, int> SnapshotMap()
    {
        var snap = new Dictionary<int, int>();
        void Walk(Thing thing)
        {
            if (thing.decay != 0) {
                snap[thing.uid] = thing.decay;
            }

            foreach (var child in thing.things) {
                Walk(child);
            }
        }

        foreach (var thing in EClass._map.things) {
            Walk(thing);
        }

        return snap;
    }

    /// <summary>Only what changed since the snapshot, so an hour costs a few bytes when little goes off</summary>
    internal static CardDecayDelta? CreateMapChanges(Dictionary<int, int> before)
    {
        var uids = new List<int>();
        var decay = new List<int>();
        foreach (var (uid, value) in SnapshotMap()) {
            if (!before.TryGetValue(uid, out var old) || old != value) {
                uids.Add(uid);
                decay.Add(value);
            }
        }

        return uids.Count == 0 ? null : new() { Uids = [..uids], Decay = [..decay] };
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (net.IsHost || Uids.Length != Decay.Length) {
            return;
        }

        for (var i = 0; i < Uids.Length; i++) {
            if (CardCache.Find(Uids[i]) is Thing { isDestroyed: false } thing) {
                thing.decay = Decay[i];
            }
        }
    }
}
