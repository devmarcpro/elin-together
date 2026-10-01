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

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost) {
            return;
        }

        PersonalQuests.Receive(Quests.Select(data => data.Decompress<Quest>()).ToList(), Taken, Fame, Karma);
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

    protected override void OnApply(ElinNetBase net)
    {
        if (net is ElinNetHost host) {
            host.StorePersonal(OriginPeer, Uid, Data);
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
        if (Giver?.Find() is Chara { quest: { } offer } giver && offer.uid == Uid && !game.quests.list.Contains(offer)) {
            giver.quest = null;
        }
    }
}

/// <summary>
///     A player to the host: its fame and karma, to keep. <br />
///     The host to a player: what a quest step the host ran for it earned
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

        if (Fame != 0) {
            player.ModFame(Fame);
        }

        if (Karma != 0) {
            player.ModKarma(Karma);
        }
    }
}
