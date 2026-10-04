"""Le depot de sauvegarde : un dossier garde le monde, le premier arrive le prend et l'heberge.
Test court (host + 1 client a la Prairie). Finit avec les deux jeux dans le monde du depot.

    python _tools/mp_test.py
    python _tools/depot_suite.py      # ~4 minutes

Idee de l'utilisateur (2026-10-03) : un serveur qui est juste la sauvegarde. Premiere forme : un dossier partage.

D1  l'host depose sa sauvegarde dans le depot
D2  l'autre joueur, a l'ecran titre, prend le monde du depot (avec le logiciel : par "Join by address", sans
    avoir regle de depot) : il le charge, le depot dit que c'est lui qui heberge
D3  pendant ce temps le premier ne peut pas le prendre (on lui dit qui heberge)
    (avec le logiciel : un mauvais mot de passe est dit comme tel)
D4  celui qui heberge change quelque chose et sauvegarde : le monde du depot change
D5  il quitte : le depot est libre ; le premier joueur le prend a son tour et retrouve le changement (sa copie
    locale a ete effacee avant : le monde vient bien du depot)
D6  il ouvre la session, l'autre le rejoint : les deux jouent dans le monde du depot

    DEPOT_SERVER=1 python _tools/depot_suite.py
Le meme scenario avec Elin Together Server a la place du dossier : l'application (aucun jeu, aucun dossier partage)
garde le monde et le verrou, les jeux lui parlent par son adresse.
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
from chara_suite import leave  # noqa: E402
from mp_test import CONTINUE, PRISTINE, SAVES, SHOTS, join_client, log, ok, shot, state, wait  # noqa: E402
from travel_suite import RESULTS, check, dismiss_dialogs, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
DEPOT = SHOTS / "depot"
REMOTE = bool(os.environ.get("DEPOT_SERVER"))
SERVER_EXE = Path(__file__).resolve().parent.parent / "_release" / "template" / "ElinTogetherServer.exe"
# pas le port habituel (55557) : un vrai serveur de l'utilisateur peut tourner sur cette machine
PORT = "55558"
ADDRESS = "127.0.0.1:" + PORT
WORLD = DEPOT / "world.zip" if REMOTE else DEPOT / "world" / "game.txt"
HELD = ('var who = HarmonyLib.AccessTools.Method(' + 'HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.SaveDepot")' +
        ', "HeldBy").Invoke(null, null); return who == null ? "" : who.ToString();')
LOCAL = SAVES / "world_depot"
DEP = 'HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.SaveDepot")'
SET = ('var e = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Client"), "DepotPath").GetValue(null); '
       'HarmonyLib.AccessTools.Property(e.GetType(), "Value").SetValue(e, @"%s"); "ok"')
PASSWORD = SET.replace("DepotPath", "DepotPassword")
CALL = 'HarmonyLib.AccessTools.Method(' + DEP + ', "%s").Invoke(null, null); "ok"'
DIALOG = 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); return d == null ? "" : d.textDetail.text;'
JOIN = ('HarmonyLib.AccessTools.Method(HarmonyLib.AccessTools.TypeByName("ElinTogether.Components.TabLobbyBrowser"), '
        '"JoinAddress").Invoke(null, new object[] { "%s" }); "ok"')
BUCKETS = 'EClass.pc.things.Flatten().Count(t => t.id == "bucket").ToString()'


def game_id(port):
    return ev(port, '(EClass.core.IsGameStarted ? Game.id : "")')


def to_title(port):
    emp.call(port, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
    wait(lambda: state(port).get("sceneMode") == "Title", "ecran titre", timeout=60)
    time.sleep(3)


def take(port):
    emp.call(port, "eval", {"code": CALL % "Take"}, timeout=180)
    time.sleep(2)


def loaded(port):
    def cond():
        emp.call(port, "eval", {"code": CONTINUE}, timeout=180)
        return state(port).get("sceneMode") == "Zone" and game_id(port) == "world_depot"
    return cond


def holder(asker):
    """Qui heberge le monde, vu du jeu `asker` ("" si personne, ou si c'est lui)."""
    return ev(asker, HELD)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    server = None
    try:
        shutil.rmtree(DEPOT, ignore_errors=True)
        shutil.rmtree(LOCAL, ignore_errors=True)
        DEPOT.mkdir(parents=True)
        if REMOTE:
            # la sauvegarde est choisie dans le logiciel (ici par sa ligne de commande, comme le bouton "Mettre
            # cette sauvegarde sur le serveur") : aucun joueur n'a a la deposer
            server = subprocess.Popen([str(SERVER_EXE), "--depot", str(DEPOT), "--port", PORT, "--import", str(PRISTINE)])
            log(f"Elin Together Server lance (pid {server.pid}), depot a {ADDRESS}")
            time.sleep(3)
        for port in (H, A):
            dismiss_dialogs(port)
            # avec le logiciel, l'autre joueur ne regle rien : il tape l'adresse dans "Join by address"
            ev(port, SET % ("" if REMOTE and port == A else ADDRESS if REMOTE else str(DEPOT)))

        log("--- D1")
        if REMOTE:
            check("la sauvegarde choisie dans le logiciel est le monde du serveur", eventually(WORLD.exists, timeout=15))
        else:
            ev(H, CALL % "Put")
            time.sleep(3)
            log(f"l'host : {ev(H, DIALOG)}")
            dismiss_dialogs(H)
            check("l'host depose sa sauvegarde : le depot contient un monde", WORLD.exists())

        log("--- D2")
        leave()
        if REMOTE:
            emp.call(A, "eval", {"code": JOIN % ADDRESS}, timeout=180)
            time.sleep(2)
        else:
            take(A)
        wait(loaded(A), "l'autre joueur charge le monde du depot", timeout=180, every=3.0)
        dismiss_dialogs(A)
        check("l'autre joueur prend le monde du depot et le charge", game_id(A) == "world_depot")
        check(f"le depot dit qui heberge ({holder(H)})", eventually(lambda: holder(H) != "", timeout=10))

        log("--- D3")
        to_title(H)
        take(H)
        said = ev(H, DIALOG)
        log(f"le premier joueur : {said}")
        check("pendant ce temps le premier joueur ne peut pas le prendre : on lui dit qui heberge",
              "is hosting" in said and state(H).get("sceneMode") == "Title")
        dismiss_dialogs(H)
        if REMOTE:
            # un mauvais mot de passe : on le dit, au lieu de "password heberge le monde"
            ev(H, PASSWORD % "faux")
            check(f"mauvais mot de passe : personne ne s'appelle \"password\" ({holder(H)!r})", holder(H) == "")
            take(H)
            said = ev(H, DIALOG)
            log(f"le premier joueur : {said}")
            check("mauvais mot de passe : le jeu dit que le serveur refuse le mot de passe", "refused" in said.lower())
            dismiss_dialogs(H)
            ev(H, PASSWORD % "")

        log("--- D4")
        before = int(ev(A, BUCKETS))
        stamp = WORLD.stat().st_mtime
        ev(A, 'EClass.pc.AddThing(ThingGen.Create("bucket")); EClass.game.Save(false, true).ToString()')
        check("celui qui heberge sauvegarde : le monde du depot change",
              eventually(lambda: WORLD.stat().st_mtime > stamp, timeout=20))
        check("pas de reste de copie dans le depot", not any(DEPOT.glob("*.new")) and not (DEPOT / "world.old").exists())

        log("--- D5")
        to_title(A)
        check("il quitte : le depot est libre", eventually(lambda: holder(H) == "", timeout=10))
        shutil.rmtree(LOCAL, ignore_errors=True)
        take(H)
        wait(loaded(H), "le premier joueur charge le monde du depot", timeout=180, every=3.0)
        dismiss_dialogs(H)
        check(f"le premier joueur le prend a son tour et retrouve le changement ({ev(H, BUCKETS)} seaux, {before} avant)",
              int(ev(H, BUCKETS)) == before + 1)

        log("--- D6")
        ok(emp.call(H, "command", {"cmd": "emp.add_local"}))
        wait(lambda: state(H)["role"] == "Host", "demarrage du serveur")
        join_client(H, A, "client")
        check("il ouvre la session, l'autre le rejoint : les deux jouent dans le monde du depot",
              eventually(lambda: len(state(H).get("players", [])) == 2 and state(A)["connected"], timeout=30))
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-depot-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass
    finally:
        if server is not None:
            server.kill()
        for port in (H, A):
            try:
                ev(port, SET % "")
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
