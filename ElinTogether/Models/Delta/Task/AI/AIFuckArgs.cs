using MessagePack;

namespace ElinTogether.Models.AI;

[MessagePackObject]
public class AIFuckArgs : TaskArgsBase
{
    [Key(0)]
    public required RemoteCard Target { get; init; }

    [Key(1)]
    public required AI_Fuck.FuckType Type { get; init; }

    // what the dialog or the ability set on the act: without them the host played "the plain one" to its end,
    // where the player pays again (a service already paid in the dialog, a free one, a vampire's bite)
    [Key(2)]
    public AI_Fuck.Variation Variation { get; init; }

    [Key(3)]
    public bool Sell { get; init; }

    [Key(4)]
    public bool Succubus { get; init; }

    public static AIFuckArgs Create(AI_Fuck ai)
    {
        return new() {
            Target = ai.target,
            Type = ai.Type,
            Variation = ai.variation,
            Sell = ai.sell,
            Succubus = ai.succubus,
        };
    }

    public override AIAct CreateSubAct()
    {
        if (Type == AI_Fuck.FuckType.fuck) {
            return new AI_Fuck {
                target = Target,
                variation = Variation,
                sell = Sell,
                succubus = Succubus,
            };
        }

        return new AI_TendAnimal {
            target = Target,
        };
    }
}