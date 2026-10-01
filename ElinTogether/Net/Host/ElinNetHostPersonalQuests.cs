using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net.Steam;

namespace ElinTogether.Net;

/// <summary>
///     Random quests, fame and karma per player (see <see cref="PersonalQuests" />): the host keeps them for
///     every player in the save, and runs the steps that create or give things for the players on its map
/// </summary>
internal partial class ElinNetHost
{
    private const int StandingFame = 0;
    private const int StandingKarma = 1;
    private const int NewPlayerKarma = 30;

    /// <summary>
    ///     Player chara uid -> quest uid -> the quest, as its player last told it
    /// </summary>
    [ElinGameIOProperty("personal_quests")]
    private static Dictionary<int, Dictionary<int, byte[]>> PersonalQuestLogs
    {
        get => field ??= [];
        set;
    }

    /// <summary>
    ///     Player chara uid -> fame, karma
    /// </summary>
    [ElinGameIOProperty("player_standing")]
    private static Dictionary<int, int[]> PlayerStandings
    {
        get => field ??= [];
        set;
    }

    private static Dictionary<int, byte[]> PersonalLogOf(int charaUid)
    {
        if (!PersonalQuestLogs.TryGetValue(charaUid, out var log)) {
            log = PersonalQuestLogs[charaUid] = [];
        }

        return log;
    }

    /// <summary>
    ///     The chara of a player, on this map or not
    /// </summary>
    private int PlayerUidOf(int peerId)
    {
        if (ActiveRemoteCharas.TryGetValue(peerId, out var chara)) {
            return chara.uid;
        }

        return Socket.Peers.FirstOrDefault(p => p.Id == peerId) is { } peer &&
               SavedRemoteCharas.TryGetValue(peer.User, out var uid)
            ? uid
            : 0;
    }

    /// <summary>
    ///     A player on this map takes the quest a resident offers
    /// </summary>
    internal void AcceptPersonal(int peerId, Quest quest)
    {
        if (!ActiveRemoteCharas.TryGetValue(peerId, out var taker)) {
            return;
        }

        // a zone hosted by a client keeps no books, the host of the world does
        var log = IsZoneSession ? null : PersonalLogOf(taker.uid);
        if (log is { Count: >= QuestManager.MaxRandomQuest }) {
            EmpLog.Debug("Rejecting quest accept, quest list of {CharaUid} full", taker.uid);
            return;
        }

        var giver = quest.chara;
        game.quests.globalList.Remove(quest);

        try {
            // what taking it sets up (the parcel to deliver, someone to escort) is for the taker
            using (PlayerStandIn.For(this, peerId, taker)) {
                using (ElinDelta.Simulate()) {
                    quest.Start();
                }
            }
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Quest {QuestId} start failed for player {CharaUid}", quest.id, taker.uid);
        }

        var data = LZ4Bytes.Create(quest);
        log?[quest.uid] = data.Bytes;

        SendDeltaTo(peerId, new QuestStartDelta {
            Uid = quest.uid,
            Owner = giver,
            AssignQuest = true,
            Data = data,
            Now = world.date.GetRaw(),
        });

        ReleaseOffer(giver, quest.uid);
        EmpLog.Debug("Player {CharaUid} took quest {QuestUid} {QuestId}", taker.uid, quest.uid, quest.id);
    }

    /// <summary>
    ///     A player on this map turns in one of its quests: only that player holds it, it comes with the request
    /// </summary>
    internal void CompletePersonal(int peerId, Quest quest)
    {
        if (!ActiveRemoteCharas.TryGetValue(peerId, out var taker)) {
            return;
        }

        // the host of the world gives a reward once, for a quest it knows that player holds
        if (!IsZoneSession && !PersonalLogOf(taker.uid).ContainsKey(quest.uid)) {
            EmpLog.Warning("Player {CharaUid} turns in quest {QuestUid} {QuestId} it does not hold", taker.uid, quest.uid, quest.id);
            return;
        }

        try {
            using (PlayerStandIn.For(this, peerId, taker)) {
                using (ElinDelta.Simulate()) {
                    quest.Complete();
                }
            }
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Quest {QuestId} completion failed for player {CharaUid}", quest.id, taker.uid);
        }

        if (!IsZoneSession) {
            PersonalLogOf(taker.uid).Remove(quest.uid);
        }

        EmpLog.Debug("Player {CharaUid} completed quest {QuestUid} {QuestId}", taker.uid, quest.uid, quest.id);
    }

    /// <summary>
    ///     A player tells what one of its quests holds now, or that it is gone (completed, failed, given up)
    /// </summary>
    /// <param name="now">the date on that player's clock: a deadline is kept as time left, on the host's</param>
    internal void StorePersonal(int peerId, int questUid, LZ4Bytes? data, int now)
    {
        if (IsZoneSession || PlayerUidOf(peerId) is not (> 0 and var uid)) {
            return;
        }

        if (data is null) {
            PersonalLogOf(uid).Remove(questUid);
            return;
        }

        var shift = now > 0 ? world.date.GetRaw() - now : 0;
        if (shift != 0 && data.Decompress<Quest>() is { deadline: > 0 } quest) {
            quest.deadline += shift;
            data = LZ4Bytes.Create(quest);
        }

        PersonalLogOf(uid)[questUid] = data.Bytes;
    }

    internal void StoreStanding(int peerId, int fame, int karma)
    {
        if (IsZoneSession || PlayerUidOf(peerId) is not (> 0 and var uid)) {
            return;
        }

        PlayerStandings[uid] = [fame, karma];
    }

    /// <summary>
    ///     A player settled on this map: its own quests and standing, and the offers others already took
    /// </summary>
    private void SendPersonalState(ISteamNetPeer peer, int charaUid)
    {
        if (IsZoneSession || !Session.Rules.UsePersonalQuests) {
            return;
        }

        if (!PlayerStandings.TryGetValue(charaUid, out var standing) || standing.Length < 2) {
            standing = PlayerStandings[charaUid] = [0, NewPlayerKarma];
        }

        var taken = PersonalQuestLogs
            .Where(kv => kv.Key != charaUid)
            .SelectMany(kv => kv.Value.Keys)
            .Concat(game.quests.list.Where(PersonalQuests.IsPersonal).Select(q => q.uid))
            .ToArray();

        SendDeltaTo(peer.Id, new PersonalStateDelta {
            Quests = PersonalLogOf(charaUid).Values.Select(bytes => new LZ4Bytes { Bytes = bytes }).ToList(),
            Taken = taken,
            Fame = standing[StandingFame],
            Karma = standing[StandingKarma],
            Now = world.date.GetRaw(),
        });
    }

    /// <summary>
    ///     A map coming back from a player travelling alone still shows the quests it took there as offered
    /// </summary>
    internal void SweepTakenOffers()
    {
        if (IsZoneSession || PersonalQuestLogs.Count == 0) {
            return;
        }

        foreach (var chara in _map.charas) {
            if (chara.quest is not { } offer || game.quests.list.Contains(offer)) {
                continue;
            }

            if (PersonalQuestLogs.Values.Any(log => log.ContainsKey(offer.uid))) {
                ReleaseOffer(chara, offer.uid);
            }
        }
    }

    private void ReleaseOffer(Chara? giver, int questUid)
    {
        if (giver?.quest?.uid == questUid) {
            giver.quest = null;
        }

        Delta.AddRemote(new QuestTakenDelta {
            Giver = giver,
            Uid = questUid,
        });
    }
}
