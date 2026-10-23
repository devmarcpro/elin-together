using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Host to the player whose fortune roll it ran: the roll counter and the lucky coins won are that player's
///     own (Player.seedFortune, Player.luckycoin), the host rolled with them (see AIUseCrafterArgs.SeedFortune)
///     and gives them back as they are now (audit 2026-10-23)
/// </summary>
[MessagePackObject]
public class FortuneCountersDelta : ElinDelta
{
    [Key(0)]
    public required int SeedFortune { get; init; }

    [Key(1)]
    public required int LuckyCoin { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost) {
            return;
        }

        player.seedFortune = SeedFortune;
        player.luckycoin = LuckyCoin;
    }
}
