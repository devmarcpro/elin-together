using System.Collections.Immutable;
using System.Linq;
using ElinTogether.Helper;
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

    /// <summary>
    ///     The sender was catching up with time made pass on another map, see WorldDateAdvanceEvent.CatchUp
    /// </summary>
    [Key(2)]
    public bool CatchUp { get; init; }

    // minutes the date of this client moved since the last of these messages: the world snapshot sets it too,
    // sometimes first
    private static int _moved;

    protected override void OnApply(ElinNetBase net)
    {
        if (net.IsHost) {
            return;
        }

        // time another player made pass (elsewhere, or by a step of this map's holder on the world map) is
        // not taken from this player's quests. A night is its own: every player of the map sleeps it
        var others = CatchUp || (Minutes > 1 && pc?.conSleep is null);

        // away from the host: this game simulates its own map and keeps its own date. With one date for the
        // world it catches up when the world went further without it; a visitor hears it from the map's holder
        if (NetSession.Instance.IsAway) {
            if (NetSession.Instance is { IsZoneAuthority: true, Rules.UseSharedWorldTime: true }) {
                WorldDateAdvanceEvent.CatchUpNextFrame([..GameDate]);
            } else if (others && net.IsZoneSession) {
                PersonalQuests.Postpone(Minutes);
            }

            _moved = 0;
            return;
        }

        // from the delta itself, not from this game's date: the world snapshot may have set the date already
        var now = WorldDateAdvanceEvent.Minutes([..GameDate]);
        var before = now - Minutes;

        // the date went further than the minutes told: hours that came with no word of their own (the express
        // travel of the map's holder calls GameDate.AdvanceHour, not AdvanceMin). Another player's time too
        var untold = _moved + now - world.date.GetRaw() - Minutes;
        PersonalQuests.Postpone((others ? Minutes : 0) + (untold is > 0 and <= Date.MonthToken ? untold : 0));

        SetClientDate([..GameDate]);
        _moved = 0;

        foreach (var zoneEvent in _zone.events.list) {
            zoneEvent.minElapsed += Minutes;
        }

        if (pc is not { isDead: false }) {
            return;
        }

        using var _ = Simulate();

        // no turns of hunger or conditions for a jump of the date: the game plays none for its own player
        // either (a night, a catch-up), except for the one who steps on the world map, and that is its step.
        // They were played here, without a limit: a day of someone's travel starved this character

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

        _moved += WorldDateAdvanceEvent.Minutes(raw) - date.GetRaw();

        var hourChanged = date.hour != raw[3];
        date.raw = raw;

        screen.RefreshGrading();
        if (hourChanged) {
            scene.OnChangeHour();
        }
    }
}