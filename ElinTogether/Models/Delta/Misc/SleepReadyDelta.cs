using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class SleepReadyDelta : ElinDelta
{
    [Key(0)]
    public required int PlayerIndex { get; init; }

    [Key(1)]
    public required bool Ready { get; init; }

    [Key(2)]
    public required int ReadyCount { get; init; }

    [Key(3)]
    public required int TotalCount { get; init; }

    /// <summary>
    ///     Name of a player away from the host map, which is not in the list of the players of that map
    /// </summary>
    [Key(4)]
    public string? Name { get; init; }

    /// <summary>
    ///     Only the count, nothing said: a player who comes in while others sleep learns how many do
    /// </summary>
    [Key(5)]
    public bool Quiet { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        // host -> client broadcast only
        if (net.IsHost) {
            return;
        }

        SleepSynchronizationContext.Sleepers = ReadyCount;
        if (!Quiet) {
            Play();
        }
    }

    public void Play()
    {
        // own sleep: who sleeps, out of how many; a player waking up is its own business
        var own = NetSession.Instance.Rules.UseOwnSleep;
        if (own && !Ready) {
            return;
        }

        var color = PeerColorizer.GetColor(PlayerIndex);
        var player = NetSession.Instance.CurrentPlayers.Find(p => p.Index == PlayerIndex);
        var name = Name ?? player?.User.Name ?? "emp_ui_unknown_player".Loc(PlayerIndex);
        var key = own ? "emp_ui_sleep_count" : Ready ? "emp_ui_sleep_wish" : "emp_ui_sleep_cancel";
        WidgetPopText.Say(key.Loc(name.TagColor(color), ReadyCount, TotalCount));
    }
}