"""Une seule date pour le monde. Test court (host + 1 client a la Prairie), finit a la Prairie.

    python _tools/mp_test.py
    python _tools/time_suite.py       # ~4 minutes

Premiere marche du serveur "depot de sauvegarde" (PLAN_serveur_depot.md) : la date n'appartient plus a l'host.
Avant : seul l'host faisait avancer la date ; un invite seul sur sa carte avait la sienne, puis reprenait celle de
l'host en rentrant. Maintenant la date la plus avancee est celle du monde.

W1  l'invite part seul a Vernis et y passe du temps (il marche) : la date de l'host avance avec la sienne
W2  l'host passe du temps chez lui : la date de l'invite, toujours a Vernis, avance avec la sienne
W3  l'invite passe cinq heures d'un coup (ce que fait une nuit : GameDate.AdvanceMin) : l'host fait le meme saut
    de date, mais son personnage ne vit pas ces heures (pas de tours joues, pas plus faim)
W6  (joue apres W3, l'invite est encore seul a Vernis) le retour de la partie du 6 octobre 2026 : l'host fait
    passer 24 heures par le voyage (8 pas de carte du monde = 8 fois 3 heures) ; chez l'invite la date a avance,
    mais il n'a pas plus faim, sa viande fraiche n'a pas vieilli, et meme affame il n'en meurt pas. Puis la meme
    chose dans l'autre sens (l'invite voyage, l'host reste). Temoin : chacun fait LUI-MEME passer une heure en
    marchant : ses tours sont joues et sa viande vieillit, comme en solo
W4  l'invite rentre : sa date ne saute pas, les deux jeux ont la meme
W7  (apres W4, l'invite est sur la carte de l'host) l'host fait passer trois heures comme le voyage express, sans
    message : l'invite n'a pas plus faim, sa viande n'a pas vieilli, sa quete aleatoire garde son temps restant
W5  case decochee : l'ancien comportement, l'host n'avance plus avec l'invite

Tolerance de W3 et W6 : 40 tours du personnage au plus pendant le temps des autres (avant la correction : 960
pour 24 heures). Le joueur ne joue pas, mais son jeu peut finir une action en cours ou jouer quelques tours le
temps des commandes du banc ; 40 tours, c'est moins d'un tirage de faim (un tirage tous les 50 tours, +1 une fois
sur trois), d'ou « faim : +1 au plus ». Le temoin compte les tours et la viande, pas la faim : en une heure de
marche la faim ne monte pas a coup sur (deux tirages a une chance sur trois).

Ce que le banc ne joue pas comme un joueur :
- le voyage de l'autre joueur est 8 fois `GameDate.AdvanceMin(180)` dans son jeu (ce que fait chaque pas sur la
  carte du monde, Chara.cs:3013), sans le pas lui-meme : ni sortie de carte, ni les 120 tours du voyageur ; W3 est
  un seul saut de 300 minutes ; une vraie nuit (LayerSleep, bonds de 10 minutes) n'est pas jouee ;
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
from combat_suite import set_option  # noqa: E402
import move_suite  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from quest_suite import accept, in_log, offer  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually,  # noqa: E402
                          move, scan_logs, wait)

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
    """Ce joueur fait passer 24 heures comme par 8 pas sur la carte du monde."""
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
    check(f"{other} voyage 24 heures : la date de {who} a suivi (+{date(still) - d0} min, ecart {gap()})", followed)
    untouched(still, who, meat, before)

    # affame : avant la correction, 960 tours a cette phase (un coup une fois sur cinq) tuaient le personnage
    hunger, hp0 = before[1], body(still)[2]
    ev(still, 'EClass.pc.hunger.Set(EClass.pc.hunger.max); "ok"')
    try:
        d0 = date(still)
        travel_day(mover)
        eventually(lambda: date(still) - d0 >= 1438, timeout=30)
        _, _, hp, dead = body(still)
        check(f"{who} affame, {other} voyage encore 24 heures : il n'en meurt pas (vie {hp0} -> {hp}, un quart perdu au plus)",
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


def express():
    """W7 : l'invite est sur la carte de l'host, qui fait passer trois heures comme le voyage express
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
    accept(A, quest)
    left = lambda: int(ev(A, f'var q = EClass.game.quests.list.Find(x => x.uid == {quest}); '  # noqa: E731
                             'return q == null ? "-99999" : (q.deadline - EClass.world.date.GetRaw()).ToString();'))
    if not check("l'invite, sur la carte de l'host, a une viande fraiche et une quete aleatoire",
                 meat is not None and eventually(lambda: in_log(A, quest) and age(A, meat) == 0, timeout=15)):
        return
    ev(A, f'var q = EClass.game.quests.list.Find(x => x.uid == {quest}); if (q.deadline <= 0) q.deadline = EClass.world.date.GetRaw() + 2880; "ok"')
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
        express()

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
