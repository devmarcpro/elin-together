"""Marcher sur un objet avec le sac plein (dev/PLAN_ramassage_sac_plein.md). Test court, sur des instances deja
lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/pickup_suite.py            # ou --only p1,p3

Retour d'une vraie partie (0.26.510) : un invite marche sur des objets, le sac plein, et ils disparaissent.
En solo le jeu dit « sac plein » et laisse l'objet par terre (Chara.Pick, Chara.cs:4619-4634).

P1  l'invite, sur la carte de l'host, le sac plein : il marche sur un seau pose a cote de lui. Le seau doit rester
    par terre dans les DEUX jeux. Puis il marche sur un caillou alors qu'il a deja des cailloux : le caillou doit
    entrer dans le sac (une pile ne demande pas de case), dans les deux jeux.
P2  temoin : la meme chose pour l'host.
P3  l'invite seul a Vernis (il tient la carte, son jeu y joue comme en solo) : la meme chose, vue par son jeu ;
    au retour, l'host voit le meme sac que lui.

Attendu sur la 0.26.510 (lu dans le code, pas vu tourner) : P1 rouge sur le seau (l'host le range de force dans le sac
de l'invite, l'invite le recoit dans un sac sans case libre : il est dans le sac, dessine nulle part) ; P2 rouge
sur le seau cote invite (le seau quitte le sol dans le jeu de l'invite seulement) ; P3 vert. Vert partout avec le
correctif de CharaPickThingEvent.

Ce que le banc ne joue pas comme un joueur :
- le sac est rempli par l'host (un caillou par case libre, poses sans les empiler), pas en ramassant ; a Vernis
  l'objet par terre est cree dans le jeu de l'invite (il y est seul) ;
- la marche est un AI_Goto vers la case voisine (le deplacement d'un clic sur la case), pas une touche enfoncee ;
- un sac dans le sac qui a de la place : pas joue, le test s'arrete en le disant ;
- le filtre de ramassage du menu avance (Player.dataPick) est suppose a son reglage d'origine ;
- pas joue : un objet rendu par une recolte ou une mine quand le sac est plein (PickOrDrop / TrySmoothPick), un
  visiteur sur la carte tenue par un autre invite (il faut trois fenetres ; c'est le code de P1 et P2, le joueur qui
  tient la carte y a le role de l'host), un sac plein a une case pres avec deux objets sur la meme case.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import awake, both, cell, chara, count, free_next_to  # noqa: E402
from mp_test import log, shot, state, wait  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, move, scan_logs, zone_uid  # noqa: E402

H, A = 27551, 27552
FILL, ITEM = "pebble", "bucket"
SETTLE = 6  # secondes laissees aux deux jeux pour se repondre apres le pas


def free_cells(port):
    """Cases libres du sac de ce joueur, dans son jeu (le seul qui tient la grille du sac)."""
    return int(ev(port, 'EClass.pc.things.RefreshGrid(); return EClass.pc.things.grid.Count(t => t == null).ToString();'))


def fill(ctx, key):
    """L'host met un caillou dans chaque case libre du sac de ce joueur. Vrai si son jeu voit le sac plein."""
    port, uid = ctx[key]
    n = free_cells(port)
    if n:
        ev(H, f'var c = {chara(H, uid)}; for (var i = 0; i < {n}; i++) c.AddThing(ThingGen.Create("{FILL}"), false); return "ok";')
    full = eventually(lambda: free_cells(port) == 0 and ev(port, 'EClass.pc.things.IsOverflowing().ToString()') == "False", timeout=20)
    log(f"sac rempli : {n} cailloux ajoutes, {free_cells(port)} case libre, poids : phase {ev(port, 'EClass.pc.burden.GetPhase().ToString()')}")
    return full


def empty(uid):
    """L'host retire les cailloux du sac de ce joueur, et ceux qui trainent sur la carte."""
    ev(H, f'var c = {chara(H, uid)}; if (c != null) foreach (var t in c.things.Where(m => m.id == "{FILL}").ToList()) t.Destroy(); '
          f'foreach (var t in EClass._map.things.Where(m => m.id == "{FILL}" && m.placeState == PlaceState.roaming).ToList()) t.Destroy(); return "ok";')


def put(port, uid, stack):
    """Ce jeu pose un objet sur une case libre a cote de ce joueur : un seau, ou (stack) la copie d'un caillou de son
    sac. Renvoie (numero, x, z), ou None s'il n'y a pas de case."""
    spot = free_next_to(port, uid)
    if not spot:
        return None
    x, z = (int(v) for v in spot.split(","))
    make = (f'var t = {chara(port, uid)}.things.First(m => m.id == "{FILL}").Duplicate(1);' if stack else f'var t = ThingGen.Create("{ITEM}");')
    return int(ev(port, f'{make} EClass._zone.AddCard(t, new Point({x}, {z})); return t.uid.ToString();')), x, z


def where(port, owner, thing):
    """Ou ce jeu voit l'objet : "sol@x,z", "sac", "sac, sans case" (dans le sac mais dessine nulle part), "nulle part"."""
    return ev(port, f'var g = EClass._map.things.Find(x => x.uid == {thing}); if (g != null) return "sol@" + g.pos.x + "," + g.pos.z; '
                    f'var c = {chara(port, owner)}; var t = c == null ? null : c.things.Find(x => x.uid == {thing}); if (t == null) return "nulle part"; '
                    'return c.things.grid != null && !c.things.grid.Contains(t) && t.invY != 1 && !t.isEquipped ? "sac, sans case" : "sac";')


def dest(port, thing):
    """Ce que le jeu de ce joueur ferait de l'objet s'il le ramassait : "pile", "case" ou "rien" (sac plein)."""
    return ev(port, f'var t = EClass._map.things.Find(x => x.uid == {thing}); if (t == null) return "objet absent"; '
                    'var d = EClass.pc.things.GetDest(t); return d.stack != null ? "pile" : (d.container != null ? "case" : "rien");')


def walk_onto(port, uid, x, z):
    """Le joueur marche sur cette case (AI_Goto, le deplacement d'un clic sur la case)."""
    awake(port)
    ev(port, f'EClass.pc.SetAIImmediate(new AI_Goto(new Point({x}, {z}), 0)); return "ok";')
    return eventually(lambda: awake(port) and cell(port, uid) == f"{x},{z}", timeout=20)


def step_full(who, port, uid, games):
    """Sac plein, un seau a cote : le joueur marche dessus. `games` : les jeux qui voient la carte."""
    made = put(H if H in games else port, uid, stack=False)
    if not check(f"{who} : un seau est pose a cote de lui ({made})", made and eventually(lambda: where(port, uid, made[0]).startswith("sol"), timeout=15)):
        return
    thing, x, z = made
    try:
        if not check(f"{who} : son jeu n'a de place nulle part pour ce seau ({dest(port, thing)})", dest(port, thing) == "rien"):
            return
        bags = {p: count(p, uid, FILL) for p in games}
        if not check(f"{who} marche sur le seau ({x},{z})", walk_onto(port, uid, x, z)):
            return
        time.sleep(SETTLE)
        seen = {p: where(p, uid, thing) for p in games}
        told = ", ".join(f"{'host' if p == H else 'invite'} : {v}" for p, v in seen.items())
        check(f"{who} : le seau n'a disparu dans aucun jeu ({told})", all(v.startswith("sol") or v == "sac" for v in seen.values()))
        check(f"{who} : comme en solo, le seau est reste par terre sur sa case, dans son jeu ({seen[port]})", seen[port] == f"sol@{x},{z}")
        if len(games) > 1:
            check(f"{who} : les deux jeux voient le seau au meme endroit ({told})", len(set(seen.values())) == 1)
        check(f"{who} : son sac ne deborde pas ({ev(port, 'EClass.pc.things.IsOverflowing().ToString()')})",
              ev(port, 'EClass.pc.things.IsOverflowing().ToString()') == "False")
        check(f"{who} : ses cailloux n'ont pas bouge ({bags} -> {({p: count(p, uid, FILL) for p in games})})",
              all(count(p, uid, FILL) == n for p, n in bags.items()))
    finally:
        ev(port, 'EClass.pc.SetNoGoal(); return "ok";')
        owner = H if H in games else port
        ev(owner, f'var c = {chara(owner, uid)}; var t = EClass._map.things.Find(x => x.uid == {thing}) ?? (c == null ? null : c.things.Find(x => x.uid == {thing})); '
                  'if (t != null) t.Destroy(); return "ok";')


def step_stack(who, port, uid, games):
    """Sac plein, un caillou a cote, des cailloux dans le sac : le joueur marche dessus, le caillou rejoint une pile."""
    made = put(H if H in games else port, uid, stack=True)
    if not check(f"{who} : un caillou est pose a cote de lui ({made})", made and eventually(lambda: where(port, uid, made[0]).startswith("sol"), timeout=15)):
        return
    thing, x, z = made
    try:
        if not check(f"{who} : son jeu a une pile ou le ranger ({dest(port, thing)})", dest(port, thing) == "pile"):
            return
        bags = {p: count(p, uid, FILL) for p in games}
        if not check(f"{who} marche sur le caillou ({x},{z})", walk_onto(port, uid, x, z)):
            return
        got = eventually(lambda: all(count(p, uid, FILL) == n + 1 for p, n in bags.items()), timeout=15)
        time.sleep(SETTLE)
        after = {p: count(p, uid, FILL) for p in games}
        check(f"{who} : le caillou est entre dans le sac, dans chaque jeu ({bags} -> {after})", got and all(after[p] == n + 1 for p, n in bags.items()))
        seen = {p: where(p, uid, thing) for p in games}
        check(f"{who} : il n'est plus par terre dans aucun jeu ({seen})", not any(v.startswith("sol") for v in seen.values()))
        check(f"{who} : son sac ne deborde pas", ev(port, 'EClass.pc.things.IsOverflowing().ToString()') == "False")
    finally:
        ev(port, 'EClass.pc.SetNoGoal(); return "ok";')


def together(ctx, key):
    who = dict((k, w) for w, k in both(ctx))[key]
    port, uid = ctx[key]
    try:
        if not check(f"mise en place : le sac de {who} est plein dans son jeu", fill(ctx, key)):
            return
        check(cond=eventually(lambda: count(H, uid, FILL) == count(port, uid, FILL), timeout=10),
              label=f"mise en place : les deux jeux voient les memes cailloux ({count(H, uid, FILL)} et {count(port, uid, FILL)})")
        step_full(who, port, uid, (H, A))
        step_stack(who, port, uid, (H, A))
    finally:
        empty(uid)


def p1(ctx):
    """l'invite sur la carte de l'host, sac plein : le seau reste par terre dans les deux jeux, le caillou rejoint sa pile"""
    together(ctx, "a")


def p2(ctx):
    """temoin, l'host : meme geste, meme resultat"""
    together(ctx, "h")


def p3(ctx):
    """l'invite seul a Vernis, sac plein : son jeu fait comme en solo ; au retour l'host voit le meme sac"""
    port, uid = ctx["a"]
    if not check("mise en place : le sac de l'invite est plein dans son jeu", fill(ctx, "a")):
        empty(uid)
        return
    try:
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
        time.sleep(3)
        check(f"l'invite est seul a Vernis, le sac toujours plein ({free_cells(A)} case libre)", free_cells(A) == 0)
        step_full("l'invite seul", A, uid, (A,))
        step_stack("l'invite seul", A, uid, (A,))
        mine = count(A, uid, FILL)
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)
    check(cond=eventually(lambda: count(H, uid, FILL) == mine, timeout=15),
          label=f"au retour, l'host voit les memes cailloux que l'invite ({count(H, uid, FILL)} et {mine})")
    check(f"au retour, pas de seau dans le sac de l'invite vu par l'host ({count(H, uid, ITEM)})", count(H, uid, ITEM) == 0)
    empty(uid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    if not check(f"les deux joueurs sont sur la meme carte ({zone_uid(H)} et {zone_uid(A)})", zone_uid(H) == zone_uid(A)):
        sys.exit(1)
    steps = [p1, p2, p3]
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
                print(f"    capture {name} : {shot(f'pickup-{step.__name__}-{name}', port)}")
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
