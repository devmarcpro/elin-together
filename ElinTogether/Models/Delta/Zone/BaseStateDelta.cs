using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     What changed in the base (research board, hearth skills, what a research gives), host to clients: nothing of the
///     base comes back to a client after it arrived, its copy only changed with its own clicks. Each part is sent only
///     when it changed, the client sets what it holds to the host's values <br />
///     Sent by the host when a research is completed or a skill is raised, see <see cref="RemoteBasePaidPatch" /> and
///     <see cref="BaseRequestDelta" />. A recipe a research gives goes by <see cref="AddRecipeDelta" /> as any other
/// </summary>
[MessagePackObject]
public class BaseStateDelta : ElinDelta
{
    /// <summary>
    ///     The base this is about: the zone that owns it
    /// </summary>
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     The whole research manager (plans, finished, new, focused)
    /// </summary>
    [Key(1)]
    public LZ4Bytes? Researches { get; init; }

    [Key(2)]
    public LZ4Bytes? Policies { get; init; }

    [Key(3)]
    public int? Knowledge { get; init; }

    /// <summary>
    ///     Base value of the elements of the base that changed
    /// </summary>
    [Key(4)]
    public Dictionary<int, int>? Elements { get; init; }

    /// <summary>
    ///     What a research may change, taken before it is completed to tell what did
    /// </summary>
    internal sealed class Before(FactionBranch branch)
    {
        internal readonly Dictionary<int, int> Elements = branch.elements.dict.ToDictionary(p => p.Key, p => p.Value.vBase);
        internal readonly int Policies = branch.policies.list.Count;
    }

    internal static BaseStateDelta ForResearch(FactionBranch branch, Before before)
    {
        return new() {
            ZoneUid = branch.owner.uid,
            Researches = LZ4Bytes.Create(branch.researches),
            Policies = branch.policies.list.Count == before.Policies ? null : LZ4Bytes.Create(branch.policies),
            Knowledge = branch.resources.knowledge.value,
            Elements = Changed(branch, before.Elements),
        };
    }

    internal static BaseStateDelta ForSkill(FactionBranch branch, int id)
    {
        return new() {
            ZoneUid = branch.owner.uid,
            Elements = new() { [id] = branch.elements.dict.TryGetValue(id, out var element) ? element.vBase : 0 },
        };
    }

    private static Dictionary<int, int>? Changed(FactionBranch branch, Dictionary<int, int> before)
    {
        var changed = branch.elements.dict
            .Where(p => !before.TryGetValue(p.Key, out var value) || value != p.Value.vBase)
            .ToDictionary(p => p.Key, p => p.Value.vBase);
        return changed.Count == 0 ? null : changed;
    }

    /// <summary>
    ///     What the game does after the purchase: the open windows show the new state, a new skill may add what the
    ///     hotbar and the menu offer
    /// </summary>
    internal static void Refresh(FactionBranch branch, bool elements)
    {
        branch.resources.SetDirty();

        if (ui.GetLayer<LayerTech>() is { } tech) {
            tech.RefreshTech();
        }

        if (ui.GetLayer<LayerHome>() is { } home && home.listFeat.callbacks != null) {
            home.listFeat.List();
        }

        if (!elements) {
            return;
        }

        player.hotbars.ResetHotbar(2);
        if (WidgetHotbar.HotBarMainMenu) {
            WidgetHotbar.HotBarMainMenu.RebuildPage();
        }

        if (WidgetMenuPanel.Instance) {
            WidgetMenuPanel.Instance.OnChangeActionMode();
        }
    }

    protected override void OnApply(ElinNetBase net)
    {
        // host to clients only, and for a base this game knows
        if (net is not ElinNetClient { IsZoneSession: false } || game.spatials.Find(ZoneUid)?.branch is not { } branch) {
            return;
        }

        if (Researches is not null) {
            var researches = Researches.Decompress<ResearchManager>();
            branch.researches = researches;
            researches.SetOwner(branch);
        }

        if (Policies is not null) {
            var policies = Policies.Decompress<PolicyManager>();
            branch.policies = policies;
            policies.SetOwner(branch);
        }

        // the field, not Mod: Mod would tell the host it was the client that spent it (HomeResourceModEvent)
        if (Knowledge is { } knowledge) {
            branch.resources.knowledge.value = knowledge;
        }

        foreach (var (id, value) in Elements ?? new Dictionary<int, int>()) {
            var current = branch.elements.dict.TryGetValue(id, out var element) ? element.vBase : 0;
            if (current != value) {
                branch.elements.ModBase(id, value - current);
            }
        }

        Refresh(branch, Elements is { Count: > 0 });
    }
}
