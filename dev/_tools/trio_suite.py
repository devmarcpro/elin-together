"""Trois joueurs dans une meme zone partagee (parite, etape 2) : host + 3 clients A, B, C.

    python _tools/trio_suite.py            # relance tout (mp_test --clients 3) puis les scenarios
    python _tools/trio_suite.py --reuse    # sur host + 3 clients deja connectes dans la Prairie

T1  A part seul a Vernis, B puis C le rejoignent : les trois se voient
T2  C pose un objet, vu par A (hote de zone) et par B (relais) ; B bouge, C le voit
T3  A rentre : un des invites reprend Vernis, l'autre rejoint sa session de zone
T4  l'host arrive a Vernis : rappel de l'hote de zone et de son invite, tout le monde avec l'host
T5  B tient Vernis avec A et C invites, B plante : un invite reprend la zone, l'autre le rejoint
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import ROOT, log, shot, state  # noqa: E402
from shared_suite import A, B, H, chara_on_map, drop, players, settled, with_host  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, check, ev, move, on_map, scan_logs, wait, zone_uid  # noqa: E402

C = 27554
NAMES = {A: "A", B: "B", C: "C"}


def guest_of_zone(port, uid):
    return settled(port, uid, away=True, guest=True, zone_session="Client")


def zone_host(port, uid):
    """Tient la zone et heberge une session de zone (au moins un invite)."""
    st = state(port)
    return ((st.get("zone") or {}).get("uid") == uid and bool(st.get("awayZone")) and not st.get("guest")
            and st.get("zoneSession") == "Host" and st.get("connected"))


def handed_pair(first, second, uid):
    """(heritier, invite) si l'un tient la zone et que l'autre est son invite."""
    for heir, other in ((first, second), (second, first)):
        if zone_host(heir, uid) and guest_of_zone(other, uid)():
            return heir, other
    return None


def try_wait(cond, what, timeout):
    try:
        wait(cond, what, timeout=timeout, every=1.0)
        return True
    except TimeoutError:
        return False


def all_see_each_other(ctx, ports):
    """Chaque joueur voit le perso des autres sur sa carte (faux tant qu'une carte se charge)."""
    try:
        for p in ports:
            for q in ports:
                if p != q and not chara_on_map(p, ctx[q]):
                    return False
    except RuntimeError:
        return False
    return True


def t1(ctx):
    for p in (A, B, C):
        ctx[p] = state(p)["pc"]["uid"]
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis")
    move(B, VERNIS)
    wait(guest_of_zone(B, VERNIS), "B invite de A", timeout=240)
    move(C, VERNIS)
    wait(guest_of_zone(C, VERNIS), "C invite de A", timeout=240)
    time.sleep(5)
    trio = sorted(ctx[p] for p in (A, B, C))
    check("A heberge, B et C sont invites", state(A).get("zoneSession") == "Host"
          and all(state(p).get("guest") for p in (B, C)))
    check("les trois listes de joueurs ont A, B et C",
          try_wait(lambda: all(players(p) == trio for p in (A, B, C)), "listes a jour", 60))
    check("chacun voit les deux autres sur sa carte",
          try_wait(lambda: all_see_each_other(ctx, (A, B, C)), "ils se voient", 60))
    check("l'host est seul chez lui", players(H) == [1] and zone_uid(H) == HOME)
    for p in (A, B, C):
        shot(f"t1-{NAMES[p]}", p)


def t2(ctx):
    mc, mc_pos = drop(C)
    check(f"objet pose par C vu par A ({mc_pos})",
          try_wait(lambda: on_map(A, [mc]).get(mc) == mc_pos, "A voit l'objet de C", 20))
    check(f"objet pose par C vu par B, via A ({mc_pos})",
          try_wait(lambda: on_map(B, [mc]).get(mc) == mc_pos, "B voit l'objet de C", 20))
    target = ev_move_next(B)
    check(f"deplacement de B vu par C, via A ({target})",
          try_wait(lambda: chara_pos(C, ctx[B]) == target, "C voit B bouger", 20))
    ctx["mc"] = (mc, mc_pos)


def ev_move_next(port):
    return ev(port, 'var p = EClass.pc.pos.GetNearestPoint(allowChara: false, ignoreCenter: true); '
                    'EClass.pc._Move(p); p.x + "," + p.z')


def chara_pos(port, uid):
    return ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); c == null ? "" : c.pos.x + "," + c.pos.z')


def t3(ctx):
    mc, mc_pos = ctx["mc"]
    move(A, HOME)
    wait(settled(A, HOME, away=False), "A rentre chez l'host", timeout=240)

    pair = None
    try:
        pair = wait(lambda: handed_pair(B, C, VERNIS), "un invite reprend Vernis, l'autre le rejoint", timeout=120, every=2.0)
    except TimeoutError:
        pass
    check("passation a 2 invites : l'un reprend Vernis, l'autre rejoint sa session", pair is not None)
    if pair is None:
        for p in (B, C):
            shot(f"fail-t3-{NAMES[p]}", p)
        return
    heir, other = pair
    log(f"heritier : {NAMES[heir]}, invite : {NAMES[other]}")
    ctx["heir"], ctx["other"] = heir, other
    time.sleep(3)
    duo = sorted(ctx[p] for p in (heir, other))
    check(f"{NAMES[heir]} heberge la session de zone, {NAMES[other]} y est invite",
          state(heir).get("zoneSession") == "Host" and state(other).get("zoneSession") == "Client")
    # l'invite se declare des le debut de sa connexion, il charge ensuite le monde de l'heritier
    check("listes de joueurs de la zone a jour (sans A)",
          try_wait(lambda: players(heir) == duo and players(other) == duo, "listes a jour", 60))
    check(f"{NAMES[heir]} et {NAMES[other]} se voient",
          try_wait(lambda: all_see_each_other(ctx, (heir, other)), "ils se voient", 60))
    check("le perso de A n'est plus a Vernis", not chara_on_map(heir, ctx[A]) and not chara_on_map(other, ctx[A]))
    check("l'objet pose par C est toujours la chez les deux",
          on_map(heir, [mc]).get(mc) == mc_pos and on_map(other, [mc]).get(mc) == mc_pos)
    mo, mo_pos = drop(other)
    check(f"objet pose par {NAMES[other]} vu par {NAMES[heir]} dans la nouvelle session",
          try_wait(lambda: on_map(heir, [mo]).get(mo) == mo_pos, "objet vu par l'heritier", 20))
    ctx["mo"] = (mo, mo_pos)


def t4(ctx):
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=240)
    ok = try_wait(lambda: all(settled(p, VERNIS, away=False)() for p in (B, C)),
                  "B et C avec l'host a Vernis", 240)
    check("rappel a 2 joueurs : B et C a Vernis avec l'host", ok)
    time.sleep(3)
    for key in ("mc", "mo"):
        if key in ctx:
            uid, pos = ctx[key]
            check(f"l'host a Vernis a l'objet {uid} ({pos})", on_map(H, [uid]).get(uid) == pos)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    with_host(A, B, C)


def t5(ctx):
    move(B, VERNIS)
    wait(settled(B, VERNIS, away=True, guest=False), "B seul a Vernis")
    move(A, VERNIS)
    wait(guest_of_zone(A, VERNIS), "A invite de B", timeout=240)
    move(C, VERNIS)
    wait(guest_of_zone(C, VERNIS), "C invite de B", timeout=240)
    time.sleep(3)
    pid = next(h["pid"] for h in emp.live_ports() if h["port"] == B)
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    log(f"B tue (pid {pid}) pendant qu'il heberge A et C")

    pair = None
    try:
        pair = wait(lambda: handed_pair(A, C, VERNIS), "un invite reprend Vernis apres le plantage", timeout=150, every=2.0)
    except TimeoutError:
        pass
    check("plantage de l'hote de zone a 2 invites : l'un reprend, l'autre le rejoint", pair is not None)
    if pair is None:
        return
    heir, other = pair
    log(f"heritier : {NAMES[heir]}, invite : {NAMES[other]}")
    time.sleep(3)
    check(f"{NAMES[heir]} et {NAMES[other]} se voient apres le plantage",
          try_wait(lambda: all_see_each_other(ctx, (heir, other)), "ils se voient", 60))
    move(other, HOME)
    wait(settled(other, HOME, away=False), f"{NAMES[other]} rentre", timeout=240)
    move(heir, HOME)
    wait(settled(heir, HOME, away=False), f"{NAMES[heir]} rentre", timeout=240)
    check("les deux survivants sont rentres chez l'host",
          try_wait(lambda: sorted(players(H)) == sorted([1, ctx[A], ctx[C]]), "A et C chez l'host", 60))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py"), "--clients", "3"], check=True)

    ctx = {}
    steps = [t1, t2, t3, t4, t5]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A), ("B", B), ("C", C)):
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
