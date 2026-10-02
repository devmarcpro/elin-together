using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     How much a resident likes the players: one value for the group, kept by the host. The game rolls dice
///     for every point, so each game would otherwise end with its own number
/// </summary>
[MessagePackObject]
public class CharaAffinityDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required int Value { get; init; }

    /// <summary>
    ///     From a client: what its action changed. From the host: the value everyone takes
    /// </summary>
    [Key(2)]
    public bool Relative { get; set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Owner.Find() is not Chara chara) {
            return;
        }

        if (net is ElinNetHost host) {
            if (!Relative) {
                return;
            }

            chara._affinity += Value;
            host.Delta.AddRemote(new CharaAffinityDelta {
                Owner = Owner,
                Value = chara._affinity,
            });
            return;
        }

        if (!Relative) {
            chara._affinity = Value;
        }
    }
}
