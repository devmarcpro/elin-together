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
// ponytail: given when the reward is given. A player who joins the world later, and the rewards of a world
// played before this, are not caught up (it needs a list of what each quest gave, per player). Next slice
internal partial class ElinNetHost
{
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
