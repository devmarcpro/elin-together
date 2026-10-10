using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The quest offers of a town were drawn again (a new day, or the "Reroll Quests" button): the old offers are
///     gone from its residents. Only the game that simulates the map draws them, so it says which offers are
///     still there and the others drop the rest <br />
///     Sent after the <see cref="QuestCreateDelta" /> of the new offers, so they are in the list
/// </summary>
[MessagePackObject]
public class QuestOffersDelta : ElinDelta
{
    /// <summary>
    ///     The zone the offers belong to, a game standing elsewhere leaves it alone
    /// </summary>
    [Key(0)]
    public required int ZoneUid { get; init; }

    /// <summary>
    ///     Uids of the offers still on the residents of that zone
    /// </summary>
    [Key(1)]
    public required int[] Kept { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (NetSession.Instance.IsHost || _zone is not { } zone || zone.uid != ZoneUid || _map is not { } map) {
            return;
        }

        var kept = new HashSet<int>(Kept);
        foreach (var chara in map.charas.Concat(map.deadCharas).ToArray()) {
            // negative: made here and waiting for the host's number. In the quest log: taken by this player
            if (chara.quest is not { uid: >= 0 } quest || kept.Contains(quest.uid) ||
                game.quests.list.Contains(quest) || game.quests.globalList.Contains(quest)) {
                continue;
            }

            chara.quest = null;
        }
    }
}
