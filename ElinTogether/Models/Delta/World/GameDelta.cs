using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class GameDelta : ElinDelta
{
    [Key(0)]
    public required float Delta { get; init; }

    /// <summary>
    ///     The host's fast-forward factor, 0 for none: a player on its own clock follows it
    /// </summary>
    [Key(1)]
    public float Turbo { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        SynchronizationContext.GameDelta += Delta;
        GameSynchronizationContext.OnHostTurbo(Turbo);
    }
}