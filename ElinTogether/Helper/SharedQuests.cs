using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     The one quest log of the world, whoever accepts, advances or completes a quest
/// </summary>
internal static class SharedQuests
{
    private const float HostAnswerTimeout = 10f;

    private static readonly Dictionary<Quest, float> _awaitingHost = [];

    /// <summary>
    ///     A story quest a dialog started on a client: kept in the quest log, without a number, until the host
    ///     starts it for everyone, so the dialog can go on with it
    /// </summary>
    internal static void AwaitHost(Quest quest)
    {
        _awaitingHost[quest] = Time.unscaledTime + HostAnswerTimeout;
    }

    internal static bool IsAwaitingHost(Quest quest)
    {
        if (!_awaitingHost.TryGetValue(quest, out var until)) {
            return false;
        }

        if (Time.unscaledTime < until) {
            return true;
        }

        // the host did not take it
        _awaitingHost.Remove(quest);
        return false;
    }

    internal static void HostAnswered(string id)
    {
        foreach (var quest in _awaitingHost.Keys.Where(q => q.id == id).ToArray()) {
            _awaitingHost.Remove(quest);
        }
    }

    /// <param name="uid">negative while a quest a dialog started on a client waits for its number from the host</param>
    /// <param name="id">tells which quest it is in that case</param>
    internal static Quest? Find(int uid, string? id)
    {
        var quests = EClass.game.quests;
        return quests.list.Find(q => q.uid == uid) ??
               quests.globalList.Find(q => q.uid == uid) ??
               (uid < 0 && id is not null ? quests.list.Find(q => q.id == id) : null);
    }
}
