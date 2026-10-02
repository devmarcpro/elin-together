"""Compagnons (parite, etape 3) : host + 1 client A.

    python _tools/companion_suite.py            # relance tout (mp_test) puis les scenarios
    python _tools/companion_suite.py --reuse    # sur host + client deja connectes dans la Prairie

K1  A recrute un compagnon chez l'host : il appartient a A (emp_owner) des deux cotes
K2  il suit A, pas l'host ; le compagnon de l'host reste avec l'host
K3  A part seul a Vernis : son compagnon part avec lui, celui de l'host reste ; l'host le garde hors carte
K4  a Vernis, le compagnon suit A
K5  checkpoint : l'host a l'etat du compagnon (objet donne a Vernis)
K6  A rentre : le compagnon revient a cote de lui chez l'host, une seule fois dans le groupe, avec l'objet
K7  l'host va a Vernis : A et son compagnon suivent, puis retour
K9  limite d'allies par joueur : les recrues de A ne prennent de place qu'a A (pas a l'host)
K8  A plante a Vernis avec son compagnon, se reconnecte : le compagnon revient avec lui
K10 le compagnon meurt en voyage seul : il revient mort chez l'host, hors du groupe, pas ramene
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import LAB_EXE, ROOT, SHOTS, WINDOW, bridge_for, join_client, log, ok, shot, state  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, host_goto, move,  # noqa: E402
                          scan_logs, wait, zone_uid)

H, A = 27551, 27552
SPECIES = ["dog", "cat", "putit", "chicken"]


def info(port, uid):
    """(zone uid ou -1, "x,z" si sur la carte active, proprietaire, nombre d'entrees dans le groupe)"""
    r = ev(port, f'var c = EClass.game.cards.globalCharas.Find({uid}); if (c == null) return "none"; '
                 f'(c.currentZone == null ? -1 : c.currentZone.uid) + "|" + '
                 f'(EClass._map.charas.Contains(c) ? c.pos.x + "," + c.pos.z : "") + "|" + c.GetInt("emp_owner") + "|" + '
                 f'EClass.pc.party.members.Count(m => m != null && m.uid == {uid})')
    if r == "none":
        return None
    zone, pos, owner, count = r.split("|")
    return int(zone), pos, int(owner), int(count)


def alive(port, uid):
    """Le perso existe, n'est pas detruit (une copie client detruite ne doit jamais atteindre l'host)."""
    return ev(port, f'var c = EClass.game.cards.globalCharas.Find({uid}); (c != null && !c.isDestroyed && c.Num > 0).ToString()') == "True"


def dist(port, a, b):
    r = ev(port, f'var x = EClass._map.charas.Find(c => c.uid == {a}); var y = EClass._map.charas.Find(c => c.uid == {b}); '
                 'x == null || y == null ? "-1" : x.Dist(y).ToString()')
    return int(r)


def recruit(port, owner_uid, host=27551):
    """L'host fait apparaitre un animal a cote du joueur, le joueur le recrute."""
    species = next(s for s in SPECIES if ev(host, f'EClass.sources.charas.map.ContainsKey("{s}").ToString()') == "True")
    uid = int(ev(host, f'var a = EClass._map.charas.Find(x => x.uid == {owner_uid}); var c = CharaGen.Create("{species}"); '
                       'EClass._zone.AddCard(c, a.pos.GetNearestPoint(allowChara: false)); c.uid.ToString()'))
    wait(lambda: ev(port, f'(EClass._map.charas.Find(x => x.uid == {uid}) != null).ToString()') == "True",
         "le joueur voit l'animal", timeout=30)
    ev(port, f'EClass._map.charas.Find(x => x.uid == {uid}).MakeAlly(false); "ok"')
    return uid


def empty_ally(port, uid=None):
    """Places d'allies libres : du joueur local, ou (vu de ce jeu) du proprietaire du compagnon uid."""
    if uid is None:
        return int(ev(port, 'EClass.player.lastEmptyAlly.ToString()'))
    return int(ev(port, 'HarmonyLib.AccessTools.Method("ElinTogether.Patches.CompanionAllyLimitPatch:EmptyAllyFor")'
                        f'.Invoke(null, new object[] {{ EClass.player, EClass.game.cards.globalCharas.Find({uid}) }}).ToString()'))


def walk_away(port, steps=12, dx=10):
    """Le joueur marche vers un point a ~dx cases (pas a pas, comme au clavier)."""
    target = ev(port, f'var p = EClass.pc.pos.Copy(); p.x += {dx}; p = p.GetNearestPoint(allowChara: false) ?? EClass.pc.pos; '
                      'p.x + "," + p.z')
    x, z = target.split(",")
    for _ in range(steps):
        ev(port, f'EClass.pc.TryMoveTowards(new Point({x}, {z})); "ok"')
        time.sleep(0.3)
    return target


def window_title(pid):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).MainWindowTitle"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def relaunch_client(attempts=3):
    """Relance le client tue. Trop tot apres le kill, Unity croit l'ancienne instance encore la
    (« Fatal error : Another instance is already running ») : on ferme et on reessaie un peu plus tard."""
    for attempt in range(attempts):
        time.sleep(15)
        proc = subprocess.Popen([str(LAB_EXE), *WINDOW, "-logFile", str(SHOTS / "elin2-player.log")], cwd=LAB_EXE.parent)
        end = time.time() + 420
        while time.time() < end:
            port = bridge_for(proc.pid)
            if port:
                return port
            if window_title(proc.pid) == "Fatal error":
                log(f"relance {attempt + 1} refusee par Unity (instance precedente), nouvel essai")
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/F"], capture_output=True)
                break
            time.sleep(3)
        else:
            raise TimeoutError("pont du client relance")
    raise TimeoutError("relance du client refusee")


def k1(ctx):
    ctx["a"] = state(A)["pc"]["uid"]
    host_comp = ev(H, 'var c = EClass.pc.party.members.Find(m => m != null && !m.IsPC && m.GetInt("emp_owner") == 0 '
                      '&& !m.GetBool("remote_chara")); c == null ? "" : c.uid.ToString()')
    species = next(s for s in SPECIES if ev(H, f'EClass.sources.charas.map.ContainsKey("{s}").ToString()') == "True")
    if not host_comp:
        # l'host recrute le sien (sans proprietaire : il suit le chef du groupe, l'host)
        host_comp = ev(H, f'var c = CharaGen.Create("{species}"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(allowChara: false)); '
                          'c.MakeAlly(false); c.uid.ToString()')
    ctx["hc"] = int(host_comp)
    log(f"compagnon de l'host : {ctx['hc']}")
    uid = int(ev(H, f'var a = EClass._map.charas.Find(x => x.uid == {ctx["a"]}); var c = CharaGen.Create("{species}"); '
                    'EClass._zone.AddCard(c, a.pos.GetNearestPoint(allowChara: false)); c.uid.ToString()'))
    ctx["k"] = uid
    log(f"compagnon de test : {species} {uid}")
    wait(lambda: ev(A, f'(EClass._map.charas.Find(x => x.uid == {uid}) != null).ToString()') == "True",
         "A voit le futur compagnon", timeout=30)
    ev(A, f'EClass._map.charas.Find(x => x.uid == {uid}).MakeAlly(false); "ok"')
    check("host : le compagnon est dans le groupe et appartient a A",
          eventually(lambda: (i := info(H, uid)) is not None and i[3] == 1 and i[2] == ctx["a"]))
    check("A : le compagnon est dans son groupe et lui appartient",
          eventually(lambda: (i := info(A, uid)) is not None and i[3] == 1 and i[2] == ctx["a"]))


def k2(ctx):
    uid = ctx["k"]
    walk_away(A)
    check("host : le compagnon a suivi A (3 cases ou moins)",
          eventually(lambda: 0 <= dist(H, uid, ctx["a"]) <= 3, timeout=30))
    if ctx["hc"]:
        check("host : son propre compagnon reste avec lui, pas avec A",
              eventually(lambda: dist(H, ctx["hc"], 1) < dist(H, ctx["hc"], ctx["a"]), timeout=30))


def k3(ctx):
    uid = ctx["k"]
    move(A, VERNIS)
    wait(client_settled(A, VERNIS, True), "A seul a Vernis")
    time.sleep(3)
    i = info(A, uid)
    check("A a Vernis : son compagnon est arrive avec lui", i is not None and i[0] == VERNIS and i[1] != ""
          and 0 <= dist(A, uid, ctx["a"]) <= 4)
    if ctx["hc"]:
        check("A a Vernis : le compagnon de l'host n'est pas venu", (info(A, ctx["hc"]) or (0, ""))[1] == "")
    i = info(H, uid)
    check("host : le compagnon de A n'est plus sur sa carte, toujours dans le groupe, hors carte",
          i is not None and i[1] == "" and i[0] == -1 and i[3] == 1)
    if ctx["hc"]:
        check("host : son compagnon est toujours avec lui", (info(H, ctx["hc"]) or (0, ""))[1] != "")
    shot("k3-A-vernis", A)


def k4(ctx):
    uid = ctx["k"]
    walk_away(A, dx=-8)
    check("A a Vernis : le compagnon le suit", eventually(lambda: 0 <= dist(A, uid, ctx["a"]) <= 3, timeout=30))


def k5(ctx):
    uid = ctx["k"]
    gift = int(ev(A, f'var t = ThingGen.Create("bucket"); EClass.game.cards.globalCharas.Find({uid}).AddThing(t); t.uid.ToString()'))
    ctx["gift"] = gift
    ev(A, 'HarmonyLib.Traverse.Create(ElinTogether.Net.NetSession.Instance.Transport).Method("SendTravelCheckpoint").GetValue(); "ok"')
    check("checkpoint : l'host a le compagnon a jour (objet donne a Vernis)",
          eventually(lambda: ev(H, f'(EClass.game.cards.globalCharas.Find({uid}).things.Find({gift}) != null).ToString()') == "True"))
    i = info(H, uid)
    check("checkpoint : le compagnon reste hors carte chez l'host, une seule fois dans le groupe",
          i is not None and i[1] == "" and i[3] == 1)


def k6(ctx):
    uid = ctx["k"]
    move(A, HOME)
    both_joined(H, A, HOME)
    check("host : le compagnon est revenu a cote de A",
          eventually(lambda: 0 <= dist(H, uid, ctx["a"]) <= 4, timeout=30))
    i = info(H, uid)
    check("host : une seule fois dans le groupe, toujours a A", i is not None and i[3] == 1 and i[2] == ctx["a"])
    check("host : le compagnon a l'objet donne a Vernis",
          ev(H, f'(EClass.game.cards.globalCharas.Find({uid}).things.Find({ctx["gift"]}) != null).ToString()') == "True")
    check("A : voit son compagnon chez l'host, dans son groupe",
          eventually(lambda: (i := info(A, uid)) is not None and i[1] != "" and i[3] == 1))
    time.sleep(5)
    check("host : 5 s plus tard, le compagnon existe toujours (pas detruit par une copie client)", alive(H, uid))
    walk_away(A, dx=-8)
    check("de retour chez l'host, le compagnon suit toujours A",
          eventually(lambda: 0 <= dist(H, uid, ctx["a"]) <= 3, timeout=30))


def k7(ctx):
    uid = ctx["k"]
    # l'host ne traine plus les joueurs : A reste, puis le rejoint de lui-meme, avec son compagnon
    host_goto(H, A, VERNIS)
    check("l'host change de zone, A le rejoint : son compagnon suit",
          eventually(lambda: (i := info(H, uid)) is not None and i[0] == VERNIS and i[1] != "", timeout=30))
    host_goto(H, A, HOME)


def k9(ctx):
    host_before, a_before = empty_ally(H), empty_ally(A)
    extra = [recruit(A, ctx["a"]) for _ in range(3)]
    log(f"recrues de A : {extra}")
    check("A : ses 3 recrues lui prennent 3 places", eventually(lambda: empty_ally(A) == a_before - 3, timeout=30))
    check("host : les recrues de A ne lui prennent aucune place", empty_ally(H) == host_before)
    check("host : les places des compagnons de A sont celles de A, celles du sien les siennes",
          empty_ally(H, ctx["k"]) == empty_ally(A) and empty_ally(H, ctx["hc"]) == empty_ally(H))
    ctx["extra"] = extra


def k10(ctx):
    port, uid = ctx.get("A", A), ctx["k"]
    move(port, VERNIS)
    wait(client_settled(port, VERNIS, True), "A seul a Vernis")
    time.sleep(3)
    ev(port, f'EClass.game.cards.globalCharas.Find({uid}).Die(); "ok"')
    check("A : son compagnon mort a quitte le groupe", eventually(lambda: (info(port, uid) or (0, "", 0, 1))[3] == 0))
    move(port, HOME)
    both_joined(H, port, HOME)
    time.sleep(3)
    r = ev(H, f'var c = EClass.game.cards.globalCharas.Find({uid}); c == null ? "none" : c.isDead + "|" + '
              f'EClass.pc.party.members.Contains(c) + "|" + EClass._map.charas.Contains(c) + "|" + c.GetInt("emp_owner")')
    check(f"host : le compagnon mort en voyage reste mort, hors du groupe, pas ramene ({r})", r == f"True|False|False|{ctx['a']}")
    check("host : les autres compagnons de A sont revenus avec lui",
          all(0 <= dist(H, c, ctx["a"]) <= 5 for c in ctx.get("extra", [])))


def k8(ctx):
    uid = ctx["k"]
    move(A, VERNIS)
    wait(client_settled(A, VERNIS, True), "A seul a Vernis")
    time.sleep(3)
    pid = next(h["pid"] for h in emp.live_ports() if h["port"] == A)
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    log(f"A tue (pid {pid}) a Vernis avec son compagnon")
    wait(lambda: len(state(H).get("players", [])) == 1, "host : A deconnecte", timeout=90)
    i = info(H, uid)
    check("host : apres le plantage, le compagnon est hors carte, toujours dans le groupe",
          i is not None and i[1] == "" and i[3] == 1)
    client = ctx["A"] = relaunch_client()
    wait(lambda: state(client).get("sceneMode") == "Title", "ecran titre du client", timeout=180)
    time.sleep(20)
    # la connexion, le choix du personnage (le premier : celui qu'il jouait) et les nouveaux essais
    join_client(H, client, "A")
    both_joined(H, client, HOME)
    check("A reconnecte : son compagnon revient a cote de lui",
          eventually(lambda: 0 <= dist(H, uid, ctx["a"]) <= 4, timeout=30))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py")], check=True)

    ctx = {}
    steps = [k1, k2, k3, k4, k5, k6, k7, k9, k8, k10]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A)):
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
