using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Helper.Extensions;

namespace ElinTogether.Helper;

/// <summary>
///     The floating windows of a player (bag, open containers it carries, abilities) and the layout of its screen
///     stay as they are when a player alone changes map: the game only closes them with the game itself
///     (Game.Kill), and puts them back when a save is loaded (Game.Load). <br />
///     A client gets a whole new game each time the host sends its world (ElinNetClient.OnSaveDataProbe): the
///     windows are closed with the old one, and what the new one says about the screen (Player.pref, dataWindow,
///     widgets, hotbars, Game.config) is the host's. Kept here from one game to the next, then opened again once
///     the map is in place
/// </summary>
internal static class OpenWindows
{
    private static Player? _player;
    private static Game.Config? _config;
    private static readonly Dictionary<int, Window.SaveData> _bags = [];
    private static readonly HashSet<int> _open = [];
    private static bool _inventory;
    private static bool _ability;
    private static bool _zoomOut;

    /// <summary>
    ///     Before the game goes away: what is open, and where
    /// </summary>
    internal static void Keep()
    {
        // a second world before the first one stood on a map: what was kept for the first is still good
        if (!EClass.core.IsGameStarted || EClass.pc is not { } pc) {
            return;
        }

        Clear();

        try {
            // as Game.Save writes them down: place and size of the floating windows, place of the widgets
            EClass.player.OnBeforeSave();
            EClass.ui.widgets.UpdateConfigs();

            foreach (var thing in pc.things.Flatten()) {
                if (thing.c_windowSaveData is { } data) {
                    _bags[thing.uid] = data;
                }
            }

            foreach (var layer in LayerInventory.listInv) {
                if (!layer.IsFloat) {
                    continue;
                }

                if (layer.mainInv) {
                    _inventory = true;
                } else if (layer.GetPlayerContainer() is { } bag) {
                    _open.Add(bag.uid);
                }
            }

            _ability = EClass.game.altAbility && EClass.ui.IsAbilityOpen;
            _zoomOut = ActionMode.Adv?.zoomOut2 ?? false;
            _config = EClass.game.config;
            _player = EClass.player;
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not note the open windows before the world is replaced");
            Clear();
        }
    }

    /// <summary>
    ///     The new game is in place, not started yet (before Game.OnGameInstantiated, which reads the widgets, and
    ///     Player.OnLoad, which reads dataWindow): the screen of this player goes in, in place of the host's
    /// </summary>
    internal static void Carry(Chara chara)
    {
        if (_player is not { } old || EClass.game?.player is not { } player || player == old) {
            return;
        }

        try {
            player.pref = old.pref;
            player.dataWindow = Window.dictData;
            player.layerAbilityConfig = old.layerAbilityConfig;
            player.mainWidgets = old.mainWidgets;
            player.subWidgets = old.subWidgets;
            player.useSubWidgetTheme = old.useSubWidgetTheme;
            player.windowAllyInv = old.windowAllyInv;
            player.openContainerCenter = old.openContainerCenter;
            player.dataPick = old.dataPick;
            player.favAbility = old.favAbility;
            player.priorityActions = old.priorityActions;
            player.questTracker = old.questTracker;
            player.trackedCategories = old.trackedCategories;
            player.trackedCards = old.trackedCards;
            player.trackedElements = old.trackedElements;
            player.memo = old.memo;
            player.memo2 = old.memo2;
            if (_config is not null) {
                EClass.game.config = _config;
            }

            // the cards are other objects in this copy of the world: found again by number
            var things = chara.things.Flatten().ToList();
            foreach (var thing in things) {
                if (_bags.TryGetValue(thing.uid, out var data)) {
                    // closing the window with the old game marked it closed
                    data.open |= _open.Contains(thing.uid);
                    thing.c_windowSaveData = data;
                }
            }

            player.hotbars = old.hotbars;
            foreach (var bar in old.hotbars.bars) {
                if (bar is null) {
                    continue;
                }

                // its widget went with the old game
                bar.actor = null;
                foreach (var page in bar.pages) {
                    for (var i = 0; i < page.items.Count; i++) {
                        switch (page.items[i]) {
                            case HotItemThing hot:
                                hot.thing = things.Find(t => t.uid == hot.thing?.uid);
                                if (hot.thing is null) {
                                    page.items[i] = null;
                                }

                                break;
                            case HotItemFocusPos { zone: not null } focus:
                                focus.zone = EClass.game.spatials.Find(focus.zone.uid);
                                break;
                        }
                    }
                }
            }
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not carry the screen layout over to the world received");
        }
    }

    /// <summary>
    ///     The map is in place (Scene.Init is done): the windows that were open are opened again, the way Game.Load
    ///     does after a save is loaded. Never twice, never for a dead player, only what the player carries
    /// </summary>
    internal static void Reopen()
    {
        if (_player is null) {
            return;
        }

        try {
            if (EClass.pc is not { isDead: false } pc) {
                return;
            }

            SoundManager.ignoreSounds = true;

            if (EClass.game.altInv) {
                if (_inventory && !LayerInventory.listInv.Exists(l => l.mainInv)) {
                    // the bag, and the containers in it whose window is marked open
                    EClass.ui.OpenFloatInv(true);
                    SoundManager.ignoreSounds = true;
                }

                // a container opened on its own, or one inside another
                foreach (var thing in pc.things.Flatten().ToList()) {
                    if (_open.Contains(thing.uid) && thing.trait is { IsContainer: true } and not TraitToolBelt &&
                        !LayerInventory.IsOpen(thing)) {
                        LayerInventory.CreateContainerPC(thing);
                    }
                }
            }

            if (_ability && EClass.game.altAbility && !EClass.ui.IsAbilityOpen) {
                EClass.ui.ToggleAbility();
            }

            if (ActionMode.Adv is { } adv) {
                adv.zoomOut2 = _zoomOut;
            }

            TooltipManager.Instance.HideTooltips(immediate: true);
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Could not open the windows again after the world was replaced");
        } finally {
            SoundManager.ignoreSounds = false;
            Clear();
        }
    }

    private static void Clear()
    {
        _player = null;
        _config = null;
        _bags.Clear();
        _open.Clear();
        _inventory = _ability = _zoomOut = false;
    }
}
