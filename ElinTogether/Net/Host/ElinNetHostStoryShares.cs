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
///     at its feet; a player elsewhere or not connected gets a parcel in its name in the mail of the base. <br />
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
        if (reward is null || !StoryScope.Active || NetSession.Instance.Transport is ElinNetClient || !IsSharedWorld ||
            !EmpConfig.Server.OncePerPlayer.Value) {
            return;
        }

        _storyRewards.Add((reward, (earner ?? pc).uid));
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
                var share = reward.Duplicate(reward.Num);

                if (other!.IsAliveInCurrentZone && _map.charas.Contains(other)) {
                    var at = other.pos.GetNearestPoint(allowChara: true, allowInstalled: true) ?? other.pos;
                    CardCache.Add(share);
                    using (ElinDelta.Simulate()) {
                        host?.Delta.AddRemote(CardGenDelta.Create(share));
                        _zone.AddCard(share, at);
                    }
                } else {
                    var parcel = ThingGen.CreateParcel(null, share);
                    parcel.c_idRefName = "emp_story_share".Loc(other.NameSimple);
                    world.SendPackage(parcel);
                }

                EmpLog.Information("Story reward {Id} x{Num}: a share for player {Uid} ({Where})",
                    reward.id, reward.Num, other.uid, other.IsAliveInCurrentZone ? "at its feet" : "by mail");
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
