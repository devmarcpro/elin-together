"""Monture et parasite d'un invite quand les joueurs se retrouvent (signale par un joueur le 2026-10-11 : « ils
disparaissent alors qu'ils sont dans l'equipe, surtout quand on rejoint l'host »). Host + 1 client, a la Prairie.

    python _tools/mp_test.py
    python _tools/ride_suite.py               # les deux (ride, parasite)
    python _tools/ride_suite.py parasite      # un seul

Pour chacun des deux (monture, puis parasite), l'invite l'a sur lui et :
V1  part seul a Vernis, y marche, puis revient chez l'host
V2  repart seul a Vernis, l'host l'y rejoint
V3  l'host rentre a la Prairie, l'invite le suit
V4  le lien tombe (l'host le ferme sans prevenir, comme Steam), l'invite revient
Apres chaque retrouvaille, dans les DEUX jeux : le joueur porte bien l'animal du monde (pas une copie), l'animal dit
etre porte par lui, il est sur sa case, une seule fois sur la carte et dans ses cases, et dans l'equipe une fois.

Ce que le banc ne joue pas comme un joueur : l'animal est apprivoise par eval (guest_suite.tame) ; monter passe par
l'acte du jeu (ACT.Create), pas par le menu ; les voyages sont des « move » du pont, pas une marche jusqu'au bord ;
rien n'est regarde a l'ecran (l'image de l'animal), seulement l'etat du jeu.
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, state  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, move, scan_logs, wait, zone_uid  # noqa: E402

H, A = 27551, 27552


def look(port, uid, m, field):
    q = (f'var r = EClass.game.cards.globalCharas.Find({uid}); var w = EClass.game.cards.globalCharas.Find({m}); '
         'if (r == null || w == null) return "absent|" + (r == null) + "|" + (w == null); '
         f'var cells = 0; EClass._map.ForeachCell(c => {{ if (c.detail != null && c.detail.charas != null) cells += c.detail.charas.Count(x => x.uid == {m}); }}); '
         f'return (r.{field} != null && ReferenceEquals(r.{field}, w)) + "|" + (w.host != null && ReferenceEquals(w.host, r)) + "|" + w.pos.Equals(r.pos) + "|" + '
         f'EClass._map.charas.Count(x => x.uid == {m}) + "|" + cells + "|" + EClass.pc.party.members.Count(x => x != null && x.uid == {m}) + "|" + '
         f'(r.{field} == null ? "rien" : r.{field}.uid.ToString()) + "|" + r.pos + "|" + w.pos + "|" + (w.currentZone == null ? "sans carte" : w.currentZone.uid.ToString());')
    return str(ev(port, q)).split("|")


def together(step, uid, m, field, what):
    """les deux jeux, apres une retrouvaille"""
    time.sleep(4)
    for who, port in (("chez l'host", H), ("chez l'invite", A)):
        got = look(port, uid, m, field)
        if got[0] == "absent":
            check(f"{step} {who} : le joueur et son {what} existent ({got})", False)
            continue
        same, back, tile, listed, cells, party, carried, at, mount, zone = got
        check(f"{step} {who} : le joueur porte son {what}, qui dit etre porte par lui ({same}, {back} ; porte : {carried})",
              same == "True" and back == "True")
        check(f"{step} {who} : le {what} est sur la case du joueur ({mount} / {at}, carte {zone})", tile == "True")
        check(f"{step} {who} : une seule fois sur la carte, dans ses cases et dans l'equipe ({listed}, {cells}, {party})",
              listed == "1" and cells == "1" and party == "1")


def walk(port, dx):
    for _ in range(3):
        ev(port, f'EClass.pc.TryMoveTowards(new Point(EClass.pc.pos.x + ({dx}), EClass.pc.pos.z)); return "ok";')
        time.sleep(1.2)


def play(kind, rider="a"):
    import guest_suite as g  # noqa: PLC0415
    field, what, act = ("ride", "cheval", "ActRide") if kind == "ride" else ("parasite", "parasite", "ActParasite")
    P = A if rider == "a" else H
    log(f"--- {kind.upper()} : {what} de {'l invite' if rider == 'a' else 'l host'}")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    uid = ctx[rider][1]
    m = g.tame(ctx, "horse" if kind == "ride" else "putit", rider)
    if not check(f"l'invite a un animal ({m})", m):
        return
    g.clear_conditions(m)
    on = ev(P, f'var m = EClass._map.charas.Find(x => x.uid == {m}); ACT.Create(EClass.sources.elements.alias["{act}"].id).Perform(EClass.pc, m, m.pos); '
               f'return (EClass.pc.{field} == m).ToString();')
    if not check(f"l'invite le prend sur lui, par l'acte du jeu ({on})", on == "True"):
        return
    check("l'autre jeu le sait", eventually(
        lambda: ev(H if rider == "a" else A, f'var r = EClass.game.cards.globalCharas.Find({uid}); return (r.{field} != null && r.{field}.uid == {m}).ToString();') == "True", timeout=15))
    together("V0 (sur place)", uid, m, field, what)
    try:
        # V1 : seul a Vernis puis retour
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        time.sleep(3)
        walk(A, 6)
        move(A, HOME)
        both_joined(H, A, HOME)
        walk(A, -6)
        together("V1 (l'invite revient chez l'host)", uid, m, field, what)

        # V2 : seul a Vernis, l'host l'y rejoint
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        time.sleep(3)
        walk(A, 6)
        move(H, VERNIS)
        wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=180)
        both_joined(H, A, VERNIS)
        walk(A, -6)
        together("V2 (l'host rejoint l'invite a Vernis)", uid, m, field, what)

        # V3 : l'host rentre, l'invite le suit
        move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=180)
        time.sleep(4)
        s = state(A)
        if s.get("awayZone") or (s.get("zone") or {}).get("uid") != HOME:
            move(A, HOME)
        both_joined(H, A, HOME)
        walk(A, 6)
        together("V3 (l'host rentre, l'invite le suit)", uid, m, field, what)

        # V4 : le lien tombe (l'host le ferme, comme Steam le fait), l'invite revient
        import emp  # noqa: PLC0415
        from travel_suite import players  # noqa: PLC0415
        emp.call(H, "command", {"cmd": "emp.drop_links"})
        time.sleep(5)
        back = lambda: state(A).get("sceneMode") == "Zone" and state(A).get("connected") and players(H) == 2  # noqa: E731
        if not eventually(back, timeout=120):
            emp.call(A, "command", {"cmd": "emp.connect_udp"})
        if check("V4 : l'invite est revenu apres la coupure", eventually(back, timeout=180)):
            time.sleep(5)
            together("V4 (coupure puis retour)", uid, m, field, what)
    finally:
        ev(P, f'if (EClass.pc.{field} != null) ActRide.Unride(EClass.pc, {"true" if kind == "parasite" else "false"}, false); return "ok";')


def play_both():
    """monture ET parasite en meme temps, ceux de l'invite : V1 a V3"""
    import guest_suite as g  # noqa: PLC0415
    log("--- BOTH : cheval et parasite de l'invite, ensemble")
    uid = state(A)["pc"]["uid"]
    ctx = {"a": (A, uid), "h": (H, state(H)["pc"]["uid"])}
    pets = []
    for species, act, field, what in (("horse", "ActRide", "ride", "cheval"), ("putit", "ActParasite", "parasite", "parasite")):
        m = g.tame(ctx, species, "a")
        g.clear_conditions(m)
        on = ev(A, f'var m = EClass._map.charas.Find(x => x.uid == {m}); ACT.Create(EClass.sources.elements.alias["{act}"].id).Perform(EClass.pc, m, m.pos); '
                   f'return (EClass.pc.{field} == m).ToString();')
        if not check(f"l'invite prend son {what} sur lui ({on})", on == "True"):
            return
        pets.append((m, field, what))
    time.sleep(4)

    def all_together(step):
        for m, field, what in pets:
            together(step, uid, m, field, what)

    try:
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        time.sleep(3)
        walk(A, 6)
        move(A, HOME)
        both_joined(H, A, HOME)
        walk(A, -6)
        all_together("B1 (l'invite revient chez l'host)")
        move(A, VERNIS)
        wait(client_settled(A, VERNIS, True), "l'invite seul a Vernis", timeout=180)
        time.sleep(3)
        move(H, VERNIS)
        wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=180)
        both_joined(H, A, VERNIS)
        walk(A, -6)
        all_together("B2 (l'host rejoint l'invite a Vernis)")
        move(H, HOME)
        wait(lambda: zone_uid(H) == HOME, "host a la Prairie", timeout=180)
        time.sleep(4)
        s = state(A)
        if s.get("awayZone") or (s.get("zone") or {}).get("uid") != HOME:
            move(A, HOME)
        both_joined(H, A, HOME)
        walk(A, 6)
        all_together("B3 (l'host rentre, l'invite le suit)")
    finally:
        ev(A, 'if (EClass.pc.parasite != null) ActRide.Unride(EClass.pc, true, false); if (EClass.pc.ride != null) ActRide.Unride(EClass.pc, false, false); return "ok";')


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    # ride, parasite : ceux de l'invite ; hride, hparasite : ceux de l'host. SOFT=1 : case « retour sur place » cochee
    import os  # noqa: PLC0415
    if os.environ.get("SOFT"):
        from combat_suite import set_option  # noqa: PLC0415
        set_option("SoftRecall", True)
        time.sleep(2)
        log("case SoftRecall cochee")
    kinds = [k for k in ("ride", "parasite", "hride", "hparasite", "both") if len(sys.argv) < 2 or k in sys.argv[1].split(",")]
    for kind in kinds:
        try:
            if kind == "both":
                play_both()
                continue
            play(kind.lstrip("h"), "h" if kind.startswith("h") else "a")
        except Exception as ex:  # noqa: BLE001
            check(f"{kind} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
    scan_logs(start)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print("  ECHEC :", label)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
