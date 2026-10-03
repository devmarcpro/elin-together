"""Compagnons recrutes par les vrais chemins du jeu, cote invite. Test court (host + 1 client a la Prairie).

    python _tools/mp_test.py
    python _tools/recruit_suite.py      # ~3 minutes, finit a la Prairie

Signale par l'utilisateur le 2026-10-03 (vraie partie a deux PC, lui invite) : "les compagnons ne suivent pas les
joueurs invites qui les ont invites". Les suites companion et party ne recrutent que par Chara.MakeAlly ; le
dialogue "rejoindre le groupe" d'un habitant de la base appelle Party.AddMemeber, que le mod ne transmettait pas.

R1  un habitant de la base, hors du groupe, connu des deux jeux
R2  l'invite lui demande de rejoindre le groupe (ce que fait le dialogue) : il est dans le groupe chez l'host
    aussi, et il appartient a l'invite
R3  il suit l'invite, pas l'host
R4  l'invite part seul a Vernis : l'habitant part avec lui et le suit la-bas
R5  l'invite rentre : l'habitant revient a cote de lui, une seule fois dans le groupe, toujours a lui
R6  l'invite le renvoie du groupe : il n'y est plus chez personne et n'appartient plus a l'invite ;
    l'host le reprend : il est a l'host
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from companion_suite import SPECIES, alive, dist, info, walk_away  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually,  # noqa: E402
                          move, scan_logs, wait)

H, A = 27551, 27552

# ce que fait le choix "rejoindre le groupe" du dialogue d'un habitant (DramaCustomSequence, etape _joinParty)
JOIN = ('var c = EClass._map.charas.Find(x => x.uid == __U__); if (c == null) return "pas vu"; '
        'if (!c.trait.CanJoinPartyResident) return "refuse"; EClass.pc.party.AddMemeber(c, showMsg: true); return "ok";')
# et le choix "quitter le groupe" (etape _leaveParty)
LEAVE = ('var c = EClass._map.charas.Find(x => x.uid == __U__); if (c == null) return "pas vu"; '
         'EClass.pc.party.RemoveMember(c); return "ok";')


def r1(ctx):
    """un habitant de la base, hors du groupe, connu des deux jeux"""
    ctx["a"], ctx["h"] = state(A)["pc"]["uid"], state(H)["pc"]["uid"]
    species = next(s for s in SPECIES if ev(H, f'EClass.sources.charas.map.ContainsKey("{s}").ToString()') == "True")
    # en trois temps, comme dans une vraie partie : il apparait, l'host le recrute, puis le laisse a la base
    uid = int(ev(H, f'var c = CharaGen.Create("{species}"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(allowChara: false)); '
                    'return c.uid.ToString();'))
    ctx["u"] = uid
    wait(lambda: ev(A, f'(EClass._map.charas.Find(x => x.uid == {uid}) != null).ToString()') == "True", "l'invite voit l'animal", timeout=30)
    ev(H, f'EClass._map.charas.Find(x => x.uid == {uid}).MakeAlly(false); "ok"')
    wait(lambda: info(A, uid) is not None and info(A, uid)[3] == 1, "l'invite le voit dans le groupe", timeout=20)
    ev(H, f'EClass.pc.party.RemoveMember(EClass._map.charas.Find(x => x.uid == {uid})); "ok"')
    seen = eventually(lambda: info(A, uid) is not None and info(A, uid)[3] == 0 and info(A, uid)[1] != "", timeout=20)
    check(f"un habitant ({species}) hors du groupe, vu par les deux jeux", seen and info(H, uid)[3] == 0)
    check("il habite la base", ev(H, f'(EClass.game.cards.globalCharas.Find({uid}).homeBranch != null).ToString()') == "True")


def r2(ctx):
    """l'invite lui demande de rejoindre le groupe : dans le groupe des deux cotes, et a l'invite"""
    u, a = ctx["u"], ctx["a"]
    # l'invite va le voir, comme pour lui parler
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {u}); EClass.pc.Teleport(c.pos.GetNearestPoint(allowChara: false), true, true); "ok"')
    time.sleep(2)
    r = ev(A, JOIN.replace("__U__", str(u)))
    check(f"l'invite fait le choix du dialogue ({r})", r == "ok")
    check("chez l'host : dans le groupe, une fois", eventually(lambda: info(H, u)[3] == 1, timeout=10))
    check("chez l'host : il appartient a l'invite", info(H, u)[2] == a)
    check("chez l'invite : dans le groupe, une fois, et a lui", eventually(lambda: info(A, u)[3] == 1 and info(A, u)[2] == a, timeout=10))


def r3(ctx):
    """il suit l'invite, pas l'host"""
    u, a, h = ctx["u"], ctx["a"], ctx["h"]
    walk_away(A)
    check("l'invite s'eloigne : l'habitant le suit (vu de l'host)", eventually(lambda: 0 <= dist(H, u, a) <= 4, timeout=30))
    check("il s'est eloigne de l'host", dist(H, u, h) > 4)


def r4(ctx):
    """l'invite part seul a Vernis : l'habitant part avec lui et le suit"""
    u, a = ctx["u"], ctx["a"]
    move(A, VERNIS)
    wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
    time.sleep(3)
    dismiss_dialogs(A)
    there = eventually(lambda: info(A, u) is not None and info(A, u)[0] == VERNIS and info(A, u)[1] != "", timeout=20)
    check("a Vernis chez l'invite : l'habitant est la, avec lui", there and 0 <= dist(A, u, a) <= 5)
    check("chez l'host : il a quitte la carte", info(H, u)[1] == "")
    walk_away(A, dx=-8)
    check("il suit l'invite a Vernis", eventually(lambda: 0 <= dist(A, u, a) <= 4, timeout=30))


def r5(ctx):
    """l'invite rentre : l'habitant revient avec lui"""
    u, a = ctx["u"], ctx["a"]
    move(A, HOME)
    both_joined(H, A, HOME)
    time.sleep(4)
    dismiss_dialogs(A)
    check("chez l'host : l'habitant est revenu a cote de l'invite",
          eventually(lambda: info(H, u)[1] != "" and 0 <= dist(H, u, a) <= 5, timeout=20))
    check("une seule fois dans le groupe, toujours a l'invite", info(H, u)[3] == 1 and info(H, u)[2] == a)
    time.sleep(5)
    check("il existe toujours des deux cotes", alive(H, u) and alive(A, u))


def r6(ctx):
    """l'invite le renvoie, l'host le reprend : il est a l'host"""
    u, a, h = ctx["u"], ctx["a"], ctx["h"]
    r = ev(A, LEAVE.replace("__U__", str(u)))
    check(f"l'invite le renvoie du groupe ({r})", r == "ok")
    check("il n'est plus dans le groupe, chez personne", eventually(lambda: info(H, u)[3] == 0 and info(A, u)[3] == 0, timeout=10))
    check("il n'appartient plus a l'invite", eventually(lambda: info(H, u)[2] == 0, timeout=10))
    r = ev(H, JOIN.replace("__U__", str(u)))
    check(f"l'host le prend dans le groupe ({r})", r == "ok" and eventually(lambda: info(A, u)[3] == 1, timeout=10))
    check("il est a l'host (aucun proprietaire) des deux cotes", info(H, u)[2] == 0 and eventually(lambda: info(A, u)[2] == 0, timeout=10))
    # (le monde de l'host est en pause sans clic de son joueur : "il suit l'host" ne se teste pas par le pont)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {}
    steps = [r1, r2, r3, r4, r5, r6]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
            for name, port in (("host", H), ("A", A)):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', port)}")
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
