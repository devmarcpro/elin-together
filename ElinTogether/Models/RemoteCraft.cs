using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using ElinTogether.Models.AI;

namespace ElinTogether.Models;

// TODO: ask Redgeoiz to rework this
internal static class RemoteCraft
{
    private static readonly ConditionalWeakTable<AI_UseCrafter, AIUseCrafterArgs> _selections = new();

    internal static Chara? ProductReceiver { get; set; }

    internal static void Attach(AI_UseCrafter act, AIUseCrafterArgs args)
    {
        _selections.Add(act, args);
    }

    internal static bool TryGet(AI_UseCrafter act, [NotNullWhen(true)] out AIUseCrafterArgs? args)
    {
        return _selections.TryGetValue(act, out args);
    }

    /// <summary>
    ///     The game asks "the player" for the feats, skills and level that shape what is crafted and how long it
    ///     takes. While the host crafts for another player, that player stands in as the local one: without it
    ///     its potions were not doubled by its own feat, and the quality came from the host's skills
    /// </summary>
    internal static ScopeExit AsCrafter(Chara crafter)
    {
        var self = EClass.player.chara;
        EClass.player.chara = crafter;

        return new() {
            OnExit = () => EClass.player.chara = self,
        };
    }

    internal static bool IsHostRun(AIAct? act)
    {
        return act is AI_UseCrafter crafter && _selections.TryGetValue(crafter, out _);
    }
}