using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The settings of a container of the map: the shared/personal flag, the storage rules (priority, no rotten,
///     only rottable, categories, advanced distribution, user filter, autodump, exclude from crafting, compress)
///     that residents, crafting and quests use, and what a player sets on the container itself (name, icon, size
///     and colour of its grid, sort). They are saved with the container, in the world of the host: every copy of
///     the world agrees on them, or what a guest sets is gone with its copy. Where the window stands on the screen
///     and whether it is open stay each player's
/// </summary>
[MessagePackObject]
public class InvSaveDataDelta : ElinDelta
{
    // name of a window slot, not of a container (all floating containers share one): the wire format only
    [Key(0)]
    public required string WindowId { get; init; }

    [Key(1)]
    public required LZ4Bytes Data { get; init; }

    // the wire format only: the sort of a shop is a preference of the player
    [Key(2)]
    public required bool IsShop { get; init; }

    // the container the flag belongs to, none from an older peer
    [Key(3)]
    public RemoteCard? Container { get; init; }

    // the name and the icon the player gave the container; not told by a game that only tells the rules
    [Key(4)]
    public bool WithCard { get; init; }

    [Key(5)]
    public string? AltName { get; init; }

    [Key(6)]
    public int Icon { get; init; }

    internal static InvSaveDataDelta Of(Card container, Window.SaveData data)
    {
        return new() {
            WindowId = "",
            Data = LZ4Bytes.Create(data),
            IsShop = false,
            Container = container,
            WithCard = true,
            AltName = container.c_altName,
            Icon = container.c_indexContainerIcon,
        };
    }

    /// <summary>
    ///     A bag, an ally, a shop and what a character carries belong to that player, not to the map
    /// </summary>
    internal static bool IsOfTheMap(Card container)
    {
        return container is { IsContainer: true, isChara: false, isNPCProperty: false } &&
               container.trait is not TraitChestMerchant && container.GetRootCard() is not Chara;
    }

    protected override void OnApply(ElinNetBase net)
    {
        if (Container?.Find() is not { } container || !IsOfTheMap(container) ||
            Data.Decompress<Window.SaveData>() is not { } data) {
            return;
        }

        // the host tells the others (the sender too: the same state twice changes nothing)
        if (net is ElinNetHost host) {
            if (!host.ActiveRemoteCharas.ContainsKey(OriginPeer)) {
                return;
            }

            // only the host manages the base: the sender gets the settings the host keeps, which puts its copy back
            if (NetSession.Instance.Rules.HostManagesBase && !host.IsZoneSession) {
                if (container.c_windowSaveData is { } kept) {
                    host.SendDeltaTo(OriginPeer, Of(container, kept));
                }

                return;
            }

            host.Delta.AddRemote(this);
        }

        // saved with the container itself; nothing here for pref.*
        var saveData = container.c_windowSaveData ??= new Window.SaveData { useBG = true };
        var look = Look(saveData);
        saveData.sharedType = data.sharedType;
        CopyRules(data, saveData);
        if (WithCard) {
            container.c_altName = AltName;
            container.c_indexContainerIcon = Icon;
        }

        InvSettingsWatch.Received(container, saveData);

        // the window is open here too: it uses the same saveData
        var inv = LayerInventory.listInv.Find(l => l.invs.Count > 0 && l.invs[0].owner.Container == container)?.invs[0];
        if (inv == null) {
            return;
        }

        if (WithCard) {
            if (look != Look(saveData)) {
                inv.RefreshWindow();
                inv.RefreshGrid();
            }

            if (container.isThing) {
                LayerInventory.SetDirty(container.Thing);
            }
        }

        var button = inv.window.buttonShared;
        if (button == null) {
            return;
        }

        var flag = saveData.sharedType == ContainerSharedType.Shared;
        button.image.sprite = flag ? EMono.core.refs.icons.shared : EMono.core.refs.icons.personal;
        button.tooltip.lang = flag ? "hintShared" : "hintPrivate";
    }

    // everything the menus of the window set, but the place of the window (x, y, w, h, anchors, fixed) and whether it is open
    private static void CopyRules(Window.SaveData from, Window.SaveData to)
    {
        to.priority = from.priority;
        to.flag = from.flag;
        to.advDistribution = from.advDistribution;
        to.noRotten = from.noRotten;
        to.onlyRottable = from.onlyRottable;
        to.excludeCraft = from.excludeCraft;
        to.excludeDump = from.excludeDump;
        to.compress = from.compress;
        to.autodump = from.autodump;
        to.cats = new HashSet<int>(from.cats ?? []);
        to.filter = from.filter;
        to._filterStrs = null;

        to.size = from.size;
        to.columns = from.columns;
        to.color = from.color;
        to.useBG = from.useBG;
        to.category = from.category;
        // (the number itself: read back, "no sort chosen" comes out as a sort)
        to.ints[15] = from.ints[15];
        to.sort_ascending = from.sort_ascending;
        to.alwaysSort = from.alwaysSort;
        to.noRightClickClose = from.noRightClickClose;
        to.shiftToShowMenu = from.shiftToShowMenu;
    }

    // what makes the window of the container look different
    private static string Look(Window.SaveData d)
    {
        return string.Join("|", d.size, d.columns, d.ints[8], d.useBG, (int)d.category, d.ints[15], d.sort_ascending, d.alwaysSort);
    }

    /// <summary>
    ///     What is told to the other games, as a text: a change is found by comparing it before and after
    /// </summary>
    internal static string State(Card container, Window.SaveData d)
    {
        return string.Join("|", (int)d.sharedType, d.priority, (int)d.flag, d.advDistribution, d.noRotten, d.onlyRottable, d.excludeCraft,
            d.excludeDump, d.compress, (int)d.autodump, d.filter, string.Join(",", (d.cats ?? []).OrderBy(i => i)),
            Look(d), d.noRightClickClose, d.shiftToShowMenu, container.c_altName, container.c_indexContainerIcon);
    }
}
