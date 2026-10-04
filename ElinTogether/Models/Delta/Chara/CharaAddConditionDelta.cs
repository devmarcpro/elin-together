using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaAddConditionDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Owner { get; init; }

    // TODO build condition type mapping
    [Key(1)]
    public required int ConditionId { get; init; }

    [Key(2)]
    public required int Power { get; init; }

    [Key(3)]
    public required bool Force { get; init; }

    [Key(4)]
    public bool Remove { get; set; }

    internal static bool IsTrapCondition(string alias)
    {
        return alias is nameof(ConSleep) or nameof(ConBlind) or nameof(ConParalyze);
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            // reject every chara add condition delta from clients, but what a trap does to the player who
            // sent it: that trap was rolled in its game only
            if (!Remove && host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) && Owner.Find() == sender &&
                sources.stats.map.TryGetValue(ConditionId, out var asked) && IsTrapCondition(asked.alias)) {
                using var _ = Simulate();
                sender.AddCondition(Condition.Create(asked.alias, Power), Force);
            }

            return;
        }

        if (Owner.Find() is not Chara chara) {
            return;
        }

        if (Remove) {
            chara.conditions.ForeachReverse(c => {
                if (c.id == ConditionId) {
                    c.Kill();
                }
            });
        } else {
            var row = sources.stats.map[ConditionId];
            chara.Stub_AddCondition(Condition.Create(row.alias, Power), Force);
        }
    }
}