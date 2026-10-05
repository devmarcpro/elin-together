using System.Collections.Generic;
using System.Linq;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;
using UnityEngine;

namespace ElinTogether.Patches;

/// <summary>
///     The areas of the base are changed from the area modes, their menu, the "delete" button of the inspector:
///     the state of all of them is compared with what it was a moment ago, as the names are, see
///     <see cref="AreaStateDelta" />
/// </summary>
internal static class AreaWatch
{
    private static Map? _map;
    private static ElinNetBase? _connection;
    private static int _hash;
    private static float _next;

    // what this game told lately: the host sends it back to everyone, it must not be taken as news
    private static readonly List<int> _sent = [];

    /// <summary>
    ///     What is there now is known to everyone (it just came from someone else)
    /// </summary>
    internal static void Accept()
    {
        _map = EClass._map;
        _connection = NetSession.Instance.Connection;
        _hash = Hash();
        _sent.Clear();
    }

    /// <summary>
    ///     A state this game itself sent a moment ago, coming back
    /// </summary>
    internal static bool IsEcho(int hash)
    {
        // once: the same state told later by someone else is news (an area removed again, for instance)
        return _sent.Remove(hash);
    }

    internal static void Update()
    {
        // four looks a second are plenty for a click, and the state is only compared as text
        if (EClass._map is not { } map || ZoneActivateEvent.IsHappening || EClass.game.isLoading ||
            Time.unscaledTime < _next) {
            return;
        }

        _next = Time.unscaledTime + 0.25f;
        var hash = Hash();
        // another map (a zone entered, the host's map loaded) or another connection: what it holds is what
        // everyone has, nothing to tell yet
        if (!ReferenceEquals(map, _map) || !ReferenceEquals(NetSession.Instance.Connection, _connection)) {
            _map = map;
            _connection = NetSession.Instance.Connection;
            _hash = hash;
            _sent.Clear();
            return;
        }

        if (hash == _hash) {
            return;
        }

        _hash = hash;
        _sent.Add(hash);
        if (_sent.Count > 8) {
            _sent.RemoveAt(0);
        }

        switch (NetSession.Instance.Connection) {
            case ElinNetHost host:
                host.Delta.AddRemote(AreaStateDelta.Create());
                break;
            case ElinNetClient client when NetSession.Instance.Rules.AllowGuestBuild:
                client.Delta.AddRemote(AreaStateDelta.Create());
                break;
        }
    }

    private static int Hash()
    {
        return Hash(EClass._map.rooms.listArea);
    }

    internal static int Hash(List<Area> areas)
    {
        return string.Join("|", areas.Select(Sign)).GetHashCode();
    }

    /// <summary>
    ///     What a player sets of an area: its number, kind, settings and cells, read field by field. Not its JSON:
    ///     the game's writer numbers every object anew at each call, and the task list changes by itself, so every
    ///     look would tell a "new" state (and undo what the other player just did)
    /// </summary>
    internal static string Sign(Area area)
    {
        return area.uid + ":" + area.type?.id + ":" + string.Join(",", area.type?.uidCharas ?? []) + ":" + area.data?.name + ":" +
               string.Join(",", area.data?.ints ?? []) + ":" + string.Join(",", area.points.Select(p => p.x + "-" + p.z));
    }
}

/// <summary>
///     The number of the area being drawn is taken when the mode is set, from this game's counter: another game
///     may have drawn an area with it since, and AddArea would fail on the register
/// </summary>
[HarmonyPatch(typeof(AM_CreateArea), nameof(AM_CreateArea.OnProcessTiles))]
internal static class AreaUidPatch
{
    [HarmonyPrefix]
    internal static void OnCreate(AM_CreateArea __instance)
    {
        var rooms = EClass._map.rooms;
        if (__instance.area is { } area && rooms.mapIDs.TryGetValue(area.uid, out var other) && other != area) {
            rooms.AssignUID(area);
        }
    }
}
