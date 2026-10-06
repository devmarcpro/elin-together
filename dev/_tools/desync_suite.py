"""Desynchronisations D1, D4, D5 de dev/PLAN_desync.md (corrections : dev/PLAN_desync_corrections.md). JAMAIS LANCE.

TROIS FENETRES par defaut : a ne lancer qu'avec l'accord de l'utilisateur (regle du Steam Deck : deux fenetres Elin
au plus). `--two` joue la meme chose a deux fenetres (host + A), sans le temoin.

    python _tools/desync_suite.py                  # relance tout (mp_test --clients 2) puis les scenarios
    python _tools/desync_suite.py --reuse          # sur host + 2 clients deja connectes dans la Prairie
    python _tools/desync_suite.py --reuse --two    # sur host + 1 client (mp_test.py)
    python _tools/desync_suite.py --reuse --only d1a,d5a [--slow]

A trois : A agit, B part et revient, l'host regarde. A deux : l'host agit, A part et revient.
Apres chaque scenario, `world_diff.diff` compare dans TOUS les jeux les personnages de la carte (uid, case, vie),
les objets au sol (uid, case, quantite), le sac et l'equipement de chaque joueur et compagnon : aucun ecart attendu.

D1a un joueur part seul a Vernis puis REVIENT ; pendant tout son retour (copie du monde, copie de la carte,
    chargement) l'autre joueur fait des gestes en continu : il marche sur un seau (il le ramasse), pose un seau,
    met puis retire un casque, blesse un monstre. Attendu sur la 0.26.510 : rouge (le sac et l'equipement de celui
    qui agit ne sont pas les memes chez celui qui revient). `--slow` : le jeu de celui qui revient tourne a
    5 images par seconde pendant le retour, pour elargir le trou.
D1b le meme joueur quitte la partie et la REJOINT (emp.disconnect puis emp.connect_udp), memes gestes, meme comparaison.
D4  l'invite recharge la carte ou il est (la copie de la carte lui est renvoyee, son jeu tourne) pendant que l'host
    agit : memes gestes, plus une rafale de seaux poses par l'host juste apres chaque demande. Chaque seau de la
    rafale est au sol dans tous les jeux, et aucun ecart. Attendu sur la 0.26.510 : rouge de temps en temps (le trou
    dure un aller-retour reseau).
D5a un seau au sol que l'host a bien mais que son registre des cartes ne connait plus : l'invite marche dessus.
    Attendu : il est dans le sac de l'invite dans tous les jeux, et le journal de l'host dit « adopted and replayed ».
    Sur la 0.26.510 : il reste au sol chez l'host et disparait chez tous les invites.
D5b un seau que l'host n'a plus mais que les invites voient encore (un fantome) : l'invite A marche dessus.
    Attendu : l'host refuse et ne le dit qu'a A (le seau quitte son jeu) ; chez B il est toujours au sol (a trois
    fenetres seulement). Sur la 0.26.510 : il disparait aussi chez B.

Ce que le banc ne joue pas comme un joueur :
- les seaux, le casque et le monstre sont crees par l'host (eval), pas trouves en jouant ;
- la marche est un AI_Goto vers la case (le deplacement d'un clic), pas une touche enfoncee ; le seau est ramasse
  par cette marche, comme en jeu ;
- poser passe par `Chara.DropThing` (la fonction derriere « poser »), mettre et retirer le casque par
  `body.Equip` / `body.Unequip`, le coup par `ACT.Melee.Perform` : pas par les fenetres du sac ni par un clic ;
- le depart et le retour sont des `pc.MoveZone(carte)`, pas une sortie a pied par le bord ;
- D4 : le rechargement est demande par `RequestZoneState` (ce que fait le mod quand une copie de carte echoue, et
  ce que fera l'outil de resynchronisation) ; le cas « l'host change de carte et l'invite le suit sans recharger
  le monde » (voyage independant decoche, carte de quete) n'est pas joue ; la rafale de seaux est creee par eval ;
- D5a : le registre de l'host est vide a la main (`CardCache.Remove`), on ne sait pas provoquer cet oubli en jouant ;
- D5b : le fantome est fabrique en coupant une seconde les envois de l'host pendant qu'il detruit le seau
  (`PauseWorldStateUpdate` / `ResumeWorldStateUpdate(true)`) : tout autre message de cette seconde est perdu aussi,
  a ne faire que sur une carte calme ;
- pas joue : un compagnon qui agit pendant le trou, un echange entre joueurs pendant le trou, deux retours en meme
  temps, un retour pendant que l'host change de carte, une deconnexion au milieu du trou, une session de zone
  (carte tenue par un invite) dans le role de l'host.
"""
import argparse
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from guest_suite import chara, free_next_to  # noqa: E402
from mp_test import ROOT, log, ok, shot, state  # noqa: E402
from pickup_suite import put, walk_onto, where  # noqa: E402
from shared_suite import settled, with_host  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, check, ev, eventually, move, scan_logs, session_log_lines,  # noqa: E402
                          wait, zone_uid)
from world_diff import diff  # noqa: E402

H, A, B = 27551, 27552, 27553
NAMES = {H: "host", A: "A", B: "B"}
ITEM, GEAR, FOE = "bucket", "helm_knight", "putty"
SETTLE = 8  # secondes laissees aux jeux pour se repondre avant de comparer

SLOW = ('var old = UnityEngine.Application.targetFrameRate + "," + UnityEngine.QualitySettings.vSyncCount; '
        'UnityEngine.QualitySettings.vSyncCount = 0; UnityEngine.Application.targetFrameRate = 5; return old;')
NET = 'var net = ElinTogether.Net.NetSession.Instance.Connection; '
RELOAD = (NET + 'HarmonyLib.AccessTools.Method(net.GetType(), "RequestZoneState")'
          '.Invoke(net, new object[] { ElinTogether.Models.MapDataRequest.CurrentRemoteZone }); return "ok";')


def pc_uid(port):
    return state(port)["pc"]["uid"]


def logged(t0, *texts):
    """Une ligne du journal du mod, depuis t0, contient tous ces textes."""
    return any(all(t in line for t in texts) for line in session_log_lines(t0))


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def compare(ctx, what):
    gaps = diff(ctx["ports"], NAMES)
    check(f"{what} : aucun ecart entre {', '.join(NAMES[p] for p in ctx['ports'])} ({len(gaps)} ecart(s))", not gaps)
    for line in gaps[:25]:
        print("        ", line)
    return not gaps


# ---------------------------------------------------------------------------------------------------- gestes

def give(uid, thing_id):
    """L'host met un objet dans le sac de ce personnage ; renvoie son numero."""
    return int(ev(H, f'var c = {chara(H, uid)}; var t = ThingGen.Create("{thing_id}"); t.SetBlessedState(BlessedState.Normal); '
                     'return c.AddThing(t, false).uid.ToString();'))


def spawn_foe(uid):
    """L'host fait apparaitre un monstre a cote de ce personnage ; renvoie son numero (0 : pas de place)."""
    spot = free_next_to(H, uid) or free_next_to(H, uid, 2)
    if not spot:
        return 0
    x, z = spot.split(",")
    return int(ev(H, f'var m = CharaGen.Create("{FOE}"); EClass._zone.AddCard(m, new Point({x}, {z})); return m.uid.ToString();'))


def walk_pick(port, uid, kit):
    """Il marche sur un seau pose a cote de lui : la marche le ramasse."""
    made = put(H, uid, stack=False)
    if not made or not eventually(lambda: where(port, uid, made[0]).startswith("sol"), timeout=8):
        return False
    return walk_onto(port, uid, made[1], made[2])


def drop(port, uid, kit):
    """Il pose un seau de son sac a ses pieds."""
    return ev(port, f'var t = EClass.pc.things.Find(x => x.id == "{ITEM}"); if (t == null) return "rien"; '
                    'EClass.pc.DropThing(t); return "ok";') == "ok"


def equip(port, uid, kit):
    """Il met le casque, ou le retire s'il le porte."""
    return ev(port, f'var t = EClass.pc.things.Find({kit["gear"]}); if (t == null) return "rien"; '
                    'if (t.isEquipped) EClass.pc.body.Unequip(t); else EClass.pc.body.Equip(t); return "ok";') == "ok"


def hurt(port, uid, kit):
    """Il va au contact du monstre et le frappe ; mort ou disparu, l'host en remet un."""
    said = ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {kit["foe"]}); if (m == null || m.isDead) return "parti"; '
                    'if (EClass.pc.Dist(m) > 1) { EClass.pc.SetAIImmediate(new AI_Goto(m.pos.Copy(), 1)); return "loin"; } '
                    'ACT.Melee.Perform(EClass.pc, m, m.pos); return "ok";')
    if said == "parti":
        kit["foe"] = spawn_foe(uid)
    elif said == "loin":
        time.sleep(1.5)
    return said == "ok"


GESTURES = (("marche et ramasse", walk_pick), ("pose", drop), ("equipe", equip), ("blesse", hurt))


class Actor:
    """Un joueur qui fait les gestes en boucle, dans un fil a part, jusqu'a `stop()`."""

    def __init__(self, port):
        self.port, self.uid = port, pc_uid(port)
        self.kit = {"gear": give(self.uid, GEAR), "foe": spawn_foe(self.uid)}
        self.done, self.failed = [], []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            for name, act in GESTURES:
                if self._stop.is_set():
                    break
                try:
                    (self.done if act(self.port, self.uid, self.kit) else self.failed).append((time.time(), name))
                except Exception as ex:  # noqa: BLE001
                    self.failed.append((time.time(), f"{name} : {type(ex).__name__}: {str(ex)[:120]}"))
                time.sleep(0.3)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=60)
        try:
            ev(self.port, 'EClass.pc.SetNoGoal(); return "ok";')
        except Exception:  # noqa: BLE001
            pass

    def between(self, t0, t1):
        """Gestes reussis entre ces deux instants : {nom: nombre}."""
        out = {}
        for t, name in self.done:
            if t0 <= t <= t1:
                out[name] = out.get(name, 0) + 1
        return out


def acted(actor, t0, t1, what):
    did = actor.between(t0, t1)
    check(f"{what} : {NAMES[actor.port]} a agi pendant ce temps ({round(t1 - t0, 1)} s : {did or 'rien'})", sum(did.values()) >= 2)
    if actor.failed:
        print(f"        gestes rates : {len(actor.failed)}, par exemple {actor.failed[-1][1]}")


# ------------------------------------------------------------------------------------------------- scenarios

def comes_back(ctx, what, leave, back, hold_line):
    """`leave` puis `back` pour celui qui bouge, pendant que l'autre agit ; puis la comparaison."""
    actor_port, mover = ctx["actor"], ctx["mover"]
    t_log = now_utc()
    leave()
    actor = Actor(actor_port).start()
    restore = None
    try:
        time.sleep(4)
        if ctx["slow"]:
            fps, vsync = ev(mover, SLOW).split(",")
            restore = f'UnityEngine.QualitySettings.vSyncCount = {vsync}; UnityEngine.Application.targetFrameRate = {fps}; return "ok";'
        t0 = time.time()
        back()
        t1 = time.time()
        time.sleep(3)
    finally:
        actor.stop()
        if restore:
            try:
                ev(mover, restore)
            except Exception:  # noqa: BLE001
                pass
    acted(actor, t0, t1, what)
    time.sleep(SETTLE)
    check(f"{what} : le journal de {NAMES[mover]} dit ce qui a ete retenu puis rejoue depuis la copie du monde",
          logged(t_log, hold_line, "world copy"))
    compare(ctx, what)


def d1a(ctx):
    """un joueur revient d'un voyage pendant que l'autre agit : memes personnages, objets, sacs et equipements partout"""
    mover = ctx["mover"]

    def leave():
        move(mover, VERNIS)
        wait(settled(mover, VERNIS, away=True), f"{NAMES[mover]} seul a Vernis", timeout=240)

    def back():
        move(mover, HOME)
        wait(settled(mover, HOME, away=False), f"{NAMES[mover]} de retour chez l'host", timeout=300)

    comes_back(ctx, f"retour de voyage de {NAMES[mover]}", leave, back, "Replaying {Held} held deltas")


def d1b(ctx):
    """un joueur quitte la partie et la rejoint pendant que l'autre agit : meme comparaison"""
    mover = ctx["mover"]

    def leave():
        ok(emp.call(mover, "command", {"cmd": "emp.disconnect"}))
        wait(lambda: not state(mover).get("connected"), f"{NAMES[mover]} hors de la partie", timeout=60)
        time.sleep(3)

    def back():
        ok(emp.call(mover, "command", {"cmd": "emp.connect_udp"}))
        wait(settled(mover, HOME, away=False), f"{NAMES[mover]} de nouveau chez l'host", timeout=300)

    comes_back(ctx, f"{NAMES[mover]} rejoint la partie", leave, back, "Replaying {Held} held deltas")


def d4(ctx):
    """l'invite recharge la carte pendant que l'host agit : rien de ce que fait l'host n'est perdu"""
    guest = A
    t_log = now_utc()
    actor = Actor(H).start()
    burst = []
    restore = None
    try:
        time.sleep(3)
        if ctx["slow"]:
            fps, vsync = ev(guest, SLOW).split(",")
            restore = f'UnityEngine.QualitySettings.vSyncCount = {vsync}; UnityEngine.Application.targetFrameRate = {fps}; return "ok";'
        t0 = time.time()
        for _ in range(4):
            ev(guest, RELOAD)
            # the host puts buckets down right behind the request: some land between its copy and the reload
            for _ in range(6):
                burst.append(int(ev(H, f'var t = ThingGen.Create("{ITEM}"); t.ignoreAutoPick = true; '
                                       'EClass._zone.AddCard(t, EClass.pc.pos.GetNearestPoint(allowChara: false) ?? EClass.pc.pos); '
                                       'return t.uid.ToString();')))
                time.sleep(0.1)
            time.sleep(4)
        t1 = time.time()
    finally:
        actor.stop()
        if restore:
            try:
                ev(guest, restore)
            except Exception:  # noqa: BLE001
                pass
    wait(settled(guest, HOME, away=False), "l'invite sur la carte", timeout=120)
    acted(actor, t0, t1, "rechargements de la carte")
    time.sleep(SETTLE)
    check("le journal de l'invite dit ce qui a ete retenu puis rejoue (carte recue pendant que son jeu tournait)",
          logged(t_log, "Replaying {Held} held deltas", "map copy, game running"))
    check("aucun rechargement n'a attendu en vain sa place sur la carte",
          not logged(t_log, "No placement on the incoming map"))
    for p in ctx["ports"]:
        seen = ev(p, 'var ids = new[] {' + ",".join(map(str, burst)) + '}; '
                     'return EClass._map.things.Count(t => ids.Contains(t.uid)).ToString();')
        check(f"{NAMES[p]} voit au sol les {len(burst)} seaux poses par l'host pendant les rechargements ({seen})",
              int(seen) == len(burst))
    compare(ctx, "apres les rechargements")


def bucket_next_to(ctx, uid):
    """Un seau pose par l'host a cote de ce joueur, vu au sol dans tous les jeux : (numero, x, z) ou None."""
    made = put(H, uid, stack=False)
    seen = made and eventually(lambda: all(where(p, uid, made[0]).startswith("sol") for p in ctx["ports"]), timeout=15)
    return made if check(f"mise en place : un seau au sol a cote de A, vu par tous ({made})", seen) else None


def d5a(ctx):
    """un objet que l'host a mais que son registre a oublie, ramasse par l'invite : il l'obtient, comme en solo"""
    uid = pc_uid(A)
    made = bucket_next_to(ctx, uid)
    if not made:
        return
    thing, x, z = made
    t_log = now_utc()
    ev(H, f'HarmonyLib.AccessTools.Method(typeof(ElinTogether.Models.CardCache), "Remove").Invoke(null, new object[] {{ {thing} }}); return "ok";')
    if not check(f"A marche sur le seau ({x},{z})", walk_onto(A, uid, x, z)):
        return
    time.sleep(SETTLE)
    seen = {NAMES[p]: where(p, uid, thing) for p in ctx["ports"]}
    check(f"le seau est dans le sac de A dans tous les jeux, comme en solo ({seen})", all(v == "sac" for v in seen.values()))
    check("le journal de l'host dit qu'il a retrouve l'objet (« adopted and replayed »)",
          logged(t_log, "adopted and replayed"))
    compare(ctx, "apres le ramassage")
    ev(H, f'var c = {chara(H, uid)}; var t = c == null ? null : c.things.Find({thing}); if (t != null) t.Destroy(); return "ok";')


def d5b(ctx):
    """un objet que l'host n'a plus, touche par l'invite : seul cet invite le perd, il ne disparait pas chez les autres"""
    uid = pc_uid(A)
    made = bucket_next_to(ctx, uid)
    if not made:
        return
    thing, x, z = made
    t_log = now_utc()
    ev(H, NET + 'HarmonyLib.AccessTools.Method(net.GetType(), "PauseWorldStateUpdate").Invoke(net, null); '
              f'EClass._map.things.Find(t => t.uid == {thing}).Destroy(); return "ok";')
    time.sleep(1)
    ev(H, NET + 'HarmonyLib.AccessTools.Method(net.GetType(), "ResumeWorldStateUpdate").Invoke(net, new object[] { true }); return "ok";')
    time.sleep(2)
    seen = {NAMES[p]: where(p, uid, thing) for p in ctx["ports"]}
    if not check(f"mise en place : l'host n'a plus le seau, les invites le voient encore ({seen})",
                 seen["host"] == "nulle part" and all(v.startswith("sol") for k, v in seen.items() if k != "host")):
        return
    try:
        if not check(f"A marche sur le seau fantome ({x},{z})", walk_onto(A, uid, x, z)):
            return
        time.sleep(SETTLE)
        seen = {NAMES[p]: where(p, uid, thing) for p in ctx["ports"]}
        check("le journal de l'host dit qu'il refuse et ne le dit qu'a ce joueur (« Refusing stale … only that player is told »)",
              logged(t_log, "Refusing stale", "only that player is told"))
        check(f"A, qui s'est trompe, n'a plus le seau, ni au sol ni dans son sac ({seen['A']})", seen["A"] == "nulle part")
        check(f"l'host n'a toujours pas le seau ({seen['host']})", seen["host"] == "nulle part")
        if B in ctx["ports"]:
            check(f"chez B, qui n'a rien touche, le seau n'a pas disparu ({seen['B']})", seen["B"] == f"sol@{x},{z}")
    finally:
        # the ghost left in the games that were not told: each one drops its own
        for p in ctx["ports"]:
            ev(p, f'var t = EClass._map.things.Find(m => m.uid == {thing}); if (t != null) t.Destroy(); return "ok";')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--two", action="store_true", help="deux fenetres : l'host agit, A part et revient")
    ap.add_argument("--slow", action="store_true", help="5 images par seconde chez celui qui charge, pour elargir le trou")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = now_utc()

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py"), *([] if a.two else ["--clients", "2"])], check=True)

    ports = [H, A] if a.two else [H, A, B]
    ctx = {"ports": ports, "actor": H if a.two else A, "mover": A if a.two else B, "slow": a.slow}
    if not check(f"tous sur la meme carte ({[zone_uid(p) for p in ports]})", len({zone_uid(p) for p in ports}) == 1):
        sys.exit(1)
    compare(ctx, "au depart")

    steps = [d1a, d1b, d4, d5a, d5b]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for p in ports:
            try:
                print(f"    capture {NAMES[p]} : {shot(f'desync-{step.__name__}-{NAMES[p]}', p)}")
            except Exception:  # noqa: BLE001
                pass
        try:
            with_host(*ports[1:])
        except Exception as ex:  # noqa: BLE001
            print(f"    retour chez l'host rate : {type(ex).__name__}: {ex}")

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
