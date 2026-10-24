using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using HarmonyLib;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The gold statue of Mani: a guest picks a gene in its window (InvOwnerChoose.Process). Its game spent its own
///     copy of the statue only: on the host the statue stayed gold and could be used again (hunt 2 row 27). The host
///     does what the pick does, for the guest; the gene, the spent statue and the message travel as any other
/// </summary>
[MessagePackObject]
public class ManiGeneRequest : ElinDelta
{
    [Key(0)]
    public required RemoteCard Statue { get; init; }

    [Key(1)]
    public required RemoteCard Gene { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host || !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) ||
            Statue.Find() is not Thing { isDestroyed: false, isOn: true, trait: TraitPowerStatue } statue ||
            Gene.Find() is not Thing gene || gene.parent != statue) {
            return;
        }

        using var simulate = Simulate();
        using var told = MsgRelayContext.RedirectTo(sender);
        statue.ChangeMaterial("onyx");
        statue.trait.OnUse(sender);
        sender.PickOrDrop(sender.pos, gene);
        statue.things.DestroyAll();
    }

    [HarmonyPatch(typeof(InvOwnerChoose), nameof(InvOwnerChoose.Process))]
    internal static class Ask
    {
        [HarmonyPrefix]
        internal static bool OnProcess(InvOwnerChoose __instance, ButtonGrid button, ref bool __result)
        {
            if (NetSession.Instance.Connection is not ElinNetClient client || IsApplying ||
                __instance.owner.trait is not TraitPowerStatue || !button || button.card?.parent != __instance.owner) {
                return true;
            }

            client.Delta.AddRemote(new ManiGeneRequest { Statue = __instance.owner, Gene = button.card });
            EClass.ui.CloseLayers();
            __result = true;
            return false;
        }
    }
}
