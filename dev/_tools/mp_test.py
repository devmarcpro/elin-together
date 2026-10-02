"""Scenario de test multijoueur local : host (jeu normal) + client (_lab/Elin2) sur le meme PC.

    python _tools/mp_test.py            # restaure world_lab, lance les 2 instances, host + client, captures
    python _tools/mp_test.py --reuse    # reutilise les instances deja lancees (pas de restauration)

Prerequis : build DEBUG (.\\build.ps1), Dev.Listener = true dans les deux configs, _lab/Elin2 cree
(make_lab.py), steam_appid.txt dans le dossier du jeu, Steam lance.
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from gamepath import GAME  # noqa: E402

# ROOT : le dossier dev/ du depot (outils, copies du jeu, captures)
ROOT = Path(__file__).resolve().parent.parent
GAME_EXE = GAME / "Elin.exe"
LAB_EXE = ROOT / "_lab" / "Elin2" / "Elin.exe"
LAB3_EXE = ROOT / "_lab" / "Elin3" / "Elin.exe"
LAB4_EXE = ROOT / "_lab" / "Elin4" / "Elin.exe"
# instances clientes : lanceur, fichier Player.log (identites de test 2, 3 et 4, voir make_lab.py)
CLIENTS = [(LAB_EXE, "elin2-player.log"), (LAB3_EXE, "elin3-player.log"), (LAB4_EXE, "elin4-player.log")]
SAVES = Path.home() / "AppData" / "LocalLow" / "Lafrontier" / "Elin" / "Save"
PRISTINE = ROOT / "_lab" / "saves" / "world_lab.pristine"
SHOTS = ROOT / "_shots"
# -empmute : instance de test muette des le demarrage (EmpDebugListener)
WINDOW = ["-screen-fullscreen", "0", "-screen-width", "1280", "-screen-height", "720", "-empmute"]
# clique "Creer" sur l'ecran de creation de personnage (meme listener que le vrai bouton)
EMBARK = ('var layer = EClass.ui.GetLayer<LayerEditBio>(); if (layer == null) return "no layer"; '
          'layer.GetComponentInChildren<Content>().transform.Find("ButtonEmbark")'
          '.GetComponentInChildren<UIButton>().onClick.Invoke(); "embark clicked"')


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def wait(cond, what, timeout=180, every=2.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            v = cond()
            if v:
                return v
        except OSError:
            pass
        time.sleep(every)
    raise TimeoutError(f"timeout : {what}")


def bridge_for(pid):
    port = next((h["port"] for h in emp.live_ports() if h["pid"] == pid), None)
    if port:
        mute(port)
    return port


def mute(port):
    """Coupe le son de l'instance de test (sans toucher aux reglages du jeu)."""
    try:
        emp.call(port, "eval", {"code": 'UnityEngine.AudioListener.volume = 0f; "ok"'}, timeout=180)
    except OSError:
        pass


def ok(r):
    if not r.get("ok"):
        raise RuntimeError(r.get("error"))
    return r.get("result")


def state(port):
    return ok(emp.call(port, "state"))


def summary(name, port):
    s = state(port)
    pc = s.get("pc") or {}
    zone = s.get("zone") or {}
    return (f"{name}: role={s['role']} connected={s['connected']} scene={s['sceneMode']} "
            f"zone={zone.get('name')} pc=({pc.get('x')},{pc.get('z')}) players={len(s.get('players', []))}")


def shot(name, port):
    r = ok(emp.call(port, "screenshot", {"scale": 0.5}))
    dst = SHOTS / f"mp-{name}.png"
    shutil.copy(r["path"], dst)
    return dst


PICK_CHARA = ('var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return "no dialog"; '
              'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(true).FirstOrDefault(x => x.name.StartsWith("ButtonGeneral(Clone)")); '
              'if (b == null) return "no button"; b.onClick.Invoke(); return "picked";')


def join_client(host_port, client_port, name, attempts=3):
    """Connecte un client a l'ecran titre (avec nouvel essai : un client tout juste lance peut rater
    son premier handshake, voir MODLOG) et valide la creation de personnage si besoin."""
    for attempt in range(attempts):
        try:
            _join_client(client_port, name)
            return
        except TimeoutError:
            if attempt == attempts - 1:
                raise
            log(f"{name} : connexion ratee, nouvel essai")
            wait(lambda: state(client_port).get("sceneMode") == "Title" and not state(client_port)["connected"],
                 f"{name} revenu a l'ecran titre", timeout=240)


def _join_client(client_port, name):
    if not state(client_port)["connected"]:
        try:
            ok(emp.call(client_port, "command", {"cmd": "emp.connect_udp"}, timeout=180))
            log(f"{name} : connexion demandee")
        except OSError:
            # le jeu etait occupe (chargement) : la demande est peut-etre partie, on attend la suite
            log(f"{name} : demande de connexion sans reponse, on attend")

    # nouveau joueur : l'hote demande une creation de personnage (LayerEditBio), on valide tel quel
    def in_zone_or_embark():
        if state(client_port)["sceneMode"] == "Zone":
            return True
        # ecran "avec quel personnage jouer ?" : le premier de la liste
        emp.call(client_port, "eval", {"code": PICK_CHARA}, timeout=180)
        r = emp.call(client_port, "eval", {"code": EMBARK}, timeout=180)
        if r.get("result") == "embark clicked":
            log(f"{name} : creation du personnage validee")
        return False

    wait(in_zone_or_embark, f"{name} en jeu", timeout=300, every=3.0)
    time.sleep(3)
    log(f"{name} en jeu")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--clients", type=int, default=1, choices=[0, 1, 2, 3])
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    SHOTS.mkdir(exist_ok=True)

    if a.reuse:
        live = emp.live_ports()
        host_port = next(h["port"] for h in live if h["role"] != "Client" and h["gameStarted"])
        client_ports = sorted(h["port"] for h in live if h["port"] != host_port)[:a.clients]
    else:
        running = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Elin.exe"], capture_output=True, text=True).stdout
        if "Elin.exe" in running:
            sys.exit("Elin tourne deja : ferme-le ou utilise --reuse")

        shutil.rmtree(SAVES / "world_lab", ignore_errors=True)
        shutil.copytree(PRISTINE, SAVES / "world_lab")
        log("world_lab restaure depuis la copie vierge")

        host = subprocess.Popen([str(GAME_EXE), *WINDOW], cwd=GAME_EXE.parent)
        log(f"host lance (pid {host.pid})")
        host_port = wait(lambda: bridge_for(host.pid), "pont du host", timeout=420)

        # une fenetre a la fois : deux jeux qui demarrent ensemble mettent 8 minutes et l'host peut rester fige
        ok(emp.call(host_port, "eval", {"code": 'Game.TryLoad("world_lab", false, () => Game.Load("world_lab", false)).ToString()'}, timeout=180))
        wait(lambda: state(host_port)["gameStarted"] and state(host_port)["sceneMode"] == "Zone", "chargement du host", timeout=600)
        log("host : world_lab charge")

        client_ports = []
        for exe, logname in CLIENTS[:a.clients]:
            client = subprocess.Popen([str(exe), *WINDOW, "-logFile", str(SHOTS / logname)], cwd=exe.parent)
            log(f"client {exe.parent.name} lance (pid {client.pid})")
            port = wait(lambda: bridge_for(client.pid), f"pont de {exe.parent.name}", timeout=600)
            wait(lambda: state(port).get("sceneMode") == "Title", f"ecran titre de {exe.parent.name}", timeout=300)
            time.sleep(10)
            client_ports.append(port)

    log(f"ports : host={host_port} clients={client_ports}")

    # juste apres le chargement, l'host peut ne pas repondre pendant une minute ou deux
    wait(lambda: bool(state(host_port)), "host qui repond apres le chargement", timeout=300, every=5.0)
    if state(host_port)["role"] != "Host":
        ok(emp.call(host_port, "command", {"cmd": "emp.add_local"}))
        wait(lambda: state(host_port)["role"] == "Host", "demarrage du serveur")
        log("host : serveur local demarre")

    try:
        for i, port in enumerate(client_ports):
            join_client(host_port, port, f"client {i + 1}")
    finally:
        print(summary("HOST  ", host_port))
        for i, port in enumerate(client_ports):
            print(summary(f"CLIENT{i + 1}", port))
        for name, port in [("host", host_port)] + [("client" if i == 0 else f"client{i + 1}", p) for i, p in enumerate(client_ports)]:
            try:
                print(f"capture {name} : {shot(name, port)}")
            except Exception as ex:  # noqa: BLE001
                print(f"capture {name} impossible : {ex}")


if __name__ == "__main__":
    main()
