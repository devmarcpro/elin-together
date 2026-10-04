"""Un serveur comme un serveur Minecraft : un Elin que personne ne joue, lance avec -empserver, rejoint par adresse.
Lance lui-meme ses deux fenetres (le serveur, puis un joueur). ~6 minutes.

    python _tools/server_suite.py

Demande de l'utilisateur le 2026-10-04 : "heberger un serveur comme un serveur minecraft" sur son PC de dev.

V1  lance avec -empserver world_lab, le jeu charge le monde et ouvre la partie tout seul
V2  un joueur le rejoint par son adresse (le champ "Join by address"), cree son personnage et joue
V3  il passe du temps sur la carte du serveur : la date du monde avance, alors que personne ne joue le serveur
V4  il part seul a Vernis et y passe du temps : la date du serveur avance avec la sienne
V5  il quitte et revient par l'adresse : il retrouve son personnage
"""
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import (EMBARK, GAME_EXE, LAB_EXE, PICK_CHARA, PRISTINE, SAVES, SHOTS, WINDOW, bridge_for, log, shot,  # noqa: E402
                     state, wait)
from travel_suite import HOME, RESULTS, VERNIS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually, move, scan_logs  # noqa: E402
import move_suite  # noqa: E402

ADDRESS = "127.0.0.1:55556"
# (les classes du mod sont internes : par reflexion, comme les autres suites)
JOIN = ('var s = ElinTogether.Net.NetSession.Instance; var t = HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetClient"); '
        'var c = HarmonyLib.AccessTools.Method(s.GetType(), "InitializeComponent").MakeGenericMethod(t).Invoke(s, null); '
        f'HarmonyLib.AccessTools.Method(t, "ConnectAddress").Invoke(c, new object[] {{ "{ADDRESS}" }}); "ok"')
DATE = 'EClass.world.date.GetRaw().ToString()'


def date(port):
    return int(ev(port, DATE))


def join(port):
    """Ce que fait le bouton "Join by address" une fois l'adresse donnee, puis l'ecran de choix ou de creation."""
    ev(port, JOIN)

    def playing():
        if state(port)["sceneMode"] == "Zone" and state(port)["connected"]:
            return True
        emp.call(port, "eval", {"code": PICK_CHARA}, timeout=180)
        emp.call(port, "eval", {"code": EMBARK}, timeout=180)
        return False

    wait(playing, "le joueur en jeu", timeout=300, every=3.0)
    time.sleep(4)
    dismiss_dialogs(port)
    return state(port)["pc"]["uid"]


def spend(port, minutes, timeout=150):
    start, end = date(port), time.time() + timeout
    while date(port) - start < minutes and time.time() < end:
        move_suite.walk(port)
        move_suite.back(port)
    return date(port) - start


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    SHOTS.mkdir(exist_ok=True)
    procs = []
    try:
        if emp.live_ports():
            raise RuntimeError("Elin tourne deja : ferme-le")
        shutil.rmtree(SAVES / "world_lab", ignore_errors=True)
        shutil.copytree(PRISTINE, SAVES / "world_lab")

        log("--- V1")
        server = subprocess.Popen([str(GAME_EXE), *WINDOW, *os.environ.get("SERVER_ARGS", "").split(), "-empserver", "world_lab"], cwd=GAME_EXE.parent)
        procs.append(server)
        log(f"serveur lance (pid {server.pid})")
        S = wait(lambda: bridge_for(server.pid), "pont du serveur", timeout=600)
        wait(lambda: state(S).get("role") == "Host", "le serveur charge le monde et ouvre la partie", timeout=600, every=5.0)
        s = state(S)
        check(f"lance avec -empserver, le jeu charge le monde et ouvre la partie tout seul ({(s.get('zone') or {}).get('name')})",
              s["role"] == "Host" and s["sceneMode"] == "Zone")

        log("--- V2")
        player = subprocess.Popen([str(LAB_EXE), *WINDOW, "-logFile", str(SHOTS / "elin2-player.log")], cwd=LAB_EXE.parent)
        procs.append(player)
        log(f"joueur lance (pid {player.pid})")
        P = wait(lambda: bridge_for(player.pid), "pont du joueur", timeout=600)
        wait(lambda: state(P).get("sceneMode") == "Title", "ecran titre du joueur", timeout=300)
        time.sleep(10)
        first = join(P)
        check(f"un joueur rejoint le serveur par son adresse ({ADDRESS}) et joue",
              eventually(lambda: len(state(S).get("players", [])) == 2, timeout=30) and first not in (0, state(S)["pc"]["uid"]))
        log(f"joueurs vus du serveur : {[(p['index'], p['charaUid']) for p in state(S)['players']]}")

        log("--- V3")
        d0 = date(S)
        spent = spend(P, 15)
        log(f"le joueur a passe {spent} min sur la carte du serveur ; date du serveur +{date(S) - d0}")
        check(f"il passe du temps sur la carte du serveur : la date du monde avance (+{date(S) - d0} min), personne ne joue le serveur",
              spent >= 15 and date(S) - d0 >= 13)

        log("--- V4")
        move(P, VERNIS)
        wait(client_settled(P, VERNIS, True), "le joueur seul a Vernis", timeout=180)
        time.sleep(3)
        dismiss_dialogs(P)
        d0 = date(S)
        spent = spend(P, 15)
        log(f"le joueur a passe {spent} min a Vernis ; date du serveur +{date(S) - d0}")
        check(f"il part seul a Vernis : la date du serveur avance avec la sienne (+{date(S) - d0} min)",
              spent >= 15 and eventually(lambda: abs(date(S) - date(P)) <= 2, timeout=10))
        move(P, HOME)
        both_joined(S, P, HOME)
        time.sleep(4)
        dismiss_dialogs(P)

        log("--- V5")
        ev(P, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
        time.sleep(3)
        if state(P).get("sceneMode") != "Title":
            emp.call(P, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
        wait(lambda: state(P).get("sceneMode") == "Title" and not state(P)["connected"], "le joueur a l'ecran titre", timeout=60)
        wait(lambda: len(state(S).get("players", [])) == 1, "le serveur ne voit plus le joueur", timeout=60)
        time.sleep(3)
        check("il quitte et revient par l'adresse : il retrouve son personnage", join(P) == first)
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for h in emp.live_ports():
            try:
                print(f"    capture : {shot('fail-server-' + str(h['port']), h['port'])}")
            except Exception:  # noqa: BLE001
                pass
    finally:
        for p in procs:
            p.kill()

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
