using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A player cannot kill another player (council 7): a strike of a player or of what fights for one (shift +
///     click, a spell gone wide, a companion) that would kill another player's character leaves it at 0 hit
///     points instead, as the game does for what it marks invulnerable. A real death by a friend's hand cost a
///     grave, gold and experience <br />
///     The host can allow it (PlayerKill). Only the game that simulates the map decides a death <br />
///     Not covered: what kills without a striker, bleeding, poison, fire and the death sentence a player left
///     on another
/// </summary>
[HarmonyPatch(typeof(Card), nameof(Card.DamageHP),
    typeof(long), typeof(int), typeof(int), typeof(AttackSource), typeof(Card), typeof(bool), typeof(Thing), typeof(Chara),
    typeof(int))]
internal static class RemotePlayerKillPatch
{
    private const string Tag = nameof(EditorTag.Invulnerable);

    [HarmonyPrefix]
    internal static void OnDamage(Card __instance, Card origin, out string? __state)
    {
        __state = NetSession.Instance.Connection is ElinNetHost ? Shield(__instance, origin) : null;
    }

    [HarmonyFinalizer]
    internal static void OnDamageEnd(Card __instance, string? __state)
    {
        Unshield(__instance, __state);
    }

    /// <summary>
    ///     The game's own "cannot die" (Card.DamageHP, EvadeDeath), for the time of one strike. Also around the
    ///     replay of that strike in the other games (CardDamageHpDelta): the replay would say "X kills Y" and
    ///     count a kill there
    /// </summary>
    /// <returns>the tags to give back to <see cref="Unshield" />, null when the strike is not shielded</returns>
    internal static string? Shield(Card card, Card? origin)
    {
        if (NetSession.Instance.Rules.AllowPlayerKill || card is not Chara target || !IsPlayer(target) ||
            origin?.Chara is not { } attacker || attacker == target ||
            !(IsPlayer(attacker) || attacker.IsPCFactionOrMinion) || target.HasEditorTag(EditorTag.Invulnerable)) {
            return null;
        }

        var tags = target.c_editorTags ?? "";
        target.c_editorTags = tags.Length == 0 ? Tag : tags + "," + Tag;
        return tags;
    }

    internal static void Unshield(Card card, string? tags)
    {
        if (tags is not null) {
            card.c_editorTags = tags.Length == 0 ? null : tags;
        }
    }

    private static bool IsPlayer(Chara chara)
    {
        return chara.IsPC || chara.IsRemotePlayer;
    }
}
