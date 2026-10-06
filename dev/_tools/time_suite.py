"""Une seule date pour le monde. Test court (host + 1 client a la Prairie), finit a la Prairie.

    python _tools/mp_test.py
    python _tools/time_suite.py       # ~10 minutes (duree pas mesuree depuis W7, W8, W8b, W9)

Premiere marche du serveur "depot de sauvegarde" (PLAN_serveur_depot.md) : la date n'appartient plus a l'host.
Avant : seul l'host faisait avancer la date ; un invite seul sur sa carte avait la sienne, puis reprenait celle de
l'host en rentrant. Maintenant il y a une seule date pour le monde.

Conseil 10 (PLAN_conseil10_verdict.md, point iv ; case « TimeJumpsTogether », cochee) : cette date avance minute
par minute pendant qu'on joue (W1, W2), et ne SAUTE que quand tous sautent ensemble. Un pas sur la carte du monde
vaut trois heures seulement si c'est un pas de l'host et que tous les joueurs sont sur la carte du monde (W9) ;
sinon le voyageur paie son pas avec son corps et la date ne bouge pas (W8, W8b). Le chronometre d'une quete
(recolte, concert, mariage) est au joueur qui la fait (W7). TOGETHER_OFF=1 : la case decochee, pour voir W8, W8b
et W9 echouer comme avant.

W1  l'invite part seul a Vernis et y passe du temps (il marche) : la date de l'host avance avec la sienne
W2  l'host passe du temps chez lui : la date de l'invite, toujours a Vernis, avance avec la sienne
W3  un saut de date fait par l'autre joueur (cinq heures, `GameDate.AdvanceMin` appele chez l'invite) : l'host fait
    le meme saut de date, mais son personnage ne vit pas ces heures (pas de tours joues, pas plus faim).
    Depuis le conseil 10 ni la nuit d'un seul joueur ni son voyage ne font plus ce saut : W3 et W6 gardent la
    protection pour les sauts qui restent (la nuit commune, les cases decochees), W8 joue le vrai voyage
W6  (joue apres W3, l'invite est encore seul a Vernis) le retour de la partie du 6 octobre 2026 : l'autre joueur
    fait sauter la date de 24 heures (8 fois `AdvanceMin(180)`, ce que faisaient 8 pas de carte du monde avant le
    conseil 10) ; chez l'invite la date a avance, mais il n'a pas plus faim, sa viande fraiche n'a pas vieilli, et
    meme affame il n'en meurt pas. Puis la meme chose dans l'autre sens. Temoin : chacun fait LUI-MEME passer une
    heure en marchant : ses tours sont joues et sa viande vieillit, comme en solo
W8  (l'invite est encore seul a Vernis) l'host sort sur la carte du monde et y fait cinq vrais pas : la date de
    l'invite avance de moins de quinze minutes (avant : quinze heures), l'host a paye ses tours (300 au moins),
    l'invite n'a rien vecu, l'host lit une fois « ton voyage ne fait pas avancer la date »
W4  l'invite rentre : sa date ne saute pas, les deux jeux ont la meme
W7  le chronometre d'une recolte : l'invite est seul sur la carte de sa quete, l'host fait passer 180 minutes : le
    chronometre de l'invite n'a pas bouge (avant : +180, la recolte finie d'un coup). Puis roles echanges : l'host
    sur la carte de sa recolte, l'invite reste en ville fait passer 180 minutes
W7e (ancien W7 ; l'invite est sur la carte de l'host) l'host fait passer trois heures comme le voyage express, sans
    message : l'invite n'a pas plus faim, sa viande n'a pas vieilli, sa quete aleatoire garde son temps restant
W8b l'inverse de W8 : l'invite seul sur la carte du monde fait cinq vrais pas, l'host est reste en ville
W9  les deux sur la carte du monde, sur la carte de l'host : trois pas de l'invite lui coutent ses tours (vus aussi
    par l'host), ne coutent rien a l'host et ne bougent pas la date ; deux pas de l'host font avancer la date des
    deux (trois heures par pas) et ne coutent aucun tour a l'invite
W5  case decochee : l'ancien comportement, l'host n'avance plus avec l'invite

Tolerance de W3 et W6 : 40 tours du personnage au plus pendant le temps des autres (avant la correction : 960
pour 24 heures). Le joueur ne joue pas, mais son jeu peut finir une action en cours ou jouer quelques tours le
temps des commandes du banc ; 40 tours, c'est moins d'un tirage de faim (un tirage tous les 50 tours, +1 une fois
sur trois), d'ou « faim : +1 au plus ». Le temoin compte les tours et la viande, pas la faim : en une heure de
marche la faim ne monte pas a coup sur (deux tirages a une chance sur trois).

Ce que le banc ne joue pas comme un joueur :
- W3 et W6 : le saut de l'autre joueur est `GameDate.AdvanceMin` appele dans son jeu (300 minutes, puis 8 fois
  180), sans geste de joueur : une vraie nuit commune (LayerSleep, bonds de 10 minutes) n'est pas jouee ;
- W8, W8b, W9 : un pas est `pc.TryMove(case voisine)`, l'appel par lequel finit une touche de direction
  (GoalManualMove), pas la touche ; la case est choisie par le banc (terre ferme, pas la mer) ; les rencontres au
  hasard sont ecartees (`player.safeTravel = 99`) ; on sort sur la carte du monde par `Player.ExitBorder` sans
  marcher jusqu'au bord, on rentre par `EnterLocalZone` sans marcher jusqu'a la case ; ni compagnon (ses tours
  payes par le pas de son joueur, pas par celui d'un autre), ni voyage express, ni joueur sur sa propre copie de la
  carte du monde pendant que l'host y marche, ni troisieme joueur reste en ville : pas joues ;
- W7 : les 180 minutes de l'autre joueur sont `GameDate.AdvanceMin(180)` dans son jeu (un pas de carte du monde ne
  les fait plus passer, une nuit commune est impossible avec un joueur en quete) ; la recolte est proposee par un
  habitant que l'host fait parler, prise et rejointe par les deux appels du dialogue (together_suite), la boite
  « venir aussi ? » est refusee d'un clic ; concert et mariage ne sont pas joues (meme chronometre) ;
- la viande est creee dans le sac par une commande, sa fraicheur posee a zero ; « affame » est pose par
  `hunger.Set(max)`, puis la faim d'avant est remise ;
- l'invite part a Vernis par `pc.MoveZone`, pas a pied ; le temoin marche pour de bon (allers de 14 cases, retour
  par teleportation) ;
- a deux fenetres : ni le visiteur d'un autre invite, ni l'invite sur la carte de l'host pendant qu'un troisieme
  voyage (trio_time_suite.py, trois fenetres) ; ni les sacs des compagnons, ni les quetes qui n'expirent plus par
  le saut d'un autre.
"""
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bot import choices, click  # noqa: E402
from combat_suite import set_option  # noqa: E402
import move_suite  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from quest_suite import accept, in_log, offer, offered  # noqa: E402
from together_suite import LEAVE, guest_alone_inside, guest_departs, guest_takes, host_enters  # noqa: E402
from together_suite import back_home as quest_back_home  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually,  # noqa: E402
                          move, scan_logs, wait, zone_uid)

H, A = 27551, 27552
DATE = 'EClass.world.date.GetRaw().ToString()'
def date(port):
    return int(ev(port, DATE))


def spend(port, minutes, timeout=150):
    """Le joueur marche pour de bon (des allers de 14 cases) jusqu'a ce que sa date ait avance d'autant.
    Renvoie les minutes passees."""
    start, end = date(port), time.time() + timeout
    while date(port) - start < minutes and time.time() < end:
        move_suite.walk(port)
        move_suite.back(port)
    return date(port) - start


def gap():
    return date(A) - date(H)


TURNS = 40
FOOD = ('var r = EClass.sources.things.rows.FirstOrDefault(x => x.category == "meat" || x._origin == "meat"); '
        'return r == null ? "meat" : r.id;')


def owner(uid):
    """Le personnage dont on regarde le sac (expression C#) : celui de ce jeu, ou un autre joueur de sa carte."""
    return "EClass.pc" if uid is None else f"EClass._map.charas.Find(x => x.uid == {uid})"


def body(port):
    """(tours joues, faim, points de vie, mort) du personnage de ce jeu."""
    turn, hunger, hp, dead = ev(port, 'EClass.pc.turn + "," + EClass.pc.hunger.value + "," + EClass.pc.hp + "," + EClass.pc.isDead').split(",")
    return int(turn), int(hunger), int(hp), dead == "True"


def fresh_meat(sim, uid=None):
    """Une viande fraiche dans le sac d'un joueur, creee par le jeu qui simule sa carte ; renvoie son numero,
    ou None si elle ne peut pas vieillir."""
    made = ev(sim, f'var t = ThingGen.Create("{ev(sim, FOOD)}"); var r = {owner(uid)}.AddThing(t, false); r.decay = 0; '
                   'return r.uid + "," + (r.trait.Decay != 0);')
    return int(made.split(",")[0]) if made.endswith("True") else None


def age(port, meat, uid=None):
    return int(ev(port, f'var t = {owner(uid)}.things.Find(x => x.uid == {meat}); return t == null ? "-1" : t.decay.ToString();'))


def travel_day(mover):
    """Ce joueur fait sauter la date de 24 heures (8 fois trois heures : ce que faisaient 8 pas sur la carte du
    monde avant le conseil 10 ; aujourd'hui seulement case decochee, ou une nuit commune)."""
    for _ in range(8):
        ev(mover, 'EClass.world.date.AdvanceMin(180); "ok"', timeout=300)
        time.sleep(1)


def untouched(port, who, meat, before, seen=()):
    """Ce joueur n'a rien vecu du temps qu'un autre vient de faire passer. `before` : body(port) d'avant ;
    `seen` : (port, uid) du jeu qui simule sa carte, quand ce n'est pas le sien."""
    t0, f0, _, _ = before
    turn, hunger, hp, dead = body(port)
    log(f"{who} : tours {t0} -> {turn}, faim {f0} -> {hunger}, viande {age(port, meat)}, vie {hp}")
    check(f"{who} n'a pas joue ces heures ({turn - t0} tours, {TURNS} au plus)", turn - t0 <= TURNS)
    check(f"{who} n'a pas plus faim (faim {f0} -> {hunger}, +1 au plus)", hunger - f0 <= 1)
    check(f"{who} : sa viande n'a pas vieilli ({age(port, meat)})", age(port, meat) == 0)
    if seen:
        check(f"{who} : ni dans le jeu qui tient sa carte ({age(seen[0], meat, seen[1])})", age(seen[0], meat, seen[1]) == 0)
    check(f"{who} n'est pas mort", not dead)


def others_day(mover, still, who, other):
    """`mover` voyage 24 heures, `still` ne joue pas : sa date suit, son personnage et son sac ne vivent rien."""
    meat = fresh_meat(still)
    if not check(f"{who} a une viande fraiche dans son sac, qui peut vieillir", meat is not None and age(still, meat) == 0):
        return None
    d0, before = date(still), body(still)
    travel_day(mover)
    followed = eventually(lambda: date(still) - d0 >= 1438 and abs(gap()) <= 2, timeout=30)
    check(f"{other} fait sauter la date de 24 heures : celle de {who} a suivi (+{date(still) - d0} min, ecart {gap()})", followed)
    untouched(still, who, meat, before)

    # affame : avant la correction, 960 tours a cette phase (un coup une fois sur cinq) tuaient le personnage
    hunger, hp0 = before[1], body(still)[2]
    ev(still, 'EClass.pc.hunger.Set(EClass.pc.hunger.max); "ok"')
    try:
        d0 = date(still)
        travel_day(mover)
        eventually(lambda: date(still) - d0 >= 1438, timeout=30)
        _, _, hp, dead = body(still)
        check(f"{who} affame, {other} fait encore sauter 24 heures : il n'en meurt pas (vie {hp0} -> {hp}, un quart perdu au plus)",
              not dead and hp >= hp0 - max(2, hp0 // 4))
    finally:
        ev(still, f'EClass.pc.hunger.Set({hunger}); "ok"')
    return meat


def own_hour(port, who, meat):
    """Temoin : ce joueur fait LUI-MEME passer une heure pleine, en marchant ; ce temps-la lui coute, comme en solo."""
    turn = body(port)[0]
    spent = spend(port, 62, timeout=400)
    log(f"{who} a marche {spent} min : tours +{body(port)[0] - turn}, viande {age(port, meat)}")
    check(f"{who} fait lui-meme passer une heure en marchant ({spent} min) : ses tours sont joues (+{body(port)[0] - turn})",
          body(port)[0] - turn > TURNS)
    check(f"{who} : sa viande a vieilli ({age(port, meat)})", eventually(lambda: age(port, meat) > 0, timeout=10))


REGION = 'EClass.world.region.uid.ToString()'
EXIT = 'EClass.player.ExitBorder(); "ok"'
ENTER = ('var z = EClass.game.spatials.Find({uid}); var em = EClass.scene.elomap; '
         'EClass.player.EnterLocalZone(new Point(z.x - em.minX, z.y - em.minY)); "ok"')
# une case voisine de terre ferme, puis l'appel par lequel finit une touche de direction
STEP = ('var pc = EClass.pc; EClass.player.safeTravel = 99; '
        'foreach (var d in new[] { new[] { 1, 0 }, new[] { -1, 0 }, new[] { 0, 1 }, new[] { 0, -1 } }) { '
        'var p = new Point(pc.pos.x + d[0], pc.pos.z + d[1]); '
        'if (!p.IsValid || !p.IsInBounds || p.cell.CanSuffocate() || !pc.CanMoveTo(p, false)) continue; '
        'if (pc.TryMove(p) == Card.MoveResult.Success) return "1"; } return "0";')
ELAPSED = 'var e = EClass._zone.events.GetEvent<ZoneEventQuest>(); return e == null ? "-1" : e.minElapsed.ToString();'


def steps(port, n):
    """Ce joueur fait n vrais pas sur la carte du monde ; renvoie le nombre de pas faits."""
    done = 0
    for _ in range(n):
        done += int(ev(port, STEP, timeout=300))
        time.sleep(1)
    return done


def told(port):
    """Combien de fois ce joueur a lu « ton voyage ne fait pas avancer la date »."""
    text = ev(port, '"emp_ui_travel_no_date".lang()').lower()
    return int(ev(port, f'EClass.game.log.dict.Values.Count(l => l.text != null && l.text.ToLower().Contains("{text}")).ToString()'))


def lone_steps(mover, still, who, other):
    """W8, W8b : `mover` est seul sur la carte du monde et y fait cinq vrais pas, `still` est ailleurs."""
    d_still, d_mover, turn, before, said = date(still), date(mover), body(mover)[0], body(still), told(mover)
    done = steps(mover, 5)
    time.sleep(3)
    paid = body(mover)[0] - turn
    log(f"{other} : {done} pas, +{paid} tours, date +{date(mover) - d_mover} min ; {who} : date +{date(still) - d_still} min")
    check(f"{other} fait cinq pas sur la carte du monde ({done})", done == 5)
    check(f"la date de {who} ne saute pas (+{date(still) - d_still} min, moins de 15 ; avant : quinze heures)", date(still) - d_still < 15)
    check(f"celle de {other} non plus (+{date(mover) - d_mover} min), les deux jeux ont la meme (ecart {gap()})",
          date(mover) - d_mover < 15 and abs(gap()) <= 2)
    check(f"{other} a paye ses pas avec son corps (+{paid} tours, 300 au moins)", paid >= 300)
    check(f"{who} n'a rien vecu de ce voyage ({body(still)[0] - before[0]} tours, {TURNS} au plus)", body(still)[0] - before[0] <= TURNS)
    check(f"{other} lit une fois que son voyage ne fait pas avancer la date ({told(mover) - said})", told(mover) - said == 1)


def side_by_side():
    """W9 : les deux sur la carte du monde, celle de l'host. Chacun paie ses pas, seuls ceux de l'host font la date."""
    me = state(A)["pc"]["uid"]
    seen = lambda: int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); return c == null ? "-1" : c.turn.ToString();'))  # noqa: E731
    d0, host, guest, copy = date(H), body(H)[0], body(A)[0], seen()
    done = steps(A, 3)
    time.sleep(3)
    paid = body(A)[0] - guest
    check(f"l'invite fait trois pas a cote de l'host ({done}) : ils lui coutent ses tours (+{paid}, 180 au moins ; avant : aucun)",
          done == 3 and paid >= 180)
    check(f"l'host, qui tient la carte, voit ces tours sur le personnage de l'invite (+{seen() - copy})",
          eventually(lambda: seen() - copy >= 180, timeout=15))
    check(f"l'host ne paie pas les pas de l'invite ({body(H)[0] - host} tours, {TURNS} au plus)", body(H)[0] - host <= TURNS)
    check(f"les pas de l'invite ne font pas avancer la date (+{date(H) - d0} min, ecart {gap()})", date(H) - d0 < 15 and abs(gap()) <= 2)

    d0, host, guest = date(A), body(H)[0], body(A)[0]
    done = steps(H, 2)
    jumped = eventually(lambda: date(A) - d0 >= 200 and abs(gap()) <= 2, timeout=20)
    check(f"l'host fait deux pas ({done}) : la date des deux avance, trois heures par pas (+{date(A) - d0} min chez l'invite, ecart {gap()})",
          done == 2 and jumped)
    check(f"l'host paie ses pas (+{body(H)[0] - host} tours, 120 au moins)", body(H)[0] - host >= 120)
    check(f"l'invite ne paie pas ceux de l'host ({body(A)[0] - guest} tours, {TURNS} au plus)", body(A)[0] - guest <= TURNS)


def refuse(port):
    """La boite « venir aussi ? » ouverte chez ce joueur : il clique Non."""
    if eventually(lambda: len(choices(port)) == 2, timeout=20):
        click(port, choices(port)[1])


def held(player, other, who, whom):
    """`player` est seul sur la carte de sa recolte, `other` fait passer 180 minutes ailleurs."""
    elapsed = lambda: int(ev(player, ELAPSED))  # noqa: E731
    m0, d0 = elapsed(), date(player)
    if not check(f"{who} est sur la carte de sa recolte, chronometre a {m0} min", m0 >= 0):
        return
    ev(other, 'EClass.world.date.AdvanceMin(180); "ok"', timeout=300)
    check(f"{whom} fait passer 180 minutes : la date de {who} a suivi (+{date(player) - d0} min)",
          eventually(lambda: date(player) - d0 >= 178, timeout=30))
    time.sleep(2)
    check(f"le chronometre de {who} n'a pas bouge ({m0} -> {elapsed()} min ; avant la correction : +180, la recolte finie)",
          0 <= elapsed() - m0 <= 10)


def leave_quest(port):
    """Ce joueur sort de la carte de sa quete (si elle n'est pas deja finie), puis les deux se retrouvent en ville."""
    dismiss_dialogs(port)
    if ev(port, "EClass._zone.IsInstance.ToString()") == "True":
        ev(port, LEAVE)
    quest_back_home()


def timer():
    """W7 : le chronometre d'une recolte est au joueur qui la fait, dans les deux sens (voir en tete ce que le banc
    ne joue pas comme un joueur)."""
    uid, giver = guest_takes("QuestHarvest")
    guest_departs(uid, giver)
    refuse(H)
    guest_alone_inside()
    held(A, H, "l'invite", "l'host")
    leave_quest(A)

    host_enters("QuestHarvest")
    refuse(A)
    if check("l'invite reste en ville et la garde", eventually(client_settled(A, HOME, True), timeout=30)):
        held(H, A, "l'host", "l'invite")
    leave_quest(H)


def express():
    """W7e : l'invite est sur la carte de l'host, qui fait passer trois heures comme le voyage express
    (`GameDate.AdvanceHour` appele directement, LayerTravel.cs:161 : aucun message n'annonce ces heures, la date
    arrive avec la minute suivante). L'invite n'a pas plus faim, sa viande n'a pas vieilli, sa quete aleatoire
    garde son temps restant.
    Ce que le banc ne joue pas comme un joueur : pas de vrai voyage express (trois `AdvanceHour` par commande) ;
    la quete est proposee par un habitant cree au besoin et prise par `quests.Start`, sans dialogue ; si elle
    n'a pas de delai le banc lui en pose un de deux jours ; elle reste dans le journal de l'invite apres le test."""
    me = state(A)["pc"]["uid"]
    # la minute que l'host marche ensuite est du temps commun de la carte : elle ne doit pas passer une heure pleine
    if int(ev(H, 'EClass.world.date.min.ToString()')) >= 50:
        spend(H, 12)
    meat = fresh_meat(H, me)
    quest, _ = offer(H)
    # la quete que l'host vient de faire proposer n'est pas encore chez l'invite : la prendre tout de suite levait
    # une NullReferenceException dans la commande du banc
    if not check("l'invite voit la quete que l'habitant propose", eventually(lambda: offered(A, quest), timeout=20)):
        return
    accept(A, quest)
    left = lambda: int(ev(A, f'var q = EClass.game.quests.list.Find(x => x.uid == {quest}); '  # noqa: E731
                             'return q == null ? "-99999" : (q.deadline - EClass.world.date.GetRaw()).ToString();'))
    if not check("l'invite, sur la carte de l'host, a une viande fraiche et une quete aleatoire",
                 meat is not None and eventually(lambda: in_log(A, quest) and age(A, meat) == 0, timeout=15)):
        return
    ev(A, f'var q = EClass.game.quests.list.Find(x => x.uid == {quest}); if (q != null && q.deadline <= 0) q.deadline = EClass.world.date.GetRaw() + 2880; "ok"')
    d0, before, l0 = date(A), body(A), left()
    ev(H, 'for (var i = 0; i < 3; i++) EClass.world.date.AdvanceHour(); "ok"', timeout=300)
    spend(H, 2)
    check(f"l'host fait passer trois heures sans les annoncer : la date de l'invite a suivi (+{date(A) - d0} min)",
          eventually(lambda: date(A) - d0 >= 178 and abs(gap()) <= 2, timeout=20))
    time.sleep(2)
    untouched(A, "l'invite", meat, before, seen=(H, me))
    check(f"sa quete garde son temps restant ({l0} -> {left()} min ; avant la correction : 180 de moins)", abs(left() - l0) <= 10)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    has_option = True
    try:
        for port in (H, A):
            dismiss_dialogs(port)
        try:
            # TIME_OFF=1 : W1 a W4 avec la case decochee, pour voir l'ancien comportement echouer
            set_option("SharedWorldTime", not os.environ.get("TIME_OFF"))
        except Exception as ex:  # noqa: BLE001
            has_option = False
            log(f"case SharedWorldTime absente de ce build ({type(ex).__name__})")
        try:
            # TOGETHER_OFF=1 : W8, W8b et W9 avec la case decochee, pour voir l'ancien comportement echouer
            set_option("TimeJumpsTogether", not os.environ.get("TOGETHER_OFF"))
        except Exception as ex:  # noqa: BLE001
            log(f"case TimeJumpsTogether absente de ce build ({type(ex).__name__})")
        time.sleep(2)

        log("--- W1")
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
        time.sleep(3)
        dismiss_dialogs(A)
        log(f"au depart : host {date(H)}, invite {date(A)} (ecart {gap()} min)")
        check(f"au depart les deux jeux ont la meme date (ecart {gap()} min)", abs(gap()) <= 2)
        h0 = date(H)
        spent = spend(A, 20)
        log(f"l'invite a passe {spent} min a Vernis ; host {date(H)} (+{date(H) - h0}), invite {date(A)}")
        check(f"l'invite passe du temps seul a Vernis ({spent} min)", spent >= 20)
        check(f"la date de l'host avance avec la sienne (host +{date(H) - h0} min)",
              eventually(lambda: abs(gap()) <= 2, timeout=10) and date(H) - h0 >= 18)

        log("--- W2")
        a0 = date(A)
        spent = spend(H, 20)
        log(f"l'host a passe {spent} min chez lui ; host {date(H)}, invite {date(A)} (+{date(A) - a0})")
        check(f"l'host passe du temps chez lui ({spent} min)", spent >= 20)
        check(f"la date de l'invite, a Vernis, avance avec la sienne (invite +{date(A) - a0} min)",
              eventually(lambda: abs(gap()) <= 2, timeout=10) and date(A) - a0 >= 18)

        log("--- W3")
        h0 = date(H)
        turn, hunger, _, _ = body(H)
        hour = ev(H, 'EClass.world.date.hour.ToString()')
        ev(A, 'EClass.world.date.AdvanceMin(300); "ok"')
        jumped = eventually(lambda: date(H) - h0 >= 295, timeout=20)
        log(f"l'invite passe 5 heures : host +{date(H) - h0} min, heure {hour} -> {ev(H, 'EClass.world.date.hour.ToString()')}, "
            f"faim de l'host {hunger} -> {body(H)[1]}, tours {turn} -> {body(H)[0]}")
        check(f"l'invite passe cinq heures d'un coup : l'host fait le meme saut (+{date(H) - h0} min)", jumped and abs(gap()) <= 2)
        # avant : « son personnage a plus faim » (200 tours joues d'un coup) : le defaut rapporte le 6 octobre 2026
        check(f"le personnage de l'host n'a pas vecu ces heures ({body(H)[0] - turn} tours, {TURNS} au plus ; faim {hunger} -> {body(H)[1]})",
              body(H)[0] - turn <= TURNS and body(H)[1] - hunger <= 1)

        log("--- W6")
        meat = others_day(H, A, "l'invite", "l'host")
        if meat is not None:
            own_hour(A, "l'invite", meat)
        meat = others_day(A, H, "l'host", "l'invite")
        if meat is not None:
            own_hour(H, "l'host", meat)

        log("--- W8")
        region = int(ev(H, REGION))
        ev(H, EXIT)
        wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=180)
        time.sleep(3)
        lone_steps(H, A, "l'invite", "l'host")
        ev(H, ENTER.format(uid=HOME))
        wait(lambda: zone_uid(H) == HOME, "host de retour a la Prairie", timeout=240)
        time.sleep(3)

        log("--- W4")
        before = date(A)
        move(A, HOME)
        both_joined(H, A, HOME)
        time.sleep(4)
        dismiss_dialogs(A)
        log(f"retour : invite {before} -> {date(A)}, host {date(H)}")
        check(f"l'invite rentre : sa date ne saute pas ({date(A) - before:+d} min)", -2 <= date(A) - before <= 10)
        check(f"les deux jeux ont la meme date (ecart {gap()} min)", eventually(lambda: abs(gap()) <= 2, timeout=10))

        log("--- W7")
        timer()

        log("--- W7e")
        express()

        log("--- W8b")
        ev(A, EXIT)
        wait(client_settled(A, region, True), "invite seul sur la carte du monde", timeout=120)
        time.sleep(3)
        lone_steps(A, H, "l'host", "l'invite")
        ev(A, ENTER.format(uid=HOME))
        both_joined(H, A, HOME)

        log("--- W9")
        ev(H, EXIT)
        wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=180)
        time.sleep(4)
        # l'invite, reste a la Prairie, sort par le meme bord : il arrive sur la carte du monde de l'host
        ev(A, EXIT)
        both_joined(H, A, region)
        side_by_side()
        ev(H, ENTER.format(uid=HOME))
        wait(lambda: zone_uid(H) == HOME, "host de retour a la Prairie", timeout=240)
        time.sleep(4)
        if not eventually(client_settled(A, HOME, False), timeout=20):
            ev(A, ENTER.format(uid=HOME))
        both_joined(H, A, HOME)
        time.sleep(3)
        dismiss_dialogs(A)

        log("--- W5")
        if has_option:
            set_option("SharedWorldTime", False)
            time.sleep(3)
            try:
                move(A, VERNIS)
                wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
                time.sleep(3)
                dismiss_dialogs(A)
                h0 = date(H)
                spent = spend(A, 20)
                time.sleep(3)
                log(f"case decochee : l'invite a passe {spent} min, host +{date(H) - h0}")
                check(f"case decochee : l'host n'avance plus avec l'invite (host +{date(H) - h0} min pour {spent})",
                      spent >= 20 and date(H) - h0 <= 2)
                move(A, HOME)
                both_joined(H, A, HOME)
                time.sleep(4)
                dismiss_dialogs(A)
            finally:
                set_option("SharedWorldTime", True)
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-time-{name}', port)}")
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
