using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Council 2026-10-23: a player on the host's world map took a step (or an hour of its express travel) that
///     moves the date, as the host's own would. Its game does not own the date: the host moves it, after
///     checking the step is one the game can make, and tells everyone with the traveller's name
/// </summary>
[MessagePackObject]
public class WorldTravelStepDelta : ElinDelta
{
    [Key(0)]
    public required int Minutes { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host || !FromPeer) {
            return;
        }

        if (Minutes is <= 0 or > WorldTravelClock.MaxStepMinutes) {
            EmpLog.Warning("World time: player {Peer} reported a step of {Minutes} minute(s), refused",
                OriginPeer, Minutes);
            return;
        }

        // the player saw everyone on the world map, the host no longer does (someone just left): no hours
        if (NetSession.Instance.Rules.WorldMapTime == WorldMapTime.TravelTogether && !host.AllOnWorldMap()) {
            EmpLog.Debug("World time: step of player {Peer} while not everyone is on the world map, no hours",
                OriginPeer);
            return;
        }

        var moves = WorldTravelClock.Step(OriginPeer, WorldTravelClock.Plausible(OriginPeer, Minutes, "travel"));
        if (moves > 0) {
            WorldDateAdvanceEvent.CatchUpNextFrame(WorldDateAdvanceEvent.AfterPending(moves), host.TravellerOf(OriginPeer));
        }
    }
}

/// <summary>
///     Council 2026-10-23, Travel Together: whether every player is on the world map, as the host sees it. A
///     player's step moves the date only then, whoever steps; its game needs to know it before stepping
/// </summary>
[MessagePackObject]
public class WorldMapTogetherDelta : ElinDelta
{
    /// <summary>
    ///     Last told by the host
    /// </summary>
    internal static bool AllOnWorldMap { get; private set; }

    [Key(0)]
    public required bool All { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (!net.IsHost) {
            AllOnWorldMap = All;
        }
    }
}
