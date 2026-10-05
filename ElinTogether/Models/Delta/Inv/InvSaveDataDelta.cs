using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The shared/personal flag and the rules of a container of the map (priority, no rotten, only rottable, categories,
///     advanced distribution, user filter, autodump, exclude from crafting, compress): residents, crafting and quests
///     use them, so every copy of the world must agree on it. The sort mode and the window layout are the screen of each
///     player (pref.sortInv, the bag window) and never travel
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

    protected override void OnApply(ElinNetBase net)
    {
        if (Container?.Find() is not { IsContainer: true } container || container.GetRootCard() is Chara ||
            Data.Decompress<Window.SaveData>() is not { } data) {
            return;
        }

        // the host tells the others (the sender too: the same state twice changes nothing)
        if (net is ElinNetHost host) {
            if (!host.ActiveRemoteCharas.ContainsKey(OriginPeer)) {
                return;
            }

            host.Delta.AddRemote(this);
        }

        // saved with the container itself; nothing here for pref.* or for the layout of a window
        var saveData = container.c_windowSaveData ??= new Window.SaveData { useBG = true };
        saveData.sharedType = data.sharedType;
        CopyRules(data, saveData);

        // the window is open here too: its button shows the new flag (it uses the same saveData)
        var button = LayerInventory.listInv.Find(l => l.invs[0].owner.Container == container)
            ?.invs[0].window.buttonShared;
        if (button == null) {
            return;
        }

        var flag = saveData.sharedType == ContainerSharedType.Shared;
        button.image.sprite = flag ? EMono.core.refs.icons.shared : EMono.core.refs.icons.personal;
        button.tooltip.lang = flag ? "hintShared" : "hintPrivate";
    }

    // the part of the settings that is a rule of the world; the position, size, colour and sort of the window stay as they are
    private static void CopyRules(Window.SaveData from, Window.SaveData to)
    {
        to.priority = from.priority;
        to.flag = from.flag;
        to.advDistribution = from.advDistribution;
        to.noRotten = from.noRotten;
        to.onlyRottable = from.onlyRottable;
        to.excludeCraft = from.excludeCraft;
        to.compress = from.compress;
        to.autodump = from.autodump;
        to.cats = new HashSet<int>(from.cats ?? []);
        to.filter = from.filter;
        to._filterStrs = null;
    }

    /// <summary>
    ///     What <see cref="CopyRules" /> copies, as a text: the changes made in the menu are found by comparing it before and after
    /// </summary>
    internal static string Rules(Window.SaveData d)
    {
        return string.Join("|", (int)d.sharedType, d.priority, (int)d.flag, d.advDistribution, d.noRotten, d.onlyRottable, d.excludeCraft,
            d.compress, (int)d.autodump, d.filter, string.Join(",", d.cats.OrderBy(i => i)));
    }
}
