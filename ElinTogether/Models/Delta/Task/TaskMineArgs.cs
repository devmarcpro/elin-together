using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class TaskMineArgs : TaskArgsBase
{
    [Key(0)]
    public required Position Pos { get; init; }

    // what the build mode's "ramp" button sets on the task
    [Key(1)]
    public TaskMine.Mode Mode { get; init; }

    [Key(2)]
    public int Ramp { get; init; }

    public static TaskMineArgs Create(TaskMine task)
    {
        return new() {
            Pos = task.pos,
            Mode = task.mode,
            Ramp = task.ramp,
        };
    }

    public override AIAct CreateSubAct()
    {
        return new TaskMine {
            id = ABILITY.TaskMine,
            pos = Pos,
            mode = Mode,
            ramp = Ramp,
        };
    }
}