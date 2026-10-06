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
R4  ecart de SAC fabrique chez l'invite, dans sa copie du sac de L'HOST (un seau retire, une pile de 5 cailloux passee
    a 2) : l'invite redemande ce personnage (« Asking for the bag of »), l'host l'envoie (« asks for the bag of »),
    l'invite remplace (« Bag of … brought to its keeper's copy »). Apres : le sac de l'host est le meme dans les deux
    jeux et le meme qu'avant (rien perdu, rien double), le seau n'est nulle part ailleurs, pas de rechargement de carte
R5  ecart dans LE PROPRE SAC de l'invite (chez lui : un seau retire, une pile entamee ; chez l'host : un seau retire
    de son personnage sans le dire, donc un seau « fantome » chez l'invite). Sous-option eteinte (le defaut) : un
    avertissement, aucune demande, le sac ne bouge pas. Sous-option allumee par eval (NetDesync.RepairOwnBag, il
    n'y a pas encore de case) : le sac de l'invite devient celui de l'host : le seau retire revient, la pile revient
    a 5, le seau fantome s'en va (c'est la « perte » voulue : l'host ne l'a pas). JAMAIS LANCE

Ce que le banc ne joue pas comme un joueur : c'est un test d'OUTIL. L'ecart est fabrique par `eval` dans le jeu de
l'invite, dans un DynamicDelta (le mod croit appliquer un message recu et ne previent donc pas l'host) : un vrai ecart
vient d'un message perdu, pas d'un retrait a la main. Le ramassage et la pose passent par Chara.Pick / DropThing sans
clic, la marche par TryMoveTowards case par case. Deux fenetres, une machine, connexion locale : pas de retard reseau,
pas de troisieme joueur, pas de session de zone (invite chez un invite), pas de grande base (cout non mesure ici :
`emp.desync` l'affiche). Sacs (R4, R5) : pas d'equipement, pas de sac dans un sac, pas d'objet tenu en main, pas de
fenetre de sac ouverte ; pas le cas « ramasse au moment meme de la reparation » (message en route) ; pas le fantome
que l'host a encore AU SOL (il faut alors un rechargement de carte en plus, trop long ici apres R2 et R3)."""
import json
import sys
import time
from datetime import datetime, timezone

from combat_suite import set_option  # noqa: E402
from equal2_suite import drop, seen, spawn  # noqa: E402
from mp_test import log, state  # noqa: E402
from pickup_suite import FILL  # noqa: E402
from travel_suite import LOCALLOW, RESULTS, check, dismiss_dialogs, ev, eventually, marker, on_map, scan_logs  # noqa: E402
from world_diff import snapshot  # noqa: E402

H, A = 27551, 27552

GUEST_LINE = "Map checksum differs on {ZoneFullName}"
HOST_LINE = "reports a map checksum that differs on {ZoneFullName}"
RELOAD_LINE = "Reloading {ZoneFullName} to repair it"
REQUEST_LINE = "Received zone state request from player"
ASK_LINE = "Asking for the bag of {Uid} again"
ANSWER_LINE = "asks for the bag of {Uid} again"
BAG_LINE = "Bag of {Uid} brought to its keeper's copy"
BAG_DIFF_LINE = "holds another bag of {Uid} on {ZoneFullName}"
OWN = ('HarmonyLib.AccessTools.Field(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.NetDesync"), "RepairOwnBag")'
       '.SetValue(null, {0}); return "ok";')

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


def bag(port, owner):
    """Ce que ce jeu voit dans le sac de ce personnage : numero -> (identifiant, quantite, emplacement, contenant)."""
    return {k[1]: v for k, v in snapshot(port)["bags"].items() if k[0] == owner}


def give(owner, thing_id, num=1):
    """L'host met un objet dans le sac de ce personnage (tout le monde en est prevenu) ; renvoie son numero."""
    return int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {owner}); var t = ThingGen.Create("{thing_id}"); '
                     f't.SetBlessedState(BlessedState.Normal); if ({num} > 1) t.SetNum({num}); return c.AddThing(t, false).uid.ToString();'))


def said(t0, text, owner):
    return [d for d in lines(t0, text) if d.get("Uid") == owner]


def bag_repaired(what, owner, t0, reference, timeout=20):
    """La demande, la reponse, le remplacement, puis : le meme sac dans les deux jeux, celui de l'host."""
    check(f"{what} : l'invite redemande ce personnage en moins de {timeout} s",
          eventually(lambda: bool(said(t0, ASK_LINE, owner)), timeout=timeout))
    check(f"{what} : l'host l'envoie", eventually(lambda: bool(said(t0, ANSWER_LINE, owner)), timeout=10))
    done = eventually(lambda: bool(said(t0, BAG_LINE, owner)), timeout=10)
    check(f"{what} : l'invite remplace le sac", done)
    for d in said(t0, BAG_LINE, owner)[:2]:
        print("       ", {k: d.get(k) for k in ("Own", "Added", "Removed", "Moved", "Counted", "Worn", "Same")})
    time.sleep(3)
    here, there = bag(A, owner), bag(H, owner)
    gaps = [f"{uid} : invite {here.get(uid)} | host {there.get(uid)} | attendu {reference.get(uid)}"
            for uid in sorted(set(here) | set(there) | set(reference)) if not here.get(uid) == there.get(uid) == reference.get(uid)]
    check(f"{what} : rien perdu, rien double : le sac est le meme chez l'invite, chez l'host, et celui que l'host avait "
          f"({len(gaps)} ecart(s))", not gaps)
    for g in gaps[:10]:
        print("       ", g)
    check(f"{what} : une seule demande ({len(said(t0, ASK_LINE, owner))})", len(said(t0, ASK_LINE, owner)) == 1)
    check(f"{what} : pas de rechargement de carte pour un sac", not lines(t0, RELOAD_LINE))
    check(f"{what} : memes nombres a la fin (host {sums(H)} | invite {sums(A)})", eventually(equal, timeout=10))


def r4(ctx):
    h = ctx["h"]
    one, pile = give(h, "bucket"), give(h, FILL, 5)
    if not check("R4 mise en place : l'invite voit le seau et les 5 cailloux dans le sac de l'host, nombres egaux",
                 eventually(lambda: one in bag(A, h) and bag(A, h) == bag(H, h), timeout=15) and eventually(equal, timeout=10)):
        return
    reference = bag(H, h)
    idle(A)
    t0 = now()
    local(A, f'var c = EClass._map.charas.Find(x => x.uid == {h}); c.RemoveThing(c.things.Find(x => x.uid == {one})); '
             f'c.things.Find(x => x.uid == {pile}).Num = 2;')
    mine = bag(A, h)
    check(f"R4 l'ecart existe chez l'invite seulement (seau {mine.get(one)}, cailloux {mine.get(pile)})",
          one not in mine and mine.get(pile, ("", 0))[1] == 2 and bag(H, h) == reference)
    bag_repaired("R4", h, t0, reference)
    seen = snapshot(A)
    check("R4 le seau revenu n'est qu'a un endroit chez l'invite (pas au sol, pas dans un autre sac)",
          one not in seen["things"] and [k[0] for k in seen["bags"] if k[1] == one] == [h])


def r5(ctx):
    a = ctx["a"]
    one, pile, ghost = give(a, "bucket"), give(a, FILL, 5), give(a, "bucket")
    if not check("R5 mise en place : l'invite a les deux seaux et les 5 cailloux dans son sac, nombres egaux",
                 eventually(lambda: ghost in bag(A, a) and bag(A, a) == bag(H, a), timeout=15) and eventually(equal, timeout=10)):
        return
    idle(A)
    t0 = now()
    local(A, f'EClass.pc.RemoveThing(EClass.pc.things.Find(x => x.uid == {one})); EClass.pc.things.Find(x => x.uid == {pile}).Num = 2;')
    # Card.RemoveThing says nothing to anyone: the guest keeps a bucket the host no longer has
    ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {a}); c.RemoveThing(c.things.Find(x => x.uid == {ghost})); return "ok";')
    reference = bag(H, a)
    mine = bag(A, a)
    if not check(f"R5 l'ecart existe : chez l'invite un seau en moins, 2 cailloux, un seau fantome ({len(mine)} / {len(reference)} objets)",
                 one not in mine and mine.get(pile, ("", 0))[1] == 2 and ghost in mine and ghost not in reference and one in reference):
        return
    time.sleep(14)
    # depuis le journal du 6 octobre : un sac qui differe n'avertit plus, l'host nomme les cartes (une fois par 5 min)
    named = [d for d in lines(t0, BAG_DIFF_LINE) if int(d.get("Uid", 0)) == a]
    quiet = not [d for d in lines(t0, GUEST_LINE)]
    check(f"R5 sous-option eteinte : pas d'avertissement, l'host nomme l'ecart ({[d.get('Diff') for d in named]}), "
          "aucune demande, le sac de l'invite n'a pas bouge",
          bool(named) and str(ghost) in str(named[0].get("Diff")) and quiet and not said(t0, ASK_LINE, a) and bag(A, a) == mine)
    ev(A, OWN.format("true"))
    try:
        idle(A)
        bag_repaired("R5 sous-option allumee", a, t0, reference)
        seen = snapshot(A)
        check("R5 le seau fantome a quitte le jeu de l'invite (l'host ne l'a pas) : ni dans un sac ni au sol",
              ghost not in seen["things"] and not [k for k in seen["bags"] if k[1] == ghost])
        check("R5 le seau retire est revenu, a un seul endroit", [k[0] for k in seen["bags"] if k[1] == one] == [a] and one not in seen["things"])
    finally:
        ev(A, OWN.format("false"))


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
        for step in (r1, r2, r3, r4, r5):
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
