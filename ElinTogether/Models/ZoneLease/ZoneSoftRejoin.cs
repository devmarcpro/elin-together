using System.Collections.Generic;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Net packet: Host -> Client <br />
///     Answer to a <see cref="ZoneLeaseRelease" /> marked Soft, in place of the copy of the world: the host stands
///     on the map this player handed back and runs it from now on, the player keeps its game and its scene and is
///     a client of the host again. Sent in place of the map the host tells everyone when it enters a zone, right
///     after what was waiting to be told: everything that comes after it happened after these numbers were taken <br />
///     Also the answer to a release that walks into the host's map (<see cref="Travel" />): the same content,
///     then that one map
/// </summary>
[MessagePackObject]
public class ZoneSoftRejoin
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     The card uid counter of the host
    /// </summary>
    [Key(1)]
    public required int UidNext { get; init; }

    /// <summary>
    ///     Cards of the player and of its companions that still waited for a host uid (<see cref="PendingUid" />):
    ///     the number they had -> the number the host gave them, see ElinNetHost.ReplaceRemoteChara
    /// </summary>
    [Key(2)]
    public Dictionary<int, int>? Rebinds { get; set; } = null;

    /// <summary>
    ///     What the player carries as the host holds it (NetDesync.Bag), compared once the numbers above are applied
    /// </summary>
    [Key(3)]
    public int BagMix { get; set; } = 0;

    /// <summary>
    ///     The numbers of the map as the host loaded it (<see cref="ZoneLeaseState.Sums" />)
    /// </summary>
    [Key(4)]
    public int[]? MapSums { get; set; } = null;

    /// <summary>
    ///     What the boxes of the world hold (shipping 0, delivery 1, bank 2, see ShippingDeposit.Box), each a list
    ///     of things: they are emptied in the game of a player who travels alone
    /// </summary>
    [Key(5)]
    public List<LZ4Bytes>? Boxes { get; set; } = null;

    [Key(6)]
    public int[]? GameDate { get; set; } = null;

    /// <summary>
    ///     The characters of the world standing on the host's map, except the player's own and its companions: the
    ///     host, the other players, their companions. The copies this player holds are as old as its last world
    /// </summary>
    [Key(7)]
    public List<LZ4Bytes>? Charas { get; set; } = null;

    /// <summary>
    ///     The player walks into the map the host stands on (<see cref="ZoneLeaseRelease.Arrival" />) instead of
    ///     the host coming to its own: <see cref="ZoneUid" /> is the host's map, which follows this message as
    ///     any map the host sends (ZoneDataResponse, then the placement). No <see cref="MapSums" />: the player
    ///     holds no copy of that map to compare
    /// </summary>
    [Key(8)]
    public bool Travel { get; set; } = false;
}

/// <summary>
///     Net packet: Client -> Host <br />
///     The return in place did not work here (nothing came, what came does not match, it could not be applied):
///     the host sends the world, as it does without the rule
/// </summary>
[MessagePackObject]
public class ZoneSoftRejoinFailed
{
    [Key(0)]
    public required int ZoneUid { get; init; }

    [Key(1)]
    public string? Reason { get; set; } = null;
}
