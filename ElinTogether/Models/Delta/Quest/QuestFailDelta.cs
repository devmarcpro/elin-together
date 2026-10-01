using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     A quest failed (expired, mostly): gone from the one quest log, for everyone
/// </summary>
[MessagePackObject]
public class QuestFailDelta : ElinDelta
{
    [Key(0)]
    public required int Uid { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        var quest = SharedQuests.Find(Uid, null);
        if (quest is null || !game.quests.list.Contains(quest)) {
            return;
        }

        if (net is ElinNetHost) {
            // failed in the copy of a player travelling alone: what a failure costs is the world's, and
            // everyone has to know
            using (Simulate()) {
                quest.Fail();
            }

            return;
        }

        QuestFailEvent.FailQuietly(quest);
    }
}
