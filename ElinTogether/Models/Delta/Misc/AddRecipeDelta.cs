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
        // not back to the player it came from: learning a known recipe again counts it twice
        if (net is ElinNetHost host) {
            host.SendDeltaToAllExcept(OriginPeer, this);
        }

        IsLanding = true;
        try {
            player.recipes.Add(RecipeId, !player.recipes.IsKnown(RecipeId));
        } finally {
            IsLanding = false;
        }
    }
}
