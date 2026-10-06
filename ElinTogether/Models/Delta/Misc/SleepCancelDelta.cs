using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class SleepCancelDelta : ElinDelta
{
    protected override void OnApply(ElinNetBase net)
    {
        // client -> host intent only
        if (net is not ElinNetHost host) {
            return;
        }

        if (!host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var chara)) {
            return;
        }

        // too late if high rtt (a night of the host's own holds nobody else)
        if (ui.GetLayer<LayerSleep>() is not null && !SleepSynchronizationContext.IsOwnNight) {
            return;
        }

        EmpLog.Debug("Sleep cancel from {PeerIndex}", OriginPeer);

        using var _ = Simulate();
        chara.conSleep?.Kill();
    }
}