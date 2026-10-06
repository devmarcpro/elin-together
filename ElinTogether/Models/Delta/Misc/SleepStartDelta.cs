using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class SleepStartDelta : ElinDelta
{
    [Key(0)]
    public required int Hours { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        // host -> client broadcast only
        if (net.IsHost) {
            return;
        }

        // own sleep: a player awake is left alone, the night screen of one asleep becomes the world's
        if (pc.isDead || SleepSynchronizationContext.JoinNight(Hours, NetSession.Instance.IsAway && !net.IsZoneSession)) {
            return;
        }

        EmpLog.Debug("Applying party sleep {SleepHours}", Hours);

        using var _ = Simulate();
        ui.AddLayer<LayerSleep>().Sleep(Hours, null);
    }
}