"""Un joueur n'est jamais deplace sans l'avoir voulu (C1 et C3 de dev/PLAN_invites_tp_sur_host.md). Deux fenetres.

    python _tools/mp_test.py             # une fois : host + 1 client dans la Prairie
    python _tools/place_suite.py         # 5 a 8 minutes, relancable (finit avec tout le monde a la Prairie)

P1  A se tient loin de l'host ; l'host part a Vernis : A n'a pas bouge (chez lui, et sur la copie de l'host)
P2  l'host revient : A n'a pas bouge (meme case chez lui et chez l'host), l'host est ailleurs
P3  l'host est a Vernis ; A sort de la Prairie par le bord puis entre a Vernis : il arrive par l'entree
    (la ou le jeu le met en solo), pas sur l'host
P4  l'host marche sur la carte du monde ; A sort de Vernis par le bord : il arrive sur la case de Vernis,
    une case ou un joueur peut se tenir, pas sur l'host
P5  (journal reel du 2026-10-06, jamais lance) A part seul a Vernis, l'host change de carte, A revient chez
    l'host : sur une case de la carte de l'host, des deux cotes ; pas d'exception dans le journal (scan final)
P6  (idem) l'host se reveille sur la carte du monde pendant que A tient la Prairie : il reste sur la carte du
    monde, A n'est pas rappele, puis A le rejoint sur une case valide. ROUGE tant que la correction notee dans
    dev/PLAN_journal_reel_placement.md n'est pas faite
P7  (idem) A seul sur la carte du monde, l'host sort de la Prairie et y rentre trois fois : A n'est ni
    recharge ni deplace
P8  (retour 21 du 2026-10-07, jamais lance) A lit sur la carte de l'host, l'host quitte la carte pendant la lecture :
    moins de 5 secondes apres que A tient la carte, sa lecture n'attend plus personne ; elle finit une seule fois
    (ou s'arrete sans rien consommer) et A peut marcher. Un livre de competence (5 tours), puis un grimoire long.
    Notes : dev/PLAN_bloque_lecture.md

Ce que le banc ne joue pas comme un joueur :
- P8 : la lecture est posee par `pc.SetAI(new AI_Read)` (ce que fait le clic « lire »), le grimoire est rendu long
  par son niveau et lu en `godMode` (aucun echec de lecture) ; le livre de competence est si court que l'host peut
  l'avoir fini avant de partir : seul le grimoire prouve le passage de main en pleine lecture ;
- l'host change de carte par `pc.MoveZone(zone)` (P1, P2, debut de P3), pas par une sortie a pied ;
- A et l'host s'eloignent par teleportation (`pc.Teleport`), pas en marchant ;
- A entre a Vernis par `player.EnterLocalZone(case de Vernis)` sans avoir marche jusqu'a cette case sur la carte
  du monde (les sorties, elles, passent par `player.ExitBorder()`, le vrai chemin du bord de carte) ;
- pas d'escalier ni de porte : seulement bord de carte, ville et carte du monde ;
- un seul invite : il tient toujours la carte. Le cas du 2e invite, qui ne la tient pas, est dans
  trio_place_suite.py (trois fenetres).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, move,  # noqa: E402
                          scan_logs, wait, zone_uid)

H, A = 27551, 27552

ENTER = ('var z = EClass.game.spatials.Find({uid}); var em = EClass.scene.elomap; '
         'EClass.player.EnterLocalZone(new Point(z.x - em.minX, z.y - em.minY)); "ok"')


def pc_pos(port):
    s = state(port)["pc"]
    return s["x"], s["z"]


def xz(text):
    x, z = text.split(",")
    return int(x), int(z)


def seen_at(port, uid):
    """Case du personnage `uid` sur la carte active de `port`, None s'il n'y est pas."""
    res = ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); c == null ? "" : c.pos.x + "," + c.pos.z')
    return xz(res) if res else None


def copy_at(port, uid):
    """Case du personnage `uid` tel que `port` le connait, meme hors de sa carte."""
    return xz(ev(port, f'var c = EClass.game.cards.globalCharas.Find({uid}); c.pos.x + "," + c.pos.z'))


def dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def step_away(port, dx, dz):
    """Raccourci du banc : le joueur se teleporte a (dx, dz) cases, sur une case libre."""
    ev(port, f'var p = EClass.pc.pos.Copy(); p.x += {dx}; p.z += {dz}; '
             'EClass.pc.Teleport(p.GetNearestPoint(false, false) ?? EClass.pc.pos, true, true); "ok"')
    time.sleep(2)
    return pc_pos(port)


def region_uid(port):
    return int(ev(port, 'EClass.world.region.uid.ToString()'))


def tile_of(port, uid):
    """Case d'une zone sur la carte du monde."""
    return xz(ev(port, f'var z = EClass.game.spatials.Find({uid}); var em = EClass.scene.elomap; '
                       '(z.x - em.minX) + "," + (z.y - em.minY)'))


def walkable_here(port):
    """La case du joueur : pas bloquee (la regle de Chara.CanMoveTo), pas de l'eau."""
    return ev(port, '(!EClass.pc.pos.cell.blocked && !EClass.pc.pos.IsWater).ToString()') == "True"


def p1(ctx):
    ctx["a"] = state(A)["pc"]["uid"]
    spot = step_away(A, 9, 4)
    ctx["spot"] = spot
    check(f"depart : A est loin de l'host ({dist(spot, pc_pos(H))} cases)", dist(spot, pc_pos(H)) > 3)
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=180)
    stayed = eventually(client_settled(A, HOME, True), timeout=30)
    check("l'host part : A reste a la Prairie", stayed)
    check(f"A n'a pas bouge chez lui ({spot} -> {pc_pos(A)})", pc_pos(A) == spot)
    check(f"la copie de A chez l'host est a la meme case ({copy_at(H, ctx['a'])})", copy_at(H, ctx["a"]) == spot)


def p2(ctx):
    ctx.setdefault("a", state(A)["pc"]["uid"])
    spot = ctx.get("spot") or pc_pos(A)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    both_joined(H, A, HOME)
    time.sleep(3)
    seen = seen_at(H, ctx["a"])
    check(f"l'host revient : A n'a pas bouge (attendu {spot}, chez A {pc_pos(A)}, chez l'host {seen})",
          pc_pos(A) == spot and seen == spot)
    check(f"l'host est ailleurs sur la carte (a {dist(spot, pc_pos(H))} cases)", dist(spot, pc_pos(H)) > 3)
    shot("p2-A", A)


def p3(ctx):
    ctx.setdefault("a", state(A)["pc"]["uid"])
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=180)
    wait(client_settled(A, HOME, True), "A garde la Prairie", timeout=30)
    region = region_uid(A)
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(A, region, True), "A sur la carte du monde", timeout=120)
    # en solo le jeu remet le joueur a la case ou il a quitte sa derniere carte (Zone.GetSpawnPos, lastZonePos),
    # ramenee dans les limites de la carte ; sinon au bord par ou il entre
    last = ev(A, 'EClass.player.lastZonePos == null ? "" : EClass.player.lastZonePos.x + "," + EClass.player.lastZonePos.z')
    # l'host se tient loin de cette case : sinon "a l'entree" et "sur l'host" ne se distinguent pas
    if last:
        lx, lz = xz(last)
        ev(H, f'var t = new Point({lx}, {lz}).Clamp(true); var p = t.Copy(); '
              'p.x += t.x + 10 <= EClass._map.bounds.maxX ? 10 : -10; '
              'EClass.pc.Teleport(p.GetNearestPoint(false, false) ?? p, true, true); "ok"')
        expected = xz(ev(H, f'var t = new Point({lx}, {lz}).Clamp(true); t.x + "," + t.z'))
    else:
        step_away(H, 10, 0)
        expected = None
    time.sleep(2)
    ev(A, ENTER.format(uid=VERNIS))
    both_joined(H, A, VERNIS)
    time.sleep(3)
    mine, seen, host = pc_pos(A), seen_at(H, ctx["a"]), pc_pos(H)
    edge = int(ev(A, 'var b = EClass._map.bounds; var p = EClass.pc.pos; '
                     'System.Math.Min(System.Math.Min(p.x - b.x, b.maxX - p.x), System.Math.Min(p.z - b.z, b.maxZ - p.z)).ToString()'))
    check(f"A entre a Vernis : meme case chez lui et chez l'host ({mine} / {seen})", seen == mine)
    check(f"A n'est pas pose sur l'host (a {dist(mine, host)} cases, host en {host})", dist(mine, host) > 3)
    check(f"A arrive par l'entree : pres de {expected} (case de sortie de sa derniere carte) ou au bord (a {edge} cases du bord)",
          (expected is not None and dist(mine, expected) <= 2) or edge <= 2)
    shot("p3-A", A)


def p4(ctx):
    ctx.setdefault("a", state(A)["pc"]["uid"])
    if zone_uid(H) != VERNIS or zone_uid(A) != VERNIS:
        raise RuntimeError("P4 part de P3 : l'host et A a Vernis")
    region = region_uid(H)
    ev(H, 'EClass.player.ExitBorder(); "ok"')
    wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=180)
    wait(client_settled(A, VERNIS, True), "A garde Vernis", timeout=30)
    town = tile_of(H, VERNIS)
    step_away(H, 6, 0)
    check(f"l'host s'est eloigne de Vernis sur la carte du monde ({dist(pc_pos(H), town)} cases)", dist(pc_pos(H), town) > 2)
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    both_joined(H, A, region)
    time.sleep(3)
    mine, seen = pc_pos(A), seen_at(H, ctx["a"])
    check(f"A sort de Vernis : il est sur la case de Vernis {town} (chez lui {mine}, chez l'host {seen})",
          mine == town and seen == town)
    check("la case de A est praticable (pas bloquee, pas de l'eau), chez lui et chez l'host",
          walkable_here(A) and ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {ctx["a"]}); '
                                     '(c != null && !c.pos.cell.blocked && !c.pos.IsWater).ToString()') == "True")
    check(f"A n'est pas pose sur l'host (a {dist(mine, pc_pos(H))} cases)", dist(mine, pc_pos(H)) > 2)
    shot("p4-A", A)


def on_tile(port, uid):
    """Le personnage `uid` est une seule fois sur la carte active de `port`, sur une case de cette carte, et dans
    la liste de cette case (un personnage a moitie pose est dans la liste de la carte et sur aucune case)."""
    return ev(port, f'var l = EClass._map.charas.Where(x => x.uid == {uid}).ToList(); '
                    '(l.Count == 1 && l[0].pos.IsValid && l[0].pos.IsInBounds && l[0].pos.detail != null && '
                    'l[0].pos.detail.charas.Contains(l[0])).ToString()') == "True"


def game_id(port):
    """Change quand le jeu de `port` recharge le monde (retour chez l'host : OnSaveDataProbe refait core.game)."""
    return ev(port, 'System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(EClass.game).ToString()')


def host_on_own_map(port):
    return ev(port, '(EClass.pc.currentZone == EClass._zone && !EClass.player.simulatingZone && '
                    'EClass.pc.pos.IsValid && EClass.pc.pos.IsInBounds).ToString()') == "True"


def p5(ctx):
    """Journal reel du 2026-10-06, defaut 1 (garde-fou) : A part seul sur une autre carte, l'host change de carte,
    A revient chez l'host : il est sur une case de la carte de l'host, des deux cotes."""
    back_home()
    ctx["a"] = state(A)["pc"]["uid"]
    region = region_uid(A)
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(A, region, True), "A sur la carte du monde", timeout=120)
    ev(A, ENTER.format(uid=VERNIS))
    wait(client_settled(A, VERNIS, True), "A seul a Vernis", timeout=180)
    step_away(A, 12, 9)
    ev(H, 'EClass.player.ExitBorder(); "ok"')
    wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=180)
    step_away(H, 5, 0)
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    both_joined(H, A, region)
    time.sleep(3)
    mine, seen = pc_pos(A), seen_at(H, ctx["a"])
    check(f"A revient : sur une case de la carte de l'host, chez lui ({mine}) et chez l'host ({seen})",
          on_tile(A, ctx["a"]) and on_tile(H, ctx["a"]))
    check(f"A revient : meme case des deux cotes ({mine} / {seen})", mine == seen)
    shot("p5-A", A)


def p6(ctx):
    """Journal reel, defaut 1 (cause) : tous les invites sont ailleurs, l'host se reveille sur la carte du monde
    et le jeu lui fait faire le tour de ses bases (Player.SimulateFaction) ; la Prairie est tenue par A.
    Raccourci du banc : pas de nuit, la fonction du reveil est appelee directement, avec du retard pose a la main
    sur la Prairie (sans retard le jeu saute la base).
    ROUGE tant que la correction notee dans dev/PLAN_journal_reel_placement.md (SleepSynchronizationContext,
    OnSimulateFaction) n'est pas faite : l'host regarde la Prairie sans y etre."""
    back_home()
    ctx["a"] = state(A)["pc"]["uid"]
    host = state(H)["pc"]["uid"]
    region = region_uid(H)
    spot = step_away(A, 9, 4)
    ev(H, 'EClass.player.ExitBorder(); "ok"')
    wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=180)
    wait(client_settled(A, HOME, True), "A garde la Prairie", timeout=30)
    ev(H, f'EClass.game.spatials.Find({HOME}).pendingSimHours = 5; EClass.player.SimulateFaction(); "ok"')
    time.sleep(8)
    check(f"reveil de l'host : il est toujours sur la carte du monde (zone {zone_uid(H)}, attendu {region})",
          zone_uid(H) == region)
    check("reveil de l'host : son personnage est sur la carte qu'il regarde, sur une case de cette carte",
          host_on_own_map(H) and on_tile(H, host))
    check(f"A n'a pas ete rappele : il tient la Prairie, sur sa case ({spot} -> {pc_pos(A)})",
          client_settled(A, HOME, True)() and pc_pos(A) == spot)
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    both_joined(H, A, region)
    time.sleep(3)
    check(f"A rejoint l'host : sur une case de sa carte, des deux cotes ({pc_pos(A)} / {seen_at(H, ctx['a'])})",
          on_tile(A, ctx["a"]) and on_tile(H, ctx["a"]) and pc_pos(A) == seen_at(H, ctx["a"]))


def p7(ctx):
    """Journal reel, defaut 2 : A marche seul sur sa copie de la carte du monde ; l'host sort de la Prairie et y
    rentre trois fois : A n'est ni recharge ni deplace (avant : rappele a chaque sortie de l'host).
    Raccourci du banc : l'host rentre par `player.EnterLocalZone(case de la Prairie)`."""
    back_home()
    region = region_uid(A)
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(A, region, True), "A seul sur la carte du monde", timeout=120)
    time.sleep(3)
    spot, game = pc_pos(A), game_id(A)
    for i in (1, 2, 3):
        ev(H, 'EClass.player.ExitBorder(); "ok"')
        wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=180)
        time.sleep(6)
        check(f"passage {i}, l'host est sur la carte du monde : A est toujours seul sur la sienne, meme case "
              f"({spot} -> {pc_pos(A)}), monde non recharge",
              client_settled(A, region, True)() and pc_pos(A) == spot and game_id(A) == game)
        ev(H, ENTER.format(uid=HOME))
        wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
        time.sleep(4)
        check(f"passage {i}, l'host est rentre : A n'a pas bouge ({pc_pos(A)}), monde non recharge",
              client_settled(A, region, True)() and pc_pos(A) == spot and game_id(A) == game)
    shot("p7-A", A)


def reading(port):
    """"libre", ou le compteur de la lecture en cours : negatif tant qu'elle attend le jeu qui tient la carte."""
    return ev(port, 'if (!(EClass.pc.ai is AI_Read) || !EClass.pc.ai.IsRunning) return "libre"; '
                    'var p = EClass.pc.ai.Current as AIProgress; return p == null ? "0" : p.progress.ToString();')


def within(cond, seconds, every=0.3):
    end = time.time() + seconds
    while time.time() < end:
        if cond():
            return True
        time.sleep(every)
    return cond()


def read_while_host_leaves(name, make, left, long):
    """A lit le livre que `make` fabrique (C#, laisse dans `t`) ; l'host part a Vernis pendant la lecture.
    `left` : expression C# du nombre qui reste du livre `t` (charges, ou exemplaires)."""
    back_home()
    a = state(A)["pc"]["uid"]
    book = int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {a}); {make} return c.AddThing(t, false).uid.ToString();'))
    find = f'var t = EClass.pc.things.Find(x => x.uid == {book});'
    wait(lambda: ev(A, f'{find} return (t != null).ToString();') == "True", f"{name} dans le sac de A", timeout=15)
    count = lambda: int(ev(A, f'{find} return t == null ? "0" : ({left}).ToString();'))  # noqa: E731
    before = count()
    ev(A, 'EClass.debug.godMode = true; "ok"')
    try:
        if long:
            ev(A, f'{find} EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
            held = within(lambda: reading(A).startswith("-"), 5)
            check(f"{name} : la lecture de A attend l'host ({reading(A)})", held)
            move(H, VERNIS)
        else:
            # cinq tours : l'host part d'abord, la lecture commence pendant son depart
            move(H, VERNIS)
            ev(A, f'{find} EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
        wait(client_settled(A, HOME, True), "A tient la Prairie", timeout=180, every=0.3)
        free = within(lambda: not reading(A).startswith("-"), 5)
        check(f"{name} : moins de 5 s apres le passage de main, la lecture de A n'attend plus personne ({reading(A)})", free)
        done = within(lambda: reading(A) == "libre", 120, every=1.0)
        after = count()
        check(f"{name} : la lecture est finie, une fois au plus ({before} -> {after})",
              done and after in (before, before - 1))
        log(f"{name} : " + ("lu une fois" if after == before - 1 else "arrete sans rien consommer"))
        idle = within(lambda: ev(A, 'EClass.pc.HasNoGoal.ToString()') == "True", 5)
        spot = pc_pos(A)
        for dx in (1, -1):
            ev(A, f'EClass.pc.TryMoveTowards(new Point(EClass.pc.pos.x + {dx}, EClass.pc.pos.z)); "ok"')
            if within(lambda: pc_pos(A) != spot, 3):
                break
        check(f"{name} : A est libre et marche ({spot} -> {pc_pos(A)})", idle and pc_pos(A) != spot)
    finally:
        ev(A, f'EClass.debug.godMode = false; {find} if (t != null) t.Destroy(); "ok"')
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=180)
    shot(f"p8-{name}-A", A)


def p8(ctx):
    """Retour 21 : un invite qui lisait quand l'host a pris l'escalier est reste fige (lecture retenue en attendant
    l'host, qu'on ne peut pas arreter a la main). Raccourcis du banc : voir l'en-tete."""
    read_while_host_leaves("livre", 'var t = ThingGen.Create("book_skill");', "t.Num", long=False)
    # un grimoire d'au moins 200 tours pour ce lecteur : l'host ne l'a pas fini quand il part
    read_while_host_leaves(
        "grimoire",
        'var t = ThingGen.Create("spellbook"); t.c_charges = 4; t.SetBlessedState(BlessedState.Normal); '
        'for (var lv = 100; lv < 200000 && t.trait.GetActDuration(c) < 200; lv *= 2) t.SetLv(lv);',
        "t.c_charges", long=True)


def back_home():
    """Tout le monde a la Prairie, pour pouvoir relancer."""
    if zone_uid(H) != HOME:
        if zone_uid(H) == region_uid(H):
            ev(H, ENTER.format(uid=HOME))
        else:
            move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    if not eventually(client_settled(A, HOME, False), timeout=20):
        if zone_uid(A) == region_uid(A):
            ev(A, ENTER.format(uid=HOME))
        else:
            move(A, HOME)
    both_joined(H, A, HOME)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {}
    steps = [p1, p2, p3, p4, p5, p6, p7, p8]
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

    try:
        back_home()
    except Exception as ex:  # noqa: BLE001
        print(f"    retour a la Prairie rate : {type(ex).__name__}: {ex}")

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
