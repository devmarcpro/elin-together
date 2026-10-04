"""Quatre ecarts host / invite de plus (PLAN_egalite_invites.md, « Etat au 2026-10-04, nuit »). Test court, sur des
instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/equal2_suite.py            # ou --only e1,e3

E1  appel a l'aide : l'invite frappe un habitant ami (il fronce les sourcils, pas hostile) ; un fanatique frappe
    appelle ses semblables. Avant : l'habitant devenait hostile tout de suite et personne n'etait appele.
E2  abattage : l'invite abat son chat avec le couteau de boucher (menu du couteau) : l'endurance est la sienne, pas
    celle de l'host ; le karma aussi. Tonte : meme mesure (elle etait deja bonne, le test le confirme).
E3  quitter son dieu : l'invite choisit un autre dieu ; l'host applique la punition (une colere et une boule, pas
    deux), les jours avec le dieu repartent de 0 des deux cotes. Sans punition : les deux dieux « cousins »
    (Ruse / Ombre de lune), la conversion de campagne, le depart de « sans dieu ».
E4  source chaude : l'invite se repose dans l'eau chaude, son compagnon recoit lui aussi le bain.

Ce que le banc ne joue pas comme un joueur :
- E3 : le choix du dieu se fait par un dialogue a l'autel ; le test appelle Religion.JoinFaith dans le jeu de
  l'invite (c'est ce que fait le dialogue, « %worship »), puis regarde ce que voit l'host.
- E4 : il faut une case d'eau ou l'on peut se tenir ; sinon le test le dit et saute. La tenue « sous-vetements » (que
  donne la cabine d'essayage) est mise directement.
- E1 : un coup unique ; avec une arme a deux attaques le deuxieme coup rend l'habitant hostile (test a relancer).
Le karma (E2) suppose « quetes et karma personnels » actif.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from council_suite import free_next_to  # noqa: E402
from guest_suite import awake, bag_size, chara, first_id, give, stand, use_held  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, check, ev, eventually, host_goto, scan_logs, zone_uid  # noqa: E402

H, A = 27551, 27552


def spawn(uid, cid, hostility="Neutral", extra=""):
    """L'host fait apparaitre ce personnage, paralyse, a cote de ce joueur ; renvoie son numero (0 : pas de place)."""
    spot = ""
    for dist in (1, 2, 3):
        spot = free_next_to(H, uid, dist)
        if spot:
            break
    if not spot:
        return 0
    x, z = spot.split(",")
    return int(ev(H, f'var m = CharaGen.Create("{cid}"); m.c_originalHostility = Hostility.{hostility}; m.hostility = Hostility.{hostility}; '
                     f'EClass._zone.AddCard(m, new Point({x}, {z})); m.hp = m.MaxHP; m.AddCondition<ConParalyze>(5000, true); {extra} '
                     'return m.uid.ToString();'))


def seen(port, m):
    return ev(port, f'(EClass._map.charas.Find(x => x.uid == {m}) != null).ToString()') == "True"


def drop(uids):
    for m in uids:
        ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {m}); if (m != null) m.Destroy(); "ok"')


def hostility(port, m):
    return ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {m}); return m == null ? "absent" : m.hostility.ToString();')


def blow(port, m):
    """Le joueur frappe, comme le clic sur un monstre le ferait."""
    awake(port)
    ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {m}); ACT.Melee.Perform(EClass.pc, m, m.pos); "ok"')


def e1(ctx):
    """appel a l'aide : l'habitant ami fronce les sourcils, le fanatique appelle ses semblables"""
    port, uid = ctx["a"]
    made = []
    ev(port, 'EClass.debug.godMode = true; "ok"')
    try:
        # (a) un ami frappe une fois : il n'est pas hostile (le jeu ne le fait que pour le joueur)
        friend = spawn(uid, "putty", "Friend", "m.hp = 100000;")
        made.append(friend)
        if not check(f"un habitant ami est a cote de l'invite ({friend})", friend and eventually(lambda: seen(port, friend), timeout=15)):
            return
        blow(port, friend)
        time.sleep(3)
        h = hostility(H, friend)
        check(f"l'ami frappe une fois n'est pas hostile, chez l'host ({h})", h == "Neutral")
        check(f"l'invite voit la meme chose ({hostility(port, friend)})", eventually(lambda: hostility(port, friend) == h, timeout=10))

        # (b) un fanatique appelle toujours : ses semblables (meme hostilite d'origine) deviennent hostiles.
        # Pas dans une base : le jeu n'y appelle jamais a l'aide, meme en solo (Chara.DoHostileAction) -> a Vernis
        host_goto(H, port, VERNIS)
        host_foe = ev(H, 'EClass.pc.enemy == null ? "" : EClass.pc.enemy.uid.ToString()')
        fanatic = spawn(uid, "fanatic", "Neutral")
        made.append(fanatic)
        others = []
        for _ in range(4):
            o = spawn(uid, "putty", "Neutral")
            made.append(o)
            others.append(o)
        if not check(f"un fanatique et {len(others)} voisins sont la ({fanatic})", fanatic and all(others)):
            return
        eventually(lambda: seen(port, fanatic) and all(seen(port, o) for o in others), timeout=15)
        angry = lambda p: sum(hostility(p, o) == "Enemy" for o in others)  # noqa: E731
        blow(port, fanatic)
        eventually(lambda: angry(H) > 0, timeout=10)
        time.sleep(2)
        check(f"le fanatique a appele : des voisins sont hostiles, chez l'host ({angry(H)} sur {len(others)})", angry(H) > 0)
        check(f"l'invite en voit autant ({angry(port)})", eventually(lambda: angry(port) == angry(H), timeout=10))
        now = ev(H, 'EClass.pc.enemy == null ? "" : EClass.pc.enemy.uid.ToString()')
        check(f"l'host n'a pas recu d'ennemi du coup de l'invite ({host_foe or 'aucun'} -> {now or 'aucun'})", now == host_foe)
    finally:
        ev(port, 'EClass.debug.godMode = false; "ok"')
        drop(made)
        if zone_uid(H) != HOME:
            host_goto(H, port, HOME)


def tame(ctx, cid):
    """L'host fait apparaitre un animal a cote de l'invite, l'invite le recrute. Renvoie son numero (0 : echec)."""
    port, uid = ctx["a"]
    m = spawn(uid, cid)
    if not m or not eventually(lambda: seen(port, m), timeout=15):
        return 0
    ev(port, f'EClass._map.charas.Find(x => x.uid == {m}).MakeAlly(false); "ok"')
    owned = eventually(lambda: ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {m}); '
                                     f'return (c != null && c.party != null && c.GetInt("emp_owner") == {uid}).ToString();') == "True", timeout=15)
    return m if owned else 0


def stamina(port, uid):
    return int(ev(port, f'{chara(port, uid)}.stamina.value.ToString()'))


def karma(port):
    return int(ev(port, 'EClass.player.karma.ToString()'))


def e2(ctx):
    """abattage et tonte : l'endurance et le karma sont ceux de l'invite, pas de l'host"""
    port, uid = ctx["a"]
    h_uid = ctx["h"][1]
    made = []
    was = ev(port, 'EClass.core.config.game.ignoreWarnSlaughter.ToString()')
    ev(port, 'EClass.core.config.game.ignoreWarnSlaughter = true; "ok"')
    try:
        knife = first_id("ToolButcher")
        cat = tame(ctx, "cat")
        made.append(cat)
        if not check(f"l'invite a recrute un chat ({cat}) et le couteau de boucher existe ({knife or 'non'})", cat and knife):
            return
        tool = give(ctx, "a", knife)
        ev(H, 'EClass.pc.stamina.Set(EClass.pc.stamina.max / 2); "ok"')
        ev(port, 'EClass.pc.stamina.Set(EClass.pc.stamina.max / 2); "ok"')
        time.sleep(2)
        pos = ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {cat}); return m.pos.x + "," + m.pos.z;').split(",")
        before = (stamina(H, h_uid), stamina(port, uid), karma(H), karma(port))
        r = use_held(port, tool, at=(int(pos[0]), int(pos[1])), pick='i.act is DynamicAct d && d.id == "AI_Slaughter"')
        log(f"l'invite abat : {r}")
        dead = lambda p: ev(p, f'var m = EClass._map.charas.Find(x => x.uid == {cat}); return (m == null || m.isDead).ToString();') == "True"  # noqa: E731
        if not check("le chat est abattu, chez l'host", eventually(lambda: awake(port) and dead(H), timeout=60)):
            return
        check("et chez l'invite", eventually(lambda: dead(port), timeout=10))
        time.sleep(3)
        after = (stamina(H, h_uid), stamina(port, uid), karma(H), karma(port))
        check(f"l'host n'a pas perdu d'endurance ({before[0]} -> {after[0]})", after[0] >= before[0])
        check(f"l'invite en a perdu, dans son jeu ({before[1]} -> {after[1]})", after[1] < before[1])
        check(f"l'host la voit baisser aussi, comme l'invite ({stamina(H, uid)})",
              eventually(lambda: stamina(H, uid) == stamina(port, uid), timeout=10))
        check(f"le karma de l'host n'a pas bouge ({before[2]} -> {after[2]})", after[2] == before[2])
        check(f"celui de l'invite a perdu 3 pour avoir tue un chat ({before[3]} -> {after[3]})", after[3] == before[3] - 3)

        # tonte : le jeu fait payer 1 d'endurance a celui qui tond (« owner »), l'invite ici
        shears = first_id("ToolShears")
        sheep = spawn(uid, "putty_snow", "Neutral", "m.c_fur = 30;")
        made.append(sheep)
        if not check(f"un animal a tondre est la ({sheep}), les ciseaux existent ({shears or 'non'})", sheep and shears):
            return
        tool = give(ctx, "a", shears)
        eventually(lambda: seen(port, sheep), timeout=15)
        ev(H, 'EClass.pc.stamina.Set(EClass.pc.stamina.max / 2); "ok"')
        time.sleep(2)
        pos = ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {sheep}); return m.pos.x + "," + m.pos.z;').split(",")
        h0, bag0 = stamina(H, h_uid), bag_size(H, uid)
        r = use_held(port, tool, at=(int(pos[0]), int(pos[1])), pick="i.act is AI_Shear")
        log(f"l'invite tond : {r}")
        sheared = lambda p: ev(p, f'var m = EClass._map.charas.Find(x => x.uid == {sheep}); return (m != null && m.c_fur < 0).ToString();') == "True"  # noqa: E731
        check("la tonte a eu lieu, chez l'host", eventually(lambda: awake(port) and sheared(H), timeout=60))
        time.sleep(2)
        check(f"l'host n'a pas perdu d'endurance ({h0} -> {stamina(H, h_uid)})", stamina(H, h_uid) >= h0)
        check(f"la laine est dans le sac de l'invite, chez l'host et chez lui ({bag0} -> {bag_size(H, uid)} et {bag_size(port, uid)})",
              eventually(lambda: bag_size(H, uid) > bag0 and bag_size(H, uid) == bag_size(port, uid), timeout=10))
    finally:
        ev(port, f'EClass.core.config.game.ignoreWarnSlaughter = {was.lower()}; EClass.pc.SetNoGoal(); "ok"')
        drop(made)


def punishment(port, uid):
    """colere / boules de punition / jours avec le dieu de ce personnage, vus par ce jeu"""
    return ev(port, f'var c = {chara(port, uid)}; return c.conditions.Count(x => x is ConWrath) + "/" + '
                    'c.things.Count(t => t.id == "punish_ball") + "/" + c.c_daysWithGod;')


def clear_wrath(ctx):
    port, uid = ctx["a"]
    code = (f'var c = {chara(H, uid)}; foreach (var x in c.conditions.Where(k => k is ConWrath).ToList()) x.Kill(); '
            'foreach (var t in c.things.Where(t => t.id == "punish_ball").ToList()) t.Destroy(); c.hp = c.MaxHP; "ok"')
    ev(H, code)
    if not eventually(lambda: punishment(port, uid).startswith("0/0/"), timeout=8):
        ev(port, code.replace(chara(H, uid), chara(port, uid)))


def set_days(ctx, days):
    port, uid = ctx["a"]
    ev(H, f'{chara(H, uid)}.c_daysWithGod = {days}; "ok"')
    ev(port, f'EClass.pc.c_daysWithGod = {days}; "ok"')


def join(ctx, god, campaign=False):
    """L'invite adopte ce dieu (champ de ReligionManager, ou "id:xxx") dans son jeu, ce que fait le dialogue de l'autel ;
    on attend que l'host le voie."""
    port, uid = ctx["a"]
    kind = ", Religion.ConvertType.Campaign" if campaign else ""
    religion = f'EClass.game.religions.Find("{god[3:]}")' if god.startswith("id:") else f"EClass.game.religions.{god}"
    ev(port, f'{religion}.JoinFaith(EClass.pc{kind}); "ok"')
    want = ev(port, f'{religion}.id')
    ok = eventually(lambda: ev(H, f'{chara(H, uid)}.faith.id') == want, timeout=15)
    time.sleep(3)
    return ok


def e3(ctx):
    """quitter son dieu : la punition de l'ancien dieu, une fois, chez l'host ; les jours repartent de 0"""
    port, uid = ctx["a"]
    was = ev(H, f'{chara(H, uid)}.faith.id')
    days = ev(port, 'EClass.pc.c_daysWithGod.ToString()')
    try:
        # (a) d'un dieu a un autre : colere
        check("l'invite suit le vent (conversion de campagne, sans punition), vu par l'host", join(ctx, "Wind", campaign=True))
        clear_wrath(ctx)
        set_days(ctx, 50)
        ok = join(ctx, "Earth")
        h, g = punishment(H, uid), punishment(port, uid)
        check(f"l'invite change de dieu, l'host le voit ({ev(H, chara(H, uid) + '.faith.id')})", ok)
        check(f"une colere et une boule, une seule, jours remis a 0 : chez l'host ({h})", h == "1/1/0")
        check(f"chez l'invite ({g})", eventually(lambda: punishment(port, uid) == "1/1/0", timeout=10))

        # (b) les deux dieux cousins : pas de punition
        clear_wrath(ctx)
        join(ctx, "Trickery", campaign=True)
        clear_wrath(ctx)
        set_days(ctx, 50)
        join(ctx, "MoonShadow")
        h = punishment(H, uid)
        check(f"de Ruse a Ombre de lune : pas de punition, jours remis a 0 ({h})", h == "0/0/0")
        check(f"l'invite voit la meme chose ({punishment(port, uid)})", eventually(lambda: punishment(port, uid) == "0/0/0", timeout=10))

        # (c) conversion de campagne : pas de punition, les jours continuent
        set_days(ctx, 50)
        join(ctx, "Healing", campaign=True)
        h = punishment(H, uid)
        check(f"conversion de campagne : pas de punition, jours gardes ({h})", h == "0/0/50")
        check(f"l'invite voit la meme chose ({punishment(port, uid)})", eventually(lambda: punishment(port, uid) == "0/0/50", timeout=10))

        # (d) en partant de « sans dieu » : rien a punir
        join(ctx, "Eyth", campaign=True)
        clear_wrath(ctx)
        set_days(ctx, 50)
        join(ctx, "Wind")
        h = punishment(H, uid)
        check(f"de « sans dieu » a un dieu : pas de punition, jours remis a 0 ({h})", h == "0/0/0")
    finally:
        clear_wrath(ctx)
        join(ctx, f"id:{was}", campaign=True)
        set_days(ctx, int(days))


def e4(ctx):
    """source chaude : l'invite se repose dans l'eau chaude, son compagnon prend le bain avec lui"""
    port, uid = ctx["a"]
    spot = ev(H, 'var b = EClass._map.bounds; for (var x = b.x; x <= b.maxX; x++) for (var z = b.z; z <= b.maxZ; z++) { '
                 'var p = new Point(x, z); if (p.IsValid && p.cell.IsTopWaterAndNoSnow && !p.IsBlocked && !p.HasChara && !p.HasThing) '
                 'return p.x + "," + p.z; } return "";')
    if not spot:
        print("    [SAUTE] E4 : pas de case d'eau ou se tenir sur cette carte, le geste ne peut pas etre joue ici")
        return
    x, z = (int(v) for v in spot.split(","))
    comp = tame(ctx, "cat")
    if not check(f"l'invite a un compagnon ({comp})", comp):
        return
    has = lambda p, who: ev(p, f'var c = EClass._map.charas.Find(x => x.uid == {who}); return (c != null && c.HasCondition<ConHotspring>()).ToString();') == "True"  # noqa: E731
    try:
        ev(H, 'EClass._zone.elements.SetBase(3701, 1); "ok"')
        # la source chaude n'est donnee qu'a qui est en sous-vetements (la cabine d'essayage) : mis ici, dans les deux jeux
        ev(port, 'EClass.pc.SetPCCState(PCCState.Undie); "ok"')
        time.sleep(2)
        ev(H, f'var c = {chara(H, uid)}; if (c.IsPCC && c.pccData.state != PCCState.Undie) c.SetPCCState(PCCState.Undie); "ok"')
        if not check(f"l'invite se tient dans l'eau ({spot}), vu par l'host", stand(port, uid, x, z)):
            return
        ev(port, 'EClass.pc.sleepiness.Set(0); EClass.pc.SetNoGoal(); "ok"')
        time.sleep(2)
        ev(port, 'EClass.pc.UseAbility("AI_Meditate", EClass.pc); "ok"')
        got = eventually(lambda: awake(port) and has(H, uid), timeout=150)
        check("l'invite a la source chaude, chez l'host", got)
        check("son compagnon aussi, chez l'host", eventually(lambda: has(H, comp), timeout=10))
        check("l'invite voit les deux", eventually(lambda: has(port, uid) and has(port, comp), timeout=10))
        log(f"l'host (pas du groupe de l'invite) l'a : {has(H, ctx['h'][1])}")
    finally:
        ev(port, 'EClass.pc.SetNoGoal(); EClass.pc.SetPCCState(PCCState.Normal); "ok"')
        ev(H, f'EClass._zone.elements.SetBase(3701, 0); foreach (var c in EClass._map.charas.ToList()) c.RemoveCondition<ConHotspring>(); '
              f'var g = {chara(H, uid)}; if (g.IsPCC) g.SetPCCState(PCCState.Normal); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [e1, e3, e2, e4]
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
                print(f"    capture {name} : {shot(f'equal2-{step.__name__}-{name}', port)}")
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
