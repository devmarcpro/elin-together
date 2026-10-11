namespace ElinTogether.Common;

public static class EmpLobbyData
{
    public const string EmpVersion = "EmpVersion";
    public const string GameBuild = "EmpGameBuild";
    public const string CurrentZone = "CurrentZone";

    /// <summary>
    ///     The mods of the game, see ModList.Compact
    /// </summary>
    public const string Mods = "EmpMods";

    /// <summary>
    ///     Which world this game hosts and how many times it was taken over: a former host of that world finds
    ///     the game that goes on (WorldHandover.Watch)
    /// </summary>
    public const string World = "EmpWorld";

    public const string Handover = "EmpHandover";
}