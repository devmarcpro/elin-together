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

    /// <summary>
    ///     Every player is paid for its own goods in the shipping box, otherwise the host gets everything
    /// </summary>
    [Key(4)]
    public bool UsePlayerShipping { get; set; }

    /// <summary>
    ///     What fights a player only acts on that player's turns, see PlayerCombatTime
    /// </summary>
    [Key(5)]
    public bool UsePlayerCombatTime { get; set; }

    /// <summary>
    ///     Random quests (from residents and boards) and what they earn, fame and karma, belong to the player who
    ///     takes them; story quests stay everyone's. Off: one quest log and one fame for the whole group
    /// </summary>
    [Key(6)]
    public bool UsePersonalQuests { get; set; }

    public static NetSessionRules Default => new() {
        UseSharedSpeed = EmpConfig.Server.SharedAverageSpeed.Value,
        UseTurnBasedCombat = EmpConfig.Server.TurnBasedCombat.Value,
        AllowIndependentTravel = EmpConfig.Server.IndependentTravel.Value,
        TravelCheckpointSeconds = EmpConfig.Server.TravelCheckpointSeconds.Value,
        UsePlayerShipping = EmpConfig.Server.PlayerShipping.Value,
        UsePlayerCombatTime = EmpConfig.Server.PlayerCombatTime.Value,
        UsePersonalQuests = EmpConfig.Server.PersonalQuests.Value,
    };
}