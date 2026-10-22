using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Auto combat protects "the player" and its party in the game that makes the damage, the host's: the host's auto
///     combat saved everyone, a guest's saved no one. A guest tells the host when its auto combat runs and who was
///     healthy when it began (<see cref="Healthy" />); the host saves with it the guest and its own companions, and
///     tells it when it did (<see cref="Saved" />): that game stops its auto combat and pays the stamina, as the game does
/// </summary>
[MessagePackObject]
public class AutoCombatDelta : ElinDelta
{
    /// <summary>
    ///     Guest to host: the characters its auto combat protects, null when it stopped
    /// </summary>
    [Key(0)]
    public int[]? Healthy { get; init; }

    /// <summary>
    ///     Host to guest: a hit that would have killed one of them was stopped
    /// </summary>
    [Key(1)]
    public bool Saved { get; init; }

    /// <summary>
    ///     The one saved was the player itself (the game's message is not the same)
    /// </summary>
    [Key(2)]
    public bool Self { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            if (host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var player)) {
                AutoCombatPerPlayerPatch.Set(player, Healthy is null ? null : new HashSet<int>(Healthy));
            }

            return;
        }

        if (!Saved) {
            return;
        }

        Msg.Say(Self ? "abort_damage" : "abort_damgeAlly");
        EClass.player.TryAbortAutoCombat();
        EClass.pc.stamina.Mod(-EClass.pc.stamina.max / 5);
    }

    internal static int[] Of(GoalAutoCombat goal)
    {
        return goal.listHealthy.Select(c => c.uid).ToArray();
    }
}
