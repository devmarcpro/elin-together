"""Ce qui est depose dans les boites du monde pendant un voyage. Test court, sur des instances deja lancees.

    python _tools/mp_test.py
    python _tools/transfer_suite.py     # ~2 minutes, finit avec le client a la Prairie

X1  A, en voyage, depose un objet a la banque : il arrive dans la banque de l'host, pas perdu avec la copie
X2  A, en voyage, met un objet dans la caisse d'expedition : l'host l'a dans sa caisse ET plus dans le sac qu'il
    garde pour A (sauvegarde immediate), donc pas "vendu et garde" si A quitte tout de suite
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from travel_suite import HOME, LUMIEST, RESULTS, both_joined, check, client_settled, ev, eventually, move, scan_logs, wait  # noqa: E402

H, A = 27551, 27552


def give(uid, item):
    """L'host donne un objet au joueur (sur sa carte), renvoie le numero de l'objet."""
    return int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); var t = ThingGen.Create("{item}"); '
                     'c.AddThing(t); return t.uid.ToString();'))


def host_has(container, item):
    return int(ev(H, f'EClass.game.cards.{container}.things.Count(t => t.id == "{item}").ToString()'))


def host_copy_has(uid, item):
    """Le sac que l'host garde pour ce joueur contient-il encore cet objet ?"""
    return ev(H, f'(EClass.game.cards.globalCharas.Find({uid}).things.Find("{item}") != null).ToString()') == "True"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        a = state(A)["pc"]["uid"]
        give(a, "torch")
        give(a, "plank")
        check("A a recu une torche et une planche", eventually(
            lambda: ev(A, '(EClass.pc.things.Find("torch") != null && EClass.pc.things.Find("plank") != null).ToString()') == "True", timeout=10))

        move(A, LUMIEST)
        wait(client_settled(A, LUMIEST, True), "A seul a Lumiest")
        time.sleep(3)

        log("--- X1")
        before = host_has("container_deposit", "torch")
        ev(A, 'EClass.game.cards.container_deposit.AddThing(EClass.pc.things.Find("torch")); "ok"')
        check("A depose la torche a la banque en voyage : elle arrive dans la banque de l'host",
              eventually(lambda: host_has("container_deposit", "torch") == before + 1, timeout=15))
        check("elle n'est plus dans le sac de A", ev(A, '(EClass.pc.things.Find("torch") == null).ToString()') == "True")

        log("--- X2")
        before = host_has("container_shipping", "plank")
        ev(A, 'EClass.game.cards.container_shipping.AddThing(EClass.pc.things.Find("plank")); "ok"')
        check("A met la planche dans la caisse en voyage : elle arrive dans la caisse de l'host",
              eventually(lambda: host_has("container_shipping", "plank") == before + 1, timeout=15))
        check("et l'host ne l'a plus dans le sac qu'il garde pour A (sauvegarde immediate)",
              eventually(lambda: not host_copy_has(a, "plank"), timeout=15))
        check("ni la torche", not host_copy_has(a, "torch"))

        move(A, HOME)
        both_joined(H, A, HOME)
        check("de retour, A n'a ni l'une ni l'autre",
              ev(A, '(EClass.pc.things.Find("torch") == null && EClass.pc.things.Find("plank") == null).ToString()') == "True")
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {ex}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-transfer-{name}', port)}")
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
