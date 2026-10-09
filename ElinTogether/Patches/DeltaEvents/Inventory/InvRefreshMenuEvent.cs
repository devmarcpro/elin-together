using System.Collections.Generic;
using ElinTogether.Models;
using ElinTogether.Net;

namespace ElinTogether.Patches;

/// <summary>
///     The settings of a container of the map are changed from many places of its window (the menu of the sort
///     button and its sub menus, the dialogs they open once the menu is gone: filter, name, colour, icon, paste;
///     the shared button). Instead of following each of them, the settings of every container whose window is open
///     are looked at each frame, and what changed is told to the other games (InvSaveDataDelta) <br />
///     Before, only the storage rules were told, and only from the menu: a name, an icon, a size or a sort set by
///     a guest lived in its copy of the world and were gone with it
/// </summary>
internal static class InvSettingsWatch
{
    // container uid -> its settings as last seen here or received
    private static readonly Dictionary<int, string> _seen = [];

    /// <summary>
    ///     Called every frame while a session is on
    /// </summary>
    internal static void Tick()
    {
        // alone on a map of its own, the whole map goes back to the host with its containers
        if (NetSession.Instance.Connection is not { } connection || !EClass.core.IsGameStarted) {
            _seen.Clear();
            return;
        }

        var open = LayerInventory.listInv;
        if (open.Count == 0) {
            return;
        }

        // (containers seen long ago and destroyed since)
        if (_seen.Count > 256) {
            _seen.Clear();
        }

        for (var i = 0; i < open.Count; i++) {
            var layer = open[i];
            if (layer == null || layer.invs.Count == 0 || layer.invs[0] is not { } inv || inv.window == null ||
                inv.window.saveData is not { } data || inv.owner?.Container is not { } container ||
                !InvSaveDataDelta.IsOfTheMap(container)) {
                continue;
            }

            var now = InvSaveDataDelta.State(container, data);
            if (!_seen.TryGetValue(container.uid, out var was)) {
                _seen[container.uid] = now;
                continue;
            }

            if (was == now) {
                continue;
            }

            _seen[container.uid] = now;
            connection.Delta.AddRemote(InvSaveDataDelta.Of(container, data));
        }
    }

    /// <summary>
    ///     What another game changed is not a change of this one
    /// </summary>
    internal static void Received(Card container, Window.SaveData data)
    {
        _seen[container.uid] = InvSaveDataDelta.State(container, data);
    }
}
