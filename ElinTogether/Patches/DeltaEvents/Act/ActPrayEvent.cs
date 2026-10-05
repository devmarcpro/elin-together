using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(ActPray), nameof(ActPray.TryPray))]
internal static class ActPrayEvent
{
    [HarmonyPrefix]
    internal static bool OnTryPray(Chara c, ref bool __result)
    {
        if (NetSession.Instance.Connection is null || !c.IsRemotePlayer) {
            return true;
        }

        __result = true;

        if (!c.HasCondition<ConWrath>() && c.things.Find<TraitPunishBall>() is { } ball) {
            ball.Destroy();
            c.PlaySound("pray");
            c.PlayEffect("revive");
            c.Say("piety2", c);
            return false;
        }

        // the gifts of its god, as for a player praying alone: before the daily prayer, and instead of it
        // (its own count of them: RemoteGodGiftPatch). The pet follows the one who prayed
        using (ElinDelta.Simulate())
        using (MsgRelayContext.RedirectTo(c))
        using (CharaMakeAllyEvent.GiftsFor(c)) {
            if (c.faith.TryGetGift(c)) {
                return false;
            }
        }

        var today = EClass.world.date.GetRawDay();
        var profile = c.NetProfile;
        if (profile.LastPrayedDay == today) {
            return false;
        }
        profile.LastPrayedDay = today;

        c.Say("pray2", c, c.faith.Name);
        c.PlaySound("pray");
        c.PlayEffect("revive");
        // as for the local player: the one who prays and its companions (ActPray.Pray heals "the player's" party)
        foreach (var member in CompanionHelper.CompanionsOf(c).Prepend(c)) {
            member.HealHP(999999L);
            member.mana.Mod(999999);
            member.Cure(CureType.Prayer, 999999);
            member.RemoveCondition<ConDeathSentense>();
        }

        return false;
    }
}