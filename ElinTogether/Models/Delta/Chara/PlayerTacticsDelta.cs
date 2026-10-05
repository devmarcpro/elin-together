using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     "Keep distance" and "don't wander", settings of each player's own game that the game reads in "the game": the companions of
///     another player are run where the map is simulated, with the setting of whoever simulates it. A player tells
///     that game its own, kept on its character there
/// </summary>
[MessagePackObject]
public class PlayerTacticsDelta : ElinDelta
{
    public const string TacticsKey = "emp_tactics";

    [Key(0)]
    public required bool AllyKeepDistance { get; init; }

    [Key(1)]
    public bool DontWander { get; init; }

    /// <summary>
    ///     What that player asked of its companions, null when it never said (the simulating game's own then)
    /// </summary>
    internal static bool? KeepDistanceOf(Chara player)
    {
        return player.GetInt(TacticsKey) is > 0 and var value ? ((value - 1) & 1) != 0 : null;
    }

    internal static bool? DontWanderOf(Chara player)
    {
        return player.GetInt(TacticsKey) is > 0 and var value ? ((value - 1) & 2) != 0 : null;
    }

    protected override void OnApply(ElinNetBase net)
    {
        // 0 is "never said": the two boxes are kept above it
        if (net is ElinNetHost host && host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var player)) {
            player.SetInt(TacticsKey, 1 + (AllyKeepDistance ? 1 : 0) + (DontWander ? 2 : 0));
        }
    }
}
