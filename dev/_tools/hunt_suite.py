"""Chasse aux differences host / invite (PLAN_chasse_differences.md) : pour chaque ligne, le meme geste par l'invite
puis par l'host. Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/hunt_suite.py            # ou --only d1,d3

D1  peur : frappe sous 20 % de points de vie, un invite ne prend pas peur (le jeu ne le fait qu'aux habitants) et
    peut toujours frapper, comme l'host.
D2  guerisseur payant : l'invite paie et il est soigne pour de bon (chez l'host aussi), comme l'host.
D3  rangement automatique : l'invite range son sac dans un coffre regle pour ca ; les fenetres de l'host restent
    ouvertes et les objets de l'host restent dans son sac.

Ce que le banc ne joue pas comme un joueur :
- D1 : les coups recus sont 300 appels a DamageHP (degats 0) chez l'host, points de vie remis a 10 % a chaque fois
  (le tirage de la peur est a 7 % par coup) ; le coup rendu est ACT.Melee, ce que fait le clic sur un monstre.
- D2 : le dialogue est le vrai (parler, « I need healing », « Yes ») ; les choix sont cliques par leur texte anglais.
- D3 : le reglage « ranger ici ce qui s'y trouve deja » du coffre est pose directement (dans les deux jeux) ; le
  rangement est lance par TaskDump.TryPerform, ce que fait la touche.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import awake, both, chara, clear_conditions, close_layers, count, give  # noqa: E402
from equal2_suite import drop, seen, spawn  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552


def d1(ctx):
    """peur : sous 20 % de points de vie, un invite frappe ne prend pas peur et peut toujours frapper, comme l'host"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        foe = spawn(uid, "putty", "Enemy", "m.hp = 100000;")
        try:
            if not check(f"{who} : un monstre est a cote de lui ({foe})", foe and eventually(lambda: seen(port, foe), timeout=15)):
                continue
            ev(H, f'var c = {chara(H, uid)}; var m = EClass._map.charas.Find(x => x.uid == {foe}); for (var i = 0; i < 300; i++) {{ '
                  'c.hp = System.Math.Max(1, c.MaxHP / 10); c.DamageHP(0, AttackSource.None, m); } "ok"')
            fear = lambda p: ev(p, f'{chara(p, uid)}.HasCondition<ConFear>().ToString()')  # noqa: E731
            time.sleep(2)
            check(f"{who} : frappe 300 fois sous 20 % de points de vie, il n'a pas peur, chez l'host ({fear(H)}) ni chez lui ({fear(port)})",
                  fear(H) == "False" and fear(port) == "False")
            hp = lambda: int(ev(H, f'EClass._map.charas.Find(x => x.uid == {foe}).hp.ToString()'))  # noqa: E731
            hp0 = hp()
            for _ in range(6):
                awake(port)
                ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {foe}); ACT.Melee.Perform(EClass.pc, m, m.pos); "ok"')
                time.sleep(1)
            check(cond=eventually(lambda: hp() < hp0, timeout=5), label=f"{who} : il peut frapper, le monstre perd des points de vie ({hp0} -> {hp()})")
        finally:
            drop([foe])
            ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; "ok"')
            clear_conditions(uid)


def talk(port, m):
    """Le joueur parle a ce personnage (le clic « parler »)."""
    awake(port)
    ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {m}); m.ShowDialog(); "ok"')
    return eventually(lambda: ev(port, '(LayerDrama.Instance != null).ToString()') == "True", timeout=10)


def pick(port, label):
    """Clique le choix du dialogue du jeu dont le texte contient `label` ; renvoie les choix proposes ensuite."""
    r = ev(port, 'var d = LayerDrama.Instance; if (d == null) return "pas de dialogue"; var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(false)'
                 f'.FirstOrDefault(x => x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.Contains("{label}"))); '
                 'if (b == null) return "pas de choix"; b.onClick.Invoke(); return "clic";')
    time.sleep(1.5)
    return r


def hang_up(port):
    ev(port, 'if (LayerDrama.Instance != null) EClass.ui.RemoveLayer<LayerDrama>(); "ok"')


def d2(ctx):
    """guerisseur payant : le joueur paie et il est soigne pour de bon, l'invite comme l'host"""
    healer = ev(H, 'EClass.sources.charas.rows.First(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Healer").id')
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        priest = spawn(uid, healer, "Friend")
        try:
            if not check(f"{who} : un guerisseur est a cote de lui ({priest})", priest and eventually(lambda: seen(port, priest), timeout=15)):
                continue
            give(ctx, key, "money", 5000)
            ev(H, f'var c = {chara(H, uid)}; c.hp = 1; "ok"')
            hp = lambda p: int(ev(p, f'{chara(p, uid)}.hp.ToString()'))  # noqa: E731
            full = int(ev(H, f'{chara(H, uid)}.MaxHP.ToString()'))
            eventually(lambda: hp(port) <= 2, timeout=10)
            gold0 = count(H, uid, "money")
            said = talk(port, priest) and pick(port, "healing") == "clic" and pick(port, "Yes") == "clic"
            if not check(f"{who} : il demande des soins au guerisseur et dit oui", said):
                continue
            check(cond=eventually(lambda: count(H, uid, "money") < gold0 and count(port, uid, "money") == count(H, uid, "money"), timeout=10),
                  label=f"{who} : il a paye, les deux jeux voient la meme bourse ({gold0} -> {count(H, uid, 'money')} et {count(port, uid, 'money')})")
            check(cond=eventually(lambda: hp(H) >= full - 1, timeout=10), label=f"{who} : il est soigne, chez l'host ({hp(H)}/{full})")
            time.sleep(3)
            check(cond=eventually(lambda: hp(port) >= full - 1, timeout=10), label=f"{who} : et chez lui, pour de bon ({hp(port)}/{full})")
        finally:
            hang_up(port)
            drop([priest])
            ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; foreach (var t in c.things.Where(m => m.id == "money").ToList()) t.Destroy(); "ok"')


def d3(ctx):
    """rangement automatique : le joueur range son sac ; les fenetres et les objets de l'autre joueur ne bougent pas"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        other_key = "h" if key == "a" else "a"
        other, other_uid = ctx[other_key]
        close_layers()
        mine, theirs = give(ctx, key, "bucket", 3), give(ctx, other_key, "bucket", 3)
        chest = int(ev(H, f'var t = ThingGen.Create("chest3"); EClass._zone.AddCard(t, {chara(H, uid)}.pos.GetNearestPoint(false, false, false, true)).Install(); '
                          't.AddCard(ThingGen.Create("bucket")); return t.uid.ToString();'))
        inside = lambda p: int(ev(p, f'var t = EClass._map.things.Find(m => m.uid == {chest}); '  # noqa: E731
                                     'return t == null ? "-1" : t.things.Where(x => x.id == "bucket").Sum(x => x.Num).ToString();'))
        try:
            eventually(lambda: inside(port) == 1, timeout=10)
            for p in (H, A):
                ev(p, f'var t = EClass._map.things.Find(m => m.uid == {chest}); t.c_windowSaveData = new Window.SaveData {{ autodump = AutodumpFlag.existing }}; "ok"')
            ev(other, 'EClass.ui.AddLayer<LayerJournal>(); "ok"')
            opened = lambda: ev(other, '(EClass.ui.layers.OfType<LayerJournal>().Any()).ToString()') == "True"  # noqa: E731
            if not check(f"{who} : l'autre joueur a une fenetre ouverte (son journal)", opened()):
                continue
            awake(port)
            ev(port, 'TaskDump.TryPerform(); "ok"')
            check(cond=eventually(lambda: inside(H) == 4, timeout=30), label=f"{who} : ses 3 seaux sont dans le coffre, chez l'host ({inside(H)} avec celui du coffre)")
            check(cond=eventually(lambda: inside(port) == inside(other) == 4, timeout=10), label=f"{who} : les deux jeux voient le meme coffre ({inside(port)} et {inside(other)})")
            check(f"{who} : il n'a plus ses seaux ({count(H, uid, 'bucket')})", count(H, uid, "bucket") == 0)
            check(f"{who} : l'autre joueur a garde les siens ({count(H, other_uid, 'bucket')})", count(H, other_uid, "bucket") == 3)
            check(f"{who} : la fenetre de l'autre joueur est restee ouverte", opened())
        finally:
            close_layers()
            for p in (port, other):
                ev(p, 'if (EClass.pc.ai is TaskDump) EClass.pc.SetNoGoal(); "ok"')
            ev(H, f'var t = EClass._map.things.Find(m => m.uid == {chest}); if (t != null) t.Destroy(); '
                  'foreach (var c in EClass._map.charas.Where(c => c.IsPCC).ToList()) foreach (var b in c.things.Where(m => m.id == "bucket").ToList()) b.Destroy(); "ok"')
            _ = mine, theirs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [d1, d2, d3]
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
                print(f"    capture {name} : {shot(f'hunt-{step.__name__}-{name}', port)}")
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
