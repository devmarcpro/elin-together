"""Captures des nouveautes, sur des instances deja lancees (host + 1 client, monde neuf).

    python _tools/mp_test.py
    python _tools/showcase.py            # ~4 minutes, images dans _shots/nouveautes/

Chaque etape est independante : une etape qui rate est signalee et la suite continue.
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import SHOTS, log, ok, state  # noqa: E402
from travel_suite import HOME, both_joined, dismiss_dialogs, ev, eventually, wait  # noqa: E402
import chara_suite  # noqa: E402
from instance_suite import enter, offer_subdue  # noqa: E402

H, A = 27551, 27552
OUT = SHOTS / "nouveautes"
T = "ElinTogether.Helper.PlayerTrade"
MENU = ('HarmonyLib.AccessTools.Method(HarmonyLib.AccessTools.TypeByName("ElinTogether.Components.LayerElinTogether"), '
        '"OpenPanelSesame").Invoke(null, new object[] { "%s" }); "ok"')
CLOSE = 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"'
DONE = []


def snap(name, port):
    r = ok(emp.call(port, "screenshot", {"scale": 1.0}))
    dst = OUT / f"{name}.png"
    shutil.copy(r["path"], dst)
    DONE.append(dst)
    log(f"capture {dst.name}")


def step(fn):
    try:
        fn()
    except Exception as ex:  # noqa: BLE001
        log(f"ETAPE RATEE {fn.__name__} : {type(ex).__name__}: {ex}")
    for port in (H, A):
        try:
            ev(port, CLOSE)
        except Exception:  # noqa: BLE001
            pass


def near_host(h):
    ev(A, f'var p = EClass._map.charas.Find(x => x.uid == {h}).pos.GetNearestPoint(false, false); EClass.pc.Teleport(p, true, true); "ok"')
    time.sleep(3)


def options():
    ev(H, MENU % "emp_tab_server")
    time.sleep(2)
    snap("01-options-de-l-host", H)
    ev(H, CLOSE)
    ev(H, MENU % "emp_tab_lobby")
    time.sleep(2)
    snap("02-menu-bot", H)


def trade():
    a, h = state(A)["pc"]["uid"], state(H)["pc"]["uid"]
    torch = int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {a}); return c.AddThing(ThingGen.Create("torch")).uid.ToString();'))
    plank = int(ev(H, 'return EClass.pc.AddThing(ThingGen.Create("plank").SetNum(3)).uid.ToString();'))
    ev(H, f'EClass._map.charas.Find(x => x.uid == {a}).ModCurrency(100); "ok"')
    time.sleep(2)
    near_host(h)
    ev(A, f'{T}.Invite({h}); "ok"')
    wait(lambda: ev(H, f'{T}.Describe()').startswith("Invited"), "invitation chez l'host", timeout=15)
    time.sleep(1)
    snap("03-echange-invitation-chez-l-host", H)
    ev(H, 'foreach (var l in EClass.ui.layers.OfType<Dialog>().ToList()) l.Close(); "ok"')
    ev(H, f'{T}.Accept(); "ok"')
    wait(lambda: ev(A, f'{T}.Describe()').startswith("Open"), "echange ouvert", timeout=15)
    ev(A, f'{T}.Offer({torch}, 1); {T}.SetGold(50); "ok"')
    ev(H, f'{T}.Offer({plank}, 2); "ok"')
    wait(lambda: f"{plank}x2" in ev(A, f'{T}.Describe()') and "+50" in ev(H, f'{T}.Describe()'), "offres sur la table", timeout=15)
    ev(H, f'{T}.Confirm(); "ok"')
    wait(lambda: "ready=True" in ev(A, f'{T}.Describe()'), "host pret", timeout=15)
    time.sleep(1)
    snap("04-echange-fenetre-du-client", A)
    snap("05-echange-fenetre-de-l-host", H)
    ev(A, f'{T}.Confirm(); "ok"')
    wait(lambda: ev(A, f'{T}.Describe()').startswith("Done"), "echange fait", timeout=15)
    time.sleep(1)
    snap("06-echange-fait-client", A)


def standing():
    # renommee et karma par joueur : la feuille de personnage de chacun
    ev(A, 'EClass.player.ModFame(120); EClass.player.ModKarma(-45); "ok"')
    time.sleep(2)
    for name, port in (("07-feuille-du-client-renommee-karma", A), ("08-feuille-de-l-host", H)):
        ev(port, 'EClass.ui.AddLayer<LayerChara>().SetChara(EClass.pc); "ok"')
        time.sleep(2)
        snap(name, port)
        ev(port, CLOSE)
    ev(A, 'EClass.player.ModKarma(45); "ok"')


def quests():
    uid, giver = offer_subdue()
    wait(lambda: ev(A, f'EClass._map.charas.Any(c => c.quest != null && c.quest.uid == {uid}).ToString()') == "True", "offre vue par A", timeout=15)
    zuid = enter(uid, giver)
    time.sleep(3)
    snap("09-quete-a-donjon-le-client-dans-sa-zone", A)
    for name, port in (("10-journal-du-client-sa-quete", A), ("11-journal-de-l-host-sans-cette-quete", H)):
        ev(port, 'EClass.ui.AddLayer<LayerJournal>(); "ok"')
        time.sleep(2)
        snap(name, port)
        ev(port, CLOSE)
    ev(A, 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); foreach (var id in e.enemies.ToList()) '
          '{ var c = EClass._map.FindChara(id); if (c != null) c.Die(); } e.CheckClear(); "ok"')
    time.sleep(2)
    ev(A, 'EClass.pc.MoveZone(EClass._zone.ParentZone); "ok"')
    both_joined(H, A, HOME)
    time.sleep(4)
    snap("12-quete-rendue-recompense-aux-pieds-du-client", A)
    dismiss_dialogs(A)
    log(f"zone de quete {zuid} rendue")


def choice():
    chara_suite.leave()
    found = chara_suite.connect()
    time.sleep(1)
    snap("13-choix-du-personnage-a-la-connexion", A)
    log(f"choix proposes : {found}")
    chara_suite.click(0)
    chara_suite.in_game()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(exist_ok=True)
    only = sys.argv[1:]
    for fn in (options, trade, standing, quests, choice):
        if not only or fn.__name__ in only:
            log(f"--- {fn.__name__}")
            step(fn)
    print("\n".join(str(p) for p in DONE))


if __name__ == "__main__":
    main()
