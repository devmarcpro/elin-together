using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class AddRecipeDelta : ElinDelta
{
    [Key(0)]
    public required string RecipeId { get; init; }

    /// <summary>
    ///     True while a recipe that came from someone else is being learnt here
    /// </summary>
    internal static bool IsLanding { get; private set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net.IsHost) {
            net.Delta.AddRemote(this);
        }

        IsLanding = true;
        try {
            player.recipes.Add(RecipeId, !player.recipes.IsKnown(RecipeId));
        } finally {
            IsLanding = false;
        }
    }
}
