using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.LangMod;
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
    ///     Former local characters whose player is not known (a world last hosted before the owner was written): the
    ///     player who comes without a character of its own gets it back. Uid -> 1
    /// </summary>
    [ElinGameIOProperty("pc_orphan")]
    private static Dictionary<int, int> PcOrphans
    {
        get => field ??= [];
        set;
    }

    /// <summary>
    ///     Whose the local character of this save is, 0 when the save does not tell: nothing written, written for
    ///     another character, or for a player who has a character of its own in this world (what 0.26.494 wrote
    ///     when a world taken over was hosted)
    /// </summary>
    private static ulong PcOwner()
    {
        if (PcOwners.Count != 1) {
            return 0;
        }

        var (owner, uid) = PcOwners.First();
        return uid != player.uidChara || OwnCharaOf(owner) is not null ? 0 : owner;
    }

    /// <summary>
    ///     The character this player plays as a guest of this world, when it is not the local one
    /// </summary>
    private static Chara? OwnCharaOf(ulong user)
    {
        return SavedRemoteCharas.TryGetValue(user, out var uid) && uid != player.uidChara
            ? game.cards.globalCharas.Find(uid)
            : null;
    }

    private static void SetPcOwner(ulong user)
    {
        PcOwners.Clear();
        PcOwners[user] = player.uidChara;
    }

    // (a table emptied may not be written again by the save: an entry is only believed when nobody plays that character)
    private static Chara? Orphan()
    {
        return PcOrphans.Keys.Select(uid => game.cards.globalCharas.Find(uid)).FirstOrDefault(c =>
            c is { isDead: false } && c.uid != player.uidChara && !SavedRemoteCharas.ContainsValue(c.uid));
    }

    /// <summary>
    ///     Hosting: the local character of this save is ours, unless the save says whose it is
    /// </summary>
    private static void RememberPcOwner()
    {
        if (PcOwner() == 0 && OwnCharaOf(LocalUser) is null) {
            SetPcOwner(LocalUser);
        }
    }

    /// <summary>
    ///     A player who joins without a character in this world, when a former local character waits for its player:
    ///     it is that player's (with two players it cannot be anyone else's)
    /// </summary>
    private static void GiveOrphanTo(ulong user)
    {
        if (SavedRemoteCharas.ContainsKey(user) || PcOwner() == user || Orphan() is not { } orphan) {
            return;
        }

        EmpLog.Information("The former local character {Uid} goes back to player {User}", orphan.uid, user);
        PcOrphans.Remove(orphan.uid);
        SavedRemoteCharas[user] = orphan.uid;
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
        var formerOwner = PcOwner();
        if (formerOwner == me) {
            return false;
        }

        // our own character in this world: the one we played as a guest, else a former local character nobody claims
        var mine = OwnCharaOf(me) ?? (SavedRemoteCharas.ContainsKey(me) ? null : Orphan());
        if (mine is null) {
            // nobody's by the save and we have no other: it is ours (the host back on a world of before)
            if (formerOwner == 0 && !SavedRemoteCharas.ContainsKey(me)) {
                SetPcOwner(me);
            }

            return false;
        }

        if (mine.isDead || pc.party is not { } party) {
            EmpLog.Warning("Our character {Mine} cannot take the place of the local one (dead: {Dead})", mine.uid, mine.isDead);
            Dialog.Ok("emp_handover_failed".Loc(mine.Name));
            return false;
        }

        // the save as it was, kept with the game's own backups
        try {
            GameIO.MakeBackup(new GameIndex { id = Game.id, cloud = game.isCloud });
        } catch (System.Exception ex) {
            // no copy to come back to: nothing is exchanged
            EmpLog.Warning(ex, "No backup before the exchange of characters, nothing exchanged");
            Dialog.Ok("emp_handover_failed".Loc(mine.Name));
            return false;
        }

        var former = pc;
        EmpLog.Information("The world was {Owner}'s (0: not known): playing our own character {Mine} in place of {Former}",
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
        PcOrphans.Remove(mine.uid);
        if (formerOwner == 0) {
            // whose it is will be known when its player comes back, see GiveOrphanTo
            PcOrphans[former.uid] = 1;
        } else {
            SavedRemoteCharas[formerOwner] = former.uid;
            if (!PlayerRosters.TryGetValue(formerOwner, out var roster)) {
                roster = PlayerRosters[formerOwner] = [];
            }

            if (!roster.Contains(former.uid)) {
                roster.Add(former.uid);
            }
        }

        SetPcOwner(me);
        return true;
    }
}
