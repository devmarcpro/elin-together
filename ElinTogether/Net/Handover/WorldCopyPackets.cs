using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client <br />
///     What the host's save folder holds after a save. The guest answers with the files it lacks
///     (<see cref="WorldCopyWant" />). Also written as copy.json in a copy once it is whole and checked
/// </summary>
[MessagePackObject]
public class WorldCopyManifest
{
    /// <summary>
    ///     Save id of the world at the host
    /// </summary>
    [Key(0)]
    public string World { get; set; } = "";

    [Key(1)]
    public ulong Host { get; set; }

    /// <summary>
    ///     How many times the world was taken over by another player, see ElinNetHost.HandoverNumber
    /// </summary>
    [Key(2)]
    public int Handover { get; set; }

    /// <summary>
    ///     When the host saved (UTC ticks of its clock): names the save in the packets that follow
    /// </summary>
    [Key(3)]
    public long Saved { get; set; }

    [Key(4)]
    public WorldCopyFile[] Files { get; set; } = [];
}

[MessagePackObject]
public class WorldCopyFile
{
    /// <summary>
    ///     Relative to the save folder, with '/'
    /// </summary>
    [Key(0)]
    public string Path { get; set; } = "";

    [Key(1)]
    public long Size { get; set; }

    /// <summary>
    ///     SHA-256, lower case hex
    /// </summary>
    [Key(2)]
    public string Hash { get; set; } = "";
}

/// <summary>
///     Net packet: Client -> Host <br />
///     The files of that save the guest does not have yet, by their index in the manifest
/// </summary>
[MessagePackObject]
public class WorldCopyWant
{
    [Key(0)]
    public long Saved { get; set; }

    [Key(1)]
    public int[] Files { get; set; } = [];
}

/// <summary>
///     Net packet: Host -> Client <br />
///     A small part of one file, the files and their parts come in order
/// </summary>
[MessagePackObject]
public class WorldCopyPiece
{
    [Key(0)]
    public long Saved { get; set; }

    [Key(1)]
    public int File { get; set; }

    [Key(2)]
    public long Offset { get; set; }

    [Key(3)]
    public byte[] Data { get; set; } = [];
}
