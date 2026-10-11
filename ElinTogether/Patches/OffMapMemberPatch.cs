using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The game takes every member of the party to stand on the map shown. Here a member can be on another map,
///     a bigger one: its tile does not exist on this one, and whatever reads that tile threw (a prayer that heals
///     the party, the end of a night). Such a member gets what the game gives, without what needs the tile
/// </summary>
[HarmonyPatch]
internal class OffMapMemberPatch
{
    private static bool OffMap(Card card)
    {
        return card.GetRootCard().pos is not { IsValid: true };
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.PlayEffect), typeof(string), typeof(bool), typeof(float), typeof(UnityEngine.Vector3))]
    internal static bool OnPlayEffect(Card __instance, ref Effect? __result)
    {
        if (!OffMap(__instance)) {
            return true;
        }

        __result = null;
        return false;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Card), nameof(Card.PlayEffect), typeof(int), typeof(bool), typeof(float))]
    internal static bool OnPlayElementEffect(Card __instance)
    {
        return !OffMap(__instance);
    }

    // (the tile only says whether the sun shines on the sleeper and whether a pillow lies there)
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.OnSleep), typeof(Thing), typeof(int))]
    internal static bool OnSleep(Chara __instance, Thing? bed, int days)
    {
        if (!OffMap(__instance)) {
            return true;
        }

        __instance.OnSleep(bed is null ? 20 : bed.Power + bed.Evalue(750) * 5, days);
        return false;
    }
}
