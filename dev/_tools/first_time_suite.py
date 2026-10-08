"""Deux joueurs qui jouent ensemble pour la premiere fois, sur un monde tout neuf, par les ecrans et les boutons du jeu.
Demande de l'utilisateur (8 octobre 2026), apres le retour de testeurs sur le premier dialogue d'Ashland.

    python _tools/first_time_suite.py              # aucun Elin ouvert : la suite lance les deux fenetres elle-meme
    python _tools/first_time_suite.py --keep       # laisse les deux fenetres ouvertes a la fin

F1  l'host : ecran titre, « Create an adventurer », la feuille, la loi du monde, le texte d'ouverture clique jusqu'au
    bout : il est dans la Prairie, l'histoire a 0, rien de revendique
F2  l'host marche jusqu'a Ashland et lui parle : un acte de propriete a ses pieds, la quete de la base commence
F3  l'host ramasse l'acte, le lit et repond oui : la Prairie est revendiquee, la quete principale passe a 200
F4  l'host ouvre sa partie, l'invite (deuxieme fenetre, ecran titre) le rejoint et cree son personnage : deux joueurs
    dans les deux jeux, les memes quetes, aucun dialogue ouvert tout seul
F5  l'invite marche jusqu'a Ashland et lui parle : une hache et dix lingots, une seule fois, la quete principale a 250
    et celle de la base a 2 dans les deux jeux, le dialogue arrive a son menu
F6  l'invite ramasse la hache et l'or : ils sont dans son sac dans les deux jeux
F7  l'invite reparle a Ashland : le menu tout de suite, rien n'est redonne
F8  l'host sauvegarde, les deux jeux sont fermes puis relances ; l'host reprend par « Continue », l'invite le rejoint
    sans recreer de personnage : aucun dialogue ne se rouvre, les quetes et le sac de l'invite sont ceux d'avant

Ce que le banc ne joue PAS comme deux vrais joueurs : la connexion passe par le reseau local (`emp.add_local`,
`emp.connect_udp`) et non par Steam (un seul compte Steam sur ce PC) ; un bouton est « clique » par son onClick et
non par la souris ; une ligne de dialogue avance par DramaSequence.PlayNext ; l'acte est lu par TraitDeed.OnRead (ce
que fait le clic « lire ») ; les jeux sont fermes en tuant leur processus apres la sauvegarde, pas par « Exit »."""
import subprocess
import sys
import time
from datetime import datetime, timezone

import emp
from mp_test import GAME_EXE, LAB_EXE, SHOTS, WINDOW, bridge_for, join_client, log, ok, state, wait
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
STARTED = []

UI = ('var top = EClass.ui.layers.LastOrDefault(); if (top == null) return ""; '
      'return top.GetType().Name + "|" + string.Join("|", top.GetComponentsInChildren<UnityEngine.UI.Button>(false).Where(b => b.interactable).Select(b => b.name + ":" + '
      'string.Join(" ", b.GetComponentsInChildren<UnityEngine.UI.Text>(true).Select(t => t.text))));')
CLICK = ('var top = EClass.ui.layers.LastOrDefault(); if (top == null) return "pas de fenetre"; var want = "%s"; '
         'var b = top.GetComponentsInChildren<UnityEngine.UI.Button>(false).Where(x => x.interactable).FirstOrDefault(x => x.name == want || '
         'x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.Contains(want))); '
         'if (b == null) return "pas de bouton"; b.onClick.Invoke(); return "clic";')
QUESTS = ('var m = EClass.game.quests.Get<QuestMain>(); var h = EClass.game.quests.Get<QuestHome>(); '
          'return "main=" + (m == null ? "none" : m.phase.ToString()) + " home=" + (h == null ? "none" : h.phase.ToString()) + '
          '" base=" + (EClass.Branch != null) + " dialogue=" + (LayerDrama.Instance != null);')
# (acte, hache, lingots) par terre ; puis dans le sac du joueur de ce numero
GROUND = ('System.Func<string, int> n = id => EClass._map.things.Where(t => t.id == id).Sum(t => t.Num); '
          'return n("deed") + "," + n("axe") + "," + n("money2");')
BAG = ('var c = EClass._map.charas.Find(x => x.uid == %d); if (c == null) return "-1,-1,-1"; '
       'System.Func<string, int> n = id => c.things.Where(t => t.id == id).Sum(t => t.Num); return n("deed") + "," + n("axe") + "," + n("money2");')
STEP = ('var d = LayerDrama.Instance; if (d == null) return "ferme|0"; return d.drama.sequence.lastStep + "|" + '
        'd.GetComponentsInChildren<UnityEngine.UI.Button>(false).Count(x => x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.Length > 3));')
NEXT = 'var d = LayerDrama.Instance; if (d == null) return "ferme"; d.drama.sequence.PlayNext(); return "suite";'
HANG_UP = 'if (LayerDrama.Instance != null) EClass.ui.RemoveLayer<LayerDrama>(); "ok"'


def nums(text):
    return [int(x) for x in text.split(",")]


def launch(exe, name, logname=None):
    args = [str(exe), *WINDOW] + (["-logFile", str(SHOTS / logname)] if logname else [])
    p = subprocess.Popen(args, cwd=exe.parent)
    STARTED.append(p)
    log(f"{name} lance (pid {p.pid})")
    port = wait(lambda: bridge_for(p.pid), f"pont de {name}", timeout=600)
    wait(lambda: state(port).get("sceneMode") == "Title", f"ecran titre de {name}", timeout=300)
    time.sleep(8)
    return port


def close_all():
    for p in STARTED:
        p.kill()
    STARTED.clear()
    time.sleep(6)


def click(port, what, pause=1.5):
    r = ev(port, CLICK % what)
    time.sleep(pause)
    return r == "clic"


def through(port, limit=80):
    """Clique un dialogue ligne apres ligne jusqu'a un choix ou sa fin : renvoie (etape, etapes vues, clics)."""
    seen = []
    for clicks in range(limit + 1):
        step, _, choices = ev(port, STEP).partition("|")
        if step not in seen:
            seen.append(step)
        if step == "ferme" or int(choices) > 0:
            return step, seen, clicks
        ev(port, NEXT)
        time.sleep(1.0)
    return step, seen, clicks


def walk_to(port, target):
    """Le joueur marche (AI_Goto, le clic sur une case) jusqu'a cote de cette chose ou de ce personnage."""
    ev(port, f'var c = {target}; if (c == null) return "absent"; var p = c.pos.GetNearestPoint(false, false) ?? c.pos; '
             'EClass.pc.SetAIImmediate(new AI_Goto(p.Copy(), 0)); return "en route";')
    return eventually(lambda: int(ev(port, f'var c = {target}; return c == null ? "99" : EClass.pc.pos.Distance(c.pos).ToString();')) <= 1, timeout=40)


def talk(port):
    ash = 'EClass._map.charas.Find(x => x.id == "ashland")'
    near = walk_to(port, ash)
    ev(port, f'{ash}.ShowDialog(); "ok"')
    eventually(lambda: ev(port, '(LayerDrama.Instance != null).ToString()') == "True", timeout=10)
    time.sleep(1)
    step, seen, clicks = through(port, 20)
    ev(port, HANG_UP)
    time.sleep(2)
    return near, step, seen, clicks


def pick_all(port, ids):
    for thing_id in ids:
        target = f'EClass._map.things.Find(t => t.id == "{thing_id}")'
        if ev(port, f'({target} != null).ToString()') != "True":
            continue
        near = walk_to(port, target)
        got = ev(port, f'var t = {target}; if (t == null) return "absent"; if (EClass.pc.ai != null) EClass.pc.ai.Cancel(); EClass.pc.Pick(t); return "pris";')
        log(f"{thing_id} : a cote {near}, {got}")
        time.sleep(1.5)


def f1():
    click(H, "button close")  # les annonces, quand le jeu les montre
    check("F1 ecran titre : « Create an adventurer » ouvre la feuille de personnage",
          click(H, "Create an adventurer") and ev(H, UI).startswith("LayerEditBio"))
    click(H, "ButtonEmbark")
    check("F1 « Create » ouvre la loi du monde", ev(H, UI).startswith("LayerWorldSetting"))
    click(H, "ButtonEmbark (1)", pause=6)
    step, seen, clicks = through(H)
    for _ in range(3):  # le texte d'ouverture continue dans la Prairie, en plusieurs dialogues
        time.sleep(3)
        if ev(H, '(LayerDrama.Instance != null).ToString()') == "True":
            more = through(H)
            clicks += more[2]
    s, q = state(H), ev(H, QUESTS)
    check(f"F1 le texte d'ouverture se clique jusqu'au bout ({clicks} clics) : l'host est en jeu ({(s.get('zone') or {}).get('name')}), histoire a 0, rien de revendique ({q})",
          s.get("sceneMode") == "Zone" and q == "main=0 home=none base=False dialogue=False")


def f2():
    near, step, seen, clicks = talk(H)
    q, g = ev(H, QUESTS), nums(ev(H, GROUND))
    check(f"F2 l'host marche jusqu'a Ashland ({near}) et lui parle : etapes {seen}, menu atteint ({step}) en {clicks} clics", near and step == "main" and seen[0] == "start_FirstMeet")
    check(f"F2 un acte de propriete par terre ({g[0]}), la quete de la base est commencee ({q})", g[0] == 1 and "main=0 home=0" in q)


def f3():
    pick_all(H, ["deed"])
    me = int(ev(H, "EClass.pc.uid.ToString()"))
    check(f"F3 l'host ramasse l'acte (sac : {ev(H, BAG % me)})", nums(ev(H, BAG % me))[0] == 1)
    ev(H, 'var t = EClass.pc.things.Find(x => x.id == "deed"); t.trait.OnRead(EClass.pc); "ok"')
    time.sleep(2)
    asked = ev(H, UI)
    yes = click(H, "Yes", pause=4)
    q = ev(H, QUESTS)
    check(f"F3 l'acte lu pose la question ({asked.split('|')[0]}), oui ({yes}) : la Prairie est revendiquee, quete principale a 200 ({q})",
          yes and q == "main=200 home=1 base=True dialogue=False")


def join(first):
    ok(emp.call(H, "command", {"cmd": "emp.add_local"}))
    wait(lambda: state(H)["role"] == "Host", "partie ouverte")
    a = launch(LAB_EXE, "invite", "elin2-player.log")
    join_client(H, a, "invite")
    time.sleep(5)
    return a


def f4():
    a = join(True)
    h, g = state(H), state(a)
    check(f"F4 l'invite rejoint et cree son personnage : deux joueurs chez l'host ({len(h.get('players', []))}) et chez l'invite ({len(g.get('players', []))})",
          a == A and len(h.get("players", [])) == 2 and len(g.get("players", [])) == 2)
    qh, qa = ev(H, QUESTS), ev(A, QUESTS)
    check(f"F4 memes quetes, aucun dialogue ouvert tout seul : host ({qh}), invite ({qa})",
          qh == qa == "main=200 home=1 base=True dialogue=False")


def f5(ctx):
    ctx["guest"] = int(state(A)["pc"]["uid"])
    before = nums(ev(H, GROUND))
    near, step, seen, clicks = talk(A)
    check(f"F5 l'invite marche jusqu'a Ashland ({near}) et lui parle : etapes {seen}, menu atteint ({step}) en {clicks} clics",
          near and step == "main" and seen[0] == "start_AfterReadDeed")
    want = "main=250 home=2 base=True dialogue=False"
    eventually(lambda: ev(H, QUESTS) == want and ev(A, QUESTS) == want, timeout=15)
    qh, qa = ev(H, QUESTS), ev(A, QUESTS)
    check(f"F5 quete principale a 250, base a 2, dans les deux jeux : host ({qh}), invite ({qa})", qh == want and qa == want)
    gh, ga = nums(ev(H, GROUND)), nums(ev(A, GROUND))
    check(f"F5 une hache et dix lingots, une seule fois, par terre dans les deux jeux : host {before} -> {gh}, invite {ga}",
          gh[1] - before[1] == 1 and gh[2] - before[2] == 10 and ga == gh)


def f6(ctx):
    pick_all(A, ["axe", "money2"])
    time.sleep(3)
    bh, ba = nums(ev(H, BAG % ctx["guest"])), nums(ev(A, BAG % ctx["guest"]))
    ctx["bag"] = ba
    check(f"F6 l'invite ramasse la hache et l'or : dans son sac chez lui {ba} et chez l'host {bh}, plus rien par terre ({ev(H, GROUND)})",
          ba[1] >= 1 and ba[2] == 10 and bh == ba and nums(ev(H, GROUND))[1:] == [0, 0])


def f7(ctx):
    near, step, seen, clicks = talk(A)
    time.sleep(3)
    check(f"F7 l'invite reparle a Ashland : le menu tout de suite ({seen}), rien n'est redonne (par terre {ev(H, GROUND)}, sac {ev(A, BAG % ctx['guest'])})",
          seen == ["main"] and nums(ev(H, GROUND))[1:] == [0, 0] and nums(ev(A, BAG % ctx["guest"])) == ctx["bag"])


def f8(ctx):
    world = ev(H, "Game.id")
    saved = ev(H, "EClass.game.Save().ToString()")
    time.sleep(3)
    close_all()
    h = launch(GAME_EXE, "host")
    click(h, "button close")
    cont = click(h, "Continue", pause=3)
    listed = ev(h, UI)
    # la sauvegarde du monde de test, dans la liste du jeu
    loaded = ev(h, f'Game.TryLoad("{world}", false, () => Game.Load("{world}", false)).ToString()') if "LayerLoadGame" in listed else "pas de liste"
    wait(lambda: state(h)["gameStarted"] and state(h)["sceneMode"] == "Zone", "chargement du host", timeout=600)
    time.sleep(5)
    check(f"F8 l'host sauvegarde ({saved}), tout est ferme et relance, « Continue » ({cont}) puis sa partie {world} : il est en jeu ({ev(h, QUESTS)})",
          saved == "True" and ev(h, QUESTS) == "main=250 home=2 base=True dialogue=False")
    a = join(False)
    time.sleep(5)
    qh, qa = ev(H, QUESTS), ev(A, QUESTS)
    check(f"F8 l'invite le rejoint : aucun dialogue ne se rouvre, memes quetes, host ({qh}), invite ({qa})",
          qh == qa == "main=250 home=2 base=True dialogue=False")
    me = int(state(A)["pc"]["uid"])
    bag = nums(ev(A, BAG % me))
    check(f"F8 l'invite retrouve son personnage ({me}, avant {ctx['guest']}) et son sac ({bag}, avant {ctx['bag']}), rien de plus par terre ({ev(H, GROUND)})",
          me == ctx["guest"] and bag == ctx["bag"] and nums(ev(H, GROUND))[1:] == [0, 0])
    ctx["world"] = world


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    keep = "--keep" in sys.argv
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    if "Elin.exe" in subprocess.run(["tasklist", "/FI", "IMAGENAME eq Elin.exe"], capture_output=True, text=True).stdout:
        sys.exit("Elin tourne deja : ferme-le")
    ctx = {}
    try:
        launch(GAME_EXE, "host")
        for step in (f1, f2, f3, f4):
            log(f"--- {step.__name__}")
            step()
        for step in (f5, f6, f7, f8):
            log(f"--- {step.__name__}")
            step(ctx)
    except Exception as ex:  # noqa: BLE001
        check(f"la suite est allee au bout ({type(ex).__name__}: {ex})", False)
    finally:
        try:
            log(f"monde de test cree : {ctx.get('world') or ev(H, 'Game.id')} (a supprimer a la main des sauvegardes)")
        except Exception:  # noqa: BLE001
            pass
        scan_logs(t0)
        if not keep:
            close_all()
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
