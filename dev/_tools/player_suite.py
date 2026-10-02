"""Le personnage d'un joueur qui n'est pas l'host : ses dons, ses talents, son apparence comptent autant que ceux
de l'host. Test court, sur des instances deja lancees (host + 1 client).

    python _tools/mp_test.py
    python _tools/player_suite.py       # ~1 minute, tout le monde reste a la Prairie

Retours de joueurs du mod d'origine (Workshop, depot), voir PLAN_retours_joueurs.md :
F1  fabrication : le don "vie de sorciere" du client double ses potions (l'host, qui rejoue la fabrication,
    lisait ses propres dons et talents)
F2  l'inverse : le don de l'host ne double pas les potions du client
F3  apparence : une couleur changee au miroir par le client est vue par l'host et tient apres une reconnexion
F4  apparence : une couleur changee par l'host est vue par le client
F5  slime : un gene absorbe par le client sur la carte de l'host est garde, chez l'host aussi, meme reconnecte
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
WITCH = 1417

# la recette d'alchimie la plus facile dont tous les ingredients sont des objets precis (pas une categorie) :
# une recette trop dure epuise un personnage debutant jusqu'a la mort
ALCHEMY = ('var src = RecipeManager.list.OrderBy(r => r.row == null ? 999 : r.row.LV).FirstOrDefault(r => { '
           'if (r.idFactory != "tool_alchemy" || r.type == "Block") return false; '
           'var rc = Recipe.Create(r, -1); rc.BuildIngredientList(); '
           'return rc.ingredients.Count > 0 && rc.ingredients.All(i => i.optional || (!i.useCat && EClass.sources.things.map.ContainsKey(i.id))); }); ')

# l'host pose un outil d'alchimie a cote du joueur __ME__ et lui donne les ingredients de la recette
SETUP = (ALCHEMY +
         'if (src == null) return "pas de recette"; var recipe = Recipe.Create(src, -1); recipe.BuildIngredientList(); '
         'var c = EClass._map.charas.Find(x => x.uid == __ME__); '
         'var spot = c.pos.GetNearestPoint(allowBlock: false, allowChara: false, allowInstalled: false, ignoreCenter: true) ?? c.pos; '
         'var tool = ThingGen.Create("tool_alchemy"); EClass._zone.AddCard(tool, spot); tool.Install(); '
         'foreach (var i in recipe.ingredients.Where(i => !i.optional)) { var t = ThingGen.Create(i.id); t.SetNum(i.req); c.AddThing(t); } '
         'return src.id + "|" + tool.trait.GetType().Name + "|" + ThingGen.Create(src.id).trait.CraftNum + "|" + tool.uid;')

# le client fabrique comme un joueur : la fenetre de fabrication de l'outil, la recette, ses ingredients, "fabriquer"
CRAFT = ('var tool = EClass._map.things.Find(x => x.uid == __TOOL__); if (tool == null) return "outil pas vu"; '
         'var recipe = Recipe.Create(RecipeManager.dict["__RECIPE__"], -1); recipe.BuildIngredientList(); '
         'foreach (var ing in recipe.ingredients.Where(i => !i.optional)) { var t = EClass.pc.things.Find(x => x.id == ing.id); '
         'if (t == null) return "il manque " + ing.id; ing.SetThing(t); } '
         'var layer = EClass.ui.AddLayer<LayerCraft>(); layer.SetFactory(tool); layer.recipe = recipe; layer.inputNum.Num = 1; '
         'layer.OnClickCraft(); return "ok";')


def count(port, chara, thing_id):
    """Nombre d'objets de ce type dans le sac du personnage, vu de ce jeu."""
    return int(ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {chara}); '
                        f'return c.things.Where(t => t.id == "{thing_id}").Sum(t => t.Num).ToString();'))


def set_witch(port, on):
    ev(port, f'EClass.pc.SetFeat({WITCH}, {1 if on else 0}); "ok"')


def brew(ctx):
    """Le client fabrique une potion d'alchimie comme un joueur. Renvoie (obtenues, par fabrication sans don)."""
    me = ctx["a"]
    recipe = ev(H, ALCHEMY + 'return src == null ? "" : src.id;')
    if not check(f"une recette d'alchimie simple existe ({recipe})", bool(recipe)):
        return None
    before = count(H, me, recipe)
    r = ev(H, SETUP.replace("__ME__", str(me)))
    recipe, tool, per_craft, tool_uid = r.split("|")
    log(f"recette {recipe} sur {tool}, {per_craft} par fabrication sans le don")
    # de quoi fabriquer sans s'epuiser (un personnage tout neuf a peu d'endurance), des deux cotes
    for port, who in ((A, "EClass.pc"), (H, f"EClass._map.charas.Find(x => x.uid == {me})")):
        ev(port, f'var c = {who}; c.stamina.Set(c.stamina.max); c.hp = c.MaxHP; "ok"')
    time.sleep(3)
    try:
        started = ev(A, CRAFT.replace("__TOOL__", tool_uid).replace("__RECIPE__", recipe))
        if not check(f"le client lance la fabrication ({started})", started == "ok"):
            return None
        made = lambda: count(H, me, recipe) - before  # noqa: E731
        check("la fabrication aboutit", eventually(lambda: made() > 0, timeout=40))
        time.sleep(2)
        check("le client a le meme nombre dans son sac que chez l'host",
              eventually(lambda: count(A, me, recipe) == count(H, me, recipe), timeout=10))
        check("le client est toujours en vie", ev(A, 'EClass.pc.isDead.ToString()') == "False")
        return made(), int(per_craft)
    finally:
        ev(A, 'EClass.ui.RemoveLayer<LayerCraft>(); "ok"')
        ev(H, f'var t = EClass._map.things.Find(x => x.uid == {tool_uid}); if (t != null) t.Destroy(); "ok"')


def f1(ctx):
    """don "vie de sorciere" : le client l'a, pas l'host ; sa potion est doublee"""
    me = ctx["a"]
    set_witch(A, True)
    set_witch(H, False)
    host_copy = f'EClass._map.charas.Find(x => x.uid == {me}).Evalue({WITCH}).ToString()'
    if not check("le don pris par le client est connu de l'host", eventually(lambda: ev(H, host_copy) == "1", timeout=10)):
        return
    check("l'host, lui, n'a pas ce don", ev(H, f'EClass.pc.Evalue({WITCH}).ToString()') == "0")
    r = brew(ctx)
    if r:
        check(f"le don du client double sa fabrication ({r[0]} obtenues, {2 * r[1]} attendues)", r[0] == 2 * r[1])


def f2(ctx):
    """l'inverse : l'host a le don, pas le client ; la potion du client n'est pas doublee"""
    me = ctx["a"]
    set_witch(A, False)
    set_witch(H, True)
    try:
        host_copy = f'EClass._map.charas.Find(x => x.uid == {me}).Evalue({WITCH}).ToString()'
        if not check("l'host sait que le client n'a plus le don", eventually(lambda: ev(H, host_copy) == "0", timeout=10)):
            return
        r = brew(ctx)
        if r:
            check(f"le don de l'host ne compte pas pour le client ({r[0]} obtenue, {r[1]} attendue)", r[0] == r[1])
    finally:
        set_witch(H, False)


RED = "FF0000FF"

# comme au miroir : l'ecran d'apparence, une couleur changee, l'ecran ferme (c'est la fermeture qui applique)
DYE = ('var l = EClass.ui.AddLayer<LayerEditPCC>("LayerPCC/LayerEditPCC"); l.Activate(EClass.pc, UIPCC.Mode.Body); '
       'var part = l.uiPCC.pcc.data.map.ContainsKey("hair") ? "hair" : l.uiPCC.pcc.data.map.Keys.First(); '
       f'l.uiPCC.pcc.data.SetColor(part, "{RED}"); l.Close(); return part;')


def colour(port, chara, part):
    """Couleur de cette partie du personnage, vue par ce jeu."""
    return ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {chara}); if (c == null) return "absent"; '
                    f'return c.pccData != null && c.pccData.map.ContainsKey("{part}") ? c.pccData.map["{part}"][2] : "rien";')


def f3(ctx):
    """apparence : le client change une couleur au miroir ; l'host la voit, et elle tient apres une reconnexion"""
    from chara_suite import click, connect, in_game, leave
    me = ctx["a"]
    part = ev(A, DYE)
    log(f"partie teinte : {part}")
    check("le client se voit avec la nouvelle couleur", colour(A, me, part) == RED)
    check(f"l'host voit la nouvelle couleur sur le personnage du client (vu : {colour(H, me, part)})",
          eventually(lambda: colour(H, me, part) == RED, timeout=10))
    leave()
    connect()
    click(0)
    back = in_game()
    check("le client se reconnecte avec le meme personnage", back == me)
    check(f"il a garde sa couleur (vu : {colour(A, me, part)})", colour(A, me, part) == RED)


def f4(ctx):
    """apparence : dans l'autre sens, l'host change une couleur, le client la voit"""
    host = state(H)["pc"]["uid"]
    part = ev(H, DYE)
    check("l'host se voit avec la nouvelle couleur", colour(H, host, part) == RED)
    check(f"le client voit la nouvelle couleur sur le personnage de l'host (vu : {colour(A, host, part)})",
          eventually(lambda: colour(A, host, part) == RED, timeout=10))


SLIME = 1274


def genes(port, chara):
    """Nombre de genes absorbes par ce personnage, et ses points de don, vus par ce jeu : "genes|points"."""
    return ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {chara}); if (c == null) return "absent"; '
                    'return (c.c_genes == null ? 0 : c.c_genes.items.Count) + "|" + c.feat;')


def f5(ctx):
    """slime : le client absorbe un gene sur la carte de l'host ; il le garde, chez l'host aussi, meme reconnecte"""
    from chara_suite import click, connect, in_game, leave
    me = ctx["a"]
    # un slime au bout de son evolution (emplacements de genes ouverts), qui a faim, avec des points de don
    ev(A, f'EClass.pc.SetFeat({SLIME}, 8); EClass.pc.hunger.Set(60); "ok"')
    host_copy = f'EClass._map.charas.Find(x => x.uid == {me}).Evalue({SLIME}).ToString()'
    if not check("l'host sait que le client est un slime", eventually(lambda: ev(H, host_copy) == "8", timeout=10)):
        return
    gene = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); c.hunger.Set(60); '
                 'var g = DNA.GenerateRandomGene(1, 7); c.AddThing(g); return g.uid + "|" + g.c_DNA.cost + "|" + g.c_DNA.slot;')
    gene, cost, slot = gene.split("|")
    log(f"gene {gene}, cout {cost} points de don, {slot} emplacement(s)")
    check("le client a le gene dans son sac",
          eventually(lambda: ev(A, f'(EClass.pc.things.Find(x => x.uid == {gene}) != null).ToString()') == "True", timeout=10))
    before_a, before_h = genes(A, me), genes(H, me)
    log(f"avant : chez le client {before_a}, chez l'host {before_h} (genes|points de don)")
    n = int(before_a.split("|")[0])
    ev(A, f'var g = EClass.pc.things.Find(x => x.uid == {gene}); EClass.pc.SetAI(new AI_Eat {{ target = g }}); "ok"')
    check(f"le client absorbe le gene (chez lui : {genes(A, me)})",
          eventually(lambda: int(genes(A, me).split("|")[0]) == n + 1, timeout=40))
    check(f"l'host le lui connait aussi (chez l'host : {genes(H, me)})",
          eventually(lambda: int(genes(H, me).split("|")[0]) == n + 1, timeout=10))
    time.sleep(2)
    check(f"memes genes et memes points de don des deux cotes (client {genes(A, me)}, host {genes(H, me)})",
          genes(A, me) == genes(H, me))
    leave()
    connect()
    click(0)
    back = in_game()
    check(f"apres reconnexion, le gene est toujours la (client {genes(A, back)}, host {genes(H, back)})",
          back == me and int(genes(A, me).split("|")[0]) == n + 1 and int(genes(H, me).split("|")[0]) == n + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": state(A)["pc"]["uid"]}
    steps = [f1, f2, f3, f4, f5]
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
