using System.Collections.Immutable;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client
/// </summary>
[MessagePackObject]
public class SessionPlayersSnapshot
{
    [Key(0)]
    public required ImmutableArray<NetPeerState> Current { get; init; }

    /// <summary>
    ///     The map of the sender as it holds it, for the players standing on it, see <see cref="NetDesync" />
    /// </summary>
    [Key(1)]
    public MapSums? Sums { get; init; }

    public static SessionPlayersSnapshot Create()
    {
        return new() {
            Current = [..NetSession.Instance.CurrentPlayers],
            // nobody to compare with while alone
            Sums = NetSession.Instance.CurrentPlayers.Count > 1 ? NetDesync.Collect() : null,
        };
    }

    public void Apply()
    {
        var session = NetSession.Instance;
        session.CurrentPlayers.Clear();
        session.CurrentPlayers.AddRange(Current);

        // resolve self state
        session.Self =
            session.CurrentPlayers.Find(n => session.Player is { } player && n.CharaUid == player.uid) ??
            session.CurrentPlayers.Find(n => n.User.IsMe);

        NetDesync.Compare(Sums);
    }
}