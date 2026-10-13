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

L1  boutique a stock limite (Fiama) : l'invite achete un objet « stock limite » par la fenetre du marchand ; l'objet
    est de nouveau dans la boutique pour l'host, avec l'invite note comme acheteur ; l'invite ne peut pas le
    racheter ; l'host l'achete a son tour ; un reassort ne le double pas ; retire a la main (monde d'avant, ou il
    etait deja vendu), il revient au reassort. La fenetre est ouverte par la fonction du jeu, pas par le dialogue.
M1  l'invite monte un cheval, part seul a Vernis, y marche, revient et marche : chez l'host la monture est LA monture
    du monde (pas une copie), sur la case de son cavalier, une seule fois sur la carte (avant : le cavalier montait
    une copie, la vraie monture gardait une case de Vernis : monde inchargeable le 9 octobre). Le banc fait monter
    par l'acte du jeu (ActRide), pas par le menu.
S1  « une part pour chacun » (conseil 14) : l'host termine une quete d'histoire (celle du curry : une cassette et
    trois graines) ; l'invite present trouve la meme chose dans son sac, dans les deux jeux ; l'invite parti a
    Vernis recoit un colis a son nom dans le courrier de la base ; ce que le jeu lache hors d'une quete d'histoire ne donne de part a personne.
    Un joueur arrive « plus tard » (le banc l'efface du registre du monde) recoit un colis de rattrapage, une fois.
    La quete est creee et terminee par le pont (Quest.Create, Complete), pas jouee ; le cas ou c'est l'INVITE qui
    termine n'est pas joue ici (il faut une vraie quete du journal).
T1  tresor du manoir maudit (Melilith) : chaque joueur peut prendre UN tresor sans etre maudit (avant : le second
    joueur etait maudit pour son premier), la quete du groupe n'avance qu'une fois, un second tresor du meme joueur
    le maudit toujours. Les tresors sont des seaux marques par le banc, pris par l'action « prendre » du jeu ; pas
    dans le vrai manoir (contenu additionnel).
O1  un membre de l'equipe est sur une autre carte, plus grande (sa case n'existe pas ici) : la priere qui soigne
    l'equipe et la fin d'une nuit ne plantent plus (deux rapports du 2026-10-11, « Index was outside the bounds of
    the array » dans Point.get_cell). Le banc met la case du membre hors de la carte a la main, puis la remet ;
    priere et fin de nuit sont appelees par les fonctions du jeu (ActPray.Pray, Chara.OnSleep), pas jouees.
G1  ce qu'une quete d'histoire donne quand elle COMMENCE (le crochet et le coffre verrouille de Fiama) : une part pour
    l'autre joueur aussi. Le banc cree la quete et appelle Quest.Start (pas le dialogue de Fiama).
E1  la terre achetee a la servante de la base (daBuyLand) agrandit la zone constructible pour tous : l'invite
    achete, l'host voit les memes limites, et l'inverse. Le banc appelle MapBounds.Expand(1), ce que fait le dialogue
    apres avoir pris la platine : ni le dialogue ni le paiement ne sont joues.
R1  les reglages d'un habitant faits dans son dialogue (« reste ici », equipement partage) : l'invite les regle,
    l'host les a, et l'inverse. Le banc ouvre le vrai dialogue (ShowDialog) et le ferme, mais ecrit les valeurs par
    eval a la place du choix du menu (noMove, orgPos, SetInt 113 : ce que fait le choix).
P1  la peche d'un invite : ses prises du jour sont comptees pour LUI chez l'host (la « fievre » du don de pecheur
    dure ses cinq premieres prises), et le compte de l'host ne bouge pas. Le banc appelle AI_Fish.Makefish chez
    l'host pour le personnage de l'invite (ce que fait la fin d'une peche), sans canne ni eau.
X1  le parchemin de reconstruction lu par l'invite : l'objet neuf va dans son sac, il n'est pas equipe d'office.
    Le banc ouvre la fenetre de choix du jeu (LayerDragGrid.CreateReconstruction) et y designe l'objet par
    OnProcess, sans lire un vrai parchemin. Pas corrige : le niveau de l'objet neuf suit le plus profond de l'host.
A1  l'artefact d'un dieu : chaque joueur a le sien. Le second joueur qui prend le sien ne detruit plus celui du
    premier (le jeu detruit tout autre exemplaire tenu par « le camp du joueur »). Le banc cree les deux artefacts
    chez l'host par AddThing (le chemin du ramassage), sans priere ni autel.
D1  un invite renvoie un habitant qui porte un artefact de dieu : l'artefact va a l'invite, pas a l'host. Le banc
    cree l'habitant et l'artefact chez l'host, et envoie la demande de renvoi du mod (BaseRequestDelta.Send), sans le
    dialogue de l'habitant.
W1  un service paye dans un dialogue (la tache AI_Fuck lancee par le dialogue apres le paiement) : a la fin, l'or de
    l'invite ne bouge plus chez l'host (avant : il touchait une moitie du prix puis payait le prix une seconde fois).
    Le banc lance la tache par SetAI chez l'invite, comme le fait le dialogue, sans le dialogue ni son paiement.
I1  l'impot supplementaire choisi aupres de la servante : choisi par l'invite, l'host l'a (c'est lui qui fait la
    facture), et l'inverse. Le banc ouvre un vrai dialogue (ShowDialog), ecrit player.extraTax par eval a la place
    du choix du menu, puis ferme le dialogue. La facture du mois n'est pas faite.
K1  le boss d'une zone tombe sur la carte de l'host : l'invite present a aussi la victoire (message « boss_win »,
    renommee) et sa copie de la zone n'a plus de boss. Le banc fait un boss d'un monstre cree par eval (uidBoss pose
    dans les deux jeux) et le tue par DamageHP chez l'host ; la Prairie n'est pas un donjon : ni fanfare ni « conquis ».
J1  l'experience donnee « a toute l'equipe » (une recolte apprend le jardinage a tous) : gagnee dans le jeu de
    l'host, l'invite l'a aussi, et l'inverse. Le banc appelle Card.ModExpParty sur la force (un personnage neuf n a pas le jardinage), sans
    recolte. Pas couvert : l'experience de voyage a l'arrivee, les compagnons des autres joueurs.
S2  une part pour chacun, dans l'autre sens : l'INVITE termine la quete d'histoire (le curry) sur la carte de l'host :
    l'invite a sa recompense, l'host recoit sa part (dans son sac), une fois. La quete est commencee chez l'host (QuestManager.Start), le banc
    appelle Quest.Complete chez l'invite sur cette quete, sans le dialogue.
U1  l'invite vend a une boutique un objet non identifie : la boutique l'identifie, chez l'host aussi (avant : il
    restait non identifie dans la boutique de l'host). Le banc cree un marchand, ouvre sa boutique et vend par la transaction
    du jeu (InvOwner.Transaction, le maj+clic), l'objet et son etat « non identifie » sont poses par eval chez l'host.
S3  rattrapage d'un monde joue avant le registre (conseil 15) : des quetes d'histoire finies, pas de registre. A la
    premiere image du jeu qui heberge, leurs recompenses sont ecrites une fois dans le registre ; chaque joueur du
    monde, host compris, recoit un colis a son nom ; une seule fois. Le banc vide le registre, marque deux quetes
    finies (QuestDefense, QuestPuppy) et remet la marque a zero par reflexion ; l'invite est ramene par un aller-retour.
Z1  factures fantomes : le compteur des factures d'impot impayees du monde est ramene aux factures qui existent
    (sacs de l'host et de l'invite, courrier, banque, carte), jamais releve ; une fois par monde tout seul, et encore
    a la demande de l'host. Le banc fabrique trois factures (deux chez l'host, une chez l'invite), ajoute quatre
    « fantomes » au compteur et appelle RepairBillCount ; la perte de karma du mois et le bouton ne sont pas joues.
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
from mp_test import log, ok, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, host_goto, players, scan_logs  # noqa: E402

TWICE = ('var p = EClass.pc.party; var c = p.members.FirstOrDefault(x => x != EClass.pc); if (c == null) return "seul"; '
         'var n = p.members.Count; var u = p.uidMembers.Count; c.party = new Party(); p.AddMemeber(c); '
         'WidgetRoster.Instance?.Build(); '
         'return (p.members.Count - n) + "/" + (p.uidMembers.Count - u) + "/" + (c.party == p);')

H, A = 27551, 27552
HOME, MYSILIA = 7, 25  # une vraie ville (Zone_Town) : Vernis n'en est pas une, aucune offre n'y est tiree
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


OFFMAP = ('var c = EClass.pc.party.members.FirstOrDefault(x => x != EClass.pc); if (c == null) return "seul"; '
          'var old = c.pos; c.pos = new Point(EClass._map.Size + 40, EClass._map.Size + 40); var hp = c.hp; c.hp = 1; '
          'try { ActPray.Pray(EClass.pc, false); c.OnSleep(null, 1); c.PlayEffect(910); c.AddCondition<ConSleep>(5, true); c.RemoveCondition<ConSleep>(); return "ok " + (c.hp > 1); } '
          'catch (System.Exception ex) { return ex.GetType().Name + " " + ex.StackTrace.Split((char)10)[0]; } '
          'finally { c.pos = old; if (c.hp < hp) c.hp = hp; }')


def o1():
    for name, port in (("host", H), ("invite", A)):
        got = str(ev(port, OFFMAP))
        if got == "seul":
            print(f"    {name} : personne d'autre dans l'equipe, rien a prouver ici")
            continue
        check(f"{name} : priere et fin de nuit avec un membre hors de la carte, il est soigne ({got})", got == "ok True")


def b1():
    for name, port in (("host", H), ("invite", A)):
        got = str(ev(port, PURSES))
        check(f"{name} : une seule bourse, dans la ceinture ({got})", got == "pc/toolbelt")


def h1():
    # les compteurs « du joueur » qui sont a chacun (prix du titre de terrain qui double a chaque achat) : 3 chez
    # l'invite, 5 chez l'host, chacun garde le sien a travers une copie du monde
    ev(A, 'EClass.player.flags.landDeedBought = 3; return "ok";')
    ev(H, 'EClass.player.flags.landDeedBought = 5; return "ok";')
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
    deeds = ev(A, 'EClass.player.flags.landDeedBought.ToString()'), ev(H, 'EClass.player.flags.landDeedBought.ToString()')
    check(f"titres de terrain achetes : chacun son compte apres la copie du monde (invite {deeds[0]}, host {deeds[1]})", deeds == ("3", "5"))
    ev(H, 'EClass.player.flags.landDeedBought = 0; return "ok";')
    ev(A, 'EClass.player.flags.landDeedBought = 0; return "ok";')
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
                  # (paralyse : il vit ses tours, que le test compte, sans frapper ; libre, a ce niveau, il tue les deux joueurs
                  # de test et tout le reste de la suite echoue sur des morts)
                  'm.hostility = Hostility.Enemy; m.SetEnemy(EClass.pc); m.SetLv(60); m.elements.SetBase(60, 400); m.hp = m.MaxHP; '
                  'm.AddCondition<ConParalyze>(5000, true); '
                  'return m.uid.ToString();'))
    if not check(f"{who} : une case libre voisine de celui qui frappe", m):
        return
    if not check(f"{who} : un monstre apparait a cote de celui qui frappe ({m})", eventually(lambda: seen(B, m), timeout=15)):
        return
    mon = MON.replace("{m}", str(m))
    # (les habitants d'une carte s'en melent et le monstre se retourne contre eux : il est garde sur sa cible)
    # (et sa cible est soignee : un monstre de niveau 60 qui joue enfin ses tours tue un personnage de test,
    # et tout ce qui suit dans la suite echoue sur un joueur mort)
    # (2026-10-13 : soignee ne suffit pas, un seul coup du monstre entre deux soins la tuait certaines passes, et un
    # host mort ne recoit plus de part d'histoire : s2 et s3 rouges derriere. Elle ne peut pas mourir pendant le test)
    keep = (f'var m = {mon}; if (m != null) {{ m.hp = m.MaxHP; m.enemy = EClass.pc; }} EClass.pc.hp = EClass.pc.MaxHP; '
            'if (!EClass.pc.HasCondition<ConInvulnerable>()) EClass.pc.AddCondition<ConInvulnerable>(5000, true); ')
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
        ev(K, keep + 'return "ok";')
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
        ev(K, f'var m = {mon}; if (m != null) m.Destroy(); var c = EClass.pc.GetCondition<ConInvulnerable>(); if (c != null) c.Kill(); return "ok";')


def f1():
    fight(H, A, "carte de l'host")


GIFT = ('var c = EClass.game.cards.globalCharas.Find({uid}); var b = c.things.Find(t => t.id == "1171"); '
        'return (c.things.Find(t => t.id == "lockpick") != null) + "|" + (b == null ? "pas de coffre" : '
        'b.c_lockLv + "/" + string.Join(",", b.things.Select(t => t.id).OrderBy(x => x)));')


def g1():
    guest = state(A)["pc"]["uid"]
    got = lambda p: str(ev(p, GIFT.replace("{uid}", str(guest))))  # noqa: E731
    before = got(H)
    ev(H, 'var q = Quest.Create("fiama_lock"); q.Start(); return "ok";')
    want = "True|50/_meat,1172,amulet_begger"
    check(f"l'host commence la quete de la serrure : l'invite a son crochet et son coffre verrouille, chez l'host ({before} -> {got(H)})",
          eventually(lambda: got(H) == want, timeout=15))
    check(f"et dans son propre jeu ({got(A)})", eventually(lambda: got(A) == want, timeout=15))
    # le livre d'histoire de Fiama : donne quand son dialogue se ferme, hors de toute quete (le banc appelle DropReward)
    book = lambda p: str(ev(p, f'return EClass.game.cards.globalCharas.Find({guest}).things.Count(t => t.id == "book_story").ToString();'))  # noqa: E731
    had = int(book(H))
    ev(H, 'EClass.player.DropReward(ThingGen.Create("book_story")); return "ok";')
    check(f"le livre d'histoire de Fiama : l'invite a le sien, chez l'host ({had} -> {book(H)})",
          eventually(lambda: int(book(H)) == had + 1, timeout=15))
    check(f"et dans son propre jeu ({book(A)})", eventually(lambda: int(book(A)) == had + 1, timeout=15))


BOUNDS = 'var b = EClass._map.bounds; return b.x + "," + b.z + "," + b.maxX + "," + b.maxZ;'


def e1():
    bounds = lambda p: str(ev(p, BOUNDS))  # noqa: E731
    for buyer, other, who in ((A, H, "l'invite"), (H, A, "l'host")):
        before = bounds(other)
        ev(buyer, 'EClass._map.bounds.Expand(1); return "ok";')
        bought = bounds(buyer)
        if not check(f"{who} achete de la terre : ses limites grandissent ({before} -> {bought})", bought != before):
            continue
        check(f"l'autre joueur a les memes limites ({before} -> {bounds(other)})",
              eventually(lambda: bounds(other) == bought, timeout=10))


SETTING = ('var c = EClass.game.cards.globalCharas.Find({uid}) ?? EClass._map.charas.Find(x => x.uid == {uid}); '
           'return c.noMove + "|" + (c.orgPos == null ? "-" : c.orgPos.x + "," + c.orgPos.z) + "|" + c.GetInt(113);')
WHO = 'var c = EClass._map.charas.Find(x => x.uid == {uid});'


def r1():
    uid = int(ev(H, 'var c = EClass._map.charas.FirstOrDefault(x => !x.IsPC && !x.IsPCParty && x.IsGlobal && !x.isDead '
                    '&& x.hostility >= Hostility.Neutral); return c == null ? "0" : c.uid.ToString();'))
    if not check(f"un personnage a qui parler est sur la carte ({uid})", uid > 0):
        return
    got = lambda p: str(ev(p, SETTING.replace("{uid}", str(uid))))  # noqa: E731
    for port, other, who, value in ((A, H, "l'invite", 1), (H, A, "l'host", 0)):
        before = got(other)
        ev(port, WHO.replace("{uid}", str(uid)) + ' c.ShowDialog(); return "ok";')
        time.sleep(2)
        ev(port, WHO.replace("{uid}", str(uid)) + (' c.noMove = true; c.orgPos = new Point(c.pos); c.SetInt(113, 1);' if value else
                                                   ' c.noMove = false; c.orgPos = null; c.SetInt(113, 0);') + ' return "ok";')
        ev(port, 'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); return "ok";')
        mine = got(port)
        check(f"{who} regle l'habitant dans son dialogue ({mine})", mine.startswith(str(bool(value))))
        check(f"l'autre joueur a les memes reglages ({before} -> {got(other)})", eventually(lambda: got(other) == mine, timeout=10))


FISH = ('var c = EClass._map.charas.Find(x => x.uid == {uid}); var mine = EClass.player.fished; '
        'var n = 0; for (var i = 0; i < 6; i++) { var t = AI_Fish.Makefish(c); if (t != null) { n++; t.Destroy(); } } '
        'var m = System.AppDomain.CurrentDomain.GetAssemblies().First(a => a.GetName().Name == "ElinTogether").GetType("ElinTogether.Patches.AIFishPatch").GetMethod("FishedToday", '
        'System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic); '
        'return m.Invoke(null, new object[] { {uid} }) + "|" + (EClass.player.fished - mine) + "|" + n;')


def p1():
    guest = state(A)["pc"]["uid"]
    first = [int(x) for x in str(ev(H, FISH.replace("{uid}", str(guest)))).split("|")]
    second = [int(x) for x in str(ev(H, FISH.replace("{uid}", str(guest)))).split("|")]
    # (une peche peut ne rien prendre : le jeu ne compte que les prises)
    check(f"les prises de l'invite sont comptees pour lui, pas pour l'host (compte|host|prises : {first} puis {second})",
          first[1] == 0 and second[1] == 0 and first[2] > 0 and second[0] == first[0] + second[2])


DAGGERS = ('var all = new System.Collections.Generic.List<string>(); var c = EClass._map.charas.Find(x => x.uid == {uid}); '
           'c.things.Foreach(t => { if (t.id == "dagger") all.Add(t.isEquipped.ToString()); }, false); return string.Join(",", all);')


def x1():
    guest = state(A)["pc"]["uid"]
    ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {guest}); foreach (var t in c.things.List(t => t.id == "dagger", true)) t.Destroy(); '
          'c.AddThing(ThingGen.Create("dagger")); return "ok";')
    if not check("l'invite a une dague dans son sac, chez lui",
                 eventually(lambda: str(ev(A, DAGGERS.replace("{uid}", str(guest)))) == "False", timeout=10)):
        return
    uid = lambda p: str(ev(p, f'var c = EClass._map.charas.Find(x => x.uid == {guest}); var t = c.things.Find(x => x.id == "dagger"); '  # noqa: E731
                              'return t == null ? "0" : t.uid.ToString();'))
    old = uid(H)
    ev(A, 'var t = EClass.pc.things.Find(x => x.id == "dagger"); var l = LayerDragGrid.CreateReconstruction(EClass.pc); '
          'l.owner.OnProcess(t); l.Close(); return "ok";')
    check(f"l'objet est refait chez l'host ({old} -> {uid(H)})", eventually(lambda: uid(H) not in ("0", old), timeout=10))
    for port, who in ((H, "chez l'host"), (A, "chez l'invite")):
        check(f"{who}, la dague neuve est dans le sac de l'invite, pas equipee ({ev(port, DAGGERS.replace('{uid}', str(guest)))})",
              eventually(lambda port=port: str(ev(port, DAGGERS.replace("{uid}", str(guest)))) == "False", timeout=10))


ARTIFACT = ('var row = EClass.sources.things.rows.First(r => r.tag != null && r.tag.Contains("godArtifact")); '
            'var g = EClass._map.charas.Find(x => x.uid == {uid}); var count = new System.Func<Chara, int>(c => c.things.List(t => t.id == row.id, true).Count); '
            'foreach (var c in new[] { EClass.pc, g }) foreach (var t in c.things.List(t => t.id == row.id, true)) t.Destroy(); '
            'EClass.pc.AddThing(ThingGen.Create(row.id)); var first = count(EClass.pc); g.AddThing(ThingGen.Create(row.id)); '
            'return row.id + "|" + first + "|" + count(EClass.pc) + "|" + count(g);')


def a1():
    guest = state(A)["pc"]["uid"]
    got = str(ev(H, ARTIFACT.replace("{uid}", str(guest))))
    check(f"l'host a son artefact, l'invite prend le sien : les deux existent (objet|host avant|host apres|invite : {got})",
          got.split("|")[1:] == ["1", "1", "1"])


def d1():
    guest = state(A)["pc"]["uid"]
    made = str(ev(H, 'var c = CharaGen.Create("farmer"); c.SetGlobal(); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(false, false)); EClass.Branch.AddMemeber(c); '
                     f'var g = EClass._map.charas.Find(x => x.uid == {guest}); foreach (var who in new[] {{ EClass.pc, g }}) '
                     'foreach (var t in who.things.List(t => t.id == "luckydagger", true)) t.Destroy(); '
                     'c.AddThing(ThingGen.Create("luckydagger")); return c.uid + "|" + c.things.List(t => t.id == "luckydagger", true).Count;'))
    uid, has = made.split("|")
    if not check(f"un habitant de la base porte un artefact de dieu ({made})", has == "1"):
        return
    eventually(lambda: ev(A, f'(EClass._map.charas.Find(x => x.uid == {uid}) != null).ToString()') == "True", timeout=10)
    ev(A, 'var asm = System.AppDomain.CurrentDomain.GetAssemblies().First(a => a.GetName().Name == "ElinTogether"); '
          'var kind = asm.GetTypes().First(t => t.Name == "BaseRequestKind"); var delta = asm.GetTypes().First(t => t.Name == "BaseRequestDelta"); '
          'HarmonyLib.AccessTools.Method(delta, "Send").Invoke(null, new object[] { System.Enum.Parse(kind, "Banish"), "' + uid + '", 0 }); return "ok";')
    count = lambda p, who: str(ev(p, f'{who}.things.List(t => t.id == "luckydagger", true).Count.ToString()'))  # noqa: E731
    g = f'EClass._map.charas.Find(x => x.uid == {guest})'
    check(f"l'invite le renvoie : l'artefact est dans le sac de l'invite, chez l'host ({count(H, g)}), pas chez l'host ({count(H, 'EClass.pc')})",
          eventually(lambda: count(H, g) == "1" and count(H, "EClass.pc") == "0", timeout=15))
    check(f"et l'invite l'a dans son propre jeu ({count(A, 'EClass.pc')})", eventually(lambda: count(A, "EClass.pc") == "1", timeout=15))


def w1():
    guest = state(A)["pc"]["uid"]
    npc = int(ev(H, 'var c = CharaGen.Create("farmer"); EClass._zone.AddCard(c, EClass._map.charas.Find(x => x.uid == %d).pos.GetNearestPoint(false, false)); '
                    'c.noMove = true; return c.uid.ToString();' % guest))
    gold = lambda: int(ev(H, f'EClass._map.charas.Find(x => x.uid == {guest}).GetCurrency().ToString()'))  # noqa: E731
    ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {guest}); g.ModCurrency(5000 - g.GetCurrency()); return "ok";')
    eventually(lambda: ev(A, f'(EClass._map.charas.Find(x => x.uid == {npc}) != null).ToString()') == "True", timeout=10)
    time.sleep(2)
    before = gold()
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {npc}); EClass.pc.SetAI(new AI_Fuck {{ target = c }}); return "ok";')
    time.sleep(2)
    done = eventually(lambda: ev(A, '(EClass.pc.ai is AI_Fuck).ToString()') == "False", timeout=90)
    time.sleep(3)
    check(f"la tache finie, l'or de l'invite n'a pas bouge chez l'host ({before} -> {gold()})", done and gold() == before)
    ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {npc}); if (c != null) c.Destroy(); return "ok";')


def i1():
    npc = int(ev(H, 'var c = EClass._map.charas.FirstOrDefault(x => !x.IsPC && !x.IsPCParty && x.IsGlobal && !x.isDead '
                    '&& x.hostility >= Hostility.Neutral); return c == null ? "0" : c.uid.ToString();'))
    if not check(f"un personnage a qui parler est sur la carte ({npc})", npc > 0):
        return
    tax = lambda p: int(ev(p, 'EClass.player.extraTax.ToString()'))  # noqa: E731
    for port, other, who, value in ((A, H, "l'invite", 300), (H, A, "l'host", 0)):
        before = tax(other)
        ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {npc}); c.ShowDialog(); return "ok";')
        time.sleep(2)
        ev(port, f'EClass.player.extraTax = {value}; if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); return "ok";')
        check(f"{who} choisit {value} d'impot supplementaire : l'autre jeu l'a ({before} -> {tax(other)})",
              eventually(lambda: tax(other) == value, timeout=10))


def k1():
    boss = int(ev(H, 'var m = CharaGen.Create("putit"); m.hostility = m.c_originalHostility = Hostility.Neutral; '
                     'EClass._zone.AddCard(m, EClass.pc.pos.GetNearestPoint(false, false)); m.noMove = true; EClass._zone.uidBoss = m.uid; return m.uid.ToString();'))
    eventually(lambda: ev(A, f'(EClass._map.charas.Find(x => x.uid == {boss}) != null).ToString()') == "True", timeout=10)
    ev(A, f'EClass._zone.uidBoss = {boss}; return "ok";')
    seen = lambda p: str(ev(p, 'return EClass.player.fame + "|" + EClass._zone.uidBoss + "|" + EClass.game.log.dict.Values.Count(x => x.text != null && x.text.Contains(Lang.Game.Get("boss_win").Split((char)35)[0].Trim()));'))  # noqa: E731
    before = {p: seen(p).split("|") for p in (H, A)}
    ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {boss}); m.DamageHP(99999, AttackSource.None, EClass.pc); return "ok";')
    eventually(lambda: seen(A).split("|")[1] == "0", timeout=20)
    time.sleep(1)
    after = {p: seen(p).split("|") for p in (H, A)}
    for who, p in (("l'host", H), ("l'invite", A)):
        check(f"{who} : le boss est tombe, plus de boss dans la zone, renommee gagnee (renommee|boss|messages : {before[p]} -> {after[p]})",
              after[p][1] == "0" and int(after[p][0]) > int(before[p][0]))


def j1():
    exp = lambda p: int(ev(p, 'var e = EClass.pc.elements.GetOrCreateElement(70); return (e.vBase * 1000 + e.vExp).ToString();'))  # noqa: E731
    for port, other, who in ((H, A, "l'host"), (A, H, "l'invite")):
        before = exp(other)
        ev(port, 'EClass.pc.ModExpParty(70, 300); return "ok";')
        check(f"{who} recolte : l'autre joueur gagne aussi l'experience d'equipe, dans son jeu ({before} -> {exp(other)})",
              eventually(lambda: exp(other) > before, timeout=15))


SEEDS = ('var c = EClass.game.cards.globalCharas.Find({uid}); return (EClass._map.things.Where(t => t.pos.Equals(c.pos))'
         '.Concat(c.things.List(t => true, true)).Where(t => t.trait is TraitSeed).Sum(t => t.Num)).ToString();')


def s2():
    host, guest = state(H)["pc"]["uid"], state(A)["pc"]["uid"]
    seeds = lambda p, uid: int(ev(p, SEEDS.replace("{uid}", str(uid))))  # noqa: E731
    before = {"host": seeds(H, host), "guest": seeds(H, guest)}
    # la quete est celle du monde : commencee chez l'host, connue de l'invite, terminee par l'invite
    ev(H, 'foreach (var old in EClass.game.quests.list.Where(x => x.id == "curry").ToList()) EClass.game.quests.Remove(old); '
          'EClass.game.quests.Start(Quest.Create("curry")); return "ok";')
    if not check("l'invite connait la quete du curry commencee dans le monde",
                 eventually(lambda: ev(A, '(EClass.game.quests.list.Find(x => x.id == "curry") != null).ToString()') == "True", timeout=15)):
        return
    before = {"host": seeds(H, host), "guest": seeds(H, guest)}
    ev(A, 'EClass.game.quests.list.Find(x => x.id == "curry").Complete(); return "ok";')
    check(f"l'invite termine la quete du curry : il a ses graines, chez l'host ({before['guest']} -> {seeds(H, guest)})",
          eventually(lambda: seeds(H, guest) > before["guest"], timeout=20))
    gained = seeds(H, guest) - before["guest"]
    check(f"l'host recoit sa part, autant ({before['host']} -> {seeds(H, host)}, l'invite en a gagne {gained})",
          eventually(lambda: seeds(H, host) - before["host"] == gained, timeout=20))
    time.sleep(5)
    check(f"et une seule fois, 5 s plus tard (host +{seeds(H, host) - before['host']}, invite +{seeds(H, guest) - before['guest']})",
          seeds(H, host) - before["host"] == gained and seeds(H, guest) - before["guest"] == gained)
    check(f"l'invite voit la meme chose dans son jeu (lui +?, compte {seeds(A, guest)} contre {seeds(H, guest)} chez l'host)",
          eventually(lambda: seeds(A, guest) == seeds(H, guest), timeout=15))


def u1():
    guest = state(A)["pc"]["uid"]
    shop = int(ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {guest}); var m = CharaGen.Create("merchant"); '
                     'EClass._zone.AddCard(m, g.pos.GetNearestPoint(false, false)); m.noMove = true; return m.uid.ToString();'))
    uid = int(ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {guest}); var t = ThingGen.Create("axe_battle"); t.c_IDTState = 5; g.AddThing(t); return t.uid.ToString();'))
    # (par la table des cartes du mod : chez l'invite le coffre du marchand n'est pas parcouru par c.things.List)
    idt = lambda p: str(ev(p, 'var asm = System.AppDomain.CurrentDomain.GetAssemblies().First(a => a.GetName().Name == "ElinTogether"); '  # noqa: E731
                              'var t = HarmonyLib.AccessTools.Method(asm.GetType("ElinTogether.Models.CardCache"), "Find", new[] { typeof(int) })'
                              '.Invoke(null, new object[] { %d }) as Thing; return t == null ? "introuvable" : t.c_IDTState + "|" + t.GetRootCard().uid;' % uid))
    if not check(f"l'invite a une hache non identifiee, dans les deux jeux ({idt(H)} / {idt(A)}), et un marchand a cote ({shop})",
                 eventually(lambda: idt(A).startswith("5|") and idt(H).startswith("5|")
                            and ev(A, f'(EClass._map.charas.Find(x => x.uid == {shop}) != null).ToString()') == "True", timeout=10)):
        return
    ev(A, f'var f = EClass._map.charas.Find(x => x.uid == {shop}); f.trait.OnBarter(); if (!LayerInventory.listInv.Any(q => q.mainInv)) EClass.ui.OpenFloatInv(true); '
          'EClass.ui.AddLayer(LayerInventory.CreateBuy(f, f.trait.CurrencyType, f.trait.PriceType)); return "ok";')
    time.sleep(2)
    sold = str(ev(A, BUY.replace("{uid}", str(uid))))
    time.sleep(3)
    ev(A, CLOSE)
    check(f"l'invite la vend au marchand ({sold}) : chez lui elle est identifiee, chez le marchand ({idt(A)})",
          eventually(lambda: idt(A) == f"0|{shop}", timeout=10))
    check(f"chez l'host aussi ({idt(H)})", eventually(lambda: idt(H) == f"0|{shop}", timeout=10))
    ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {shop}); if (m != null) m.Destroy(); return "ok";')


LEDGER = ('var t = System.AppDomain.CurrentDomain.GetAssemblies().First(a => a.GetName().Name == "ElinTogether").GetType("ElinTogether.Net.ElinNetHost"); '
          'var f = System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic; '
          'var rewards = (System.Collections.Generic.Dictionary<int, byte[]>)t.GetProperty("StoryRewards", f).GetValue(null); '
          'var received = (System.Collections.Generic.Dictionary<int, int[]>)t.GetProperty("StoryReceived", f).GetValue(null); '
          'var seeded = (int[])t.GetProperty("StorySeeded", f).GetValue(null); ')
PARCELS = ('return string.Join(";", EClass.game.cards.listPackage.Where(p => p.c_idRefName != null && p.c_idRefName.Contains("{name}"))'
           '.Select(p => string.Join(",", p.things.Select(t => t.id + "x" + t.Num).OrderBy(x => x))));')


def s3():
    from travel_suite import VERNIS, both_joined, client_settled, move, wait  # noqa: PLC0415
    names = {"host": state(H)["pc"]["name"].split(" ")[-1].strip("「」"), "invite": state(A)["pc"]["name"].split(" ")[-1].strip("「」")}
    parcels = lambda who: str(ev(H, PARCELS.replace("{name}", names[who])))  # noqa: E731
    before = {w: parcels(w) for w in names}
    ev(H, LEDGER + 'rewards.Clear(); received.Clear(); EClass.game.quests.completedTypes.Add("QuestDefense"); '
                   'EClass.game.quests.completedTypes.Add("QuestPuppy"); seeded[0] = 0; return "ok";')
    time.sleep(3)
    got = str(ev(H, LEDGER + 'return seeded[0] + "|" + rewards.Count + "|" + string.Join(",", received.Values.Select(v => v.Length));'))
    mark, count, had = got.split("|")
    # (deux quetes marquees ici, plus celles que les etapes d'avant ont finies pour de bon : le curry)
    check(f"le registre est rempli une fois : marque, au moins deux recompenses, recues par l'host seulement pour l'instant ({got})",
          mark == "1" and int(count) >= 2 and set(had.split(",")) == {"1"})
    check(f"l'host a son colis de rattrapage ({before['host']!r} -> {parcels('host')!r})",
          "coolerbox" in parcels("host") and "plat" in parcels("host") and parcels("host") != before["host"])
    try:
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        time.sleep(3)
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)
    check(f"l'invite, de retour chez l'host, a le sien ({before['invite']!r} -> {parcels('invite')!r})",
          eventually(lambda: "coolerbox" in parcels("invite") and "plat" in parcels("invite"), timeout=20))
    mine, its = parcels("host"), parcels("invite")
    ev(H, LEDGER + 'var m = t.GetMethod("SeedOldWorld", f); m.Invoke(null, null); return "ok";')
    time.sleep(3)
    check("une seule fois : rien de plus apres un second appel", parcels("host") == mine and parcels("invite") == its)


BILLS = ('var t = System.AppDomain.CurrentDomain.GetAssemblies().First(a => a.GetName().Name == "ElinTogether").GetType("ElinTogether.Net.ElinNetHost"); '
         'var f = System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic; '
         'var count = new System.Func<int>(() => (int)t.GetMethod("CountTaxBills", f).Invoke(null, null)); '
         'var repair = new System.Func<bool, int>(again => (int)t.GetMethod("RepairBillCount", f).Invoke(null, new object[] { again })); ')


def z1():
    guest = state(A)["pc"]["uid"]
    made = str(ev(H, BILLS + f'var g = EClass._map.charas.Find(x => x.uid == {guest}); var before = EClass.player.taxBills; var had = count(); '
                             'EClass.pc.AddThing(ThingGen.CreateBill(100, true)); EClass.pc.AddThing(ThingGen.CreateBill(120, true)); '
                             'g.AddThing(ThingGen.CreateBill(140, true)); return before + "|" + had + "|" + EClass.player.taxBills + "|" + count();'))
    before, had, counted, found = (int(x) for x in made.split("|"))
    check(f"trois factures faites : le compteur monte de trois et le mod les trouve toutes, celle de l'invite aussi (compteur {before} -> {counted}, trouvees {had} -> {found})",
          counted == before + 3 and found == had + 3)
    got = str(ev(H, BILLS + 'EClass.player.taxBills += 4; var up = EClass.player.taxBills; var off = repair(true); '
                            'return up + "|" + off + "|" + EClass.player.taxBills + "|" + count();'))
    up, off, now, found = (int(x) for x in got.split("|"))
    check(f"quatre factures fantomes ajoutees au compteur ({up}) : la reparation les retire, le compteur vaut les factures trouvees ({off} retirees, compteur {now}, trouvees {found})",
          now == found and off == up - found and off >= 4)
    got = str(ev(H, BILLS + 'var off = repair(true); EClass.player.taxBills -= 1; var low = EClass.player.taxBills; var off2 = repair(true); '
                            'return off + "|" + low + "|" + off2 + "|" + EClass.player.taxBills;'))
    check(f"rien a retirer une seconde fois, et un compteur plus bas que les factures n'est jamais releve (retirees|compteur baisse|retirees|compteur : {got})",
          got.split("|")[0] == "0" and got.split("|")[2] == "0" and got.split("|")[1] == got.split("|")[3])
    got = str(ev(H, BILLS + 'EClass.player.taxBills += 5; var off = repair(false); var kept = EClass.player.taxBills; var off2 = repair(true); '
                            'return off + "|" + kept + "|" + off2 + "|" + EClass.player.taxBills + "|" + count();'))
    off, kept, off2, now, found = (int(x) for x in got.split("|"))
    check(f"tout seul une seule fois par monde (deja fait a l'ouverture : rien), puis a la demande de l'host (retirees|compteur|retirees|compteur|trouvees : {got})",
          off == 0 and off2 == kept - found and off2 > 0 and now == found)
    # menage : les trois factures du banc et leur part du compteur
    ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {guest}); foreach (var who in new[] {{ EClass.pc, g }}) '
          'foreach (var b in who.things.List(t => t.id == "bill_tax" && (t.c_bill == 100 || t.c_bill == 120 || t.c_bill == 140), true)) b.Destroy(); '
          f'EClass.player.taxBills = {before}; return "ok";')


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

SHOP = 'var f = EClass._map.charas.Find(c => c.trait is TraitFiama); var chest = f == null ? null : f.things.Find("chest_merchant"); '
LIMITED = SHOP + ('if (chest == null) return ""; return string.Join(";", chest.things.Where(t => t.GetInt(101) != 0)'
                  '.Select(t => t.uid + "|" + t.id + "|" + t.trait.IdNoRestock + "|" + t.GetStr("emp_limited_buyers") + "|" + t.Num));')
RESTOCK = SHOP + 'if (f == null) return "pas de Fiama"; f.c_dateStockExpire = 0; f.isRestocking = false; f.trait.OnBarter(); return "ok";'
OPEN = SHOP + ('f.trait.OnBarter(); if (!LayerInventory.listInv.Any(q => q.mainInv)) EClass.ui.OpenFloatInv(true); '
               'EClass.ui.AddLayer(LayerInventory.CreateBuy(f, f.trait.CurrencyType, f.trait.PriceType)); return "ok";')
BUY = ('var b = LayerInventory.listInv.SelectMany(q => q.GetComponentsInChildren<ButtonGrid>(true))'
       '.FirstOrDefault(x => x.card != null && x.card.uid == {uid}); if (b == null) return "bouton absent"; '
       # (Process(true) est le clic : il paie puis tient l'objet en main, a poser ; sans argument c'est maj+clic, droit au sac)
       'return new InvOwner.Transaction(b, 1).Process().ToString();')
CLOSE = ('var l = LayerInventory.listInv.FirstOrDefault(q => q.invs.Count > 0 && q.invs[0].owner is InvOwnerShop); '
         'if (l == null) return "pas de boutique"; l.Close(); return "ok";')


def limited(port=H):
    """Objets « stock limite » de la boutique : cle -> (numero, {joueur: combien achetes}, taille de la pile), vus par ce jeu."""
    out = {}
    for row in filter(None, str(ev(port, LIMITED)).split(";")):
        uid, tid, key, buyers, num = row.split("|")
        out[f"{tid}/{key}"] = (int(uid), dict(b.split(":") for b in buyers.split(",") if ":" in b), int(num))
    return out


def buys(port, key, who):
    """Ce joueur ouvre la boutique, achete cet objet, ferme. Renvoie ce que rend l'achat."""
    ev(port, OPEN)
    time.sleep(2)
    # dans la monnaie du marchand (Fiama se paie en lingots, pas en orens) ; la monnaie d'un joueur est a lui
    ev(port, 'var id = InvOwner.Trader.currency.ToString().ToLowerInvariant(); if (EClass.pc.GetCurrency(id) < 100) EClass.pc.ModCurrency(100, id); return "ok";')
    time.sleep(1)
    uid = limited(port).get(key, (0, ""))[0]
    if not check(f"{who} voit l'objet dans la boutique ({uid})", uid):
        ev(port, CLOSE)
        return "absent"
    r = str(ev(port, BUY.replace("{uid}", str(uid))))
    time.sleep(3)
    ev(port, CLOSE)
    time.sleep(3)
    return r


def l1():
    guest, host = str(state(A)["pc"]["uid"]), str(state(H)["pc"]["uid"])
    if not check(f"Fiama est sur la carte et son stock est fait ({ev(H, RESTOCK)})", limited()):
        return
    none = (0, {}, 0)
    n0 = len(limited())
    key = next((k for k, v in sorted(limited().items()) if v[2] == 1), None)
    pile = next((k for k, v in sorted(limited().items()) if v[2] > 1), None)
    if not check(f"un objet a stock limite a l'unite ({key}) et une pile ({pile})", key and pile):
        return
    r = buys(A, key, "l'invite")
    check(f"l'invite achete « {key} » ({r}) : l'objet est de nouveau dans la boutique, note pour lui ({limited().get(key)})",
          eventually(lambda: limited().get(key, none)[1].get(guest) == "1" and limited()[key][2] == 1, timeout=15))
    check(f"autant d'objets a stock limite qu'avant ({n0} -> {len(limited())})", len(limited()) == n0)
    check("l'invite voit le meme objet que l'host dans la boutique",
          eventually(lambda: limited(A).get(key, none)[0] == limited().get(key, (-1,))[0], timeout=20))
    r = buys(A, key, "l'invite, une seconde fois,")
    time.sleep(2)
    check(f"l'invite ne peut pas le racheter ({r} ; {limited().get(key)})", limited().get(key, none)[1] == {guest: "1"})
    r = buys(H, key, "l'host")
    check(f"l'host l'achete a son tour ({r}) : l'objet reste, note pour les deux ({limited().get(key)})",
          eventually(lambda: limited().get(key, none)[1] == {guest: "1", host: "1"} and limited()[key][2] == 1, timeout=15))
    size, had = limited()[pile][2], int(limited()[pile][1].get(guest, 0))
    r = buys(A, pile, "l'invite, pour la pile,")
    check(f"l'invite achete un exemplaire d'une pile de {size} ({r}) : la pile est entiere pour les autres, un de plus note pour lui ({limited().get(pile)})",
          eventually(lambda: limited().get(pile, none)[1].get(guest) == str(had + 1) and limited()[pile][2] == size, timeout=15))
    ev(H, RESTOCK)
    time.sleep(2)
    after = limited()
    check(f"un reassort ne double rien et garde les acheteurs ({len(after)} objets, {after.get(key)})",
          len(after) == n0 and after.get(key, none)[1] == {guest: "1", host: "1"})
    ev(H, SHOP + f'var t = chest.things.Find(x => x.uid == {after[key][0]}); if (t != null) t.Destroy(); return "ok";')
    check("retire a la main (monde d'avant : deja vendu, plus rien dans la boutique)", key not in limited())
    ev(H, RESTOCK)
    time.sleep(2)
    check(f"il revient au reassort suivant, pour tous ({limited().get(key)})", key in limited() and not limited()[key][1])

def m1():
    import guest_suite as g  # noqa: PLC0415
    from travel_suite import VERNIS, both_joined, client_settled, move, wait  # noqa: PLC0415
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    uid = ctx["a"][1]
    m = g.tame(ctx, "horse", "a")
    if not check(f"l'invite a un cheval ({m})", m):
        return
    g.clear_conditions(m)
    rides = ev(A, f'var m = EClass._map.charas.Find(x => x.uid == {m}); ACT.Create(6018).Perform(EClass.pc, m, m.pos); return (EClass.pc.ride == m).ToString();')
    check(f"l'invite le monte, par l'acte du jeu ({rides})", rides == "True")
    known = eventually(lambda: ev(H, f'var r = EClass.game.cards.globalCharas.Find({uid}); return (r.ride != null && r.ride.uid == {m}).ToString();') == "True", timeout=15)
    check("l'host sait que l'invite est monte", known)
    look = (f'var r = EClass.game.cards.globalCharas.Find({uid}); var w = EClass.game.cards.globalCharas.Find({m}); '
            f'var cells = 0; EClass._map.ForeachCell(c => {{ if (c.detail != null && c.detail.charas != null) cells += c.detail.charas.Count(x => x.uid == {m}); }}); '
            'return (r.ride != null && ReferenceEquals(r.ride, w)) + "|" + (w.host != null && ReferenceEquals(w.host, r)) + "|" + w.pos.Equals(r.pos) + "|" + '
            f'EClass._map.charas.Count(x => x.uid == {m}) + "|" + cells + "|" + r.pos + "|" + w.pos;')
    try:
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis, sur son cheval", timeout=180)
        time.sleep(3)
        ev(A, 'for (var i = 0; i < 4; i++) EClass.pc.TryMoveTowards(new Point(EClass.pc.pos.x + 6, EClass.pc.pos.z)); return "ok";')
        time.sleep(2)
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)
    time.sleep(4)
    for _ in range(3):
        ev(A, 'EClass.pc.TryMoveTowards(new Point(EClass.pc.pos.x - 6, EClass.pc.pos.z)); return "ok";')
        time.sleep(1.2)
    for who, port in (("chez l'host", H), ("chez l'invite", A)):
        same, back, tile, listed, cells, at, mount = str(ev(port, look)).split("|")
        check(f"{who} : le cavalier monte la monture du monde, qui le porte ({same}, {back})", same == "True" and back == "True")
        check(f"{who} : la monture est sur la case du cavalier ({mount} / {at})", tile == "True")
        check(f"{who} : une seule fois sur la carte et dans ses cases ({listed}, {cells})", listed == "1" and cells == "1")
    ev(A, 'if (EClass.pc.ride != null) ActRide.Unride(EClass.pc, false, false); return "ok";')

NEAR = ('var c = EClass.game.cards.globalCharas.Find({uid}); return string.Join(",", EClass._map.things.Where(t => t.pos.Equals(c.pos))'
        '.Concat(c.things).Where(t => t.trait is TraitSeed || t.id == "bucket").Select(t => t.id + "x" + t.Num).OrderBy(x => x));')
MAIL = ('string.Join(";", EClass.game.cards.listPackage.Where(p => p.c_idRefName != null && p.c_idRefName.Contains("{name}"))'
        '.Select(p => string.Join(",", p.things.Select(t => t.id + "x" + t.Num).OrderBy(x => x))))')


def s1():
    from travel_suite import VERNIS, both_joined, client_settled, move, wait  # noqa: PLC0415
    host, guest = state(H)["pc"]["uid"], state(A)["pc"]
    near = lambda p, uid: str(ev(p, NEAR.replace("{uid}", str(uid))))  # noqa: E731
    before = near(H, guest["uid"])
    ev(H, 'var q = Quest.Create("curry"); q.Complete(); return "ok";')
    time.sleep(3)
    mine = near(H, host)
    check(f"l'host termine la quete du curry : sa recompense est a ses pieds ({mine})", "seed" in mine)
    check(f"l'invite present a la meme chose (dans son sac), chez l'host ({near(H, guest['uid'])})",
          eventually(lambda: near(H, guest["uid"]) == mine and near(H, guest["uid"]) != before, timeout=15))
    check(f"et dans son propre jeu ({near(A, guest['uid'])})", eventually(lambda: near(A, guest["uid"]) == mine, timeout=15))
    told = str(ev(H, 'return "emp_story_share_got".lang().Split((char)123)[0];'))
    check(f"l'invite lit qu'il recoit sa part (« {told}... » dans son journal)", told.strip() != "emp_story_share_got" and eventually(
        lambda: str(ev(A, 'return EClass.game.log.dict.Values.Any(x => x.text != null && x.text.Contains("' + told + '")).ToString();')) == "True", timeout=10))
    ev(H, 'EClass.player.DropReward(ThingGen.Create("bucket")); return "ok";')
    time.sleep(3)
    check(f"une recompense hors de l'histoire (un seau lache par le jeu) ne donne pas de part ({near(H, guest['uid'])})",
          "bucket" in near(H, host) and "bucket" not in near(H, guest["uid"]))
    # la case de l'host « une fois par monde = une fois par joueur » decochee : comme le jeu, rien pour l'invite
    from combat_suite import set_option  # noqa: PLC0415
    set_option("OncePerPlayer", False)
    try:
        time.sleep(2)
        seen = near(H, guest["uid"])
        ev(H, 'var q = Quest.Create("curry"); q.Complete(); return "ok";')
        time.sleep(4)
        check(f"case decochee : pas de part pour l'invite ({near(H, guest['uid'])})", near(H, guest["uid"]) == seen)
    finally:
        set_option("OncePerPlayer", True)
        time.sleep(2)
    mail = lambda: str(ev(H, MAIL.replace("{name}", guest["name"].split(" ")[-1].strip("「」"))))  # noqa: E731
    m0 = mail()
    try:
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        time.sleep(3)
        ev(H, 'var q = Quest.Create("curry"); q.Complete(); return "ok";')
        check(f"l'invite ailleurs : un colis a son nom part au courrier de la base ({mail()})",
              eventually(lambda: mail() != m0 and "seed" in mail(), timeout=15))
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)
    # un joueur arrive plus tard dans le monde : le registre du monde ne le connait pas pour ces recompenses (ici le
    # banc efface l'invite du registre), il recoit a son arrivee UN colis a son nom avec ce qu'il n'a pas eu, une fois
    time.sleep(3)
    parcels = lambda: int(ev(H, 'EClass.game.cards.listPackage.Count(p => p.c_idRefName != null && p.c_idRefName.Contains("{name}")).ToString()'  # noqa: E731
                                .replace("{name}", guest["name"].split(" ")[-1].strip("「」"))))
    p0 = parcels()
    forgot = ev(H, 'var t = HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetHost"); '
                   'var d = (System.Collections.Generic.Dictionary<int, int[]>)HarmonyLib.AccessTools.Property(t, "StoryReceived").GetValue(null); '
                   f'foreach (var k in d.Keys.ToList()) d[k] = d[k].Where(u => u != {guest["uid"]}).ToArray(); return d.Count.ToString();')
    check(f"le registre du monde garde les recompenses d'histoire donnees ({forgot})", int(forgot) >= 2)
    for turn, want in ((1, p0 + 1), (2, p0 + 1)):
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite repart a Vernis", timeout=180)
        time.sleep(3)
        move(A, HOME)
        both_joined(H, A, HOME)
        time.sleep(3)
        label = "arrive « plus tard » : un colis a son nom avec ce qu'il n'avait pas eu" if turn == 1 else "revient encore : pas de second colis"
        check(f"l'invite {label} ({p0} -> {parcels()})", parcels() == want)
    inside = ev(H, 'var p = EClass.game.cards.listPackage.Last(x => x.c_idRefName != null); return string.Join(",", p.things.Select(t => t.id + "x" + t.Num));')
    check(f"le colis contient les recompenses du registre ({inside})", "seed" in inside)

TAKE = ('var t = EClass._map.things.Find(x => x.uid == {uid}); if (t == null) return "tresor absent"; '
        'var p = new ActPlan { input = ActInput.RightMouse }; p.pos.Set(t.pos); p.dist = EClass.pc.pos.Distance(p.pos); '
        'HarmonyLib.AccessTools.Field(typeof(ActPlan), "_canInteractNeighbor").SetValue(p, p.dist <= 1); '
        'HotItemNoItem._TrySetAct(p); var item = p.list.FirstOrDefault(i => i.act is DynamicAct d && d.id == "actHold"); '
        'if (item == null) return "action absente : " + string.Join(",", p.list.Select(i => i.act is DynamicAct d ? d.id : i.act.GetType().Name)); '
        'item.Perform(); return "pris";')
MINE = ('EClass.player.flags.pickedMelilithTreasure + "/" + EClass.player.flags.gotMelilithCurse + "/" + EClass.pc.Evalue(1206) + "/" + '
        '(EClass.player.dialogFlags.ContainsKey("emp_melilith_taken") ? EClass.player.dialogFlags["emp_melilith_taken"] : 0)')
PHASE = 'var q = EClass.game.quests.Get<QuestCursedManor>(); return q == null ? "aucune" : q.phase.ToString();'


def t1():
    def treasure(port_of):
        uid = state(port_of)["pc"]["uid"]
        return int(ev(H, f'var c = EClass.game.cards.globalCharas.Find({uid}); var t = ThingGen.Create("bucket"); '
                         't.c_editorTags = "TreasureMelilith"; EClass._zone.AddCard(t, c.pos); return t.uid.ToString();'))
    # les drapeaux « a soi » d'un invite sont gardes dans son fichier de reglages, par monde et par personnage : le monde
    # du banc est remis a neuf a chaque passe et le personnage de test reprend souvent le meme numero, il retrouvait
    # alors « tresor deja pris » d'une passe d'avant (rouge du 2026-10-12 : maudit des le premier tresor)
    for p in (H, A):
        ev(p, 'EClass.player.flags.pickedMelilithTreasure = false; EClass.player.flags.gotMelilithCurse = false; EClass.pc.SetFeat(1206, 0); return "ok";')
    time.sleep(2)
    started = ev(H, 'var row = EClass.sources.quests.rows.FirstOrDefault(r => r.type == "QuestCursedManor"); if (row == null) return "pas de ligne"; '
                    'if (EClass.game.quests.Get<QuestCursedManor>() == null) EClass.game.quests.Start(row.id); return row.id;')
    time.sleep(3)
    p0 = str(ev(H, PHASE))
    log(f"quete du manoir : {started}, phase {p0} chez l'host, {ev(A, PHASE)} chez l'invite")
    first = treasure(A)
    eventually(lambda: ev(A, f'(EClass._map.things.Find(x => x.uid == {first}) != null).ToString()') == "True", timeout=10)
    r = ev(A, TAKE.replace("{uid}", str(first)))
    time.sleep(3)
    check(f"l'invite prend un tresor ({r}) : note pour lui, pas maudit ({ev(A, MINE)})", str(ev(A, MINE)).startswith("True/False/0"))
    check(f"le monde sait qu'un tresor a ete pris, chez l'host ({ev(H, MINE)})", eventually(lambda: str(ev(H, MINE)).endswith("/1"), timeout=15)
          if p0 != "aucune" else True)
    check(f"l'host n'est pas note comme ayant pris le sien ({ev(H, MINE)})", str(ev(H, MINE)).startswith("False/False/0"))
    p1 = str(ev(H, PHASE))
    second = treasure(H)
    r = ev(H, TAKE.replace("{uid}", str(second)))
    time.sleep(3)
    check(f"l'host prend le sien ({r}) : pas maudit ({ev(H, MINE)})", str(ev(H, MINE)).startswith("True/False/0"))
    if p0 != "aucune":
        check(f"la quete du groupe a avance une seule fois ({p0} -> {p1} -> {ev(H, PHASE)})",
              p1 != p0 and str(ev(H, PHASE)) == p1 and eventually(lambda: str(ev(A, PHASE)) == p1, timeout=15))
    third = treasure(A)
    eventually(lambda: ev(A, f'(EClass._map.things.Find(x => x.uid == {third}) != null).ToString()') == "True", timeout=10)
    r = ev(A, TAKE.replace("{uid}", str(third)))
    time.sleep(3)
    check(f"un second tresor pour l'invite ({r}) : maudit, comme le veut le jeu ({ev(A, MINE)})", str(ev(A, MINE)).startswith("True/True/1"))
    # (le banc retire la malediction de son personnage de test)
    ev(A, 'EClass.pc.SetFeat(1206, 0); EClass.player.flags.gotMelilithCurse = false; return "ok";')


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
    try:
        offers()
    finally:
        # (retour : les suites lancees ensuite sur ces fenetres partent de la carte de depart)
        host_goto(H, A, HOME)


def offers():
    before = str(ev(H, OFFERS))
    check(f"depart : memes offres a Mysilia ({before.count(',') + 1 if before else 0})",
          eventually(lambda: str(ev(A, OFFERS)) == str(ev(H, OFFERS)), timeout=30))
    ev(H, 'EClass._zone.UpdateQuests(true); "ok"')
    after = str(ev(H, OFFERS))
    check("le tirage a change les offres de l'host", after != before)
    check(f"apres le tirage : memes offres chez l'invite (host {after} ; invite {ev(A, OFFERS)})",
          eventually(lambda: str(ev(A, OFFERS)) == str(ev(H, OFFERS)), timeout=30))
    # le bouton « Reroll Quests » du tableau chez l'INVITE (ce que fait son clic : UpdateQuests(true) dans son jeu,
    # puis l'influence en moins) : c'est le jeu qui tient la carte qui tire
    ev(H, 'EClass._zone.influence = 5; "ok"')
    ev(A, 'EClass._zone.UpdateQuests(true); "ok"')
    check(f"l'invite demande un nouveau tirage : les offres de l'host changent ({after} -> {ev(H, OFFERS)})",
          eventually(lambda: str(ev(H, OFFERS)) != after, timeout=20))
    check("et ce sont les memes chez l'invite", eventually(lambda: str(ev(A, OFFERS)) == str(ev(H, OFFERS)), timeout=30))
    check(f"l'host a paye l'influence ({ev(H, 'EClass._zone.influence.ToString()')})", ev(H, 'EClass._zone.influence.ToString()') == "4")


VQ = 'var q = EClass.game.quests.Get<QuestVernis>(); '
VREPAIR = ('System.AppDomain.CurrentDomain.GetAssemblies().First(a => a.GetName().Name == "ElinTogether").GetType("ElinTogether.Patches.QuestVernisRepair")'
           '.GetMethod("Repair", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic).Invoke(null, null); ')


def v1():
    """Quete de Vernis (2026-10-12) : un joueur seul au journal en retard ne la fait plus reculer ; un monde ou elle
    a recule est remis ou la mine dit qu'il en etait ; l'etage du boss sans boss la fait avancer."""
    from travel_suite import VERNIS, both_joined, client_settled, move, wait, zone_uid  # noqa: PLC0415
    phase = lambda port: str(ev(port, VQ + 'return q == null ? "aucune" : q.phase.ToString();'))  # noqa: E731
    ev(H, 'if (EClass.game.quests.Get<QuestVernis>() == null) EClass.game.quests.Start("vernis_gold", "loytel"); return "ok";')
    # (le pas de quete ouvre le dialogue de Loytel, comme dans le jeu : il n'existe pas dans le monde du banc)
    ev(H, 'if (EClass.game.cards.globalCharas.Find("loytel") == null) CharaGen.Create("loytel").SetGlobal(EClass.game.spatials.Find(7), 50, 50); return "ok";')
    shut = lambda: ev(H, 'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); return "ok";')  # noqa: E731
    if not check("la quete de Vernis est dans le journal des deux jeux", eventually(lambda: phase(A) != "aucune", timeout=20)):
        return
    for port in (H, A):
        ev(port, VQ + 'q.phase = 8; q.task = null; return "ok";')
    try:
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        time.sleep(3)
        ev(A, VQ + 'q.phase = 2; q.ChangePhase(3); return "ok";')
        time.sleep(5)
        check(f"l'invite seul, journal en retard a 2, fait 2 -> 3 : le monde reste a 8 (host {phase(H)})", phase(H) == "8")
        check("et son journal revient a 8", eventually(lambda: phase(A) == "8", timeout=20))
        ev(H, VQ + 'q.phase = 7; return "ok";')
        ev(A, VQ + 'q.ChangePhase(9); return "ok";')
        check("un pas en avant d'un joueur seul reste accepte, meme si l'host etait a une autre etape (7, invite 8 -> 9)",
              eventually(lambda: phase(H) == "9", timeout=20))
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)
    time.sleep(3)
    # le monde abime : quete a 3, mine ouverte jusqu'a l'etage du boss (cree comme le fait le depart de test du jeu)
    floor = int(ev(H, 'var z = EClass.game.spatials.map.Values.OfType<Zone_VernisMine>().FirstOrDefault(x => x.lv == -8); '
                      'if (z == null) { z = SpatialGen.Create("vernis_mine", EClass.game.spatials.Find("vernis"), true) as Zone_VernisMine; z.lv = -8; } '
                      + VQ + 'q.phase = 3; return z.uid;'))
    ev(H, VREPAIR + 'return "ok";')
    check(f"quete a 3 dans un monde dont l'etage du boss existe : remise a 8 a l'hebergement ({phase(H)})", phase(H) == "8")
    ev(H, VQ + 'q.phase = 9; ' + VREPAIR + 'return "ok";')
    check(f"jamais abaissee (9 reste 9 : {phase(H)})", phase(H) == "9")
    for port in (H, A):
        ev(port, VQ + 'q.phase = 8; return "ok";')
    try:
        move(H, floor)
        wait(lambda: zone_uid(H) == floor, "l'host a l'etage du boss", timeout=180)
        time.sleep(5)
        boss = str(ev(H, 'var b = EClass._map.charas.FirstOrDefault(c => c.id == "vernis_boss"); return b == null ? "aucun" : b.uid.ToString();'))
        check(f"le boss est la et la quete attend sa mort (boss {boss}, etape {phase(H)})", boss != "aucun" and phase(H) == "8")
        ev(H, 'var b = EClass._map.charas.First(c => c.id == "vernis_boss"); b.DamageHP(9999999, AttackSource.None, EClass.pc); return "ok";')
        time.sleep(2)
        shut()
        check("le boss meurt : etape 9, comme dans le jeu", eventually(lambda: phase(H) == "9", timeout=15))
        # le monde abime : le boss est mort mais la quete est revenue a 8
        ev(H, VQ + 'q.phase = 8; return "ok";')
        move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "l'host a la base", timeout=180)
        time.sleep(4)
        move(H, floor)
        wait(lambda: zone_uid(H) == floor, "l'host de retour a l'etage du boss", timeout=180)
        check("etage du boss sans boss, quete a 8 : elle avance a 9", eventually(lambda: phase(H) == "9", timeout=20))
        time.sleep(2)
        shut()
        check("chez l'invite aussi", eventually(lambda: phase(A) == "9", timeout=20))
    finally:
        move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "l'host a la base", timeout=180)
        both_joined(H, A, HOME)
        ev(H, 'var q = EClass.game.quests.Get<QuestVernis>(); if (q != null) EClass.game.quests.Remove(q); '
              'foreach (var z in EClass.game.spatials.map.Values.OfType<Zone_VernisMine>().Where(x => x.lv == -8).ToList()) z.Destroy(); return "ok";')


def v2():
    """Journal des quetes (2026-10-13) : un jeu en retard rattrape celui du monde, jamais l'inverse ; Nymelle remise
    ou son donjon dit que le monde en etait ; l'etage du boss de Lesimas sans boss fait avancer la quete.
    Ce que le banc ne joue pas : les etapes sont ecrites par eval (un journal « en retard » ne se fabrique pas
    autrement), les etages sont crees comme le fait le depart de test du jeu, pas descendus a pied."""
    from travel_suite import VERNIS, both_joined, client_settled, move, wait, zone_uid  # noqa: PLC0415
    phase = lambda port, kind="QuestVernis": str(ev(port, f'var q = EClass.game.quests.Get<{kind}>(); return q == null ? "aucune" : q.phase.ToString();'))  # noqa: E731
    put = lambda port, n: ev(port, VQ + f'q.phase = {n}; q.task = null; return "ok";')  # noqa: E731
    shut = lambda: ev(H, 'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); return "ok";')  # noqa: E731
    for who in ("loytel", "kettle"):
        ev(H, f'if (EClass.game.cards.globalCharas.Find("{who}") == null) CharaGen.Create("{who}").SetGlobal(EClass.game.spatials.Find(7), 50, 50); return "ok";')
    ev(H, 'if (EClass.game.quests.Get<QuestVernis>() == null) EClass.game.quests.Start("vernis_gold", "loytel"); return "ok";')
    if not check("la quete de Vernis est dans le journal des deux jeux", eventually(lambda: phase(A) != "aucune", timeout=20)):
        return
    try:
        put(H, 6)
        put(A, 2)
        check("journal de l'invite en retard (2, le monde a 6) : il rattrape tout seul", eventually(lambda: phase(A) == "6", timeout=45))
        put(A, 7)
        time.sleep(30)
        check(f"journal de l'invite en avance (7, le monde a 6) : il n'est pas ramene en arriere ({phase(A)})", phase(A) == "7")
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        put(H, 9)
        check("seul sur sa carte, il rattrape aussi (9)", eventually(lambda: phase(A) == "9", timeout=45))
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)
    time.sleep(3)
    ev(H, VQ + 'EClass.game.quests.Remove(q); EClass.game.quests.completedIDs.Add("vernis_gold"); return "ok";')
    check("quete finie dans le monde, encore ouverte chez l'invite : elle se ferme chez lui",
          eventually(lambda: ev(A, '(EClass.game.quests.Get<QuestVernis>() == null && EClass.game.quests.completedIDs.Contains("vernis_gold")).ToString()') == "True", timeout=45))
    for port in (H, A):
        ev(port, 'EClass.game.quests.completedIDs.Remove("vernis_gold"); EClass.game.quests.completedTypes.Remove("QuestVernis"); return "ok";')
    # Nymelle : quete au debut, donjon ouvert jusqu'au cristal
    ev(H, 'if (EClass.game.quests.Get<QuestExploration>() == null) EClass.game.quests.Start("exploration", EClass.game.cards.globalCharas.Find("ashland"), false); '
          'var q = EClass.game.quests.Get<QuestExploration>(); q.phase = 0; var top = EClass.game.spatials.Find("nymelle"); '
          'var z = SpatialGen.Create("nymelle", top, true) as Zone; z.lv = -3; return "ok";')
    ev(H, VREPAIR + 'return "ok";')
    check(f"Nymelle a 0 avec un etage sous le deuxieme : remise a 1 ({phase(H, 'QuestExploration')})", phase(H, "QuestExploration") == "1")
    ev(H, 'var z = SpatialGen.Create("nymelle_crystal", EClass.game.spatials.Find("nymelle"), true) as Zone; z.lv = -6; return "ok";')
    ev(H, VREPAIR + 'return "ok";')
    check(f"avec l'etage du cristal : remise a 3 ({phase(H, 'QuestExploration')})", phase(H, "QuestExploration") == "3")
    ev(H, 'var q = EClass.game.quests.Get<QuestExploration>(); q.phase = 5; ' + VREPAIR + 'return "ok";')
    check(f"jamais abaissee (5 reste 5 : {phase(H, 'QuestExploration')})", phase(H, "QuestExploration") == "5")
    check("l'invite suit (5)", eventually(lambda: phase(A, "QuestExploration") == "5", timeout=45))
    # Lesimas : quete a 5, etage du boss sans boss
    floor = int(ev(H, 'if (EClass.game.quests.Get<QuestIntoDarkness>() == null) EClass.game.quests.Start("into_darkness", EClass.game.cards.globalCharas.Find("kettle")); '
                      'EClass.game.quests.Get<QuestIntoDarkness>().phase = 5; '
                      'var z = SpatialGen.Create("cave_dead", EClass.game.spatials.Find("cave_dead"), true) as Zone; z.lv = -6; return z.uid;'))
    try:
        move(H, floor)
        wait(lambda: zone_uid(H) == floor, "l'host a l'etage du boss de Lesimas", timeout=180)
        check("Lesimas a 5, etage du boss sans boss : la quete avance a 6", eventually(lambda: phase(H, "QuestIntoDarkness") == "6", timeout=20))
        time.sleep(2)
        shut()
        check("chez l'invite aussi", eventually(lambda: phase(A, "QuestIntoDarkness") == "6", timeout=45))
    finally:
        move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "l'host a la base", timeout=180)
        both_joined(H, A, HOME)
        ev(A, 'foreach (var q in EClass.game.quests.list.Where(x => x is QuestVernis || x is QuestExploration || x is QuestIntoDarkness).ToList()) EClass.game.quests.Remove(q); return "ok";')
        ev(H, 'foreach (var q in EClass.game.quests.list.Where(x => x is QuestVernis || x is QuestExploration || x is QuestIntoDarkness).ToList()) EClass.game.quests.Remove(q); '
              'foreach (var z in EClass.game.spatials.map.Values.Where(x => (x is Zone_Nymelle || x is Zone_DungeonDead) && x.lv < -1).ToList()) z.Destroy(); return "ok";')


def v3():
    """Quetes d'histoire, suite de la relecture du 2026-10-13 : une quete finie dont un jeu n'a jamais entendu parler
    y est notee finie ; la fin de la quete de Nasu faite par l'invite (elle reprend le sac a dos de « le joueur ») ;
    les reves de Lesimas ne sont plus avances par deux jeux sur la meme carte.
    Ce que le banc ne joue pas : les quetes sont creees et terminees par eval, pas par leurs dialogues."""
    guest = state(A)["pc"]["uid"]
    done = lambda port, qid: ev(port, f'EClass.game.quests.completedIDs.Contains("{qid}").ToString()') == "True"  # noqa: E731
    phase = lambda port: str(ev(port, 'var q = EClass.game.quests.Get<QuestIntoDarkness>(); return q == null ? "aucune" : q.phase.ToString();'))  # noqa: E731
    shut = lambda: ev(H, 'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); return "ok";')  # noqa: E731
    ev(H, 'EClass.game.quests.completedIDs.Add("banc_finie"); EClass.game.quests.completedTypes.Add("BancFinie"); return "ok";')
    check("une quete finie dans le monde, inconnue de l'invite : notee finie chez lui",
          eventually(lambda: done(A, "banc_finie") and ev(A, 'EClass.game.quests.completedTypes.Contains("BancFinie").ToString()') == "True", timeout=45))
    for port in (H, A):
        ev(port, 'EClass.game.quests.completedIDs.Remove("banc_finie"); EClass.game.quests.completedTypes.Remove("BancFinie"); return "ok";')
    # Nasu : l'invite a le sac a dos, l'invite termine
    ev(H, 'foreach (var port in new[] { "nasu" }) { EClass.game.quests.completedIDs.Remove(port); } EClass.game.quests.completedTypes.Remove("QuestNasu"); '
          'var n = EClass.game.cards.globalCharas.Find("fairy_nanasu") ?? CharaGen.Create("fairy_nanasu").SetGlobal(EClass.game.spatials.Find(7), 50, 50); '
          'if (EClass.game.quests.Get<QuestNasu>() == null) EClass.game.quests.Start("nasu", n, false); '
          f'var g = EClass._map.charas.Find(x => x.uid == {guest}); g.AddThing(ThingGen.Create("backpack_holding")); return "ok";')
    has = lambda: str(ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {guest}); return (g.things.Find("backpack_holding") != null) + "|" + '  # noqa: E731
                            '(EClass._map.things.Where(t => t.pos.Equals(g.pos)).Concat(g.things.List(t => true, true)).Where(t => t.id == "697").Sum(t => t.Num));'))
    if not check("l'invite connait la quete de Nasu et a le sac a dos",
                 eventually(lambda: ev(A, '(EClass.game.quests.Get<QuestNasu>() != null && EClass.pc.things.Find("backpack_holding") != null).ToString()') == "True", timeout=20)):
        return
    before = has()
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ev(A, 'EClass.game.quests.Get<QuestNasu>().Complete(); return "ok";')
    check("l'invite termine la quete de Nasu : finie dans le monde", eventually(lambda: done(H, "nasu"), timeout=20))
    time.sleep(3)
    after = has()
    check(f"elle a repris le sac a dos de l'invite et il a ses 77 pieces (sac|pieces : {before} -> {after})",
          after.split("|")[0] == "False" and int(after.split("|")[1]) - int(before.split("|")[1]) == 77)
    from guest_suite import journal  # noqa: PLC0415
    check("la fin de la quete n'a pas plante chez l'host", not journal(t0, "completion threw on the host"))
    for port in (H, A):
        ev(port, 'EClass.game.quests.completedIDs.Remove("nasu"); EClass.game.quests.completedTypes.Remove("QuestNasu"); return "ok";')
    # reves de Lesimas : sur la carte de l'host, seul le jeu de l'host avance la quete
    ev(H, 'if (EClass.game.cards.globalCharas.Find("kettle") == null) CharaGen.Create("kettle").SetGlobal(EClass.game.spatials.Find(7), 50, 50); '
          'if (EClass.game.quests.Get<QuestIntoDarkness>() == null) EClass.game.quests.Start("into_darkness", EClass.game.cards.globalCharas.Find("kettle")); return "ok";')
    if not check("la quete de Lesimas est dans les deux journaux", eventually(lambda: phase(A) != "aucune", timeout=20)):
        return
    for port in (H, A):
        ev(port, 'EClass.game.quests.Get<QuestIntoDarkness>().phase = 1; return "ok";')
    ev(A, 'EClass.player.flags.OnEnterZone(); return "ok";')
    time.sleep(4)
    check(f"l'invite entre dans la base, sur la carte de l'host : son jeu n'avance pas la quete (host {phase(H)}, invite {phase(A)})",
          phase(H) == "1" and phase(A) == "1")
    ev(H, 'EClass.player.flags.OnEnterZone(); return "ok";')
    time.sleep(2)
    shut()
    check(f"l'host y entre : un pas, un seul, chez les deux (host {phase(H)})", phase(H) == "2" and eventually(lambda: phase(A) == "2", timeout=20))
    ev(H, 'var q = EClass.game.quests.Get<QuestIntoDarkness>(); if (q != null) EClass.game.quests.Remove(q); return "ok";')


def v4():
    """Suite du 2026-10-13 : une quete d'histoire proposee dans le monde pendant qu'un joueur est seul lui arrive ;
    l'invite lit un acte de propriete et dit oui : la terre est prise pour tout le monde (avant : refuse a l'invite).
    Ce que le banc ne joue pas : l'offre est ajoutee par QuestManager.Add (ce que fait le jeu a une date ou dans un
    dialogue) ; Vernis est rendue prenable en mettant sa quete a l'etape 4 par eval ; l'acte est lu par OnRead
    (ce que fait « lire ») et le oui est le vrai bouton de la boite du jeu. ETAPE A JOUER EN DERNIER : Vernis
    reste une base dans le monde du banc."""
    from base_suite import click_yes, dialog_open  # noqa: PLC0415
    from travel_suite import VERNIS, both_joined, client_settled, move, wait  # noqa: PLC0415
    guest = state(A)["pc"]["uid"]
    offered = lambda port: ev(port, '(EClass.game.quests.globalList.Exists(q => q.id == "into_darkness")).ToString()') == "True"  # noqa: E731
    ev(H, 'EClass.game.quests.globalList.RemoveAll(q => q.id == "into_darkness"); return "ok";')
    try:
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        time.sleep(3)
        ev(A, 'EClass.game.quests.globalList.RemoveAll(q => q.id == "into_darkness"); EClass.game.quests.list.RemoveAll(q => q.id == "into_darkness"); return "ok";')
        ev(H, 'EClass.game.quests.Add("into_darkness", "ashland"); return "ok";')
        check("l'host a une nouvelle quete d'histoire a proposer", offered(H))
        check("l'invite, seul sur sa carte, la recoit", eventually(lambda: offered(A), timeout=45))
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)
    ev(H, 'EClass.game.quests.globalList.RemoveAll(q => q.id == "into_darkness"); return "ok";')
    ev(A, 'EClass.game.quests.globalList.RemoveAll(q => q.id == "into_darkness"); return "ok";')
    # l'acte de propriete lu par l'invite, a Vernis (prenable a l'etape 4 de sa quete)
    ev(H, 'if (EClass.game.cards.globalCharas.Find("loytel") == null) CharaGen.Create("loytel").SetGlobal(EClass.game.spatials.Find(7), 50, 50); '
          'if (EClass.game.quests.Get<QuestVernis>() == null) EClass.game.quests.Start("vernis_gold", "loytel"); return "ok";')
    if not check("la quete de Vernis est dans les deux journaux",
                 eventually(lambda: ev(A, '(EClass.game.quests.Get<QuestVernis>() != null).ToString()') == "True", timeout=20)):
        return
    for port in (H, A):
        ev(port, VQ + 'q.phase = 4; q.task = null; return "ok";')
    host_goto(H, A, VERNIS)
    time.sleep(4)
    look = 'return EClass._zone.id + "|" + EClass._zone.IsPCFaction + "|" + (EClass._zone.branch != null) + "|" + EClass._map.things.Count(t => t.trait is TraitCoreZone);'
    deeds = lambda port: int(ev(port, f'var g = EClass._map.charas.Find(x => x.uid == {guest}); return g.things.List(t => t.trait is TraitDeed, true).Sum(t => t.Num).ToString();'))  # noqa: E731
    if not check(f"les deux sont a Vernis, qui n'est a personne et peut etre prise (host {ev(H, look)}, invite {ev(A, look)}, prenable {ev(A, 'EClass._zone.isClaimable.ToString()')})",
                 str(ev(H, look)).startswith("vernis|False|False") and ev(A, 'EClass._zone.isClaimable.ToString()') == "True" and ev(H, 'EClass._zone.isClaimable.ToString()') == "True"):
        return
    ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {guest}); g.AddThing(ThingGen.Create("deed")); return "ok";')
    check("l'invite a un acte de propriete, dans les deux jeux", eventually(lambda: deeds(A) == 1 and deeds(H) == 1, timeout=15))
    ev(A, 'var t = EClass.pc.things.List(x => x.trait is TraitDeed, true).First(); t.trait.OnRead(EClass.pc); return "ok";')
    time.sleep(2)
    if not check("la boite « reclamer cette terre ? » s'ouvre chez l'invite (avant : refus)", dialog_open(A)):
        return
    check(f"il clique oui ({click_yes(A)})", True)
    check("chez l'host : Vernis est une base, avec sa branche et sa pierre de foyer",
          eventually(lambda: str(ev(H, look)) == "vernis|True|True|1", timeout=30))
    check("chez l'invite aussi", eventually(lambda: state(A).get("connected") and str(ev(A, look)) == "vernis|True|True|1", timeout=120))
    time.sleep(3)
    check(f"l'acte est consomme, une fois (host {deeds(H)}, invite {deeds(A)})", deeds(H) == 0 and deeds(A) == 0)
    ev(H, 'var q = EClass.game.quests.Get<QuestVernis>(); if (q != null) EClass.game.quests.Remove(q); return "ok";')
    host_goto(H, A, HOME)


def v5():
    """Suite du 2026-10-13 : les factures d'impot faites et payees du monde sont connues de l'invite (la quete
    d'impot les demande a « le joueur ») ; la dette de Loytel prise par l'invite : Loytel le rejoint LUI et la
    cassette va dans SON sac. Le banc pose les compteurs par eval et accepte la dette par QuestManager.Start sur
    l'offre du monde (ce que fait le oui du dialogue de Loytel), sans jouer le dialogue."""
    guest = state(A)["pc"]["uid"]
    tax = lambda port: str(ev(port, 'EClass.player.stats.taxBills + "|" + EClass.player.stats.taxBillsPaid'))  # noqa: E731
    before = tax(A)
    ev(H, 'EClass.player.stats.taxBills += 3; EClass.player.stats.taxBillsPaid += 500; return "ok";')
    check(f"factures faites et payees du monde : l'invite les connait ({before} -> {tax(H)})", eventually(lambda: tax(A) == tax(H), timeout=45))
    ev(H, 'var l = EClass.game.cards.globalCharas.Find("loytel") ?? CharaGen.Create("loytel").SetGlobal(EClass.game.spatials.Find(7), 50, 50); '
          'if (!EClass._map.charas.Contains(l)) EClass._zone.AddCard(l, EClass.pc.pos.GetNearestPoint(false, false)); '
          'foreach (var q in EClass.game.quests.list.Where(x => x is QuestDebt).ToList()) EClass.game.quests.Remove(q); '
          'EClass.game.quests.globalList.RemoveAll(x => x is QuestDebt); EClass.game.quests.Add("debt", "loytel"); return "ok";')
    if not check("la dette est proposee, l'invite le sait",
                 eventually(lambda: ev(A, '(EClass.game.quests.globalList.Exists(q => q is QuestDebt)).ToString()') == "True", timeout=45)):
        return
    look = (f'var g = EClass.game.cards.globalCharas.Find({guest}); var l = EClass.game.cards.globalCharas.Find("loytel"); '
            'return (EClass.game.quests.Get<QuestDebt>() != null) + "|" + EClass.pc.party.members.Contains(l) + "|" + l.GetInt("emp_owner") + "|" + '
            'g.things.List(t => t.id == "856", true).Count + "|" + EClass.pc.things.List(t => t.id == "856", true).Count;')
    before = str(ev(H, look))
    ev(A, 'EClass.game.quests.Start(EClass.game.quests.globalList.First(q => q is QuestDebt)); return "ok";')
    want = lambda: str(ev(H, look))  # noqa: E731
    ok_ = eventually(lambda: want().split("|")[:2] == ["True", "True"], timeout=20)
    now = want()
    # (PAS FAIT : Loytel entre dans l'equipe comme compagnon de l'host, « a qui » reste 0 ; il devrait suivre l'invite)
    check(f"l'invite prend la dette : elle commence dans le monde, Loytel entre dans l'equipe (dette|dans l'equipe|a qui|cassettes invite|cassettes host : {before} -> {now})", ok_)
    check(f"la cassette est dans son sac, pas dans celui de l'host ({before} -> {now})",
          int(now.split("|")[3]) == int(before.split("|")[3]) + 1 and now.split("|")[4] == before.split("|")[4])
    ev(H, 'var l = EClass.game.cards.globalCharas.Find("loytel"); if (EClass.pc.party.members.Contains(l)) EClass.pc.party.RemoveMember(l); '
          'foreach (var q in EClass.game.quests.list.Where(x => x is QuestDebt).ToList()) EClass.game.quests.Remove(q); return "ok";')


def main():
    start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for name, port in (("host", 27551), ("invite", 27552)):
        r = str(ev(port, TWICE))
        if r == "seul":
            print(f"    {name} : personne d'autre dans l'equipe, rien a prouver ici")
            continue
        check(f"{name} : pas de deuxieme ajout, lien remis ({r})", r == "0/0/True")
    check("au moins un jeu avait un autre membre dans l'equipe", RESULTS)
    steps = (o1, b1, c1, h1, f1, l1, m1, s1, s2, s3, g1, e1, r1, p1, x1, a1, d1, w1, i1, k1, j1, u1, z1, v1, v2, v3, v5, t1, q1, f2, v4)  # v1 avant t1 : t1 maudit l'invite de test, qui en meurt et ne voyage plus
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
