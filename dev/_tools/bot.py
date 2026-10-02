"""Bot qui joue au hasard sur une des fenetres, pour secouer le mod. Sur des instances deja lancees.

    python _tools/mp_test.py                       # une fois : host + 1 client dans la Prairie
    python _tools/bot.py --minutes 5 --seed 1      # le client fait n'importe quoi pendant 5 minutes
    python _tools/bot.py --who host                # c'est l'host qui fait n'importe quoi
    python _tools/bot.py --only marche,voyage      # seulement certaines actions
    python _tools/bot.py --watch --minutes 5       # seulement surveiller : le bot lance depuis le menu ElinTogether
                                                   # (onglet Lobby, "Add a bot player") joue tout seul

Le bot ne sait pas si le jeu se comporte "bien". Il verifie, toutes les quelques actions :
  - les deux jeux repondent encore et le client est toujours connecte
  - aucune nouvelle exception dans les journaux des deux jeux, aucune erreur dans celui du mod
  - aucun objet en double (deux objets differents avec le meme numero)
  - le journal de quetes est le meme des deux cotes (quetes d'histoire ; les quetes aleatoires sont par joueur)
  - sur la meme carte : chaque joueur est vu au meme endroit, avec la meme vie, le meme sac et le meme or,
    et la carte porte le meme nombre d'objets
Le meme --seed rejoue la meme suite d'actions. Tout est ecrit dans _shots/bot-<date>.log.
"""
import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import SHOTS, shot, state  # noqa: E402
from travel_suite import HOME, LOCALLOW, LUMIEST, VERNIS, ev, session_log_lines  # noqa: E402

ZONES = {HOME: "Prairie", VERNIS: "Vernis", LUMIEST: "Lumiest"}
PC = "EClass.pc"
NEAR = "x.pos.Distance(EClass.pc.pos)"

OUT = None


def say(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    if OUT:
        OUT.write(line + "\n")
        OUT.flush()


# ---------------------------------------------------------------- actions (ce que le joueur ferait)

def a_marche(bot, rng):
    return ev(bot, f'var p = {PC}.pos.GetRandomPoint({rng.randint(2, 9)}, true, false, false); if (p == null) return "nulle part"; '
                   f'{PC}.SetAIImmediate(new AI_Goto(p.Copy(), 0)); return "vers " + p.x + "," + p.z;')


def a_pas(bot, rng):
    return ev(bot, f'var p = {PC}.pos.GetRandomPoint(4, true, false, false); if (p == null) return "nulle part"; '
                   f'for (var i = 0; i < {rng.randint(1, 4)}; i++) {PC}.TryMoveTowards(p); return "pas vers " + p.x + "," + p.z;')


def a_voyage(bot, rng):
    here = (state(bot).get("zone") or {}).get("uid")
    dest = rng.choice([z for z in ZONES if z != here])
    ev(bot, f'{PC}.MoveZone(EClass.game.spatials.Find({dest})); "ok"')
    t0 = time.time()
    while time.time() - t0 < 120:
        close_dialogs(bot)
        s = state(bot)
        if s.get("sceneMode") == "Zone" and (s.get("zone") or {}).get("uid") == dest and s.get("connected"):
            time.sleep(3)
            return f"arrive a {ZONES[dest]} en {time.time() - t0:.0f} s"
        time.sleep(1)
    raise Problem(f"voyage vers {ZONES[dest]} pas termine apres 120 s")


def a_ramasse(bot, rng):
    return ev(bot, f'var l = EClass._map.things.Where(x => x.placeState == PlaceState.roaming && !x.isNPCProperty && {NEAR} <= 6).ToList(); '
                   f'if (l.Count == 0) return "rien a ramasser"; var t = l[EClass.rnd(l.Count)]; var n = t.id; {PC}.Pick(t); return "ramasse " + n;')


def a_pose(bot, rng):
    return ev(bot, f'var l = {PC}.things.Where(x => !x.isEquipped && !x.IsContainer && x.id != "money").ToList(); '
                   f'if (l.Count == 0) return "sac vide"; var t = l[EClass.rnd(l.Count)]; var n = t.id; {PC}.DropThing(t); return "pose " + n;')


def a_mange(bot, rng):
    return ev(bot, f'var t = {PC}.things.Where(x => x.IsFood && !x.isEquipped).FirstOrDefault(); if (t == null) return "rien a manger"; '
                   f'var n = t.id; {PC}.InstantEat(t); return "mange " + n;')


def a_parle(bot, rng):
    text = f"bot {rng.randint(100, 999)}"
    ev(bot, f'Msg.Say("{text}"); ActionMode.Adv.OnEnterChat("{text}"); "ok"')
    return f'dit "{text}"'


def a_attaque(bot, rng):
    return ev(bot, f'var c = EClass._map.charas.Where(x => !x.isDead && x.IsHostile({PC}) && {NEAR} <= 8).OrderBy(x => {NEAR}).FirstOrDefault(); '
                   f'if (c == null) return "aucun ennemi"; '
                   f'if (c.pos.Distance({PC}.pos) > 1) {{ {PC}.SetAIImmediate(new AI_Goto(c, 1)); return "approche " + c.id; }} '
                   f'ACT.Melee.Perform({PC}, c, c.pos); return "frappe " + c.id;')


def a_quete(bot, rng):
    if rng.random() < 0.6:
        return ev(bot, 'var c = EClass._map.charas.Find(x => x.quest != null && !EClass.game.quests.list.Contains(x.quest)); '
                       'if (c == null) return "personne ne propose de quete"; var q = c.quest; EClass.game.quests.Start(q); return "accepte " + q.id + " " + q.uid;')
    return ev(bot, 'var l = EClass.game.quests.list.Where(x => x.IsRandomQuest).ToList(); if (l.Count == 0) return "aucune quete a rendre"; '
                   'var q = l[EClass.rnd(l.Count)]; var n = q.id + " " + q.uid; q.Complete(); return "rend " + n;')


def a_vend(bot, rng):
    return ev(bot, f'var l = {PC}.things.Where(x => !x.isEquipped && !x.IsContainer && x.id != "money").ToList(); '
                   f'if (l.Count == 0) return "sac vide"; var t = l[EClass.rnd(l.Count)]; var n = t.id; '
                   f'EClass.game.cards.container_shipping.AddThing(t); return "met " + n + " dans la caisse d\'expedition";')


def a_equipe(bot, rng):
    return ev(bot, f'var l = {PC}.things.Where(x => x.IsEquipment && !x.isEquipped).ToList(); '
                   f'if (l.Count == 0) {{ var w = {PC}.body.slots.Where(s => s.thing != null).ToList(); if (w.Count == 0) return "rien a equiper"; '
                   f'var s = w[EClass.rnd(w.Count)]; var m = s.thing.id; {PC}.body.Unequip(s); return "retire " + m; }} '
                   f'var t = l[EClass.rnd(l.Count)]; var n = t.id; {PC}.body.Equip(t); return "equipe " + n;')


def a_outil(bot, rng):
    """Prendre un outil en main et s'en servir sur une case proche : miner, creuser, couper."""
    r = ev(bot, f'var tools = {PC}.things.Where(x => x.id == "pickaxe" || x.id == "shovel" || x.id == "axe").ToList(); '
                f'if (tools.Count == 0) return "aucun outil"; var tool = tools[EClass.rnd(tools.Count)]; {PC}.HoldCard(tool); '
                f'for (var i = 0; i < 60; i++) {{ var p = {PC}.pos.GetRandomPoint(3, false, true, true); if (p == null || !p.IsValid) continue; '
                f'AIAct task = null; '
                f'if (tool.id == "pickaxe" && TaskMine.CanMine(p, tool)) task = new TaskMine {{ pos = p.Copy() }}; '
                f'else if (tool.id == "shovel" && !p.HasBlock && !p.HasObj && !p.HasChara) task = new TaskDig {{ pos = p.Copy(), mode = TaskDig.Mode.RemoveFloor }}; '
                f'else if (tool.id == "axe" && p.HasObj) task = TaskHarvest.TryGetAct({PC}, p); '
                f'if (task != null) {{ {PC}.SetAI(task); return tool.id + " en " + p.x + "," + p.z; }} }} '
                f'return tool.id + " : rien a faire ici";')
    if " en " in r:
        time.sleep(rng.uniform(3, 6))
    return r


def a_construit(bot, rng):
    r = ev(bot, f'var l = {PC}.things.Where(x => x.id == "chest6" || x.id == "torch" || x.id == "log" || x.id == "plank").ToList(); '
                f'if (l.Count == 0) return "rien a installer"; var t = l[EClass.rnd(l.Count)]; var n = t.id; '
                f'var p = {PC}.pos.GetRandomPoint(2, true, false, false); if (p == null || p.HasObj || p.HasBlock) return "pas de place"; '
                f'{PC}.HoldCard(t); var recipe = t.trait.GetRecipe(); if (recipe == null) return n + " : pas installable"; '
                f'var task = new TaskBuild {{ recipe = recipe, held = {PC}.held, pos = p.Copy() }}; '
                f'var build = ActionMode.Build; build.bridgeHeight = -1; build.recipe = recipe; build.mold = task; '
                f'{PC}.SetAI(task); return "installe " + n + " en " + p.x + "," + p.z;')
    if r.startswith("installe"):
        time.sleep(rng.uniform(2, 4))
    return r


def a_coffre(bot, rng):
    return ev(bot, f'var cs = EClass._map.things.Where(x => x.IsContainer && x.placeState == PlaceState.installed && !x.isNPCProperty '
                   f'&& x.c_lockLv == 0 && {NEAR} <= 8).ToList(); if (cs.Count == 0) return "pas de coffre"; var c = cs[EClass.rnd(cs.Count)]; '
                   f'if (c.things.Count > 0 && EClass.rnd(2) == 0) {{ var t = c.things[EClass.rnd(c.things.Count)]; var n = t.id; {PC}.Pick(t); return "prend " + n + " dans " + c.id; }} '
                   f'var l = {PC}.things.Where(x => !x.isEquipped && !x.IsContainer && x.id != "money").ToList(); if (l.Count == 0) return "sac vide"; '
                   f'var g = l[EClass.rnd(l.Count)]; var m = g.id; c.AddThing(g); return "range " + m + " dans " + c.id;')


def a_compagnon(bot, rng):
    ctx = a_compagnon.ctx
    if ctx["who"] != "client" or (state(bot).get("zone") or {}).get("uid") != (state(ctx["host"]).get("zone") or {}).get("uid"):
        return "pas sur la carte de l'host"
    if ctx["allies"] >= 2:
        return "deja 2 compagnons"
    from companion_suite import recruit
    uid = recruit(bot, state(bot)["pc"]["uid"], ctx["host"])
    ctx["allies"] += 1
    return f"recrute un animal ({uid})"


def a_reconnecte(bot, rng):
    ctx = a_reconnecte.ctx
    if ctx["who"] != "client":
        return "seul un client peut se deconnecter"
    ev(bot, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
    time.sleep(3)
    if state(bot).get("sceneMode") != "Title":
        emp.call(bot, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
    time.sleep(rng.uniform(3, 8))
    t0 = time.time()
    from mp_test import join_client
    join_client(ctx["host"], bot, "bot")
    time.sleep(4)
    return f"deconnecte puis revenu en {time.time() - t0:.0f} s"


def give_kit(host, uid):
    """L'host donne au bot de quoi tout essayer : outils, de quoi construire, a manger."""
    return ev(host, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); if (c == null) return "absent"; '
                    'foreach (var id in new[] { "pickaxe", "shovel", "axe", "chest6", "torch", "log", "plank", "dish_soup" }) '
                    '{ if (c.things.Find(id) == null) c.AddThing(ThingGen.Create(id)); } return "ok";')


def a_attend(bot, rng):
    time.sleep(rng.uniform(1, 3))
    return "ne fait rien"


ACTIONS = {
    "marche": (a_marche, 5), "pas": (a_pas, 4), "voyage": (a_voyage, 1), "ramasse": (a_ramasse, 3), "pose": (a_pose, 3),
    "mange": (a_mange, 1), "parle": (a_parle, 1), "attaque": (a_attaque, 3), "quete": (a_quete, 2), "vend": (a_vend, 1),
    "equipe": (a_equipe, 2), "attend": (a_attend, 1),
    "outil": (a_outil, 4), "construit": (a_construit, 2), "coffre": (a_coffre, 3), "compagnon": (a_compagnon, 1),
    "reconnecte": (a_reconnecte, 1),
}


def click(port, label):
    """Clique un bouton de la fenetre de dialogue ouverte, par son texte."""
    return ev(port, 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return "pas de dialogue"; '
                    'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(true).FirstOrDefault(x => '
                    f'x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text == "{label}")); '
                    'if (b == null) return "pas de bouton"; b.onClick.Invoke(); return "clic";')


def choices(port):
    return ev(port, 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return ""; '
                    'return string.Join("|", d.GetComponentsInChildren<UnityEngine.UI.Button>(true).Where(x => x.name.StartsWith("ButtonGeneral(Clone)"))'
                    '.Select(x => x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Last().text));').split("|")


def die_and_return(bot, rng):
    """L'ecran de mort, comme un joueur : valider les derniers mots, puis choisir ou revenir (jamais "enterre")."""
    t0 = time.time()
    while "Ok" not in choices(bot):
        if time.time() - t0 > 20:
            raise Problem("mort, mais la fenetre des derniers mots n'apparait pas")
        time.sleep(1)
    click(bot, "Ok")
    t0 = time.time()
    while True:
        options = [c for c in choices(bot) if c and c not in ("Ok", "Cancel")]
        if len(options) >= 2:
            break
        if time.time() - t0 > 20:
            raise Problem(f"mort, mais le choix du retour n'apparait pas (boutons : {options})")
        time.sleep(1)
    choice = rng.choice(options[:-1])
    click(bot, choice)
    t0 = time.time()
    while time.time() - t0 < 120:
        s = state(bot)
        if s.get("sceneMode") == "Zone" and s.get("connected") and ev(bot, "EClass.pc.isDead.ToString()") == "False":
            time.sleep(3)
            return f'mort, choisit "{choice}", revient a {(state(bot).get("zone") or {}).get("name")} en {time.time() - t0:.0f} s'
        time.sleep(1)
    raise Problem(f'mort, choisit "{choice}", mais ne revient pas apres 120 s')


# ---------------------------------------------------------------- verifications

class Problem(Exception):
    pass


def close_dialogs(port):
    """Ferme ce qui bloquerait un joueur jusqu'au clic (dialogue du jeu, question oui/non)."""
    ev(port, 'foreach (var l in EClass.ui.layers.ToList()) if (l is LayerDrama || l is Dialog) l.Close(); "ok"')


def seen(port, uid):
    """Un personnage vu par ce jeu : "x,z|vie|objets du sac|or", ou "absent"."""
    return ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); if (c == null) return "absent"; '
                    'return c.pos.x + "," + c.pos.z + "|" + c.hp + "|" + c.things.Count + "|" + c.GetCurrency("money");')


def quests(port):
    return ev(port, 'var personal = ElinTogether.Net.NetSession.Instance.Rules.UsePersonalQuests; '
                    'return string.Join(",", EClass.game.quests.list.Where(q => !personal || !q.IsRandomQuest).Select(q => q.uid).OrderBy(u => u));')


def doubles(port):
    """Numeros portes par deux objets differents dans ce jeu (au sol, dans les sacs, dans les coffres) : "" si aucun."""
    return ev(port, 'var all = EClass._map.things.Cast<Card>().Concat(EClass._map.charas.SelectMany(c => c.things.Cast<Card>())).ToList(); '
                    'var inside = all.SelectMany(c => c.things.Cast<Card>()).ToList(); all.AddRange(inside); '
                    'return string.Join(",", all.GroupBy(c => c.uid).Where(g => g.Distinct().Count() > 1).Select(g => g.Key + ":" + g.First().id).Take(8));')


def settle(read_a, read_b, timeout=8):
    """Les deux lectures finissent-elles par etre egales ? Renvoie (egal, a, b)."""
    t0 = time.time()
    while True:
        a, b = read_a(), read_b()
        if a == b or time.time() - t0 > timeout:
            return a == b, a, b
        time.sleep(1)


# verifications de suite pendant lesquelles un jeu peut etre entre deux cartes (un chargement dure 3 a 10 s)
BUSY_CHECKS = 6


class Watch:
    def __init__(self, bot, other, names):
        self.bot, self.other, self.names = bot, other, names
        self.problems = []
        self.t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        self.logs = {"journal du host": LOCALLOW / "Player.log", "journal du client": SHOTS / "elin2-player.log"}
        self.offsets = {k: (p.stat().st_size if p.exists() else 0) for k, p in self.logs.items()}
        self.mod_seen = 0
        self.busy = 0

    def problem(self, text, last):
        self.problems.append((text, last))
        say(f"  !! {text}   (derniere action : {last})")
        for port, name in ((self.bot, "bot"), (self.other, "autre")):
            try:
                say(f"     capture {name} : {shot(f'bot-{len(self.problems)}-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass

    def check(self, last):
        try:
            sb, so = state(self.bot), state(self.other)
        except OSError as ex:
            self.problem(f"un des deux jeux ne repond plus ({ex})", last)
            return False
        for s, name in ((sb, self.names[0]), (so, self.names[1])):
            if s.get("role") == "Client" and not s.get("connected"):
                self.problem(f"{name} est deconnecte", last)
                return False

        for name, path in self.logs.items():
            if not path.exists():
                continue
            with open(path, encoding="utf-8", errors="replace") as f:
                f.seek(self.offsets[name])
                new = f.read()
                self.offsets[name] = f.tell()
            exc = [l for l in new.splitlines() if "Exception" in l]
            if exc:
                self.problem(f"{name} : {len(exc)} exception(s), la premiere : {exc[0][:200]}", last)
        mod = [json.loads(l) for l in session_log_lines(self.t0)]
        mod = [d for d in mod if d.get("@l") in ("Error", "Fatal")]
        for d in mod[self.mod_seen:]:
            self.problem(f'journal du mod : {d["@l"]} {d["@mt"][:160]}', last)
        self.mod_seen = len(mod)

        # un jeu entre deux cartes (voyage, retour chez l'host) n'a pas de carte a comparer : on repasse au tour
        # suivant. Mais pas sans fin : un joueur qui reste sans carte est un vrai defaut (vu le 2026-10-02)
        try:
            self.compare(sb, so, last)
            self.busy = 0
        except RuntimeError as ex:
            self.busy += 1
            if self.busy > BUSY_CHECKS:
                self.problem(f"un jeu reste sans carte depuis {self.busy} verifications ({str(ex)[:120]})", last)
                return False
        return True

    def compare(self, sb, so, last):
        for s in (sb, so):
            if not s.get("gameStarted") or s.get("sceneMode") != "Zone" or s.get("inTransfer"):
                raise RuntimeError("en chargement")

        for port, name in ((self.bot, self.names[0]), (self.other, self.names[1])):
            twice = doubles(port)
            if twice:
                self.problem(f"objets en double chez {name} (numero:objet) : {twice}", last)

        same, a, b = settle(lambda: quests(self.bot), lambda: quests(self.other))
        if not same:
            self.problem(f"journaux de quetes differents : {self.names[0]} [{a}]  {self.names[1]} [{b}]", last)

        zb, zo = (sb.get("zone") or {}).get("uid"), (so.get("zone") or {}).get("uid")
        if zb == zo and sb.get("sceneMode") == "Zone" and so.get("sceneMode") == "Zone":
            for uid, who in ((sb["pc"]["uid"], self.names[0]), (so["pc"]["uid"], self.names[1])):
                same, a, b = settle(lambda: seen(self.bot, uid), lambda: seen(self.other, uid))
                if not same:
                    self.problem(f"{who} n'est pas vu pareil (x,z|vie|sac|or) : chez {self.names[0]} {a}, chez {self.names[1]} {b}", last)
            count = 'EClass._map.things.Count.ToString()'
            same, a, b = settle(lambda: ev(self.bot, count), lambda: ev(self.other, count))
            if not same:
                self.problem(f"objets sur la carte : {a} chez {self.names[0]}, {b} chez {self.names[1]}", last)


def main():
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=5)
    ap.add_argument("--seed", type=int, default=int(time.time()) % 100000)
    ap.add_argument("--who", choices=["client", "host"], default="client")
    ap.add_argument("--only", help="actions separees par des virgules : " + ",".join(ACTIONS))
    ap.add_argument("--every", type=int, default=4, help="verifier toutes les N actions")
    ap.add_argument("--watch", action="store_true", help="ne rien faire, seulement verifier (le bot du menu du jeu joue deja)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    live = emp.live_ports()
    host = next(h["port"] for h in live if h["role"] == "Host")
    client = next(h["port"] for h in live if h["role"] == "Client")
    bot, other = (client, host) if a.who == "client" else (host, client)
    names = ("le bot", "l'autre joueur")

    OUT = open(SHOTS / f"bot-{time.strftime('%Y%m%d-%H%M%S')}.log", "w", encoding="utf-8")
    rng = random.Random(a.seed)
    pool = {k: v for k, v in ACTIONS.items() if not a.only or k in a.only.split(",")}
    say(f"bot sur le {a.who} (port {bot}), graine {a.seed}, {a.minutes:g} min, actions : {', '.join(pool)}")

    if "voyage" not in pool and (state(bot).get("zone") or {}).get("uid") != (state(other).get("zone") or {}).get("uid"):
        dest = (state(other).get("zone") or {}).get("uid")
        say("sans voyage : le bot rejoint d'abord l'autre joueur")
        ev(bot, f'{PC}.MoveZone(EClass.game.spatials.Find({dest})); "ok"')
        t0 = time.time()
        while (state(bot).get("zone") or {}).get("uid") != dest or not state(bot).get("connected"):
            if time.time() - t0 > 120:
                sys.exit("le bot n'a pas rejoint l'autre joueur")
            time.sleep(1)
        time.sleep(4)

    a_compagnon.ctx = a_reconnecte.ctx = {"who": a.who, "host": host, "allies": 0}
    if not a.watch:
        say(f"materiel donne au bot : {give_kit(host, state(bot)['pc']['uid'])}")
        time.sleep(2)

    watch = Watch(bot, other, names)
    if a.watch:
        say("surveillance seule : c'est le bot lance depuis le menu du jeu qui joue")
        end, n = time.time() + a.minutes * 60, 0
        while time.time() < end:
            time.sleep(8)
            n += 1
            if not watch.check(f"verification {n}"):
                break
        say(f"{n} verifications, {len(watch.problems)} probleme(s)")
        for text, at in watch.problems:
            say(f"  - {text}   ({at})")
        sys.exit(1 if watch.problems else 0)

    done, skipped = {}, {}
    end = time.time() + a.minutes * 60
    n, last = 0, "aucune"
    while time.time() < end:
        n += 1
        name = rng.choices(list(pool), weights=[w for _, w in pool.values()])[0]
        try:
            # comme un joueur : pas d'action pendant que son personnage change de mains
            waited = time.time()
            while state(bot).get("inTransfer") and time.time() - waited < 40:
                time.sleep(0.5)
            if ev(bot, "EClass.pc.isDead.ToString()") == "True":
                name = "mort"
                result = die_and_return(bot, rng)
            else:
                close_dialogs(bot)
                result = pool[name][0](bot, rng)
            done[name] = done.get(name, 0) + 1
        except Problem as ex:
            watch.problem(str(ex), name)
            break
        except Exception as ex:  # noqa: BLE001
            result = f"action impossible : {type(ex).__name__}: {str(ex)[:160]}"
            skipped[name] = skipped.get(name, 0) + 1
        last = f"{n} {name} : {result}"
        say(last)
        time.sleep(rng.uniform(0.3, 1.5))
        if n % a.every == 0 and not watch.check(last):
            break
    else:
        watch.check(last)

    say("")
    say(f"{n} actions : " + ", ".join(f"{k} {v}" for k, v in sorted(done.items())))
    if skipped:
        say("actions impossibles (a corriger dans le bot, pas forcement dans le mod) : " + ", ".join(f"{k} {v}" for k, v in skipped.items()))
    say(f"{len(watch.problems)} probleme(s)")
    for text, at in watch.problems:
        say(f"  - {text}\n      apres : {at}")
    say(f"pour rejouer la meme suite : python _tools/bot.py --seed {a.seed} --who {a.who}")
    sys.exit(1 if watch.problems else 0)


if __name__ == "__main__":
    main()
