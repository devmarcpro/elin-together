using System;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(Chara), nameof(Chara.GiveGift))]
internal static class CharaGiveGiftEvent
{
    [HarmonyPrefix]
    internal static void OnGiveGift(Chara __instance, Chara c, Thing t)
    {
        if (NetSession.Instance.Connection is not { } connection) {
            return;
        }

        // the "give" gesture hands one out of the held stack: that one only exists here, the host knows the stack
        // it came from (how many is in the reference)
        var gift = PendingSplit.Split(t);
        if (connection.IsClient && (!__instance.IsPC || CardCache.Find(gift.Uid) is null)) {
            return;
        }

        connection.Delta.AddRemote(new CharaGiveGiftDelta {
            From = __instance,
            To = c,
            Thing = gift,
        });
    }

    extension(Chara chara)
    {
        [HarmonyReversePatch(HarmonyReversePatchType.Snapshot)]
        internal void Stub_GiveGift(Chara c, Thing t)
        {
            throw new NotImplementedException("Chara.GiveGift");
        }
    }
}