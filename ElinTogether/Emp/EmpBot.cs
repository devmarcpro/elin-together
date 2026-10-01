#if DEBUG
using System;
using System.Collections.Generic;
using System.Linq;
using ElinTogether.Net;
using UnityEngine;
using UnityEngine.UI;

namespace ElinTogether;

/// <summary>
///     A game started with -empbot joins the local session by itself, then plays at random: a second player
///     to shake the mod with, see <see cref="EmpBotLauncher" />
/// </summary>
internal class EmpBot : EMono
{
    private const float ConnectRetry = 30f;

    internal static readonly bool Requested = HasArg("-empbot");

    /// <summary>
    ///     Also what changes the world for everyone: accepting quests, selling through the shipping chest,
    ///     digging, cutting, building, taking from chests
    /// </summary>
    private static readonly bool _allActions = HasArg("-empbotall");

    private readonly List<(string Name, int Weight, Func<string> Run)> _actions = [];
    private float _connectAt;
    private float _next;
    private int _steps;

    private void Awake()
    {
        _actions.Add(("walk", 5, Walk));
        _actions.Add(("step", 4, Step));
        _actions.Add(("travel", 1, Travel));
        _actions.Add(("pick", 3, PickUp));
        _actions.Add(("drop", 3, Drop));
        _actions.Add(("eat", 1, Eat));
        _actions.Add(("say", 1, Say));
        _actions.Add(("attack", 3, Attack));
        _actions.Add(("equip", 2, Equip));
        _actions.Add(("wait", 2, () => "nothing"));

        if (_allActions) {
            _actions.Add(("quest", 2, AcceptQuest));
            _actions.Add(("ship", 1, Ship));
            _actions.Add(("tool", 4, UseTool));
            _actions.Add(("build", 2, Build));
            _actions.Add(("chest", 3, UseChest));
        }
    }

    private void Update()
    {
        if (Time.unscaledTime < _next || NetShutdown.IsQuitting) {
            return;
        }

        _next = Time.unscaledTime + 1f + EClass.rnd(15) / 10f;

        try {
            Tick();
        } catch (Exception ex) {
            EmpLog.Warning(ex, "Bot: step failed");
        }
    }

    private static bool HasArg(string arg)
    {
        return Array.IndexOf(Environment.GetCommandLineArgs(), arg) >= 0;
    }

    private void Tick()
    {
        if (core?.scene is null || ui is null) {
            return;
        }

        // a new player: the host asks for a character, taken as it comes
        if (ui.GetLayer<LayerEditBio>() is { } bio) {
            bio.GetComponentInChildren<Content>().transform.Find("ButtonEmbark")
                .GetComponentInChildren<UIButton>().onClick.Invoke();
            EmpLog.Information("Bot: character created");
            return;
        }

        if (!core.IsGameStarted) {
            // which character to play: the first one
            if (NetSession.Instance.Transport is ElinNetClient &&
                ui.layers.OfType<Dialog>().LastOrDefault() is { } choice &&
                choice.GetComponentsInChildren<Button>(true).FirstOrDefault(b => b.name.StartsWith("ButtonGeneral(Clone)")) is { } first) {
                first.onClick.Invoke();
                EmpLog.Information("Bot: plays {Chara}", Label(first));
                return;
            }

            Join();
            return;
        }

        if (core.scene.mode != Scene.Mode.Zone || pc?.currentZone != _zone || !NetSession.Instance.HasActiveConnection) {
            return;
        }

        if (pc.isDead) {
            LeaveDeathScreen();
            return;
        }

        // a player's input is held while its character changes hands, see ElinNetClient.IsInTransfer
        if (NetSession.Instance.Transport is ElinNetClient { IsInTransfer: true }) {
            return;
        }

        // what would wait for a click: a game dialog, a yes/no question
        foreach (var layer in ui.layers.Where(l => l is LayerDrama or Dialog).ToArray()) {
            layer.Close();
        }

        var total = _actions.Sum(a => a.Weight);
        var roll = EClass.rnd(total);
        var action = _actions.First(a => (roll -= a.Weight) < 0);

        string result;
        try {
            result = action.Run();
        } catch (Exception ex) {
            result = $"failed: {ex.GetType().Name} {ex.Message}";
        }

        EmpLog.Information("Bot: {Step} {Action}: {Result}", ++_steps, action.Name, result);
    }

    private void Join()
    {
        if (core.scene.mode != Scene.Mode.Title || Time.unscaledTime < _connectAt) {
            return;
        }

        // a game that just started may miss its first handshake
        _connectAt = Time.unscaledTime + ConnectRetry;

        var session = NetSession.Instance;
        if (session.Transport is not null && !session.HasActiveConnection) {
            session.ResetSession();
        }

        if (session.Transport is null) {
            EmpLog.Information("Bot: joining the local session");
            session.InitializeComponent<ElinNetClient>().ConnectLocalPort();
        }
    }

    /// <summary>
    ///     The death screen, as a player: confirm the last words, then pick where to come back (never "buried")
    /// </summary>
    private void LeaveDeathScreen()
    {
        if (ui.layers.OfType<Dialog>().LastOrDefault() is not { } dialog) {
            return;
        }

        var buttons = dialog.GetComponentsInChildren<Button>(true)
            .Where(b => b.name.StartsWith("ButtonGeneral(Clone)"))
            .ToList();
        if (buttons.Count == 0) {
            return;
        }

        var confirm = buttons.Find(b => Label(b) == Lang.Get("ok"));
        if (confirm is not null) {
            confirm.onClick.Invoke();
            return;
        }

        if (buttons.Count < 2) {
            return;
        }

        var choice = buttons[EClass.rnd(buttons.Count - 1)];
        EmpLog.Information("Bot: died, comes back with \"{Choice}\"", Label(choice));
        choice.onClick.Invoke();
        _next = Time.unscaledTime + 8f;
    }

    private static string Label(Button button)
    {
        return button.GetComponentsInChildren<Text>(true).LastOrDefault()?.text ?? "";
    }

    private static string Walk()
    {
        var point = pc.pos.GetRandomPoint(2 + EClass.rnd(8), true, false);
        if (point is null) {
            return "nowhere to go";
        }

        pc.SetAIImmediate(new AI_Goto(point.Copy(), 0));
        return $"to {point.x},{point.z}";
    }

    private static string Step()
    {
        var point = pc.pos.GetRandomPoint(4, true, false);
        if (point is null) {
            return "nowhere to go";
        }

        for (var i = EClass.rnd(4); i >= 0; i--) {
            pc.TryMoveTowards(point);
        }

        return $"towards {point.x},{point.z}";
    }

    private string Travel()
    {
        var zones = game.spatials.map.Values
            .OfType<Zone>()
            .Where(z => z != _zone && z.lv == 0 && (z is Zone_Town || z.IsPCFaction))
            .ToList();
        if (zones.Count == 0) {
            return "nowhere to travel";
        }

        var zone = zones[EClass.rnd(zones.Count)];
        pc.MoveZone(zone);
        _next = Time.unscaledTime + 10f;
        return $"to {zone.Name}";
    }

    private static string PickUp()
    {
        var things = _map.things
            .Where(t => t.placeState == PlaceState.roaming && !t.isNPCProperty && t.pos.Distance(pc.pos) <= 6)
            .ToList();
        if (things.Count == 0) {
            return "nothing to pick up";
        }

        var thing = things[EClass.rnd(things.Count)];
        var name = thing.id;
        pc.Pick(thing);
        return name;
    }

    private static List<Thing> Loose()
    {
        return pc.things.Where(t => !t.isEquipped && !t.IsContainer && t.id != "money").ToList();
    }

    private static string Drop()
    {
        var things = Loose();
        if (things.Count == 0) {
            return "empty bag";
        }

        var thing = things[EClass.rnd(things.Count)];
        var name = thing.id;
        pc.DropThing(thing);
        return name;
    }

    private static string Eat()
    {
        var food = pc.things.FirstOrDefault(t => t.IsFood && !t.isEquipped);
        if (food is null) {
            return "nothing to eat";
        }

        var name = food.id;
        pc.InstantEat(food);
        return name;
    }

    private static string Say()
    {
        var text = $"bot {100 + EClass.rnd(900)}";
        Msg.Say(text);
        ActionMode.Adv.OnEnterChat(text);
        return text;
    }

    private static string Attack()
    {
        var enemy = _map.charas
            .Where(c => !c.isDead && c.IsHostile(pc) && c.pos.Distance(pc.pos) <= 8)
            .OrderBy(c => c.pos.Distance(pc.pos))
            .FirstOrDefault();
        if (enemy is null) {
            return "no enemy";
        }

        if (enemy.pos.Distance(pc.pos) > 1) {
            pc.SetAIImmediate(new AI_Goto(enemy, 1));
            return $"closing on {enemy.id}";
        }

        ACT.Melee.Perform(pc, enemy, enemy.pos);
        return $"hits {enemy.id}";
    }

    private static string Equip()
    {
        var things = pc.things.Where(t => t.IsEquipment && !t.isEquipped).ToList();
        if (things.Count > 0) {
            var thing = things[EClass.rnd(things.Count)];
            var name = thing.id;
            pc.body.Equip(thing);
            return $"on {name}";
        }

        var worn = pc.body.slots.Where(s => s.thing is not null).ToList();
        if (worn.Count == 0) {
            return "nothing to wear";
        }

        var slot = worn[EClass.rnd(worn.Count)];
        var removed = slot.thing.id;
        pc.body.Unequip(slot);
        return $"off {removed}";
    }

    /// <summary>
    ///     Takes a tool in hand and uses it on a tile nearby: mine, dig, cut
    /// </summary>
    private string UseTool()
    {
        var tools = pc.things.Where(t => t.id is "pickaxe" or "shovel" or "axe").ToList();
        if (tools.Count == 0) {
            return "no tool";
        }

        var tool = tools[EClass.rnd(tools.Count)];
        pc.HoldCard(tool);

        for (var i = 0; i < 60; i++) {
            var point = pc.pos.GetRandomPoint(3, false, true, true);
            if (point is null || !point.IsValid) {
                continue;
            }

            AIAct? task = tool.id switch {
                "pickaxe" when TaskMine.CanMine(point, tool) => new TaskMine {
                    pos = point.Copy(),
                },
                "shovel" when !point.HasBlock && !point.HasObj && !point.HasChara => new TaskDig {
                    pos = point.Copy(),
                    mode = TaskDig.Mode.RemoveFloor,
                },
                "axe" when point.HasObj => TaskHarvest.TryGetAct(pc, point),
                _ => null,
            };
            if (task is null) {
                continue;
            }

            pc.SetAI(task);
            // the time to get somewhere with it
            _next = Time.unscaledTime + 4f;
            return $"{tool.id} at {point.x},{point.z}";
        }

        return $"{tool.id}: nothing to do here";
    }

    private string Build()
    {
        var things = pc.things.Where(t => t.id is "chest6" or "torch" or "log" or "plank").ToList();
        if (things.Count == 0) {
            return "nothing to place";
        }

        var thing = things[EClass.rnd(things.Count)];
        var name = thing.id;

        var point = pc.pos.GetRandomPoint(2, true, false);
        if (point is null || point.HasObj || point.HasBlock) {
            return "no room";
        }

        pc.HoldCard(thing);
        if (thing.trait.GetRecipe() is not { } recipe) {
            return $"{name} cannot be placed";
        }

        var task = new TaskBuild {
            recipe = recipe,
            held = pc.held,
            pos = point.Copy(),
        };

        // what the build mode sets before the game places something held
        var build = ActionMode.Build;
        build.bridgeHeight = -1;
        build.recipe = recipe;
        build.mold = task;

        pc.SetAI(task);
        _next = Time.unscaledTime + 3f;
        return $"{name} at {point.x},{point.z}";
    }

    private static string UseChest()
    {
        var chests = _map.things
            .Where(t => t.IsContainer && t.placeState == PlaceState.installed && !t.isNPCProperty && t.c_lockLv == 0 &&
                        t.pos.Distance(pc.pos) <= 8)
            .ToList();
        if (chests.Count == 0) {
            return "no chest";
        }

        var chest = chests[EClass.rnd(chests.Count)];
        if (chest.things.Count > 0 && EClass.rnd(2) == 0) {
            var taken = chest.things[EClass.rnd(chest.things.Count)];
            var name = taken.id;
            pc.Pick(taken);
            return $"takes {name} from {chest.id}";
        }

        var things = Loose();
        if (things.Count == 0) {
            return "empty bag";
        }

        var stored = things[EClass.rnd(things.Count)];
        var id = stored.id;
        chest.AddThing(stored);
        return $"puts {id} in {chest.id}";
    }

    private static string AcceptQuest()
    {
        var giver = _map.charas.Find(c => c.quest is not null && !game.quests.list.Contains(c.quest));
        if (giver is null) {
            return "nobody offers a quest";
        }

        var quest = giver.quest;
        game.quests.Start(quest);
        return $"{quest.id} {quest.uid}";
    }

    private static string Ship()
    {
        var things = Loose();
        if (things.Count == 0) {
            return "empty bag";
        }

        var thing = things[EClass.rnd(things.Count)];
        var name = thing.id;
        game.cards.container_shipping.AddThing(thing);
        return name;
    }
}
#endif
