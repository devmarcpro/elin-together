"""Zones partagees entre clients (parite, etape 2) : host + 2 clients.

    python _tools/shared_suite.py            # relance tout (mp_test --clients 2) puis les scenarios
    python _tools/shared_suite.py --reuse    # sur host + 2 clients deja connectes dans la Prairie

G1  A part seul a Vernis, B demande Vernis : B rejoint la session de zone de A
G2  interaction : objets poses vus par l'autre, deplacement de B vu par A
G3  checkpoint de A : l'host recoit aussi le perso de B
G4  B revient chez l'host proprement, la session de zone de A se ferme toute seule
G5  A revient, l'host va a Vernis et retrouve les objets des deux
G7  passation : A rentre en laissant B a Vernis, B devient l'hote de la zone ; A revient en invite de B ;
    l'host arrive : rappel de B et de son invite, tout le monde a Vernis
G6  B rejoint A, A plante : B garde la zone et la rend a l'host en rentrant
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import ROOT, log, shot, state  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, check, dismiss_dialogs, ev, marker, move, on_map,  # noqa: E402
                          scan_logs, wait, zone_uid)

H, A, B = 27551, 27552, 27553


def players(port):
    return sorted(p["charaUid"] for p in state(port).get("players", []))


def settled(port, uid, *, away, guest=None, zone_session=None):
    def cond():
        dismiss_dialogs(port)
        s = state(port)
        return (s.get("sceneMode") == "Zone" and (s.get("zone") or {}).get("uid") == uid
                and bool(s.get("awayZone")) == away and s.get("connected")
                and (guest is None or s.get("guest") == guest)
                and (zone_session is None or s.get("zoneSession") == zone_session))
    return cond


def with_host(*ports, zone=HOME):
    """Tous avec l'host sur sa carte (la Prairie par defaut), sessions de zone fermees.
    Depuis que l'host ne traine plus les joueurs, ceux qui sont ailleurs le rejoignent d'eux-memes."""
    def back(p):
        """Le joueur est chez l'host ; sinon on lui redemande d'y aller (sans effet pendant un transfert)."""
        try:
            if settled(p, zone, away=False)():
                return True
            s = state(p)
            if s.get("sceneMode") == "Zone" and not s.get("inTransfer") and (s.get("zone") or {}).get("uid") != zone:
                move(p, zone)
        except (RuntimeError, OSError):
            pass  # en plein chargement
        return False

    for p in ports:
        wait(lambda p=p: back(p), f"{p} chez l'host", timeout=240, every=4.0)
    wait(lambda: len(players(H)) == 1 + len(ports), "joueurs chez l'host", timeout=60)
    time.sleep(3)


def chara_on_map(port, chara_uid):
    return ev(port, f'EClass._map.charas.Any(c => c.uid == {chara_uid}).ToString()') == "True"


def host_copy_has(chara_uid, thing_uid):
    return ev(H, f'EClass.game.cards.globalCharas.Find({chara_uid}).things.Find({thing_uid}) != null ? "y" : "n"') == "y"


def g1(ctx):
    ctx["a"] = state(A)["pc"]["uid"]
    ctx["b"] = state(B)["pc"]["uid"]
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis")
    move(B, VERNIS)
    wait(settled(B, VERNIS, away=True, guest=True, zone_session="Client"), "B invite de A a Vernis", timeout=240)
    time.sleep(5)
    sa, sb = state(A), state(B)
    check("A heberge la zone (session de zone host)", sa.get("zoneSession") == "Host" and not sa.get("guest"))
    check("B est invite (session de zone client)", sb.get("zoneSession") == "Client" and sb.get("guest"))
    check("A et B se voient dans la liste des joueurs de la zone",
          players(A) == sorted([ctx["a"], ctx["b"]]) and players(B) == sorted([ctx["a"], ctx["b"]]))
    check("A voit le perso de B sur sa carte", chara_on_map(A, ctx["b"]))
    check("B voit le perso de A sur sa carte", chara_on_map(B, ctx["a"]))
    check("l'host est seul chez lui (A et B partis)", players(H) == [1] and zone_uid(H) == HOME)
    shot("g1-A", A)
    shot("g1-B", B)


def drop(port):
    """Objet du sac pose pres du joueur (comme DropThing, synchronise), renvoie (uid, "x,z").
    Un client ne cree pas d'objets a partir de rien : ils sont detruits, seul l'hote en cree."""
    # pose a 4 cases : la case du joueur est souvent le point d'arrivee, ou le suivant ramasse tout
    uid, pos = ev(port, 'var t = EClass.pc.things.Find(x => !x.isEquipped && !x.c_isImportant && !x.IsContainer '
                        '&& x.trait.CanBeDropped && !(x.trait is TraitAbility) && x.id != "money"); '
                        'var p = EClass.pc.pos.Copy(); p.x += 4; p = p.GetNearestPoint(allowChara: false) ?? EClass.pc.pos; '
                        't.ignoreAutoPick = true; EClass._zone.AddCard(t, p); t.uid + "|" + t.pos.x + "," + t.pos.z').split("|")
    return int(uid), pos


def g2(ctx):
    mb, mb_pos = drop(B)
    ok = False
    try:
        wait(lambda: on_map(A, [mb]).get(mb) == mb_pos, "A voit l'objet de B", timeout=20, every=1.0)
        ok = True
    except TimeoutError:
        pass
    check(f"objet pose par B vu par A ({mb_pos})", ok)
    ma, ma_pos = marker(A)
    ok = False
    try:
        wait(lambda: on_map(B, [ma]).get(ma) == ma_pos, "B voit l'objet de A", timeout=20, every=1.0)
        ok = True
    except TimeoutError:
        pass
    check(f"objet pose par A vu par B ({ma_pos})", ok)
    target = ev(B, 'var p = EClass.pc.pos.GetNearestPoint(allowChara: false, ignoreCenter: true); EClass.pc._Move(p); p.x + "," + p.z')
    ok = False
    try:
        wait(lambda: ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {ctx["b"]}); c == null ? "" : c.pos.x + "," + c.pos.z') == target,
             "A voit B bouger", timeout=20, every=1.0)
        ok = True
    except TimeoutError:
        pass
    check(f"deplacement de B vu par A ({target})", ok)
    ctx.update(mb=(mb, mb_pos), ma=(ma, ma_pos))


def g3(ctx):
    ma, _ = ctx["ma"]
    ev(B, f'var t = EClass._map.things.Find(x => x.uid == {ma}); if (t != null) EClass.pc.Pick(t); "ok"')
    time.sleep(3)
    ev(A, 'HarmonyLib.Traverse.Create(ElinTogether.Net.NetSession.Instance.Transport).Method("SendTravelCheckpoint").GetValue(); "ok"')
    ok = False
    try:
        wait(lambda: host_copy_has(ctx["b"], ma), "l'host voit l'objet dans l'inventaire de B", timeout=20, every=1.0)
        ok = True
    except TimeoutError:
        pass
    check("checkpoint de A : l'host a le perso de B a jour (objet ramasse chez A)", ok)


def g4(ctx):
    move(B, HOME)
    with_host(B)
    check("B revenu chez l'host", zone_uid(B) == HOME and not state(B).get("guest"))
    check("l'inventaire de B chez l'host a l'objet ramasse chez A", host_copy_has(ctx["b"], ctx["ma"][0]))
    ok = False
    try:
        wait(lambda: state(A).get("zoneSession") is None, "session de zone de A fermee", timeout=20, every=1.0)
        ok = True
    except TimeoutError:
        pass
    check("A seul de nouveau : sa session de zone s'est fermee", ok and state(A).get("awayZone"))


def g5(ctx):
    move(A, HOME)
    with_host(A, B)
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=240)
    # ils sont restes a la Prairie (A la tient, B est son invite) : ils rejoignent l'host d'eux-memes.
    # Une demande faite pendant que la Prairie change de mains est perdue : comme un joueur, on redemande.
    with_host(A, B, zone=VERNIS)
    mb, mb_pos = ctx["mb"]
    found = on_map(H, [mb])
    check("host a Vernis : l'objet pose par B (invite) est la", found.get(mb) == mb_pos)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    with_host(A, B)


def holder(port, uid):
    """Simule seul la zone (bail a lui, pas d'invite, pas de session de zone)."""
    def cond():
        dismiss_dialogs(port)
        st = state(port)
        return ((st.get("zone") or {}).get("uid") == uid and bool(st.get("awayZone")) and not st.get("guest")
                and st.get("zoneSession") is None and st.get("connected"))
    return cond


def g7(ctx):
    ctx.setdefault("a", state(A)["pc"]["uid"])
    ctx.setdefault("b", state(B)["pc"]["uid"])
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis")
    move(B, VERNIS)
    wait(settled(B, VERNIS, away=True, guest=True, zone_session="Client"), "B invite de A", timeout=240)
    time.sleep(3)
    ma, ma_pos = marker(A)
    wait(lambda: on_map(B, [ma]).get(ma) == ma_pos, "B voit l'objet de A", timeout=20, every=1.0)
    move(A, HOME)
    wait(settled(A, HOME, away=False), "A rentre chez l'host", timeout=240)
    ok = False
    try:
        wait(holder(B, VERNIS), "B prend la main sur Vernis", timeout=60, every=1.0)
        ok = True
    except TimeoutError:
        pass
    check("passation : B simule Vernis apres le depart de A", ok)
    check("passation : l'objet pose par A est toujours la chez B", on_map(B, [ma]).get(ma) == ma_pos)
    check("passation : le perso de A n'est plus sur la carte de B", not chara_on_map(B, ctx["a"]))
    shot("g7-B-holder", B)
    if not ok:
        return
    # A revient, en invite de B cette fois
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=True, zone_session="Client"), "A invite de B", timeout=240)
    check("A rejoint la session de zone de B", state(B).get("zoneSession") == "Host")
    # l'host arrive : il rappelle la zone de B, l'invite A rentre aussi
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=240)
    ok = False
    try:
        wait(lambda: all(settled(p, VERNIS, away=False)() for p in (A, B)), "A et B avec l'host a Vernis",
             timeout=240)
        ok = True
    except TimeoutError:
        pass
    check("rappel avec invite : A et B a Vernis avec l'host", ok)
    time.sleep(3)
    check("l'host a Vernis a l'objet pose par A", on_map(H, [ma]).get(ma) == ma_pos)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    with_host(A, B)


def g6(ctx):
    ctx.setdefault("a", state(A)["pc"]["uid"])
    ctx.setdefault("b", state(B)["pc"]["uid"])
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis")
    move(B, VERNIS)
    wait(settled(B, VERNIS, away=True, guest=True, zone_session="Client"), "B invite de A", timeout=240)
    time.sleep(3)
    pid = next(h["pid"] for h in emp.live_ports() if h["port"] == A)
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    log(f"A tue (pid {pid}) pendant qu'il heberge B")
    ok = False
    try:
        wait(holder(B, VERNIS), "B garde Vernis", timeout=120, every=2.0)
        ok = True
    except TimeoutError:
        pass
    check("A plante : B garde Vernis et la simule", ok)
    if not ok:
        return
    mb, mb_pos = drop(B)
    time.sleep(2)
    move(B, HOME)
    wait(settled(B, HOME, away=False), "B rentre", timeout=240)
    wait(lambda: ctx["b"] in players(H), "B chez l'host", timeout=60)
    check("B rentre chez l'host", zone_uid(B) == HOME and not state(B).get("guest"))
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=240)
    time.sleep(3)
    check("l'host a Vernis a l'objet pose par B apres la reprise", on_map(H, [mb]).get(mb) == mb_pos)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py"), "--clients", "2"], check=True)

    ctx = {}
    steps = [g1, g2, g3, g4, g5, g7, g6]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A), ("B", B)):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', port)}")
                except Exception:  # noqa: BLE001
                    pass
            break

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
