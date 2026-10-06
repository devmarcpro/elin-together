"""Personnage a la connexion. Test court, sur des instances deja lancees (host + 1 client).

    python _tools/mp_test.py
    python _tools/chara_suite.py      # ~12 minutes, finit avec le client en jeu sur son premier personnage

Depuis l'etape 1 du conseil 9 (A1) un joueur qui revient n'est plus interroge : il reprend le dernier personnage
joue. L'ecran de choix ne s'ouvre que si l'host coche « Players choose their character when joining » (reglage
ChooseCharacter, eteint par defaut), ou si rien ne dit quel personnage il jouait.

C1  le client se deconnecte et revient : aucun ecran, il reprend son personnage
C2  case de l'host cochee : il revient, l'ecran propose son personnage et "nouveau personnage" ; il choisit
    "nouveau personnage" : creation (avec un objet detruit sous le pointeur, voir CharaMakerHoverPatch), un autre
    personnage, l'host en garde deux
C3  case cochee : il revient, l'ecran propose les deux, il reprend le premier, avec sa renommee
C4  il prend le second (case cochee), puis case decochee : il revient sans ecran sur le second, le dernier joue,
    pas le premier de la liste
C5  il change de personnage (il jouait le second, il revient avec le premier) : le second n'est sur la carte ni chez
    l'host ni chez l'invite, n'est plus dans le groupe ni parmi les habitants de la base, tout de suite, quand
    l'invite tient une carte seul, apres que l'host a quitte la carte et y est revenu ; il garde son sac, son or et
    ses points de vie ; le joueur le reprend et le retrouve tel quel
    Ce que C5 ne joue pas comme un joueur : aucun chemin du jeu n'a ete trouve qui remet l'ancien personnage sur
    une carte, alors le banc pose lui-meme les trois etats que l'enquete a trouves (par eval) : « sa zone est une
    carte » dans le monde de l'invite puis dans celui de l'host (ce que Map.OnDeactivate laisse a un personnage
    reste sur une carte quittee), et « sur la carte avec une zone vide » chez l'host. Les cartes sont changees par
    MoveZone direct, pas a pied. Pas joue : un combat pres de l'ancien personnage, une sauvegarde puis un
    rechargement de l'host, trois joueurs (l'ancien personnage vu par un autre invite qui tient la carte).

Ce que le banc ne joue pas comme un joueur : les boutons sont cliques par le pont, pas a la souris ; le joueur quitte
par ResetSession (le bouton « Disconnect » du mod fait la meme chose) ; connexion locale par port, un seul compte
Steam. Pas joue : un joueur qui a plusieurs personnages et dont le dernier joue n'existe plus (l'ecran doit s'ouvrir).
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from combat_suite import set_option  # noqa: E402
from mp_test import EMBARK, log, ok, shot, state, wait  # noqa: E402
from travel_suite import (HOME, LUMIEST, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, move,  # noqa: E402
                          scan_logs, zone_uid)

H, A = 27551, 27552

CHOICES = ('var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return ""; '
           'return string.Join("|", d.GetComponentsInChildren<UnityEngine.UI.Button>(true).Where(x => x.name.StartsWith("ButtonGeneral(Clone)"))'
           '.Select(x => x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Last().text));')


# un objet detruit parmi ceux que le pointeur survole, et l'ecran de creation qui les relit, dans la meme image
# (a la suivante le jeu refait sa liste si la fenetre a le focus)
STALE_HOVER = ('var go = new UnityEngine.GameObject("emp_test_hover"); InputModuleEX.GetPointerEventData().hovered.Add(go); '
               'UnityEngine.Object.DestroyImmediate(go); EClass.ui.GetLayer<LayerEditBio>().maker.RefreshPortraitZoom(); "ok"')


def click(index):
    return ev(A, 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return "no dialog"; '
                 'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(true).Where(x => x.name.StartsWith("ButtonGeneral(Clone)")).ToList(); '
                 f'b[{index} < 0 ? b.Count + {index} : {index}].onClick.Invoke(); return "clic";')


def leave():
    ev(A, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
    time.sleep(3)
    if state(A).get("sceneMode") != "Title":
        # comme le bouton "se deconnecter" du menu
        emp.call(A, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
    wait(lambda: state(A).get("sceneMode") == "Title" and not state(A)["connected"], "client a l'ecran titre", timeout=60)
    wait(lambda: len(state(H).get("players", [])) == 1, "l'host ne voit plus le client", timeout=60)
    time.sleep(3)


def connect():
    """Demande la connexion et attend l'ecran de choix ; renvoie les choix proposes."""
    ok(emp.call(A, "command", {"cmd": "emp.connect_udp"}))
    found = []

    def offered():
        found[:] = [c for c in ev(A, CHOICES).split("|") if c]
        return len(found) >= 2

    wait(offered, "ecran de choix du personnage", timeout=90, every=2.0)
    return list(found)


def connect_unasked():
    """Demande la connexion et regarde jusqu'a l'arrivee en jeu ; vrai si aucun ecran de choix ne s'est ouvert."""
    ok(emp.call(A, "command", {"cmd": "emp.connect_udp"}))
    asked = False
    end = time.time() + 90
    while time.time() < end and not (state(A)["sceneMode"] == "Zone" and state(A)["connected"]):
        asked = asked or bool(ev(A, CHOICES))
        time.sleep(0.5)
    return not asked


def in_game():
    def cond():
        if state(A)["sceneMode"] == "Zone" and state(A)["connected"]:
            return True
        emp.call(A, "eval", {"code": EMBARK}, timeout=180)
        return False

    wait(cond, "client en jeu", timeout=180, every=3.0)
    wait(lambda: len(state(H).get("players", [])) == 2, "l'host voit le client", timeout=60)
    time.sleep(4)
    return state(A)["pc"]["uid"]


def roster():
    return ev(H, 'var r = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetHost"), "PlayerRosters")'
                 '.GetValue(null) as System.Collections.Generic.Dictionary<ulong, System.Collections.Generic.List<int>>; '
                 'return string.Join(";", r.Values.Select(l => string.Join(",", l)));')


def standing(port, uid):
    """Le personnage est-il sur la carte active de ce jeu."""
    return ev(port, f'EClass._map.charas.Any(c => c.uid == {uid}).ToString()') == "True"


def waiting(uid):
    """Chez l'host : "<sans zone>|<dans le groupe>|<habitant de la base>|<mort>" ; un personnage qui attend son
    joueur donne True|False|-|False (il reste habitant de la base : le retirer detruisait des artefacts en double a chaque retour)."""
    return ev(H, f'var c = EClass.game.cards.globalCharas.Find({uid}); if (c == null) return "disparu"; '
                 'return (c.currentZone == null) + "|" + EClass.pc.party.members.Contains(c) + "|" '
                 '+ "-" + "|" + c.isDead;')  # (habitant : il le reste, voir RemoveRemoteChara)


def belongings(port, uid):
    """"<objets du sac>|<or>|<points de vie>" du personnage, tel que ce jeu le connait (sans les jetons de competence,
    que seul le jeu de celui qui le joue fabrique)."""
    return ev(port, f'var c = EClass.game.cards.globalCharas.Find({uid}); if (c == null) return "disparu"; '
                    'return c.things.Count(t => !(t.trait is TraitAbility)) + "|" + c.GetCurrency() + "|" + c.hp;')


def rearm(port, uid, zone):
    """Ce que Map.OnDeactivate laisse a un personnage reste sur une carte quittee : sa zone est cette carte."""
    ev(port, f'EClass.game.cards.globalCharas.Find({uid}).currentZone = EClass.game.spatials.Find({zone}); "ok"')


def c5(first, second):
    log("--- C5")
    # il joue le second (fin de C4). Ce qu'il a, vu par l'host, avant de le laisser
    time.sleep(3)
    had = belongings(H, second)
    log(f"le second a : {had} (objets|or|vie)")
    set_option("ChooseCharacter", True)
    time.sleep(2)
    leave()
    check("le joueur parti, son personnage attend : sans zone, hors du groupe, vivant",
          waiting(second) == "True|False|-|False")
    connect()
    click(0)
    check("il revient avec l'autre personnage (le premier)", in_game() == first)
    check("tout de suite : l'ancien n'est sur la carte ni chez l'host ni chez l'invite",
          not standing(H, second) and not standing(A, second) and waiting(second) == "True|False|-|False")

    # l'host quitte la carte : l'invite la tient seul, aucun filet de l'host ne tourne dans son jeu
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=180)
    wait(client_settled(A, HOME, True), "l'invite tient la Prairie seul", timeout=120)
    check("l'invite tient la carte seul : l'ancien n'y est pas", not standing(A, second))
    # dans le monde de l'invite (la copie recue a sa connexion) l'ancien personnage a encore une carte pour zone
    rearm(A, second, LUMIEST)
    move(A, LUMIEST)
    wait(client_settled(A, LUMIEST, True), "l'invite seul a Lumiest", timeout=180)
    time.sleep(3)
    check("l'invite active seul une carte ou son monde range l'ancien personnage : il n'y est pas",
          not standing(A, second))

    # chez l'host : l'ancien etait reste sur la Prairie quand il l'a quittee
    rearm(H, second, HOME)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host de retour a la Prairie", timeout=180)
    check("l'host revient sur la carte : l'ancien n'y est pas, des l'arrivee", not standing(H, second))
    move(A, HOME)
    both_joined(H, A, HOME)
    check("les deux de retour sur la carte : l'ancien n'y est ni chez l'host ni chez l'invite",
          not standing(H, second) and not standing(A, second))

    # sur la carte avec une zone vide : le filet de l'host le laissait la (RemoveRemoteChara, branche « ailleurs »)
    ev(H, f'var c = EClass.game.cards.globalCharas.Find({second}); '
          'EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(allowChara: false) ?? EClass.pc.pos); c.currentZone = null; "ok"')
    check("pose sur la carte avec une zone vide : retire en quelques secondes, chez l'host et chez l'invite",
          eventually(lambda: not standing(H, second) and not standing(A, second), timeout=15))
    time.sleep(10)
    check("dix secondes plus tard il attend toujours : sans zone, hors du groupe, vivant",
          waiting(second) == "True|False|-|False" and not standing(H, second) and not standing(A, second))
    check(f"il a toujours son sac, son or et ses points de vie ({belongings(H, second)} pour {had})", belongings(H, second) == had)

    leave()
    connect()
    click(1)
    check("le joueur reprend l'ancien personnage", in_game() == second)
    check(f"il le retrouve tel quel dans son jeu ({belongings(A, second)} pour {had})", belongings(A, second) == had)
    check("il est de nouveau sur la carte chez les deux, une seule fois parmi les habitants de la base",
          standing(H, second) and standing(A, second)
          and ev(H, f'EClass.pc.homeBranch.members.Count(c => c.uid == {second}).ToString()') == "1")
    check("et c'est le premier qui attend a son tour", waiting(first) == "True|False|False|False" and not standing(H, first))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        if not state(A)["connected"]:
            from mp_test import join_client
            join_client(H, A, "client")
        first = state(A)["pc"]["uid"]
        ev(A, 'EClass.player.ModFame(7); "ok"')
        time.sleep(2)
        fame = int(ev(A, 'EClass.player.fame.ToString()'))

        log("--- C1")
        set_option("ChooseCharacter", False)
        time.sleep(2)
        leave()
        check("il revient : aucun ecran de choix", connect_unasked())
        check("il reprend le meme personnage", in_game() == first)

        log("--- C2")
        set_option("ChooseCharacter", True)
        time.sleep(2)
        leave()
        choices = connect()
        log(f"choix proposes : {choices}")
        check("case de l'host cochee : l'ecran propose son personnage et \"nouveau personnage\"",
              len(choices) == 2 and choices[-1] == "A new character")
        click(-1)
        # ce que le pointeur survolait a ete detruit entre-temps (une fenetre sans le focus garde ses anciens
        # objets survoles) : l'ecran de creation du jeu trebuchait dessus en s'ouvrant, le bouton gardait
        # l'action du jeu et le joueur restait bloque sur les reglages du monde
        wait(lambda: ev(A, '(EClass.ui.GetLayer<LayerEditBio>() != null).ToString()') == "True", "ecran de creation", timeout=60)
        hover = emp.call(A, "eval", {"code": STALE_HOVER}, timeout=180)
        check(f"un objet detruit sous le pointeur ne casse pas l'ecran de creation ({hover.get('error') or 'ok'})"[:200],
              hover.get("ok"))
        second = in_game()
        check("\"nouveau personnage\" : il joue un autre personnage", second != first)
        check("l'host garde les deux", eventually(lambda: sorted(roster().split(",")) == sorted([str(first), str(second)]), timeout=10))
        check("le nouveau commence sans la renommee du premier", int(ev(A, 'EClass.player.fame.ToString()')) == 0)

        log("--- C3")
        leave()
        choices = connect()
        log(f"choix proposes : {choices}")
        check("l'ecran propose les deux personnages", len(choices) == 3)
        click(0)
        check("il reprend le premier", in_game() == first)
        check("avec sa renommee", eventually(lambda: int(ev(A, 'EClass.player.fame.ToString()')) == fame, timeout=10))

        log("--- C4")
        leave()
        connect()
        click(1)
        check("case cochee : il prend le second", in_game() == second)
        set_option("ChooseCharacter", False)
        time.sleep(2)
        leave()
        check("case decochee, deux personnages : aucun ecran de choix", connect_unasked())
        check("il reprend le dernier joue (le second), pas le premier de la liste", in_game() == second)

        c5(first, second)
        # finir sur le premier personnage, comme les autres suites l'attendent
        leave()
        connect()
        click(0)
        check("pour finir il reprend le premier", in_game() == first)
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {ex}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-chara-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass
    finally:
        try:
            set_option("ChooseCharacter", False)
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
