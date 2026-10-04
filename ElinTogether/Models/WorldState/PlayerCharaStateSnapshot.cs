using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class PlayerCharaStateSnapshot
{
    [Key(0)]
    public required int LastAct { get; init; }

    [Key(2)]
    public required int LastReceivedTick { get; init; }

    [Key(3)]
    public required int Speed { get; init; }

    /// <summary>
    ///     The player is fast-forwarding its own game (running, holding Shift): on its own clock the host
    ///     does not see it otherwise, and the world must speed up with it as it does for the host
    /// </summary>
    [Key(4)]
    public bool Turbo { get; init; }
}