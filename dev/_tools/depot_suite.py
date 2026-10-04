"""Le depot de sauvegarde : un dossier garde le monde, le premier arrive le prend et l'heberge.
Test court (host + 1 client a la Prairie). Finit avec les deux jeux dans le monde du depot.

    python _tools/mp_test.py
    python _tools/depot_suite.py      # ~4 minutes

Idee de l'utilisateur (2026-10-03) : un serveur qui est juste la sauvegarde. Premiere forme : un dossier partage.

D1  l'host depose sa sauvegarde dans le depot
D2  l'autre joueur, a l'ecran titre, prend le monde du depot : il le charge, le depot dit que c'est lui qui heberge
D3  pendant ce temps le premier ne peut pas le prendre (on lui dit qui heberge)
D4  celui qui heberge change quelque chose et sauvegarde : le monde du depot change
D5  il quitte : le depot est libre ; le premier joueur le prend a son tour et retrouve le changement (sa copie
    locale a ete effacee avant : le monde vient bien du depot)
D6  il ouvre la session, l'autre le rejoint : les deux jouent dans le monde du depot
"""
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from chara_suite import leave  # noqa: E402
from mp_test import CONTINUE, SAVES, SHOTS, join_client, log, ok, shot, state, wait  # noqa: E402
from travel_suite import RESULTS, check, dismiss_dialogs, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
DEPOT = SHOTS / "depot"
LOCAL = SAVES / "world_depot"
DEP = 'HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.SaveDepot")'
SET = ('var e = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Client"), "DepotPath").GetValue(null); '
       'HarmonyLib.AccessTools.Property(e.GetType(), "Value").SetValue(e, @"%s"); "ok"')
CALL = 'HarmonyLib.AccessTools.Method(' + DEP + ', "%s").Invoke(null, null); "ok"'
DIALOG = 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); return d == null ? "" : d.textDetail.text;'
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


def holder():
    f = DEPOT / "host.txt"
    return f.read_text(encoding="utf-8").splitlines() if f.exists() else []


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        shutil.rmtree(DEPOT, ignore_errors=True)
        shutil.rmtree(LOCAL, ignore_errors=True)
        DEPOT.mkdir(parents=True)
        for port in (H, A):
            dismiss_dialogs(port)
            ev(port, SET % str(DEPOT))

        log("--- D1")
        ev(H, CALL % "Put")
        time.sleep(3)
        log(f"l'host : {ev(H, DIALOG)}")
        dismiss_dialogs(H)
        check("l'host depose sa sauvegarde : le depot contient un monde", (DEPOT / "world" / "game.txt").exists())

        log("--- D2")
        leave()
        take(A)
        wait(loaded(A), "l'autre joueur charge le monde du depot", timeout=180, every=3.0)
        dismiss_dialogs(A)
        check("l'autre joueur prend le monde du depot et le charge", game_id(A) == "world_depot")
        check(f"le depot dit qui heberge ({holder()[1:]})", eventually(lambda: len(holder()) == 2, timeout=10))

        log("--- D3")
        to_title(H)
        take(H)
        said = ev(H, DIALOG)
        log(f"le premier joueur : {said}")
        check("pendant ce temps le premier joueur ne peut pas le prendre : on lui dit qui heberge",
              "is hosting" in said and state(H).get("sceneMode") == "Title")
        dismiss_dialogs(H)

        log("--- D4")
        before = int(ev(A, BUCKETS))
        stamp = (DEPOT / "world" / "game.txt").stat().st_mtime
        ev(A, 'EClass.pc.AddThing(ThingGen.Create("bucket")); EClass.game.Save(false, true).ToString()')
        check("celui qui heberge sauvegarde : le monde du depot change",
              eventually(lambda: (DEPOT / "world" / "game.txt").stat().st_mtime > stamp, timeout=20))
        check("pas de reste de copie dans le depot", not (DEPOT / "world.new").exists() and not (DEPOT / "world.old").exists())

        log("--- D5")
        to_title(A)
        check("il quitte : le depot est libre", eventually(lambda: not holder(), timeout=10))
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
