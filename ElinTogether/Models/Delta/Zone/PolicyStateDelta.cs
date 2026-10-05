using System.Linq;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Which policies of the base are on. A player switches them in its policy window, on its own copy of the base:
///     a guest's never reached the host, who runs the base, and the host's never reached the guests <br />
///     The whole set is sent, not the click: applying it twice changes nothing
/// </summary>
[MessagePackObject]
public class PolicyStateDelta : ElinDelta
{
    [Key(0)]
    public required int[] Active { get; init; }

    internal static int[] Read(FactionBranch branch)
    {
        return branch.policies.list.Where(policy => policy.active).Select(policy => policy.id).OrderBy(id => id).ToArray();
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (_zone?.branch is not { } branch) {
            return;
        }

        if (net is ElinNetHost host) {
            // a player standing on this base, not one travelling
            if (!host.ActiveRemoteCharas.ContainsKey(OriginPeer) || host.IsAwayPeer(OriginPeer)) {
                return;
            }

            // only the host manages the base: the sender gets the set the host keeps, which puts its copy back
            if (NetSession.Instance.Rules.HostManagesBase && !host.IsZoneSession) {
                host.SendDeltaTo(OriginPeer, new PolicyStateDelta { Active = Read(branch) });
                return;
            }

            host.Delta.AddRemote(this);
        }

        foreach (var policy in branch.policies.list) {
            policy.active = Active.Contains(policy.id);
        }

        branch.policies.RefreshEffects();

        // the window open here shows it
        if (ui.GetLayer<LayerPolicy>() is { } layer) {
            layer.RefreshPolicyIcons();
        }
    }
}
