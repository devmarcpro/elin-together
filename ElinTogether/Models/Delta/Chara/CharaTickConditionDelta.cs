using System;
using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaTickConditionDelta : ElinDelta
{
    private const int MaxCount = 1000;

    // ticks counted during a step on the world map, see Emit
    private static readonly Dictionary<Chara, int> _step = [];

    [Key(0)]
    public required RemoteCard Owner { get; init; }

    /// <summary>
    ///     How many times the conditions are ticked: a step on the world map plays about 120 turns
    /// </summary>
    [Key(1)]
    public int Count { get; set; } = 1;

    /// <summary>
    ///     Tells the others that <paramref name="chara" /> ticked its conditions once. During a step on the world
    ///     map the ticks are only counted, <see cref="FlushStep" /> sends them as one message per character
    /// </summary>
    internal static void Emit(ElinNetBase net, Chara chara)
    {
        if (RemoteTravelRegionPatch.IsPayingStep) {
            _step[chara] = _step.GetValueOrDefault(chara) + 1;
            return;
        }

        net.Delta.AddRemote(new CharaTickConditionDelta {
            Owner = chara,
        });
    }

    /// <summary>
    ///     The step ended (or threw): what it counted goes out
    /// </summary>
    internal static void FlushStep(ElinNetBase? net)
    {
        if (_step.Count == 0) {
            return;
        }

        if (net is not null) {
            foreach (var (chara, count) in _step) {
                net.Delta.AddRemote(new CharaTickConditionDelta {
                    Owner = chara,
                    Count = count,
                });
            }
        }

        _step.Clear();
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Owner.Find() is not Chara { IsPC: false } chara) {
            return;
        }

        if (!chara.IsInActiveMap) {
            return;
        }

        if (net.IsHost) {
            net.Delta.AddRemote(this);
        }

        // a count off the wire is never trusted for a loop; the game's own step skips the dead
        for (var i = Math.Clamp(Count, 1, MaxCount); i > 0; i--) {
            chara.Stub_TickConditions();

            if (chara.isDead) {
                break;
            }
        }
    }
}
