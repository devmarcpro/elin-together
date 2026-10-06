using MessagePack;

namespace ElinTogether.Models.AI;

/// <summary>
///     Practising on a training dummy or a restrained resident. Sent as an unknown task, the host answered the
///     progress of the player with "no matching act" and a cancel: the practice of a guest stopped at once <br />
///     The blows are struck in the game of the one who practises and replayed one by one (CharaActPerformDelta):
///     the copy made here strikes nothing, see <c>AIPracticeDummyPatch</c>
/// </summary>
[MessagePackObject]
public class AIPracticeDummyArgs : TaskArgsBase
{
    [Key(0)]
    public required RemoteCard Target { get; init; }

    public static AIPracticeDummyArgs Create(AI_PracticeDummy ai)
    {
        return new() {
            Target = ai.target,
        };
    }

    public override AIAct CreateSubAct()
    {
        if (Target.Find() is not { } target) {
            return new NoGoal();
        }

        return new AI_PracticeDummy {
            target = target,
        };
    }
}
