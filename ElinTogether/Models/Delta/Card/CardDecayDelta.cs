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
