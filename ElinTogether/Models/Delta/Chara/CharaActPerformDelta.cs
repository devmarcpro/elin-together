using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaActPerformDelta : ElinDelta
{
    // builtin acts that are not instantiated
    private static readonly Dictionary<int, Act> _builtInMapping = new() {
        [ABILITY.ActWait] = ACT.Wait,
        [ABILITY.ActMelee] = ACT.Melee,
        [ABILITY.ActThrow] = ACT.Throw,
        [ABILITY.ActRanged] = ACT.Ranged,
        [ABILITY.ActKick] = ACT.Kick,
        [ABILITY.ActChat] = ACT.Chat,
        [ABILITY.ActPick] = ACT.Pick,
        [ABILITY.ActItem] = ACT.Item,
    };
    private static bool _staticMapped;

    [Key(0)]
    public required int ActId { get; init; }

    [Key(1)]
    public required RemoteCard Owner { get; init; }

    [Key(2)]
    public required RemoteCard? TargetCard { get; init; }

    [Key(3)]
    public required Position? Pos { get; init; }

    /// <summary>
    ///     The tool of an act the game builds around a held item (a rod and its ActZap). Such an act has no id of
    ///     its own to be made again from: without the tool the other side performed an empty act, the rod of a
    ///     client did nothing to the world and kept its charges
    /// </summary>
    [Key(4)]
    public RemoteCard? Tool { get; init; }

    public static CharaActPerformDelta Create(Act act)
    {
        ApplyBuiltInMapping();

        return new() {
            ActId = act.id,
            Owner = Act.CC,
            TargetCard = Act.TC,
            Pos = Act.TP,
            Tool = ToolOf(act),
        };
    }

    private static Card? ToolOf(Act act)
    {
        return act switch {
            ActZap zap => zap.trait?.owner,
            _ => null,
        };
    }

    private static Act? ActOf(Card? tool)
    {
        return tool?.trait switch {
            TraitRod rod => new ActZap { trait = rod },
            _ => null,
        };
    }

    protected override void OnApply(ElinNetBase net)
    {
        ApplyBuiltInMapping();

        // we do not apply to ourselves
        if (Owner.Find() is not Chara { IsPC: false } chara) {
            return;
        }

        if (Tool is not null) {
            PerformWithTool(net, chara);
            return;
        }

        // reperform act
        var act = _builtInMapping.GetValueOrDefault(ActId);
        act ??= chara.elements.GetElement(ActId)?.act ?? ACT.Create(ActId);
        act.id = ActId;

        // pos compensation if high rtt
        var target = TargetCard?.Find();
        var pos = Pos;
        if (target is Chara { isDead: false, IsInActiveMap: true } targetChara &&
            pos is not null && targetChara.pos.Distance(pos) <= 2) {
            pos = targetChara.pos;
        }

        act.Perform(chara, target, pos);
    }

    private void PerformWithTool(ElinNetBase net, Chara chara)
    {
        // only with the tool in that character's hands
        var tool = Tool?.Find();
        if (tool is null || tool.GetRootCard() != chara || ActOf(tool) is not { } act) {
            return;
        }

        // a zap names its user as target while it performs: only the tile aimed at is passed on
        if (net.IsHost) {
            act.Perform(chara, null, Pos);
            return;
        }

        // the charge left came from the host already, this replay is for show
        var charges = tool.c_charges;
        tool.c_charges = charges + 1;
        try {
            act.Perform(chara, null, Pos);
        } finally {
            tool.c_charges = charges;
        }
    }

    private static void ApplyBuiltInMapping()
    {
        if (_staticMapped) {
            return;
        }

        foreach (var (k, v) in _builtInMapping) {
            v.id = k;
        }
        _staticMapped = true;
    }
}