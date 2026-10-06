"""TROIS FENETRES : a ne lancer qu'avec l'accord de l'utilisateur (regle du Steam Deck : deux fenetres Elin au plus).

« Chacun dort pour soi » a trois (conseil 10, point iii ; plan : dev/PLAN_nuit_chacun_pour_soi.md) : la date du monde
n'avance d'une nuit que lorsque TOUS les joueurs dorment en meme temps. Deux fenetres ne peuvent pas jouer « deux
dorment, un troisieme non » (sleep_suite.py N1 a N4 jouent un dormeur, puis les deux).

    python _tools/trio_sleep_suite.py            # relance tout (mp_test --clients 2) puis les scenarios
    python _tools/trio_sleep_suite.py --reuse    # sur host + 2 clients deja connectes dans la Prairie

Q1  A et B se couchent, l'host marche : A et B se reveillent seuls, reposes ; la date des trois jeux n'a pas saute ;
    l'host n'a ni dormi ni eu faim en plus
Q2  les trois se couchent (l'host, puis A, puis B) : la date avance d'une nuit, une seule, dans les trois jeux
Q3  cartes differentes : A part seul a Vernis. L'host et B se couchent sans lui : pas de saut. Puis A se couche la-bas,
    B et l'host aussitot apres : la nuit passe chez l'host et B, et la date de A la rejoint

Ce que le banc ne joue pas comme un joueur :
- fatigue, faim et endurance de depart sont posees par eval, le lit est cree dans le sac par l'host ;
- on se couche par l'action « Dormir » de la barre (pas par le clic) ; celui qui marche fait un pas par seconde ;
- A change de carte par `pc.MoveZone`, pas a pied ;
- les textes a l'ecran (« A dort (1 sur 3) », « Tout le monde dort ») ne sont pas lus ; les compagnons ne sont pas
  regardes ; pas joue : un joueur mort, un joueur qui se deconnecte endormi, le visiteur d'un autre invite.
- Q3 est le chemin le moins sur : un joueur absent ne recoit de l'host ni « tout le monde dort » ni son reveil (voir
  le plan, ligne manquante dans ElinNetClientTravel.cs) ; sa nuit finit seule et sa date rattrape celle du monde.
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import ROOT, log, shot  # noqa: E402
from shared_suite import A, B, H, settled, with_host  # noqa: E402
from sleep_suite import STEP, awake, body, own_rule, ready_for_bed, to_bed, up, view  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, check, ev, eventually, move, scan_logs, wait, zone_uid  # noqa: E402

WHO = {H: "l'host", A: "A", B: "B"}


def rested(port, before, after):
    gain = after[port]["hunger"] - before[port]["hunger"]
    check(f"{WHO[port]} est repose (fatigue {after[port]['tired']}) et n'a eu qu'une nuit de faim (+{gain})",
          after[port]["tired"] <= 2 and 18 <= gain <= 26)


def q1(ctx):
    if not check("la regle « chacun dort pour soi » est active dans les trois jeux", own_rule(H, A, B)):
        return
    ready_for_bed(H, tired=False)
    for p in (A, B):
        check(f"{WHO[p]} est epuise et a un lit dans son sac", ready_for_bed(p, tired=True))
    time.sleep(2)
    before = {p: body(p) for p in (H, A, B)}
    t0 = time.time()
    to_bed(A)
    to_bed(B)
    check("A et B s'endorment tout de suite", eventually(lambda: body(A)["asleep"] and body(B)["asleep"], timeout=10))
    woke, dozed = None, False
    while time.time() - t0 < 60:
        ev(H, STEP)
        dozed = dozed or not up(H)
        if up(A) and up(B):
            woke = time.time() - t0
            break
        time.sleep(1)
    check(f"A et B se reveillent seuls en moins de 25 secondes ({'jamais' if woke is None else f'{woke:.0f} s'})",
          woke is not None and woke < 25)
    time.sleep(3)
    after = {p: body(p) for p in (H, A, B)}
    log(" ; ".join(f"{WHO[p]} : {before[p]} -> {after[p]}" for p in (H, A, B)))
    for p in (A, B):
        rested(p, before, after)
    for p in (H, A, B):
        moved = after[p]["now"] - before[p]["now"]
        check(f"deux dorment, un marche : la date du jeu de {WHO[p]} n'a pas saute (+{moved} min, moins de 30)", 0 <= moved < 30)
    gain = after[H]["hunger"] - before[H]["hunger"]
    check(f"l'host n'a jamais dormi, n'a pas eu faim en plus (+{gain}), n'a pas ete repose de force",
          not dozed and up(H) and gain <= 3 and after[H]["tired"] >= before[H]["tired"])


def night_passed(ports, before, what):
    """La date de ces jeux a avance d'une nuit (le jeu la tire entre 4 et 18 heures), une seule, la meme partout."""
    after = {p: body(p) for p in ports}
    for p in ports:
        moved = after[p]["now"] - before[p]["now"]
        check(f"{what} : chez {WHO[p]} la date a avance d'une nuit, une seule ({moved // 60} h {moved % 60} min)",
              180 <= moved <= 19 * 60)
    check(f"{what} : la meme date partout ({[after[p]['now'] for p in ports]})",
          max(after[p]["now"] for p in ports) - min(after[p]["now"] for p in ports) <= 15)
    return after


def q2(ctx):
    if not check("la regle « chacun dort pour soi » est active dans les trois jeux", own_rule(H, A, B)):
        return
    check("tout le monde est debout", eventually(lambda: all(up(p) for p in (H, A, B)), timeout=60))
    for p in (H, A, B):
        check(f"{WHO[p]} est epuise et a un lit dans son sac", ready_for_bed(p, tired=True))
    time.sleep(2)
    before = {p: body(p) for p in (H, A, B)}
    for p in (H, A, B):
        to_bed(p)
    for p in (H, A, B):
        check(f"l'ecran de nuit s'ouvre chez {WHO[p]}", eventually(lambda p=p: "LayerSleep" in view(p)["layers"], timeout=30))
    for p in (H, A, B):
        check(f"{WHO[p]} se reveille", eventually(lambda p=p: awake(p), timeout=180))
    time.sleep(3)
    after = night_passed((H, A, B), before, "les trois dorment")
    for p in (H, A, B):
        rested(p, before, after)


def q3(ctx):
    if not check("la regle « chacun dort pour soi » est active dans les trois jeux", own_rule(H, A, B)):
        return
    check("tout le monde est debout", eventually(lambda: all(up(p) for p in (H, A, B)), timeout=60))
    # le lit de A est mis dans son sac tant qu'il est chez l'host (c'est l'host qui le cree)
    ready_for_bed(A, tired=False)
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis", timeout=180)
    time.sleep(3)
    for p in (H, B):
        check(f"{WHO[p]} est epuise et a un lit dans son sac", ready_for_bed(p, tired=True))
    time.sleep(2)
    before = {p: body(p) for p in (H, A, B)}
    to_bed(H)
    to_bed(B)
    check("l'host et B s'endorment", eventually(lambda: body(H)["asleep"] and body(B)["asleep"], timeout=10))
    check("l'host et B se reveillent seuls", eventually(lambda: up(H) and up(B), timeout=60))
    time.sleep(3)
    after = {p: body(p) for p in (H, A, B)}
    for p in (H, A, B):
        moved = after[p]["now"] - before[p]["now"]
        check(f"A est ailleurs et ne dort pas : la date du jeu de {WHO[p]} n'a pas saute (+{moved} min, moins de 30)", 0 <= moved < 30)

    # A se couche la-bas, puis B, puis l'host : le dernier ferme les yeux pendant que les deux autres dorment encore
    for p in (H, A, B):
        ready_for_bed(p, tired=True)
    time.sleep(2)
    before = {p: body(p) for p in (H, A, B)}
    to_bed(A)
    check("A s'endort sur sa carte", eventually(lambda: body(A)["asleep"], timeout=10))
    to_bed(B)
    to_bed(H)
    for p in (H, B):
        check(f"l'ecran de nuit s'ouvre chez {WHO[p]}", eventually(lambda p=p: "LayerSleep" in view(p)["layers"], timeout=30))
    for p in (H, A, B):
        check(f"{WHO[p]} se reveille", eventually(lambda p=p: awake(p), timeout=180))
    time.sleep(3)
    night_passed((H, B), before, "tous dorment, sur deux cartes")
    check(f"la date de A, sur sa carte, rejoint celle du monde ({body(A)['now']} / {body(H)['now']})",
          eventually(lambda: abs(body(A)["now"] - body(H)["now"]) <= 15, timeout=40))
    a = body(A)
    check(f"A est repose (fatigue {a['tired']}) et n'a eu qu'une nuit de faim (+{a['hunger'] - before[A]['hunger']})",
          a["tired"] <= 2 and 18 <= a["hunger"] - before[A]["hunger"] <= 26)


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
    steps = [q1, q2, q3]
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
