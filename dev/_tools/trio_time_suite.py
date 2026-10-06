"""TROIS FENETRES : a ne lancer qu'avec l'accord de l'utilisateur (regle du Steam Deck : deux fenetres Elin au plus).

Le temps qu'un autre joueur fait passer change la date, pas mon personnage ni mon sac : les deux chemins que deux
fenetres ne jouent pas (time_suite.py W6 joue le joueur seul sur sa carte, dans les deux sens).

    python _tools/trio_time_suite.py            # relance tout (mp_test --clients 2) puis les scenarios
    python _tools/trio_time_suite.py --reuse    # sur host + 2 clients deja connectes dans la Prairie

R1  l'host part a Vernis : l'un des invites garde la Prairie, l'autre est son visiteur. L'host fait passer 24 heures
    par le voyage (8 fois 3 heures) : chez les deux la date a suivi ; aucun n'a joue ces heures, n'a plus faim, n'est
    mort ; la viande fraiche de chacun n'a pas vieilli (celle du visiteur : dans son jeu et dans celui qui tient la
    carte, ou son sac est compte)
R2  tous chez l'host, puis A part seul a Vernis et fait passer 24 heures : l'host et B, reste sur la carte de l'host,
    n'ont rien vecu non plus (la viande de B : dans son jeu et chez l'host)

Tolerance : celle de time_suite (40 tours au plus, faim +1 au plus ; avant la correction 960 tours).

Ce que le banc ne joue pas comme un joueur :
- le voyage est 8 fois `GameDate.AdvanceMin(180)` dans le jeu du voyageur (ce que fait chaque pas sur la carte du
  monde), sans le pas lui-meme ; l'host et A changent de carte par `pc.MoveZone`, pas a pied ;
- la viande est creee dans le sac par une commande du jeu qui simule la carte, sa fraicheur posee a zero ;
- qui garde la Prairie est decide par l'host (le premier connecte) : le banc le constate, il ne le choisit pas ;
- pas joue : une vraie nuit, le temoin (le joueur fait lui-meme passer une heure : time_suite W6), le visiteur
  affame, les sacs des compagnons, les quetes qui n'expirent plus par le saut d'un autre, un 3e invite.
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import ROOT, log, shot, state  # noqa: E402
from shared_suite import A, B, H, settled, with_host  # noqa: E402
from time_suite import age, body, date, fresh_meat, travel_day, untouched  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, check, eventually, move, scan_logs, wait, zone_uid  # noqa: E402
from trio_place_suite import host_leaves  # noqa: E402
from trio_suite import NAMES  # noqa: E402


def followed(ports, mover, d0):
    """La date de ces jeux a suivi les 24 heures du voyageur."""
    return eventually(lambda: all(date(p) - d0[p] >= 1438 and abs(date(p) - date(mover)) <= 2 for p in ports), timeout=40)


def r1(ctx):
    for p in (A, B):
        ctx[p] = state(p)["pc"]["uid"]
    heir, other = host_leaves(ctx)
    # le sac du visiteur est compte par le jeu qui tient la carte : c'est lui qui y met la viande
    meat = {heir: fresh_meat(heir), other: fresh_meat(heir, ctx[other])}
    if not check("le teneur et son visiteur ont chacun une viande fraiche, qui peut vieillir",
                 None not in meat.values() and eventually(lambda: age(other, meat[other]) == 0, timeout=15)):
        return
    d0 = {p: date(p) for p in (heir, other)}
    before = {p: body(p) for p in (heir, other)}
    travel_day(H)
    check(f"l'host voyage 24 heures : la date a suivi chez {NAMES[heir]} (+{date(heir) - d0[heir]} min) et chez "
          f"{NAMES[other]} (+{date(other) - d0[other]} min)", followed((heir, other), H, d0))
    time.sleep(3)
    untouched(heir, f"{NAMES[heir]} (tient la carte)", meat[heir], before[heir])
    untouched(other, f"{NAMES[other]} (visiteur)", meat[other], before[other], seen=(heir, ctx[other]))


def r2(ctx):
    for p in (A, B):
        ctx.setdefault(p, state(p)["pc"]["uid"])
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    with_host(A, B)
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis", timeout=180)
    time.sleep(3)
    meat = {H: fresh_meat(H), B: fresh_meat(H, ctx[B])}
    if not check("l'host et B, sur la carte de l'host, ont chacun une viande fraiche, qui peut vieillir",
                 None not in meat.values() and eventually(lambda: age(B, meat[B]) == 0, timeout=15)):
        return
    d0 = {p: date(p) for p in (H, B)}
    before = {p: body(p) for p in (H, B)}
    travel_day(A)
    check(f"A voyage 24 heures : la date a suivi chez l'host (+{date(H) - d0[H]} min) et chez B (+{date(B) - d0[B]} min)",
          followed((H, B), A, d0))
    time.sleep(3)
    untouched(H, "l'host", meat[H], before[H])
    untouched(B, "B (sur la carte de l'host)", meat[B], before[B], seen=(H, ctx[B]))


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
    steps = [r1, r2]
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

    try:
        move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
        with_host(A, B)
    except Exception as ex:  # noqa: BLE001
        print(f"    retour a la Prairie rate : {type(ex).__name__}: {ex}")

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
