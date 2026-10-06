using System.Collections.Generic;
using ElinTogether.Helper;
using ElinTogether.LangMod;
using ElinTogether.Models;
using ElinTogether.Net;
using HarmonyLib;

namespace ElinTogether.Patches;

[HarmonyPatch]
internal class SleepSynchronizationContext : SynchronizationContext
{
    private static readonly HashSet<int> _ready = [];
    private static readonly HashSet<int> _lastReady = [];
    private static bool _sleepStarted;
    private static bool _cancelSent;
    private static bool _nightTick;
    private static readonly List<Chara> _shielded = [];
    private static readonly List<Chara> _noDreams = [];
    private static (Thing? Bed, Thing? Pillow, ItemPosition? PosBed, ItemPosition? PosPillow)? _laidDown;
    private static Thing? _bed;

    private static readonly AccessTools.FieldRef<LayerSleep, int> _minRef =
        AccessTools.FieldRefAccess<LayerSleep, int>("min");
    private static readonly AccessTools.FieldRef<LayerSleep, int> _maxMinRef =
        AccessTools.FieldRefAccess<LayerSleep, int>("maxMin");
    private static readonly AccessTools.FieldRef<LayerSleep, int> _hoursRef =
        AccessTools.FieldRefAccess<LayerSleep, int>("hours");

    internal static bool AllPlayersReady { get; private set; } = true;

    internal static void Update()
    {
        if (pc?.conSleep is null) {
            _cancelSent = false;
        }

        if (NetSession.Instance.Connection is not ElinNetHost host || pc is null) {
            _ready.Clear();
            _lastReady.Clear();
            _sleepStarted = false;
            AllPlayersReady = true;
            return;
        }

        _ready.Clear();
        var alive = 0;
        foreach (var netPlayer in NetSession.Instance.CurrentPlayers) {
            var chara = netPlayer.CharaUid == pc.uid ? pc : netPlayer.FindChara();
            // 死是凉爽的夏夜，可供人无忧的安眠
            if (chara is null or { isDead: true }) {
                continue;
            }

            alive++;
            if (chara.conSleep is not null) {
                _ready.Add(netPlayer.Index);
            }
        }

        // nobody to wait for when alone (the game's own sleep, as AllowPartySleep)
        AllPlayersReady = _ready.Count >= alive;

        if (_sleepStarted || alive < 2) {
            if (_sleepStarted && _ready.Count == 0) {
                _sleepStarted = false;
            }

            _lastReady.Clear();
            _lastReady.UnionWith(_ready);
            return;
        }

        foreach (var index in _ready) {
            if (!_lastReady.Contains(index)) {
                Announce(host, index, true, alive);
            }
        }

        foreach (var index in _lastReady) {
            if (!_ready.Contains(index)) {
                Announce(host, index, false, alive);
            }
        }

        _lastReady.Clear();
        _lastReady.UnionWith(_ready);
    }

    private static void Announce(ElinNetHost host, int playerIndex, bool ready, int total)
    {
        EmpLog.Debug("Sleep vote from {PeerIndex}, ready {SleepReady}, {SleepReadyCount} of {PlayerCount}",
            playerIndex, ready, _ready.Count, total);

        var delta = new SleepReadyDelta {
            PlayerIndex = playerIndex,
            Ready = ready,
            ReadyCount = _ready.Count,
            TotalCount = total,
        };
        delta.Play();
        host.Delta.AddRemote(delta);
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.CanSleep))]
    internal static void AllowPartySleep(Chara __instance, ref bool __result)
    {
        // alone in a session (it opens by itself at load): the game's own rule, as in a solo game
        if (__result || NetSession.Instance.Connection is null || NetSession.Instance.CurrentPlayers.Count <= 1 ||
            !__instance.IsPC) {
            return;
        }

        if (_zone.events.GetEvent<ZoneEventQuest>() is not null) {
            return;
        }

        // a rest dozes off one turn in ten once the player can sleep: only when it is tired for real, or every
        // rest of a session ended in a sleep within seconds
        if (AIPassTimePatch.IsResting) {
            return;
        }

        // are you tired? yes you are
        __result = true;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.Sleep))]
    internal static bool OnPcSleep(Chara __instance, Thing? bed, Thing? pillow, bool pickup,
        ItemPosition? posBed, ItemPosition? posPillow)
    {
        if (NetSession.Instance.Connection is not ElinNetClient client || !__instance.IsPC) {
            return true;
        }

        // forced
        if (ElinDelta.IsApplying) {
            return false;
        }

        if (__instance.conSleep is not null) {
            return false;
        }

        _laidDown = pickup ? (bed, pillow, posBed, posPillow) : null;
        _bed = bed;

        EmpLog.Debug("Requesting party sleep");

        client.Delta.AddRemote(new SleepRequestDelta());
        WidgetPopText.Say("emp_ui_sleep_request".Loc());
        return false;
    }

    /// <summary>
    ///     Sleeping from the hotbar, the game lays the bed and pillow of the bag on the floor and notes on the
    ///     sleep condition to take them back at wake-up. A client's sleep is only a request: its condition comes
    ///     from the host, with nothing to take back, and both stayed on the floor <br />
    ///     What was laid down is kept from the request and put back on the condition as it ends, the game does
    ///     the rest
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(ConSleep), nameof(ConSleep.OnRemoved))]
    internal static void OnPcWake(ConSleep __instance, out ElinDelta.PatchScope __state)
    {
        __state = default;

        if (__instance.owner is not { IsPC: true } || _laidDown is not { } laid) {
            return;
        }

        _laidDown = null;

        // the game's own sleep (no session, or this player simulates the map): it knows what to take back
        if (__instance.pickup) {
            return;
        }

        (__instance.pcBed, __instance.pcPillow, __instance.posBed, __instance.posPillow) = laid;
        __instance.pickup = true;

        // a sleep given up ends by a delta from the host, yet taking the bed back is this player's own act
        __state = ElinDelta.PatchScope.Simulate();
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(ConSleep), nameof(ConSleep.OnRemoved))]
    internal static void OnPcWakeEnd(ElinDelta.PatchScope __state)
    {
        __state.Exit();
    }

    /// <summary>
    ///     The bed this player asked to sleep in, null for none: its own sleep power at wake-up comes from it,
    ///     see <see cref="CharaSleepDelta" />
    /// </summary>
    internal static Thing? TakeBed()
    {
        var bed = _bed;
        _bed = null;
        return bed is { isDestroyed: false } ? bed : null;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(RecipeManager), nameof(RecipeManager.OnSleep))]
    internal static bool OnDreamRecipe(bool ehe)
    {
        return !CharaSleepDelta.DeferRecipe(ehe);
    }

    private static bool InSleepWaitWindow(Chara chara)
    {
        if (chara.conSleep is not { pcSleep: <= 1 } || ui.GetLayer<LayerSleep>() is not null) {
            return false;
        }

        return NetSession.Instance.Connection is not ElinNetHost || !AllPlayersReady;
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(ConSleep), nameof(ConSleep.ConsumeTurn), MethodType.Getter)]
    internal static void FreezeWaitTurns(ConSleep __instance, ref bool __result)
    {
        if (!__result || NetSession.Instance.Connection is null) {
            return;
        }

        if (__instance.owner is { IsPC: true } owner && InSleepWaitWindow(owner)) {
            __result = false;
        }
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.SetAIImmediate))]
    internal static bool CancelSleepOnAction(Chara __instance, AIAct g)
    {
        if (NetSession.Instance.Connection is not { } connection || !__instance.IsPC || g.IsNoGoal) {
            return true;
        }

        if (ElinDelta.IsApplying || !InSleepWaitWindow(__instance)) {
            return true;
        }

        switch (connection) {
            case ElinNetHost:
                __instance.conSleep?.Kill();
                break;
            case ElinNetClient client when !_cancelSent:
                // client wait for delta
                _cancelSent = true;
                EmpLog.Debug("Requesting sleep cancel");
                client.Delta.AddRemote(new SleepCancelDelta());
                break;
        }

        return false;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(ConSleep), nameof(ConSleep.Tick))]
    internal static bool GateSleepTick(ConSleep __instance)
    {
        if (NetSession.Instance.Connection is not { } connection || __instance.owner is not { } owner) {
            return true;
        }

        if (connection.IsClient) {
            return !owner.IsPlayer;
        }

        if (owner.IsRemotePlayer) {
            return false;
        }

        var run = !owner.IsPC || __instance.pcSleep != 1 || AllPlayersReady;
        if (run && owner.IsPC && __instance.pcSleep == 1) {
            ShieldOtherPlayers(owner);
        }

        return run;
    }

    /// <summary>
    ///     The tick that ends the countdown of the host makes the animals of the map sleep beside the bed: the game
    ///     picks them from every chara of the map, taking the companions of the other players and the other players
    ///     themselves from where they stand <br />
    ///     Those skip the game's loop (restrained ones do), and what the game does for the sleeper is done for each
    ///     other player on its own companions, see <see cref="EndSleepTick" />
    /// </summary>
    private static void ShieldOtherPlayers(Chara sleeper)
    {
        _nightTick = true;
        foreach (var chara in _map.charas) {
            if (!chara.isRestrained && CompanionHelper.OwnerOf(chara) is { } who && who != sleeper) {
                chara.isRestrained = true;
                _shielded.Add(chara);
            }
        }
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(ConSleep), nameof(ConSleep.Tick))]
    internal static void EndSleepTick(ConSleep __instance)
    {
        if (!_nightTick) {
            return;
        }

        _nightTick = false;
        foreach (var chara in _shielded) {
            chara.isRestrained = false;
        }

        _shielded.Clear();

        if (__instance.slept && NetSession.Instance.Connection is ElinNetHost host) {
            BringCompanionsBeside(host);
        }
    }

    /// <summary>
    ///     ConSleep.Tick for a player asleep: the animals of its own come beside it, one in five, or all those
    ///     told to by a dialogue. The game only does it for the local player, the host here, so the guests get the
    ///     same
    /// </summary>
    private static void BringCompanionsBeside(ElinNetHost host)
    {
        foreach (var guest in host.ActiveRemoteCharas.Values) {
            if (guest.conSleep is null || !guest.IsInActiveMap || guest.pos.IsInSpot<TraitPillowStrange>()) {
                continue;
            }

            foreach (var chara in CompanionHelper.CompanionsOf(guest)) {
                if (!chara.IsInActiveMap || chara.host != null || chara.noMove || chara.conSuspend != null ||
                    chara.isRestrained) {
                    continue;
                }

                if (!chara.GetBool(123) &&
                    !(System.Array.IndexOf(chara.race.tag, "sleepBeside") >= 0 && rnd(5) == 0)) {
                    continue;
                }

                chara.MoveImmediate(guest.pos);
                chara.SetDir(chara.IsPCC ? guest.dir : 0);
                chara.Say("sleep_beside", chara, guest);
                if (!chara.HasCondition<ConSleep>()) {
                    chara.AddCondition<ConSleep>(20 + rnd(25), force: true);
                }
            }
        }
    }

    /// <summary>
    ///     A dream monster (succubus, dream worm) is picked among the charas of the map, the other players' ones
    ///     included: one of them would be pulled onto the bed of the sleeper <br />
    ///     "Told to leave dreamers alone" is how the game lets a chara out of it
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(ConSleep), nameof(ConSleep.SuccubusVisit))]
    internal static void ShieldPlayersFromDreams()
    {
        if (NetSession.Instance.Connection is not ElinNetHost host) {
            return;
        }

        foreach (var chara in host.ActiveRemoteCharas.Values) {
            if (chara.GetInt(119) == 0) {
                chara.SetInt(119, 1);
                _noDreams.Add(chara);
            }
        }
    }

    [HarmonyFinalizer]
    [HarmonyPatch(typeof(ConSleep), nameof(ConSleep.SuccubusVisit))]
    internal static void EndDreamVisit()
    {
        foreach (var chara in _noDreams) {
            chara.SetInt(119, 0);
        }

        _noDreams.Clear();
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(LayerSleep), nameof(LayerSleep.Sleep))]
    internal static void OnSleepStart(int _hours)
    {
        if (NetSession.Instance.Connection is not ElinNetHost host) {
            return;
        }

        _sleepStarted = true;

        EmpLog.Debug("Party sleep started {SleepHours}", _hours);

        host.Delta.AddRemote(new SleepStartDelta {
            Hours = _hours,
        });
    }

    [HarmonyPostfix]
    [HarmonyPatch(typeof(Chara), nameof(Chara.OnSleep), typeof(int), typeof(int), typeof(bool))]
    internal static void OnHostSleep(Chara __instance, int power, int days)
    {
        if (NetSession.Instance.Connection is not ElinNetHost host) {
            return;
        }

        if (!__instance.IsPC) {
            return;
        }

        EmpLog.Debug("Zzz party sleep {SleepPower}", power);

        host.Delta.AddRemote(new CharaSleepDelta {
            Power = power,
            Days = days,
        });

        foreach (var chara in host.ActiveRemoteCharas.Values) {
            if (chara.conSleep is { } sleep) {
                sleep.Kill();
            }
        }
    }

    /// <summary>
    ///     Waking up away from a base, the game walks the player through each of its bases and back, to catch
    ///     them up on the hours slept: zone changes one after the other, in one frame. For the host of a session
    ///     these are real moves to everything else here. The players asleep next to it were handed the map, the
    ///     way back waited for that map to be recalled while the game went on without waiting, and the host woke
    ///     up looking at a map its character was not on, unable to do anything <br />
    ///     Not done while others are connected: a base catches up when someone enters it <br />
    ///     Nor for a guest, alone on a map it holds or not: the bases belong to the host's world, and each
    ///     move of the walk is a request for a lease to the host
    /// </summary>
    [HarmonyPrefix]
    [HarmonyPatch(typeof(Player), nameof(Player.SimulateFaction))]
    internal static bool OnSimulateFaction()
    {
        var session = NetSession.Instance;
        if (session.Transport is ElinNetClient) {
            return false;
        }

        return session.Connection is not ElinNetHost || session.CurrentPlayers.Count < 2;
    }

    [HarmonyPrefix]
    [HarmonyPatch(typeof(LayerSleep), nameof(LayerSleep.Advance))]
    internal static bool OnClientAdvance(LayerSleep __instance)
    {
        if (NetSession.Instance.Connection is not ElinNetClient) {
            return true;
        }

        if (_minRef(__instance) > _maxMinRef(__instance) + 600) {
            EmpLog.Warning("Sleep layer timed out waiting for host wake");
            CloseSleepLayer(__instance);
        } else {
            _minRef(__instance) += 10;
        }

        return false;
    }

    internal static void CloseSleepLayerIfOpen()
    {
        if (ui.GetLayer<LayerSleep>() is { } layer) {
            CloseSleepLayer(layer);
        }
    }

    private static void CloseSleepLayer(LayerSleep layer)
    {
        if (_maxMinRef(layer) == int.MaxValue) {
            return;
        }

        _maxMinRef(layer) = int.MaxValue;
        layer.CancelInvoke();
        Msg.Say("slept", _hoursRef(layer).ToString());
        ui.ShowCover();
        TweenUtil.Delay(layer.hideDelay, () => ui.HideCover(layer.coverHide, layer.Close));
    }
}