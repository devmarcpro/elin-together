using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models.AI;

[MessagePackObject]
public class AIEatArgs : TaskArgsBase
{
    [Key(0)]
    public required RemoteCard? Target { get; init; }

    [Key(1)]
    public required bool Cook { get; init; }

    /// <summary>
    ///     Full in its own game: the local player then stops and keeps the food. The host plays another player's
    ///     meal as a resident's, who eats anyway: the food was used up for nothing
    /// </summary>
    [Key(2)]
    public bool Full { get; init; }

    public static AIEatArgs Create(AI_Eat ai, Chara owner)
    {
        var food = ai.target ?? owner.held;
        return new() {
            Target = PendingSplit.Split(food),
            Cook = ai.cook,
            Full = owner.IsPC && owner.hunger.GetPhase() == 0 && !EClass.debug.godFood &&
                   !(EClass._zone.HasField(10001) && food is not null && food.GetBool(128)),
        };
    }

    public override AIAct CreateSubAct()
    {
        var eat = new AI_Eat {
            target = Target,
            cook = Cook,
        };

        if (Full) {
            AIEatPatch.MarkFull(eat);
        }

        return eat;
    }
}
