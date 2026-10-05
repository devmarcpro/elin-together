using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.Models;
using ElinTogether.Net.Steam;
using HeathenEngineering.SteamworksIntegration;

namespace ElinTogether.Net;

/// <summary>
///     A world that changes hands (the save depot): the game loads it with the character of whoever saved it
///     last as the local one, and the player who takes it over would play that character, with its bag and gold,
///     while its own stays a character of the save <br />
///     The save remembers whose its local character is. Loaded by another player who has a character in it, the two
///     are exchanged before anything is played: the one who takes the world plays its own, the former one becomes
///     the character of an absent player, as any player who left, with its standing, its random quests and its
///     companions kept for its return. Nothing is copied, only who is the local character changes <br />
///     A world last hosted before this was written does not know whose its character is: nothing is exchanged
/// </summary>
internal partial class ElinNetHost
{
    /// <summary>
    ///     The player whose character is the local one of this save -> that character's uid (one entry)
    /// </summary>
    [ElinGameIOProperty("pc_owner")]
    private static Dictionary<ulong, int> PcOwners
    {
        get => field ??= [];
        set;
    }

    /// <summary>
    ///     Who plays in this game. Debug windows sharing one Steam account are the identity the host knows them by,
    ///     see SteamNetPeer.UseDevIdentity
    /// </summary>
    private static ulong LocalUser =>
#if DEBUG
        EmpConfig.Dev.Identity.Value != 0 ? SteamNetPeer.DevIdentityBase + (ulong)EmpConfig.Dev.Identity.Value :
#endif
        UserData.Me;

    /// <summary>
    ///     Hosting: the local character of this save is ours
    /// </summary>
    private static void RememberPcOwner()
    {
        PcOwners.Clear();
        PcOwners[LocalUser] = player.uidChara;
    }

    private static Chara? Giver(Quest quest)
    {
        return quest.person?.uidChara is { } uid and not 0 ? game.cards.globalCharas.Find(uid) : null;
    }

    /// <summary>
    ///     The world just loaded was another player's: our character becomes the local one. True when exchanged, the
    ///     world is then saved and loaded again so that the game starts from it as from any save
    /// </summary>
    private static bool TakeOverPc()
    {
        var me = LocalUser;
        if (PcOwners.Count != 1) {
            return false;
        }

        var (formerOwner, pcUid) = PcOwners.First();
        if (formerOwner == me || pcUid != player.uidChara || !SavedRemoteCharas.TryGetValue(me, out var myUid) ||
            myUid == pcUid || game.cards.globalCharas.Find(myUid) is not { isDead: false } mine ||
            pc.party is not { } party) {
            return false;
        }

        var former = pc;
        EmpLog.Information("The world was {Owner}'s: playing our own character {Mine} in place of {Former}",
            formerOwner, mine.uid, former.uid);

        // fame, karma and random quests: the save holds the former player's, the books hold ours
        if (PlayerStandings.TryGetValue(mine.uid, out var standing) && standing.Length >= 2) {
            PlayerStandings[former.uid] = [player.fame, player.karma];
            PlayerStandings.Remove(mine.uid);
            player.fame = standing[StandingFame];
            player.karma = standing[StandingKarma];

            var theirs = PersonalLogOf(former.uid);
            foreach (var quest in game.quests.list.Where(q => q.IsRandomQuest).ToArray()) {
                theirs[quest.uid] = LZ4Bytes.Create(quest).Bytes;
                game.quests.list.Remove(quest);
                if (Giver(quest) is { } giver && giver.quest?.uid == quest.uid) {
                    giver.quest = null;
                }
            }

            foreach (var bytes in PersonalLogOf(mine.uid).Values) {
                // as PersonalQuests.Restore does for a client: who it is for is looked up again in this world
                var quest = new LZ4Bytes { Bytes = bytes }.Decompress<Quest>();
                game.quests.list.Insert(0, quest);
                if (Giver(quest) is { } giver) {
                    giver.quest = quest;
                }
            }

            PersonalQuestLogs.Remove(mine.uid);
        }

        // the companions of the leader have no owner written: they stay the former player's, and wait with it
        foreach (var companion in CompanionHelper.CompanionsOf(former)) {
            companion.SetCompanionOwner(former);
            companion.currentZone = null;
        }

        // ours come back with us, where the former character stood
        if (!party.members.Contains(mine)) {
            party.members.Add(mine);
            party.uidMembers.Add(mine.uid);
            mine.party = party;
        }

        party.SetLeader(mine);
        foreach (var arriving in CompanionHelper.CompanionsOf(mine).Append(mine)) {
            arriving.currentZone = former.currentZone;
            arriving.pos.Set(former.pos);
            if (arriving.global is { } global) {
                global.transition = null;
            }
        }

        mine.homeZone ??= former.homeZone ?? EClass.pc.homeZone;

        // the former character is now the one of an absent player
        party.members.Remove(former);
        party.uidMembers.Remove(former.uid);
        former.party = null;
        former.currentZone = null;
        former.SetBool("remote_chara", true);
        // it has its own things: not the axe a new player is given
        former.SetBool("remote_axe_given", true);
        mine.SetBool("remote_chara", false);
        former.SetInt(CINT.IsPC, 0);
        mine.SetInt(CINT.IsPC, 1);

        player.uidChara = mine.uid;
        player.chara = mine;

        SavedRemoteCharas.Remove(me);
        SavedRemoteCharas[formerOwner] = former.uid;
        if (!PlayerRosters.TryGetValue(formerOwner, out var roster)) {
            roster = PlayerRosters[formerOwner] = [];
        }

        if (!roster.Contains(former.uid)) {
            roster.Add(former.uid);
        }

        PcOwners.Clear();
        PcOwners[me] = mine.uid;
        return true;
    }
}
