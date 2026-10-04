using ElinTogether.LangMod;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     The host entered the zone of a quest it took and asks the player it left in town along; that player
///     answers when it does not come. Coming along is not an answer, it arrives, see ElinNetClient.FollowHost
/// </summary>
[MessagePackObject]
public class QuestFollowDelta : ElinDelta
{
    public const int Invite = 0;
    public const int Declined = 1;
    public const int NoAnswer = 2;

    [Key(0)]
    public required int Kind { get; init; }

    /// <summary>
    ///     Who asks, or who answers
    /// </summary>
    [Key(1)]
    public required string Name { get; init; }

    /// <summary>
    ///     The zone of the quest, the question is void once the host is out of it
    /// </summary>
    [Key(2)]
    public int ZoneUid { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        switch (net) {
            case ElinNetHost { IsZoneSession: false } when Kind != Invite:
                Msg.Say((Kind == Declined ? "emp_quest_follow_declined" : "emp_quest_follow_no_answer").Loc(Name));
                break;
            case ElinNetClient { IsZoneSession: false } client when Kind == Invite:
                client.OnQuestFollowInvite(this);
                break;
        }
    }
}
