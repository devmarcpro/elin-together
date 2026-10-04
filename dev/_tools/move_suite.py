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
V4  l'host devient trois fois plus rapide que l'invite : l'invite marche au meme rythme qu'avant, et l'host au
    meme rythme que l'invite (case "chaque joueur marche comme en solo")
V5  case decochee : le pas de l'invite s'allonge avec l'ecart de vitesse (l'ancien comportement)
V6  l'accelere se partage. Une marche lancee par AI_Goto met le jeu de celui qui marche en accelere (x2,2) :
    les 118 ms par pas ci-dessus sont deja une allure d'accelere. Quand l'invite marche, le monde de l'host
    accelere avec lui (comme quand c'est l'host qui marche) ; quand l'host marche, le jeu de l'invite immobile a
    cote de lui suit (lu dans le mod : FollowsHost, pas mesure sur un geste de l'invite) ; tout retombe ensuite

Limite : la marche est lancee par AI_Goto (le meme deplacement qu'un clic sur une case), pas touche enfoncee.
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
# la meme recherche, puis le depart : une seule commande, toujours le meme texte. Le pont de test compile chaque
# texte nouveau, le jeu se fige un instant puis rattrape, et les premiers pas partent en rafale
GO = (TARGET.replace('return best.x + "," + best.z + "," + (best.x - p.x);', '') +
      'if (best.x - p.x >= 8) EClass.pc.SetAIImmediate(new AI_Goto(best, 0)); return (best.x - p.x).ToString();')
WEST = 'var p = EClass.pc.pos.Copy(); p.x -= 16; EClass.pc.Teleport(p.GetNearestPoint(false, false) ?? EClass.pc.pos, true, true); "ok"'
POS = 'EClass.pc.pos.x + "," + EClass.pc.pos.z + "," + EClass.pc.HasNoGoal'


TURBO = 'AM_Adv.turbo.ToString(System.Globalization.CultureInfo.InvariantCulture)'
# a quelle allure tourne ce jeu : 1 normal, 2.2 en accelere (le temps de jeu de la derniere image sur son temps reel)
PACE = '(Core.gameDelta / Mathf.Max(0.0001f, Core.delta)).ToString("0.00", System.Globalization.CultureInfo.InvariantCulture)'
# un joueur immobile perd l'accelere a chaque image : celui qui accelere marche, trois cases a l'est puis retour
PACER = ('if (EClass.pc.HasNoGoal) { var p = EClass.pc.pos.Copy(); '
         'p.x += (EClass.pc.GetInt(990001) == 0 ? 3 : -3); EClass.pc.SetInt(990001, 1 - EClass.pc.GetInt(990001)); '
         'EClass.pc.SetAIImmediate(new AI_Goto(p, 0)); } ActionMode.Adv.SetTurbo(); "ok"')

# la position de celui qui marche, en tenant son accelere : une marche l'allume ou non selon ce que la fenetre
# recoit (souris, touche Maj), et une mesure faite pendant qu'on se sert du PC devenait irreguliere
RUN = 'ActionMode.Adv.SetTurbo(); return ' + POS + ';'


def calm(port):
    """Attend que ce jeu tourne a l'allure normale."""
    for _ in range(40):
        if float(ev(port, PACE)) < 1.3:
            return True
        time.sleep(0.5)
    return False


FOLLOWS = ('((bool)HarmonyLib.Traverse.Create(HarmonyLib.AccessTools.TypeByName('
           '"ElinTogether.Patches.GameSynchronizationContext")).Property("FollowsHost").GetValue() ? "1" : "0")')


def walk(port, turbo=None, watch=None, read=PACE):
    """Fait marcher le joueur en ligne droite et releve l'instant de chaque pas. Renvoie les intervalles (s).
    turbo : port du jeu ou l'accelere est tenu pendant la marche ; watch : port dont on releve l'accelere."""
    if int(ev(port, GO)) < 8:
        # pas assez de place vers l'est : on repart plus a l'ouest
        ev(port, WEST)
        time.sleep(2)
        ev(port, GO)
    steps, last, end = [], None, time.time() + 25
    seen = []
    while time.time() < end:
        if turbo is not None:
            ev(turbo, PACER if turbo != port else 'ActionMode.Adv.SetTurbo(); "ok"')
        if watch is not None:
            seen.append(float(ev(watch, read)))
        px, pz, idle = ev(port, RUN).split(",")
        now = time.perf_counter()
        if (px, pz) != last:
            steps.append(now)
            last = (px, pz)
        if idle == "True" and len(steps) > 3:
            break
    # le premier releve n'est pas un pas, le premier pas part tout de suite : on garde les intervalles suivants
    gaps = [b - a for a, b in zip(steps[2:], steps[3:])]
    if turbo is not None:
        ev(turbo, 'EClass.pc.SetInt(990001, 0); ActionMode.Adv.EndTurbo(); "ok"')
    if watch is not None:
        return gaps, seen
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


def option(name, value):
    """Regle une case de l'host. Sur un build qui n'a pas encore la case : rien, et on le dit."""
    try:
        set_option(name, value)
        return True
    except Exception as ex:  # noqa: BLE001
        log(f"case {name} absente de ce build ({type(ex).__name__})")
        return False


def speed(port):
    return int(ev(port, "EClass.pc.Speed.ToString()"))


def host_fps(fps):
    ev(H, f'UnityEngine.QualitySettings.vSyncCount = 0; UnityEngine.Application.targetFrameRate = {fps}; "ok"')


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    saved = ev(H, 'UnityEngine.QualitySettings.vSyncCount + "," + UnityEngine.Application.targetFrameRate')
    # "courir tout seul" (option du jeu) allume l'accelere selon la distance entre la souris et le personnage :
    # la mesure dependait de l'endroit ou trainait le pointeur. Coupee le temps du test, l'accelere est mis a la main
    autorun = {port: ev(port, 'var a = EClass.core.config.input.autorun; EClass.core.config.input.autorun = false; a.ToString()') for port in (H, A)}
    try:
        for port in (H, A):
            dismiss_dialogs(port)

        # les cases dont depend ce test, quoi qu'une suite precedente ait laisse
        option("PlayerCombatTime", True)
        option("PlayerClock", True)
        has_pace = option("PlayerStepPace", True)
        time.sleep(3)

        # echauffement : la premiere marche fait compiler ses commandes par le pont de test, le jeu se fige un
        # instant puis rattrape (le temps d'image du jeu est lisse) : ses premiers pas partent en rafale
        for port in (A, H):
            ev(port, WEST)
            time.sleep(1)
            for _ in range(2):
                walk(port)
                back(port)
        time.sleep(2)
        check("les deux jeux tournent a l'allure normale avant de mesurer", calm(H) and calm(A))

        log("--- V1")
        # la premiere marche mesuree apres un lancement est parfois encore en rafale : reprise, trois fois au plus
        for _ in range(3):
            ref = describe(walk(A))
            if ref is not None and ref["cv"] < 0.15:
                break
            back(A)
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
        if option("PlayerClock", False):
            time.sleep(3)
            try:
                # d'abord sans gener l'host : la reference de l'ancien comportement (l'host accelere son monde
                # pour chaque pas d'un invite), puis l'host qui rame
                base = describe(walk(A))
                back(A)
                log(f"option decochee : {show(base)}")
                host_fps(5)
                time.sleep(2)
                old = describe(walk(A))
                log(f"option decochee, host a 5 images par seconde : {show(old)}")
                check(f"option decochee : le rythme de l'invite depend de nouveau de l'host ({show(old)})",
                      old is not None and base is not None and
                      (old["cv"] >= 0.35 or abs(old["mean"] - base["mean"]) / base["mean"] >= 0.3))
            finally:
                host_fps(60)
                option("PlayerClock", True)
            back(A)
            time.sleep(3)

        log("--- V4")
        before = speed(H), speed(A)
        # l'host devient bien plus rapide que l'invite (element 79 : vitesse)
        bonus = max(200, before[1] * 2)
        ev(H, f'EClass.pc.elements.ModBase(79, {bonus}); EClass.pc.Refresh(); "ok"')
        try:
            time.sleep(6)  # la vitesse de chacun voyage avec l'etat des joueurs
            log(f"vitesses : host {before[0]} -> {speed(H)}, invite {before[1]} -> {speed(A)}")
            gap = describe(walk(A))
            back(A)
            fast = describe(walk(H))
            back(H)
            log(f"host trois fois plus rapide : invite {show(gap)} ; host {show(fast)}")
            check(f"l'host est bien plus rapide que l'invite ({speed(H)} contre {speed(A)})", speed(H) >= speed(A) * 2)
            check(f"l'invite marche au meme rythme qu'avant ({show(gap)}, avant {show(ref)})",
                  gap is not None and ref is not None and abs(gap["mean"] - ref["mean"]) / ref["mean"] < 0.2)
            check(f"l'host marche au meme rythme que l'invite ({show(fast)})",
                  gap is not None and fast is not None and abs(fast["mean"] - gap["mean"]) / gap["mean"] < 0.2)

            log("--- V5")
            if has_pace:
                option("PlayerStepPace", False)
                time.sleep(3)
                try:
                    stretched = describe(walk(A))
                    back(A)
                    log(f"case decochee : invite {show(stretched)}")
                    check(f"case decochee : le pas de l'invite s'allonge avec l'ecart de vitesse ({show(stretched)})",
                          stretched is not None and ref is not None and stretched["mean"] > ref["mean"] * 1.3)
                finally:
                    option("PlayerStepPace", True)
        finally:
            ev(H, f'EClass.pc.elements.ModBase(79, {-bonus}); EClass.pc.Refresh(); "ok"')
        time.sleep(6)

        log("--- V6")
        for port in (H, A):
            ev(port, 'ActionMode.Adv.EndTurbo(); "ok"')
        time.sleep(1)
        gaps, seen = walk(A, watch=H)
        quick = describe(gaps)
        back(A)
        share = sum(1 for t in seen if t > 1.5) / max(1, len(seen))
        log(f"l'invite marche : {show(quick)} ; monde de l'host en accelere {share * 100:.0f} % du temps")
        check(f"l'invite marche toujours au meme rythme ({show(quick)}, reference {show(ref)})",
              quick is not None and ref is not None and abs(quick["mean"] - ref["mean"]) / ref["mean"] < 0.2 and quick["cv"] < 0.35)
        check(f"quand l'invite marche, le monde de l'host accelere avec lui ({share * 100:.0f} % du temps)", share > 0.7)
        time.sleep(2)
        check("le monde de l'host reprend l'allure normale quand l'invite s'arrete", calm(H))
        gaps, seen = walk(H, watch=A, read=FOLLOWS)
        back(H)
        share = sum(1 for t in seen if t > 0) / max(1, len(seen))
        log(f"l'host marche : le jeu de l'invite immobile suit {share * 100:.0f} % du temps")
        check(f"quand l'host marche, le jeu de l'invite a cote de lui accelere aussi ({share * 100:.0f} % du temps)", share > 0.7)
        time.sleep(2)
        check("et tout le monde reprend l'allure normale ensuite", calm(H) and calm(A) and ev(A, FOLLOWS) == "0")
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-move-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass
    finally:
        for port, value in autorun.items():
            ev(port, f'EClass.core.config.input.autorun = {value.lower()}; "ok"')
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
