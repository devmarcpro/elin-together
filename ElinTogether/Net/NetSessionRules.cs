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

    /// <summary>
    ///     Two players next to each other can trade items and gold through a window both confirm
    /// </summary>
    [Key(7)]
    public bool AllowPlayerTrade { get; set; }

    /// <summary>
    ///     The turns of a player's own character follow the clock of its own game, not the host's game time as
    ///     the network brings it. Only means something with <see cref="UsePlayerCombatTime" />: without it the
    ///     world runs on the host's clock and a guest on its own would act out of step with it
    /// </summary>
    [Key(8)]
    public bool UsePlayerClock { get; set; }

    [IgnoreMember]
    internal bool OwnClock => UsePlayerClock && UsePlayerCombatTime;

    /// <summary>
    ///     A player's own turn always lasts the base act time, as in a solo game, instead of being stretched or
    ///     shortened by the speed of the other players. Only with <see cref="UsePlayerCombatTime" />, which keeps
    ///     speed meaningful in a fight: what fights a player gets time for each of its turns
    /// </summary>
    [Key(9)]
    public bool UsePlayerStepPace { get; set; }

    [IgnoreMember]
    internal bool OwnPace => UsePlayerStepPace && UsePlayerCombatTime;

    /// <summary>
    ///     One date for the world, whoever makes time pass: a player alone on a map it simulates no longer has
    ///     a date of its own that the host's replaces when it comes back. The most advanced date is the world's
    /// </summary>
    [Key(10)]
    public bool UseSharedWorldTime { get; set; }

    public static NetSessionRules Default => new() {
        UseSharedSpeed = EmpConfig.Server.SharedAverageSpeed.Value,
        UseTurnBasedCombat = EmpConfig.Server.TurnBasedCombat.Value,
        AllowIndependentTravel = EmpConfig.Server.IndependentTravel.Value,
        TravelCheckpointSeconds = EmpConfig.Server.TravelCheckpointSeconds.Value,
        UsePlayerShipping = EmpConfig.Server.PlayerShipping.Value,
        UsePlayerCombatTime = EmpConfig.Server.PlayerCombatTime.Value,
        UsePersonalQuests = EmpConfig.Server.PersonalQuests.Value,
        AllowPlayerTrade = EmpConfig.Server.PlayerTrade.Value,
        UsePlayerClock = EmpConfig.Server.PlayerClock.Value,
        UsePlayerStepPace = EmpConfig.Server.PlayerStepPace.Value,
        UseSharedWorldTime = EmpConfig.Server.SharedWorldTime.Value,
    };
}