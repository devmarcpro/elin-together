using System.Collections.Generic;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client, the characters this player has in this world, to pick one
/// </summary>
[MessagePackObject]
public class SessionCharaSelectRequest
{
    [Key(0)]
    public required List<SessionCharaEntry> Charas { get; init; }

    /// <summary>
    ///     The host lets players bring the character of one of their own saves
    /// </summary>
    [Key(1)]
    public bool AllowImport { get; init; }

    /// <summary>
    ///     Lang id of what to tell the player first, when its last answer was turned down
    /// </summary>
    [Key(2)]
    public string? Notice { get; init; }
}

[MessagePackObject]
public class SessionCharaEntry
{
    [Key(0)]
    public required int Uid { get; init; }

    /// <summary>
    ///     Name, race, job and level, as the host words them
    /// </summary>
    [Key(1)]
    public required string Label { get; init; }
}

/// <summary>
///     Net packet: Client -> Host
/// </summary>
[MessagePackObject]
public class SessionCharaSelectResponse
{
    /// <summary>
    ///     0 for a new character
    /// </summary>
    [Key(0)]
    public required int Uid { get; init; }
}

/// <summary>
///     Net packet: Client -> Host, the character of one of the player's own saves, to play in this world
/// </summary>
[MessagePackObject]
public class SessionCharaImportResponse
{
    [Key(0)]
    public required LZ4Bytes Chara { get; init; }

    [Key(1)]
    public required int Fame { get; init; }

    [Key(2)]
    public required int Karma { get; init; }

    /// <summary>
    ///     Which save it comes from: one copy of each per player
    /// </summary>
    [Key(3)]
    public required string Source { get; init; }
}
