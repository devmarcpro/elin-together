"""Compagnons dans les zones partagees (parite, etape 3) : host + 2 clients A, B.

    python _tools/party_suite.py            # relance tout (mp_test --clients 2) puis les scenarios
    python _tools/party_suite.py --reuse    # sur host + 2 clients deja connectes dans la Prairie

P1  A et B recrutent chacun un compagnon (Ka, Kb) chez l'host
P2  A part seul a Vernis avec Ka, B le rejoint avec Kb : chacun suit son proprietaire chez A
P3  checkpoint de A : l'host a Kb a jour (objet donne par A, qui simule la zone)
P4  B rentre : Kb revient avec lui chez l'host, avec l'objet ; Ka reste a Vernis avec A
P5  B rejoint A, A rentre : B reprend Vernis avec Kb, Ka part avec A
P6  l'host arrive a Vernis : rappel de B, tout le monde a Vernis avec son compagnon a cote
P7  A recrute un compagnon en voyage seul : il revient avec lui chez l'host
P8  A renvoie ce compagnon en voyage seul : l'host ne le ramene pas
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from companion_suite import SPECIES, alive, dist, info, recruit, walk_away  # noqa: E402
from mp_test import ROOT, log, shot, state  # noqa: E402
from shared_suite import A, B, H, holder, settled, with_host  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, check, ev, eventually, move, scan_logs, wait, zone_uid  # noqa: E402

NAMES = {A: "A", B: "B"}


def near(port, comp, owner, d=4):
    return 0 <= dist(port, comp, owner) <= d


def p1(ctx):
    ctx["a"], ctx["b"] = state(A)["pc"]["uid"], state(B)["pc"]["uid"]
    ctx["ka"] = recruit(A, ctx["a"])
    ctx["kb"] = recruit(B, ctx["b"])
    log(f"Ka = {ctx['ka']}, Kb = {ctx['kb']}")
    check("host : Ka a A, Kb a B",
          eventually(lambda: (info(H, ctx["ka"]) or (0, "", 0, 0))[2] == ctx["a"]
                     and (info(H, ctx["kb"]) or (0, "", 0, 0))[2] == ctx["b"]))


def p2(ctx):
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis")
    move(B, VERNIS)
    wait(settled(B, VERNIS, away=True, guest=True, zone_session="Client"), "B invite de A", timeout=240)
    time.sleep(5)
    check("chez A : Ka a cote de A", eventually(lambda: near(A, ctx["ka"], ctx["a"])))
    check("chez A : Kb est venu avec B, a cote de lui", eventually(lambda: near(A, ctx["kb"], ctx["b"])))
    check("chez B : Ka et Kb sont la", eventually(lambda: dist(B, ctx["ka"], ctx["a"]) >= 0 and dist(B, ctx["kb"], ctx["b"]) >= 0))
    walk_away(B, dx=-8)
    check("chez A : Kb suit B", eventually(lambda: near(A, ctx["kb"], ctx["b"], 3), timeout=30))
    check("chez A : Ka reste avec A", near(A, ctx["ka"], ctx["a"]))
    i = info(H, ctx["kb"])
    check("host : Kb hors de sa carte pendant que B est chez A", i is not None and i[1] == "")
    shot("p2-A", A)
    shot("p2-B", B)


def p3(ctx):
    gift = int(ev(A, f'var t = ThingGen.Create("bucket"); EClass.game.cards.globalCharas.Find({ctx["kb"]}).AddThing(t); t.uid.ToString()'))
    ctx["gift"] = gift
    ev(A, 'HarmonyLib.Traverse.Create(ElinTogether.Net.NetSession.Instance.Transport).Method("SendTravelCheckpoint").GetValue(); "ok"')
    check("checkpoint de A : l'host a Kb a jour",
          eventually(lambda: ev(H, f'(EClass.game.cards.globalCharas.Find({ctx["kb"]}).things.Find({gift}) != null).ToString()') == "True"))


def p4(ctx):
    move(B, HOME)
    with_host(B)
    check("B rentre : Kb revient a cote de lui chez l'host", eventually(lambda: near(H, ctx["kb"], ctx["b"]), timeout=30))
    check("Kb a toujours l'objet donne chez A",
          ev(H, f'(EClass.game.cards.globalCharas.Find({ctx["kb"]}).things.Find({ctx["gift"]}) != null).ToString()') == "True")
    i = info(H, ctx["kb"])
    check("host : Kb une seule fois dans le groupe, a B", i is not None and i[3] == 1 and i[2] == ctx["b"])
    time.sleep(5)
    check("host : 5 s plus tard, Kb existe toujours", alive(H, ctx["kb"]))
    check("chez A : Kb est parti avec B, Ka est toujours la",
          eventually(lambda: dist(A, ctx["kb"], ctx["a"]) < 0 and near(A, ctx["ka"], ctx["a"])))


def p5(ctx):
    move(B, VERNIS)
    wait(settled(B, VERNIS, away=True, guest=True, zone_session="Client"), "B invite de A", timeout=240)
    time.sleep(3)
    check("B revient chez A : Kb aussi", eventually(lambda: near(A, ctx["kb"], ctx["b"])))
    move(A, HOME)
    wait(settled(A, HOME, away=False), "A rentre", timeout=240)
    ok = eventually(holder(B, VERNIS), timeout=60)
    check("passation : B tient Vernis", ok)
    check("passation : Kb toujours a cote de B, Ka parti avec A",
          eventually(lambda: near(B, ctx["kb"], ctx["b"]) and dist(B, ctx["ka"], ctx["b"]) < 0))
    check("host : Ka revenu a cote de A", eventually(lambda: near(H, ctx["ka"], ctx["a"]), timeout=30))


def p6(ctx):
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=240)
    # A etait avec l'host a la Prairie : il y reste, et rejoint l'host de lui-meme
    time.sleep(3)
    if zone_uid(A) != VERNIS:
        move(A, VERNIS)
    wait(lambda: all(settled(p, VERNIS, away=False)() for p in (A, B)), "A et B avec l'host a Vernis", timeout=240)
    time.sleep(3)
    check("rappel : chez l'host a Vernis, Ka a cote de A et Kb a cote de B",
          eventually(lambda: near(H, ctx["ka"], ctx["a"]) and near(H, ctx["kb"], ctx["b"]), timeout=30))
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    with_host(A, B)


def p7(ctx):
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis")
    species = next(s for s in SPECIES if ev(A, f'EClass.sources.charas.map.ContainsKey("{s}").ToString()') == "True")
    kn = int(ev(A, f'var c = CharaGen.Create("{species}"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(allowChara: false)); '
                   'c.MakeAlly(false); c.uid.ToString()'))
    ctx["kn"] = kn
    log(f"Kn = {kn} (recrute en voyage seul)")
    check("A recrute en voyage seul : Kn lui appartient", (info(A, kn) or (0, "", 0, 0))[2] == ctx["a"])
    move(A, HOME)
    wait(settled(A, HOME, away=False), "A rentre", timeout=240)
    check("host : Kn arrive avec A, dans le groupe, a A",
          eventually(lambda: near(H, kn, ctx["a"]) and (info(H, kn) or (0, "", 0, 0))[2:] == (ctx["a"], 1), timeout=30))
    check("B voit Kn chez l'host", eventually(lambda: dist(B, kn, ctx["a"]) >= 0))
    time.sleep(5)
    check("host : 5 s plus tard, Ka et Kn existent toujours", alive(H, ctx["ka"]) and alive(H, kn))


def p8(ctx):
    kn = ctx["kn"]
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis")
    time.sleep(3)
    ev(A, f'EClass.pc.party.RemoveMember(EClass.game.cards.globalCharas.Find({kn})); "ok"')
    move(A, HOME)
    wait(settled(A, HOME, away=False), "A rentre", timeout=240)
    time.sleep(5)
    i = info(H, kn)
    # renvoye, il rentre chez lui (ici sa maison est la Prairie de l'host) : plus dans le groupe, plus a personne
    check("host : Kn renvoye en voyage, plus dans le groupe, plus a A", i is not None and i[3] == 0 and i[2] == 0)
    check("A : Kn n'est plus dans son groupe", eventually(lambda: (info(A, kn) or (0, "", 0, 0))[3] == 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py"), "--clients", "2"], check=True)

    ctx = {}
    steps = [p1, p2, p3, p4, p5, p6, p7, p8]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A), ("B", B)):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', port)}")
                except Exception:  # noqa: BLE001
                    pass
            break

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
