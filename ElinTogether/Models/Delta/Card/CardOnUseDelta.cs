using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CardOnUseDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Card { get; init; }

    [Key(1)]
    public required RemoteCard? RootCard { get; init; }

    [Key(2)]
    public required RemoteCard User { get; init; }

    /// <summary>
    ///     Used on a tile (an empty bottle at the water's edge)
    /// </summary>
    [Key(3)]
    public Position? Pos { get; init; }

    /// <summary>
    ///     Used on another card (a dye on a piece of furniture, meat on a grave)
    /// </summary>
    [Key(4)]
    public RemoteCard? Target { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Card.Find() is not { isDestroyed: false } card || User.Find() is not Chara user) {
            return;
        }

        if (RootCard?.Find() != card.GetRootCard()) {
            return;
        }

        // two players reaching for the same shrine: its power is given once
        if (net.IsHost && card.trait is TraitPowerStatue && !card.isOn) {
            return;
        }

        // on the host these give or change things for the user: its own doing, to be sent like any other
        if (Pos is not null) {
            Point pos = Pos!;
            if (net.IsHost && (!pos.IsValid || !card.trait.CanUse(user, pos))) {
                return;
            }

            Relay(net);
            using var _ = Simulate(net.IsHost);
            card.trait.OnUse(user, pos);
            return;
        }

        if (Target is not null) {
            if (Target.Find() is not { isDestroyed: false } target || (net.IsHost && !card.trait.CanUse(user, target))) {
                return;
            }

            Relay(net);
            using var _ = Simulate(net.IsHost);
            card.trait.OnUse(user, target);
            return;
        }

        Relay(net);
        card.trait.OnUse(user);
    }

    private void Relay(ElinNetBase net)
    {
        if (net.IsHost) {
            net.Delta.AddRemote(this);
        }
    }
}
