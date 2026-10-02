using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Net;
using MessagePack;

namespace ElinTogether.Models;

/// <summary>
///     Host to one player: the quests and the standing the host keeps for it
/// </summary>
[MessagePackObject]
public class PersonalStateDelta : ElinDelta
{
    [Key(0)]
    public required List<LZ4Bytes> Quests { get; init; }

    /// <summary>
    ///     Quests other players hold: their offers are gone
    /// </summary>
    [Key(1)]
    public required int[] Taken { get; init; }

    [Key(2)]
    public required int Fame { get; init; }

    [Key(3)]
    public required int Karma { get; init; }

    /// <summary>
    ///     The date on the host's clock, deadlines are dates on it
    /// </summary>
    [Key(4)]
    public int Now { get; set; }

    // it may land before the world it is for has started
    internal override bool RequiresGameStarted => false;

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost) {
            return;
        }

        PersonalQuests.Receive(Quests.Select(data => data.Decompress<Quest>()).ToList(), Taken, Fame, Karma, Now);
    }
}

/// <summary>
///     A player to the host of the world: what one of its quests holds now, or nothing when it is gone
/// </summary>
[MessagePackObject]
public class PersonalQuestDelta : ElinDelta
{
    [Key(0)]
    public required int Uid { get; init; }

    [Key(1)]
    public required LZ4Bytes? Data { get; init; }

    /// <summary>
    ///     The date on the sender's clock
    /// </summary>
    [Key(2)]
    public int Now { get; set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            host.StorePersonal(OriginPeer, Uid, Data, Now);
        }
    }
}

/// <summary>
///     The quest a resident offered was taken by a player: it is not on offer anymore
/// </summary>
[MessagePackObject]
public class QuestTakenDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard? Giver { get; init; }

    [Key(1)]
    public required int Uid { get; init; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost) {
            return;
        }

        // not for the one who took it
        if (game.quests.list.Exists(q => q.uid == Uid)) {
            return;
        }

        PersonalQuests.MarkTaken(Uid);
        if (Giver?.Find() is Chara { quest: { } offer } giver && offer.uid == Uid) {
            giver.quest = null;
        }
    }
}

/// <summary>
///     A player to the host: its fame and karma, to keep. <br />
///     The host to a player: what a quest step the host ran for it earned, or what a deed of its cost
/// </summary>
[MessagePackObject]
public class PlayerStandingDelta : ElinDelta
{
    [Key(0)]
    public required int Fame { get; init; }

    [Key(1)]
    public required int Karma { get; init; }

    [Key(2)]
    public bool Relative { get; set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            if (!Relative) {
                host.StoreStanding(OriginPeer, Fame, Karma);
            }

            return;
        }

        if (!Relative) {
            return;
        }

        using var _ = PlayerKarma.Own();

        if (Fame != 0) {
            player.ModFame(Fame);
        }

        if (Karma != 0) {
            player.ModKarma(Karma);
        }
    }
}
