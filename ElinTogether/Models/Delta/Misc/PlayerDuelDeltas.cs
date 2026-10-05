using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A player to the game simulating the map: challenge, accept, decline (see <see cref="PlayerDuel" />)
/// </summary>
[MessagePackObject]
public class DuelIntentDelta : ElinDelta
{
    [Key(0)]
    public required int Kind { get; init; }

    [Key(1)]
    public int DuelId { get; set; }

    /// <summary>
    ///     Who is challenged, for a challenge
    /// </summary>
    [Key(2)]
    public int PartnerUid { get; set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host && host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var from)) {
            PlayerDuel.Handle(this, from, host);
        }
    }
}

/// <summary>
///     The game simulating the map to everyone: who duels who and where it stands. The two duellists show it,
///     every game needs it to know which blows are a duel's
/// </summary>
[MessagePackObject]
public class DuelStateDelta : ElinDelta
{
    /// <summary>
    ///     0 for a challenge refused before any duel existed
    /// </summary>
    [Key(0)]
    public int DuelId { get; set; }

    [Key(1)]
    public int Phase { get; set; }

    /// <summary>
    ///     The challenger
    /// </summary>
    [Key(2)]
    public int UidA { get; set; }

    [Key(3)]
    public int UidB { get; set; }

    [Key(4)]
    public int WinnerUid { get; set; }

    /// <summary>
    ///     Why it ended without a winner, as a text id
    /// </summary>
    [Key(5)]
    public string Reason { get; set; } = "";

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost) {
            PlayerDuel.Show(this);
        }
    }
}
