using System.Collections.Immutable;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A player who simulates a map away from the host tells the date its own game reached. The world has one
///     date: the most advanced one. The host catches up and tells everyone, see <see cref="WorldDateAdvanceDelta" />
/// </summary>
[MessagePackObject]
public class WorldTimeReportDelta : ElinDelta
{
    [Key(0)]
    public required ImmutableArray<int> GameDate { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost || !NetSession.Instance.Rules.UseSharedWorldTime) {
            return;
        }

        WorldDateAdvanceEvent.CatchUpNextFrame([..GameDate]);
    }
}
