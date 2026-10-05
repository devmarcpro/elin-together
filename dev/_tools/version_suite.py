"""Version d'Elin differente entre deux joueurs : ce n'est plus un mur. Test court, sur des instances deja lancees
(host + 1 client).

    python _tools/mp_test.py
    python _tools/version_suite.py

V1  l'invite a une autre version d'Elin que l'host (meme version du mod) : il entre quand meme.
V2  l'host coche « Require the same Elin version » : le meme invite est refuse. Case decochee : il entre de nouveau.

Ce que le banc ne joue pas comme un joueur : il n'a pas deux versions d'Elin ; il change le numero de version que le jeu
de l'invite annonce (`core.version.fix`), puis fait la connexion comme le bouton du menu. Le numero est remis a la fin.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import chara_suite  # noqa: E402
from combat_suite import set_option  # noqa: E402
from mp_test import log, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402
from datetime import datetime, timezone  # noqa: E402

H, A = 27551, 27552
VERSION = 'EClass.core.version.major + "." + EClass.core.version.minor + "." + EClass.core.version.batch + "." + EClass.core.version.fix'


def joined(timeout=60):
    """Demande la connexion comme le bouton du menu ; vrai si le client finit en jeu chez l'host."""
    from mp_test import ok
    import emp
    ok(emp.call(A, "command", {"cmd": "emp.connect_udp"}))
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = state(A)
        if s.get("connected") and s.get("sceneMode") == "Zone":
            return True
        choices = [c for c in ev(A, chara_suite.CHOICES).split("|") if c]
        if len(choices) >= 2:
            chara_suite.click(0)
            chara_suite.in_game()
            return True
        time.sleep(2)
    return False


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    fix = ev(A, "EClass.core.version.fix.ToString()")
    try:
        log("--- V1 : une autre version d'Elin, meme version du mod : l'invite entre")
        chara_suite.leave()
        ev(A, 'EClass.core.version.fix = 77; "ok"')
        check(f"les deux jeux annoncent des versions d'Elin differentes (host {ev(H, VERSION)}, invite {ev(A, VERSION)})", ev(H, VERSION) != ev(A, VERSION))
        check("l'invite entre quand meme chez l'host", joined())
        check("l'host le voit", eventually(lambda: len(state(H).get("players", [])) == 2, timeout=30))

        log("--- V2 : l'host exige la meme version : refuse ; case decochee : il entre")
        chara_suite.leave()
        set_option("SameGameVersion", True)
        check("case cochee : l'invite n'entre pas", not joined(timeout=40))
        check("l'host ne le voit pas", len(state(H).get("players", [])) == 1)
        ev(A, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
        time.sleep(4)
        set_option("SameGameVersion", False)
        check("case decochee : il entre de nouveau", joined())
    finally:
        set_option("SameGameVersion", False)
        ev(A, f'EClass.core.version.fix = {fix}; "ok"')
    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
