"""Scenario du premier jalon : voyage independant d'un client.

    python _tools/mp_test.py                  # d'abord : host + client connectes
    python _tools/travel_test.py --zone lumiest

1. le client va seul dans --zone (l'host reste chez lui)
2. il y depose sa hache et un objet cree sur place (uid dans la plage reservee)
3. il revient dans la zone de l'host
4. verifications : inventaire du client cote host, zone ecrite chez l'host, puis l'host y va et retrouve les objets
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import SHOTS, log, ok, shot, state, wait  # noqa: E402


def ev(port, code, timeout=180):
    return ok(emp.call(port, "eval", {"code": code}, timeout=timeout))


def check(label, cond):
    print(f"  [{'OK' if cond else 'ECHEC'}] {label}")
    return cond


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", default="lumiest", help="id Elin de la zone de destination du client")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    live = emp.live_ports()
    host = next(h["port"] for h in live if h["role"] == "Host")
    client = next(h["port"] for h in live if h["role"] == "Client")
    home = state(host)["zone"]
    target = ev(host, f'var z = EClass.game.spatials.Find("{a.zone}"); z == null ? "" : z.uid + "|" + z.ZoneFullName + "|" + z.isGenerated')
    if not target:
        sys.exit(f"zone {a.zone} introuvable")
    target_uid, target_name, target_gen = target.split("|")
    log(f"host={host} client={client} maison={home['name']} ({home['uid']}) cible={target_name} ({target_uid}) generee chez l'host={target_gen}")
    client_uid = state(client)["pc"]["uid"]

    # 1. depart
    ev(client, f'EClass.pc.MoveZone(EClass.game.spatials.Find({target_uid})); "ok"')
    wait(lambda: (state(client).get("zone") or {}).get("uid") == int(target_uid), "client dans la zone cible", timeout=120)
    time.sleep(3)
    c, h = state(client), state(host)
    log(f"client : zone={c['zone']['name']} away={c.get('awayZone')} | host : zone={h['zone']['name']} joueurs={len(h['players'])}")
    shot("travel-1-client-away", client)

    # 2. depot : la hache de l'inventaire + un objet cree sur place
    drop = ev(client, 'var axe = EClass.pc.things.Find("axe"); var axeUid = axe?.uid ?? -1; '
                      'if (axe != null) EClass.pc.DropThing(axe); '
                      'var gem = ThingGen.Create("apple"); EClass._zone.AddCard(gem, EClass.pc.pos); '
                      'axeUid + "|" + gem.uid + "|" + EClass.pc.pos.x + "," + EClass.pc.pos.z')
    axe_uid, apple_uid, pos = drop.split("|")
    log(f"client : hache {axe_uid} deposee, pomme {apple_uid} creee, position {pos}")
    shot("travel-2-client-drop", client)

    # 3. retour
    ev(client, f'EClass.pc.MoveZone(EClass.game.spatials.Find({home["uid"]})); "ok"')
    wait(lambda: (lambda s: s.get("sceneMode") == "Zone" and (s.get("zone") or {}).get("uid") == home["uid"]
                  and not s.get("awayZone") and s.get("connected"))(state(client)), "client de retour", timeout=180)
    time.sleep(5)
    c, h = state(client), state(host)
    log(f"client : zone={c['zone']['name']} away={c.get('awayZone')} | host : joueurs={len(h['players'])}")

    # 4. verifications
    print("Verifications :")
    results = [
        check("client revenu chez l'host, plus en mode absent", c["zone"]["uid"] == home["uid"] and not c.get("awayZone")),
        check("2 joueurs des deux cotes", len(h["players"]) == 2 and len(c["players"]) == 2),
        check("host : le perso du client n'a plus la hache",
              ev(host, f'EClass.game.cards.globalCharas.Find({client_uid}).things.Find("axe") == null ? "yes" : "no"') == "yes"),
        check("host : zone cible marquee generee",
              ev(host, f'EClass.game.spatials.Find({target_uid}).isGenerated.ToString()') == "True"),
        check("host : fichiers de carte ecrits",
              ev(host, f'System.IO.File.Exists(EClass.game.spatials.Find({target_uid}).pathSave + "map").ToString()') == "True"),
        check(f"host : compteur d'uid au-dela de la pomme ({apple_uid})",
              int(ev(host, 'EClass.game.cards.uidNext.ToString()')) > int(apple_uid)),
    ]

    # l'host va dans la zone et cherche les objets
    ev(host, f'EClass.pc.MoveZone(EClass.game.spatials.Find({target_uid})); "ok"')
    wait(lambda: (state(host).get("zone") or {}).get("uid") == int(target_uid), "host dans la zone cible", timeout=180)
    time.sleep(5)
    found = ev(host, f'string.Join(";", EClass._map.things.Where(t => t.uid == {axe_uid} || t.uid == {apple_uid})'
                     '.Select(t => t.id + "@" + t.pos.x + "," + t.pos.z))')
    log(f"host dans {target_name}, objets trouves : {found or 'aucun'}")
    results.append(check("host : la hache est au sol dans la zone", f"axe@{pos}" in (found or "")))
    results.append(check("host : la pomme creee par le client est au sol", f"apple@{pos}" in (found or "")))
    ev(host, f'var p = new Point({pos.replace(",", ", ")}); EClass.pc.Teleport(p.GetNearestPoint(), silent: true); "ok"')
    time.sleep(2)
    print(f"capture host : {shot('travel-3-host-finds', host)}")

    print(f"\n{sum(results)}/{len(results)} verifications OK")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
