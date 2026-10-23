using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A diary brings its writer as a companion of "the player" who reads it. A client cannot create characters (its
///     copy vanishes at the end of the frame) and the diary it used up was lost; the host read it for a resident:
///     nothing happened (audit 2026-10-23). The host brings the writer for that player when it replays the read
///     (CharaTaskDelta, AI_Read) and uses the diary up, the reader's own game says the line and gets the achievement
/// </summary>
[HarmonyPatch(typeof(TraitDiary), nameof(TraitDiary.OnRead))]
internal static class TraitDiaryPatch
{
    [HarmonyPrefix]
    internal static bool OnRead(TraitDiary __instance, Chara c)
    {
        switch (NetSession.Instance.Connection) {
            case ElinNetClient when c.IsPC:
                Msg.Say("diary_" + __instance.GetParam(1));
                if (__instance.GetParam(1) == "sister") {
                    Steam.GetAchievement(ID_Achievement.DIARY);
                }

                return false;
            case ElinNetHost when c is { IsPC: false, IsRemotePlayer: true }:
                // as TraitDiary.OnRead does for the player, next to this one and following it
                using (ElinDelta.Simulate()) {
                    var chara = CharaGen.Create(__instance.GetParam(1));
                    chara.c_daysWithPC = EClass.player.stats.days + 365 + EClass.rnd(365);
                    EClass._zone.AddCard(chara, c.pos.GetNearestPoint(allowBlock: false, allowChara: false));
                    chara.SetCompanionOwner(c);
                    chara.MakeAlly(msg: false);
                    chara.PlaySound("identify");
                    chara.PlayEffect("teleport");
                    __instance.owner.ModNum(-1);
                }

                return false;
            default:
                return true;
        }
    }
}
