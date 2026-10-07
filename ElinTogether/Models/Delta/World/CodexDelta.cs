using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

public enum CodexKind : byte
{
    /// <summary>
    ///     Cards put in the codex (Num below zero: taken out)
    /// </summary>
    Card,

    Kill,
    Weakspot,
    Spawn,

    /// <summary>
    ///     This creature gave its card once
    /// </summary>
    CardDrop,
}

/// <summary>
///     The codex is the world's, one for everyone like the recipes: it lives in the Player object, which a guest
///     gets again from the host at every world copy. What a guest collected, killed or learnt only counted in its
///     own copy and was gone at the next one. Who tells whom: see CodexPatch
/// </summary>
[MessagePackObject]
public class CodexDelta : ElinDelta
{
    [Key(0)]
    public required string Id { get; init; }

    [Key(1)]
    public required int Num { get; init; }

    /// <summary>
    ///     Passed on by a player who keeps a map, alone or for visitors: those of that map know already
    /// </summary>
    [Key(2)]
    public bool Relayed { get; init; }

    [Key(3)]
    public CodexKind Kind { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (string.IsNullOrEmpty(Id) || Num == 0 || Num is > 9999 or < -9999 || player?.codex is not { } codex) {
            return;
        }

        var creature = codex.GetOrCreate(Id);
        switch (Kind) {
            case CodexKind.Card:
                // never below zero: two players took the last card out at the same moment
                creature.numCard = System.Math.Max(0, creature.numCard + Num);
                break;
            case CodexKind.Kill:
                creature.kills = System.Math.Max(0, creature.kills + Num);
                break;
            case CodexKind.Weakspot:
                creature.weakspot = System.Math.Max(0, creature.weakspot + Num);
                break;
            case CodexKind.Spawn:
                creature.spawns = System.Math.Max(0, creature.spawns + Num);
                break;
            case CodexKind.CardDrop:
                creature.droppedCard = true;
                break;
            default:
                return;
        }

        switch (net) {
            // the game that keeps a map for visitors: they hear it from here (not a kill: they saw it, the blow
            // was played again in their game), the world from its own link
            case ElinNetHost { IsZoneSession: true } zone:
                if (Kind != CodexKind.Kill) {
                    zone.SendDeltaToAllExcept(OriginPeer, this);
                }

                if (NetSession.Instance.Transport is ElinNetClient main) {
                    main.SendWhileAway(new CodexDelta { Id = Id, Num = Num, Kind = Kind, Relayed = true });
                }

                break;
            // the players of that map know already: the others, on this map, hear it now; those alone elsewhere
            // get the codex with their next world copy
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
