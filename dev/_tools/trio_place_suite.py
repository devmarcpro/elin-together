"""TROIS FENETRES : a ne lancer qu'avec l'accord de l'utilisateur (regle du Steam Deck : deux fenetres Elin au plus).

Le 2e invite, celui qui ne tient pas la carte, n'est jamais deplace sans l'avoir voulu (C1 et C3 de
dev/PLAN_invites_tp_sur_host.md). A deux fenetres ce cas n'existe pas : le seul invite tient toujours la carte.

    python _tools/trio_place_suite.py            # relance tout (mp_test --clients 2) puis les scenarios
    python _tools/trio_place_suite.py --reuse    # sur host + 2 clients deja connectes dans la Prairie

Q1  A et B se tiennent loin de l'host et l'un de l'autre ; l'host part a Vernis : l'un garde la Prairie, l'autre
    devient son invite (son jeu recharge la carte) ; aucun des deux n'a bouge, chez lui comme chez l'autre
Q2  l'host revient : les deux sont rappeles, aucun n'a bouge (meme case chez lui et chez l'host), l'host est ailleurs ;
    au plus 2 sauvegardes de l'host pour les deux retours et son propre deplacement (A1a, emp.autosave_every pose ici)
Q3  l'host repart a Vernis ; l'invite (celui qui ne tient pas la Prairie) sort par le bord puis entre a Vernis :
    il arrive par l'entree, pas sur l'host ; celui qui tient la Prairie n'a pas bouge
Q4  (`--only q4`, a part) l'host entre dans la zone d'une quete prise en ville : le teneur ET le visiteur voient la
    question, le visiteur dit Oui et arrive, une seule fois (B4)
Q5  (`--only q5`, a part) B, avec un compagnon, part seul a Vernis et revient, puis quitte la partie et la rejoint,
    pendant que A reste : apres chaque retour A et l'host voient B et son compagnon sur la bonne case, une seule fois,
    meme apres un rechargement de la carte de A ; world_diff ne trouve aucun personnage en trop ni en moins

Ce que le banc ne joue pas comme un joueur :
- l'host change de carte par `pc.MoveZone(zone)`, pas par une sortie a pied ;
- A, B et l'host s'eloignent par teleportation (`pc.Teleport`), pas en marchant ;
- l'invite entre a Vernis par `player.EnterLocalZone(case de Vernis)` sans avoir marche jusqu'a cette case sur la
  carte du monde (sa sortie de la Prairie passe par `player.ExitBorder()`, le vrai bord de carte) ;
- qui garde la carte est decide par l'host (le premier connecte) : le banc le constate, il ne le choisit pas ;
- pas de passation en chaine (le teneur part a son tour), pas de plantage du teneur, pas de 3e invite.
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from bot import choices, click  # noqa: E402
from mp_test import ROOT, log, shot, state  # noqa: E402
from place_suite import ENTER, dist, pc_pos, region_uid, seen_at, step_away, xz  # noqa: E402
from shared_suite import A, B, H, settled, with_host  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, check, ev, move, scan_logs, wait, zone_uid  # noqa: E402
from together_suite import BOX, host_enters  # noqa: E402
from trio_suite import NAMES, handed_pair, try_wait  # noqa: E402


def host_leaves(ctx):
    """L'host part a Vernis ; renvoie (teneur, invite) de la Prairie."""
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=180)
    pair = wait(lambda: handed_pair(A, B, HOME), "l'un garde la Prairie, l'autre le rejoint", timeout=180, every=2.0)
    log(f"teneur : {NAMES[pair[0]]}, invite : {NAMES[pair[1]]}")
    time.sleep(4)
    return pair


def q1(ctx):
    for p in (A, B):
        ctx[p] = state(p)["pc"]["uid"]
    spots = {A: step_away(A, 9, 4), B: step_away(B, -8, 6)}
    ctx["spots"] = spots
    check(f"depart : A et B loin de l'host et l'un de l'autre (A {spots[A]}, B {spots[B]}, host {pc_pos(H)})",
          min(dist(spots[A], pc_pos(H)), dist(spots[B], pc_pos(H)), dist(spots[A], spots[B])) > 3)
    heir, other = host_leaves(ctx)
    ctx["heir"], ctx["other"] = heir, other
    check(f"{NAMES[heir]} garde la carte : il n'a pas bouge ({spots[heir]} -> {pc_pos(heir)})", pc_pos(heir) == spots[heir])
    check(f"{NAMES[other]} ne tient pas la carte, son jeu l'a rechargee : il n'a pas bouge ({spots[other]} -> {pc_pos(other)})",
          pc_pos(other) == spots[other])
    check(f"chez {NAMES[heir]}, {NAMES[other]} est a la meme case ({seen_at(heir, ctx[other])})",
          seen_at(heir, ctx[other]) == spots[other])
    check(f"chez {NAMES[other]}, {NAMES[heir]} est a la meme case ({seen_at(other, ctx[heir])})",
          seen_at(other, ctx[heir]) == spots[heir])
    for p in (A, B):
        shot(f"q1-{NAMES[p]}", p)


def saves(port):
    return int(ev(port, 'EClass.game.saveCount.ToString()'))


def q2(ctx):
    spots = ctx["spots"]
    # the bench saves by itself only once asked (EmpAutoHost.RequestSave falls back to a save in the frame of the
    # return otherwise); an hour keeps the periodic save out of the count
    emp.call(H, "command", {"cmd": "emp.autosave_every 3600"})
    saved0 = saves(H)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    check("l'host revient : A et B sont avec lui a la Prairie",
          try_wait(lambda: all(settled(p, HOME, away=False)() for p in (A, B)), "A et B avec l'host", 240))
    time.sleep(4)
    # a save is asked for at each return and made once, 5 s later (A1a of dev/PLAN_lenteurs_corrections.md); the game
    # saves once more when the host walks into its own base. Before: one save per return as well, so 3 here
    time.sleep(8)
    done = saves(H) - saved0
    check(f"l'host revient : au plus 2 sauvegardes pour 2 retours et son propre deplacement ({done})", done <= 2)
    host = pc_pos(H)
    for p in (A, B):
        role = "tenait la carte" if p == ctx.get("heir") else "ne tenait pas la carte"
        seen = seen_at(H, ctx[p])
        check(f"{NAMES[p]} ({role}) n'a pas bouge : attendu {spots[p]}, chez lui {pc_pos(p)}, chez l'host {seen}",
              pc_pos(p) == spots[p] and seen == spots[p])
        check(f"{NAMES[p]} n'est pas pose sur l'host (a {dist(spots[p], host)} cases)", dist(spots[p], host) > 3)
    for p in (A, B):
        shot(f"q2-{NAMES[p]}", p)


def q3(ctx):
    for p in (A, B):
        ctx.setdefault(p, state(p)["pc"]["uid"])
    heir, other = host_leaves(ctx)
    kept = pc_pos(heir)
    region = region_uid(other)
    ev(other, 'EClass.player.ExitBorder(); "ok"')
    wait(settled(other, region, away=True, guest=False), f"{NAMES[other]} sur la carte du monde", timeout=180)
    last = ev(other, 'EClass.player.lastZonePos == null ? "" : EClass.player.lastZonePos.x + "," + EClass.player.lastZonePos.z')
    expected = None
    if last:
        lx, lz = xz(last)
        ev(H, f'var t = new Point({lx}, {lz}).Clamp(true); var p = t.Copy(); '
              'p.x += t.x + 10 <= EClass._map.bounds.maxX ? 10 : -10; '
              'EClass.pc.Teleport(p.GetNearestPoint(false, false) ?? p, true, true); "ok"')
        expected = xz(ev(H, f'var t = new Point({lx}, {lz}).Clamp(true); t.x + "," + t.z'))
    else:
        step_away(H, 10, 0)
    time.sleep(2)
    ev(other, ENTER.format(uid=VERNIS))
    wait(settled(other, VERNIS, away=False), f"{NAMES[other]} avec l'host a Vernis", timeout=240)
    time.sleep(4)
    mine, seen, host = pc_pos(other), seen_at(H, ctx[other]), pc_pos(H)
    edge = int(ev(other, 'var b = EClass._map.bounds; var p = EClass.pc.pos; '
                         'System.Math.Min(System.Math.Min(p.x - b.x, b.maxX - p.x), System.Math.Min(p.z - b.z, b.maxZ - p.z)).ToString()'))
    check(f"{NAMES[other]} entre a Vernis : meme case chez lui et chez l'host ({mine} / {seen})", seen == mine)
    check(f"{NAMES[other]} n'est pas pose sur l'host (a {dist(mine, host)} cases)", dist(mine, host) > 3)
    check(f"{NAMES[other]} arrive par l'entree : pres de {expected} (case de sortie de sa derniere carte) ou au bord "
          f"(a {edge} cases du bord)", (expected is not None and dist(mine, expected) <= 2) or edge <= 2)
    check(f"{NAMES[heir]}, reste a la Prairie, n'a pas bouge ({kept} -> {pc_pos(heir)})", pc_pos(heir) == kept)


def q4(ctx):
    """B4 (PLAN_lenteurs_corrections.md), a part : `--only q4`, jamais joue encore. L'host prend une quete en ville et y
    entre : celui qui tient la ville ET celui qui la visite voient la question ; le visiteur dit Oui et arrive dans la
    zone de la quete, une seule fois"""
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    wait(lambda: all(settled(p, HOME, away=False)() for p in (A, B)), "A et B avec l'host", timeout=240, every=2.0)
    uid = {p: state(p)["pc"]["uid"] for p in (A, B)}
    _, zuid = host_enters()
    heir, other = wait(lambda: handed_pair(A, B, HOME), "l'un garde la Prairie, l'autre la visite", timeout=180, every=2.0)
    for p, role in ((heir, "tient la ville"), (other, "visite la ville")):
        check(f"{NAMES[p]} ({role}) voit la boite Oui/Non ({ev(p, BOX)!r})",
              try_wait(lambda p=p: len(choices(p)) == 2, f"boite chez {NAMES[p]}", 30))
    click(other, choices(other)[0])
    check(f"{NAMES[other]} (visiteur) dit Oui et arrive dans la zone de la quete",
          try_wait(lambda: zone_uid(other) == zuid, f"{NAMES[other]} dans la zone", 120))
    time.sleep(4)
    check(f"{NAMES[other]} n'est qu'une fois chez l'host",
          ev(H, f'EClass._map.charas.Count(c => c.uid == {uid[other]}).ToString()') == "1")


def q5(ctx):
    """Joueurs invisibles (dev/PLAN_joueurs_invisibles.md), jamais joue encore. B a un compagnon. B part seul a Vernis et
    revient, puis quitte la partie et la rejoint, pendant que A reste a la Prairie avec l'host. Apres chaque depart,
    ni A ni l'host n'ont B ou son compagnon sur la carte ; apres chaque retour, A et l'host les voient sur la case ou
    le jeu de B les a ; A recharge alors sa carte et les voit toujours ; world_diff ne trouve rien en trop ni en moins.
    Ce que le banc ne joue pas : il tourne en Debug, ou les patchs du mod ne sont jamais retires (ElinNetBase.OnDestroy,
    `#if !DEBUG`) : la cause principale de la partie du 6 octobre ne se voit qu'avec une version Release"""
    from companion_suite import recruit
    from desync_suite import RELOAD
    from mp_test import ok
    from world_diff import diff

    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
    with_host(A, B)
    a, b = (state(p)["pc"]["uid"] for p in (A, B))
    pet = recruit(B, b, host=H)
    check(f"B a un compagnon ({pet}) que A voit", try_wait(lambda: seen_at(A, pet) is not None, "A voit le compagnon", 30))
    step_away(B, 6, -5)
    time.sleep(3)
    names = {H: "host", A: "A", B: "B"}

    def gone(why):
        for p in (H, A):
            check(f"{why} : chez {names[p]}, ni B ni son compagnon ne sont sur la carte "
                  f"({seen_at(p, b)}, {seen_at(p, pet)})",
                  try_wait(lambda p=p: seen_at(p, b) is None and seen_at(p, pet) is None, "B et son compagnon partis", 30))
        check(f"{why} : A est toujours a la Prairie, une seule fois chez l'host",
              ev(H, f'EClass._map.charas.Count(c => c.uid == {a}).ToString()') == "1")

    def back(why):
        time.sleep(4)
        mine, pet_at = pc_pos(B), seen_at(B, pet)
        for p in (H, A):
            check(f"{why} : chez {names[p]}, B est sur sa case ({seen_at(p, b)} / chez lui {mine})",
                  try_wait(lambda p=p: (at := seen_at(p, b)) is not None and dist(at, pc_pos(B)) <= 2, "B visible", 20))
            check(f"{why} : chez {names[p]}, son compagnon est sur sa case ({seen_at(p, pet)} / chez B {pet_at})",
                  try_wait(lambda p=p: (at := seen_at(p, pet)) is not None and (there := seen_at(B, pet)) is not None
                           and dist(at, there) <= 2, "compagnon visible", 20))
            for uid in (b, pet):
                check(f"{why} : chez {names[p]}, {uid} n'est qu'une fois sur la carte et dans le monde",
                      ev(p, f'(EClass._map.charas.Count(c => c.uid == {uid}) == 1 && '
                            f'EClass.game.cards.globalCharas.Find({uid}) == EClass._map.charas.Find(c => c.uid == {uid})).ToString()') == "True")
        # the reload a guest asks for by itself brings the map file only: the others must still stand there
        ev(A, RELOAD)
        time.sleep(3)
        wait(settled(A, HOME, away=False), "A sur la carte rechargee", timeout=120)
        time.sleep(3)
        check(f"{why} : A recharge sa carte et voit toujours B et son compagnon ({seen_at(A, b)}, {seen_at(A, pet)})",
              try_wait(lambda: seen_at(A, b) is not None and seen_at(A, pet) is not None, "B apres rechargement", 20))
        gaps = [g for g in diff([H, A, B], names) if g.startswith("personnage")]
        check(f"{why} : aucun personnage en trop ni en moins entre les trois jeux ({len(gaps)} ecart(s))", not gaps)
        for g in gaps[:8]:
            print(f"      {g}")

    move(B, VERNIS)
    wait(settled(B, VERNIS, away=True), "B seul a Vernis", timeout=240)
    gone("B parti a Vernis")
    move(B, HOME)
    wait(settled(B, HOME, away=False), "B de retour chez l'host", timeout=300)
    back("B revenu de Vernis")

    ok(emp.call(B, "command", {"cmd": "emp.disconnect"}))
    wait(lambda: not state(B).get("connected"), "B hors de la partie", timeout=60)
    gone("B deconnecte")
    ok(emp.call(B, "command", {"cmd": "emp.connect_udp"}))
    wait(settled(B, HOME, away=False), "B de nouveau chez l'host", timeout=300)
    back("B reconnecte")
    for p in (A, B):
        shot(f"q5-{NAMES[p]}", p)


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
    steps = [q1, q2, q3]
    if a.only:
        steps = [s for s in (*steps, q4, q5) if s.__name__ in a.only.split(",")]
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

    try:
        move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=240)
        with_host(A, B)
    except Exception as ex:  # noqa: BLE001
        print(f"    retour a la Prairie rate : {type(ex).__name__}: {ex}")

    try:
        emp.call(H, "command", {"cmd": "emp.autosave_every 0"})
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
