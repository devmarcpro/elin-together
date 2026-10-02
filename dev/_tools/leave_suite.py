"""L'hote change de carte : les joueurs restent (voyage independant). Test court, sur des instances deja lancees.

    python _tools/mp_test.py             # une fois : host + 1 client dans la Prairie
    python _tools/leave_suite.py         # 2 a 3 minutes, relancable (finit avec tout le monde a la Prairie)

L1  l'host part a Vernis : A reste a la Prairie et la garde, sans rechargement ; l'host est seul a Vernis
L2  A pose un objet ; l'host revient : A le rejoint, l'objet est la
L3  l'host repart, A prend la meme sortie : A rejoint l'host a Vernis
L4  option decochee : l'host change de carte, A est emmene (comme avant)
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from combat_suite import set_option  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, marker, move,  # noqa: E402
                          on_map, players, scan_logs, wait, zone_uid)

H, A = 27551, 27552


def pc_id(port):
    """Change si le jeu a ete recharge (le perso est un nouvel objet apres un rechargement)."""
    return ev(port, 'EClass.pc.GetHashCode().ToString()')


def pc_pos(port):
    s = state(port)["pc"]
    return s["x"], s["z"]


def on_map_chara(port, uid):
    return ev(port, f'EClass._map.charas.Any(c => c.uid == {uid}).ToString()') == "True"


def host_leaves(ctx, dest):
    """L'host change de carte, A doit rester ou il est."""
    before = {"zone": zone_uid(A), "pos": pc_pos(A), "id": pc_id(A)}
    move(H, dest)
    wait(lambda: zone_uid(H) == dest, "host arrive", timeout=180)
    stayed = eventually(client_settled(A, before["zone"], True), timeout=30)
    return before, stayed


def l1(ctx):
    ctx["a"] = state(A)["pc"]["uid"]
    before, stayed = host_leaves(ctx, VERNIS)
    check("l'host part a Vernis : A reste a la Prairie, a son compte", stayed and not state(A).get("guest"))
    check("A n'a pas bouge et n'a pas ete recharge", pc_pos(A) == before["pos"] and pc_id(A) == before["id"])
    check("chez A : le perso de l'host n'est plus sur la carte", not on_map_chara(A, 1))
    check("l'host est seul a Vernis (A n'a pas ete emmene)", players(H) == 1 and not on_map_chara(H, ctx["a"]))
    shot("l1-A", A)


def l2(ctx):
    m, pos = marker(A)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    both_joined(H, A, HOME)
    check("l'host revient a la Prairie : A est avec lui", not state(A).get("awayZone") and on_map_chara(H, ctx["a"]))
    check(f"l'host retrouve l'objet pose par A pendant son absence ({pos})", on_map(H, [m]).get(m) == pos)


def l3(ctx):
    _, stayed = host_leaves(ctx, VERNIS)
    check("l'host repart : A reste encore", stayed)
    move(A, VERNIS)
    joined = eventually(client_settled(A, VERNIS, False), timeout=120)
    check("A prend la meme sortie : il rejoint l'host a Vernis", joined and eventually(lambda: players(H) == 2, timeout=30))


def l4(ctx):
    set_option("IndependentTravel", False)
    time.sleep(2)
    try:
        move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
        followed = eventually(client_settled(A, HOME, False), timeout=120)
        check("option decochee : A est emmene avec l'host, comme avant", followed and eventually(lambda: players(H) == 2, timeout=30))
    finally:
        set_option("IndependentTravel", True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {}
    steps = [l1, l2, l3, l4]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A)):
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
