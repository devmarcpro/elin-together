using HarmonyLib;

namespace ElinTogether.Patches;

/// <summary>
///     A mount (or a parasite) is brought to its rider's tile by Chara.SyncRide, which first takes it off the tile
///     it says it stands on. In a world that changed hands (the depot, a guest that takes the world over, a client
///     that joins) the mount of a player's character can still say a tile of the map it was last moved on, outside
///     this one: the game then reads a cell that does not exist, and the map never finishes loading
///     (IndexOutOfRangeException in Zone.Activate, which brings the mount of every character of the map, then an
///     error at every frame). Seen on 2026-10-08 for a client and on 2026-10-09 for a world taken from the depot,
///     which nobody could load any more. A mount that stands nowhere on this map is put on its rider's tile
///     without being taken off anything <br />
///     Not one of the patches of a session (a release build only has those while a session is on, and a world
///     taken from the depot is loaded before any): put in place once, when the mod starts, under a name of its
///     own, and left there. It only acts where the game would fail
/// </summary>
internal static class RideOffMapPatch
{
    private static bool _applied;

    internal static void Apply()
    {
        if (_applied) {
            return;
        }

        _applied = true;
        try {
            // (not the id of the session patches: those are all removed when the last session closes)
            new Harmony(ModInfo.Guid + ".always").Patch(
                AccessTools.Method(typeof(Chara), nameof(Chara.SyncRide), [typeof(Chara)]),
                prefix: new(typeof(RideOffMapPatch), nameof(OnSyncRide)));
        } catch (System.Exception ex) {
            EmpLog.Warning(ex, "The guard for mounts that stand outside the map is not in place");
        }
    }

    internal static bool OnSyncRide(Chara __instance, Chara c)
    {
        if (c?.pos is not { } at || __instance.pos is not { } to || EClass._map is not { } map || map.cells is null) {
            return true;
        }

        var size = map.Size;
        if (at.x >= 0 && at.z >= 0 && at.x < size && at.z < size) {
            return true;
        }

        // the rider itself is nowhere: the game's own code says so and places it
        if (to.x < 0 || to.z < 0 || to.x >= size || to.z >= size) {
            return true;
        }

        EmpLog.Information("Mount {Uid} of chara {Rider} said the tile ({X}, {Z}), outside this map: put on its rider's tile",
            c.uid, __instance.uid, at.x, at.z);
        // (as placed on the map for the first time: nothing to take it off from)
        map._AddCard(to.x, to.z, c, true);
        return false;
    }
}
