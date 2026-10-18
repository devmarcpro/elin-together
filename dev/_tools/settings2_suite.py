"""Reglages d'objets qu'un invite changeait seulement chez lui (audit du 2026-10-18), sur des fenetres deja ouvertes
(host + invite sur la meme carte, une base avec des portes : le monde du depot ou world_lab).

    python _tools/settings2_suite.py

P1  une porte ouverte puis fermee a la main par l'invite (menu de la case, « ouvrir », Maj « fermer ») : pareil chez l'host
P2  un objet cache puis remontre par l'invite (outil de visibilite du mode construction) : pareil chez l'host
P3  le nom donne par l'invite a une graine de son sac (« changer le nom » est propose par le jeu) : l'host le connait
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually  # noqa: E402

H, A = 27551, 27552


def act(port, at, pick, all_actions=False):
    """Le menu d'une case, comme guest_suite.use_menu ; `all_actions` : Maj enfoncee (les actions de plus, dont fermer une porte)."""
    inp = "ActInput.AllAction" if all_actions else "ActInput.LeftMouse"
    return ev(port,
              f'var p = new ActPlan {{ input = {inp} }}; var pt = new PointTarget(); '
              f'pt.pos.Set(new Point({at[0]}, {at[1]})); p._Update(pt); '
              'var offered = string.Join(",", p.list.Select(i => i.act is DynamicAct d ? d.id : i.act.GetType().Name)); '
              f'var item = p.list.FirstOrDefault(i => {pick}); if (item == null) return "action absente, proposees : " + offered; '
              'item.Perform(); return "ok";')


def thing(uid):
    return f'EClass._map.things.Find(x => x.uid == {uid})'


def walk_next_to(port, x, z):
    near = lambda: int(ev(port, f'EClass.pc.pos.Distance(new Point({x}, {z})).ToString()')) <= 1  # noqa: E731
    for _ in range(4):
        # (comme dialog_walk_suite.open_dialog : le pas s'arrete parfois, le joueur recliquerait)
        ev(port, f'EClass.pc.SetAIImmediate(new AI_Goto(new Point({x}, {z}), 1)); "ok"')
        if eventually(near, timeout=15):
            return True
    return near()


def p1(ctx):
    me = state(A)["pc"]["uid"]
    door = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var d = EClass._map.things.Where(t => t.IsInstalled && t.trait.GetType() == typeof(TraitDoor) '
                 '&& t.c_lockLv == 0 && !(t.trait as TraitDoor).IsOpen() && !t.pos.HasChara).OrderBy(t => t.pos.Distance(c.pos)).FirstOrDefault(); '
                 'return d == null ? "" : d.uid + "," + d.pos.x + "," + d.pos.z;')
    if not check("une porte fermee, sans serrure, sur la carte", bool(door)):
        return
    uid, x, z = door.split(",")
    if not check("l'invite marche a cote de la porte", walk_next_to(A, x, z)):
        return
    dirs = lambda: (ev(H, f'{thing(uid)}.dir.ToString()'), ev(A, f'{thing(uid)}.dir.ToString()'))  # noqa: E731
    before = dirs()
    log(f"porte {uid} en {x},{z} : dir host/invite {before}")
    r = act(A, (x, z), 'i.act is DynamicAct d && d.id == "actOpen"')
    check(f"l'invite ouvre la porte ({r})", r == "ok")
    check("ouverte chez l'host comme chez l'invite", eventually(lambda: dirs()[0] == dirs()[1] != before[1], timeout=8))
    opened = dirs()
    r = act(A, (x, z), 'i.act is DynamicAct d && d.id == "actClose"', all_actions=True)
    check(f"l'invite la referme, Maj enfoncee ({r})", r == "ok")
    check("fermee chez l'host comme chez l'invite", eventually(lambda: dirs()[0] == dirs()[1] != opened[1], timeout=8))


def p2(ctx):
    me = state(A)["pc"]["uid"]
    spot = ev(A, f'var c = EClass.pc; var t = EClass._map.things.Where(x => x.IsInstalled && !x.isMasked && x.trait.CanBeMasked && x.pos.Distance(c.pos) < 12)'
                 '.OrderBy(x => x.pos.Distance(c.pos)).FirstOrDefault(); return t == null ? "" : t.uid + "," + t.pos.x + "," + t.pos.z;')
    if not check(f"un objet a cacher pres de l'invite ({me})", bool(spot)):
        return
    uid, x, z = spot.split(",")
    uid = ev(A, f'var t = ActionMode.Visibility.GetTarget(new Point({x}, {z})); return t == null ? "0" : t.uid.ToString();')
    masked = lambda: (ev(H, f'{thing(uid)}.isMasked.ToString()'), ev(A, f'{thing(uid)}.isMasked.ToString()'))  # noqa: E731
    log(f"objet vise par l'outil en {x},{z} : {uid}, cache host/invite {masked()}")
    ev(A, f'ActionMode.Visibility.OnProcessTiles(new Point({x}, {z}), 0); "ok"')
    check("cache chez l'host comme chez l'invite", eventually(lambda: masked() == ("True", "True"), timeout=8))
    ev(A, f'ActionMode.Visibility.OnProcessTiles(new Point({x}, {z}), 0); "ok"')
    check("remontre partout", eventually(lambda: masked() == ("False", "False"), timeout=8))


def p3(ctx):
    me = state(A)["pc"]["uid"]
    seed = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var s = ThingGen.Create("seed"); c.AddThing(s); return s.uid.ToString();')
    if not check("l'host donne une graine a l'invite", eventually(lambda: ev(A, f'(EClass.pc.things.Find(x => x.uid == {seed}) != null).ToString()') == "True", timeout=15)):
        return
    offered = ev(A, f'var t = EClass.pc.things.Find(x => x.uid == {seed}); return t.trait.CanName.ToString();')
    check("le jeu propose de nommer la graine", offered == "True")
    # ce que fait la fenetre de saisie du jeu (ActPlan, « changeName ») quand le joueur valide
    ev(A, f'EClass.pc.things.Find(x => x.uid == {seed}).c_refText = "Zorblax"; "ok"')
    name = lambda: ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var t = c.things.Find(x => x.uid == {seed}); return t == null ? "absente" : (t.c_refText ?? "");')  # noqa: E731
    check("l'host connait le nom", eventually(lambda: name() == "Zorblax", timeout=8))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for step in (p1, p2, p3):
        log(f"--- {step.__name__.upper()} : {step.__doc__ or ''}")
        try:
            step({})
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
    ok = sum(1 for r in RESULTS if r[1])
    log(f"=== {ok}/{len(RESULTS)}")


if __name__ == "__main__":
    main()
