using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The weather of the world, as its keeper drew it (see <see cref="WorldKeeper" />)
/// </summary>
[MessagePackObject]
public class WeatherDelta : ElinDelta
{
    [Key(0)]
    public required int Condition { get; init; }

    [Key(1)]
    public required int Duration { get; init; }

    [Key(2)]
    public required int LastRain { get; init; }

    /// <summary>
    ///     What comes next: condition, duration, condition, duration…
    /// </summary>
    [Key(3)]
    public required List<int> Forecasts { get; init; }

    internal static WeatherDelta Create(Weather weather)
    {
        return new() {
            Condition = (int)weather._currentCondition,
            Duration = weather.duration,
            LastRain = weather.lastRain,
            Forecasts = weather.forecasts.SelectMany(f => new[] { (int)f.condition, f.duration }).ToList(),
        };
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (WorldKeeper.IsKeeper || world?.weather is not { } weather) {
            return;
        }

        var changed = (int)weather._currentCondition != Condition;
        weather._currentCondition = (Weather.Condition)Condition;
        weather.duration = Duration;
        weather.lastRain = LastRain;
        weather.forecasts.Clear();
        for (var i = 0; i + 1 < Forecasts.Count; i += 2) {
            weather.forecasts.Add(new() {
                condition = (Weather.Condition)Forecasts[i],
                duration = Forecasts[i + 1],
            });
        }

        if (changed && game?.activeZone?.map is not null) {
            weather.RefreshWeather();
        }
    }
}
