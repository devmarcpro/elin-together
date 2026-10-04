using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The luck and the seed of the day, as the world keeper drew them (see <see cref="WorldKeeper" />): the
///     same fortune and the same newspaper for everyone
/// </summary>
[MessagePackObject]
public class DayDataDelta : ElinDelta
{
    [Key(0)]
    public required int Luck { get; init; }

    [Key(1)]
    public required int Seed { get; init; }

    internal static DayDataDelta Create(DayData day)
    {
        return new() {
            Luck = (int)day.luck,
            Seed = day.seed,
        };
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (WorldKeeper.IsKeeper || world is null) {
            return;
        }

        world.dayData = new() {
            luck = (DayData.Luck)Luck,
            seed = Seed,
        };
    }
}
