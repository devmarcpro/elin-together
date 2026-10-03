"""Deplacements de l'invite : aussi reguliers que ceux de l'host. Test court (host + 1 client a la Prairie).

    python _tools/mp_test.py
    python _tools/move_suite.py         # ~1 minute

Signale par l'utilisateur le 2026-10-03 (vraie partie, lui invite) : "les deplacements des invites ne sont pas
aussi fluides que ceux de l'host". Cause lue dans le code : chez un client, le moment de chaque pas suivait le
temps de jeu de l'host tel que le reseau l'apportait (par paquets), alors que l'animation suit l'horloge locale.

V1  l'invite marche sur la carte de l'host : ses pas sont reguliers (reference)
V2  le jeu de l'host tourne mal (5 images par seconde, comme un PC qui rame ou un reseau qui livre par a-coups) :
    les pas de l'invite gardent le meme rythme et la meme regularite
V3  option decochee : le rythme de l'invite depend de nouveau de l'host (l'ancien comportement)
"""
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from combat_suite import set_option  # noqa: E402
from mp_test import log, shot  # noqa: E402
from travel_suite import RESULTS, check, dismiss_dialogs, ev, scan_logs  # noqa: E402

H, A = 27551, 27552
CELLS = 14

# la case libre la plus loin vers l'est en ligne droite, a CELLS cases au plus : un trajet sans detour
TARGET = ('var p = EClass.pc.pos.Copy(); var best = p.Copy(); '
          f'for (var i = 1; i <= {CELLS}; i++) {{ var q = new Point(p.x + i, p.z); '
          'if (!q.IsInBounds || q.IsBlocked || q.HasChara) break; best = q; } '
          'return best.x + "," + best.z + "," + (best.x - p.x);')
POS = 'EClass.pc.pos.x + "," + EClass.pc.pos.z + "," + EClass.pc.HasNoGoal'


def walk(port):
    """Fait marcher le joueur en ligne droite et releve l'instant de chaque pas. Renvoie les intervalles (s)."""
    x, z, n = ev(port, TARGET).split(",")
    if int(n) < 8:
        # pas assez de place vers l'est : on repart du point d'arrivee vers l'ouest
        ev(port, 'var p = EClass.pc.pos.Copy(); p.x -= 16; EClass.pc.Teleport(p.GetNearestPoint(false, false) ?? EClass.pc.pos, true, true); "ok"')
        time.sleep(2)
        x, z, n = ev(port, TARGET).split(",")
    ev(port, f'EClass.pc.SetAIImmediate(new AI_Goto(new Point({x}, {z}), 0)); "ok"')
    steps, last, end = [], None, time.time() + 25
    while time.time() < end:
        px, pz, idle = ev(port, POS).split(",")
        now = time.perf_counter()
        if (px, pz) != last:
            steps.append(now)
            last = (px, pz)
        if idle == "True" and len(steps) > 3:
            break
    # le premier releve n'est pas un pas, le premier pas part tout de suite : on garde les intervalles suivants
    gaps = [b - a for a, b in zip(steps[2:], steps[3:])]
    return gaps


def describe(gaps):
    if len(gaps) < 4:
        return None
    mean = statistics.mean(gaps)
    return {"n": len(gaps), "mean": mean, "cv": statistics.pstdev(gaps) / mean, "max": max(gaps) / statistics.median(gaps)}


def show(d):
    return "trop peu de pas" if d is None else f"{d['n']} pas, {d['mean'] * 1000:.0f} ms par pas, ecart {d['cv'] * 100:.0f} %, pire {d['max']:.1f}x"


def back(port):
    ev(port, 'var p = EClass.pc.pos.Copy(); p.x -= 14; EClass.pc.Teleport(p.GetNearestPoint(false, false) ?? EClass.pc.pos, true, true); "ok"')
    time.sleep(2)


def host_fps(fps):
    ev(H, f'UnityEngine.QualitySettings.vSyncCount = 0; UnityEngine.Application.targetFrameRate = {fps}; "ok"')


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    saved = ev(H, 'UnityEngine.QualitySettings.vSyncCount + "," + UnityEngine.Application.targetFrameRate')
    try:
        for port in (H, A):
            dismiss_dialogs(port)

        log("--- V1")
        ref = describe(walk(A))
        log(f"reference : {show(ref)}")
        check(f"l'invite marche sur la carte de l'host : pas reguliers ({show(ref)})", ref is not None and ref["cv"] < 0.35)
        back(A)

        log("--- V2")
        host_fps(5)
        time.sleep(2)
        slow = describe(walk(A))
        host_fps(60)
        log(f"host a 5 images par seconde : {show(slow)}")
        check(f"le jeu de l'host rame : les pas de l'invite restent reguliers ({show(slow)})",
              slow is not None and slow["cv"] < 0.35 and slow["max"] < 2.5)
        check("et gardent le meme rythme", slow is not None and ref is not None and abs(slow["mean"] - ref["mean"]) / ref["mean"] < 0.3)
        back(A)

        log("--- V3")
        set_option("PlayerClock", False)
        time.sleep(3)
        try:
            host_fps(5)
            time.sleep(2)
            old = describe(walk(A))
            log(f"option decochee, host a 5 images par seconde : {show(old)}")
            check(f"option decochee : le rythme de l'invite depend de nouveau de l'host ({show(old)})",
                  old is not None and ref is not None and (old["cv"] >= 0.35 or abs(old["mean"] - ref["mean"]) / ref["mean"] >= 0.3))
        finally:
            host_fps(60)
            set_option("PlayerClock", True)
        back(A)
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-move-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass
    finally:
        vsync, fps = saved.split(",")
        ev(H, f'UnityEngine.QualitySettings.vSyncCount = {vsync}; UnityEngine.Application.targetFrameRate = {fps}; "ok"')

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
