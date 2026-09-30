using MessagePack;

namespace ElinTogether.Net;

[MessagePackObject]
public class NetSessionRules
{
    [Key(0)]
    public required bool UseSharedSpeed { get; set; }

    [Key(1)]
    public required bool UseTurnBasedCombat { get; set; }

    [Key(2)]
    public bool AllowIndependentTravel { get; set; }

    /// <summary>
    ///     Seconds between two checkpoints of an away client, 0 disables them
    /// </summary>
    [Key(3)]
    public int TravelCheckpointSeconds { get; set; }

    public static NetSessionRules Default => new() {
        UseSharedSpeed = EmpConfig.Server.SharedAverageSpeed.Value,
        UseTurnBasedCombat = EmpConfig.Server.TurnBasedCombat.Value,
        AllowIndependentTravel = EmpConfig.Server.IndependentTravel.Value,
        TravelCheckpointSeconds = EmpConfig.Server.TravelCheckpointSeconds.Value,
    };
}