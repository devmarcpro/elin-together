"""Reprise automatique a TROIS (tranche R4 de PLAN_reprise_automatique.md) : l'host quitte sa partie, l'invite
designe reprend le monde depuis sa copie, l'AUTRE invite le rejoint tout seul, avec son personnage.

    python _tools/mp_test.py --clients 2
    python _tools/takeover_trio.py

Ce que le banc ne joue pas comme un joueur : trois fenetres sur un PC, le nouvel host ouvre le meme port local que
l'ancien (le chemin par Steam, salon du nouvel host retrouve chez l'ami ou dans la liste, ne se prouve qu'entre vrais
PC) ; l'host « part » par emp.disconnect (ce que fait le bouton Disconnect) ; la regle est cochee par une commande.
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import log, ok, state  # noqa: E402
from travel_suite import RESULTS, check, dismiss_dialogs, ev, eventually, players, scan_logs  # noqa: E402
from worldcopy_suite import BENCH, save_once  # noqa: E402

H, A, B = 27551, 27552, 27553


def command(port, cmd):
    r = ok(emp.call(port, "command", {"cmd": cmd}, timeout=180))
    log(f"{port} {cmd} : {r}")
    return str(r)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for p in (H, A, B):
        dismiss_dialogs(p)
    if not check("depart : trois joueurs dans la partie", all(players(p) == 3 for p in (H, A, B))):
        return finish(start)
    me = {p: state(p)["pc"] for p in (A, B)}
    command(H, "emp.takeover_rule 1")
    for p in (A, B):
        command(p, "emp.auto_open 1")
        command(p, "emp.link_timeout 1")
    check("l'host sauvegarde sans geste", save_once())
    has = lambda p: "mine: none" not in str(ev(p, f"{BENCH}.State"))  # noqa: E731
    if not check("les deux invites ont une copie entiere du monde", eventually(lambda: has(A) and has(B), timeout=180)):
        for p in (A, B):
            log(f"{p} : " + str(ev(p, f"{BENCH}.State")))
        return finish(start)
    for p in (A, B):
        log(f"{p} : " + str(ev(p, f"{BENCH}.State")))
    t = time.time()
    command(H, "emp.disconnect")
    check("l'host a quitte sa partie", eventually(lambda: state(H).get("role") != "Host", timeout=60))

    def taker():
        for p in (A, B):
            s = state(p)
            if s.get("sceneMode") == "Zone" and s.get("role") == "Host":
                return p
        return 0
    if not check("un des deux invites devient host du monde, sans un clic", eventually(lambda: taker() != 0, timeout=300)):
        for p in (A, B):
            log(f"{p} : {state(p).get('role')} {state(p).get('sceneMode')} ; " + str(ev(p, f"{BENCH}.Takeover")))
        return finish(start)
    new = taker()
    other = B if new == A else A
    log(f"repreneur : {new}, {time.time() - t:.0f} s apres le depart de l'host ; " + str(ev(new, f"{BENCH}.Takeover")))

    def joined():
        s = state(other)
        return s.get("sceneMode") == "Zone" and s.get("role") == "Client" and s.get("connected") and players(other) == 2 and players(new) == 2
    back = eventually(joined, timeout=240)
    if not check(f"l'autre invite a rejoint le repreneur tout seul, {time.time() - t:.0f} s apres le depart de l'host", back):
        log(f"autre invite : {state(other).get('role')} {state(other).get('sceneMode')} connecte {state(other).get('connected')}")
        return finish(start)
    time.sleep(4)
    for p in (new, other):
        now = state(p)["pc"]
        check(f"{p} joue son personnage ({now.get('name')}, {now.get('uid')})", now.get("uid") == me[p]["uid"] and now.get("name") == me[p]["name"])
    check("chacun voit l'autre sur la carte",
          ev(new, f'(EClass._map.charas.Any(c => c.uid == {me[other]["uid"]})).ToString()') == "True"
          and ev(other, f'(EClass._map.charas.Any(c => c.uid == {me[new]["uid"]})).ToString()') == "True")
    check("un seul personnage de chacun sur la carte du repreneur",
          ev(new, f'EClass._map.charas.Count(c => c.uid == {me[other]["uid"]}).ToString()') == "1")
    finish(start)


def finish(start):
    for p in (A, B):
        try:
            emp.call(p, "command", {"cmd": "emp.link_timeout 0"})
        except Exception:  # noqa: BLE001
            pass
    scan_logs(start)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
