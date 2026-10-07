using System.Runtime.CompilerServices;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class FakeTask : TaskArgsBase
{
    // the acts of this game's player that went out as FakeTask: the host has no copy of them that runs
    private static readonly ConditionalWeakTable<AIAct, object> _sent = new();

    public static FakeTask Default => field ??= new();

    public override AIAct CreateSubAct()
    {
        return new NoGoal();
    }

    internal static void Mark(AIAct act)
    {
        _sent.GetOrCreateValue(act);
    }

    // the acts started under a FakeTask one that the keeper was told to run for themselves, see
    // CharaTaskRemoteEvent.OnSetChild
    private static readonly ConditionalWeakTable<AIAct, object> _real = new();

    internal static void MarkReal(AIAct act)
    {
        _real.GetOrCreateValue(act);
    }

    internal static bool IsReal(AIAct act)
    {
        return _real.TryGetValue(act, out _);
    }

    /// <summary>
    ///     Whether this act, or the act it runs under, went out as FakeTask. Such a task is run and stopped by this game
    ///     alone: the host has nothing to match its progress with, and nothing to relay its stop
    /// </summary>
    internal static bool IsMarked(AIAct? act)
    {
        for (; act is not null; act = act.parent) {
            // told to the keeper for itself, whatever it runs under
            if (_real.TryGetValue(act, out _)) {
                return false;
            }

            if (_sent.TryGetValue(act, out _)) {
                return true;
            }
        }

        return false;
    }
}
