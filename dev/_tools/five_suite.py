"""Cinq joueurs : host + 4 clients A, B, C, D (le groupe complet de l'utilisateur). PC libre seulement : cinq fenetres.

    python _tools/five_suite.py            # relance tout (mp_test --clients 4) puis les scenarios
    python _tools/five_suite.py --reuse    # sur host + 4 clients deja connectes dans la Prairie

F1  les cinq sont sur la carte de l'host : memes listes de joueurs, chacun voit les quatre autres
F2  chacun pose un objet, les quatre autres le voient a la meme case ; chacun marche, l'host et un autre le voient
F3  une minute de jeu a cinq (marcher, ramasser, poser le meme seau a tour de role) : memes nombres de carte partout
F4  les cinq se couchent : la nuit du monde passe une fois, la meme date dans les cinq jeux
F5  A et B partent a Vernis (A tient la carte, B invite), C et D restent : puis tout le monde rentre, memes nombres

Ce que le banc ne joue pas comme un joueur : memes raccourcis que les suites dont il reprend les gestes
(shared_suite.drop, resync_suite.steps/pick/put, sleep_suite.ready_for_bed/to_bed, travel_suite.move) ; les cinq jeux
tournent sur un seul PC, en dessous de la memoire qu'il faudrait : les temps de reponse ne disent rien d'une vraie partie.
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import ROOT, log, shot, state  # noqa: E402
from shared_suite import A, B, H, chara_on_map, drop, players  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, check, ev, move, on_map, scan_logs, zone_uid  # noqa: E402
import resync_suite as rs  # noqa: E402
import sleep_suite as sl  # noqa: E402

C, D = 27554, 27555
GUESTS = (A, B, C, D)
ALL = (H, A, B, C, D)
NAMES = {H: "host", A: "A", B: "B", C: "C", D: "D"}


def soon(cond, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if cond():
                return True
        except (RuntimeError, OSError, ValueError):
            pass
        time.sleep(1)
    return False


def see_all(ctx, ports):
    return all(chara_on_map(p, ctx[q]) for p in ports for q in ports if p != q)


def same_sums(ports):
    """Les memes nombres de carte dans tous ces jeux (les sacs ne sont compares que par le mod, dans son journal)."""
    got = {p: rs.sums(p)[0] for p in ports}
    return len(set(got.values())) == 1, got


def f1(ctx):
    for p in ALL:
        ctx[p] = int(ev(p, "EClass.pc.uid.ToString()"))
    five = sorted(ctx[p] for p in ALL)
    check("les cinq sont sur la carte de l'host", soon(lambda: all(zone_uid(p) == HOME for p in ALL), 60))
    for p in ALL:
        check(f"{NAMES[p]} : sa liste a les cinq joueurs ({players(p)})", soon(lambda p=p: players(p) == five, 60))
    check("chacun voit les quatre autres sur sa carte", soon(lambda: see_all(ctx, ALL), 60))


def f2(ctx):
    for p in ALL:
        uid, where = drop(p)
        others = [q for q in ALL if q != p]
        seen = soon(lambda: all(on_map(q, [uid]).get(uid) == where for q in others), 30)
        check(f"objet pose par {NAMES[p]} vu a la meme case par les quatre autres ({where})", seen)
    for i, p in enumerate(ALL):
        rs.idle(p)
        rs.steps(p)
        time.sleep(3)
        mine = rs.pos(p)
        watcher = ALL[(i + 2) % len(ALL)]
        for q in {H, watcher} - {p}:
            check(f"{NAMES[p]} marche, {NAMES[q]} le voit ou il est ({mine})",
                  soon(lambda q=q: max(abs(a - b) for a, b in zip(rs.pos(q, ctx[p]), rs.pos(p))) <= 1, 20))


def f3(ctx):
    t0 = rs.now()
    bucket, _ = rs.marker(H)
    check("le seau pose par l'host est chez les quatre autres", soon(lambda: all(bucket in on_map(p, [bucket]) for p in GUESTS), 20))
    end, turn = time.time() + 60, 0
    while time.time() < end:
        for p in ALL:
            rs.steps(p)
        time.sleep(1.5)
        port = ALL[turn % len(ALL)]
        if rs.pick(port, bucket) == "ok":
            time.sleep(1.5)
            rs.steps(port)
            time.sleep(1.0)
            rs.put(port, bucket)
        time.sleep(2.0)
        turn += 1
    for p in ALL:
        rs.idle(p)
        rs.put(p, bucket)  # celui qui le tenait encore le repose
    check(f"le seau a ete ramasse et pose {turn} fois, il est au sol dans les cinq jeux",
          soon(lambda: all(bucket in on_map(p, [bucket]) for p in ALL), 20))
    ok = soon(lambda: same_sums(ALL)[0], 30)
    for p, got in same_sums(ALL)[1].items():
        log(f"{NAMES[p]} : {got}")
    check("memes nombres de carte dans les cinq jeux apres une minute de jeu", ok)
    warned = rs.lines(t0, rs.GUEST_LINE) + rs.lines(t0, rs.HOST_LINE)
    check(f"aucun avertissement d'ecart pendant ce temps ({len(warned)})", not warned)
    for d in warned[:6]:
        print("       ", d.get("Detail") or d.get("Diff") or d.get("@mt"))


def f4(ctx):
    if not check("la regle « chacun dort pour soi » est active dans les cinq jeux", sl.own_rule(*ALL)):
        return
    for p in ALL:
        check(f"{NAMES[p]} est epuise et a un lit", sl.ready_for_bed(p, tired=True))
    time.sleep(2)
    before = {p: sl.body(p) for p in ALL}
    for p in ALL:
        sl.to_bed(p)
    for p in ALL:
        check(f"l'ecran de nuit s'ouvre chez {NAMES[p]}", soon(lambda p=p: "LayerSleep" in sl.view(p)["layers"], 40))
    for p in ALL:
        check(f"{NAMES[p]} se reveille", soon(lambda p=p: sl.up(p), 90))
    time.sleep(4)
    after = {p: sl.body(p) for p in ALL}
    hours = (after[H]["now"] - before[H]["now"]) / 60
    check(f"la date de l'host a avance d'une nuit, une seule ({hours:.1f} h, entre 3 et 19)", 3 <= hours <= 19)
    dates = {NAMES[p]: after[p]["now"] for p in ALL}
    check(f"la meme date dans les cinq jeux, a 2 minutes pres ({dates})", max(dates.values()) - min(dates.values()) <= 2)
    for p in ALL:
        gain = after[p]["hunger"] - before[p]["hunger"]
        check(f"{NAMES[p]} est repose (fatigue {after[p]['tired']}) avec une seule nuit de faim (+{gain})",
              after[p]["tired"] <= 2 and 15 <= gain <= 30)


def f5(ctx):
    move(A, VERNIS)
    check("A est seul a Vernis", soon(lambda: zone_uid(A) == VERNIS and state(A).get("awayZone"), 240))
    move(B, VERNIS)
    check("B rejoint A a Vernis, comme invite", soon(lambda: zone_uid(B) == VERNIS and state(B).get("guest"), 240))
    check("A et B se voient a Vernis", soon(lambda: see_all(ctx, (A, B)), 60))
    check("l'host, C et D se voient toujours chez l'host", soon(lambda: see_all(ctx, (H, C, D)), 30))
    uid, where = drop(B)
    check(f"objet pose par B vu par A a Vernis ({where})", soon(lambda: on_map(A, [uid]).get(uid) == where, 30))
    uid, where = drop(D)
    check(f"objet pose par D vu par l'host et C ({where})", soon(lambda: all(on_map(q, [uid]).get(uid) == where for q in (H, C)), 30))
    move(B, HOME)
    check("B est rentre chez l'host", soon(lambda: zone_uid(B) == HOME and not state(B).get("awayZone"), 240))
    move(A, HOME)
    check("A est rentre chez l'host", soon(lambda: zone_uid(A) == HOME and not state(A).get("awayZone"), 240))
    check("les cinq se voient de nouveau", soon(lambda: see_all(ctx, ALL), 90))
    for p in ALL:
        rs.idle(p)
    ok = soon(lambda: same_sums(ALL)[0], 40)
    for p, got in same_sums(ALL)[1].items():
        log(f"{NAMES[p]} : {got}")
    check("memes nombres de carte dans les cinq jeux au retour", ok)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py"), "--clients", "4"], check=True)

    ctx = {}
    steps = [f1, f2, f3, f4, f5]
    if a.only:
        wanted = a.only.split(",")
        steps = [f1] + [s for s in steps[1:] if s.__name__ in wanted]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {(step.__doc__ or '').strip()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for p in ALL:
            try:
                shot(f"five-{step.__name__}-{NAMES[p]}", p)
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
