using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Chopping a log into planks: not sent, it only ran in the client's game, where the planks it makes are gone
///     at the end of the frame and the log is never used up
/// </summary>
[MessagePackObject]
public class TaskChopWoodArgs : TaskArgsBase
{
    [Key(0)]
    public required Position Pos { get; init; }

    public static TaskChopWoodArgs Create(TaskChopWood task)
    {
        return new() {
            Pos = task.pos,
        };
    }

    public override AIAct CreateSubAct()
    {
        return new TaskChopWood {
            pos = Pos,
        };
    }
}
