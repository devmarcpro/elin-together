using ElinTogether.Models;
using ElinTogether.Net;

namespace ElinTogether.Patches;

internal class NetProfileSynchronizationContext : SynchronizationContext
{
    private static RemoteCard? _heldMainHand;
    private static RemoteCard? _heldOffHand;

    private static bool _inputsKnown;
    private static bool _hadPending;
    private static bool _hide;
    private static bool _showOff;
    private static object? _hot;
    private static object? _held;
    private static object? _main;
    private static object? _off;

    private static bool IsPending(Card? card)
    {
        return card is not null && PendingUid.IsPending(card.uid);
    }

    internal static void Update()
    {
        if (core.game?.player?.chara is null) {
            return;
        }

        // Create reads exactly these: nothing changed, same delta (a pending uid may resolve meanwhile: recompute)
        var hot = player.currentHotItem.RenderThing;
        var held = pc.held;
        var main = pc.body.slotMainHand?.thing;
        var off = pc.body.slotOffHand?.thing;
        var hide = pc.combatCount <= 0 && core.config.game.hideWeapons;
        var showOff = core.config.game.showOffhand;
        if (_inputsKnown && !_hadPending && ReferenceEquals(_hot, hot) && ReferenceEquals(_held, held) &&
            ReferenceEquals(_main, main) && ReferenceEquals(_off, off) && _hide == hide && _showOff == showOff) {
            return;
        }

        _inputsKnown = true;
        _hot = hot;
        _held = held;
        _main = main;
        _off = off;
        _hide = hide;
        _showOff = showOff;
        _hadPending = IsPending(hot) || IsPending(held) || IsPending(main) || IsPending(off);

        var delta = CharaSwitchHeldDelta.Create();
        if (_heldMainHand == delta.HeldMainHand && _heldOffHand == delta.HeldOffHand) {
            return;
        }

        _heldMainHand = delta.HeldMainHand;
        _heldOffHand = delta.HeldOffHand;

        NetSession.Instance.Connection!.Delta.AddRemote(delta);
    }
}