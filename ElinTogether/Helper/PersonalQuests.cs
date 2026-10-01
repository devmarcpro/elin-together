using System.Collections.Generic;
using System.Linq;
using ElinTogether.Models;
using ElinTogether.Net;

namespace ElinTogether.Helper;

/// <summary>
///     Random quests belong to the player who takes them, with the fame and karma they earn. Each game only
///     holds its own in the quest log, next to the story quests everyone shares. <br />
///     A client's world is the host's: after every load of it (joining, travelling alone, coming back) its own
///     quests and standing are put back in place of the host's
/// </summary>
internal static class PersonalQuests
{
    private static List<Quest> _mine = [];
    private static Game? _source;
    private static bool _hasStanding;
    private static int _fame;
    private static int _karma;

    internal static bool Enabled => NetSession.Instance.Rules.UsePersonalQuests;

    internal static bool IsPersonal(Quest quest)
    {
        return Enabled && quest.IsRandomQuest;
    }

    internal static void Tick()
    {
        var session = NetSession.Instance;
        if (session.Transport is null || !Enabled) {
            _mine = [];
            _source = null;
            _hasStanding = false;
            return;
        }

        if (!EClass.core.IsGameStarted || EClass.game?.quests is not { } quests) {
            return;
        }

        if (session.Transport is ElinNetHost host) {
            host.SweepTakenOffers();
            return;
        }

        if (!ReferenceEquals(EClass.game, _source)) {
            _source = EClass.game;
            Restore();
            return;
        }

        // nobody else holds these: they expire on this player's clock
        foreach (var expired in quests.list.Where(q => IsPersonal(q) && q.IsExpired).ToArray()) {
            Msg.Say("questExpired", expired.GetTitle());
            expired.Fail();
        }

        _mine = quests.list.Where(IsPersonal).ToList();

        var player = EClass.player;
        if (_hasStanding && player.fame == _fame && player.karma == _karma) {
            return;
        }

        _hasStanding = true;
        _fame = player.fame;
        _karma = player.karma;
        TellHost(new PlayerStandingDelta {
            Fame = _fame,
            Karma = _karma,
        });
    }

    /// <summary>
    ///     From the host, when this player settles on its map: what the host kept for it
    /// </summary>
    internal static void Receive(List<Quest> mine, int[] taken, int fame, int karma)
    {
        _mine = mine;
        _fame = fame;
        _karma = karma;
        _hasStanding = true;
        _source = EClass.game;
        Restore();

        // offers of this map someone else already took
        foreach (var chara in EClass._map.charas) {
            if (chara.quest is { } offer && taken.Contains(offer.uid) && !EClass.game.quests.list.Contains(offer)) {
                chara.quest = null;
            }
        }
    }

    /// <summary>
    ///     To the host of the world, wherever this player is: on its map, travelling alone, a guest somewhere
    /// </summary>
    internal static void TellHost(ElinDelta delta)
    {
        if (NetSession.Instance.Transport is not ElinNetClient main) {
            return;
        }

        if (NetSession.Instance.IsAway) {
            main.SendWhileAway(delta);
        } else {
            main.Delta.AddRemote(delta);
        }
    }

    /// <summary>
    ///     The player hosting a map took a quest there: its offer is gone for the others on that map
    /// </summary>
    internal static void OnStarted(Quest quest)
    {
        if (NetSession.Instance.Connection is ElinNetHost host) {
            host.Delta.AddRemote(new QuestTakenDelta {
                Giver = quest.person.chara,
                Uid = quest.uid,
            });
        }
    }

    private static void Restore()
    {
        var quests = EClass.game.quests;

        // the random quests of this world are the host's own
        quests.list.RemoveAll(q => q.IsRandomQuest && !_mine.Contains(q));

        foreach (var quest in _mine) {
            if (!quests.list.Contains(quest)) {
                quests.list.Insert(0, quest);
            }

            if (quest.chara is { } giver && giver.quest?.uid != quest.uid) {
                giver.quest = quest;
            }

            SharedQuests.Remember(quest);
        }

        if (_hasStanding) {
            EClass.player.fame = _fame;
            EClass.player.karma = _karma;
        }
    }
}

/// <summary>
///     While the host runs a quest step for a player on its map (taking a quest, turning it in), that player
///     stands in as the local one: the game's own code gives it the item to deliver, drops the reward at its
///     feet, and the fame and karma it earns go to it
/// </summary>
internal static class PlayerStandIn
{
    private static int _fame;
    private static int _karma;

    internal static bool IsActive { get; private set; }

    internal static ScopeExit For(ElinNetHost host, int peerId, Chara actor)
    {
        var self = EClass.player.chara;

        IsActive = true;
        _fame = _karma = 0;
        EClass.player.chara = actor;

        return new() {
            OnExit = () => {
                EClass.player.chara = self;
                IsActive = false;

                if (_fame != 0 || _karma != 0) {
                    host.SendDeltaTo(peerId, new PlayerStandingDelta {
                        Fame = _fame,
                        Karma = _karma,
                        Relative = true,
                    });
                }
            },
        };
    }

    internal static bool Redirect(int fame, int karma)
    {
        if (!IsActive) {
            return false;
        }

        _fame += fame;
        _karma += karma;
        return true;
    }
}
