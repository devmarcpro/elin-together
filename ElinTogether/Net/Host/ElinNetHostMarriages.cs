using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;

namespace ElinTogether.Net;

/// <summary>
///     Council 2026-10-24 (<see cref="SharedMarriages" />): who each married resident is married to, kept in the
///     host's save. The game's own LoveData and feat stay as they are: a game without the mod sees the resident
///     married to the player of the save
/// </summary>
internal partial class ElinNetHost
{
    /// <summary>
    ///     Resident chara uid -> the uid of the player character it married
    /// </summary>
    [ElinGameIOProperty("marriage_spouses")]
    internal static Dictionary<int, int> Spouses
    {
        get => field ??= [];
        set;
    }

    /// <summary>
    ///     A player joins: everyone is told the whole list. A resident married before there was a list (an old
    ///     save, a game without the box) is the host's character's
    /// </summary>
    internal void TellMarriages()
    {
        // (a zone hosted by a client keeps no books, the host of the world does)
        if (IsZoneSession) {
            return;
        }

        foreach (var chara in game.cards.globalCharas.Values.Concat(_map?.charas ?? [])) {
            if (chara.IsMarried && !Spouses.ContainsKey(chara.uid)) {
                Spouses[chara.uid] = player.uidChara;
            }
        }

        Delta.AddRemote(new MarriageDelta {
            Spouses = new(Spouses),
        });
    }
}
