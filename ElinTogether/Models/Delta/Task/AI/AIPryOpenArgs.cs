using MessagePack;

namespace ElinTogether.Models.AI;

[MessagePackObject]
public class AIPryOpenArgs : TaskArgsBase
{
    [Key(0)]
    public required RemoteCard Target { get; init; }

    public static AIPryOpenArgs Create(AI_PryOpen ai)
    {
        return new() {
            Target = ai.target,
        };
    }

    public override AIAct CreateSubAct()
    {
        return new AI_PryOpen {
            target = Target,
        };
    }
}