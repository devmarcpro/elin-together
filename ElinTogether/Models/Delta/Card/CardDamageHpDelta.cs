using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CardDamageHpDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard Owner { get; init; }

    [Key(1)]
    public required long Dmg { get; init; }

    [Key(2)]
    public required int Ele { get; init; }

    [Key(3)]
    public int EleP { get; init; }

    [Key(4)]
    public AttackSource AttackSource { get; init; }

    [Key(5)]
    public RemoteCard? Origin { get; init; }

    [Key(6)]
    public bool ShowEffect { get; init; }

    [Key(7)]
    public RemoteCard? Weapon { get; init; }

    [Key(8)]
    public RemoteCard? OriginalTarget { get; init; }

    [Key(9)]
    public int ResistPenetrationLevel { get; init; }

    [Key(10)]
    public int? HpAfter { get; set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (Owner.Find() is not { } card) {
            return;
        }

        // a player is shielded from another player's blow wherever the blow lands: in the replay of what the
        // simulating game decided, and here when a client reports the blow its own game dealt to its player
        // (the stub is the game's own code, without the prefix that shields)
        var origin = Origin?.Find();
        var shield = RemotePlayerKillPatch.Shield(card, origin);
        try {
            using (Simulate(net.IsHost)) {
                card.Stub_DamageHP(Dmg, Ele, EleP, AttackSource, Origin, ShowEffect, Weapon, OriginalTarget, ResistPenetrationLevel);
            }
        } finally {
            RemotePlayerKillPatch.Unshield(card, shield, origin);
        }

        if (!net.IsHost && HpAfter is { } hpAfter && card is not Chara { isDead: true }) {
            card.hp = hpAfter;
        }
    }
}