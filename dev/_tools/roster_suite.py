"""Un personnage deja dans l'equipe n'y est pas ajoute une deuxieme fois (bug du 2026-10-10 : « An item with the
same key has already been added » dans WidgetRoster.Build, a chaque rafraichissement). Test court, host + 1 client.

    python _tools/mp_test.py
    python _tools/roster_suite.py

R1  dans chaque jeu : un membre de l'equipe (pas le joueur) recoit une autre « equipe » comme lien, ce que fait une
    copie du personnage venue d'un autre jeu ; Party.AddMemeber ne l'ajoute pas une deuxieme fois, son lien est
    remis, et la liste de l'ecran se reconstruit sans exception.

Ce que le banc ne joue pas comme un joueur : le lien est casse a la main, le vrai chemin qui l'a casse dans la
partie de l'utilisateur n'est pas connu. JAMAIS LANCEE a l'ecriture.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from travel_suite import RESULTS, check, ev, scan_logs  # noqa: E402

TWICE = ('var p = EClass.pc.party; var c = p.members.FirstOrDefault(x => x != EClass.pc); if (c == null) return "seul"; '
         'var n = p.members.Count; var u = p.uidMembers.Count; c.party = new Party(); p.AddMemeber(c); '
         'WidgetRoster.Instance?.Build(); '
         'return (p.members.Count - n) + "/" + (p.uidMembers.Count - u) + "/" + (c.party == p);')


def main():
    start = time.time()
    for name, port in (("host", 27551), ("invite", 27552)):
        r = str(ev(port, TWICE))
        if r == "seul":
            print(f"    {name} : personne d'autre dans l'equipe, rien a prouver ici")
            continue
        check(f"{name} : pas de deuxieme ajout, lien remis ({r})", r == "0/0/True")
    check("au moins un jeu avait un autre membre dans l'equipe", RESULTS)
    scan_logs(start)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
