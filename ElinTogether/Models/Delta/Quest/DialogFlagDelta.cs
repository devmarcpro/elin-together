using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     What a dialog remembers (what was said, what was chosen), the same for every player, like the quest log
/// </summary>
[MessagePackObject]
public class DialogFlagDelta : ElinDelta
{
    [Key(0)]
    public required string Id { get; init; }

    [Key(1)]
    public required int Value { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        DialogFlagSync.Learn(Id, Value);

        if (net is not ElinNetHost host) {
            return;
        }

        host.SendDeltaToAllExcept(OriginPeer, this);
        // hosting a zone as a client: the host of the world has to know too
        QuestAwaySync.Send(this);
    }
}
