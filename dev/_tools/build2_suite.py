"""Mode construction a deux (PLAN_construction_invite.md, conseil 5). Test court, sur des instances deja lancees
(host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/build2_suite.py            # ou --only g1,c3

G1  garde-fou (etape 1 du conseil) : l'invite clique un sol puis un mur a miner en mode construction : rien n'est
    paye, rien ne change, ni chez lui ni chez l'host. A retirer geste par geste quand C1 et C2 passent.
C3  l'host pose un sol en mode construction (ligne 4) : l'invite le voit sans rentrer dans la zone.
C1  (cible, seulement avec --only) l'invite pose un sol : pose chez les deux, 10 or et les matieres une fois.
C2  (cible, seulement avec --only) l'invite mine un mur : tombe chez les deux, 10 or une fois.

Ce que le banc ne joue pas comme un joueur : le mode et la recette sont choisis par l'appel que fait le bouton du menu
(StartBuild, Activate), la souris est posee par Scene.HitPoint ; le clic lui-meme est celui du jeu (TryProcessTiles).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import chara, count, give  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552

FLOOR = ('RecipeManager.BuildList(); '
         'var src = RecipeManager.list.FirstOrDefault(r => r.type == "Floor" && !r.isBridge && r.row.factory.IsEmpty() && !r.noListing); '
         'if (src == null) return "pas de recette de sol"; var recipe = Recipe.Create(src); recipe.BuildIngredientList(); ')


def spot(uid):
    """une case libre a 2 cases du joueur (vue de l'host), sans objet ni mur"""
    return ev(H, f'var p = {chara(H, uid)}.pos; var s = EClass._map.ListPointsInCircle(p, 4f, false, true)'
                 '.Where(q => q.Distance(p) >= 2 && !q.HasBlock && !q.HasObj && !q.HasChara && q.Things.Count == 0 '
                 '&& q.IsInBounds && !q.cell.IsTopWater).FirstOrDefault(); return s == null ? "" : s.x + "," + s.z;').split(",")


def floor_at(port, x, z):
    return ev(port, f'var c = new Point({x}, {z}).cell; return c._floor + "/" + c._floorMat;')


def block_at(port, x, z):
    return ev(port, f'new Point({x}, {z}).HasBlock.ToString()')


def gold(port, uid):
    return int(ev(port, f'{chara(port, uid)}.GetCurrency().ToString()'))


def click(port, x, z, mode_code):
    """activer le mode, attendre, puis un clic (deux eval : EInput.skipFrame)"""
    ev(port, mode_code)
    time.sleep(1.2)
    return ev(port, f'Scene.HitPoint.Set({x}, {z}); var sel = EClass.screen.tileSelector; sel.start = Scene.HitPoint.Copy(); '
                    'sel.RefreshSummary(); var ok = EClass.scene.actionMode.CanProcessTiles(); var n = sel.summary.countValid; '
                    'var m = sel.summary.money; if (ok) sel.TryProcessTiles(Scene.HitPoint.Copy()); '
                    'return ok + "|" + n + "|" + m;')


def leave(port):
    ev(port, 'ActionMode.DefaultMode.Activate(false); "ok"')


def floor_click(ctx, key, x, z):
    """le joueur recoit de quoi poser un sol, ouvre la recette et clique la case ; rend (id de la matiere, quantite, resultat du clic)"""
    port, uid = ctx[key]
    ing_id, req = ev(port, FLOOR + 'return recipe.ingredients[0].id + "," + recipe.ingredients[0].req;').split(",")
    mats = give(ctx, key, ing_id, 10)
    ev(H, f'{chara(H, uid)}.ModCurrency(500); "ok"')
    time.sleep(3)
    r = click(port, x, z, FLOOR + f'var t = EClass.pc.things.Find(q => q.uid == {mats}); recipe.ingredients[0].SetThing(t); '
                          'ActionMode.Build.StartBuild(recipe, () => null); "ok"')
    return ing_id, int(req), r


def restore_floor(x, z, before):
    fid, fmat = before.split("/")
    for p in (H, A):
        ev(p, f'EClass._map.SetFloor({x}, {z}, {fmat}, {fid}); "ok"')


def wall(x, z, up):
    for p in (H, A):  # le terrain n'est pas encore synchronise : le meme mur des deux cotes
        ev(p, f'EClass._map.SetBlock({x}, {z}, 3, 1); new Point({x}, {z}).cell.isSeen = true; "ok"' if up else
              f'if (new Point({x}, {z}).HasBlock) EClass._map.SetBlock({x}, {z}, 0, 0); "ok"')


def g1(ctx):
    """garde-fou : l'invite clique un sol puis un mur a miner : rien de paye, rien de change, nulle part"""
    port, uid = ctx["a"]
    x, z = spot(uid)
    before = floor_at(H, x, z)
    ing_id = ""
    try:
        g0 = gold(H, uid) + 500
        ing_id, req, r = floor_click(ctx, "a", x, z)
        log(f"invite clique un sol en {x},{z} : {r}")
        time.sleep(4)
        check(f"sol : rien n'est pose, ni chez l'host ni chez l'invite ({before} / {floor_at(H, x, z)} / {floor_at(port, x, z)})",
              floor_at(H, x, z) == before and floor_at(port, x, z) == before)
        check(f"sol : les matieres de l'invite sont intactes ({count(H, uid, ing_id)}, chez lui {count(port, uid, ing_id)})",
              count(H, uid, ing_id) == 10 == count(port, uid, ing_id))
        check(f"sol : aucun or n'est parti ({g0} -> {gold(H, uid)}, chez lui {gold(port, uid)})", gold(H, uid) == g0 == gold(port, uid))
    finally:
        leave(port)
        restore_floor(x, z, before)
        ev(H, f'var c = {chara(H, uid)}; foreach (var k in c.things.Where(t => t.id == "{ing_id}").ToList()) k.Destroy(); "ok"')
    wall(x, z, True)
    try:
        time.sleep(2)
        g1_ = gold(H, uid)
        r = click(port, x, z, 'ActionMode.Mine.Activate(false); "ok"')
        log(f"invite mine {x},{z} : {r}")
        time.sleep(4)
        check(f"mur : il tient chez l'host et chez l'invite ({block_at(H, x, z)} / {block_at(port, x, z)})",
              block_at(H, x, z) == "True" and block_at(port, x, z) == "True")
        check(f"mur : aucun or n'est parti (avant {g1_}, apres {gold(H, uid)}, chez lui {gold(port, uid)})",
              gold(H, uid) == g1_ == gold(port, uid))
    finally:
        leave(port)
        wall(x, z, False)


def c1(ctx):
    """l'invite pose un sol en mode construction : pose chez les deux, l'or et les matieres partent une fois"""
    port, uid = ctx["a"]
    x, z = spot(uid)
    before = floor_at(H, x, z)
    g0 = gold(H, uid) + 500
    try:
        ing_id, req, r = floor_click(ctx, "a", x, z)
        log(f"invite clique en {x},{z} : {r}")
        check(f"le clic est accepte par le jeu ({r})", r.startswith("True|1|"))
        check(cond=eventually(lambda: floor_at(H, x, z) != before, timeout=15), label=f"host : le sol de l'invite est pose ({before} -> {floor_at(H, x, z)})")
        check(cond=eventually(lambda: floor_at(port, x, z) == floor_at(H, x, z), timeout=10), label=f"invite : il le voit aussi ({floor_at(port, x, z)})")
        check(cond=eventually(lambda: g0 - gold(H, uid) == 10, timeout=10), label=f"l'or part une seule fois : 10 ({g0} -> {gold(H, uid)})")
        check(cond=eventually(lambda: count(H, uid, ing_id) == 10 - req, timeout=10), label=f"les matieres partent une seule fois ({req} : 10 -> {count(H, uid, ing_id)})")
    finally:
        leave(port)
        restore_floor(x, z, before)


def c2(ctx):
    """l'invite mine un mur en mode construction : il tombe chez les deux, l'or part une fois"""
    port, uid = ctx["a"]
    x, z = spot(uid)
    wall(x, z, True)
    ev(H, f'{chara(H, uid)}.ModCurrency(500); "ok"')
    time.sleep(3)
    g0 = gold(H, uid)
    try:
        r = click(port, x, z, 'ActionMode.Mine.Activate(false); "ok"')
        log(f"invite mine {x},{z} : {r}")
        check(cond=eventually(lambda: block_at(H, x, z) == "False", timeout=15), label=f"host : le mur est tombe ({block_at(H, x, z)})")
        check(cond=eventually(lambda: block_at(port, x, z) == "False", timeout=10), label=f"invite : son mur est tombe aussi ({block_at(port, x, z)})")
        check(cond=eventually(lambda: g0 - gold(H, uid) == 10, timeout=10), label=f"l'or part une seule fois : 10 ({g0} -> {gold(H, uid)})")
    finally:
        leave(port)
        wall(x, z, False)


def c3(ctx):
    """l'host pose un sol en mode construction : l'invite le voit sans rentrer a nouveau dans la zone"""
    x, z = spot(ctx["h"][1])
    before = floor_at(A, x, z)
    try:
        ing_id, req, r = floor_click(ctx, "h", x, z)
        log(f"host clique en {x},{z} : {r}")
        check(cond=eventually(lambda: floor_at(H, x, z) != before, timeout=10), label=f"host : le sol est pose ({before} -> {floor_at(H, x, z)})")
        check(cond=eventually(lambda: floor_at(A, x, z) == floor_at(H, x, z), timeout=15), label=f"invite : il voit le sol de l'host ({before} -> {floor_at(A, x, z)})")
    finally:
        leave(H)
        restore_floor(x, z, before)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [g1, c3]
    if a.only:
        steps = [s for s in (g1, c1, c2, c3) if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'build2-{step.__name__}-{name}', port)}")
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
