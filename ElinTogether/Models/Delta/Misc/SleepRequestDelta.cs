using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class SleepRequestDelta : ElinDelta
{
    /// <summary>
    ///     Own sleep: hours of the night it starts, as its own game counts them (how tired it is)
    /// </summary>
    [Key(0)]
    public int Hours { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        // client -> host intent only
        if (net is not ElinNetHost host) {
            return;
        }

        if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var chara)) {
            return;
        }

        if (chara is { isDead: true } || chara.conSleep is not null) {
            return;
        }

        EmpLog.Debug("Sleep request from {PeerIndex}", OriginPeer);

        using var _ = Simulate();
        chara.AddCondition<ConSleep>(50, true);

        // it sleeps at once, a night of its own
        if (NetSession.Instance.Rules.UseOwnSleep && chara.conSleep is not null) {
            SleepSynchronizationContext.OnGuestAsleep(OriginPeer, chara, Hours);
        }
    }
}