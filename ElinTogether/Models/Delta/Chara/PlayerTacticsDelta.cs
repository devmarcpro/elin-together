using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     "Keep distance", a setting of each player's own game that the game reads in "the game": the companions of
///     another player are run where the map is simulated, with the setting of whoever simulates it. A player tells
///     that game its own, kept on its character there
/// </summary>
[MessagePackObject]
public class PlayerTacticsDelta : ElinDelta
{
    public const string TacticsKey = "emp_tactics";

    [Key(0)]
    public required bool AllyKeepDistance { get; init; }

    /// <summary>
    ///     What that player asked of its companions, null when it never said (the simulating game's own then)
    /// </summary>
    internal static bool? KeepDistanceOf(Chara player)
    {
        return player.GetInt(TacticsKey) switch {
            0 => null,
            var value => value == 2,
        };
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host && host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var player)) {
            player.SetInt(TacticsKey, AllyKeepDistance ? 2 : 1);
        }
    }
}
