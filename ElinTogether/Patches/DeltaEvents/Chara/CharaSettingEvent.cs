using ElinTogether.Helper;
using System.Linq;
using ElinTogether.Models;
using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     The settings a dialog menu writes on the character talked to, see <see cref="CharaSettingDelta" />: read
///     when the dialog is built, compared when it closes
/// </summary>
[HarmonyPatch]
internal static class CharaSettingEvent
{
    private static Chara? _talkedTo;
    private static int[] _before = [];

    // the extra tax of the month, chosen in the same menus (ExtraTaxDelta)
    private static int _extraTax = -1;

    [HarmonyPrefix]
    [HarmonyPatch(typeof(DramaCustomSequence), nameof(DramaCustomSequence.Build))]
    internal static void OnDialogBuilt(Chara c)
    {
        _extraTax = EClass.player?.extraTax ?? -1;
        if (c is null || c.IsPlayer) {
            return;
        }

        _talkedTo = c;
        _before = CharaSettingDelta.Read(c);
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(LayerDrama), nameof(LayerDrama.OnKill))]
    internal static void OnDialogClosed()
    {
        if (_extraTax >= 0 && EClass.player is { } player && player.extraTax != _extraTax) {
            ExtraTaxDelta.Emit();
        }

        _extraTax = -1;
        if (_talkedTo is not { } chara) {
            return;
        }

        _talkedTo = null;
        if (!chara.isDestroyed && !CharaSettingDelta.Read(chara).SequenceEqual(_before)) {
            CharaSettingDelta.Emit(chara);
        }
    }
}
