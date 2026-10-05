using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A build of the build mode's menu (no held item): the recipe as the game saves it with a designation, its
///     ingredients by uid
/// </summary>
[MessagePackObject]
public class TaskBuildArgs : TaskArgsBase
{
    [Key(0)]
    public required Position Pos { get; init; }

    [Key(1)]
    public required LZ4Bytes Recipe { get; init; }

    [Key(2)]
    public required int Dir { get; init; }

    [Key(3)]
    public required int Altitude { get; init; }

    [Key(4)]
    public required int BridgeHeight { get; init; }

    // the look picked in the menu, which the game does not save with the recipe
    [Key(5)]
    public int IdSkin { get; init; }

    public static TaskBuildArgs Create(TaskBuild task)
    {
        return new() {
            Pos = task.pos,
            Recipe = LZ4Bytes.Create(task.recipe),
            Dir = task.dir,
            Altitude = task.altitude,
            BridgeHeight = task.bridgeHeight,
            IdSkin = task.recipe.idSkin,
        };
    }

    public override AIAct CreateSubAct()
    {
        var recipe = Recipe.Decompress<Recipe>();
        if (recipe is null) {
            return null!;
        }

        recipe._dir = Dir;
        recipe.idSkin = IdSkin;
        return new TaskBuild {
            recipe = recipe,
            pos = Pos,
            dir = Dir,
            altitude = Altitude,
            bridgeHeight = BridgeHeight,
        };
    }
}
