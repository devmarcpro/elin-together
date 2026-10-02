using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal class AddRecipeEvent
{
    [HarmonyPostfix]
    [HarmonyPatch(typeof(RecipeManager), nameof(RecipeManager.Add))]
    internal static void OnAddRecipe(string id)
    {
        if (NetSession.Instance.Connection is not { } connection || AddRecipeDelta.IsLanding) {
            return;
        }

        // the recipe a player comes up with while harvesting, digging or mining is found when the end of its
        // own task is replayed here: the host, for whom that character is not "the player", never rolls for it
        var ownTask = CharaProgressCompleteDelta.Current?.Owner.Find() is Chara { IsPC: true };
        if (ElinDelta.IsApplying && !ownTask) {
            return;
        }

        connection.Delta.AddRemote(new AddRecipeDelta {
            RecipeId = id,
        });
    }
}
