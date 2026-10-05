using ElinTogether.Models;
using ElinTogether.Net;

namespace ElinTogether.Patches;

/// <summary>
///     The names of the base and of the faction are set from boxes all over the game: they are compared with what
///     they were, as the story flags are, see <see cref="NameDelta" />
/// </summary>
internal static class NameWatch
{
    private static int _zone = -1;
    private static string? _zoneName;
    private static string? _home;

    /// <summary>
    ///     What is there now is known to everyone (it just came from someone else)
    /// </summary>
    internal static void Accept()
    {
        _zone = EClass._zone?.uid ?? -1;
        _zoneName = EClass._zone?.name;
        _home = EClass.Home?.name;
    }

    internal static void Update()
    {
        if (EClass._zone is not { } zone || NetSession.Instance.Connection is not { } connection) {
            return;
        }

        if (zone.uid != _zone) {
            _zone = zone.uid;
            _zoneName = zone.name;
        } else if (zone.name != _zoneName) {
            _zoneName = zone.name;
            if (zone.IsPCFaction) {
                RemoteBasePaidPatch.WarnHostOnly();
                connection.Delta.AddRemote(new NameDelta {
                    Kind = NameDelta.OfZone,
                    ZoneUid = zone.uid,
                    Name = zone.name,
                });
            }
        }

        var home = EClass.Home?.name;
        if (_home is null) {
            _home = home;
        } else if (home != _home) {
            _home = home;
            RemoteBasePaidPatch.WarnHostOnly();
            connection.Delta.AddRemote(new NameDelta {
                Kind = NameDelta.OfFaction,
                Name = home,
            });
        }
    }
}
