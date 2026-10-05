"""Mode construction a deux (PLAN_construction_invite.md, conseil 5). Test court, sur des instances deja lancees
(host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/build2_suite.py            # ou --only c7,c3

C6  l'invite pose un meuble neuf du menu : cree et pose chez les deux, une fois ; or et matieres une fois.
C7  l'invite monte une case avec l'outil de terrain, trois coups de suite : +3 pas chez les deux (pas +1) ; puis l'host.
C8  l'invite cree une zone de base "Stockpile", change son nom et son acces, puis l'efface : memes zones, points et
    reglages chez les deux, l'objet Area de l'envoyeur n'est pas remplace par l'echo ; puis l'host.
C9  l'host tourne un mur (Cell.RotateAll) et fait pousser / marque recolte une plante (GrowSystem) : meme etat chez l'invite.
C3  l'host pose un sol en mode construction (ligne 4) : l'invite le voit sans rentrer dans la zone.
C4  l'host mine un mur en mode construction : il tombe aussi chez l'invite.
C5  l'invite coupe un objet de case en mode construction : parti chez les deux, 10 or une fois.
C1  l'invite pose un sol du menu de construction : pose chez les deux, 10 or et les matieres une fois.
C2  l'invite mine un mur en mode construction : il tombe chez les deux, 10 or une fois, la pierre dans son sac.

Ce que le banc ne joue pas comme un joueur : le mode et la recette sont choisis par l'appel que fait le bouton du menu
(StartBuild, Activate), la souris est posee par Scene.HitPoint ; le clic lui-meme est celui du jeu (TryProcessTiles).
C7 : un seul coup de pinceau (un TryProcessTiles), pas un glisser bouton enfonce ; le sens du pinceau est regle par
ActionMode.Terrain.mode, pas par le bouton du sous-menu. C8 : la zone est celle de l'onglet "area" (SetArea puis Activate) ;
l'effacement appelle RemoveArea, le corps du bouton "delete" du menu contextuel d'AM_EditArea, pas le menu lui-meme ;
le nom et l'acces sont poses par les champs de data, pas par les boites de dialogue. C9 : la touche R est Cell.RotateAll
appele a la main (sans souris sur un objet) ; la pousse est GrowSystem.Grow et SetStage appeles a la main, pas une
heure de jeu qui passe ; la recolte (GrowSystem.Harvest, qui cree des objets) n'est pas jouee, seulement la marque
"recolte" posee par SetStage(.., true) ; le sol tourne (RotateFloor, RotateObj) n'est pas joue.
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
    return stroke(port, x, z)


def stroke(port, x, z):
    """le clic seul, dans un mode deja actif"""
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


def heights(port, x, z):
    """hauteur et hauteur de pont des cases autour de (x, z), dans l'ordre (le pinceau en touche 4 de rayon)"""
    return ev(port, f'var s = ""; for (int i = {x} - 4; i <= {x} + 4; i++) for (int j = {z} - 4; j <= {z} + 4; j++) {{ '
                    'if (i < 0 || j < 0 || i >= EClass._map.Size || j >= EClass._map.Size) continue; '
                    'var c = EClass._map.cells[i, j]; s += c.height + "/" + c.bridgeHeight + ","; } return s;')


def restore_heights(x, z, snap):
    """le terrain n'est pas remis par le jeu : les anciennes hauteurs, ecrites a la main des DEUX cotes"""
    for p in (H, A):
        ev(p, f'var h = "{snap}".Split(",".ToCharArray(), StringSplitOptions.RemoveEmptyEntries); int k = 0; '
              f'for (int i = {x} - 4; i <= {x} + 4; i++) for (int j = {z} - 4; j <= {z} + 4; j++) {{ '
              'if (i < 0 || j < 0 || i >= EClass._map.Size || j >= EClass._map.Size) continue; '
              'var c = EClass._map.cells[i, j]; var q = h[k++].Split("/".ToCharArray()); c.height = byte.Parse(q[0]); c.bridgeHeight = byte.Parse(q[1]); } '
              'EClass._map.RefreshAllTiles(); return "ok";')


def terrain_click(port, x, z, strokes=1):
    """le pinceau monte la case (descend si elle n'a pas la place de monter), `strokes` coups espaces de 0,4 s ;
    rend (resultat du premier clic, hauteur attendue au centre)"""
    h0 = int(ev(port, f'new Point({x}, {z}).cell.height.ToString()'))
    top = int(ev(port, 'EClass.setting.maxGenHeight.ToString()'))
    radius = int(ev(port, 'ActionMode.Terrain.brushRadius.ToString()'))
    up = h0 + strokes * radius <= top
    r = click(port, x, z, f'ActionMode.Terrain.mode = AM_Terrain.Mode.{"Up" if up else "Down"}; ActionMode.Terrain.Activate(false); "ok"')
    for _ in range(strokes - 1):
        time.sleep(0.4)
        stroke(port, x, z)
    want = h0 + strokes * radius if up else max(0, h0 - strokes * radius)
    return r, want


def centre(port, x, z):
    return int(ev(port, f'new Point({x}, {z}).cell.height.ToString()'))


def c7(ctx):
    """l'invite monte une case avec l'outil de terrain, trois coups de suite : +3 pas chez les deux ; puis l'host"""
    port, uid = ctx["a"]
    x, z = spot(uid)
    snap = heights(H, x, z)
    check("point de depart : memes hauteurs chez les deux", heights(port, x, z) == snap)
    try:
        r, want = terrain_click(port, x, z, strokes=3)
        log(f"invite passe le pinceau 3 fois en {x},{z} : {r}, centre attendu {want}")
        check(f"le clic est accepte par le jeu ({r})", r.startswith("True|"))
        check(cond=eventually(lambda: centre(H, x, z) == want, timeout=15), label=f"host : le centre est a {want} ({centre(H, x, z)})")
        check(cond=eventually(lambda: heights(port, x, z) == heights(H, x, z), timeout=10),
              label=f"invite : les memes hauteurs que l'host (centre {centre(port, x, z)} / {centre(H, x, z)})")
        time.sleep(3)
        check("rien ne bouge ensuite", heights(port, x, z) == heights(H, x, z) != snap and centre(port, x, z) == want)
    finally:
        leave(port)
        restore_heights(x, z, snap)
    time.sleep(2)
    snap = heights(H, x, z)
    try:
        r, want = terrain_click(H, x, z)
        log(f"host passe le pinceau en {x},{z} : {r}")
        check(cond=eventually(lambda: centre(H, x, z) == want, timeout=10), label=f"host : le centre est a {want} ({centre(H, x, z)})")
        check(cond=eventually(lambda: heights(port, x, z) == heights(H, x, z) != snap, timeout=15), label="invite : il voit le terrain de l'host")
    finally:
        leave(H)
        restore_heights(x, z, snap)


def zones(port):
    """les zones de base : numero, type et points, dans l'ordre des points"""
    return ev(port, 'string.Join(";", EClass._map.rooms.listArea.OrderBy(a => a.uid).Select(a => a.uid + ":" + a.type.id + ":" + '
                    'a.data.name + ":" + a.data.accessType + ":" + '
                    'string.Join(",", a.points.Select(p => p.x + "-" + p.z).OrderBy(t => t)))).ToString()')


def c8(ctx):
    """l'invite cree une zone "Stockpile", change son nom et son acces, puis l'efface : memes zones, points et reglages
    chez les deux, et l'objet Area de la zone n'est remplace nulle part (ni par l'echo chez l'envoyeur) ; puis l'host"""
    port, uid = ctx["a"]
    x, z = spot(uid)
    zone0 = zones(H)
    check("point de depart : memes zones chez les deux", zones(port) == zone0)
    known = ",".join(str(int(a.split(":")[0])) for a in zone0.split(";") if a)
    try:
        for who, name in ((port, "invite"), (H, "host")):
            other = H if who == port else port
            r = click(who, x, z, 'ActionMode.CreateArea.SetArea(Area.Create("Stockpile")); ActionMode.CreateArea.Activate(); "ok"')
            log(f"{name} trace une zone en {x},{z} : {r}")
            check(f"{name} : le clic est accepte par le jeu ({r})", r.startswith("True|1|"))
            check(cond=eventually(lambda: zones(H) != zone0 and zones(port) == zones(H), timeout=15),
                  label=f"{name} : une zone de plus, les memes zones et points chez les deux ({zones(H)[-60:]})")
            check(f"{name} : le point est {x}-{z}", f":{x}-{z}" in zones(other))
            # nom et acces changes d'un cote : l'autre les voit, et l'objet de la zone reste le meme des deux cotes
            for p in (H, port):
                # garde l'objet d'une commande a l'autre (une variable du script ne survit pas a la commande)
                ev(p, f'System.AppDomain.CurrentDomain.SetData("keepArea", EClass._map.rooms.listArea.Where(q => q.points.Any(p => p.x == {x} && p.z == {z})).First()); "ok"')
            ev(who, 'var keepArea = (Area)System.AppDomain.CurrentDomain.GetData("keepArea"); keepArea.data.name = "Zx"; keepArea.data.accessType = BaseArea.AccessType.Private; "ok"')
            check(cond=eventually(lambda: ":Zx:Private:" in zones(other) and zones(H) == zones(port), timeout=15),
                  label=f"{name} : le nom et l'acces sont les memes chez les deux ({zones(other)[-60:]})")
            time.sleep(2)
            for p, who_p in ((who, name), (other, "l'autre")):
                same_obj = ev(p, 'var keepArea = (Area)System.AppDomain.CurrentDomain.GetData("keepArea"); '
                                 'return object.ReferenceEquals(keepArea, EClass._map.rooms.listArea.FirstOrDefault(q => q.uid == keepArea.uid)).ToString();')
                check(f"{who_p} : l'objet Area de la zone n'a pas ete remplace ({same_obj})", same_obj == "True")
            # le corps du bouton "delete" du menu contextuel d'AM_EditArea
            ev(who, f'var a = EClass._map.rooms.listArea.Where(q => q.points.Any(p => p.x == {x} && p.z == {z})).First(); '
                    'EClass._map.rooms.RemoveArea(a); "ok"')
            check(cond=eventually(lambda: zones(H) == zone0 and zones(port) == zone0, timeout=15),
                  label=f"{name} : la zone est effacee chez les deux ({zones(H)[-60:] or 'aucune'} / {zones(port)[-60:] or 'aucune'})")
            leave(who)
            time.sleep(1)
    finally:
        leave(port)
        leave(H)
        for p in (H, A):
            ev(p, f'var known = new HashSet<int> {{ {known} }}; '
                  'foreach (var a in EClass._map.rooms.listArea.Where(q => !known.Contains(q.uid)).ToList()) EClass._map.rooms.RemoveArea(a); "ok"')


def c9(ctx):
    """l'host tourne un mur (Cell.RotateAll, la touche R) puis fait pousser et marque "recolte" une plante : meme etat chez l'invite"""
    x, z = spot(ctx["h"][1])
    wall(x, z, True)
    time.sleep(2)
    cellstate = lambda p: ev(p, f'var c = new Point({x}, {z}).cell; return c._block + "/" + c.blockDir + "/" + c.crossWall + "/" + c.obj + "/" + c.objVal + "/" + c.isHarvested;')  # noqa: E731
    try:
        before = cellstate(H)
        check(f"point de depart : le meme mur chez les deux ({before} / {cellstate(A)})", before == cellstate(A))
        ev(H, f'new Point({x}, {z}).cell.RotateAll(); "ok"')
        check(f"host : le mur a tourne ({before} -> {cellstate(H)})", cellstate(H) != before)
        check(cond=eventually(lambda: cellstate(A) == cellstate(H), timeout=15), label=f"invite : le mur tourne aussi ({cellstate(A)})")
    finally:
        wall(x, z, False)
    # une plante : posee, avancee de plusieurs etapes, puis marquee "recoltee"
    x, z = spot(ctx["h"][1])
    r = ev(H, f'var row = EClass.sources.objs.rows.FirstOrDefault(o => o.HasGrowth && !o.growth.IsTree); if (row == null) return "aucune plante"; '
              f'new Point({x}, {z}).SetObj(row.id); return new Point({x}, {z}).cell.growth == null ? "pas de pousse" : "ok";')
    if not check(f"une plante posee par l'host ({r})", r == "ok"):
        return
    try:
        check(cond=eventually(lambda: cellstate(A) == cellstate(H), timeout=15), label=f"invite : il voit la plante ({cellstate(A)})")
        before = cellstate(H)
        ev(H, f'new Point({x}, {z}).cell.growth.Grow(100); "ok"')
        check(f"host : la plante a pousse ({before} -> {cellstate(H)})", cellstate(H) != before)
        check(cond=eventually(lambda: cellstate(A) == cellstate(H), timeout=15), label=f"invite : la pousse est la meme ({cellstate(A)})")
        ev(H, f'new Point({x}, {z}).cell.growth.SetStage(0, true); "ok"')
        check(f"host : marquee recoltee ({cellstate(H)})", cellstate(H).endswith("True"))
        check(cond=eventually(lambda: cellstate(A) == cellstate(H), timeout=15), label=f"invite : la marque est la meme ({cellstate(A)})")
    finally:
        ev(H, f'EClass._map.SetObj({x}, {z}, 0, 0, 0, 0, true); "ok"')


def c1(ctx):
    """l'invite pose un sol en mode construction : pose chez les deux, l'or et les matieres partent une fois"""
    port, uid = ctx["a"]
    x, z = spot(uid)
    before = floor_at(H, x, z)
    g0 = gold(H, uid) + 500
    # ce qu'il a deja de cette matiere (la pierre d'un mur mine plus tot en est aussi)
    m0 = count(H, uid, ev(port, FLOOR + 'return recipe.ingredients[0].id;')) + 10
    try:
        ing_id, req, r = floor_click(ctx, "a", x, z)
        log(f"invite clique en {x},{z} : {r}")
        check(f"le clic est accepte par le jeu ({r})", r.startswith("True|1|"))
        check(cond=eventually(lambda: floor_at(H, x, z) != before, timeout=15), label=f"host : le sol de l'invite est pose ({before} -> {floor_at(H, x, z)})")
        check(cond=eventually(lambda: floor_at(port, x, z) == floor_at(H, x, z), timeout=10), label=f"invite : il le voit aussi ({floor_at(port, x, z)})")
        check(cond=eventually(lambda: g0 - gold(H, uid) == 10, timeout=10), label=f"l'or part une seule fois : 10 ({g0} -> {gold(H, uid)})")
        check(cond=eventually(lambda: count(H, uid, ing_id) == m0 - req and count(port, uid, ing_id) == m0 - req, timeout=10),
              label=f"les matieres partent une seule fois ({req} : {m0} -> {count(H, uid, ing_id)}, chez lui {count(port, uid, ing_id)})")
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
    bag = lambda p: int(ev(p, f'{chara(p, uid)}.things.Sum(t => t.Num).ToString()'))  # noqa: E731
    b0 = bag(H)
    try:
        r = click(port, x, z, 'ActionMode.Mine.Activate(false); "ok"')
        log(f"invite mine {x},{z} : {r}")
        check(cond=eventually(lambda: block_at(H, x, z) == "False", timeout=15), label=f"host : le mur est tombe ({block_at(H, x, z)})")
        check(cond=eventually(lambda: block_at(port, x, z) == "False", timeout=10), label=f"invite : son mur est tombe aussi ({block_at(port, x, z)})")
        check(cond=eventually(lambda: g0 - gold(H, uid) == 10 and gold(port, uid) == gold(H, uid), timeout=10),
              label=f"l'or part une seule fois : 10 ({g0} -> {gold(H, uid)}, chez lui {gold(port, uid)})")
        check(cond=eventually(lambda: bag(H) > b0 and bag(port) == bag(H), timeout=10),
              label=f"la pierre du mur est dans le sac de l'invite, une fois ({b0} -> {bag(H)}, chez lui {bag(port)})")
        time.sleep(3)
        check(f"rien ne bouge ensuite (or {gold(H, uid)}, sac {bag(H)} / {bag(port)})", g0 - gold(H, uid) == 10 and bag(port) == bag(H))
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


def c4(ctx):
    """l'host mine un mur en mode construction : il tombe aussi chez l'invite, sans rentrer dans la zone"""
    x, z = spot(ctx["h"][1])
    ev(H, f'EClass._map.SetBlock({x}, {z}, 3, 1); EClass.pc.ModCurrency(100); "ok"')
    try:
        check(cond=eventually(lambda: block_at(A, x, z) == "True", timeout=10), label=f"un mur monte chez l'host arrive chez l'invite ({block_at(A, x, z)})")
        r = click(H, x, z, 'ActionMode.Mine.Activate(false); "ok"')
        log(f"host mine {x},{z} : {r}")
        check(cond=eventually(lambda: block_at(H, x, z) == "False", timeout=10), label=f"host : le mur est tombe ({block_at(H, x, z)})")
        check(cond=eventually(lambda: block_at(A, x, z) == "False", timeout=15), label=f"invite : il est tombe chez lui aussi ({block_at(A, x, z)})")
    finally:
        leave(H)
        wall(x, z, False)


def c5(ctx):
    """l'invite coupe un objet de case (arbre, plante) en mode construction : il disparait chez les deux, l'or part une fois"""
    port, uid = ctx["a"]
    where = ev(H, f'var p = {chara(H, uid)}.pos; var s = EClass._map.ListPointsInCircle(p, 12f, false, false)'
                  '.Where(q => q.HasObj && !q.HasBlock && q.IsInBounds).OrderBy(q => q.Distance(p)).FirstOrDefault(); return s == null ? "" : s.x + "," + s.z;')
    if not check(f"un objet de case a couper pres de l'invite ({where or 'aucun'})", bool(where)):
        return
    x, z = where.split(",")
    obj = lambda p: ev(p, f'new Point({x}, {z}).HasObj.ToString()')  # noqa: E731
    ev(H, f'{chara(H, uid)}.ModCurrency(100); "ok"')
    time.sleep(3)
    g0 = gold(H, uid)
    try:
        r = click(port, x, z, 'ActionMode.Cut.Activate(false); "ok"')
        log(f"invite coupe {x},{z} : {r}")
        check(cond=eventually(lambda: obj(H) == "False", timeout=15), label=f"host : l'objet de case est coupe ({obj(H)})")
        check(cond=eventually(lambda: obj(port) == "False", timeout=10), label=f"invite : chez lui aussi ({obj(port)})")
        check(cond=eventually(lambda: g0 - gold(H, uid) == 10 and gold(port, uid) == gold(H, uid), timeout=10),
              label=f"l'or part une seule fois : 10 ({g0} -> {gold(H, uid)}, chez lui {gold(port, uid)})")
    finally:
        leave(port)


CARD = ('RecipeManager.BuildList(); '
        'var src = RecipeManager.list.FirstOrDefault(r => r.row is CardRow && r.row.factory.IsEmpty() && !r.noListing && !r.isChara); '
        'if (src == null) return "pas de recette de meuble"; var recipe = Recipe.Create(src); recipe.BuildIngredientList(); ')


def c6(ctx):
    """l'invite pose un meuble neuf du menu de construction : cree et pose chez les deux, une fois, l'or et les matieres une fois"""
    port, uid = ctx["a"]
    x, z = spot(uid)
    what = ev(port, CARD + 'return recipe.GetIdThing() + "|" + string.Join(";", recipe.ingredients.Select(i => i.id + ":" + i.req));')
    if not check(f"une recette de meuble sans atelier existe ({what})", "|" in what):
        return
    made, ings = what.split("|")
    ings = [i.split(":") for i in ings.split(";") if i]
    for ing_id, req in ings:
        give(ctx, "a", ing_id, int(req) + 2)
    ev(H, f'{chara(H, uid)}.ModCurrency(100); "ok"')
    time.sleep(3)
    g0 = gold(H, uid)
    have = lambda p: [count(p, uid, i) for i, _ in ings]  # noqa: E731
    h0 = have(H)
    here = lambda p: int(ev(p, f'new Point({x}, {z}).Things.Count(t => t.id == "{made}" && t.IsInstalled).ToString()'))  # noqa: E731
    try:
        r = click(port, x, z, CARD + 'foreach (var i in recipe.ingredients) i.SetThing(EClass.pc.things.Find(t => t.id == i.id)); '
                              'ActionMode.Build.StartBuild(recipe, () => null); "ok"')
        log(f"invite pose un meuble ({made}) en {x},{z} : {r}")
        check(cond=eventually(lambda: here(H) == 1, timeout=15), label=f"host : le meuble est pose, un seul ({here(H)})")
        check(cond=eventually(lambda: here(port) == 1, timeout=10), label=f"invite : il le voit, un seul ({here(port)})")
        check(cond=eventually(lambda: g0 - gold(H, uid) == 10 and gold(port, uid) == gold(H, uid), timeout=10),
              label=f"l'or part une seule fois : 10 ({g0} -> {gold(H, uid)}, chez lui {gold(port, uid)})")
        want = [h - int(req) for h, (_, req) in zip(h0, ings)]
        check(cond=eventually(lambda: have(H) == want and have(port) == want, timeout=10),
              label=f"les matieres partent une seule fois ({h0} -> {have(H)}, chez lui {have(port)})")
        time.sleep(3)
        check(f"rien de plus ensuite (meubles {here(H)} / {here(port)}, or {gold(H, uid)})", here(H) == 1 and here(port) == 1 and g0 - gold(H, uid) == 10)
    finally:
        leave(port)
        ev(H, f'foreach (var t in new Point({x}, {z}).Things.Where(t => t.id == "{made}").ToList()) t.Destroy(); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [c3, c4, c2, c5, c1, c6, c7, c8, c9]
    if a.only:
        steps = [s for s in (c1, c2, c3, c4, c5, c6, c7, c8, c9) if s.__name__ in a.only.split(",")]
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
