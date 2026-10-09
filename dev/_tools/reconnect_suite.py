"""Retour automatique apres une coupure (conseil 9, etape 1 : PLAN_conseil9_verdict.md). Test court, sur des instances
deja lancees (host + 1 client, dans la meme carte).

    python _tools/mp_test.py
    python _tools/reconnect_suite.py            # ~6 minutes, ou --only r1

R1  l'invite perd son lien 20 s (emp.cut_link) : il n'est jamais laisse seul sur l'ecran titre (le message de
    reconnexion est affiche), il revient seul en jeu en moins de 60 s, meme personnage, meme case ou voisine, meme
    sac ; l'host n'a qu'un personnage de lui sur la carte et deux joueurs.
R2  la meme chose deux fois de suite.
R3  l'invite quitte de lui-meme : aucune reconnexion, il reste a l'ecran titre ; il rejoint a la main, sans ecran
    de choix du personnage.
R4  case de l'host « Players come back by themselves... » decochee : comme avant, l'ecran titre, aucune reconnexion.
R5  « Cancel » sur le message : les essais s'arretent, il reste a l'ecran titre meme quand le lien est revenu.

Ce que le banc ne joue pas comme un joueur :
- deux fenetres sur un seul PC et un seul compte Steam, reliees par un port local : le chemin du salon Steam
  (rejoindre le meme salon, la cle de connexion, le relais) n'est PAS joue, ni la connexion par adresse ;
- la coupure est la perte de paquets simulee de Steam (emp.cut_link), dans le jeu de l'invite seulement : pas un
  cable debranche, pas un host qui plante. Les deux cotes voient le lien mourir a peu pres en meme temps : le cas
  « l'invite revient alors que l'host tient encore son ancien lien » n'est pas provoque ;
- emp.cut_link allume en Debug le delai de coupure d'un build Release (15 s), eteint sinon ; la suite le remet a
  l'arret en partant ;
- R3 : le pont appelle ce que fait le bouton « Disconnect » du mod (ResetSession puis l'ecran titre), il ne clique
  pas le bouton ; R5 : le bouton du message est clique par le pont, pas a la souris ;
- le texte du message n'est pas lu (on regarde qu'une boite est ouverte pendant que NetReconnect.Active est vrai) ;
- les 3 minutes d'essais puis la phrase finale ne sont pas jouees (trop long) ; pas joue non plus : un invite parti
  seul sur une autre carte, un renvoi par l'host, un refus de version.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from combat_suite import set_option  # noqa: E402
from mp_test import PICK_CHARA, log, ok, shot, state, wait  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, players, scan_logs  # noqa: E402

H, A = 27551, 27552

# dans une seule image du jeu : reconnexion en cours | scene | partie lancee | une boite est ouverte
WATCH = ('var t = HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.NetReconnect"); '
         'return HarmonyLib.AccessTools.Property(t, "Active").GetValue(null) + "|" + EClass.core.scene.mode + "|" + '
         'EClass.core.IsGameStarted + "|" + EClass.ui.layers.OfType<Dialog>().Any();')

# les cartes d'aptitude du sac sont refaites a chaque arrivee dans la partie : pas des objets du joueur
BAG = ('string.Join(",", EClass.pc.things.Where(t => t.id != "ability").Select(t => t.uid + ":" + t.id + ":" + t.Num)'
       '.OrderBy(s => s))')


def watch():
    active, mode, started, box = ev(A, WATCH).split("|")
    return active == "True", mode, started == "True", box == "True"


def snap():
    pc = state(A)["pc"]
    return {"uid": pc["uid"], "pos": (pc["x"], pc["z"]), "bag": ev(A, BAG)}


def rule(port):
    return ev(port, 'ElinTogether.Net.NetSession.Instance.Rules.AllowReconnect.ToString()')


def in_game():
    s = state(A)
    return s.get("sceneMode") == "Zone" and s.get("connected")


def cut(seconds):
    log(ok(emp.call(A, "command", {"cmd": f"emp.cut_link {seconds}"})))
    return time.time()


def rejoin():
    """L'invite rejoint a la main, depuis l'ecran titre ; vrai si aucun ecran de choix ne s'est ouvert."""
    ok(emp.call(A, "command", {"cmd": "emp.connect_udp"}))
    asked = False
    end = time.time() + 180
    while time.time() < end and not in_game():
        asked = asked or watch()[3]
        time.sleep(0.5)
    wait(in_game, "invite de retour en jeu", timeout=10)
    wait(lambda: players(H) == 2, "l'host voit l'invite", timeout=60)
    time.sleep(3)
    return not asked


def stays_out(until, what):
    """Jusqu'a cet instant : aucune reconnexion, ecran titre, pas de lien."""
    tried = left = False
    while time.time() < until:
        active, mode, started, _ = watch()
        tried = tried or active
        left = left or mode != "Title" or started or state(A)["connected"]
        time.sleep(1)
    check(f"{what} : aucun essai de reconnexion", not tried)
    check(f"{what} : il reste a l'ecran titre, sans lien", not left)


def drop():
    """Steam ferme le lien de lui-meme, avec son propre mot (« Connection dropped ») : vu en vraie partie le
    2026-10-09, l'invite etait laisse a l'ecran titre. L'host ferme le lien sans passer par le mod."""
    log(ok(emp.call(H, "command", {"cmd": "emp.drop_links"})))
    return time.time()


def lose_and_return(n, how=None):
    """Coupure de 20 s : l'invite revient seul. `n` : le numero de la coupure, pour les libelles."""
    before = snap()
    t = how() if how else cut(20)
    lost = back = None
    shown = stranded = False
    while time.time() - t < 90:
        active, mode, started, box = watch()
        now = time.time() - t
        if active:
            lost = lost or now
            shown = shown or box
        elif lost is None and mode == "Title":
            stranded = True
        elif lost is not None and mode == "Title" and not started:
            stranded = True
        elif lost is not None and started and in_game():
            back = now
            break
        time.sleep(0.5)
    log(f"coupure {n} : lien perdu a {lost and round(lost)} s, de retour en jeu a {back and round(back)} s")
    if not check(f"coupure {n} : le lien est tombe et la reconnexion a commence ({lost and round(lost)} s apres la coupure)",
                 lost is not None):
        return
    check(f"coupure {n} : le message de reconnexion est affiche", shown)
    check(f"coupure {n} : jamais laisse seul sur l'ecran titre", not stranded)
    if not check(f"coupure {n} : il revient seul en jeu en moins de 60 s ({back and round(back)} s)", back is not None and back < 60):
        return
    check(f"coupure {n} : l'host le revoit (2 joueurs des deux cotes)",
          eventually(lambda: players(H) == 2 and players(A) == 2, timeout=30))
    time.sleep(3)
    after = snap()
    check(f"coupure {n} : meme personnage ({before['uid']} -> {after['uid']})", after["uid"] == before["uid"])
    near = all(abs(a - b) <= 1 for a, b in zip(after["pos"], before["pos"]))
    check(f"coupure {n} : meme case ou voisine ({before['pos']} -> {after['pos']})", near)
    check(f"coupure {n} : meme sac ({len(before['bag'].split(','))} objets)", after["bag"] == before["bag"])
    uid = before["uid"]
    seen = ev(H, f'EClass._map.charas.Count(c => c.uid == {uid}) + "|" + '
                 'EClass._map.charas.Count(c => c != EClass.pc && c.GetBool("remote_chara"))')
    check(f"coupure {n} : l'host n'a qu'un personnage de lui sur la carte (lui|joueurs distants : {seen})", seen == "1|1")
    check(f"coupure {n} : le message est referme", not watch()[3])


def r1(ctx):
    """l'invite perd son lien 20 s : il revient seul, a sa place, sans ecran"""
    lose_and_return(1)


def r6(ctx):
    """le lien ferme par Steam avec un mot qui n'est pas du mod : l'invite revient seul aussi
    Ce que le banc ne joue pas comme un joueur : la fermeture est provoquee chez l'host (CloseConnection avec le texte
    de Steam), pas par une vraie panne du relais Steam entre deux PC"""
    lose_and_return(6, drop)


def r2(ctx):
    """la meme chose deux fois de suite"""
    lose_and_return(2)
    lose_and_return(3)


def r3(ctx):
    """l'invite quitte de lui-meme : aucune reconnexion"""
    uid = state(A)["pc"]["uid"]
    # le delai de coupure d'un build Release, pour que rien ne tienne a son absence
    ok(emp.call(A, "command", {"cmd": "emp.link_timeout 1"}))
    ev(A, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
    time.sleep(3)
    if state(A).get("sceneMode") != "Title":
        emp.call(A, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
    wait(lambda: state(A).get("sceneMode") == "Title" and not state(A)["connected"], "invite a l'ecran titre", timeout=60)
    stays_out(time.time() + 25, "depart voulu")
    check("depart voulu : l'host ne le compte plus", eventually(lambda: players(H) == 1, timeout=30))
    check("il rejoint a la main : aucun ecran de choix du personnage", rejoin())
    check("et retrouve son personnage", state(A)["pc"]["uid"] == uid)


def r4(ctx):
    """case de l'host decochee : comme avant, l'ecran titre"""
    set_option("AutoReconnect", False)
    try:
        if not check("la case decochee arrive dans le jeu de l'invite", eventually(lambda: rule(A) == "False", timeout=10)):
            return
        t = cut(20)
        gone = eventually(lambda: watch()[1] == "Title" and not state(A)["connected"], timeout=60)
        if not check(f"case decochee : apres la coupure l'invite est a l'ecran titre ({round(time.time() - t)} s)", gone):
            return
        # bien apres le retour du lien
        stays_out(t + 50, "case decochee")
    finally:
        set_option("AutoReconnect", True)
        if not in_game():
            rejoin()
    check("la case recochee arrive dans le jeu de l'invite", eventually(lambda: rule(A) == "True", timeout=10))


def r5(ctx):
    """« Cancel » sur le message arrete les essais"""
    t = cut(45)
    try:
        if not check("coupure de 45 s : le message de reconnexion s'affiche",
                     eventually(lambda: watch()[0] and watch()[3], timeout=60)):
            return
        time.sleep(3)
        # le seul bouton de la boite
        clicked = ev(A, PICK_CHARA)
        check(f"clic sur « Cancel » ({clicked}) : les essais s'arretent, le message se ferme",
              eventually(lambda: not watch()[0] and not watch()[3], timeout=5))
        # le lien revient a 45 s : toujours rien
        stays_out(t + 60, "apres « Cancel »")
    finally:
        wait(lambda: time.time() > t + 47, "retour du lien", timeout=60)
        if not in_game():
            rejoin()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {}
    steps = [r1, r2, r3, r4, r5, r6]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    try:
        for step in steps:
            log(f"--- {step.__name__.upper()} : {step.__doc__}")
            try:
                step(ctx)
            except Exception as ex:  # noqa: BLE001
                check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
                for name, port in (("host", H), ("A", A)):
                    try:
                        print(f"    capture {name} : {shot(f'fail-reconnect-{step.__name__}-{name}', port)}")
                    except Exception:  # noqa: BLE001
                        pass
                break
    finally:
        # le banc repart comme il est venu : pas de delai de coupure en Debug, la case de l'host cochee
        for restore in (lambda: emp.call(A, "command", {"cmd": "emp.link_timeout 0"}),
                        lambda: set_option("AutoReconnect", True)):
            try:
                restore()
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
