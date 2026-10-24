using ElinTogether.Net;
using HarmonyLib;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A guest sends away a summoned minion ("Banish summon", ActPlan): its game removed its own copy only, which is
///     never authoritative (CardDestroyEvent), and the summon kept fighting on the host and came back (hunt 2 row
///     13). The host sends it away, the removal reaches everyone as any other
/// </summary>
[MessagePackObject]
public class CharaBanishRequest : ElinDelta
{
    [Key(0)]
    public required RemoteCard Target { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is not ElinNetHost host || !host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) ||
            Target.Find() is not Chara { IsPCFactionMinion: true, isDestroyed: false } minion || minion.currentZone != EClass._zone) {
            return;
        }

        using var simulate = Simulate();
        minion.Banish(sender);
    }

    [HarmonyPatch(typeof(Chara), nameof(Chara.Banish))]
    internal static class Ask
    {
        [HarmonyPrefix]
        internal static void OnBanish(Chara __instance, Chara owner)
        {
            if (NetSession.Instance.Connection is ElinNetClient client && !IsApplying && owner is { IsPC: true }) {
                // (the host checks it is a minion: the guest's copy may not know its master)
                client.Delta.AddRemote(new CharaBanishRequest { Target = __instance });
            }
        }
    }
}
