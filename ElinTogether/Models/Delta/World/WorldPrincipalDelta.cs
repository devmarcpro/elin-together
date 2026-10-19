using ElinTogether.Net;
using MessagePack;
using Newtonsoft.Json;

namespace ElinTogether.Models;

/// <summary>
///     The world settings (GamePrincipal: death penalty protection, void blessing, permadeath...) are the world's, so
///     the host's (council of 2026-10-19): a guest's game kept its own changes and applied other rules than the host's
///     game. The host tells its settings whenever it changes them; a guest's changes are not kept (LayerWorldSetting)
/// </summary>
[MessagePackObject]
public class WorldPrincipalDelta : ElinDelta
{
    [Key(0)]
    public required string Json { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net.IsHost || game is null || JsonConvert.DeserializeObject<GamePrincipal>(Json) is not { } principal) {
            return;
        }

        game.principal = principal;
        // what LayerWorldSetting.Apply does with the permadeath of the player
        pc?.SetFeat(1220, principal.permadeath ? 1 : 0);
    }
}
