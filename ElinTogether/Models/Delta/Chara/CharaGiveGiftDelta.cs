using ElinTogether.Helper;
using ElinTogether.Net;
using ElinTogether.Patches;
using MessagePack;

namespace ElinTogether.Models;

[MessagePackObject]
public class CharaGiveGiftDelta : ElinDelta
{
    [Key(0)]
    public required RemoteCard From { get; init; }

    [Key(1)]
    public required RemoteCard To { get; init; }

    [Key(2)]
    public required RemoteCard Thing { get; init; }

    /// <summary>
    ///     True while the gift of another player is played here: the task it gives "the player" (the massage of a
    ///     hostess ticket) is set by the giver's own game, see CharaTaskRemoteEvent
    /// </summary>
    internal static bool IsReplaying { get; private set; }

    protected override void OnApply(ElinNetBase net)
    {
        if (From.Find() is not Chara from || To.Find() is not Chara to || Thing.Find() is not Thing thing) {
            return;
        }

        if (net.IsClient && from.IsPC) {
            return;
        }

        if (net.IsHost) {
            net.Delta.AddRemote(this);
        }

        // one out of a stack (the "give" gesture of a client): the gift is that one, not the stack
        if (net.IsHost && Thing.Num > 0 && Thing.Num < thing.Num) {
            using var split = Simulate();
            thing = thing.Split(Thing.Num);
        }

        // what a gift brings back is for "the player" (a hostess ticket: the massage, the arm pillow): another
        // player's gift played here massaged this game's player instead
        using var giver = from.IsRemotePlayer ? RemoteCraft.AsCrafter(from) : null;
        IsReplaying = true;
        try {
            from.Stub_GiveGift(to, thing);
        } finally {
            IsReplaying = false;
        }
    }
}