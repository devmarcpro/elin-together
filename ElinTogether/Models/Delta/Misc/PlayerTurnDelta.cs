using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Client -> host: this player took a turn, what fights it may act, see PlayerCombatTime
/// </summary>
[MessagePackObject]
public class PlayerTurnDelta : ElinDelta
{
    /// <summary>
    ///     What this player attacked during that turn, 0 for nothing. Said by its own game: an act that fails (a
    ///     blow that misses) is not sent at all, and the monster missed ten times in a row stood frozen
    /// </summary>
    [Key(0)]
    public int Attacked { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host || !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var chara)) {
            return;
        }

        if (Attacked != 0 && _map?.charas.Find(c => c.uid == Attacked) is { } target) {
            PlayerCombatTime.Struck(target, chara);
        }

        PlayerCombatTime.OnPlayerTurn(chara);
    }
}
