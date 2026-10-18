using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A guest cast the gate spell: its companions come along (Card.Teleport in its game), but the host runs the map and
///     its copy of them stayed behind. The guest asks the host to bring each of its own companions where they went
/// </summary>
[MessagePackObject]
public class GateFollowDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Chara { get; init; }

    [Key(1)]
    public required int X { get; init; }

    [Key(2)]
    public required int Z { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        // only the host, for the companions of the one who asks, on a map it runs
        if (net is not ElinNetHost host || !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) ||
            Chara.Find() is not global::Chara { ExistsOnMap: true } companion || companion == sender || CompanionHelper.OwnerOf(companion) != sender) {
            return;
        }

        var point = new Point(X, Z);
        if (point.IsValid) {
            companion.Teleport(point);
        }
    }
}
