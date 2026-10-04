"""Les six decisions du conseil du 2026-10-04 (MODLOG, « Points restants traites en autonomie »). Test court, sur
des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/council_suite.py            # ou --only c2,c3

C1  grimoires : la lecture n'est tiree que dans le jeu du lecteur ; un echec use quand meme le livre chez l'host
C2  mort : apres le jour 90, l'invite qui meurt chez l'host perd une part de son or, qui tombe par terre
C3  prime de la guilde des guerriers : a l'invite qui tue, pas a l'host
C4  cadeaux du dieu : l'invite recoit son familier et son artefact, meme si l'host a deja ceux de ce dieu
C5  pieges (a Vernis) : tire seulement dans le jeu de l'invite ; le sommeil d'un piege lui arrive quand meme
C6  carte au tresor (les deux sur la carte du monde) : l'invite creuse, le coffre apparait, sa carte est utilisee
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from death_suite import death_screen  # noqa: E402
from guest_suite import awake, chara, give, give_made, stand, use_held  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, VERNIS, both_joined, check, ev, eventually, host_goto, scan_logs, wait, zone_uid  # noqa: E402

H, A = 27551, 27552
GOLD = '{c}.GetCurrency("money").ToString()'


def gold(port, uid):
    return int(ev(port, GOLD.format(c=chara(port, uid))))


def free_next_to(port, uid, dist=1):
    """Une case libre a cote de ce personnage, vue par ce jeu : "x,z"."""
    return ev(port, f'var c = {chara(port, uid)}; for (var dx = -{dist}; dx <= {dist}; dx++) for (var dz = -{dist}; dz <= {dist}; dz++) {{ '
                    f'if (System.Math.Max(System.Math.Abs(dx), System.Math.Abs(dz)) != {dist}) continue; var p = new Point(c.pos.x + dx, c.pos.z + dz); '
                    'if (p.IsValid && p.IsInBounds && !p.IsBlocked && !p.HasChara && !p.HasThing && !p.cell.IsTopWaterAndNoSnow) return p.x + "," + p.z; } return "";')


def c1(ctx):
    """grimoires : un seul tirage, dans le jeu du lecteur"""
    port, uid = ctx["a"]
    seen = lambda p, b: ev(p, f'var t = {chara(p, uid)}.things.Find(x => x.uid == {b}); return t == null ? "disparu" : t.c_charges.ToString();')  # noqa: E731
    reading = 'EClass.pc.ai is AI_Read && EClass.pc.ai.IsRunning ? "lit" : "libre"'
    make = 'var t = ThingGen.Create("spellbook"); t.c_charges = 4; t.SetBlessedState(BlessedState.Normal);'
    try:
        # (a) chez l'host, la copie de l'invite est confuse : son tirage a lui raterait trois fois sur quatre a
        # chaque pas. Dans le jeu de l'invite la lecture est sure : elle doit aller au bout
        book = give_made(ctx, "a", make)
        ev(port, 'EClass.debug.godMode = true; EClass.pc.RemoveCondition<ConConfuse>(); "ok"')
        ev(H, f'var c = {chara(H, uid)}; c.AddCondition<ConConfuse>(2000, true); "ok"')
        time.sleep(1)
        awake(port)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {book}); EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
        time.sleep(2)
        done = eventually(lambda: awake(port) and ev(port, reading) == "libre", timeout=120)
        left = seen(H, book)
        check(f"l'invite, sur de lui dans son jeu, lit son grimoire jusqu'au bout (charges chez l'host : 4 -> {left})",
              done and left == "3")
        ev(H, f'var c = {chara(H, uid)}; c.RemoveCondition<ConConfuse>(); var t = c.things.Find(x => x.uid == {book}); if (t != null) t.Destroy(); "ok"')
        time.sleep(1)

        # (b) l'invite rate dans son jeu (confus pour de vrai) : la lecture s'arrete et le livre perd une charge
        ev(port, 'EClass.debug.godMode = false; "ok"')
        book = give_made(ctx, "a", make)
        ev(H, f'var c = {chara(H, uid)}; c.AddCondition<ConConfuse>(2000, true); "ok"')
        eventually(lambda: ev(port, "EClass.pc.isConfused.ToString()") == "True", timeout=10)
        used = False
        for _ in range(4):
            awake(port)
            ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {book}); if (t != null) EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
            time.sleep(2)
            eventually(lambda: awake(port) and ev(port, reading) == "libre", timeout=60)
            time.sleep(2)
            if seen(H, book) != "4":
                used = True
                break
        left = seen(H, book)
        check(f"un echec de l'invite use le livre d'une charge chez l'host, pas plus (4 -> {left})", used and left == "3")
        check(f"l'invite voit la meme chose ({seen(port, book)})", eventually(lambda: seen(port, book) == left, timeout=10))
    finally:
        ev(port, 'EClass.debug.godMode = false; "ok"')
        ev(H, f'var c = {chara(H, uid)}; c.RemoveCondition<ConConfuse>(); c.hp = c.MaxHP; '
              'foreach (var m in EClass._map.charas.Where(x => x.IsHostile() && !x.IsPCFaction).ToList()) m.Destroy(); "ok"')


def c2(ctx):
    """mort : apres le jour 90, l'invite paie comme un joueur seul"""
    port, uid = ctx["a"]
    days = ev(H, "EClass.player.stats.days.ToString()")
    try:
        ev(H, 'EClass.player.stats.days = 100; "ok"')
        ev(H, f'var c = {chara(H, uid)}; foreach (var t in c.things.Where(x => x.id == "letter_will").ToList()) t.Destroy(); "ok"')
        had = gold(port, uid)
        ev(port, f'EClass.pc.ModCurrency({max(0, 3000 - had)}); "ok"')
        eventually(lambda: gold(H, uid) >= 3000, timeout=10)
        before = gold(H, uid)
        ev(H, f'var c = {chara(H, uid)}; c.hp = 0; c.Die(); "ok"')
        check("l'invite se voit mort", eventually(lambda: ev(port, "EClass.pc.isDead.ToString()") == "True", timeout=15))
        death_screen(port, 0)
        after = gold(H, uid)
        lost = before - after
        check(f"l'invite a perdu entre un tiers et deux tiers de son or ({before} -> {after})",
              before // 3 <= lost <= 2 * (before // 3) + 1)
        check(f"l'invite voit le meme or que l'host ({gold(port, uid)})", eventually(lambda: gold(port, uid) == after, timeout=10))
        pile = lambda p: ev(p, f'var c = {chara(p, uid)}; return EClass._map.things.Where(t => t.id == "money" && t.pos.Distance(c.pos) <= 1).Sum(t => t.Num).ToString();')  # noqa: E731
        check(f"l'or perdu est par terre a ses pieds, chez l'host ({pile(H)})", int(pile(H)) == lost)
        check(f"et chez l'invite ({pile(port)})", eventually(lambda: int(pile(port)) == lost, timeout=10))
    finally:
        ev(H, f'EClass.player.stats.days = {days}; "ok"')


def c3(ctx):
    """prime de la guilde des guerriers : a celui qui tue"""
    port, uid = ctx["a"]
    rel = ev(H, 'var r = Guild.Fighter.relation; return (int)r.type + "/" + r.rank;')
    try:
        for p in (H, port):
            ev(p, 'var r = Guild.Fighter.relation; r.type = FactionRelation.RelationType.Member; r.rank = 4; "ok"')
        spot = free_next_to(H, uid)
        x, z = spot.split(",")
        target = ev(H, f'Chara m = null; for (var i = 0; i < 6; i++) {{ m = CharaGen.Create("putty"); if (m.uid % 2 != 0) break; m.Destroy(); }} '
                       'm.rarity = Rarity.Legendary; m.c_originalHostility = Hostility.Enemy; m.hostility = Hostility.Enemy; '
                       f'EClass._zone.AddCard(m, new Point({x}, {z})); m.hp = 1; m.AddCondition<ConParalyze>(5000, true); '
                       'return m.uid + "/" + Guild.Fighter.HasBounty(m);')
        m = int(target.split("/")[0])
        if not check(f"un monstre a prime est a cote de l'invite ({target})", target.endswith("/True")):
            return
        eventually(lambda: ev(port, f'(EClass._map.charas.Find(x => x.uid == {m}) != null).ToString()') == "True", timeout=10)
        mine, hosts = gold(H, uid), gold(H, ctx["h"][1])
        dead = lambda: ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {m}); return (m == null || m.isDead).ToString();') == "True"  # noqa: E731
        for _ in range(40):
            if dead():
                break
            awake(port)
            ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {m}); if (m != null && !m.isDead) ACT.Melee.Perform(EClass.pc, m, m.pos); "ok"')
            time.sleep(1.5)
        if not check("l'invite tue le monstre", dead()):
            return
        time.sleep(2)
        check(f"la prime va a l'invite (son or chez l'host : {mine} -> {gold(H, uid)})", gold(H, uid) - mine >= 100)
        check(f"pas a l'host ({hosts} -> {gold(H, ctx['h'][1])})", gold(H, ctx["h"][1]) == hosts)
        check(f"l'invite voit le meme or ({gold(port, uid)})", eventually(lambda: gold(port, uid) == gold(H, uid), timeout=10))
    finally:
        t, r = rel.split("/")
        for p in (H, port):
            ev(p, f'var r = Guild.Fighter.relation; r.type = (FactionRelation.RelationType){t}; r.rank = {r}; "ok"')


def c4(ctx):
    """cadeaux du dieu : chaque joueur les recoit une fois, meme si l'host a deja ceux de ce dieu"""
    port, uid = ctx["a"]
    god = "EClass.game.religions.Healing"
    was = ev(H, f'{chara(H, uid)}.faith.id')
    rank = ev(H, f"{god}.giftRank.ToString()")
    rewards = ev(H, f'string.Join(";", {god}.source.rewards)')
    if not check(f"ce dieu a un familier et un artefact a donner ({rewards})", rewards.count(";") >= 1):
        return
    pet, arts = rewards.split(";")[0], rewards.split(";")[1].split("|")
    pets = lambda p: int(ev(p, f'EClass._map.charas.Count(x => x.id == "{pet}").ToString()'))  # noqa: E731
    owned = lambda: int(ev(H, f'EClass._map.charas.Count(x => x.id == "{pet}" && x.GetInt("emp_owner") == {uid}).ToString()'))  # noqa: E731
    ids = ",".join(f'"{a}"' for a in arts)
    things = lambda p: int(ev(p, f'var ids = new[] {{ {ids} }}; var c = {chara(p, uid)}; '  # noqa: E731
                                 'return (EClass._map.things.Count(t => ids.Contains(t.id)) + c.things.Count(t => ids.Contains(t.id))).ToString();'))
    pray = lambda: (awake(port), ev(port, 'ACT.Create(6050).Perform(EClass.pc); "ok"'), time.sleep(4))  # noqa: E731
    try:
        # l'host a deja eu les deux cadeaux de ce dieu : pour le jeu, ce monde n'a plus rien a donner
        ev(H, f'{god}.giftRank = 2; "ok"')
        ev(port, f'{god}.JoinFaith(EClass.pc, Religion.ConvertType.Campaign); EClass.pc.elements.SetBase(85, 40); "ok"')
        ok = eventually(lambda: ev(H, f'var c = {chara(H, uid)}; return c.faith.id + "/" + c.Evalue(85);') == "healing/40", timeout=15)
        if not check("l'invite suit ce dieu, avec assez de piete (vu par l'host)", ok):
            return
        p0, t0 = pets(H), things(H)
        pray()
        check(f"premiere priere : un familier de plus, a l'invite ({p0} -> {pets(H)}, a lui : {owned()})",
              eventually(lambda: pets(H) == p0 + 1 and owned() >= 1, timeout=10))
        check(f"l'invite le voit ({pets(port)})", eventually(lambda: pets(port) == pets(H), timeout=10))
        pray()
        check(f"deuxieme priere : l'artefact ({t0} -> {things(H)}, attendu +{len(arts)})",
              eventually(lambda: things(H) == t0 + len(arts), timeout=10))
        check(f"l'invite le voit ({things(port)})", eventually(lambda: things(port) == things(H), timeout=10))
        pray()
        pray()
        check(f"ensuite plus rien : un seul familier, un seul artefact ({pets(H) - p0}, {things(H) - t0})",
              pets(H) == p0 + 1 and things(H) == t0 + len(arts))
        check(f"le compte du monde (celui de l'host) n'a pas bouge ({ev(H, god + '.giftRank.ToString()')})",
              ev(H, f"{god}.giftRank.ToString()") == "2")
    finally:
        ev(H, f'{god}.giftRank = {rank}; "ok"')
        # retour a son dieu d'avant sans colere du dieu quitte (conversion "de campagne")
        ev(port, f'EClass.game.religions.Find("{was}").JoinFaith(EClass.pc, Religion.ConvertType.Campaign); "ok"')


TRAP = ('var row = EClass.sources.things.rows.FirstOrDefault(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Trap" '
        '&& x.vals != null && x.vals.Length > 0 && x.vals[0] == "%s"); if (row == null) return ""; '
        'var t = ThingGen.Create(row.id); EClass._zone.AddCard(t, new Point(%s, %s)).Install(); t.SetHidden(false); return t.uid.ToString();')


def step_on(ctx, kind):
    """Un piege pose a cote de l'invite, sur lequel il marche. Renvoie son numero."""
    port, uid = ctx["a"]
    spot = free_next_to(H, uid)
    x, z = spot.split(",")
    trap = ev(H, TRAP % (kind, x, z))
    if not check(f"un piege ({kind}) est pose a cote de l'invite ({trap or 'introuvable'} en {spot})", bool(trap)):
        return 0
    eventually(lambda: ev(port, f'(EClass._map.things.Find(t => t.uid == {trap}) != null).ToString()') == "True", timeout=10)
    awake(port)
    ev(port, f'EClass.pc.SetAIImmediate(new AI_Goto(new Point({x}, {z}), 0)); "ok"')
    there = eventually(lambda: ev(H, f'var c = {chara(H, uid)}; return c.pos.x + "," + c.pos.z;') == spot, timeout=10)
    log(f"l'invite marche sur la case {spot} : {'oui' if there else 'non'}")
    time.sleep(2)
    return int(trap)


def c5(ctx):
    """pieges : tire seulement dans le jeu de celui qui marche dessus"""
    port, uid = ctx["a"]
    host_goto(H, port, VERNIS)
    try:
        # un invite maladroit : il rate le desamorcage dans son jeu
        ev(port, 'EClass.pc.elements.SetBase(293, 0); "ok"')
        time.sleep(2)
        hit = False
        for _ in range(6):
            ev(H, f'var c = {chara(H, uid)}; c.RemoveCondition<ConSleep>(); c.hp = c.MaxHP; "ok"')
            time.sleep(1)
            hp = int(ev(H, f'{chara(H, uid)}.hp.ToString()'))
            trap = step_on(ctx, "spear")
            if not trap:
                return
            # un desamorcage rate par un membre du groupe laisse une marque sur le piege, dans le jeu qui a tire
            marks = lambda p: ev(p, f'var t = EClass._map.things.Find(x => x.uid == {trap}); return t == null ? "detruit" : t.GetInt(60).ToString();')  # noqa: E731
            cur = lambda: int(ev(H, f'{chara(H, uid)}.hp.ToString()'))  # noqa: E731
            eventually(lambda: cur() < hp, timeout=6)
            now = cur()
            log(f"piege {trap} : points de vie {hp} -> {now}, marques host {marks(H)}, invite {marks(port)}")
            rolled_here = marks(H) not in ("0", "detruit")
            if rolled_here or now < hp:
                hit = now < hp
                check(f"l'host n'a pas tire ce piege pour l'invite (marques chez l'host : {marks(H)})", not rolled_here)
                break
            ev(H, f'var t = EClass._map.things.Find(x => x.uid == {trap}); if (t != null) t.Destroy(); "ok"')
        check("le piege rate par l'invite dans son jeu le blesse, chez l'host", hit)

        ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; "ok"')
        slept = False
        for _ in range(4):
            trap = step_on(ctx, "sleep")
            if not trap:
                return
            if eventually(lambda: ev(H, f'{chara(H, uid)}.HasCondition<ConSleep>().ToString()') == "True", timeout=5):
                slept = True
                break
            ev(H, f'var t = EClass._map.things.Find(x => x.uid == {trap}); if (t != null) t.Destroy(); "ok"')
        check("un piege de sommeil endort l'invite, vu par l'host", slept)
        check("et dans son jeu", eventually(lambda: ev(port, "EClass.pc.HasCondition<ConSleep>().ToString()") == "True", timeout=10))
    finally:
        ev(H, f'var c = {chara(H, uid)}; c.RemoveCondition<ConSleep>(); c.hp = c.MaxHP; "ok"')


def c6(ctx):
    """carte au tresor : sur la carte du monde avec l'host, le coffre est pour celui qui creuse"""
    port, uid = ctx["a"]
    region = int(ev(H, "EClass.world.region.uid.ToString()"))
    ev(H, 'EClass.player.ExitBorder(); "ok"')
    wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=120)
    time.sleep(4)
    st = state(port)
    if st.get("awayZone") or (st.get("zone") or {}).get("uid") != region:
        ev(port, 'EClass.player.ExitBorder(); "ok"')
    both_joined(H, port, region)

    shovel = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.elements != null && x.elements.Length > 0 && x.elements[0] == 230); return r == null ? "" : r.id;')
    tool = give(ctx, "a", shovel)
    scroll = give(ctx, "a", "map_treasure")
    # l'host a lui aussi une carte : elle ne doit pas servir a la place de celle de l'invite
    hosts_map = int(ev(H, 'var t = EClass.pc.AddThing(ThingGen.Create("map_treasure"), false); return t.uid.ToString();'))
    dest = ev(H, f'var t = {chara(H, uid)}.things.Find(x => x.uid == {scroll}); var p = ((TraitScrollMapTreasure)t.trait).GetDest(true); return p == null ? "" : p.x + "," + p.z;')
    if not check(f"la carte de l'invite mene quelque part ({dest})", bool(dest)):
        return
    x, z = (int(v) for v in dest.split(","))
    # sur la carte du monde on creuse sous ses pieds : l'invite est pose sur la case (mise en place), prend sa
    # pelle en main et creuse (la tache que lance le clic, donnee directement)
    ev(port, f'EClass.pc.MoveImmediate(new Point({x}, {z}), true, true); "ok"')
    there = eventually(lambda: ev(H, f'var c = {chara(H, uid)}; return c == null ? "" : c.pos.x + "," + c.pos.z;') == dest, timeout=10)
    if not check(f"l'invite est sur la case du tresor, vu par l'host ({dest})", there):
        return
    awake(port)
    r = ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {tool}); EClass.pc.HoldCard(t); '
                 'var task = new TaskDig { pos = EClass.pc.pos.Copy(), mode = TaskDig.Mode.RemoveFloor }; '
                 'var hit = task.GetHitResult(); EClass.pc.SetAI(task); return hit.ToString();')
    log(f"l'invite creuse en {dest} : {r}")
    chest = lambda p: ev(p, f'EClass._map.things.Count(t => t.id == "chest_treasure" && t.pos.x == {x} && t.pos.z == {z}).ToString()')  # noqa: E731
    check(f"le coffre apparait chez l'host ({chest(H)})", eventually(lambda: awake(port) and chest(H) == "1", timeout=40))
    check(f"l'invite le voit et il reste la ({chest(port)})", eventually(lambda: chest(port) == "1", timeout=10) and (time.sleep(3) or chest(port) == "1"))
    has = lambda p, who, m: ev(p, f'({chara(p, who)}.things.Find(x => x.uid == {m}) != null).ToString()')  # noqa: E731
    check("la carte de l'invite est utilisee (vu par l'host)", has(H, uid, scroll) == "False")
    check("et dans son jeu", eventually(lambda: has(port, uid, scroll) == "False", timeout=10))
    check("la carte de l'host, elle, est toujours dans son sac", has(H, ctx["h"][1], hosts_map) == "True")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    # C5 emmene les deux joueurs a Vernis : en dernier. C6 n'est pas dans la passe par defaut : sur la carte du
    # monde le banc n'arrive pas a faire creuser l'invite comme un joueur (l'host ne recoit pas sa tache), a
    # essayer en vrai ; `--only c6` pour le relancer, sur des fenetres neuves
    steps = [c1, c3, c4, c2, c5]
    if a.only:
        steps = [s for s in (c1, c3, c4, c2, c6, c5) if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'council-{step.__name__}-{name}', port)}")
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
