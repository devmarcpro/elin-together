"""Un personnage deja dans l'equipe n'y est pas ajoute une deuxieme fois (bug du 2026-10-10 : « An item with the
same key has already been added » dans WidgetRoster.Build, a chaque rafraichissement). Test court, host + 1 client.

    python _tools/mp_test.py
    python _tools/oct10_suite.py

Corrections du 2026-10-10, ecrites par lecture du code. JAMAIS LANCEE a l'ecriture : un rouge peut venir du test.

R1  dans chaque jeu : un membre de l'equipe (pas le joueur) recoit une autre « equipe » comme lien, ce que fait une
    copie du personnage venue d'un autre jeu ; Party.AddMemeber ne l'ajoute pas une deuxieme fois, son lien est
    remis, et la liste de l'ecran se reconstruit sans exception.

C1  l'invite apprend une recette de bloc qui a une variante pilier (-p) : comptee 1 fois dans les deux jeux, la
    variante aussi (avant : 2 chez l'host).
Q1  a Mysilia, l'host retire au sort les offres de quetes (Zone.UpdateQuests(true), ce que fait le bouton « Reroll
    Quests ») : memes offres dans les deux jeux (avant : l'invite gardait les anciennes en plus).

Ce que le banc ne joue pas comme un joueur : la recette est apprise par la fonction du jeu, pas par un livre ; le
tirage des quetes est appele par le pont, pas par le bouton du panneau ; nuit commune (saignement, poison) et copie
de carte precedee de ses changements en attente : pas de test ici.
 le lien est casse a la main, le vrai chemin qui l'a casse dans la
partie de l'utilisateur n'est pas connu. JAMAIS LANCEE a l'ecriture.
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from travel_suite import RESULTS, check, ev, eventually, host_goto, scan_logs  # noqa: E402

TWICE = ('var p = EClass.pc.party; var c = p.members.FirstOrDefault(x => x != EClass.pc); if (c == null) return "seul"; '
         'var n = p.members.Count; var u = p.uidMembers.Count; c.party = new Party(); p.AddMemeber(c); '
         'WidgetRoster.Instance?.Build(); '
         'return (p.members.Count - n) + "/" + (p.uidMembers.Count - u) + "/" + (c.party == p);')

H, A = 27551, 27552
MYSILIA = 25  # une vraie ville (Zone_Town) : Vernis n'en est pas une, aucune offre n'y est tiree
LEARN = ('var known = EClass.player.recipes.knownRecipes; '
         'var id = RecipeManager.dict.Keys.FirstOrDefault(k => !k.EndsWith("-p") && !k.EndsWith("-b") && '
         'RecipeManager.dict.ContainsKey(k + "-p") && !known.ContainsKey(k) && !known.ContainsKey(k + "-p")); '
         'if (id == null) return ""; EClass.player.recipes.Add(id); return id;')
COUNT = ('var known = EClass.player.recipes.knownRecipes; int a, b; known.TryGetValue("{id}", out a); '
         'known.TryGetValue("{id}-p", out b); return a + "/" + b;')
OFFERS = ('string.Join(",", EClass._map.charas.Concat(EClass._map.deadCharas).Where(c => c.quest != null && '
          '!EClass.game.quests.list.Contains(c.quest)).Select(c => c.quest.uid).OrderBy(x => x))')


def c1():
    rid = str(ev(A, LEARN))
    if not check(f"une recette de bloc a variante pilier inconnue des deux ({rid})", rid):
        return
    count = COUNT.replace("{id}", rid)
    check(f"l'invite : comptee une fois, la variante aussi ({ev(A, count)})", str(ev(A, count)) == "1/1")
    check("l'host : pareil", eventually(lambda: str(ev(H, count)) == "1/1", timeout=15))
    check(f"toujours pareil 5 s plus tard (host {ev(H, count)})", not time.sleep(5) and str(ev(H, count)) == "1/1")


def q1():
    host_goto(H, A, MYSILIA)
    before = str(ev(H, OFFERS))
    check(f"depart : memes offres a Mysilia ({before.count(',') + 1 if before else 0})",
          eventually(lambda: str(ev(A, OFFERS)) == str(ev(H, OFFERS)), timeout=30))
    ev(H, 'EClass._zone.UpdateQuests(true); "ok"')
    after = str(ev(H, OFFERS))
    check("le tirage a change les offres de l'host", after != before)
    check(f"apres le tirage : memes offres chez l'invite (host {after} ; invite {ev(A, OFFERS)})",
          eventually(lambda: str(ev(A, OFFERS)) == str(ev(H, OFFERS)), timeout=30))


def main():
    start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for name, port in (("host", 27551), ("invite", 27552)):
        r = str(ev(port, TWICE))
        if r == "seul":
            print(f"    {name} : personne d'autre dans l'equipe, rien a prouver ici")
            continue
        check(f"{name} : pas de deuxieme ajout, lien remis ({r})", r == "0/0/True")
    check("au moins un jeu avait un autre membre dans l'equipe", RESULTS)
    for step in (c1, q1):
        try:
            step()
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
    scan_logs(start)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
