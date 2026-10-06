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
    both_joined(H, A, state(H)["zone"]["uid"])
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


def reconnect():
    """Le lien de l'invite est coupe : le message "on vous ramene dans la partie", puis le retour tout seul."""
    ok(emp.call(A, "command", {"cmd": "emp.link_timeout 1"}))
    ok(emp.call(A, "command", {"cmd": "emp.cut_link 30"}))
    time.sleep(21)
    snap("14-coupure-l-invite-revient-tout-seul", A)
    wait(lambda: state(A).get("connected") and state(A).get("sceneMode") == "Zone", "l'invite est revenu", timeout=120, every=3.0)
    emp.call(A, "command", {"cmd": "emp.link_timeout 0"})


def imported():
    """Rejoindre avec le personnage d'une sauvegarde : l'ecran de choix, la liste, puis en jeu."""
    import import_suite
    from combat_suite import set_option
    from mp_test import PRISTINE
    shutil.rmtree(import_suite.SOLO, ignore_errors=True)
    shutil.copytree(PRISTINE, import_suite.SOLO, copy_function=shutil.copy)
    set_option("ImportCharacter", True)
    try:
        time.sleep(2)
        chara_suite.leave()
        chara_suite.connect()
        time.sleep(1)
        snap("14-choix-avec-un-personnage-d-une-sauvegarde", A)
        import_suite.pick(import_suite.IMPORT)
        wait(lambda: any("(world_import)" in c for c in import_suite.choices()), "liste des sauvegardes", timeout=30, every=1.0)
        time.sleep(1)
        snap("15-liste-de-mes-sauvegardes", A)
        import_suite.pick("(world_import)")
        chara_suite.in_game()
        dismiss_dialogs(A)
        time.sleep(2)
        snap("16-personnage-importe-en-jeu", A)
    finally:
        set_option("ImportCharacter", False)
        shutil.rmtree(import_suite.SOLO, ignore_errors=True)


def together():
    """quetes a donjon a deux : la boite chez l'autre joueur, dans les deux sens, et les deux dans la meme zone"""
    import together_suite as ts
    from travel_suite import host_goto
    host, guest = ev(H, "EClass.pc.Name"), ev(A, "EClass.pc.Name")
    ev(H, CLOSE)
    ev(A, CLOSE)
    if state(H)["zone"]["uid"] != HOME:
        host_goto(H, A, HOME)
    both_joined(H, A, HOME)
    _, zuid = ts.host_enters()
    if ts.asked(host):
        snap("17-quete-a-deux-l-host-part-la-boite-chez-l-invite", A)
        ts.follow(zuid)
        time.sleep(3)
        snap("18-quete-a-deux-les-deux-dans-la-zone-vu-par-l-invite", A)
    ts.host_leaves()
    uid, giver = ts.guest_takes()
    ts.guest_departs(uid, giver)
    if ts.host_asked(guest):
        snap("19-quete-a-deux-l-invite-part-la-boite-chez-l-host", H)
        ts.host_comes()
        time.sleep(3)
        snap("20-quete-a-deux-l-host-accompagne-l-invite", H)
    else:
        ts.guest_alone_inside()
    ev(A, ts.LEAVE)
    ts.back_home()


def base():
    """un invite a la base : la recherche est refusee avec un message, rien n'est debite"""
    ev(A, CLOSE)
    ev(A, 'var b = EClass.Branch; if (b.researches.plans.Count == 0) b.researches.AddPlan(ResearchPlan.Create("hearth_stone")); '
          'EClass.ui.AddLayer<LayerTech>(); "ok"')
    time.sleep(2)
    ev(A, 'var b = EClass.Branch; b.researches.CanCompletePlan(b.researches.plans[0]); "ok"')
    time.sleep(1)
    snap("21-base-la-recherche-d-un-invite-est-refusee-avec-un-message", A)
    ev(A, CLOSE)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(exist_ok=True)
    only = sys.argv[1:]
    for fn in (options, trade, standing, quests, together, base, choice, reconnect, imported):
        if not only or fn.__name__ in only:
            log(f"--- {fn.__name__}")
            step(fn)
    print("\n".join(str(p) for p in DONE))


if __name__ == "__main__":
    main()
