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


def spawn_wild(ctx, key):
    """un animal sauvage a cote de l'invite, vu des deux jeux"""
    a = ctx["a"]
    species = next(s for s in SPECIES if ev(H, f'EClass.sources.charas.map.ContainsKey("{s}").ToString()') == "True")
    uid = int(ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {a}); var c = CharaGen.Create("{species}"); '
                    'EClass._zone.AddCard(c, g.pos.GetNearestPoint(allowChara: false)); return c.uid.ToString();'))
    wait(lambda: ev(A, f'(EClass._map.charas.Find(x => x.uid == {uid}) != null).ToString()') == "True", "l'invite voit l'animal", timeout=30)
    ctx[key] = uid
    return uid


def owned_by_guest(ctx, uid, what):
    a, h = ctx["a"], ctx["h"]
    check(f"{what} : dans le groupe chez l'host, une fois", eventually(lambda: info(H, uid) is not None and info(H, uid)[3] == 1, timeout=15))
    check(f"{what} : il appartient a l'invite chez l'host", info(H, uid) is not None and info(H, uid)[2] == a)
    check(f"{what} : pareil chez l'invite", eventually(lambda: info(A, uid) is not None and info(A, uid)[3] == 1 and info(A, uid)[2] == a, timeout=15))
    walk_away(A)
    check(f"{what} : il suit l'invite, pas l'host", eventually(lambda: 0 <= dist(H, uid, a) <= 4, timeout=30) and dist(H, uid, h) > 4)
    walk_away(A, dx=-8)
    time.sleep(3)


FULL = 'EClass._map.things.FirstOrDefault(t => t.trait is TraitMonsterBall && (t.trait as TraitMonsterBall).chara != null)'
HELD = 'EClass.pc.things.Find(t => t.trait is TraitMonsterBall && (t.trait as TraitMonsterBall).chara != null)'


def r7(ctx):
    """boule a monstre : l'invite capture un animal puis le relache, il est a lui et le suit"""
    a = ctx.setdefault("a", state(A)["pc"]["uid"])
    ctx.setdefault("h", state(H)["pc"]["uid"])
    known = ctx.get("u", 0)
    uid = spawn_wild(ctx, "ball")
    # une boule assez forte dans le sac de l'invite, un animal affaibli (la capture demande peu de vie)
    ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {a}); g.AddThing(ThingGen.Create("monsterball", -1, 100)); '
          f'var c = EClass._map.charas.Find(x => x.uid == {uid}); c.hp = 1; "ok"')
    wait(lambda: ev(A, '(EClass.pc.things.Find("monsterball") != null).ToString()') == "True", "la boule arrive dans le sac", timeout=20)
    time.sleep(2)
    # le lancer du jeu (ce que fait le clic "lancer" : ACT.Throw.Perform)
    r = ev(A, f'var b = EClass.pc.things.Find("monsterball"); var c = EClass._map.charas.Find(x => x.uid == {uid}); '
              'ACT.Throw.target = b; ACT.Throw.Perform(EClass.pc, c, c.pos); return "lance";')
    log(f"capture : {r}")
    caught = eventually(lambda: ev(H, f'({FULL} != null).ToString()') == "True", timeout=20)
    check("l'invite lance la boule : l'animal est dedans (vu de l'host)", caught)
    # il va la ramasser
    wait(lambda: ev(A, f'({FULL} != null).ToString()') == "True", "l'invite voit la boule pleine", timeout=20)
    ev(A, f'var b = {FULL}; EClass.pc.SetAIImmediate(new AI_Goto(b.pos.Copy(), 0)); "ok"')
    wait(lambda: ev(A, f'var b = {FULL}; return (b == null || EClass.pc.pos.Distance(b.pos) <= 1).ToString();') == "True", "l'invite rejoint la boule", timeout=30)
    ev(A, f'var b = {FULL}; EClass.pc.Pick(b); "ok"')
    wait(lambda: ev(A, f'({HELD} != null).ToString()') == "True", "la boule pleine est dans son sac", timeout=20)
    time.sleep(2)
    # et la relance a cote de lui
    ev(A, f'var b = {HELD}; var p = EClass.pc.pos.GetNearestPoint(false, false); ACT.Throw.target = b; '
          'ACT.Throw.Perform(EClass.pc, null, p); return "relache";')
    mine = (f'EClass._map.charas.LastOrDefault(x => x.IsPCParty && x.GetInt("emp_owner") == {a} && '
            f'!x.GetBool("remote_chara") && x.uid != {known})')
    out = eventually(lambda: ev(H, f'({mine} != null).ToString()') == "True", timeout=20)
    check("il relache l'animal : un nouveau compagnon de l'invite chez l'host", out)
    got = int(ev(H, f'var c = {mine}; return (c == null ? 0 : c.uid).ToString();'))
    ctx["ball"] = got
    owned_by_guest(ctx, got, "boule a monstre")


def r8(ctx):
    """animal achete : celui que le marchand vend n'existe que chez l'invite, il arrive chez l'host et le suit"""
    ctx.setdefault("a", state(A)["pc"]["uid"])
    ctx.setdefault("h", state(H)["pc"]["uid"])
    species = next(s for s in SPECIES if ev(H, f'EClass.sources.charas.map.ContainsKey("{s}").ToString()') == "True")
    before = int(ev(H, 'EClass.pc.party.members.Count.ToString()'))
    # ce que fait le "oui" du dialogue du marchand d'esclaves (DramaCustomSequence, etape _buySlaveConfirm) : le
    # personnage de sa liste, fabrique dans le jeu de l'acheteur, est pose sur la carte puis recrute
    r = ev(A, f'var tc = CharaGen.Create("{species}"); tc.c_altName = "achete"; '
              'EClass._zone.AddCard(tc, EClass.pc.pos.GetNearestPoint()); tc.MakeAlly(); tc.SetInt(100, 1); return tc.uid.ToString();')
    log(f"achat : personnage local {r}")
    arrived = eventually(lambda: int(ev(H, 'EClass.pc.party.members.Count.ToString()')) == before + 1, timeout=20)
    check("l'animal achete par l'invite arrive chez l'host", arrived)
    got = int(ev(H, 'var c = EClass.pc.party.members.LastOrDefault(x => x.c_altName == "achete"); return (c == null ? 0 : c.uid).ToString();'))
    check("avec un numero de ce monde", 0 < got < 0x40000000)
    ctx["bought"] = got
    # le dialogue de Fiama marque son animal juste apres l'avoir recrute (DramaOutcome.fiama_pet : SetInt(100, 1))
    check("la marque posee juste apres le recrutement (celle de l'animal de Fiama) arrive chez l'host",
          ev(H, f'EClass.game.cards.globalCharas.Find({got}).GetInt(100).ToString()') == "1")
    owned_by_guest(ctx, got, "animal achete")
    check("chez l'invite il n'existe qu'une fois (pas de double local)",
          eventually(lambda: ev(A, 'EClass._map.charas.Count(c => c.c_altName == "achete").ToString()') == "1", timeout=15))


def r9(ctx):
    """monture : l'invite monte un habitant de la base, il entre dans le groupe a son nom"""
    a = ctx.setdefault("a", state(A)["pc"]["uid"])
    ctx.setdefault("h", state(H)["pc"]["uid"])
    uid = spawn_wild(ctx, "mount")
    # un habitant de la base hors du groupe : recrute puis laisse par l'host, comme dans R1
    ev(H, f'EClass._map.charas.Find(x => x.uid == {uid}).MakeAlly(false); "ok"')
    wait(lambda: info(A, uid) is not None and info(A, uid)[3] == 1, "l'invite le voit dans le groupe", timeout=20)
    ev(H, f'EClass.pc.party.RemoveMember(EClass._map.charas.Find(x => x.uid == {uid})); "ok"')
    wait(lambda: info(A, uid) is not None and info(A, uid)[3] == 0, "il est sorti du groupe", timeout=20)
    time.sleep(2)
    # l'aptitude "monter" du jeu (celle de la barre d'actions), sur la case de l'habitant
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); EClass.pc.Teleport(c.pos.GetNearestPoint(allowChara: false), true, true); "ok"')
    time.sleep(2)
    r = ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); EClass.pc.UseAbility(ACT.Create(ABILITY.ActRide), c, c.pos); return EClass.pc.ride == null ? "pas monte" : "monte";')
    log(f"monture : {r}")
    check("monture : dans le groupe chez l'host, une fois", eventually(lambda: info(H, uid)[3] == 1, timeout=15))
    check("monture : elle appartient a l'invite chez l'host", eventually(lambda: info(H, uid)[2] == a, timeout=10))
    check("monture : pareil chez l'invite", eventually(lambda: info(A, uid)[3] == 1 and info(A, uid)[2] == a, timeout=15))
    check("l'host voit l'invite monte dessus",
          eventually(lambda: ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {a}); return (g.ride != null && g.ride.uid == {uid}).ToString();') == "True", timeout=15))
    # la meme aptitude sur sa propre case : il descend
    ev(A, 'EClass.pc.UseAbility(ACT.Create(ABILITY.ActRide), EClass.pc, EClass.pc.pos); "ok"')
    check("il descend : l'host le voit a pied",
          eventually(lambda: ev(H, f'(EClass._map.charas.Find(x => x.uid == {a}).ride == null).ToString()') == "True", timeout=15))
    time.sleep(2)


def r10(ctx):
    """brosse : l'invite brosse un animal qui l'apprecie, il devient son compagnon"""
    a = ctx.setdefault("a", state(A)["pc"]["uid"])
    ctx.setdefault("h", state(H)["pc"]["uid"])
    uid = spawn_wild(ctx, "tame")
    # une brosse dans le sac de l'invite ; un animal qui l'apprecie deja assez pour le suivre (le domptage
    # demande une affinite haute) et moins fort que le charisme du dompteur : celui de l'invite, monte ici ;
    # celui de l'host reste trop bas (le jeu lisait le charisme du joueur local, donc celui de l'host)
    ev(H, f'var g = EClass._map.charas.Find(x => x.uid == {a}); g.AddThing(ThingGen.Create("brush")); '
          f'var c = EClass._map.charas.Find(x => x.uid == {uid}); c._affinity = 200; g.elements.SetBase(77, 40); "ok"')
    wait(lambda: ev(A, '(EClass.pc.things.Find("brush") != null).ToString()') == "True", "la brosse arrive dans le sac", timeout=20)
    log("avant : " + ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); var g = EClass._map.charas.Find(x => x.uid == {a}); '
                           'return "domptable=" + TraitToolBrush.IsTamePossible(c) + " affinite=" + c.affinity.CanInvite() + '
                           '" meilleur attribut=" + c.GetBestAttribute() + " charisme host=" + EClass.pc.CHA + " invite=" + g.CHA;'))
    # il va a cote, prend la brosse en main et brosse : l'action de la brosse (TraitToolBrush.TrySetHeldAct)
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); EClass.pc.Teleport(c.pos.GetNearestPoint(allowChara: false), true, true); "ok"')
    time.sleep(2)
    r = ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); EClass.pc.HoldCard(EClass.pc.things.Find("brush")); '
              'EClass.pc.SetAI(new AI_TendAnimal { target = c }); return "brosse";')
    log(f"brosse : {r}")
    tamed = eventually(lambda: info(H, uid) is not None and info(H, uid)[3] == 1, timeout=60)
    check("l'invite brosse l'animal : il rejoint le groupe (vu de l'host)", tamed)
    owned_by_guest(ctx, uid, "brosse")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {}
    # R9 avant R7 et R8 : "monter" prend le dernier personnage de la case visee, et les compagnons que l'invite
    # gagne ensuite le suivent jusque sur cette case
    steps = [r1, r2, r3, r4, r5, r6, r9, r7, r8, r10]
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
