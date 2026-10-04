"""Une seule date pour le monde. Test court (host + 1 client a la Prairie), finit a la Prairie.

    python _tools/mp_test.py
    python _tools/time_suite.py       # ~4 minutes

Premiere marche du serveur "depot de sauvegarde" (PLAN_serveur_depot.md) : la date n'appartient plus a l'host.
Avant : seul l'host faisait avancer la date ; un invite seul sur sa carte avait la sienne, puis reprenait celle de
l'host en rentrant. Maintenant la date la plus avancee est celle du monde.

W1  l'invite part seul a Vernis et y passe du temps (il marche) : la date de l'host avance avec la sienne
W2  l'host passe du temps chez lui : la date de l'invite, toujours a Vernis, avance avec la sienne
W3  l'invite passe cinq heures d'un coup (ce que fait une nuit : GameDate.AdvanceMin) : l'host fait le meme saut,
    et les heures passent chez lui (son personnage a plus faim)
W4  l'invite rentre : sa date ne saute pas, les deux jeux ont la meme
W5  case decochee : l'ancien comportement, l'host n'avance plus avec l'invite
"""
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from combat_suite import set_option  # noqa: E402
import move_suite  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually,  # noqa: E402
                          move, scan_logs, wait)

H, A = 27551, 27552
DATE = 'EClass.world.date.GetRaw().ToString()'
def date(port):
    return int(ev(port, DATE))


def spend(port, minutes, timeout=150):
    """Le joueur marche pour de bon (des allers de 14 cases) jusqu'a ce que sa date ait avance d'autant.
    Renvoie les minutes passees."""
    start, end = date(port), time.time() + timeout
    while date(port) - start < minutes and time.time() < end:
        move_suite.walk(port)
        move_suite.back(port)
    return date(port) - start


def gap():
    return date(A) - date(H)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    has_option = True
    try:
        for port in (H, A):
            dismiss_dialogs(port)
        try:
            # TIME_OFF=1 : W1 a W4 avec la case decochee, pour voir l'ancien comportement echouer
            set_option("SharedWorldTime", not os.environ.get("TIME_OFF"))
        except Exception as ex:  # noqa: BLE001
            has_option = False
            log(f"case SharedWorldTime absente de ce build ({type(ex).__name__})")
        time.sleep(2)

        log("--- W1")
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
        time.sleep(3)
        dismiss_dialogs(A)
        log(f"au depart : host {date(H)}, invite {date(A)} (ecart {gap()} min)")
        check(f"au depart les deux jeux ont la meme date (ecart {gap()} min)", abs(gap()) <= 2)
        h0 = date(H)
        spent = spend(A, 20)
        log(f"l'invite a passe {spent} min a Vernis ; host {date(H)} (+{date(H) - h0}), invite {date(A)}")
        check(f"l'invite passe du temps seul a Vernis ({spent} min)", spent >= 20)
        check(f"la date de l'host avance avec la sienne (host +{date(H) - h0} min)",
              eventually(lambda: abs(gap()) <= 2, timeout=10) and date(H) - h0 >= 18)

        log("--- W2")
        a0 = date(A)
        spent = spend(H, 20)
        log(f"l'host a passe {spent} min chez lui ; host {date(H)}, invite {date(A)} (+{date(A) - a0})")
        check(f"l'host passe du temps chez lui ({spent} min)", spent >= 20)
        check(f"la date de l'invite, a Vernis, avance avec la sienne (invite +{date(A) - a0} min)",
              eventually(lambda: abs(gap()) <= 2, timeout=10) and date(A) - a0 >= 18)

        log("--- W3")
        h0 = date(H)
        hunger = int(ev(H, 'EClass.pc.hunger.value.ToString()'))
        hour = ev(H, 'EClass.world.date.hour.ToString()')
        ev(A, 'EClass.world.date.AdvanceMin(300); "ok"')
        jumped = eventually(lambda: date(H) - h0 >= 295, timeout=20)
        log(f"l'invite passe 5 heures : host +{date(H) - h0} min, heure {hour} -> {ev(H, 'EClass.world.date.hour.ToString()')}, "
            f"faim de l'host {hunger} -> {ev(H, 'EClass.pc.hunger.value.ToString()')}")
        check(f"l'invite passe cinq heures d'un coup : l'host fait le meme saut (+{date(H) - h0} min)", jumped and abs(gap()) <= 2)
        check("les heures sont passees chez l'host (son personnage a plus faim)",
              int(ev(H, 'EClass.pc.hunger.value.ToString()')) > hunger)

        log("--- W4")
        before = date(A)
        move(A, HOME)
        both_joined(H, A, HOME)
        time.sleep(4)
        dismiss_dialogs(A)
        log(f"retour : invite {before} -> {date(A)}, host {date(H)}")
        check(f"l'invite rentre : sa date ne saute pas ({date(A) - before:+d} min)", -2 <= date(A) - before <= 10)
        check(f"les deux jeux ont la meme date (ecart {gap()} min)", eventually(lambda: abs(gap()) <= 2, timeout=10))

        log("--- W5")
        if has_option:
            set_option("SharedWorldTime", False)
            time.sleep(3)
            try:
                move(A, VERNIS)
                wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
                time.sleep(3)
                dismiss_dialogs(A)
                h0 = date(H)
                spent = spend(A, 20)
                time.sleep(3)
                log(f"case decochee : l'invite a passe {spent} min, host +{date(H) - h0}")
                check(f"case decochee : l'host n'avance plus avec l'invite (host +{date(H) - h0} min pour {spent})",
                      spent >= 20 and date(H) - h0 <= 2)
                move(A, HOME)
                both_joined(H, A, HOME)
                time.sleep(4)
                dismiss_dialogs(A)
            finally:
                set_option("SharedWorldTime", True)
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-time-{name}', port)}")
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
