"""Pose d'objets et changements de la carte. Test court, sur des instances deja lancees (host + 1 client).

    python _tools/mp_test.py
    python _tools/build_suite.py        # ~1 minute, tout le monde reste a la Prairie

Retours de joueurs du mod d'origine (Workshop, depot), voir PLAN_retours_joueurs.md :
B1  l'host pose un objet en mode construction : le client le voit pose, pas "au sol" (il pouvait le ramasser)
B2  le client pose deux objets tenus, pris d'une pile de deux : poses des deux cotes, rien au sol (ticket 9)
B4  l'host pose un objet tenu en main : le client le voit pose
B5  meme chose quand le jeu du client ne peut pas rejouer la pose (son image du sac de l'host n'est plus a
    jour) : c'est le cas ou le client voyait l'objet "au sol" et pouvait le ramasser
B3  un monstre casse un mur chez l'host : le mur disparait aussi chez le client
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552

# case libre a cote du joueur local, ni mur ni objet ni personnage
SPOT = ('var spot = EClass._map.ListPointsInCircle(EClass.pc.pos, 3f, false, true)'
        '.Where(q => q.Distance(EClass.pc.pos) == 1 && !q.HasBlock && !q.HasObj && !q.HasChara && q.Things.Count == 0)'
        '.FirstOrDefault(); if (spot == null) return "pas de case libre"; ')


def placed(port, uid):
    """Un objet vu par ce jeu : "etat|x,z|nombre", "absent" s'il n'est pas sur la carte."""
    return ev(port, f'var t = EClass._map.things.Find(x => x.uid == {uid}); '
                    'return t == null ? "absent" : t.placeState + "|" + t.pos.x + "," + t.pos.z + "|" + t.Num;')


def b1(ctx):
    """l'host pose un objet en mode construction (rien en main, c'est l'agent de construction qui pose)"""
    r = ev(H, SPOT + 'var t = ThingGen.Create("chest6"); EClass.pc.AddThing(t); '
              'var k = new TaskBuild { recipe = Recipe.Create(t), pos = spot.Copy(), owner = EClass.player.Agent }; '
              'k.OnProgressComplete(); return t.uid + "|" + spot.x + "," + spot.z;')
    uid, pos = r.split("|")
    log(f"coffre {uid} pose par l'host en {pos}")
    check(f"host : le coffre est pose ({placed(H, uid)})", placed(H, uid) == f"installed|{pos}|1")
    check("client : il le voit pose au meme endroit, pas au sol",
          eventually(lambda: placed(A, uid) == f"installed|{pos}|1", timeout=10))
    log(f"vu du client : {placed(A, uid)}")


# comme un joueur : l'objet (ou la pile) en main, puis la pose sur une case voisine (ce que fait HotItemHeld)
BUILD_HELD = ('var thing = EClass.pc.things.Find(t => t.id == "__ID__" && !t.isEquipped); if (thing == null) return "plus rien a poser"; '
              + SPOT +
              'EClass.pc.HoldCard(thing); var recipe = EClass.pc.held.trait.GetRecipe(); if (recipe == null) return "pas posable"; '
              'var task = new TaskBuild { recipe = recipe, held = EClass.pc.held, pos = spot.Copy() }; '
              'var build = ActionMode.Build; build.bridgeHeight = -1; build.recipe = recipe; build.mold = task; '
              'EClass.pc.SetAI(task); return spot.x + "," + spot.z;')


# l'host : la fin de la pose tout de suite. Sans clic de son joueur le monde de l'host est en pause, une tache
# donnee par le pont n'y avancerait pas
BUILD_HELD_NOW = (BUILD_HELD.replace('var task = new TaskBuild {', 'var task = new TaskBuild { owner = EClass.pc,')
                  .replace('EClass.pc.SetAI(task);', 'task.OnProgressComplete();'))


def at(port, thing_id, pos):
    """Objets de ce type sur cette case, vus par ce jeu : "etat,etat" (vide s'il n'y en a pas)."""
    x, z = pos.split(",")
    return ev(port, f'string.Join(",", EClass._map.things.Where(t => t.id == "{thing_id}" && t.pos.x == {x} && t.pos.z == {z})'
                    '.Select(t => t.placeState.ToString()))')


def in_bag(port, chara, thing_id):
    return int(ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {chara}); '
                        f'return c.things.Where(t => t.id == "{thing_id}").Sum(t => t.Num).ToString();'))


def place_held(ctx, who, port, other, thing_id, count):
    """Le joueur de ce jeu recoit `count` objets et les pose un par un ; verifie des deux cotes."""
    me = state(port)["pc"]["uid"]
    had = in_bag(port, me, thing_id)
    if had:
        ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); '
              f'foreach (var t in c.things.Where(t => t.id == "{thing_id}").ToList()) t.Destroy(); "ok"')
        eventually(lambda: in_bag(port, me, thing_id) == 0, timeout=10)
    ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var t = ThingGen.Create("{thing_id}"); t.SetNum({count}); '
          'c.AddThing(t); "ok"')
    check(f"{who} a {count} {thing_id} dans son sac", eventually(lambda: in_bag(port, me, thing_id) == count, timeout=10))
    for n in range(1, count + 1):
        pos = ev(port, (BUILD_HELD_NOW if port == H else BUILD_HELD).replace("__ID__", thing_id))
        if "," not in pos:
            check(f"pose {n} par {who} : {pos}", False)
            return
        ok = eventually(lambda: at(port, thing_id, pos) == "installed" and at(other, thing_id, pos) == "installed", timeout=20)
        check(f"pose {n} par {who} en {pos} : pose des deux cotes (chez lui [{at(port, thing_id, pos)}], chez l'autre [{at(other, thing_id, pos)}])", ok)
        time.sleep(1)
    check(f"il ne reste rien dans le sac de {who}, vu des deux cotes",
          eventually(lambda: in_bag(port, me, thing_id) == 0 and in_bag(other, me, thing_id) == 0, timeout=10))
    loose = f'EClass._map.things.Count(t => t.id == "{thing_id}" && t.placeState != PlaceState.installed).ToString()'
    check("rien au sol, ni chez l'un ni chez l'autre", ev(port, loose) == "0" and ev(other, loose) == "0")


def b2(ctx):
    """le client pose deux objets tenus pris d'une pile de deux (la pile passe a un, puis disparait)"""
    place_held(ctx, "le client", A, H, "torch", 2)


def b4(ctx):
    """l'host pose un objet tenu en main : le client le voit pose, pas au sol"""
    place_held(ctx, "l'host", H, A, "chest6", 1)


def b5(ctx):
    """l'host pose un objet tenu que le jeu du client ne lui connait plus en main : pose quand meme"""
    host = state(H)["pc"]["uid"]
    ev(H, 'var t = ThingGen.Create("chest6"); EClass.pc.AddThing(t); "ok"')
    check("le client voit le coffre dans le sac de l'host", eventually(lambda: in_bag(A, host, "chest6") == 1, timeout=10))
    # chez le client seulement : le coffre sort du sac de l'host sans que rien ne soit envoye, comme un sac qui
    # n'est plus a jour. La pose rejouee chez le client s'arrete alors avant d'installer ("Refusing stale")
    ev(A, f'var h = EClass._map.charas.Find(x => x.uid == {host}); var t = h.things.Find(x => x.id == "chest6"); '
          'h.things.Remove(t); t.parent = null; "ok"')
    pos = ev(H, BUILD_HELD_NOW.replace("__ID__", "chest6"))
    check(f"l'host pose le coffre en {pos}", eventually(lambda: at(H, "chest6", pos) == "installed", timeout=20))
    seen = eventually(lambda: at(A, "chest6", pos) == "installed", timeout=10)
    check(f"client : le coffre est pose, pas au sol (vu : [{at(A, 'chest6', pos)}])", seen)


def b3(ctx):
    """un monstre casse un mur chez l'host (boss de donjon) : le mur disparait aussi chez le client"""
    me = state(A)["pc"]["uid"]
    # a trois cases : les cases voisines des joueurs servent aux poses des autres etapes
    pos = ev(H, SPOT.replace("3f", "6f").replace("== 1", "== 3") + 'return spot.x + "," + spot.z;')
    x, z = pos.split(",")
    has_wall = f'new Point({x}, {z}).HasBlock.ToString()'
    # le terrain n'est pas synchronise par le mod : le meme mur est monte des deux cotes
    for port in (H, A):
        ev(port, f'EClass._map.SetBlock({x}, {z}, 3, 1); "ok"')
    check(f"un mur est monte en {pos} des deux cotes", ev(H, has_wall) == "True" and ev(A, has_wall) == "True")
    who = ev(H, f'var c = EClass._map.charas.Find(q => !q.IsPC && q.uid != {me} && !q.isDead); '
                f'c.DestroyPath(new Point({x}, {z})); return c.uid + " " + c.id;')
    log(f"mur casse chez l'host par {who}")
    check("host : le mur est casse", ev(H, has_wall) == "False")
    check("client : le mur est casse aussi", eventually(lambda: ev(A, has_wall) == "False", timeout=10))
    ev(A, f'if (new Point({x}, {z}).HasBlock) EClass._map.SetBlock({x}, {z}, 0, 0); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {}
    steps = [b1, b2, b4, b5, b3]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
            for name, port in (("host", H), ("A", A)):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', port)}")
                except Exception:  # noqa: BLE001
                    pass

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
