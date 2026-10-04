"""Ce que le temps fait au monde n'arrive qu'une fois. Test court (host + 1 client a la Prairie), finit a la Prairie.

    python _tools/mp_test.py
    python _tools/world_suite.py      # ~4 minutes

Deuxieme marche du serveur "depot de sauvegarde" (PLAN_serveur_depot.md) : le gardien du monde. Chaque jeu qui
simule une carte fait avancer la date dans sa copie du monde (l'host, et un joueur seul sur une carte qu'il tient).
Avant, chacun y faisait aussi ce qu'une heure, un jour ou un mois fait au MONDE : chaque copie tirait sa meteo,
l'impot du mois et le salaire etaient comptes dans chaque copie, une quete expirait deux fois.

K1  l'invite, seul a Vernis, passe 30 heures : les deux jeux ont la meme meteo (celle du gardien) et les memes
    previsions
K2  l'invite passe la fin du mois : l'impot et le salaire ne sont comptes que chez le gardien (une facture de plus
    chez l'host, aucune dans la copie de l'invite, aucun colis fabrique chez l'invite)
K3  il rentre : la meteo est toujours la meme dans les deux jeux
K4  case decochee : l'ancien comportement, la copie de l'invite compte aussi sa fin de mois

TIME_OFF-like : WORLD_OFF=1 joue K1 a K3 avec la case decochee, pour voir l'ancien comportement echouer.
"""
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from combat_suite import set_option  # noqa: E402
from mp_test import log, shot  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually,  # noqa: E402
                          move, scan_logs, wait)

H, A = 27551, 27552
DATE = 'EClass.world.date.GetRaw().ToString()'
WEATHER = ('var w = EClass.world.weather; return (int)w._currentCondition + "/" + w.duration + "/" + '
           'string.Join(",", w.forecasts.Select(f => (int)f.condition + ":" + f.duration));')
MONTH = 'EClass.world.date.month.ToString()'
BILLS = 'EClass.player.taxBills.ToString()'
PARCELS = 'EClass.game.cards.listPackage.Count.ToString()'


def date(port):
    return int(ev(port, DATE))


def jump(port, minutes):
    """Le joueur fait passer ce temps d'un coup (ce que fait une nuit : GameDate.AdvanceMin), l'autre jeu suit."""
    other = H if port == A else A
    target = date(port) + minutes
    ev(port, f'EClass.world.date.AdvanceMin({minutes}); "ok"', timeout=300)
    if not eventually(lambda: abs(date(other) - target) <= 2, timeout=60):
        raise RuntimeError(f"l'autre jeu n'a pas suivi : {date(other)} au lieu de {target}")


def away():
    move(A, VERNIS)
    wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
    time.sleep(3)
    dismiss_dialogs(A)


def home():
    move(A, HOME)
    both_joined(H, A, HOME)
    time.sleep(4)
    dismiss_dialogs(A)


def cross_month():
    """L'invite avance par bonds jusqu'au mois suivant. Renvoie (factures host, factures invite, colis invite) gagnes."""
    before = int(ev(H, BILLS)), int(ev(A, BILLS)), int(ev(A, PARCELS))
    month = ev(A, MONTH)
    for _ in range(4):
        if ev(A, MONTH) != month:
            break
        jump(A, 20000)
    time.sleep(3)
    after = int(ev(H, BILLS)), int(ev(A, BILLS)), int(ev(A, PARCELS))
    log(f"mois {month} -> {ev(A, MONTH)} (host {ev(H, MONTH)}) ; factures host {before[0]} -> {after[0]}, "
        f"invite {before[1]} -> {after[1]} ; colis chez l'invite {before[2]} -> {after[2]}")
    return tuple(a - b for a, b in zip(after, before))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    has_option = True
    try:
        for port in (H, A):
            dismiss_dialogs(port)
        set_option("SharedWorldTime", True)
        try:
            set_option("WorldKeeper", not os.environ.get("WORLD_OFF"))
        except Exception as ex:  # noqa: BLE001
            has_option = False
            log(f"case WorldKeeper absente de ce build ({type(ex).__name__})")
        time.sleep(2)

        log("--- K1")
        away()
        jump(A, 1800)
        same = eventually(lambda: ev(H, WEATHER) == ev(A, WEATHER), timeout=15)
        log(f"meteo host   : {ev(H, WEATHER)}")
        log(f"meteo invite : {ev(A, WEATHER)}")
        check("apres 30 heures passees par l'invite seul a Vernis, les deux jeux ont la meme meteo et les memes previsions", same)

        log("--- K2")
        host, guest, parcels = cross_month()
        check(f"la fin du mois est comptee chez le gardien (factures de l'host : +{host})", host == 1)
        check(f"et pas dans la copie de l'invite (factures : +{guest}, colis fabriques : +{parcels})", guest == 0 and parcels == 0)
        check("la meteo est toujours la meme dans les deux jeux", eventually(lambda: ev(H, WEATHER) == ev(A, WEATHER), timeout=15))

        log("--- K3")
        home()
        check("l'invite rentre : meme date, meme meteo",
              eventually(lambda: abs(date(A) - date(H)) <= 2 and ev(H, WEATHER) == ev(A, WEATHER), timeout=15))

        log("--- K4")
        if has_option and not os.environ.get("WORLD_OFF"):
            set_option("WorldKeeper", False)
            time.sleep(3)
            try:
                away()
                host, guest, parcels = cross_month()
                check(f"case decochee : la copie de l'invite compte aussi sa fin de mois (factures : +{guest})", guest >= 1)
                home()
            finally:
                set_option("WorldKeeper", True)
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-world-{name}', port)}")
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
