using System;

namespace ElinTogether.Net;

/// <summary>
///     Whether another player exists in this world. A host alone in its session lives the single player game: what
///     the mod changes only matters once there is somebody to agree with <br />
///     Read only, it looks at what the session already keeps. A player counts from the first moment of its
///     connection (connecting, choosing a character) to the last, also on another map: a guest travelling alone
///     leaves <c>CurrentPlayers</c> but stays a peer, so <c>CurrentPlayers.Count</c> alone is not the question, and
///     a connected peer is not always on this map either <br />
///     Alone in an away zone (no connection) there is nobody: the game runs as single player there
/// </summary>
internal static class NetCompany
{
    // the peers' state is asked from Steam: hot paths (every skill read) look at most this often. A player is
    // only missed for that long, the one who arrives gets the whole state when it is ready, not before
    private const int RefreshMs = 50;

    private static ElinNetBase? _of;
    private static int _at;
    private static bool _peers;

    public static bool HasCompany {
        get {
            var session = NetSession.Instance;
            if (session.Connection is not { } connection) {
                return false;
            }

            // the host, or the one simulating the zone visited, is another player
            if (connection.IsClient || session.CurrentPlayers.Count > 1) {
                return true;
            }

            var now = Environment.TickCount;
            if (_of != connection || unchecked(now - _at) >= RefreshMs) {
                _of = connection;
                _at = now;
                _peers = connection.IsConnected;
            }

            return _peers;
        }
    }
}
