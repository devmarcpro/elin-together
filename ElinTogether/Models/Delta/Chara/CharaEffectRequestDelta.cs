using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     An effect a dialog gives the player for its money (the healer): played in the client's game only, where hit
///     points and conditions are not its own to change, it paid for nothing. The host plays it on the player or on
///     one of its companions <br />
///     Closed list, see <see cref="DramaEffectPatch" />
/// </summary>
[MessagePackObject]
public class CharaEffectRequestDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Target { get; init; }

    [Key(1)]
    public required EffectId Id { get; init; }

    internal static bool IsAllowed(EffectId id)
    {
        return id is EffectId.HealComplete;
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host || !IsAllowed(Id) || !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) ||
            Target.Find() is not Chara { isDead: false } target || (target != sender && !target.IsCompanionOf(sender))) {
            return;
        }

        using var simulate = Simulate();
        using var told = MsgRelayContext.Suppress();
        ActEffect.Proc(Id, target);
    }
}
