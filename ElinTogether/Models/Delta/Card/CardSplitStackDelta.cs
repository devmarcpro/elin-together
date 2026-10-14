using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A guest splits a stack with the game's split menu: the game splits off what STAYS (a new stack put back in
///     the bag, apart) and carries away the stack itself, now smaller. On a guest nothing changes a stack's count
///     by itself (the host does): the stack it then dropped, or put in a chest, left whole, and the part it kept
///     was a copy only its own game had, gone later. Medals laid on the floor by a guest "vanished" (player
///     report, 2026-10-14). <br />
///     The host makes that split for it: the stack gets smaller everywhere, the part kept is a stack of the world,
///     bound to the number the guest gave it, so what the guest does next with either finds them
/// </summary>
[MessagePackObject]
public class CardSplitStackDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Source { get; init; }

    [Key(1)]
    public required RemoteCard Parent { get; init; }

    /// <summary>
    ///     How many stay apart, in the new stack
    /// </summary>
    [Key(2)]
    public required int Num { get; init; }

    /// <summary>
    ///     The number the guest gave the new stack
    /// </summary>
    [Key(3)]
    public required int Pending { get; init; }

    /// <summary>
    ///     The host's answer to the guest who split: the number of the new stack in the world, which its own copy
    ///     takes (dropped later, the guest saw it twice: its copy and the host's)
    /// </summary>
    [Key(4)]
    public int Real { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host) {
            if (Real > 0 && pc?.things.List(t => t.uid == Pending, true).FirstOrDefault() is { } copy) {
                CardCache.Rebind(copy, Real);
            }

            return;
        }

        if (Source.Find() is not Thing { isDestroyed: false } source || Parent.Find() is not { isDestroyed: false } parent ||
            source.parent != parent || Num <= 0 || Num >= source.Num ||
            source.GetRootCard() is not Chara { IsPlayer: true } holder || holder != host.ActiveRemoteCharas.GetValueOrDefault(OriginPeer)) {
            EmpLog.Warning("Split of {Uid} for peer {Peer} refused (gone, moved, or not that player's)", Source.Uid, OriginPeer);
            return;
        }

        // the smaller stack is told to everyone (ModNum is the host's own gesture); the new stack to the others
        // only: the guest has it already, under its own number, which the host now knows it by
        var kept = source.Split(Num);
        parent.AddThing(kept, false);
        PendingRebind.Bind(Pending, kept.uid);
        host.SendDeltaToAllExcept(OriginPeer, new CardAddThingDelta {
            Thing = RemoteCard.Create(kept, true, true)!,
            Parent = parent,
            TryStack = false,
            DestInvX = -1,
            DestInvY = -1,
        });
        host.SendDeltaTo(OriginPeer, new CardSplitStackDelta {
            Source = source,
            Parent = parent,
            Num = Num,
            Pending = Pending,
            Real = kept.uid,
        });
        EmpLog.Debug("Split {Uid} for peer {Peer}: {Num} kept apart as {Kept} (its {Pending})", source.uid, OriginPeer, Num, kept.uid, Pending);
    }
}
