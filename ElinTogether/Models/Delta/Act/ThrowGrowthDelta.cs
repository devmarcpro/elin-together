using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     What a player's throw taught it and cost it. A guest's throw is played in the host's game only (the guest's
///     own game replays the host's throw for the picture): the experience (throwing on a hit, a potion, a snowball,
///     a monster ball...) and the stamina of the throw went to the host's copy of that player, which nothing reads,
///     and the guest got a flat 50 throwing experience instead, hit or miss (audit 2026-10-23). The host tells that
///     player what the throw gave in the game that decided it, see <see cref="Patches.ThrowGrowthPatch" />
/// </summary>
[MessagePackObject]
public class ThrowGrowthDelta : ElinDelta
{
    [Key(0)]
    public required int[] Elements { get; init; }

    [Key(1)]
    public required int[] Amounts { get; init; }

    [Key(2)]
    public required int Stamina { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net.IsHost || pc is null) {
            return;
        }

        // as this player's own gain: what it becomes is told as any other growth of its character
        using var own = Simulate();
        for (var i = 0; i < Elements.Length && i < Amounts.Length; i++) {
            if (Amounts[i] is > 0 and <= 100000 && sources.elements.map.ContainsKey(Elements[i])) {
                pc.ModExp(Elements[i], Amounts[i]);
            }
        }

        if (Stamina is < 0 and > -1000) {
            pc.stamina.Mod(Stamina);
        }
    }
}
