"""Sauvegarde reguliere de celui qui heberge et partie qui s'ouvre toute seule (conseil 9, etape 2 :
PLAN_conseil9_verdict.md). Test court, sur des instances deja lancees (host + 1 client, dans la meme carte).

    python _tools/mp_test.py
    python _tools/autosave_suite.py            # ~4 minutes, ou --only s1,s3

S1  avec un invite connecte, le monde est sauvegarde sans geste (la date de game.txt change), deux fois de suite.
S3  la duree de chaque sauvegarde est ecrite dans le journal du mod (« Autosave: saved in N ms ») et lue ici.
S4  quand l'invite part, une sauvegarde, une seule.
S2  seul, sans invite : aucune sauvegarde.
S5  l'host retourne a l'ecran titre et recharge son monde : la partie s'ouvre sans la commande emp.add_local,
    l'invite la rejoint.
(Joues dans l'ordre S1, S3, S4, S2, S5 : S2 a besoin que l'invite soit parti, S5 le fait revenir.)

Ce que le banc ne joue pas comme un joueur :
- une fenetre du banc (-empmute) ne sauvegarde pas toute seule tant qu'emp.autosave_every ne l'a pas demande
  (les autres suites comptent sur un monde qui n'est pas sauve dans leur dos) ; un joueur, lui, a le vrai rythme ;
- l'intervalle est raccourci a 5 s par emp.autosave_every (Debug) : les 2 minutes reelles ne sont pas attendues, ni
  le passage a 5 minutes apres une sauvegarde de plus d'une demi-seconde (la duree est seulement lue et affichee) ;
- world_lab est un petit monde : la duree lue ici ne dit rien d'un long monde. C'est sur le vrai monde de
  l'utilisateur qu'il faut la lire (meme ligne du journal) ;
- les reports de 10 s (dialogue ouvert, combat, action en cours, ecran de fin, glisser-deposer) ne sont pas
  provoques : l'host du banc est immobile, sans fenetre ouverte ;
- S5 : dans une fenetre du banc (-empmute) rien ne s'ouvre tout seul, pour que mp_test.py et les suites gardent
  leur emp.add_local ; emp.auto_open 1 le rallume, et la partie s'ouvre alors sur le port local, pas par Steam :
  le salon Steam, l'invitation et « amis seulement » ne sont PAS joues. Le retour a l'ecran titre et le chargement
  passent par le pont (ce que font « retour au titre » et « Continue »), pas par les menus ;
- S4 : l'invite quitte par ce que fait le bouton « Disconnect » du mod, pas par un plantage ni une coupure ;
- pas joues : la case decochee (AutoSave, AutoHost), le mode serveur (-empserver, qui garde sa propre boucle),
  un monde sans base (refus sans fenetre), un monde repris a un autre joueur (echange de personnages puis
  rechargement), le depot.
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import CONTINUE, join_client, log, ok, shot, state, wait  # noqa: E402
from travel_suite import (RESULTS, check, dismiss_dialogs, ev, eventually, players, save_mtime, scan_logs,  # noqa: E402
                          session_log_lines)

H, A = 27551, 27552

# ce qui repousse une sauvegarde (EmpAutoHost.CanSave), pour lire un echec
WHY = ('"scene " + EClass.scene.mode + ", sans but " + EClass.pc.HasNoGoal + ", fenetre " + EClass.ui.IsActive + '
       '", mode aventure " + ActionMode.AdvOrRegion.IsActive + ", poursuivi " + '
       'EClass._map.charas.Exists(c => c.enemy == EClass.pc && !c.isDead)')


def every(seconds):
    log(ok(emp.call(H, "command", {"cmd": f"emp.autosave_every {seconds}"})))


def saves(t0):
    """Les sauvegardes automatiques ecrites dans le journal du mod depuis t0 : (resultat, millisecondes)."""
    out = []
    for line in session_log_lines(t0):
        d = json.loads(line)
        if d.get("@mt", "").startswith("Autosave: {Result}"):
            out.append((d.get("Result"), d.get("Ms")))
    return out


def saved_after(before, timeout=40):
    good = eventually(lambda: save_mtime() > before, timeout=timeout)
    if not good:
        log("pas de sauvegarde : " + ev(H, WHY))
    return good


def s1(ctx):
    """avec un invite connecte, le monde est sauvegarde sans geste"""
    dismiss_dialogs(H)
    if not check("depart : deux joueurs dans la partie", players(H) == 2):
        return
    before = save_mtime()
    every(5)
    if not check("invite connecte : game.txt est reecrit sans geste (intervalle de 5 s)", saved_after(before)):
        return
    again = save_mtime()
    check("et encore au tour suivant", saved_after(again, timeout=30))
    check("aucune fenetre ouverte chez l'host par la sauvegarde", ev(H, 'EClass.ui.IsActive.ToString()') == "False")


def s3(ctx):
    """la duree mesuree est ecrite dans le journal et lue ici"""
    found = []
    eventually(lambda: found.extend(saves(ctx["t0"])) or found, timeout=15)
    if not check(f"journal du mod : {len(found)} ligne(s) « Autosave »", found):
        return
    result, ms = found[-1]
    check(f"la derniere dit « saved » et sa duree : {ms} ms", result == "saved" and isinstance(ms, int))
    worst = max(m for _, m in found if isinstance(m, int))
    log(f"durees lues : {[m for _, m in found]} ms ; la plus longue {worst} ms "
        f"({'plus' if worst > 500 else 'moins'} d'une demi-seconde : intervalle reel de {5 if worst > 500 else 2} minutes)")


def s4(ctx):
    """quand l'invite part, une sauvegarde"""
    # plus de sauvegarde reguliere d'ici la : celle qui vient est celle du depart
    every(600)
    time.sleep(2)
    before, count = save_mtime(), len(saves(ctx["t0"]))
    ev(A, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
    time.sleep(3)
    if state(A).get("sceneMode") != "Title":
        emp.call(A, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
    if not check("l'invite est parti : l'host est seul", eventually(lambda: players(H) == 1, timeout=60)):
        return
    check("depart de l'invite : game.txt est reecrit", saved_after(before))
    time.sleep(15)
    after = len(saves(ctx["t0"]))
    check(f"une sauvegarde, une seule ({after - count} ligne(s) de plus dans le journal)", after - count == 1)


def s2(ctx):
    """seul, sans invite : aucune sauvegarde"""
    if not check("depart : l'host est seul, partie ouverte", players(H) == 1 and state(H)["role"] == "Host"):
        return
    every(5)
    time.sleep(3)
    before, count = save_mtime(), len(saves(ctx["t0"]))
    time.sleep(25)
    check("25 s seul, intervalle de 5 s : game.txt n'a pas bouge", save_mtime() == before)
    check("et rien de plus dans le journal", len(saves(ctx["t0"])) == count)


def s5(ctx):
    """un monde charge s'ouvre sans la commande du banc"""
    log(ok(emp.call(H, "command", {"cmd": "emp.auto_open 1"})))
    # ce que fait « retour au titre » quand on repond oui : sauvegarde, puis l'ecran titre
    ev(H, 'EClass.game.Save(true, true); EClass.scene.Init(Scene.Mode.Title); "ok"')
    wait(lambda: state(H).get("sceneMode") == "Title", "host a l'ecran titre", timeout=60)
    time.sleep(3)
    if not check("a l'ecran titre la partie est fermee", state(H)["role"] == "None"):
        return
    # comme mp_test.py charge le monde ; a l'ecran titre le mod peut encore refuser ce chemin (GameSaveLoad)
    asked = ev(H, 'Game.TryLoad("world_lab", false, () => Game.Load("world_lab", false)).ToString()')
    if asked != "True":
        log("Game.TryLoad refuse a l'ecran titre : chargement direct par Game.Load")
        ev(H, 'Game.Load("world_lab", false); "ok"')
    wait(lambda: state(H)["gameStarted"] and state(H)["sceneMode"] == "Zone", "chargement du host", timeout=600)
    if emp.call(H, "eval", {"code": CONTINUE}, timeout=180).get("result") == "continued":
        log("host : question \"mods manquants\" passee (continuer)")
    if not check("le monde charge, la partie s'ouvre toute seule (aucun emp.add_local)",
                 eventually(lambda: state(H)["role"] == "Host", timeout=60)):
        return
    check("une seule partie, un seul joueur : l'host", players(H) == 1)
    join_client(H, A, "invite")
    check("l'invite rejoint la partie ouverte toute seule (2 joueurs des deux cotes)",
          eventually(lambda: players(H) == 2 and players(A) == 2, timeout=60))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"t0": t0}
    steps = [s1, s3, s4, s2, s5]
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
                        print(f"    capture {name} : {shot(f'fail-autosave-{step.__name__}-{name}', port)}")
                    except Exception:  # noqa: BLE001
                        pass
                break
    finally:
        # le banc repart comme il est venu : l'intervalle reel, rien qui s'ouvre tout seul
        for cmd in ("emp.autosave_every 0", "emp.auto_open 0"):
            try:
                emp.call(H, "command", {"cmd": cmd})
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
