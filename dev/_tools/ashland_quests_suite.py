"""Les trois premieres demandes d'Ashland, prises au tableau des quetes par l'invite et par l'host, sur un monde neuf.

    python _tools/first_time_suite.py --keep     # deux joueurs sur un monde neuf, l'histoire a 250
    python _tools/ashland_quests_suite.py

Q1  le tableau des quetes de l'invite et celui de l'host montrent les trois memes demandes d'Ashland
Q2  l'invite clique « Essential Equipment » : le dialogue va au bout, la quete est au journal des deux jeux et n'est
    plus proposee, le coffre offert tombe une fois
Q3  l'invite clique « Way of Crafter » : pareil, sans cadeau en double
Q4  l'host clique « Defense Training » : pareil
Q5  les deux tableaux sont vides des trois demandes, les deux jeux sont d'accord sur tout ce que la chasse compare
Q6  l'invite reparle a Ashland : rien n'est redonne, rien n'est repropose

Pas comme un joueur : le tableau est ouvert par EClass.ui.AddLayer<LayerQuestBoard>() (ce que fait « lire le
tableau »), les boutons par leur onClick, les lignes par ce que fait le clic."""
import sys
import time
from datetime import datetime, timezone

from bot import doubles, settle
from dialog_walk_suite import CLOSE, WORLD, leave, open_dialog, to_menu
from mp_test import log, state
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
BOARD = ('var b = EClass.ui.GetLayer<LayerQuestBoard>(); if (b == null) return "ferme"; '
         'return string.Join("|", b.GetComponentsInChildren<UnityEngine.UI.Button>(false).Where(x => x.name.StartsWith("item quest"))'
         '.Select(x => x.GetComponentsInChildren<UnityEngine.UI.Text>(true).First(t => t.text.Length > 3).text));')
CLICK = ('var b = EClass.ui.GetLayer<LayerQuestBoard>(); if (b == null) return "ferme"; var x = b.GetComponentsInChildren<UnityEngine.UI.Button>(false)'
         '.FirstOrDefault(i => i.name.StartsWith("item quest") && i.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.Contains("%s"))); '
         'if (x == null) return "pas de demande"; x.onClick.Invoke(); return "clic";')
JOURNAL = 'string.Join(",", EClass.game.quests.list.Select(q => q.id + ":" + q.phase).OrderBy(x => x))'
OFFERS = 'string.Join(",", EClass.game.quests.globalList.Select(q => q.id).OrderBy(x => x))'
CHESTS = 'EClass._map.things.Concat(EClass._map.charas.SelectMany(c => c.things)).Where(t => t.id == "chest6").Sum(t => t.Num).ToString()'


def board(port):
    ev(port, CLOSE)
    ev(port, 'EClass.ui.AddLayer<LayerQuestBoard>(); "ok"')
    time.sleep(2)
    return [t for t in ev(port, BOARD).split("|") if t]


def take(port, name, title, quest, world):
    """Ce joueur clique cette demande au tableau et va au bout du dialogue."""
    chests = int(ev(H, CHESTS))
    listed = board(port)
    clicked = ev(port, CLICK % title)
    opened = eventually(lambda: ev(port, '(LayerDrama.Instance != null).ToString()') == "True", timeout=10)
    time.sleep(1)
    problem, step, _, seen, clicks = to_menu(port)
    leave(port)
    ev(port, CLOSE)
    check(f"{name} clique « {title} » au tableau ({clicked}, {len(listed)} demandes) : le dialogue s'ouvre ({opened}) et va au bout ({step}, {clicks} clics, etapes {sorted(set(seen))}){' : ' + problem if problem else ''}",
          clicked == "clic" and opened and problem is None)
    want = lambda p: quest + ":" in ev(p, JOURNAL) and quest not in ev(p, OFFERS).split(",")  # noqa: E731
    eventually(lambda: want(H) and want(A), timeout=15)
    check(f"{name} > « {title} » : la quete {quest} est au journal et n'est plus proposee, chez l'host (journal {ev(H, JOURNAL)} ; offres {ev(H, OFFERS)}) "
          f"et chez l'invite (journal {ev(A, JOURNAL)} ; offres {ev(A, OFFERS)})", want(H) and want(A))
    same, wh, wa = settle(lambda: ev(H, world), lambda: ev(A, world), timeout=12)
    check(f"{name} > « {title} » : les deux jeux sont d'accord ({wh[:260]}){'' if same else ' / invite ' + wa[:260]}", same)
    twice = doubles(H) + doubles(A)
    check(f"{name} > « {title} » : aucun objet en double ({twice or 'aucun'})", not twice)
    return int(ev(H, CHESTS)) - chests


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    for port in (H, A):
        ev(port, CLOSE)
    world = WORLD % f'{int(state(H)["pc"]["uid"])}, {int(state(A)["pc"]["uid"])}'
    bh, ba = board(H), board(A)
    for port in (H, A):
        ev(port, CLOSE)
    if not check(f"Q1 les deux tableaux montrent les trois memes demandes d'Ashland : host {bh}, invite {ba}",
                 len(bh) == 3 and bh == ba and ev(H, OFFERS) == "crafter,defense,sharedContainer"):
        return finish(t0)
    got = take(A, "Q2 l'invite", "Essential Equipment", "sharedContainer", world)
    check(f"Q2 le coffre offert tombe une fois ({got})", got == 1)
    got = take(A, "Q3 l'invite", "Way of Crafter", "crafter", world)
    check(f"Q3 pas de coffre en plus ({got})", got == 0)
    take(H, "Q4 l'host", "Defense Training", "defense", world)
    bh, ba = board(H), board(A)
    for port in (H, A):
        ev(port, CLOSE)
    check(f"Q5 plus aucune des trois demandes aux deux tableaux : host {bh}, invite {ba}", bh == ba == [])
    before = ev(H, world)
    ash = int(ev(A, 'EClass._map.charas.Find(x => x.id == "ashland").uid.ToString()'))
    opened = open_dialog(A, ash)
    problem, step, _, seen, clicks = to_menu(A)
    leave(A)
    same, wh, wa = settle(lambda: ev(H, world), lambda: ev(A, world), timeout=12)
    log(f"Q6 etapes {seen}, {clicks} clics")
    check(f"Q6 l'invite reparle a Ashland ({opened}, arrive a {step}) : rien n'est redonne ni repropose ({'rien de change' if wh == before else before[:200] + ' -> ' + wh[:200]}), jeux d'accord ({same})",
          opened and problem is None and same and wh == before)
    finish(t0)


def finish(t0):
    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
