using System.Linq;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

public enum BaseRequestKind : byte
{
    /// <summary>
    ///     A plan of the research board, paid in the knowledge of the base. Id is the plan's id
    /// </summary>
    Research,

    /// <summary>
    ///     A skill of the hearth, paid in the platinum of the player. Id is the element's id
    /// </summary>
    HomeSkill,
}

public enum BaseAnswer : byte
{
    /// <summary>
    ///     A request, client to host
    /// </summary>
    None,

    Done,
    Refused,
}

/// <summary>
///     Something the base sells, asked of the host: the client's game would pay and then make it in its own copy of the
///     base only, which the host never sees. The client sends this instead and changes nothing; the host checks the
///     payment against its own state, pays and makes it, and answers the same type with <see cref="Answer" />
///     (Done or Refused) <br />
///     The new state of the base goes to everyone with <see cref="BaseStateDelta" />, see <see cref="RemoteBasePaidPatch" />
/// </summary>
[MessagePackObject]
public class BaseRequestDelta : ElinDelta
{
    // a request lost on the way must not block the next one for ever
    private const float WaitSeconds = 5f;

    private static bool _waiting;
    private static float _sentAt;

    [Key(0)]
    public required BaseRequestKind Kind { get; init; }

    [Key(1)]
    public required string Id { get; init; }

    [Key(2)]
    public BaseAnswer Answer { get; init; }

    /// <summary>
    ///     Client side: one request at a time, the next waits for the answer of the last
    /// </summary>
    internal static void Send(BaseRequestKind kind, string id)
    {
        if (NetSession.Instance.Connection is not ElinNetClient client) {
            return;
        }

        if (_waiting && UnityEngine.Time.realtimeSinceStartup - _sentAt < WaitSeconds) {
            SE.Beep();
            EmpPop.Information("emp_base_pending".lang());
            return;
        }

        _waiting = true;
        _sentAt = UnityEngine.Time.realtimeSinceStartup;
        client.Delta.AddRemote(new BaseRequestDelta {
            Kind = kind,
            Id = id,
        });
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Answer != BaseAnswer.None) {
            OnAnswer(net);
            return;
        }

        // not in a zone session: the zone's branch belongs to the world the host saves, not to the game holding the zone
        if (net is not ElinNetHost { IsZoneSession: false } host) {
            return;
        }

        // all of it is read again from this game's state, whatever the sender believed: a request that comes twice
        // or late finds the plan, the knowledge or the platinum as they are now, it cannot pay for nothing
        var done = host.ActiveRemoteCharas.TryGetValue(OriginPeer, out var sender) && !host.IsAwayPeer(OriginPeer) &&
                   _zone.branch is { } branch && Execute(host, branch, sender);

        host.SendDeltaTo(OriginPeer, new BaseRequestDelta {
            Kind = Kind,
            Id = Id,
            Answer = done ? BaseAnswer.Done : BaseAnswer.Refused,
        });
    }

    private bool Execute(ElinNetHost host, FactionBranch branch, Chara sender)
    {
        // as the host's own gesture: a recipe learnt on the way must reach everyone (AddRecipeEvent skips what is applied)
        using var simulate = Simulate();

        if (Kind == BaseRequestKind.Research) {
            // what the click does: the knowledge goes by Mod, the plan by CompletePlan (recipes, policies, feats).
            // The new state goes out from there, see RemoteBasePaidPatch.OnCompletePlan
            if (branch.researches.plans.FirstOrDefault(p => p.id == Id) is not { } plan ||
                !branch.researches.CanCompletePlan(plan)) {
                return false;
            }

            branch.resources.knowledge.Mod(-plan.source.tech);
            branch.researches.CompletePlan(plan);
            BaseStateDelta.Refresh(branch, false);
            return true;
        }

        // the list of the hearth shows these, and its click refuses the rest (LayerHome.RefreshFeat)
        if (!int.TryParse(Id, out var id) || !branch.elements.dict.TryGetValue(id, out var element) ||
            element.source.category is "policy" or "landfeat" || element.HasTag("hidden") ||
            (element.Value <= 0 && element.vBase <= 0) || element.source.cost is not { Length: > 0 } ||
            element.source.cost[0] == 0 || element.ValueWithoutLink == 0) {
            return false;
        }

        var cost = branch.GetTechUpgradeCost(element);
        if (cost == 0 || cost > sender.GetCurrency("money2")) {
            return false;
        }

        // the platinum is in the bag this game keeps of the sender, the way it reaches the sender's own bag is the one
        // of any other change made here to a player's things
        sender.ModCurrency(-cost, "money2");
        branch.elements.ModBase(id, 1);
        BaseStateDelta.Refresh(branch, true);
        host.Delta.AddRemote(BaseStateDelta.ForSkill(branch, id));
        return true;
    }

    private void OnAnswer(ElinNetBase net)
    {
        if (net is not ElinNetClient { IsZoneSession: false }) {
            return;
        }

        _waiting = false;
        if (Answer == BaseAnswer.Refused) {
            SE.Beep();
            EmpPop.Information("emp_base_refused".lang());
            return;
        }

        // the sound and the line the game makes at the end of the click, the state itself comes in BaseStateDelta
        if (Kind == BaseRequestKind.Research) {
            if (sources.researches.map.TryGetValue(Id, out var row)) {
                WidgetPopText.Say("completePlan".lang(row.GetName()), FontColor.Great);
            }

            SE.Play("good");
        } else {
            SE.Pay();
        }
    }
}
