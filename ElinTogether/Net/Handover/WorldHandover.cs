using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Models;

namespace ElinTogether.Net;

/// <summary>
///     Council 9, step 4, prepared and not switched on: what a guest needs to know to take the world over when
///     its host is gone. Nothing in here is called by the game yet, and nothing in here starts anything: the
///     takeover itself is another piece of work, after trials on two PCs
/// </summary>
internal static class WorldHandover
{
    /// <summary>
    ///     The guest whose turn it is has that long to open the world, then it is the next one's turn
    /// </summary>
    internal const float TurnSeconds = 120f;

    // the world this game last played in as a guest, and who was in it, as of the host's last save
    private static WorldCopyManifest? _last;
    private static ulong _me;
    private static ulong[] _guests = [];

    /// <summary>
    ///     A whole copy of a world kept on this disk
    /// </summary>
    internal readonly struct Copy
    {
        internal required string Dir { get; init; }
        internal required string World { get; init; }
        internal required ulong Host { get; init; }
        internal required int Handover { get; init; }
        internal required DateTime SavedUtc { get; init; }
        internal required int Files { get; init; }
        internal required long Bytes { get; init; }

        /// <summary>
        ///     The highest handover number wins, then the latest save: two games that both went on with the same
        ///     world are told apart by who took it over last
        /// </summary>
        internal bool IsNewerThan(int handover, DateTime savedUtc)
        {
            return Handover != handover ? Handover > handover : SavedUtc > savedUtc;
        }

        public override string ToString()
        {
            return $"{World} of {Host}, handover {Handover}, saved {SavedUtc:u}, {Files} files, {Bytes} bytes";
        }
    }

    /// <summary>
    ///     Every save the host offers: which world this is and who plays in it
    /// </summary>
    internal static void Remember(WorldCopyManifest offer)
    {
        var session = NetSession.Instance;
        _last = offer;
        _me = session.Self is { } self ? (ulong)self.User : 0UL;
        // the host is the player 0 of its own list
        _guests = session.CurrentPlayers.Where(p => p.Index != 0).Select(p => (ulong)p.User).ToArray();
    }

    /// <summary>
    ///     "I have a whole copy of the world I was playing in, of that handover number, saved at that time",
    ///     null when there is none. Whole means every file was checked when the copy was closed; see
    ///     <see cref="Verify" /> to read them again
    /// </summary>
    internal static Copy? Mine()
    {
        return _last is null ? null : Find(_last.Host, _last.World);
    }

    internal static Copy? Find(ulong host, string world)
    {
        var folder = WorldCopyStore.Folder(new() { Host = host, World = world });
        foreach (var (dir, manifest) in WorldCopyStore.Copies(folder)) {
            return new Copy {
                Dir = dir,
                World = manifest.World,
                Host = manifest.Host,
                Handover = manifest.Handover,
                SavedUtc = new(manifest.Saved, DateTimeKind.Utc),
                Files = manifest.Files.Length,
                Bytes = manifest.Files.Sum(f => f.Size),
            };
        }

        return null;
    }

    /// <summary>
    ///     Reads every file of the copy again: before a world is opened from it. Not on the game's thread
    /// </summary>
    internal static bool Verify(Copy copy)
    {
        return WorldCopyStore.Copies(System.IO.Path.GetDirectoryName(copy.Dir)!)
            .Any(c => c.Dir == copy.Dir && WorldCopyStore.Verify(c.Dir, c.Manifest));
    }

    /// <summary>
    ///     Who takes the world over: the smallest Steam id among the guests, and the next one for every
    ///     <see cref="TurnSeconds" /> gone by without the world being open again. Every guest finds the same
    ///     answer from the same list without asking anyone. 0 when there is nobody
    /// </summary>
    internal static ulong Successor(IEnumerable<ulong> guests, float secondsWithoutHost)
    {
        var order = guests.Where(g => g != 0).Distinct().OrderBy(g => g).ToArray();
        if (order.Length == 0) {
            return 0;
        }

        var turn = (int)(Math.Max(0f, secondsWithoutHost) / TurnSeconds);
        return order[Math.Min(turn, order.Length - 1)];
    }

    /// <summary>
    ///     This game is the one to take over the world it was last a guest of, that long after its host was lost
    /// </summary>
    internal static bool IsMyTurn(float secondsWithoutHost)
    {
        return _me != 0 && Successor(_guests, secondsWithoutHost) == _me && Mine() is not null;
    }

#if DEBUG
    internal static string State =>
        $"mine: {Mine()?.ToString() ?? "none"}; me {_me}; guests {string.Join(",", _guests)}; first {Successor(_guests, 0f)}";
#endif
}
