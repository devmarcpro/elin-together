using System.Collections.Generic;
using ElinTogether.Models;
using ElinTogether.Net;

namespace ElinTogether.Helper;

/// <summary>
///     What a dialog gives when a client is the one talking. A client cannot create things, they would vanish at
///     the end of the frame: the host creates them instead, at the same place, for everyone to see
/// </summary>
internal static class StoryGifts
{
    private static readonly List<Thing> _offered = [];

    internal static void Offer(Thing thing)
    {
        if (!_offered.Contains(thing)) {
            _offered.Add(thing);
        }
    }

    /// <summary>
    ///     End of the frame, before the client's own copies go: what the story code did to the gift after
    ///     dropping it (identified, charges, material) is in by now
    /// </summary>
    internal static void Flush()
    {
        if (_offered.Count == 0) {
            return;
        }

        if (NetSession.Instance.Connection is ElinNetClient client) {
            foreach (var thing in _offered) {
                Position? pos = thing.pos;
                if (thing.isDestroyed || pos is null) {
                    continue;
                }

                client.Delta.AddRemote(new StoryGiftDelta {
                    Data = LZ4Bytes.Create(thing),
                    Pos = pos,
                });
                EmpLog.Debug("Asking the host for story gift {ThingId}", thing.id);
            }
        }

        _offered.Clear();
    }
}
