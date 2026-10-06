using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     How a player walks into a map someone else simulates: what the game reads to pick where it arrives
///     (Zone.GetSpawnPos). The one simulating the map picks the tile, as the game does for a player alone
/// </summary>
[MessagePackObject]
public class ZoneArrival
{
    /// <summary>
    ///     The map walked into
    /// </summary>
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     The map walked out of
    /// </summary>
    [Key(1)]
    public required int LastZoneUid { get; init; }

    /// <summary>
    ///     ZoneTransition.EnterState
    /// </summary>
    [Key(2)]
    public required int State { get; init; }

    [Key(3)]
    public int X { get; init; }

    [Key(4)]
    public int Z { get; init; }

    [Key(5)]
    public string? IdTele { get; init; }

    [Key(6)]
    public float RatePos { get; init; } = -1f;

    /// <summary>
    ///     The move the local player is about to make, before the game runs it
    /// </summary>
    internal static ZoneArrival Create(int zoneUid, ZoneTransition transition)
    {
        var leaving = EClass.pc.currentZone;

        // what the game only does for the local player: out of an instance it goes back to where it went in
        // (Chara.MoveZone), and walking into a map from the world map it stands where it last left a map
        // (Zone.GetSpawnPos, player.lastZonePos)
        if (leaving?.instance is { } instance) {
            transition = new() {
                state = instance.ReturnState,
                x = instance.x,
                z = instance.z,
            };
        } else if (leaving is { IsRegion: true } && EClass.player.lastZonePos is { } last &&
                   transition.state is ZoneTransition.EnterState.Top or ZoneTransition.EnterState.Right
                       or ZoneTransition.EnterState.Bottom or ZoneTransition.EnterState.Left) {
            transition = new() {
                state = ZoneTransition.EnterState.Exact,
                x = last.x,
                z = last.z,
            };
        }

        return new() {
            ZoneUid = zoneUid,
            LastZoneUid = leaving?.uid ?? 0,
            State = (int)transition.state,
            X = transition.x,
            Z = transition.z,
            IdTele = transition.idTele,
            RatePos = transition.ratePos,
        };
    }

    internal ZoneTransition ToTransition()
    {
        return new() {
            uidLastZone = LastZoneUid,
            state = (ZoneTransition.EnterState)State,
            x = X,
            z = Z,
            idTele = IdTele,
            ratePos = RatePos,
        };
    }
}
