using MessagePack;

namespace ElinTogether.Models.AI;

[MessagePackObject]
public class AIOpenGambleChestArgs : TaskArgsBase
{
    [Key(0)]
    public required RemoteCard Target { get; init; }

    public static AIOpenGambleChestArgs Create(AI_OpenGambleChest ai)
    {
        return new() {
            Target = ai.target,
        };
    }

    public override AIAct CreateSubAct()
    {
        return new AI_OpenGambleChest {
            target = Target,
        };
    }
}
