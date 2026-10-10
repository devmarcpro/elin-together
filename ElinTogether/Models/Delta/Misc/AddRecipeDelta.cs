using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class AddRecipeDelta : ElinDelta
{
    [Key(0)]
    public required string RecipeId { get; init; }

    /// <summary>
    ///     Passed on by a player who keeps a map, alone or for visitors: those of that map know already
    /// </summary>
    [Key(1)]
    public bool Relayed { get; init; }

    /// <summary>
    ///     True while a recipe that came from someone else is being learnt here
    /// </summary>
    internal static bool IsLanding { get; private set; }

    protected override void OnApply(ElinNetBase net)
    {
        // never back to the player it came from, never twice to anyone: learning a known recipe again counts
        // it twice
        switch (net) {
            // the game that keeps a map for visitors: they hear it from here, the world from its own link
            case ElinNetHost { IsZoneSession: true } zone:
                zone.SendDeltaToAllExcept(OriginPeer, this);
                if (NetSession.Instance.Transport is ElinNetClient main) {
                    main.SendWhileAway(new AddRecipeDelta { RecipeId = RecipeId, Relayed = true });
                }

                break;
            // the players of that map know already: the others, on this map, hear it now; those alone elsewhere
            // get the recipes with their next world copy
            case ElinNetHost host when Relayed:
                foreach (var peer in host.ActiveRemoteCharas.Keys) {
                    if (peer != OriginPeer && !host.IsAwayPeer(peer)) {
                        host.SendDeltaTo(peer, this);
                    }
                }

                break;
            case ElinNetHost host:
                host.SendDeltaToAllExcept(OriginPeer, this);
                break;
        }

        IsLanding = true;
        try {
            player.recipes.Add(RecipeId, !player.recipes.IsKnown(RecipeId));
        } finally {
            IsLanding = false;
        }
    }
}
