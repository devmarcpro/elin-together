using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Host to the player whose craft it ran: its first craft of that recipe got its bonus, its game notes the
///     recipe as made (the list is the player's own, the host never touches its own for someone else)
/// </summary>
[MessagePackObject]
public class CraftFirstTimeDelta : ElinDelta
{
    [Key(0)]
    public required string RecipeId { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost) {
            return;
        }

        player.recipes.craftedRecipes.Add(RecipeId);
    }
}
