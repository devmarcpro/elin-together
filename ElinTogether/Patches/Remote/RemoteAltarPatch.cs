using ElinTogether.Helper;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The dice of an offering on an altar. Every game plays TraitAltar.OnOffer for the offerer, and the duel of
///     faiths of an offering to another god is rolled there: with nothing shared the altar could change god in one
///     game only. The offerer rolls the dice, InvOwnerOnProcessDelta carries them, every game plays the duel with them
/// </summary>
internal static class AltarDice
{
    // set by whoever is about to play OnOffer, taken (and cleared) when it starts
    internal static int Next;

    // the dice of the OnOffer being played, 0 for none
    internal static int Current;

    internal static Chara? Offerer;

    internal static int Roll()
    {
        return Next = 1 + EClass.rnd(int.MaxValue - 1);
    }
}

[HarmonyPatch(typeof(TraitAltar), nameof(TraitAltar.OnOffer))]
internal static class AltarOfferPatch
{
    [HarmonyPrefix]
    internal static void Before(Chara c, out (int Dice, Chara? Who) __state)
    {
        __state = (AltarDice.Current, AltarDice.Offerer);
        (AltarDice.Current, AltarDice.Next, AltarDice.Offerer) = (AltarDice.Next, 0, c);
    }

    [HarmonyFinalizer]
    internal static void After((int Dice, Chara? Who) __state)
    {
        if (AltarDice.Current != 0) {
            Rand.SetSeed();
        }

        (AltarDice.Current, AltarDice.Offerer) = __state;
    }
}

/// <summary>
///     The duel rolls "rnd(value) > rnd(200)" right after asking the value: the dice are set again there, so that
///     nothing drawn before (effects, sounds) can shift them from one game to the other
/// </summary>
[HarmonyPatch(typeof(Religion), nameof(Religion.GetOfferingValue))]
internal static class AltarDiceReseed
{
    [HarmonyPostfix]
    internal static void After()
    {
        if (AltarDice.Current != 0) {
            Rand.SetSeed(AltarDice.Current);
        }
    }
}

/// <summary>
///     The game puts the reforged artifact at the feet of "the player", which for the host is the host, whoever
///     made the offering: it goes next to the one who offered
/// </summary>
[HarmonyPatch(typeof(ReligionManager), nameof(ReligionManager.Reforge))]
internal static class AltarReforgePatch
{
    [HarmonyPrefix]
    internal static void Before(ref Point? pos)
    {
        if (pos is null && NetSession.Instance.Connection is ElinNetHost && AltarDice.Offerer is { IsRemotePlayer: true } who) {
            pos = who.pos.Copy();
        }
    }
}
