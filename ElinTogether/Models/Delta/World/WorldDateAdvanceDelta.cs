using System.Collections.Immutable;
using System.Linq;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class WorldDateAdvanceDelta : ElinDelta
{
    [Key(0)]
    public required int Minutes { get; init; }

    [Key(1)]
    public required ImmutableArray<int> GameDate { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net.IsHost) {
            return;
        }

        // away from the host: this game simulates its own map and keeps its own date. With one date for the
        // world it catches up when the world went further without it; a visitor hears it from the map's holder
        if (NetSession.Instance.IsAway) {
            if (NetSession.Instance is { IsZoneAuthority: true, Rules.UseSharedWorldTime: true }) {
                WorldDateAdvanceEvent.CatchUpNextFrame([..GameDate]);
            }

            return;
        }

        // from the delta itself, not from this game's date: the world snapshot may have set the date already
        var now = WorldDateAdvanceEvent.Minutes([..GameDate]);
        var before = now - Minutes;

        SetClientDate([..GameDate]);

        foreach (var zoneEvent in _zone.events.list) {
            zoneEvent.minElapsed += Minutes;
        }

        if (pc.isDead) {
            return;
        }

        using var _ = Simulate();
        // a jump of the host's time (sleep, rest): in normal play the host advances minute by minute, 0 tick
        var ticks = Minutes * 4 / 6;
        if (ticks > 0) {
            EmpLog.Debug("Catching up host time adv {AdvancedMins} {NeedTicks}", Minutes, ticks);
        }

        for (var i = 0; i < ticks && !pc.isDead; ++i) {
            pc.TickConditions();
        }

        // what GameDate.AdvanceHour, Day, Month and Year do for the player of a game that owns its date
        var hours = now / Date.HourToken - before / Date.HourToken;
        if (hours is > 0 and <= 24 && !pc.isDead) {
            for (var h = 0; h < hours; h++) {
                player.OnAdvanceHour();
            }
        }

        var days = now / Date.DayToken - before / Date.DayToken;
        if (days is > 0 and <= 3 && !pc.isDead) {
            for (var d = 0; d < days; d++) {
                player.stats.days++;
                player.questRerollCost = System.Math.Max(0, player.questRerollCost - 3);
                if (!player.prayed && pc.Evalue(FEAT.featModelBeliever) > 0) {
                    ActPray.TryPray(pc, true);
                }

                player.OnAdvanceDay();
            }
        }

        if (now / Date.MonthToken > before / Date.MonthToken) {
            player.stats.months++;
            player.nums.OnAdvanceMonth();
            if (world.date.month % 2 == 0) {
                player.holyWell++;
            }
        }

        if (now / Date.YearToken > before / Date.YearToken) {
            player.flags.santa = 0;
            player.wellWished = false;
            player.nums.OnAdvanceYear();
        }
    }

    internal static void SetClientDate(int[] raw)
    {
        var date = world.date;
        if (date.raw.SequenceEqual(raw)) {
            return;
        }

        var hourChanged = date.hour != raw[3];
        date.raw = raw;

        screen.RefreshGrading();
        if (hourChanged) {
            scene.OnChangeHour();
        }
    }
}