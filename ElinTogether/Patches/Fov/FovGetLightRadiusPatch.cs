using System;
using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

// hand of 105gun
[HarmonyPatch(typeof(Card), nameof(Card.GetLightRadius))]
internal class FovGetLightRadiusPatch
{
    [HarmonyPrefix]
    internal static bool OnCardGetLightRadius(Card __instance, ref int __result)
    {
        // vanilla returns 0 for a held thing unless EClass.pc holds it: do the same for any player's held light
        if (__instance is Thing { IsInstalled: false } held && held.parent is Chara holder
            && holder.held == held && holder.IsPlayer && !holder.IsPC) {
            __result = held.trait is TraitLightSource src && held.isEquipped
                ? src.LightRadius
                : held.LightData != null && held.trait.IsLightOn ? held.LightData.radius : 0;
            return false;
        }

        // treat this card as pc
        if (__instance is not Chara { IsPlayer: true } chara) {
            return true;
        }

        if (chara.isBlind) {
            __result = 1;
            return false;
        }

        // copied from Card.GetLightRadius
        var baseRadius = EClass._map.IsIndoor || EClass.world.date.IsNight
            ? 2
            : EClass.world.date.periodOfDay == PeriodOfDay.Day
                ? 6
                : 5;

        var extraRadius = 2;
        if (chara.body.GetEquippedThing(SLOT.lightsource)?.trait is TraitLightSource trait) {
            extraRadius = trait.LightRadius;
        }

        var heldLightRadius = chara.held?.GetLightRadius() ?? 0;
        if (heldLightRadius > 0) {
            extraRadius = Math.Max(extraRadius, heldLightRadius - 1);
            extraRadius = Math.Max(extraRadius, 3);
        }

        __result = Math.Max(baseRadius, extraRadius);

        return false;
    }
}
// the lit visual of a held torch follows its holder, not the local player
[HarmonyPatch(typeof(TraitToolTorch), nameof(TraitToolTorch.IsLit), MethodType.Getter)]
internal class TorchIsLitPatch
{
    [HarmonyPrefix]
    internal static bool OnIsLit(TraitToolTorch __instance, ref bool __result)
    {
        if (__instance.owner.GetRootCard() is not Chara { IsPC: false, IsPlayer: true } holder) {
            return true;
        }

        __result = holder.GetCondition<ConTorch>() != null;
        return false;
    }
}
