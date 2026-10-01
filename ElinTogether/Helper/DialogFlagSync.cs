using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using ElinTogether.Models;
using ElinTogether.Net;
using ElinTogether.Patches;
using UnityEngine;

namespace ElinTogether.Helper;

/// <summary>
///     What the story remembers is the same for every player, like the quest log: dialog flags, story flags,
///     key items, the debt. These are written all over the game, so they are compared with what was last shared
///     instead of being caught where they change
/// </summary>
internal static class DialogFlagSync
{
    private const float Interval = 0.5f;

    private const string Dialog = "d:";
    private const string Story = "f:";
    private const string KeyItem = "k:";
    private const string Debt = "p:debt";

    /// <summary>
    ///     Flags about one player's screen or body, not about the story
    /// </summary>
    private static readonly HashSet<string> _personal = [
        nameof(Player.Flags.gotClickReward),
        nameof(Player.Flags.welcome),
        nameof(Player.Flags.helpHighlightDisabled),
        nameof(Player.Flags.isShoesOff),
        nameof(Player.Flags.backpackHighlightDisabled),
        nameof(Player.Flags.abilityHighlightDisabled),
        nameof(Player.Flags.toggleHotbarHighlightDisabled),
        nameof(Player.Flags.toggleHotbarHighlightActivated),
        nameof(Player.Flags.debugEnabled),
        nameof(Player.Flags.gotMelilithCurse),
        nameof(Player.Flags.gotEtherDisease),
    ];

    private static readonly PropertyInfo[] _storyFlags = typeof(Player.Flags)
        .GetProperties(BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly)
        .Where(p => p.CanRead && p.CanWrite && (p.PropertyType == typeof(bool) || p.PropertyType == typeof(int)))
        .Where(p => !_personal.Contains(p.Name))
        .ToArray();

    private static readonly Dictionary<string, int> _shared = [];
    private static Player? _source;
    private static float _next;

    internal static void Tick()
    {
        if (Time.unscaledTime < _next) {
            return;
        }

        _next = Time.unscaledTime + Interval;

        if (!EClass.core.IsGameStarted || EClass.player is not { } player) {
            return;
        }

        var current = Read(player);

        if (!ReferenceEquals(player, _source)) {
            // another world, or another copy of it: what it holds is what it was given
            _source = player;
            _shared.Clear();
            foreach (var (id, value) in current) {
                _shared[id] = value;
            }

            return;
        }

        foreach (var (id, value) in current) {
            if (_shared.TryGetValue(id, out var shared) && shared == value) {
                continue;
            }

            _shared[id] = value;

            var delta = new DialogFlagDelta {
                Id = id,
                Value = value,
            };
            QuestAwaySync.Send(delta);
            NetSession.Instance.Connection?.Delta.AddRemote(delta);
        }
    }

    internal static void Learn(string id, int value)
    {
        if (EClass.player is not { } player) {
            return;
        }

        if (id.StartsWith(Dialog)) {
            player.dialogFlags[id[Dialog.Length..]] = value;
        } else if (id.StartsWith(KeyItem) && int.TryParse(id[KeyItem.Length..], out var item)) {
            player.keyItems[item] = value;
        } else if (id == Debt) {
            player.debt = value;
        } else if (id.StartsWith(Story) && _storyFlags.FirstOrDefault(p => p.Name == id[Story.Length..]) is { } flag) {
            flag.SetValue(player.flags, flag.PropertyType == typeof(bool) ? value != 0 : value);
        } else {
            return;
        }

        if (ReferenceEquals(player, _source)) {
            _shared[id] = value;
        }
    }

    private static Dictionary<string, int> Read(Player player)
    {
        var values = new Dictionary<string, int>();

        foreach (var (id, value) in player.dialogFlags) {
            values[Dialog + id] = value;
        }

        foreach (var (item, count) in player.keyItems) {
            values[KeyItem + item] = count;
        }

        foreach (var flag in _storyFlags) {
            values[Story + flag.Name] = flag.GetValue(player.flags) switch {
                bool set => set ? 1 : 0,
                int number => number,
                _ => 0,
            };
        }

        values[Debt] = player.debt;
        return values;
    }
}
