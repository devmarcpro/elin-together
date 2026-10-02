using MessagePack;

namespace ElinTogether.Models.AI;

/// <summary>
///     Resting and meditating, see AIPassTimePatch
/// </summary>
[MessagePackObject]
public class AIPassTimeArgs : TaskArgsBase
{
    [Key(0)]
    public required bool Meditate { get; init; }

    /// <summary>
    ///     The bed rested on, if any
    /// </summary>
    [Key(1)]
    public required RemoteCard? Target { get; init; }

    public static AIPassTimeArgs Create(AI_PassTime ai)
    {
        return new() {
            Meditate = ai.type == AI_PassTime.Type.meditate,
            Target = ai.target,
        };
    }

    public override AIAct CreateSubAct()
    {
        var ai = Meditate ? new AI_Meditate() : new AI_PassTime();
        ai.target = Target;
        return ai;
    }
}
