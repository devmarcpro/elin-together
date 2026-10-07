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
import resync_suite as rs  # noqa: E402
from travel_suite import (DESCEND, HOME, UP, at_zone, enter_at, marker, on_map, LOCALLOW, RESULTS, both_joined, check, dismiss_dialogs, ev, host_goto,  # noqa: E402
                          make_nefia, scan_logs, wait, walk_in, zone_uid)

COPY_LINE = "Received save data from host"
RETURN_LINE = "Back after"
BAG = 'EClass.pc.things.List(t => true, true).Sum(t => t.Num).ToString()'
# tranche 2 (retour par la carte seule) : lignes de journal de l'invite et de l'host, et replis sur la copie du monde
SOFT_MAP_LINE = "Soft return: map {ZoneFullName} loaded"
SOFT_HOST_LINE = "Soft return to"
GIVEN_UP_LINE = "given up"
# numeros en double sur la carte et dans les sacs (les jetons de competence sont propres a chaque jeu)
DUPES = ('var u = new System.Collections.Generic.List<int>(); '
         'foreach (var t in EClass._map.things) { u.Add(t.uid); foreach (var s in t.things.List(x => !(x.trait is TraitAbility), true)) u.Add(s.uid); } '
         'foreach (var c in EClass._map.charas) { u.Add(c.uid); foreach (var s in c.things.List(x => !(x.trait is TraitAbility), true)) u.Add(s.uid); } '
         'return (u.Count - new System.Collections.Generic.HashSet<int>(u).Count).ToString();')


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


def descend(port, who, down=True):
    """L'escalier de la carte de ce joueur (descendant, ou montant quand `down` est faux : un donjon de test n'a que
    deux ou trois etages) ; attend qu'il soit en jeu sur un autre etage."""
    lv = level(port)
    took = ev(port, DESCEND if down else UP)
    if not check(f"{who} : un escalier {'descend' if down else 'monte'} depuis l'etage {lv} ({took})", took == "ok"):
        return False

    def moved():
        dismiss_dialogs(port)
        return state(port).get("sceneMode") == "Zone" and level(port) != lv

    wait(moved, f"{who} hors de l'etage {lv}", timeout=180)
    return True


def put_down(host, port):
    """Un seau pose par ce joueur : l'host cree le sien au sol ; celui de l'invite lui est donne par l'host (un
    client ne cree pas d'objet) puis pose par l'invite, comme un objet de son sac."""
    if port == host:
        return marker(host)
    me = ev(port, "EClass.pc.uid.ToString()")
    uid = int(ev(host, f'var c = EClass._map.charas.Find(x => x.uid == {me}); var t = c.AddThing(ThingGen.Create("bucket")); return t.uid.ToString();'))
    rs.eventually(lambda: ev(port, f'(EClass.pc.things.Find({uid}) != null).ToString()') == "True", timeout=15)
    rs.put(port, uid)
    rs.eventually(lambda: uid in on_map(port, [uid]), timeout=15)
    return uid, on_map(port, [uid]).get(uid)


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
    # on descend tant qu'il y a un escalier, puis on remonte : chaque passage est un changement d'etage
    down = ev(first, 'return (EClass._map.FindThing<TraitStairsDown>() != null).ToString();') == "True"
    if not descend(first, f"etage {n}, {order} : {names[first]}", down):
        return None
    time.sleep(4)
    if not descend(second, f"etage {n}, {order} : {names[second]}", down):
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
    # tranche 2 (jamais lance au moment de l'ecriture) : « host d'abord » = l'invite marche vers la carte de l'host
    by_map, told, given_up = (len(lines(t0, x)) for x in (SOFT_MAP_LINE, SOFT_HOST_LINE, GIVEN_UP_LINE))
    log(f"    retour par la carte seule : {by_map} chez l'invite, {told} chez l'host ; replis sur la copie : {given_up}")
    if ctx.get("soft"):
        if order == "host d'abord":
            check(f"etage {n}, {order} : l'invite est revenu par la carte seule ({by_map}, annonce par l'host {told})",
                  by_map == 1 and told >= 1)
        check(f"etage {n}, {order} : aucun repli sur la copie du monde ({given_up})", given_up == 0)
    dupes = {p: ev(p, DUPES) for p in (host, client)}
    check(f"etage {n}, {order} : aucun numero en double sur la carte et dans les sacs (host {dupes[host]}, invite {dupes[client]})",
          dupes[host] == "0" and dupes[client] == "0")
    # apres le passage, le jeu continue-t-il juste ? chacun pose un objet que l'autre voit a la meme case, chacun
    # marche et l'autre le voit, puis les deux jeux ont les memes nombres de carte
    # loin de la case d'arrivee : un seau pose dessus est ramasse par celui qui y arrive au passage suivant
    for p in (client, host):
        rs.idle(p)
        rs.steps(p, 5)
    time.sleep(4)
    for p, q in ((client, host), (host, client)):
        uid, where = put_down(host, p)
        check(f"etage {n}, {order} : objet pose par {names[p]} vu par {names[q]} a la meme case ({where})",
              rs.eventually(lambda: on_map(q, [uid]).get(uid) == where, timeout=20))
    me = int(ev(client, "EClass.pc.uid.ToString()"))
    rs.idle(client)
    rs.steps(client)
    time.sleep(3)
    check(f"etage {n}, {order} : l'invite marche, l'host le voit ou il est ({rs.pos(client)})",
          rs.eventually(lambda: max(abs(a - b) for a, b in zip(rs.pos(host, me), rs.pos(client))) <= 1, timeout=15))
    for p in (host, client):
        rs.idle(p)
    same = rs.eventually(rs.equal, timeout=30)
    check(f"etage {n}, {order} : memes nombres de carte (host {rs.sums(host)[0]} | invite {rs.sums(client)[0]})", same)
    return {"etage": n, "ordre": order, "copies": copies, "secondes": round(took, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--floors", type=int, default=4)
    ap.add_argument("--soft", action="store_true", help="coche la regle SoftRecall chez l'host avant de descendre")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = now()

    live = emp.live_ports()
    ctx = {"host": next(h["port"] for h in live if h["role"] == "Host"),
           "client": next(h["port"] for h in live if h["role"] == "Client")}
    host, client = ctx["host"], ctx["client"]
    both_joined(host, client, HOME)
    ctx["soft"] = a.soft
    if a.soft:
        from combat_suite import set_option
        set_option("SoftRecall", True)
        time.sleep(3)
        log("regle SoftRecall : " + " / ".join(ev(p, "ElinTogether.Net.NetSession.Instance.Rules.SoftRecall.ToString()") for p in (host, client)))
    region = int(ev(client, 'EClass._zone.ParentZone.uid.ToString()'))

    rows = []
    try:
        site = make_nefia(ctx, "donjon")
        if site:
            nefia, spot = site
            walk_in(ctx, host, region, nefia, spot)
            # l'invite y rejoint l'host : il n'y est pas seul, walk_in attendrait qu'il le soit
            ev(client, 'EClass.player.ExitBorder(); "ok"')
            at_zone(ctx, client, region)
            enter_at(client, spot)
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
