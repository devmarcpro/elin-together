using System.Linq;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A creature broke through a wall or an obstacle on the map of whoever simulates it (dungeon bosses, big
///     monsters). Terrain has no delta of its own: without this the others kept the wall and saw the creature
///     walk through it
/// </summary>
[MessagePackObject]
public class CharaDestroyPathDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required Position Pos { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        // only ever told by the one simulating the map
        if (net.IsHost || Owner.Find() is not Chara chara) {
            return;
        }

        Point pos = Pos;
        var known = _map.things.Count;
        var broke = false;

        // the terrain half of Chara.DestroyPath: doors and furniture in the way have their own deltas
        pos.ForeachMultiSize(chara.W, chara.H, (p, _) => {
            if (!p.IsValid) {
                return;
            }

            if (p.HasBlock) {
                _map.MineBlock(p, false, chara);
                if (p.HasObj) {
                    _map.MineObj(p, null, chara);
                }

                broke = true;
            }

            if (p.HasObj && p.IsBlocked) {
                _map.MineObj(p, null, chara);
                broke = true;
            }
        });

        // what an ally breaks drops things: the real ones come from the simulating side
        foreach (var made in _map.things.Skip(known).ToList()) {
            CardCache.DelayDestroy(made);
        }

        if (broke) {
            Msg.Say("stomp");
            Shaker.ShakeCam("stomp");
        }
    }
}
