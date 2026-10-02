"""Le personnage d'un joueur qui n'est pas l'host : ses dons, ses talents, son apparence comptent autant que ceux
de l'host. Test court, sur des instances deja lancees (host + 1 client).

    python _tools/mp_test.py
    python _tools/player_suite.py       # ~1 minute, tout le monde reste a la Prairie

Retours de joueurs du mod d'origine (Workshop, depot), voir PLAN_retours_joueurs.md :
F1  fabrication : le don "vie de sorciere" du client double ses potions (l'host, qui rejoue la fabrication,
    lisait ses propres dons et talents)
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

# une recette d'alchimie dont tous les ingredients sont des objets precis (pas une categorie)
ALCHEMY = ('var src = RecipeManager.list.FirstOrDefault(r => { if (r.idFactory != "tool_alchemy" || r.type == "Block") return false; '
           'var rc = Recipe.Create(r, -1); rc.BuildIngredientList(); '
           'return rc.ingredients.Count > 0 && rc.ingredients.All(i => i.optional || (!i.useCat && EClass.sources.things.map.ContainsKey(i.id))); }); ')

# l'host recoit la tache de fabrication du joueur __ME__ (ce qu'envoie son jeu quand il fabrique) et la rejoue
CRAFT = (ALCHEMY +
         'if (src == null) return "pas de recette"; var recipe = Recipe.Create(src, -1); recipe.BuildIngredientList(); '
         'var c = EClass._map.charas.Find(x => x.uid == __ME__); '
         'var tool = ThingGen.Create("tool_alchemy"); EClass._zone.AddCard(tool, c.pos); tool.Install(); '
         'var needed = recipe.ingredients.Where(i => !i.optional).ToList(); '
         'var ings = needed.Select(i => { var t = ThingGen.Create(i.id); t.SetNum(i.req); return c.AddThing(t); }).ToList(); '
         'var args = new ElinTogether.Models.AI.AIUseCrafterArgs { Factory = tool, Duration = 1, Num = 1, '
         'Targets = ings.Select(t => (ElinTogether.Models.RemoteCard)t).ToList(), Required = needed.Select(i => i.req).ToList(), '
         'Repeat = false, RecipeId = src.id, RecipeMat = -1 }; '
         'var act = args.CreateSubAct(); '
         'HarmonyLib.AccessTools.Method(c.ai.GetType(), "InsertAction").Invoke(c.ai, new object[] { act }); '
         'return src.id + "|" + tool.trait.GetType().Name + "|" + ThingGen.Create(src.id).trait.CraftNum + "|" + tool.uid;')


def count(port, chara, thing_id):
    """Nombre d'objets de ce type dans le sac du personnage, vu de ce jeu."""
    return int(ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {chara}); '
                        f'return c.things.Where(t => t.id == "{thing_id}").Sum(t => t.Num).ToString();'))


def f1(ctx):
    """don "vie de sorciere" : le client fabrique une potion, il en obtient le double"""
    me = ctx["a"]
    ev(A, f'EClass.pc.SetFeat({WITCH}, 1); "ok"')
    host_copy = f'EClass._map.charas.Find(x => x.uid == {me}).Evalue({WITCH}).ToString()'
    if not check("le don pris par le client est connu de l'host", eventually(lambda: ev(H, host_copy) == "1", timeout=10)):
        return
    check("l'host, lui, n'a pas ce don", ev(H, f'EClass.pc.Evalue({WITCH}).ToString()') == "0")

    recipe = ev(H, ALCHEMY + 'return src == null ? "" : src.id;')
    if not check(f"une recette d'alchimie simple existe ({recipe})", bool(recipe)):
        return
    before = count(H, me, recipe)
    r = ev(H, CRAFT.replace("__ME__", str(me)))
    recipe, tool, per_craft, tool_uid = r.split("|")
    per_craft = int(per_craft)
    log(f"recette {recipe} sur {tool}, {per_craft} par fabrication sans le don")
    made = lambda: count(H, me, recipe) - before  # noqa: E731
    check("la fabrication aboutit chez l'host", eventually(lambda: made() > 0, timeout=30))
    time.sleep(2)
    check(f"le don du client double la fabrication ({made()} obtenus, {2 * per_craft} attendus)", made() == 2 * per_craft)
    check("le client a le meme nombre dans son sac", eventually(lambda: count(A, me, recipe) == count(H, me, recipe), timeout=10))
    ev(H, f'var t = EClass._map.things.Find(x => x.uid == {tool_uid}); if (t != null) t.Destroy(); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": state(A)["pc"]["uid"]}
    steps = [f1]
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
