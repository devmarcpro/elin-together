"""Le public d'un musicien : le personnage d'un autre joueur n'en fait pas partie (retour d'une vraie partie, 6 octobre
2026 : l'host jouait de la musique, le personnage de l'invite lui jetait des orens).

    python _tools/mp_test.py
    python _tools/witness_suite.py

W1  l'host a cote de l'invite : la liste du public de l'host (Point.ListWitnesses, type musique, celle que lit
    AI_PlayMusic) ne contient pas le personnage de l'invite ; ni dans l'autre sens, lue chez l'host pour le musicien invite
    (c'est l'host qui simule la musique d'un invite)

Ce que le banc ne joue pas comme un joueur : il lit la liste du public, il ne joue pas un morceau entier ni ne compte
les pieces jetees."""
import sys

from mp_test import state  # noqa: E402
from travel_suite import RESULTS, check, ev, scan_logs  # noqa: E402
from datetime import datetime, timezone

H, A = 27551, 27552


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    uid_h = int(ev(H, "EClass.pc.uid.ToString()"))
    uid_a = int(state(A)["pc"]["uid"])
    near = ev(H, f'EClass.pc.pos.Distance(EClass._map.charas.Find(c => c.uid == {uid_a}).pos).ToString()')
    check(f"les deux joueurs sont a portee de musique l'un de l'autre (distance {near})", int(near) <= 4)
    seen = ev(H, 'string.Join(",", EClass.pc.pos.ListWitnesses(EClass.pc, 4, WitnessType.music).Select(c => c.uid))')
    check(f"W1 l'host joue : le personnage de l'invite ({uid_a}) n'est pas dans son public ({seen or 'personne'})",
          str(uid_a) not in seen.split(","))
    seen = ev(H, f'var g = EClass._map.charas.Find(c => c.uid == {uid_a}); '
                 'return string.Join(",", g.pos.ListWitnesses(g, 4, WitnessType.music).Select(c => c.uid));')
    check(f"W1 l'invite joue (simule chez l'host) : le personnage de l'host ({uid_h}) n'est pas dans son public ({seen or 'personne'})",
          str(uid_h) not in seen.split(","))
    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
