using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Cards put in the codex (Num below zero: taken out). The codex is the world's, one for everyone like the
///     recipes: it lives in the Player object, which a guest gets again from the host at every world copy. What a
///     guest collected only counted in its own copy and was gone at the next one
/// </summary>
[MessagePackObject]
public class CodexCardDelta : ElinDelta
{
    [Key(0)]
    public required string Id { get; init; }

    [Key(1)]
    public required int Num { get; init; }

    /// <summary>
    ///     Passed on by a player who keeps a map for visitors: its visitors know already
    /// </summary>
    [Key(2)]
    public bool Relayed { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (string.IsNullOrEmpty(Id) || Num == 0 || Num is > 9999 or < -9999 || player?.codex is not { } codex) {
            return;
        }

        // never below zero: two players took the last card out at the same moment
        var creature = codex.GetOrCreate(Id);
        creature.numCard = System.Math.Max(0, creature.numCard + Num);

        switch (net) {
            // the game that keeps a map for visitors: they hear it from here, the world from its own link
            case ElinNetHost { IsZoneSession: true } zone:
                zone.SendDeltaToAllExcept(OriginPeer, this);
                if (NetSession.Instance.Transport is ElinNetClient main) {
                    main.SendWhileAway(new CodexCardDelta { Id = Id, Num = Num, Relayed = true });
                }

                break;
            // the players of that map heard it there already: the others, on this map, hear it now; those alone
            // elsewhere get the codex with their next world copy
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
    }
}
