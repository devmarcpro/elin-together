using ElinTogether.Net;
using HarmonyLib;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A trolley (a cart, a boat, a wheelchair on rails) carries its rider along the rails: the rider's steps are
///     shared, the trolley's were not, and it stayed where it started in the other games (diff_suite, a guest's ride
///     at Vernis, 2026-10-23). The game where it moves sends where it is and where it faces, every game that has that
///     map puts it there
/// </summary>
[MessagePackObject]
public class TrolleyDelta : ElinDelta
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    [Key(1)]
    public required int Uid { get; init; }

    [Key(2)]
    public required int X { get; init; }

    [Key(3)]
    public required int Z { get; init; }

    [Key(4)]
    public required int Dir { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        // (a trolley on a tile of this map, nothing else: checked before it goes further when this game has the map;
        // a map two guests share without the host goes on as it came)
        Point to = new(X, Z);
        var here = EClass._zone?.uid == ZoneUid;
        var trolley = here && to.IsValid && to.IsInBounds
            ? EClass._map.things.Find(t => t.uid == Uid && t.trait is TraitTrolley)
            : null;
        if (here && trolley is null) {
            return;
        }

        if (net is ElinNetHost host) {
            host.SendDeltaToAllExcept(OriginPeer, this);
        }

        if (trolley is null) {
            return;
        }

        trolley.dir = Dir;
        trolley.MoveImmediate(to);
    }

    [HarmonyPatch(typeof(Card), nameof(Card.MoveImmediate))]
    internal static class MovePatch
    {
        [HarmonyPostfix]
        internal static void OnMoveImmediate(Card __instance)
        {
            if (IsApplying || __instance is not Thing { trait: TraitTrolley } trolley ||
                NetSession.Instance.Connection is not { } connection || EClass._zone is not { } zone) {
                return;
            }

            connection.Delta.AddRemote(new TrolleyDelta {
                ZoneUid = zone.uid,
                Uid = trolley.uid,
                X = trolley.pos.x,
                Z = trolley.pos.z,
                Dir = trolley.dir,
            });
        }
    }
}
