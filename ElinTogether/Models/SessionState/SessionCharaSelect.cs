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
