using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Own sleep (NetSessionRules.UseOwnSleep): a player away from the host map tells the host of the world that
///     it sleeps, or no longer does. The host does not see its character, and the night of the world passes when
///     every player sleeps, wherever they are
/// </summary>
[MessagePackObject]
public class SleepStateDelta : ElinDelta
{
    [Key(0)]
    public required bool Asleep { get; init; }

    /// <summary>
    ///     Hours of the night it starts, as its own game counts them
    /// </summary>
    [Key(1)]
    public int Hours { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        // away client -> host of the world only
        if (net is ElinNetHost { IsZoneSession: false } host && host.IsAwayPeer(OriginPeer)) {
            SleepSynchronizationContext.OnAwaySleep(OriginPeer, Asleep, Hours);
        }
    }
}
