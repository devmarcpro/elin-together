using ElinTogether.Helper;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The end of a reading runs for another player as for a resident: the ancient book it deciphers is used up
///     in one go, and a god's book converts it, which its own game never hears of. A player keeps the book and
///     its god, as the local one does
/// </summary>
[HarmonyPatch]
internal static class TraitBaseSpellbookPatch
{
    private static Chara? _reader;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(TraitBaseSpellbook), nameof(TraitBaseSpellbook.OnRead))]
    internal static void OnRead(Chara c, out Chara? __state)
    {
        __state = _reader;
        _reader = c is { IsPC: false, IsRemotePlayer: true } ? c : null;
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(TraitBaseSpellbook), nameof(TraitBaseSpellbook.OnRead))]
    internal static void OnReadEnd(Chara? __state)
    {
        _reader = __state;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(TraitBaseSpellbook), nameof(TraitBaseSpellbook.ModCharge))]
    internal static bool OnModCharge(TraitBaseSpellbook __instance, Chara c, ref int a)
    {
        if (_reader is null || c != _reader) {
            return true;
        }

        switch (__instance.BookType) {
            // the game takes no charge from the local player for a book it deciphered
            case TraitBaseSpellbook.Type.Ancient:
                return false;
            // one charge, not the whole book
            case TraitBaseSpellbook.Type.Dojin:
                a = -1;
                return true;
            default:
                return true;
        }
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Religion), nameof(Religion.JoinFaith))]
    internal static bool OnJoinFaith(Chara c)
    {
        return _reader is null || c != _reader;
    }
}
