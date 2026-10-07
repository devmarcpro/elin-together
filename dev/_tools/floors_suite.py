"""Descente de donjon a deux : combien de fois le jeu de l'invite recoit le monde entier (conseil 11).

    python _tools/mp_test.py               # une fois : host + 1 client dans la Prairie
    python _tools/floors_suite.py          # 6 a 10 minutes ; --floors 4 par defaut

Mesure de depart (journal reel du 2026-10-07, 0.26.557) : 9 copies du monde en 13 minutes de donjon, une par etage.
Cible (PLAN_conseil11_rechargements.md) : zero copie du monde pour un changement d'etage, un chargement de carte.

Pour chaque etage, a tour de role :
  « host d'abord »    l'host prend l'escalier, l'invite reste (il herite de l'etage), puis le prend a son tour
  « invite d'abord »  l'invite prend l'escalier (il tient l'etage du dessous), puis l'host le rejoint (rappel)
et on note : copies du monde recues par l'invite, secondes entre le dernier escalier et « ensemble sur l'etage »,
total des objets du sac de chacun avant et apres (rien perdu, rien en double), tache de lecture gardee ou non.

Ce que le banc ne joue pas comme un joueur : la Nefia est creee par l'host (CreateRandomSite), on y entre par la carte
du monde (EnterLocalZone) et l'escalier est pris par son action (TraitStairsDown.MoveZone) sans marcher dessus ; pas de
monstres combattus ; une seule machine, connexion locale : les secondes ne disent rien d'une vraie partie, seul le
nombre de copies se compare.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import log, state  # noqa: E402
from travel_suite import (DESCEND, HOME, LOCALLOW, RESULTS, both_joined, check, dismiss_dialogs, ev, host_goto,  # noqa: E402
                          make_nefia, scan_logs, wait, walk_in, zone_uid)

COPY_LINE = "Received save data from host"
RETURN_LINE = "Back after"
BAG = 'EClass.pc.things.List(t => true, true).Sum(t => t.Num).ToString()'


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def lines(t0, text):
    out = []
    for f in (LOCALLOW / "ElinMP" / "Logs").glob(f"Session_{datetime.now():%Y%m%d}*.log"):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if text not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("@t", "") >= t0 and text in d.get("@mt", ""):
                out.append(d)
    return out


def level(port):
    return int(ev(port, 'EClass._zone.lv.ToString()'))


def descend(port, who):
    """L'escalier descendant de la carte de ce joueur ; attend qu'il soit en jeu un etage plus bas."""
    lv = level(port)
    if not check(f"{who} : un escalier descend depuis l'etage {lv}", ev(port, DESCEND) == "ok"):
        return False

    def below():
        dismiss_dialogs(port)
        return state(port).get("sceneMode") == "Zone" and level(port) < lv

    wait(below, f"{who} sous l'etage {lv}", timeout=180)
    return True


def together(host, client):
    """Les deux sur la meme carte, l'invite client de l'host (ni seul, ni invite d'un autre)."""
    def cond():
        dismiss_dialogs(client)
        s = state(client)
        return (zone_uid(host) == zone_uid(client) and not s.get("awayZone") and s.get("connected")
                and len(state(host).get("players", [])) == 2)
    wait(cond, "ensemble sur le meme etage", timeout=240)


def step(ctx, n, order):
    host, client = ctx["host"], ctx["client"]
    first, second = (host, client) if order == "host d'abord" else (client, host)
    names = {host: "l'host", client: "l'invite"}
    bags = {p: int(ev(p, BAG)) for p in (host, client)}
    t0 = now()
    if not descend(first, f"etage {n}, {order} : {names[first]}"):
        return None
    time.sleep(4)
    if not descend(second, f"etage {n}, {order} : {names[second]}"):
        return None
    started = time.time()
    together(host, client)
    took = time.time() - started
    time.sleep(4)
    copies = len(lines(t0, COPY_LINE))
    after = {p: int(ev(p, BAG)) for p in (host, client)}
    for d in lines(t0, RETURN_LINE):
        log(f"    retour : {d.get('Seconds', 0):.0f} s d'absence, copie de {d.get('Bytes')} octets, {d.get('Skipped')} messages non pris ({d.get('Kinds')})")
    check(f"etage {n}, {order} : les deux sont ensemble sur l'etage {level(host)}", zone_uid(host) == zone_uid(client))
    check(f"etage {n}, {order} : sacs inchanges (host {bags[host]} -> {after[host]}, invite {bags[client]} -> {after[client]})",
          bags == after)
    check(f"etage {n}, {order} : aucune copie du monde pour l'invite ({copies})", copies == 0)
    return {"etage": n, "ordre": order, "copies": copies, "secondes": round(took, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--floors", type=int, default=4)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = now()

    live = emp.live_ports()
    ctx = {"host": next(h["port"] for h in live if h["role"] == "Host"),
           "client": next(h["port"] for h in live if h["role"] == "Client")}
    host, client = ctx["host"], ctx["client"]
    both_joined(host, client, HOME)
    region = int(ev(client, 'EClass._zone.ParentZone.uid.ToString()'))

    rows = []
    try:
        site = make_nefia(ctx, "donjon")
        if site:
            nefia, spot = site
            walk_in(ctx, host, region, nefia, spot)
            walk_in(ctx, client, region, nefia, spot)
            together(host, client)
            for n in range(1, a.floors + 1):
                order = "host d'abord" if n % 2 else "invite d'abord"
                log(f"--- etage {n} : {order}")
                try:
                    row = step(ctx, n, order)
                except Exception as ex:  # noqa: BLE001
                    check(f"etage {n} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
                    break
                if row is None:
                    break
                rows.append(row)
    finally:
        try:
            host_goto(host, client, HOME)
        except Exception as ex:  # noqa: BLE001
            log(f"retour a la Prairie impossible : {ex}")

    print("\nMesure :")
    for r in rows:
        print(f"    etage {r['etage']} ({r['ordre']}) : {r['copies']} copie(s) du monde, {r['secondes']} s pour etre ensemble")
    if rows:
        print(f"    total : {sum(r['copies'] for r in rows)} copie(s) du monde pour {len(rows)} etage(s)")

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
