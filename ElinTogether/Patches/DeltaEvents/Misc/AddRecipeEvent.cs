using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal class AddRecipeEvent
{
    // how deep in RecipeManager.Add: the game learns the variants of a block (pillar, bridge) by calling Add again
    private static int _depth;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(RecipeManager), nameof(RecipeManager.Add))]
    internal static void OnAddRecipeBegin()
    {
        _depth++;
    }

    // a finalizer: a throw does not leave the count up
    [HarmonyFinalizer]
    [HarmonyPatch(typeof(RecipeManager), nameof(RecipeManager.Add))]
    internal static void OnAddRecipeEnd()
    {
        _depth--;
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(RecipeManager), nameof(RecipeManager.Add))]
    internal static void OnAddRecipe(string id)
    {
        // a variant learnt inside another Add: the other games learn it the same way from the outer one, and
        // told apart they counted the block twice
        if (_depth > 1 || NetSession.Instance.Connection is not { } connection || AddRecipeDelta.IsLanding) {
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
