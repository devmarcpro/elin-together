"""Choix du personnage a la connexion. Test court, sur des instances deja lancees (host + 1 client).

    python _tools/mp_test.py
    python _tools/chara_suite.py      # ~3 minutes, finit avec le client en jeu sur son premier personnage

C1  le client se deconnecte et revient : l'ecran propose son personnage, il le reprend (meme personnage)
C2  il revient et choisit "nouveau personnage" : creation (avec un objet detruit sous le pointeur, voir
    CharaMakerHoverPatch), un autre personnage, l'host en garde deux
C3  il revient : l'ecran propose les deux, il reprend le premier, avec sa renommee
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import EMBARK, log, ok, shot, state, wait  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

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
        leave()
        choices = connect()
        log(f"choix proposes : {choices}")
        check("l'ecran propose son personnage et \"nouveau personnage\"", len(choices) == 2 and choices[-1] == "A new character")
        click(0)
        check("il reprend le meme personnage", in_game() == first)

        log("--- C2")
        leave()
        choices = connect()
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
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {ex}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-chara-{name}', port)}")
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
