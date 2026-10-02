"""Ce qui n'appartenait qu'a l'host : affinite des habitants, guildes. Test court (host + 1 client deja lances).

    python _tools/mp_test.py
    python _tools/parity_suite.py     # ~1 minute

Y1  A se fait apprecier d'un habitant : la meme valeur chez l'host ; l'host la fait baisser : la meme chez A
Y2  A rejoint une guilde et monte en grade : l'host est membre au meme grade ; la contribution suit
Y3  le personnage de A tue un habitant : A perd 5 de karma, pas l'host ; l'host en tue un : l'host seul en perd
Y4  A devient criminel : les gardes de l'host en ont apres A, pas apres l'host ; A se rachete : plus personne
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552


def affinity(port, uid):
    return int(ev(port, f'EClass._map.charas.Find(c => c.uid == {uid})._affinity.ToString()'))


def guild(port):
    return ev(port, 'var r = Guild.Fighter.relation; return (int)r.type + "/" + r.rank + "/" + r.exp;')


def karma(port):
    return int(ev(port, "EClass.player.karma.ToString()"))


def spawn(what):
    """L'host fait apparaitre pres de lui un habitant humain amical, ou un garde ; renvoie son numero."""
    if what == "guard":
        make = 'var c = CharaGen.Create("guard");'
    else:
        make = ('Chara c = null; foreach (var r in EClass.sources.charas.rows.Where(r => r.hostility == "Friend" && r.quality == 0)) '
                '{ var x = CharaGen.Create(r.id); if (x.IsHuman && !(x.trait is TraitGuard) && !(x.trait is TraitMerchantTravel)) { c = x; break; } }')
    return int(ev(H, make + ' EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(false, false)); return c.uid.ToString();'))


def hostile(guard, target):
    return ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {guard}); var t = EClass._map.charas.Find(x => x.uid == {target}); '
                 'return g.IsHostile(t).ToString();') == "True"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        log("--- Y1")
        npc = int(ev(H, 'EClass._map.charas.Find(c => !c.IsPC && !c.GetBool("remote_chara") && c.trait.CanChangeAffinity).uid.ToString()'))
        before = affinity(H, npc)
        ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {npc}); for (var i = 0; i < 6; i++) c.ModAffinity(EClass.pc, 5, false); "ok"')
        time.sleep(1)
        mine = affinity(A, npc)
        check(f"A se fait apprecier d'un habitant ({before} -> {mine})", mine != before)
        check("la meme valeur chez l'host", eventually(lambda: affinity(H, npc) == affinity(A, npc), timeout=10))
        ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {npc}); c.ModAffinity(EClass.pc, -7, false); "ok"')
        check("l'host la fait baisser : la meme valeur chez A",
              eventually(lambda: affinity(A, npc) == affinity(H, npc) and affinity(H, npc) != mine, timeout=10))

        log("--- Y2")
        ev(A, 'var r = Guild.Fighter.relation; r.type = FactionRelation.RelationType.Member; r.rank = 2; "ok"')
        check("A rejoint la guilde des guerriers au grade 2 : l'host aussi", eventually(lambda: guild(H).startswith("1/2/") or guild(H) == guild(A), timeout=10))
        ev(H, 'Guild.Fighter.AddContribution(50); "ok"')
        check("la contribution de l'host arrive chez A", eventually(lambda: guild(A) == guild(H) and guild(H).endswith("/50"), timeout=10))

        log("--- Y3")
        a, h = state(A)["pc"]["uid"], state(H)["pc"]["uid"]
        if ev(H, 'ElinTogether.Net.NetSession.Instance.Rules.UsePersonalQuests.ToString()') != "True":
            log("karma par joueur : option des quetes par joueur decochee, Y3 et Y4 sautes")
        else:
            ka, kh = karma(A), karma(H)
            victim = spawn("citizen")
            time.sleep(2)
            ev(H, f'var v = EClass._map.charas.Find(x => x.uid == {victim}); v.Die(null, EClass._map.charas.Find(x => x.uid == {a})); "ok"')
            check(f"le personnage de A tue un habitant : A perd 5 de karma ({ka} -> {ka - 5})", eventually(lambda: karma(A) == ka - 5, timeout=10))
            check("l'host n'en perd pas", karma(H) == kh)
            victim = spawn("citizen")
            time.sleep(2)
            ev(H, f'var v = EClass._map.charas.Find(x => x.uid == {victim}); v.Die(null, EClass.pc); "ok"')
            check("l'host tue un habitant : l'host perd 5 de karma", eventually(lambda: karma(H) == kh - 5, timeout=10))
            time.sleep(2)
            check("A n'en perd pas davantage", karma(A) == ka - 5)

            log("--- Y4")
            guard = spawn("guard")
            time.sleep(2)
            check("personne n'est criminel : le garde n'en a apres personne", not hostile(guard, a) and not hostile(guard, h))
            down = karma(A) + 15
            ev(A, f'EClass.player.ModKarma(-{down}); "ok"')
            check("A devient criminel : le garde de l'host en a apres A", eventually(lambda: hostile(guard, a), timeout=10))
            check("pas apres l'host, qui n'est pas criminel chez lui",
                  not hostile(guard, h) and ev(H, "EClass.player.IsCriminal.ToString()") == "False")
            ev(A, f'EClass.player.ModKarma({down}); "ok"')
            check("A se rachete : le garde n'en a plus apres A", eventually(lambda: not hostile(guard, a), timeout=10))
            ev(H, f'EClass.player.ModKarma({kh} - EClass.player.karma); foreach (var c in EClass._map.charas.Where(x => x.uid == {guard}).ToList()) c.Destroy(); "ok"')
            ev(A, f'EClass.player.ModKarma({ka} - EClass.player.karma); "ok"')
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {ex}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-parity-{name}', port)}")
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
