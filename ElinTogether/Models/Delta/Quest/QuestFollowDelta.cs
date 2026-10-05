using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Going along to the zone of a quest someone else took, both ways. <br />
///     The host entered the zone of a quest it took and asks the player it left in town along; that player
///     answers when it does not come. Coming along is not an answer, it arrives, see ElinNetClient.FollowHost. <br />
///     A player leaves for the zone of a quest it took and the host, standing next to it, is asked along: when
///     it comes it runs that zone itself, see ElinNetHost.AskAlongToQuestZone
/// </summary>
[MessagePackObject]
public class QuestFollowDelta : ElinDelta
{
    public const int Invite = 0;
    public const int Declined = 1;
    public const int NoAnswer = 2;

    /// <summary>
    ///     Host to the player leaving for its quest: the host is being asked along, the answer follows
    /// </summary>
    public const int Asked = 3;

    /// <summary>
    ///     The player whose quest it is walks out of the zone the host runs for it: everyone leaves
    /// </summary>
    public const int Leave = 4;

    /// <summary>
    ///     Host to that player, on the way out: how its quest went. It settles it itself, once back in town
    /// </summary>
    public const int Won = 5;
    public const int Lost = 6;

    /// <summary>
    ///     Host to that player: what the quest events of the zone hold on the host (the monsters to hunt). Its
    ///     copy of the zone is the one it made when taking the quest, with an event that never ran
    /// </summary>
    public const int ZoneState = 7;

    /// <summary>
    ///     Not a refusal: the reason of the <see cref="ZoneLeaseDenied" /> a player gets for the zone of its
    ///     quest when the host comes along and makes that zone itself
    /// </summary>
    internal const string Coming = "quest_follow_coming";

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

    /// <summary>
    ///     Won, Lost: the quest, and who gave it
    /// </summary>
    [Key(3)]
    public int QuestUid { get; init; }

    [Key(4)]
    public int Giver { get; init; }

    /// <summary>
    ///     ZoneState: the quest events of the zone, a list of ZoneEvent
    /// </summary>
    [Key(5)]
    public LZ4Bytes? Events { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        switch (net) {
            case ElinNetHost { IsZoneSession: false } host when Kind == Leave:
                host.OnQuestTakerLeaves(OriginPeer);
                break;
            case ElinNetClient { IsZoneSession: false } client when Kind == Invite:
                client.OnQuestFollowInvite(this);
                break;
            case ElinNetClient { IsZoneSession: false } when Kind == Asked:
                Msg.Say("emp_quest_follow_asked".Loc(Name));
                break;
            case ElinNetClient { IsZoneSession: false } client when Kind == ZoneState:
                client.OnQuestZoneState(ZoneUid, Events);
                break;
            case ElinNetClient { IsZoneSession: false } when Kind is Won or Lost:
                PersonalQuests.OnHostSettled(QuestUid, Giver, Kind == Lost);
                break;
            // the one who asked reads the refusal, host or player
            case { IsZoneSession: false } when Kind is Declined or NoAnswer:
                Msg.Say((Kind == Declined ? "emp_quest_follow_declined" : "emp_quest_follow_no_answer").Loc(Name));
                break;
        }
    }
}
