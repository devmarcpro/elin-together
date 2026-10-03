"""Cohabitation avec d'autres mods. Test court (host + 1 client a la Prairie), finit avec le client reconnecte.

    python _tools/mp_test.py
    python _tools/compat_suite.py       # ~2 minutes

M1  Somewhat Enhanced Display (Workshop 3781674985), vu dans une vraie partie le 2026-10-03 : sa barre de vie suit
    le dernier personnage survole ; quand la session finit (retour a l'ecran titre), elle continue de le lire a
    chaque image alors qu'il n'y a plus de jeu : 11 342 erreurs en quatre minutes dans le journal du joueur.
    Ici : le client "survole" son personnage, quitte la session, et son journal ne doit montrer aucune erreur.
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import SHOTS, log, shot  # noqa: E402
import chara_suite  # noqa: E402
from travel_suite import RESULTS, check, ev, scan_logs  # noqa: E402

H, A = 27551, 27552
CLIENT_LOG = SHOTS / "elin2-player.log"
SED = "Macchacoffee.ElinMods.SomewhatEnhancedDisplay"

# ce que fait le survol d'un personnage : la barre de vie du mod se met a le suivre
HOVER = (f'var ui = HarmonyLib.AccessTools.TypeByName("{SED}.UI.ModUI"); if (ui == null) return "absent"; '
         'var hg = HarmonyLib.AccessTools.Property(ui, "HoverGuide").GetValue(null); if (hg == null) return "pas de bulle"; '
         'var item = HarmonyLib.AccessTools.Property(hg.GetType(), "Item1").GetValue(hg); '
         'var bar = HarmonyLib.AccessTools.Property(item.GetType(), "HealthBar").GetValue(item); '
         'HarmonyLib.AccessTools.Method(bar.GetType(), "UpdateTarget", new[] { typeof(Chara) }).Invoke(bar, new object[] { EClass.pc }); '
         'return "ok";')


def errors_since(offset):
    text = CLIENT_LOG.read_bytes()[offset:].decode("utf-8", errors="replace")
    return text.count("NullReferenceException"), text.count(f"{SED}.UI.HoverGuide.HealthBar.Update")


def m1():
    r = ev(A, HOVER)
    if r == "absent":
        log("Somewhat Enhanced Display n'est pas installe sur ce PC : M1 saute")
        return
    check(f"le client survole son personnage, la barre de vie du mod le suit ({r})", r == "ok")
    offset = CLIENT_LOG.stat().st_size
    chara_suite.leave()
    time.sleep(8)
    errors, from_mod = errors_since(offset)
    check(f"session finie, ecran titre : aucune erreur dans le journal du client ({errors} erreurs, {from_mod} venant du mod)",
          errors == 0)
    chara_suite.connect()
    chara_suite.click(0)
    chara_suite.in_game()
    time.sleep(3)
    errors, _ = errors_since(offset)
    check(f"de retour en jeu : toujours aucune erreur ({errors})", errors == 0)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        log("--- M1")
        m1()
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-compat-{name}', port)}")
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
