using System.Collections.Generic;
using ElinTogether.Models;
using ElinTogether.Net;
using ElinTogether.Patches;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     Dialog flags are written all over the dialog scripts, so they are compared with what was last shared
///     instead of being caught where they change
/// </summary>
internal static class DialogFlagSync
{
    private const float Interval = 0.5f;

    private static readonly Dictionary<string, int> _shared = [];
    private static Dictionary<string, int>? _source;
    private static float _next;

    internal static void Tick()
    {
        if (Time.unscaledTime < _next) {
            return;
        }

        _next = Time.unscaledTime + Interval;

        if (!EClass.core.IsGameStarted || EClass.player?.dialogFlags is not { } flags) {
            return;
        }

        if (!ReferenceEquals(flags, _source)) {
            // another world, or another copy of it: what it holds is what it was given
            _source = flags;
            _shared.Clear();
            foreach (var (id, value) in flags) {
                _shared[id] = value;
            }

            return;
        }

        List<DialogFlagDelta>? changed = null;
        foreach (var (id, value) in flags) {
            if (_shared.TryGetValue(id, out var shared) && shared == value) {
                continue;
            }

            (changed ??= []).Add(new() {
                Id = id,
                Value = value,
            });
        }

        if (changed is null) {
            return;
        }

        foreach (var delta in changed) {
            _shared[delta.Id] = delta.Value;

            QuestAwaySync.Send(delta);
            NetSession.Instance.Connection?.Delta.AddRemote(delta);
        }
    }

    internal static void Learn(string id, int value)
    {
        if (EClass.player?.dialogFlags is not { } flags) {
            return;
        }

        flags[id] = value;
        if (ReferenceEquals(flags, _source)) {
            _shared[id] = value;
        }
    }
}
