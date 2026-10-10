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

B1  le personnage de l'invite (cree par le banc a la connexion) a UNE bourse, celle de la ceinture a outils, comme
    l'host (avant : une deuxieme dans le sac).
H1  l'invite pose un sort sur une barre de raccourcis, ses reglages sont notes dans son fichier, puis il perd son
    lien et revient en ne se servant que du fichier (ce que fait une nouvelle session) : le sort est toujours la
    (avant : les barres de l'host a la place).

F2  (trois fenetres : mp_test.py --clients 2) la meme chose que F1 sur une carte tenue par un invite, frappe par
    un autre invite.
F1  un monstre vise l'host, qui ne fait rien ; l'invite le frappe dix fois : le monstre joue ses tours (avant : fige,
    0 tour, tue sans risque) ; puis plus personne ne joue : le monstre s'arrete (le temps s'arrete, comme en solo).
    Le coup de l'invite est ACT.Melee puis la fin de tour du jeu, pas le clic ; le monstre est soigne par le banc
    entre les coups pour ne pas mourir.

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
import emp  # noqa: E402
from mp_test import ok, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, host_goto, players, scan_logs  # noqa: E402

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

PURSES = ('var l = new System.Collections.Generic.List<string>(); System.Action<Card, string> walk = null; '
          'walk = (c, path) => { foreach (var t in c.things) { if (t.id == "purse") l.Add(path); walk(t, path + "/" + t.id); } }; '
          'walk(EClass.pc, "pc"); return string.Join(",", l);')
OWN = 'var own = HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.OwnSettings"); '
SPELL = ('var bars = EClass.player.hotbars.bars; var b = System.Array.FindIndex(bars, x => x != null && x.pages.Count > 0); '
         'var id = EClass.sources.elements.alias["ActPray"].id; ')
LAY = SPELL + 'bars[b].pages[0].SetItem(bars[b], new HotItemAct { id = id }, 0); return b + ":" + id;'
READ = SPELL + 'var a = bars[b].pages[0].GetItem(0) as HotItemAct; return b + ":" + (a == null ? 0 : a.id);'


def b1():
    for name, port in (("host", H), ("invite", A)):
        got = str(ev(port, PURSES))
        check(f"{name} : une seule bourse, dans la ceinture ({got})", got == "pc/toolbelt")


def h1():
    laid = str(ev(A, LAY))
    check(f"l'invite pose un sort sur une barre ({laid})", laid == str(ev(A, READ)) and not laid.endswith(":0"))
    # le fichier seul : ce qui est note en memoire est oublie, comme apres une fermeture du jeu
    ev(A, OWN + 'HarmonyLib.AccessTools.Method(own, "Keep").Invoke(null, null); '
                'HarmonyLib.AccessTools.Field(own, "_kept").SetValue(null, null); return "ok";')
    ok(emp.call(A, "command", {"cmd": "emp.cut_link 20"}))
    time.sleep(25)
    back = eventually(lambda: state(A).get("sceneMode") != "Title" and players(A) == 2 and players(H) == 2, timeout=120)
    if not check("l'invite a perdu son lien et est revenu seul", back):
        return
    time.sleep(3)
    check(f"le sort est toujours sur sa barre ({ev(A, READ)})", str(ev(A, READ)) == laid)
    ok(emp.call(A, "command", {"cmd": "emp.link_timeout 0"}))

MON = "EClass._map.charas.Find(x => x.uid == {m})"


def fight(K, B, who):
    """Le jeu du port K simule la carte et son personnage est la cible du monstre ; le joueur du port B frappe."""
    from guest_suite import seen  # noqa: PLC0415
    b = state(B)["pc"]["uid"]
    # sur une case voisine de celui qui frappe (a deux cases le coup de melee n'a pas lieu du tout)
    m = int(ev(K, f'var b = EClass._map.charas.Find(x => x.uid == {b}); var p = b.pos.GetNearestPoint(false, false, true, true); '
                  'if (p == null || p.Distance(b.pos) != 1) return "0"; '
                  'var m = CharaGen.Create("putty"); EClass._zone.AddCard(m, p); m.c_originalHostility = Hostility.Enemy; '
                  'm.hostility = Hostility.Enemy; m.SetEnemy(EClass.pc); m.SetLv(60); m.elements.SetBase(60, 400); m.hp = m.MaxHP; '
                  'return m.uid.ToString();'))
    if not check(f"{who} : une case libre voisine de celui qui frappe", m):
        return
    if not check(f"{who} : un monstre apparait a cote de celui qui frappe ({m})", eventually(lambda: seen(B, m), timeout=15)):
        return
    mon = MON.replace("{m}", str(m))
    # (les habitants d'une carte s'en melent et le monstre se retourne contre eux : il est garde sur sa cible)
    keep = f'var m = {mon}; if (m != null) {{ m.hp = m.MaxHP; m.enemy = EClass.pc; }} '
    blow = f'var m = {mon}; if (m != null) {{ ACT.Melee.Perform(EClass.pc, m, m.pos); EClass.player.EndTurn(false); }} return "ok";'
    try:
        time.sleep(2)
        turns = lambda: int(ev(K, f'var m = {mon}; return (m == null ? -1 : m.turn).ToString();'))  # noqa: E731
        played = lambda p: int(ev(p, 'EClass.player.stats.turns.ToString()'))  # noqa: E731
        t0, s0 = turns(), played(B)
        check(f"{who} : le monstre est la avant les coups (tour {t0})", t0 >= 0)
        for _ in range(10):
            ev(K, keep + 'return "ok";')
            ev(B, blow)
            time.sleep(0.7)
        time.sleep(1)
        t1 = turns()
        # ce qu'un tour de celui qui frappe donne au monstre, mesure ici (la vitesse d'un joueur lue dans la copie
        # d'un autre jeu n'est pas la sienne)
        rate = (t1 - t0) / max(1, played(B) - s0)
        check(f"{who} : frappe dix fois par l'autre joueur, sa cible ne faisant rien, le monstre joue ses tours ({t0} -> {t1})",
              t1 >= 0 and t1 - t0 >= 4)
        time.sleep(5)
        t2 = turns()
        check(f"{who} : plus personne ne joue, le monstre s'arrete ({t2 - t1} tour en 5 s)", t2 - t1 <= 1)
        # les deux jouent : le monstre doit suivre le plus rapide des deux, pas la somme. Compte en tours reels de
        # chacun (une fin de tour demandee par le pont ne fait pas toujours exactement un tour)
        pace = lambda p, uid: float(ev(K, f'var m = {mon}; var c = EClass._map.charas.Find(x => x.uid == {uid}); '  # noqa: E731
                                          'return ((float)m.Speed / System.Math.Max(1, c.Speed)).ToString(System.Globalization.CultureInfo.InvariantCulture);'))
        k = state(K)["pc"]["uid"]
        a0, b0 = played(K), played(B)
        for _ in range(10):
            ev(K, keep + 'EClass.player.EndTurn(false); return "ok";')
            ev(B, blow)
            time.sleep(0.7)
        time.sleep(1)
        t3 = turns()
        da, db = (played(K) - a0) * pace(K, k), (played(B) - b0) * rate
        check(f"{who} : les deux jouent, le monstre suit le plus rapide des deux ({t3 - t2} tours ; attendu {max(da, db):.1f}, "
              f"la somme ferait {da + db:.1f})", t3 >= 0 and max(da, db) - 2.5 <= t3 - t2 <= max(da, db) + 2.5)
    finally:
        ev(K, f'var m = {mon}; if (m != null) m.Destroy(); return "ok";')


def f1():
    fight(H, A, "carte de l'host")


def f2():
    """a trois fenetres : la meme chose sur une carte tenue par un INVITE, le troisieme joueur frappe"""
    from travel_suite import HOME, VERNIS, client_settled, move, wait  # noqa: PLC0415
    B = 27553
    try:
        state(B)
    except Exception:  # noqa: BLE001
        print("    f2 : pas de troisieme fenetre (mp_test.py --clients 2), etape sautee")
        return
    move(A, VERNIS)
    wait(client_settled(A, VERNIS, True), "le premier invite seul a Vernis, il tient la carte", timeout=180)
    time.sleep(3)
    move(B, VERNIS)
    b = state(B)["pc"]["uid"]
    there = eventually(lambda: (state(B).get("zone") or {}).get("uid") == VERNIS and state(B).get("sceneMode") == "Zone"
                       and ev(A, f'(EClass._map.charas.Find(x => x.uid == {b}) != null).ToString()') == "True", timeout=180)
    if not check("le second invite arrive sur la carte tenue par le premier, qui le voit", there):
        return
    time.sleep(3)
    try:
        fight(A, B, "carte tenue par un invite")
    finally:
        move(B, HOME)
        time.sleep(8)
        move(A, HOME)
        time.sleep(15)


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
    steps = (b1, c1, h1, f1, q1, f2)
    if len(sys.argv) > 1:
        steps = [x for x in steps if x.__name__ in sys.argv[1].split(',')]
    for step in steps:
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
