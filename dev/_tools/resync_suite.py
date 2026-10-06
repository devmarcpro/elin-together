"""Somme de controle de la carte et remise a niveau toute seule (Net/NetDesync.cs, case host « AutoResync », cochee ;
plan : dev/PLAN_desync.md section 4, notes : dev/PLAN_desync_outil.md).

    python _tools/mp_test.py
    python _tools/resync_suite.py          # ~3 minutes, deux fenetres deja connectees sur la meme carte

R1  deux jeux synchronises : pendant 30 s les deux joueurs marchent, ramassent et posent un seau ; aucun avertissement
    « Map checksum differs » dans le journal, et a la fin les nombres des deux jeux sont egaux
R2  ecart fait a la main chez l'invite seulement (un seau retire du sol, un autre deplace de 2 cases, un poulet retire
    de la carte et de la memoire des cartes) : l'avertissement parait en moins de 10 s chez l'invite ET chez l'host,
    la carte est redemandee, et 15 s plus tard les nombres sont egaux, le seau, la case de l'autre seau et le poulet
    sont revenus chez l'invite, et l'invite n'a pas ete deplace a cote de l'host (2 cases au plus).
    Les nombres ne comptent plus la case des objets (un objet lance ou eparpille tombe selon les des de chaque jeu) :
    le seau deplace seul ne serait PAS vu. L'ecart est vu par le seau retire et le poulet ; le seau deplace reste
    dans le test pour verifier que le rechargement le remet a sa case
R3  case decochee : meme ecart (un seau retire) : avertissement dans les deux journaux, pas de rechargement en 20 s.
    Case recochee : la carte est rechargee toute seule (au plus un rechargement par 30 s, deja passees ici) et le seau
    revient. Les avertissements voulus de R2 et R3 sont listes par le releve des journaux a la fin : c'est normal

Ce que le banc ne joue pas comme un joueur : c'est un test d'OUTIL. L'ecart est fabrique par `eval` dans le jeu de
l'invite, dans un DynamicDelta (le mod croit appliquer un message recu et ne previent donc pas l'host) : un vrai ecart
vient d'un message perdu, pas d'un retrait a la main. Le ramassage et la pose passent par Chara.Pick / DropThing sans
clic, la marche par TryMoveTowards case par case. Deux fenetres, une machine, connexion locale : pas de retard reseau,
pas de troisieme joueur, pas de session de zone (invite chez un invite), pas de grande base (cout non mesure ici :
`emp.desync` l'affiche). Les sacs ne sont que surveilles (aucun ecart de sac n'est fabrique ici)."""
import json
import sys
import time
from datetime import datetime, timezone

from combat_suite import set_option  # noqa: E402
from equal2_suite import drop, seen, spawn  # noqa: E402
from mp_test import log, state  # noqa: E402
from travel_suite import LOCALLOW, RESULTS, check, dismiss_dialogs, ev, eventually, marker, on_map, scan_logs  # noqa: E402

H, A = 27551, 27552

GUEST_LINE = "Map checksum differs on {ZoneFullName}"
HOST_LINE = "reports a map checksum that differs on {ZoneFullName}"
RELOAD_LINE = "Reloading {ZoneFullName} to repair it"
REQUEST_LINE = "Received zone state request from player"

DESCRIBE = ('(string)HarmonyLib.AccessTools.Method(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.NetDesync"), "Describe")'
            '.Invoke(null, null)')
# le mod croit appliquer un message recu : rien n'est dit a l'host
LOCAL = ('new ElinTogether.Models.DynamicDelta {{ Action = n => {{ {0} }} }}'
         '.Apply(ElinTogether.Net.NetSession.Instance.Connection); return "ok";')
FORGET = ('HarmonyLib.AccessTools.Method(HarmonyLib.AccessTools.TypeByName("ElinTogether.Models.CardCache"), "Remove", '
          'new[] {{ typeof(int) }}).Invoke(null, new object[] {{ {0} }});')
RULE = 'ElinTogether.Net.NetSession.Instance.Rules.AutoResync.ToString()'


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def lines(t0, text):
    """Lignes du journal du mod (les deux jeux y ecrivent) depuis t0 dont le texte fixe contient `text`."""
    out = []
    for f in (LOCALLOW / "ElinMP" / "Logs").glob(f"Session_{datetime.now():%Y%m%d}*.log"):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("@t", "") >= t0 and text in d.get("@mt", ""):
                out.append(d)
    return out


def sums(port):
    """Les nombres de la carte vus par ce jeu : (carte, sacs)."""
    here = ev(port, f"return {DESCRIBE};").splitlines()[0]
    here = here[len("here: "):].split(", computed")[0]
    map_part, _, bags = here.partition(" bags ")
    return map_part, frozenset(bags.split())


def equal():
    return sums(H) == sums(A)


def local(port, code):
    return ev(port, LOCAL.format(code))


def pos(port, uid=None):
    who = "EClass.pc" if uid is None else f"EClass._map.charas.Find(x => x.uid == {uid})"
    x, z = ev(port, f'var c = {who}; return c.pos.x + "," + c.pos.z;').split(",")
    return int(x), int(z)


def steps(port, n=3):
    ev(port, 'var p = EClass.pc.pos.GetRandomPoint(4, true, false, false); if (p == null) return "nulle part"; '
             f'for (var i = 0; i < {n}; i++) EClass.pc.TryMoveTowards(p); return "ok";')


def pick(port, uid):
    return ev(port, f'var t = EClass._map.things.Find(x => x.uid == {uid}); if (t == null) return "absent"; EClass.pc.Pick(t); return "ok";')


def put(port, uid):
    return ev(port, f'var t = EClass.pc.things.Find({uid}); if (t == null) return "absent"; EClass.pc.DropThing(t); return "ok";')


def idle(port):
    """Le joueur ne fait rien et n'a aucune fenetre ouverte : sans cela le mod ne recharge pas la carte."""
    dismiss_dialogs(port)
    ev(port, 'if (!EClass.pc.HasNoGoal) EClass.pc.SetNoGoal(); "ok"')


def r1(ctx):
    t0 = now()
    bucket, _ = marker(H)
    check("R1 le seau pose par l'host est chez l'invite", eventually(lambda: bucket in on_map(A, [bucket]), timeout=10))
    end = time.time() + 30
    turn = 0
    while time.time() < end:
        port = (A, H)[turn % 2]
        steps(H)
        steps(A)
        time.sleep(1.5)
        if pick(port, bucket) == "ok":
            time.sleep(1.5)
            steps(port)
            time.sleep(1.0)
            put(port, bucket)
        time.sleep(2.0)
        turn += 1
    check(f"R1 le seau a ete ramasse et pose {turn} fois, il est au sol chez les deux",
          eventually(lambda: bucket in on_map(H, [bucket]) and bucket in on_map(A, [bucket]), timeout=10))
    warned = lines(t0, GUEST_LINE) + lines(t0, HOST_LINE)
    check(f"R1 aucun avertissement d'ecart en 30 s de jeu ({len(warned)})", not warned)
    for d in warned[:4]:
        print("       ", d.get("@t", "")[11:19], d.get("Detail"))
    check(f"R1 memes nombres chez les deux (host {sums(H)[0]} | invite {sums(A)[0]})", eventually(equal, timeout=8))
    ctx["bucket"] = bucket


def gap_seen(t0, timeout=10):
    """L'avertissement dans les deux journaux : secondes jusqu'a celui de l'invite et celui de l'host (None : absent)."""
    start = time.time()
    guest = host = None
    while time.time() - start < timeout + 2 and (guest is None or host is None):
        if guest is None and lines(t0, GUEST_LINE):
            guest = time.time() - start
        if host is None and lines(t0, HOST_LINE):
            host = time.time() - start
        time.sleep(0.5)
    return guest, host


def r2(ctx):
    bucket = ctx["bucket"]
    other, _ = marker(H)
    hen = spawn(ctx["a"], "chicken")
    ready = eventually(lambda: other in on_map(A, [other]) and (not hen or seen(A, hen)), timeout=15)
    if not check(f"R2 un deuxieme seau et un poulet ({hen or 'pas de place'}) sont chez l'invite, nombres egaux",
                 ready and eventually(equal, timeout=10)):
        return
    idle(A)
    stood = pos(A)
    spot = on_map(A, [other])[other]
    x, z = (int(v) for v in spot.split(","))
    t0 = now()
    local(A, f'EClass._zone.RemoveCard(EClass._map.things.Find(x => x.uid == {bucket})); '
             f'EClass._map.things.Find(x => x.uid == {other})._Move(new Point({x + 2}, {z})); '
             + (f'EClass._zone.RemoveCard(EClass._map.charas.Find(x => x.uid == {hen})); ' + FORGET.format(hen) if hen else ""))
    check("R2 l'ecart existe chez l'invite seulement (l'host a toujours les deux seaux a leur place)",
          bucket not in on_map(A, [bucket]) and on_map(H, [bucket, other]).get(other) == spot and bucket in on_map(H, [bucket])
          and not equal())
    guest, host = gap_seen(t0)
    check(f"R2 avertissement chez l'invite en moins de 10 s ({'absent' if guest is None else f'{guest:.1f} s'})",
          guest is not None and guest <= 10)
    check(f"R2 avertissement chez l'host en moins de 10 s ({'absent' if host is None else f'{host:.1f} s'})",
          host is not None and host <= 10)
    for d in lines(t0, GUEST_LINE)[:2]:
        print("       ", d.get("Detail"))
    check("R2 la carte est redemandee (ligne de l'invite et demande recue par l'host)",
          eventually(lambda: bool(lines(t0, RELOAD_LINE)) and bool(lines(t0, REQUEST_LINE)), timeout=10))
    time.sleep(15)
    dismiss_dialogs(A)
    check(f"R2 15 s plus tard : memes nombres (host {sums(H)[0]} | invite {sums(A)[0]})", equal())
    back = on_map(A, [bucket, other])
    check(f"R2 le seau retire est revenu, l'autre est a sa case {spot} (invite : {back})",
          bucket in back and back.get(other) == spot)
    if hen:
        check("R2 le poulet est revenu chez l'invite", seen(A, hen))
    after = pos(A)
    check(f"R2 l'invite est reste sur place, 2 cases au plus ({stood} -> {after})",
          max(abs(stood[0] - after[0]), abs(stood[1] - after[1])) <= 2)
    seen_by_host = pos(H, ctx["a"])
    check(f"R2 l'host voit l'invite ou il est ({seen_by_host} / {after})",
          max(abs(seen_by_host[0] - after[0]), abs(seen_by_host[1] - after[1])) <= 2)
    check(f"R2 un seul rechargement ({len(lines(t0, RELOAD_LINE))})", len(lines(t0, RELOAD_LINE)) == 1)
    ctx["hen"] = hen


def r3(ctx):
    bucket = ctx["bucket"]
    set_option("AutoResync", False)
    try:
        if not check("R3 la case est decochee chez l'host et chez l'invite",
                     eventually(lambda: ev(A, RULE) == "False" and ev(H, RULE) == "False", timeout=10)):
            return
        idle(A)
        t0 = now()
        local(A, f'EClass._zone.RemoveCard(EClass._map.things.Find(x => x.uid == {bucket}));')
        guest, host = gap_seen(t0)
        check(f"R3 case decochee : avertissement chez l'invite ({'absent' if guest is None else f'{guest:.1f} s'}) "
              f"et chez l'host ({'absent' if host is None else f'{host:.1f} s'})", guest is not None and host is not None)
        time.sleep(20)
        check("R3 case decochee : pas de rechargement en 20 s, le seau manque toujours chez l'invite",
              not lines(t0, RELOAD_LINE) and bucket not in on_map(A, [bucket]))
    finally:
        set_option("AutoResync", True)
    eventually(lambda: ev(A, RULE) == "True", timeout=10)
    idle(A)
    # au plus un rechargement par 30 s (60 s apres le deuxieme sur la meme carte, puis 120...)
    check("R3 case recochee : la carte est rechargee toute seule et le seau revient",
          eventually(lambda: bool(lines(t0, RELOAD_LINE)) and bucket in on_map(A, [bucket]), timeout=90))
    check(f"R3 memes nombres a la fin (host {sums(H)[0]} | invite {sums(A)[0]})", eventually(equal, timeout=20))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = now()
    ctx = {"h": int(state(H)["pc"]["uid"]), "a": int(state(A)["pc"]["uid"])}
    same = (state(H).get("zone") or {}).get("uid") == (state(A).get("zone") or {}).get("uid")
    if not check("les deux joueurs sont sur la meme carte, la regle AutoResync est cochee",
                 same and ev(A, RULE) == "True"):
        sys.exit(1)
    log(ev(A, f"return {DESCRIBE};").splitlines()[0])
    try:
        for step in (r1, r2, r3):
            dismiss_dialogs(H)
            dismiss_dialogs(A)
            step(ctx)
    finally:
        if ctx.get("hen"):
            drop([ctx["hen"]])
    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
