"""Deuxieme chasse aux differences host / invite (PLAN_chasse_differences_2.md) : le meme geste par l'invite puis par
l'host. Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/hunt2_suite.py            # ou --only e1,e3

E1  tailler un rondin a la hache (ligne 2) : la planche sort et le rondin baisse, chez l'host aussi.
E2  priere (ligne 5) : celui qui prie est soigne, et son compagnon aussi.
E3  nourriture du sac (ligne 6) : elle vieillit d'heure en heure dans le sac de l'invite comme dans celui de l'host.

Ce que le banc ne joue pas comme un joueur :
- E2 : la priere est l'acte du jeu (ACT 6050, ce que fait le bouton) ; les points de vie sont baisses par l'host.
- E3 : le temps est avance d'un coup de trois heures chez l'host (GameDate.AdvanceMin, ce que fait une attente).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import awake, both, chara, clear_conditions, count, give, give_made, tame, use_held  # noqa: E402
from equal2_suite import drop  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552


def e1(ctx):
    """tailler un rondin a la hache : la planche sort et le rondin baisse, pour l'invite comme pour l'host"""
    axe = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.elements != null && x.elements.Length > 0 && x.elements.Contains(225) '
                '&& x.trait != null && x.trait.Length > 0 && x.trait[0].StartsWith("Tool")); return r == null ? "" : r.id;')
    if not check(f"le jeu a une hache ({axe})", bool(axe)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        x, z = (int(v) for v in ev(H, f'var p = {chara(H, uid)}.pos.GetNearestPoint(false, false, false, true); return p.x + "," + p.z;').split(","))
        logs = int(ev(H, f'var t = ThingGen.Create("log"); t.SetNum(3); EClass._zone.AddCard(t, new Point({x}, {z})); return t.uid.ToString();'))
        left = lambda p: ev(p, f'var t = EClass._map.things.Find(m => m.uid == {logs}); return t == null ? "0" : t.Num.ToString();')  # noqa: E731
        planks = lambda p: int(ev(p, f'({chara(p, uid)}.things.Where(t => t.id == "plank").Sum(t => t.Num) + '  # noqa: E731
                                     f'EClass._map.things.Where(t => t.id == "plank" && t.pos.Distance(new Point({x}, {z})) <= 2).Sum(t => t.Num)).ToString()'))
        try:
            eventually(lambda: left(port) == "3", timeout=10)
            tool = give(ctx, key, axe)
            p0 = planks(H)
            awake(port)
            log(f"{who} taille : {use_held(port, tool, at=(x, z), pick='i.act is TaskChopWood')}")
            check(cond=eventually(lambda: awake(port) and int(left(H)) < 3, timeout=60), label=f"{who} : le rondin baisse, chez l'host (3 -> {left(H)})")
            check(cond=eventually(lambda: planks(H) > p0, timeout=15), label=f"{who} : des planches sortent, chez l'host ({p0} -> {planks(H)})")
            check(cond=eventually(lambda: left(port) == left(H) and planks(port) == planks(H), timeout=15),
                  label=f"{who} : son jeu voit pareil (rondins {left(port)}, planches {planks(port)})")
        finally:
            ev(port, 'EClass.pc.SetNoGoal(); "ok"')
            time.sleep(1)
            ev(H, f'var t = EClass._map.things.Find(m => m.uid == {logs}); if (t != null) t.Destroy(); '
                  f'foreach (var k in EClass._map.things.Where(t => t.id == "plank" && t.pos.Distance(new Point({x}, {z})) <= 2).ToList()) k.Destroy(); '
                  f'var c = {chara(H, uid)}; foreach (var k in c.things.Where(t => t.id == "plank" || t.id == "{axe}").ToList()) k.Destroy(); "ok"')


def e2(ctx):
    """priere : celui qui prie est soigne, et son compagnon aussi, l'invite comme l'host"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        pet = tame(ctx, "cat", key)
        if not check(f"{who} a un compagnon ({pet})", bool(pet)):
            continue
        try:
            clear_conditions(pet)
            ev(port, 'if (EClass.pc.faith == null || EClass.pc.faith.IsEyth) EClass.game.religions.Wind.JoinFaith(EClass.pc, Religion.ConvertType.Campaign); '
                     'EClass.player.prayed = false; "ok"')
            time.sleep(3)
            ev(H, f'foreach (var u in new[] {{ {uid}, {pet} }}) {{ var c = EClass._map.charas.Find(x => x.uid == u); c.hp = System.Math.Max(1, c.MaxHP / 4); }} "ok"')
            hp = lambda u: ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {u}); return c.hp + "/" + c.MaxHP;')  # noqa: E731
            full = lambda u: (lambda a, b: int(a) >= int(b) - 1)(*hp(u).split("/"))  # noqa: E731
            time.sleep(2)
            before = (hp(uid), hp(pet))
            awake(port)
            ev(port, 'ACT.Create(6050).Perform(EClass.pc); "ok"')
            check(cond=eventually(lambda: full(uid), timeout=15), label=f"{who} prie : il est soigne, chez l'host ({before[0]} -> {hp(uid)})")
            check(cond=eventually(lambda: full(pet), timeout=10), label=f"{who} : son compagnon aussi ({before[1]} -> {hp(pet)})")
        finally:
            drop([pet])
            ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; "ok"')


def e3(ctx):
    """nourriture du sac : elle vieillit d'heure en heure, dans le sac de l'invite comme dans celui de l'host"""
    food = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.category == "meat" || x._origin == "meat"); return r == null ? "meat" : r.id;')
    made = {}
    for who, key in both(ctx):
        port, uid = ctx[key]
        made[key] = give_made(ctx, key, f'var t = ThingGen.Create("{food}"); t.decay = 0;')
    age = lambda p, key: int(ev(p, f'var t = {chara(p, ctx[key][1])}.things.Find(x => x.uid == {made[key]}); return t == null ? "-1" : t.decay.ToString();'))  # noqa: E731
    try:
        if not check(f"chaque joueur a une viande fraiche ({food}) dans son sac, qui peut vieillir",
                     all(age(H, k) == 0 for k in made) and ev(H, f'({chara(H, ctx["a"][1])}.things.Find(x => x.uid == {made["a"]}).trait.Decay != 0).ToString()') == "True"):
            return
        ev(H, 'EClass.world.date.AdvanceMin(180); "ok"', timeout=300)
        time.sleep(6)
        for who, key in both(ctx):
            port = ctx[key][0]
            check(cond=eventually(lambda: age(H, key) > 0, timeout=20), label=f"{who} : trois heures plus tard sa viande a vieilli, chez l'host ({age(H, key)})")
            check(cond=eventually(lambda: age(port, key) > 0, timeout=20), label=f"{who} : et dans son jeu ({age(port, key)})")
        check(f"elles ont vieilli pareil chez l'host (invite {age(H, 'a')}, host {age(H, 'h')})", age(H, "a") == age(H, "h"))
    finally:
        for key in made:
            ev(H, f'var t = {chara(H, ctx[key][1])}.things.Find(x => x.uid == {made[key]}); if (t != null) t.Destroy(); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [e1, e2, e3]
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
                print(f"    capture {name} : {shot(f'hunt2-{step.__name__}-{name}', port)}")
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
