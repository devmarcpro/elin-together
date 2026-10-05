using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The shared/personal flag of a container of the map: companions, crafting and quests use the shared ones, so
///     every copy of the world must agree on it. The sort mode and the window layout are the screen of each player
///     (pref.sortInv, the bag window) and never travel
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

        // saved with the container itself; nothing here for pref.* or for the layout of a window
        var saveData = container.c_windowSaveData ??= new Window.SaveData { useBG = true };
        saveData.sharedType = data.sharedType;

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
}
