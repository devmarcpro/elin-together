using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch(typeof(LayerEditPCC), nameof(LayerEditPCC.Apply))]
internal static class CharaAppearanceEvent
{
    [HarmonyPostfix]
    internal static void OnApplyLook(LayerEditPCC __instance)
    {
        if (NetSession.Instance.Connection is not { } connection ||
            __instance.chara is not { IsPC: true, pccData: not null } chara) {
            return;
        }

        connection.Delta.AddRemote(CharaAppearanceDelta.Create(chara));
    }
}
