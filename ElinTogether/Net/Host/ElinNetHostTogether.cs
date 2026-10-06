using System.Linq;

namespace ElinTogether.Net;

internal partial class ElinNetHost
{
    /// <summary>
    ///     Council 10: every connected player is on the world map, on the host's or on its own copy of it. Then
    ///     only a jump of the date is everyone's (see RemoteTravelRegionPatch). A player still loading a map,
    ///     moving between two, or visiting another player is not travelling
    /// </summary>
    internal bool AllOnWorldMap()
    {
        if (_zone is not { IsRegion: true }) {
            return false;
        }

        foreach (var peer in Socket.Peers) {
            // on this map
            if (ActiveRemoteCharas.ContainsKey(peer.Id)) {
                continue;
            }

            // ponytail: a dead player away from the host still counts, the host is not told it died there
            if (!_departed.Contains(peer.Id) || _guests.ContainsKey(peer.Id) ||
                !_leases.TryGetValue(peer.Id, out var zones) || zones.Count == 0 ||
                zones.Keys.Any(uid => game.spatials.Find(uid) is not { IsRegion: true })) {
                return false;
            }
        }

        return true;
    }
}
