"""Reprise du monde par un invite depuis sa copie, a la main (conseil 9, etape 4, tranche R2 de
PLAN_reprise_automatique.md). Test court, sur des instances deja lancees (host + 1 client, dans la meme carte).

    python _tools/mp_test.py
    python _tools/takeover_suite.py            # ~10 minutes : la reprise demandee a la main (emp.take_over), R2
    python _tools/takeover_suite.py --auto     # ~15 minutes : l'host quitte, l'invite reprend tout seul, R3
    python _tools/takeover_suite.py --menu     # pareil, l'host quitte par le menu du jeu (retour au titre, oui)

T0  (--auto) case « un autre joueur reprend quand l'host part » decochee : l'host ferme sa partie, l'invite se
    retrouve a l'ecran titre et ne rouvre rien ; l'host rouvre, l'invite revient seul. Puis la case est cochee.
T1  l'host sauvegarde sans geste, l'invite a une copie entiere du monde.
T2  l'host ferme sa partie (emp.disconnect), l'invite se retrouve a l'ecran titre ; emp.take_over : il rouvre le
    monde depuis sa copie, dans un dossier de sauvegarde neuf, y joue SON personnage avec son or, le numero de reprise
    du monde passe a 1, la partie est ouverte ; le personnage de l'ancien host attend son joueur ; ni la sauvegarde
    de l'host ni aucune autre sauvegarde n'a ete touchee.
    Avec --auto : pas de commande, l'host qui ferme previent et l'invite fait tout cela seul.
T3  l'ancien host rejoint la partie du nouvel host : il retrouve son personnage, sans ecran de creation.
(Joues dans l'ordre. Apres cette suite les roles sont inverses : relancer mp_test.py pour une autre suite.)

Ce que le banc ne joue pas comme un joueur :
- sans --auto la reprise est demandee par une commande de test ;
- l'host « part » en fermant sa session (emp.disconnect, ce que fait le bouton Disconnect) : il ne revient pas a
  l'ecran titre par le menu, ne ferme pas Elin, ne plante pas (R5) ;
- --menu : GotoTitle est appele par le pont de test (ce que fait la ligne du menu), le « oui » est clique ;
- la derniere copie est prouvee par un objet pose par l'HOST apres la derniere sauvegarde automatique ; ce que
  l'INVITE a fait entre-temps n'est pas mesure (il ne bouge pas) ;
- la case est cochee par une commande de test (emp.takeover_rule), pas dans l'onglet Server Setting ;
- deux fenetres sur un seul PC : le nouvel host ouvre un port local, pas un salon Steam ; l'ancien host le rejoint
  par ce port, pas par une invitation ni par la liste d'amis ;
- T3 : l'ancien host revient a l'ecran titre par le pont de test (sans sauvegarder), pas par le menu du jeu ;
- world_lab est un petit monde : le temps de reprise lu ici ne dit rien d'un grand monde ;
- pas joues : un invite parti sur une autre carte au moment de la reprise, un personnage mort, un invite arrive
  apres la derniere copie, un troisieme joueur, une copie abimee (l'invite doit refuser).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import SAVES, log, ok, shot, state  # noqa: E402
from travel_suite import RESULTS, check, dismiss_dialogs, ev, eventually, marker, players, scan_logs  # noqa: E402
from worldcopy_suite import BENCH, copies, guest_saves, host_files, same_as_host, save_once, whole  # noqa: E402

H, A = 27551, 27552
GOLD = 'EClass.game.cards.globalCharas.Find({uid}).GetCurrency().ToString()'
# la question du jeu « retourner au titre ? » : le premier bouton, oui
YES = ('var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return "no dialog"; '
       'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(true).Where(x => x.name.StartsWith("ButtonGeneral(Clone)")).ToList(); '
       'if (b.Count != 2) return "other dialog"; b[0].onClick.Invoke(); return "yes";')
TO_TITLE = 'EClass.ui.RemoveLayers(); EClass.game.Kill(); EClass.scene.Init(Scene.Mode.Title); "ok"'


def command(port, cmd):
    r = ok(emp.call(port, "command", {"cmd": cmd}, timeout=180))
    log(f"{port} {cmd} : {r}")
    return str(r)


def pc(port):
    return state(port).get("pc") or {}


def t0(ctx):
    """case decochee : l'host ferme, personne ne reprend ; puis l'invite revient seul"""
    if not check("depart : deux joueurs dans la partie", players(H) == 2 and players(A) == 2):
        return False
    command(H, "emp.takeover_rule 0")
    command(A, "emp.auto_open 1")
    command(A, "emp.link_timeout 1")
    had = copies()[-1:]
    if not check("l'host sauvegarde sans geste", save_once()):
        return False
    check("l'invite a une copie du monde", eventually(lambda: copies()[-1:] != had and same_as_host(copies()[-1]), timeout=120))
    before = {d.name for d in SAVES.iterdir() if d.is_dir()}
    command(H, "emp.disconnect")
    if not check("l'host parti, l'invite se retrouve a l'ecran titre",
                 eventually(lambda: state(A).get("sceneMode") == "Title", timeout=90)):
        return False
    time.sleep(40)
    s = state(A)
    told = ev(A, f"{BENCH}.Takeover")
    check(f"40 s plus tard il n'a rien rouvert (role {s.get('role')}, reprise : {told})",
          s.get("sceneMode") == "Title" and s.get("role") != "Host" and told == "idle")
    # (la copie de travail de l'invite, world_emp*, est effacee a chaque coupure : seuls les dossiers en plus comptent)
    added = {d.name for d in SAVES.iterdir() if d.is_dir()} - before
    check(f"aucun dossier de sauvegarde ajoute ({sorted(added) or 'aucun'})", not added)
    command(H, "emp.add_local")
    back = eventually(lambda: state(A).get("sceneMode") == "Zone" and state(A).get("connected") and players(H) == 2,
                      timeout=240)
    if not check("l'host rouvre sa partie, l'invite revient seul", back):
        return False
    time.sleep(5)
    command(H, "emp.takeover_rule 1")
    time.sleep(3)
    return True


def t1(ctx):
    """l'invite a une copie entiere du monde"""
    dismiss_dialogs(H)
    dismiss_dialogs(A)
    if not check("depart : deux joueurs dans la partie", players(H) == 2 and players(A) == 2):
        return False
    ctx["host"], ctx["guest"] = pc(H), pc(A)
    log(f"host : {ctx['host'].get('name')} ({ctx['host'].get('uid')}), invite : {ctx['guest'].get('name')} ({ctx['guest'].get('uid')})")
    had = copies()[-1:]
    if not check("l'host sauvegarde sans geste", save_once()):
        return False
    # ce que la sauvegarde de l'host dit de l'invite a ce moment-la : c'est ce que la copie contient
    ctx["gold"] = ev(H, GOLD.format(uid=ctx["guest"]["uid"]))
    if not check("l'invite a une copie entiere, la meme que le dossier de l'host",
                 eventually(lambda: copies()[-1:] != had and same_as_host(copies()[-1]), timeout=120)):
        log("etat chez l'invite : " + ev(A, f"{BENCH}.State"))
        return False
    check(f"l'or de l'invite est le meme chez lui et dans le monde de l'host ({ctx['gold']})",
          ev(A, "EClass.pc.GetCurrency().ToString()") == ctx["gold"])
    return True


def t2(ctx):
    """l'host parti, l'invite rouvre le monde depuis sa copie"""
    copy = copies()[-1]
    command(A, "emp.auto_open 1")
    command(A, "emp.link_timeout 1")
    if ctx["auto"]:
        ctx["saves"] = guest_saves()
        before = {d.name for d in SAVES.iterdir() if d.is_dir()}
        # pose apres la derniere sauvegarde automatique : dans le monde repris seulement si l'host, en partant,
        # a sauvegarde et envoye cette sauvegarde
        ctx["mark"], _ = marker(H)
        time.sleep(2)
        t = time.time()
        if ctx["menu"]:
            ev(H, 'EClass.game.GotoTitle(); "ok"')
            time.sleep(1)
            log("menu du jeu, retour au titre : " + ev(H, YES))
        else:
            command(H, "emp.disconnect")
        check("l'host a quitte sa partie", eventually(lambda: state(H).get("role") != "Host", timeout=60))
        time.sleep(1)
        ctx["world"] = host_files()
    else:
        command(H, "emp.disconnect")
        if not check("l'host parti, l'invite se retrouve a l'ecran titre",
                     eventually(lambda: state(A).get("sceneMode") == "Title", timeout=90)):
            return False
        time.sleep(3)
        ctx["world"] = host_files()
        ctx["saves"] = guest_saves()
        before = {d.name for d in SAVES.iterdir() if d.is_dir()}

        t = time.time()
        if not check("emp.take_over : la reprise commence", command(A, "emp.take_over") == "Taking the world over"):
            return False

    def hosting():
        s = state(A)
        return s.get("sceneMode") == "Zone" and s.get("role") == "Host" and ev(A, f"{BENCH}.Takeover").startswith("done")
    opened = eventually(hosting, timeout=300)
    log("reprise : " + ev(A, f"{BENCH}.Takeover"))
    since = "le depart de l'host" if ctx["auto"] else "la commande"
    if not check(f"l'invite est host du monde {time.time() - t:.0f} s apres {since}, sans un clic", opened):
        log(f"etat de l'invite : {state(A)}")
        return False
    time.sleep(3)

    world = ev(A, "Game.id")
    new = {d.name for d in SAVES.iterdir() if d.is_dir()} - before
    check(f"le monde est dans un dossier de sauvegarde neuf ({world})",
          world in new and world != "world_lab" and not world.startswith("world_emp"))
    me = pc(A)
    check(f"il joue son personnage ({me.get('name')}, {me.get('uid')}), pas celui de l'host",
          me.get("uid") == ctx["guest"]["uid"] and me.get("name") == ctx["guest"]["name"])
    gold = ev(A, "EClass.pc.GetCurrency().ToString()")
    check(f"avec son or ({gold}, {ctx['gold']} a la derniere copie)", gold == ctx["gold"])
    if ctx.get("mark"):
        check("ce que l'host a fait apres la derniere sauvegarde automatique est dans le monde repris (un seau pose)",
              ev(A, f"EClass._map.things.Any(t => t.uid == {ctx['mark']}).ToString()") == "True")
    check("vivant, sur une carte", not me.get("isDead") and ev(A, "EClass.pc.IsInActiveZone.ToString()") == "True")
    number = ev(A, f"{BENCH}.Handover.ToString()")
    check(f"le numero de reprise du monde est 1 ({number})", number == "1")
    who = ev(A, f"{BENCH}.Who")
    log("qui joue qui : " + who)
    check("le personnage de l'ancien host est garde pour son joueur",
          who.rstrip().endswith(f"={ctx['host']['uid']}") or f"={ctx['host']['uid']}," in who)
    check("et il n'est pas sur la carte",
          ev(A, f"EClass._map.charas.Any(c => c.uid == {ctx['host']['uid']}).ToString()") == "False")
    open_ui = ev(A, 'EClass.ui.IsActive ? string.Join(",", EClass.ui.layers.Select(l => l.GetType().Name)) : ""')
    check(f"aucune fenetre ouverte chez lui ({open_ui or 'aucune'})", not open_ui)

    check("la sauvegarde de l'host n'a pas change d'un octet", host_files() == ctx["world"])
    now = guest_saves()
    changed = sorted(k for k, v in ctx["saves"].items() if now.get(k) != v)
    added = {k.split("/")[1] for k in now if k not in ctx["saves"]}
    check("aucune sauvegarde deja la n'a ete touchee" + (f", change : {changed[:5]}" if changed else ""), not changed)
    check(f"un seul dossier ajoute dans les sauvegardes ({sorted(added)})", added == {world})
    check("la copie qui a servi est toujours la, entiere", copy in copies() and whole(copy))

    # la sauvegarde ecrite par la reprise porte le numero : relue sur le disque, pas dans le jeu
    saved = (SAVES / world / "game.txt").exists() and (SAVES / world / "index.txt").exists()
    check("le dossier neuf est une sauvegarde du jeu (game.txt, index.txt)", saved)
    return True


def t3(ctx):
    """l'ancien host rejoint le nouvel host et retrouve son personnage"""
    if state(H).get("gameStarted"):
        ev(H, TO_TITLE)
    if not check("l'ancien host est a l'ecran titre", eventually(lambda: state(H).get("sceneMode") == "Title", timeout=60)):
        return False
    time.sleep(3)
    command(H, "emp.connect_udp")
    asked = []

    def joined():
        if ev(H, '(EClass.ui.GetLayer<LayerEditBio>() != null).ToString()') == "True":
            asked.append(1)
            return True
        return state(H).get("sceneMode") == "Zone" and state(H).get("connected")
    back = eventually(joined, timeout=300)
    if not check("on ne lui demande pas de creer un personnage", not asked):
        return False
    if not check("il est dans la partie du nouvel host", back):
        log(f"etat de l'ancien host : {state(H)}")
        return False
    time.sleep(5)
    me = pc(H)
    check(f"il retrouve son personnage ({me.get('name')}, {me.get('uid')})",
          me.get("uid") == ctx["host"]["uid"] and me.get("name") == ctx["host"]["name"])
    check("deux joueurs des deux cotes", eventually(lambda: players(H) == 2 and players(A) == 2, timeout=60))
    check("le nouvel host joue toujours le sien", pc(A).get("uid") == ctx["guest"]["uid"])
    check("la sauvegarde de l'ancien host n'a toujours pas change", host_files() == ctx["world"])
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--menu", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"auto": a.auto or a.menu, "menu": a.menu}
    try:
        for step in ((t0, t1, t2, t3) if ctx["auto"] else (t1, t2, t3)):
            log(f"--- {step.__name__.upper()} : {step.__doc__}")
            try:
                good = step(ctx)
            except Exception as ex:  # noqa: BLE001
                good = check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
            if not good:
                for name, port in (("host", H), ("A", A)):
                    try:
                        print(f"    capture {name} : {shot(f'fail-takeover-{step.__name__}-{name}', port)}")
                    except Exception:  # noqa: BLE001
                        pass
                break
    finally:
        for port, cmd in ((H, "emp.autosave_every 0"), (A, "emp.link_timeout 0"), (H, "emp.takeover_rule 0"),
                          (A, "emp.takeover_rule 0")):
            try:
                emp.call(port, "command", {"cmd": cmd})
            except Exception:  # noqa: BLE001
                pass
    scan_logs(start)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
