using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Models;
using ElinTogether.Patches;

namespace ElinTogether.Net;

/// <summary>
///     Council 14, "a share for everyone": the story is the group's (one quest log, one set of story flags), so
///     what a story quest or a dialog gives is given to every player of the world, not only to the one who
///     completed the quest or played the dialog. Nobody plays anything again, nobody is asked anything. <br />
///     One place: the game's own <c>Player.DropReward</c>, while a story quest completes or a dialog outcome
///     runs (<see cref="StoryScope" />), in the game that hosts the world. A player on the map finds its share
///     in its bag; a player elsewhere or not connected gets a parcel in its name in the mail of the base. <br />
///     Only goods a player carries are multiplied. What is the world's is not: recipes (known by all already),
///     deeds, and artifacts, except the few named here. What is not listed is not multiplied
/// </summary>
// ponytail: what a world gave BEFORE this was written is not caught up (nothing recorded what each quest gave, nor
// to whom). It needs a table of the rewards of each story quest, by hand
internal partial class ElinNetHost
{
    /// <summary>
    ///     The ledger of the world: each reward of the story that was shared, as given (number -> the thing)
    /// </summary>
    [ElinGameIOProperty("story_rewards")]
    private static Dictionary<int, byte[]> StoryRewards
    {
        get => field ??= [];
        set;
    }

    /// <summary>
    ///     Reward number -> the characters of the players who have it: who earned it, who got a share
    /// </summary>
    [ElinGameIOProperty("story_received")]
    private static Dictionary<int, int[]> StoryReceived
    {
        get => field ??= [];
        set;
    }

    /// <summary>
    ///     A player stands on the host's map: what the story gave before it played in this world, or while
    ///     nothing knew it, comes to it as one parcel in its name in the mail of the base (not a flood in its
    ///     bag). Each reward once: the ledger notes it
    /// </summary>
    internal static void CatchUpStoryShares(Chara player)
    {
        if (!EmpConfig.Server.OncePerPlayer.Value || StoryRewards.Count == 0) {
            return;
        }

        var owed = new List<Thing>();
        foreach (var (number, data) in StoryRewards.ToArray()) {
            var received = StoryReceived.GetValueOrDefault(number) ?? [];
            if (received.Contains(player.uid)) {
                continue;
            }

            try {
                var share = new LZ4Bytes { Bytes = data }.Decompress<Thing>();
                game.cards.AssignUIDRecursive(share);
                owed.Add(share);
            } catch (System.Exception ex) {
                EmpLog.Warning(ex, "Story reward {Number} of the ledger could not be read", number);
            }

            // (noted even when it could not be read: not tried again at every arrival)
            StoryReceived[number] = received.Append(player.uid).ToArray();
        }

        if (owed.Count == 0) {
            return;
        }

        var parcel = ThingGen.CreateParcel(null, owed.ToArray());
        parcel.c_idRefName = "emp_story_share".Loc(player.NameSimple);
        world.SendPackage(parcel);
        EmpLog.Information("Story rewards given before player {Uid} knew of them: {Count} in a parcel in its name",
            player.uid, owed.Count);
    }

    // rewards dropped this frame and who earned them: copied at the end of the frame, once the story code is
    // done with them (charges, material, what a chest holds are set after the drop)
    private static readonly List<(Thing Reward, int Earner)> _storyRewards = [];

    // artifacts every player must have its own of
    private static readonly HashSet<string> _ownArtifacts = ["backpack_holding"];

    internal static void NoteStoryReward(Thing reward, Chara? earner)
    {
        if (StoryScope.Active) {
            ShareStoryReward(reward, earner);
        }
    }

    /// <summary>
    ///     A reward of the story known as such by the caller (a gift a client's dialog asked this game to make)
    /// </summary>
    internal static void ShareStoryReward(Thing reward, Chara? earner)
    {
        if (reward is null || NetSession.Instance.Transport is ElinNetClient || !IsSharedWorld ||
            !EmpConfig.Server.OncePerPlayer.Value) {
            return;
        }

        _storyRewards.Add((reward, (earner ?? pc).uid));
    }

    // (the game's Duplicate makes a new thing of that kind: a chest comes with loot of its own drawn at random,
    // and without what the reward holds)
    private static Thing Whole(Thing reward)
    {
        var copy = reward.Duplicate(reward.Num);
        copy.things.DestroyAll();
        foreach (var held in reward.things) {
            copy.AddCard(Whole(held));
        }

        return copy;
    }

    /// <summary>
    ///     End of the frame
    /// </summary>
    internal static void GiveStoryShares()
    {
        if (_storyRewards.Count == 0) {
            return;
        }

        var rewards = _storyRewards.ToArray();
        _storyRewards.Clear();
        if (!core.IsGameStarted || _zone is null) {
            return;
        }

        // every character a player plays in this world, the local one included
        var players = SavedRemoteCharas.Values.Append(player.uidChara).Distinct()
            .Select(uid => game.cards.globalCharas.Find(uid))
            .Where(c => c is { isDead: false })
            .ToList();
        var host = NetSession.Instance.Transport as ElinNetHost;

        foreach (var (reward, earner) in rewards) {
            if (reward.isDestroyed || !Multiplied(reward)) {
                continue;
            }

            // in the ledger, for who plays in this world later
            var number = StoryRewards.Count == 0 ? 1 : StoryRewards.Keys.Max() + 1;
            StoryRewards[number] = LZ4Bytes.Create(Whole(reward)).Bytes;
            StoryReceived[number] = players.Select(p => p!.uid).Append(earner).Distinct().ToArray();

            foreach (var other in players.Where(p => p!.uid != earner)) {
                var share = Whole(reward);

                // in its bag when it is here: at its feet it piled up with the earner's own, one tile away, and the
                // first to bend down had both (and nothing lands in water or in a wall). A full bag: at its feet
                var here = other!.IsAliveInCurrentZone && _map.charas.Contains(other);
                if (here && !other.things.IsFull(share)) {
                    using (ElinDelta.Simulate()) {
                        other.AddThing(share);
                    }
                } else if (here) {
                    CardCache.Add(share);
                    CardCache.CacheContainer(share.things);
                    using (ElinDelta.Simulate()) {
                        host?.Delta.AddRemote(CardGenDelta.Create(share));
                        _zone.AddCard(share, other.pos);
                    }
                } else {
                    var parcel = ThingGen.CreateParcel(null, share);
                    parcel.c_idRefName = "emp_story_share".Loc(other.NameSimple);
                    world.SendPackage(parcel);
                }

                EmpLog.Information("Story reward {Id} x{Num}: a share for player {Uid} ({Where})",
                    reward.id, reward.Num, other.uid, here ? "in its bag" : "by mail");
            }
        }
    }

    private static bool Multiplied(Thing reward)
    {
        // known by every player already, or the world's
        var kind = reward.trait.GetType().Name;
        if (kind.Contains("Recipe") || kind.Contains("Deed") || kind.Contains("License")) {
            return false;
        }

        return reward.rarity < Rarity.Artifact || _ownArtifacts.Contains(reward.id);
    }
}
