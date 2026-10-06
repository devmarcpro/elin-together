"""Fabrication « flottante » (TaskCraft) et meuble deplace, pour un invite (PLAN_fabrication_invite.md).
Test court, sur des instances deja lancees (host + 1 client, tous les deux sur la meme carte).

    python _tools/mp_test.py
    python _tools/craft_suite.py            # ou --only c1,c4

C1  garde-fou : le jeu ne propose toujours pas la fabrication flottante (reglage altCraft faux, Thing.GetRecipes vide,
    liste vide meme avec de quoi fabriquer dans le sac). ROUGE le jour ou le jeu l'active : realiser alors le plan
    (PLAN_fabrication_invite.md, section 3) et passer GUEST_CRAFTS a True.
C2  l'invite lance TaskCraft comme le ferait le clic de la liste. Aujourd'hui (GUEST_CRAFTS = False) : l'host l'arrete,
    RIEN n'est pris et rien n'est cree, dans les deux jeux. Apres le plan (True) : ingredients partis une fois, produit
    une fois dans SON sac dans les deux jeux, experience gagnee.
C3  l'host (temoin) : la meme tache, il obtient ce qu'un joueur seul obtient ; lu aussi chez l'invite.
C4  meuble installe deplace avec une hauteur (mode construction, AM_Inspect) par l'invite puis par l'host : la case ET
    la hauteur sont les memes dans les deux jeux. Rouge avant CardPoseDelta (hauteur 0 chez l'autre), et rouge tant
    que la ligne [Union(843, typeof(CardPoseDelta))] n'est pas dans ElinDelta.cs.

Ce que le banc ne joue pas comme un joueur :
- C2/C3 : la liste flottante est vide dans le jeu, il n'y a rien a cliquer. La tache est construite comme
  LayerCraftFloat.cs:91-105 la construit (recette, num = 1, floatMode, ResetReq, IsIngredientsValid, SetAI). La recette
  est la recette d'alchimie la plus simple (celle de player_suite), sans outil d'alchimie a cote : la tache ne le
  verifie pas, la liste l'aurait verifie. Les ingredients sont donnes par l'host, un de plus que necessaire (pile
  partielle : le cas ou Split fait une copie).
- C4 : le meuble (un coffre) est cree et installe par l'host ; le mode est ouvert par Activate(objet), la hauteur est
  posee sur le modele du mode (ce que fait la molette), le clic est OnProcessTiles (ce qu'appelle le clic) ;
  « terminer tout de suite » (instaComplete) est mis a vrai le temps du geste. Ni mode toit, ni pose libre.
Jamais lance : ecrit sans avoir tourne.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dummy_suite import skills  # noqa: E402
from guest_suite import awake, chara, free_next_to, give  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs, session_log_lines  # noqa: E402

H, A = 27551, 27552
# passe a True quand le plan (section 3) est realise
GUEST_CRAFTS = False

# la recette d'alchimie la plus facile dont tous les ingredients sont des objets precis, sans ingredient facultatif
RECIPE = ('var src = RecipeManager.list.OrderBy(r => r.row == null ? 999 : r.row.LV).FirstOrDefault(r => { '
          'if (r.idFactory != "tool_alchemy" || r.type == "Block") return false; '
          'var rc = Recipe.Create(r, -1); rc.BuildIngredientList(); '
          'return rc.ingredients.Count > 0 && rc.ingredients.All(i => !i.optional && !i.useCat && EClass.sources.things.map.ContainsKey(i.id)); }); ')

# ce que fait le clic d'une ligne de la liste flottante (LayerCraftFloat.cs:82-105)
START = ('var recipe = Recipe.Create(RecipeManager.dict["__RECIPE__"], -1); recipe.BuildIngredientList(); '
         'foreach (var ing in recipe.ingredients) { var t = EClass.pc.things.Find(x => x.id == ing.id); '
         'if (t == null) return "il manque " + ing.id; ing.SetThing(t); } '
         'recipe.OnChangeIngredient(); '
         'var task = new TaskCraft { recipe = recipe, num = 1, repeat = false, floatMode = true }; task.ResetReq(); '
         'if (!task.IsIngredientsValid(false, task.num)) return "ingredients refuses"; '
         'EClass.pc.SetAI(task); return "ok";')


def has(port, uid, thing_id):
    """Nombre d'objets de ce type chez ce joueur (sac, sous-sacs et main), vu par ce jeu."""
    return int(ev(port, f'var c = {chara(port, uid)}; return c == null ? "-1" : c.things.List(t => t.id == "{thing_id}").Sum(t => t.Num).ToString();'))


def c1(ctx):
    """garde-fou : le jeu ne propose pas la fabrication flottante"""
    for name, port in (("host", H), ("invite", A)):
        il = ev(port, 'typeof(Thing).GetMethod("GetRecipes").GetMethodBody().GetILAsByteArray().Length.ToString()')
        alt = ev(port, 'EClass.game.altCraft.ToString()')
        layer = ev(port, '(LayerCraftFloat.Instance != null).ToString()')
        check(f"{name} : Thing.GetRecipes est vide ({il} octet(s)), altCraft = {alt}, liste ouverte = {layer}",
              int(il) <= 2 and alt == "False" and layer == "False")


def craft(ctx, who, expect_done):
    port, uid = ctx[who]
    other = A if port == H else H
    recipe = ev(H, RECIPE + 'return src == null ? "" : src.id;')
    if not check(f"une recette simple existe ({recipe})", bool(recipe)):
        return
    ings = dict((i.split(":")[0], int(i.split(":")[1])) for i in ev(
        H, f'var rc = Recipe.Create(RecipeManager.dict["{recipe}"], -1); rc.BuildIngredientList(); '
           'return string.Join(";", rc.ingredients.Select(i => i.id + ":" + i.req));').split(";"))
    for thing_id, req in ings.items():
        give(ctx, who, thing_id, req + 1)
    ev(port, 'EClass.pc.SetNoGoal(); EClass.pc.stamina.value = EClass.pc.stamina.max; "ok"')
    time.sleep(3)
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    made0 = has(H, uid, recipe)
    ings0 = {i: has(H, uid, i) for i in ings}
    exp0 = skills(port, uid)
    try:
        awake(port)
        started = ev(port, START.replace("__RECIPE__", recipe))
        if not check(f"{who} : la fabrication est lancee ({started})", started == "ok"):
            return
        check(cond=eventually(lambda: awake(port) and ev(port, '(EClass.pc.ai is TaskCraft).ToString()') == "False", timeout=40),
              label=f"{who} : la tache se termine")
        time.sleep(3)
        made = {p: has(p, uid, recipe) - made0 for p in (port, other)}
        used = {p: {i: ings0[i] - has(p, uid, i) for i in ings} for p in (port, other)}
        gained = {k: v for k, v in skills(port, uid).items() if exp0.get(k) != v}
        refused = [line for line in session_log_lines(t0) if "no matching act" in line and "TaskCraft" in line]
        if expect_done:
            check(f"{who} : les ingredients sont partis une fois, dans les deux jeux ({used}, attendu {ings})",
                  used[port] == ings and used[other] == ings)
            check(f"{who} : le produit est chez lui, une fois, dans les deux jeux ({made})", made[port] == made[other] > 0)
            check(f"{who} : il a gagne de l'experience ({gained or 'rien'})", bool(gained))
            check(f"{who} : l'host n'a pas refuse la tache ({len(refused)} fois)", not refused)
        else:
            check(f"{who} : aucun ingredient pris, dans les deux jeux ({used})",
                  all(v == 0 for p in used.values() for v in p.values()))
            check(f"{who} : aucun produit, dans les deux jeux ({made})", made[port] == made[other] == 0)
            log(f"(information) l'host a refuse la tache : {len(refused)} fois ; experience : {gained or 'rien'}")
    finally:
        ev(port, 'if (EClass.pc.ai is TaskCraft) EClass.pc.SetNoGoal(); "ok"')
        ids = " || ".join(f'm.id == "{i}"' for i in list(ings) + [recipe])
        ev(H, f'var c = {chara(H, uid)}; if (c != null) foreach (var t in c.things.List(m => {ids})) t.Destroy(); "ok"')


def c2(ctx):
    """l'invite lance TaskCraft : rien de perdu aujourd'hui, la fabrication complete une fois le plan realise"""
    craft(ctx, "a", GUEST_CRAFTS)


def c3(ctx):
    """l'host (temoin) lance TaskCraft : ce qu'un joueur seul obtient"""
    craft(ctx, "h", True)


def c4(ctx):
    """meuble installe deplace avec une hauteur : meme case et meme hauteur dans les deux jeux"""
    for who in ("a", "h"):
        port, uid = ctx[who]
        other = A if port == H else H
        first, second = free_next_to(H, uid, 1), free_next_to(H, uid, 2)
        if not check(f"{who} : deux cases libres pres de lui ({first} / {second})", first and second):
            continue
        x, z = first.split(",")
        chest = int(ev(H, f'var t = ThingGen.Create("chest3"); t.c_lockLv = 0; EClass._zone.AddCard(t, new Point({x}, {z})).Install(); return t.uid.ToString();'))
        where = lambda p: ev(p, f'var t = EClass._map.things.Find(m => m.uid == {chest}); '  # noqa: E731
                                'return t == null ? "absent" : t.pos.x + "," + t.pos.z + " hauteur " + t.altitude + (t.IsInstalled ? "" : " pas pose");')
        try:
            if not check(f"{who} : le coffre est pose, dans son jeu ({where(port)})",
                         eventually(lambda: where(port) == f"{first} hauteur 0", timeout=15)):
                continue
            x, z = second.split(",")
            moved = ev(port, f'var t = EClass._map.things.Find(m => m.uid == {chest}); var insta = EClass.player.instaComplete; '
                             'EClass.player.instaComplete = true; var am = ActionMode.Inspect; '
                             f'try {{ am.Activate(t); am.moldCard.altitude = 2; am.OnProcessTiles(new Point({x}, {z}), 0); }} '
                             'finally { EClass.player.instaComplete = insta; ActionMode.Adv.Activate(); } return "ok";')
            want = f"{second} hauteur 2"
            if not check(f"{who} : il deplace le coffre ({moved}) ; dans son jeu : {where(port)}", moved == "ok" and where(port) == want):
                continue
            check(cond=eventually(lambda: where(other) == want, timeout=15),
                  label=f"{who} : l'autre jeu voit la meme case et la meme hauteur ({where(other)}, attendu {want})")
            check(f"{who} : son jeu n'a pas ete corrige en retour ({where(port)})", where(port) == want)
        finally:
            ev(port, 'if (!(EClass.scene.actionMode is AM_Adv)) ActionMode.Adv.Activate(); "ok"')
            ev(H, f'var t = EClass._map.things.Find(m => m.uid == {chest}); if (t != null) t.Destroy(); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [c1, c2, c3, c4]
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
                print(f"    capture {name} : {shot(f'craft-{step.__name__}-{name}', port)}")
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
