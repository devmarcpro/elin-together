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
    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host || !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var chara)) {
            return;
        }

        PlayerCombatTime.OnPlayerTurn(chara);
    }
}
