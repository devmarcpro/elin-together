"""Deuxieme chasse aux differences host / invite (PLAN_chasse_differences_2.md) : le meme geste par l'invite puis par
l'host. Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/hunt2_suite.py            # ou --only e1,e3

E1  tailler un rondin a la hache (ligne 2) : la planche sort et le rondin baisse, chez l'host aussi.
E2  priere (ligne 5) : celui qui prie est soigne, et son compagnon aussi.
E4  priere sans dieu (ligne 25) : pas de soin.
E5  un jour passe (ligne 33) : compteur de jours et cout de relance des quetes, chez l'invite aussi.
E3  nourriture du sac (ligne 6) : elle vieillit d'heure en heure dans le sac de l'invite comme dans celui de l'host.
E6  offrande sur l'autel d'un autre dieu (ligne 10) : le duel de conversion donne le meme dieu a l'autel dans les deux jeux
    (8 offrandes de suite), et l'artefact du dieu de l'autel est reforge a cote de celui qui l'offre, chez les deux.

Ce que le banc ne joue pas comme un joueur :
- E2 : la priere est l'acte du jeu (ACT 6050, ce que fait le bouton) ; les points de vie sont baisses par l'host.
- E3 : le temps est avance d'un coup de trois heures chez l'host (GameDate.AdvanceMin, ce que fait une attente).
- E6 : le clic gauche sur l'autel, le menu du jeu et la vraie fenetre d'offrande sont joues, mais le glisser a la souris
  est remplace par le depot (InvOwnerDraglet.OnProcess, comme g10) ; le dieu de l'autel est pose par SetDeity (un joueur
  le trouve ou le fait changer en jeu) ; la valeur de l'offrande est reglee par le nombre d'objets (environ 200, une
  chance sur deux de gagner), pas par un vrai objet precieux ; l'autre joueur est teleporte loin (mise en place), pour
  que l'artefact dise lequel des deux est son voisin ; vie et conditions de colere sont remises a neuf entre deux essais
  (sinon un deuxieme duel perdu tuerait le joueur) ; un joueur sans dieu rejoint le vent (JoinFaith, comme e2).
  Il ne prouve pas non plus : un pair d'une ancienne version (graine absente), ni le glisser d'un artefact au clavier.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import (LAYERS, awake, both, chara, clear_conditions, close_layers, count, give, give_made, stand, tame,  # noqa: E402
                         use_held, use_menu)
from equal2_suite import drop  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from setting_suite import furniture, thing  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552


def e1(ctx):
    """tailler un rondin a la hache : la planche sort et le rondin baisse, pour l'invite comme pour l'host"""
    axe = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.elements != null && x.elements.Length > 0 && x.elements.Contains(225) '
                '&& x.trait != null && x.trait.Length > 0 && x.trait[0].StartsWith("Tool")); return r == null ? "" : r.id;')
    if not check(f"le jeu a une hache ({axe})", bool(axe)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        x, z = (int(v) for v in ev(H, f'var p = {chara(H, uid)}.pos.GetNearestPoint(false, false, false, true); return p.x + "," + p.z;').split(","))
        logs = int(ev(H, f'var t = ThingGen.Create("log"); t.SetNum(3); EClass._zone.AddCard(t, new Point({x}, {z})); return t.uid.ToString();'))
        left = lambda p: ev(p, f'var t = EClass._map.things.Find(m => m.uid == {logs}); return t == null ? "0" : t.Num.ToString();')  # noqa: E731
        planks = lambda p: int(ev(p, f'({chara(p, uid)}.things.Where(t => t.id == "plank").Sum(t => t.Num) + '  # noqa: E731
                                     f'EClass._map.things.Where(t => t.id == "plank" && t.pos.Distance(new Point({x}, {z})) <= 2).Sum(t => t.Num)).ToString()'))
        try:
            eventually(lambda: left(port) == "3", timeout=10)
            tool = give(ctx, key, axe)
            p0 = planks(H)
            awake(port)
            log(f"{who} taille : {use_held(port, tool, at=(x, z), pick='i.act is TaskChopWood')}")
            check(cond=eventually(lambda: awake(port) and int(left(H)) < 3, timeout=60), label=f"{who} : le rondin baisse, chez l'host (3 -> {left(H)})")
            check(cond=eventually(lambda: planks(H) > p0, timeout=15), label=f"{who} : des planches sortent, chez l'host ({p0} -> {planks(H)})")
            check(cond=eventually(lambda: left(port) == left(H) and planks(port) == planks(H), timeout=15),
                  label=f"{who} : son jeu voit pareil (rondins {left(port)}, planches {planks(port)})")
        finally:
            ev(port, 'EClass.pc.SetNoGoal(); "ok"')
            time.sleep(1)
            ev(H, f'var t = EClass._map.things.Find(m => m.uid == {logs}); if (t != null) t.Destroy(); '
                  f'foreach (var k in EClass._map.things.Where(t => t.id == "plank" && t.pos.Distance(new Point({x}, {z})) <= 2).ToList()) k.Destroy(); '
                  f'var c = {chara(H, uid)}; foreach (var k in c.things.Where(t => t.id == "plank" || t.id == "{axe}").ToList()) k.Destroy(); "ok"')


def e2(ctx):
    """priere : celui qui prie est soigne, et son compagnon aussi, l'invite comme l'host"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        pet = tame(ctx, "cat", key)
        if not check(f"{who} a un compagnon ({pet})", bool(pet)):
            continue
        try:
            clear_conditions(pet)
            ev(port, 'if (EClass.pc.faith == null || EClass.pc.faith.IsEyth) EClass.game.religions.Wind.JoinFaith(EClass.pc, Religion.ConvertType.Campaign); '
                     'EClass.player.prayed = false; "ok"')
            time.sleep(3)
            ev(H, f'foreach (var u in new[] {{ {uid}, {pet} }}) {{ var c = EClass._map.charas.Find(x => x.uid == u); c.hp = System.Math.Max(1, c.MaxHP / 4); }} "ok"')
            hp = lambda u: ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {u}); return c.hp + "/" + c.MaxHP;')  # noqa: E731
            full = lambda u: (lambda a, b: int(a) >= int(b) - 1)(*hp(u).split("/"))  # noqa: E731
            time.sleep(2)
            before = (hp(uid), hp(pet))
            awake(port)
            ev(port, 'ACT.Create(6050).Perform(EClass.pc); "ok"')
            check(cond=eventually(lambda: full(uid), timeout=15), label=f"{who} prie : il est soigne, chez l'host ({before[0]} -> {hp(uid)})")
            check(cond=eventually(lambda: full(pet), timeout=10), label=f"{who} : son compagnon aussi ({before[1]} -> {hp(pet)})")
        finally:
            drop([pet])
            ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; "ok"')


def e3(ctx):
    """nourriture du sac : elle vieillit d'heure en heure, dans le sac de l'invite comme dans celui de l'host"""
    food = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.category == "meat" || x._origin == "meat"); return r == null ? "meat" : r.id;')
    made = {}
    for who, key in both(ctx):
        port, uid = ctx[key]
        made[key] = give_made(ctx, key, f'var t = ThingGen.Create("{food}"); t.decay = 0;')
    age = lambda p, key: int(ev(p, f'var t = {chara(p, ctx[key][1])}.things.Find(x => x.uid == {made[key]}); return t == null ? "-1" : t.decay.ToString();'))  # noqa: E731
    try:
        if not check(f"chaque joueur a une viande fraiche ({food}) dans son sac, qui peut vieillir",
                     all(age(H, k) == 0 for k in made) and ev(H, f'({chara(H, ctx["a"][1])}.things.Find(x => x.uid == {made["a"]}).trait.Decay != 0).ToString()') == "True"):
            return
        ev(H, 'EClass.world.date.AdvanceMin(180); "ok"', timeout=300)
        time.sleep(6)
        for who, key in both(ctx):
            port = ctx[key][0]
            check(cond=eventually(lambda: age(H, key) > 0, timeout=20), label=f"{who} : trois heures plus tard sa viande a vieilli, chez l'host ({age(H, key)})")
            check(cond=eventually(lambda: age(port, key) > 0, timeout=20), label=f"{who} : et dans son jeu ({age(port, key)})")
        check(f"elles ont vieilli pareil chez l'host (invite {age(H, 'a')}, host {age(H, 'h')})", age(H, "a") == age(H, "h"))
    finally:
        for key in made:
            ev(H, f'var t = {chara(H, ctx[key][1])}.things.Find(x => x.uid == {made[key]}); if (t != null) t.Destroy(); "ok"')


def e4(ctx):
    """priere sans dieu (ligne 25) : pas de soin, pour l'invite comme pour l'host"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        old = ev(port, 'EClass.pc.faith.id')
        try:
            for p in {port, H}:
                ev(p, f'{chara(p, uid)}.SetFaith("eyth"); "ok"')
            ev(port, 'EClass.player.prayed = false; "ok"')
            ev(H, f'var c = {chara(H, uid)}; c.hp = System.Math.Max(1, c.MaxHP / 4); "ok"')
            time.sleep(3)
            hp = lambda: ev(H, f'var c = {chara(H, uid)}; return c.hp + "/" + c.MaxHP;')  # noqa: E731
            before = hp()
            awake(port)
            ev(port, 'ACT.Create(6050).Perform(EClass.pc); "ok"')
            time.sleep(6)
            a, b = (int(v) for v in hp().split("/"))
            check(f"{who} sans dieu prie : pas de soin, chez l'host ({before} -> {a}/{b})", a < b // 2)
        finally:
            for p in {port, H}:
                ev(p, f'var c = {chara(p, uid)}; c.SetFaith("{old}"); c.hp = c.MaxHP; "ok"')


def e5(ctx):
    """un jour passe (ligne 33) : le compteur de jours monte et la relance du tableau de quetes baisse, chez l'invite comme chez l'host"""
    read = lambda p: tuple(int(v) for v in ev(p, 'EClass.player.stats.days + "," + EClass.player.questRerollCost').split(","))  # noqa: E731
    for p in (H, A):
        ev(p, 'EClass.player.questRerollCost = 9; EClass.player.prayed = true; "ok"')
    before = {p: read(p) for p in (H, A)}
    # heure par heure, comme une attente : un saut d'un coup arrive chez l'invite par l'instantane du monde
    for _ in range(24):
        ev(H, 'EClass.world.date.AdvanceMin(60); "ok"', timeout=300)
        time.sleep(1.5)
    time.sleep(5)
    for who, p in (("host", H), ("invite", A)):
        d, r = read(p)
        check(f"{who} : un jour de plus au compteur ({before[p][0]} -> {d})", d == before[p][0] + 1)
        check(f"{who} : la relance des quetes coute 3 de moins ({before[p][1]} -> {r})", r == 6)
        check(f"{who} : il peut de nouveau prier (la priere du jour est remise a zero)", ev(p, 'EClass.player.prayed.ToString()') == "False")


def apart(ctx, key):
    """L'autre joueur va a 8 cases ou plus de celui-ci (mise en place) : l'objet reforge dira lequel des deux est son voisin."""
    _, uid = ctx[key]
    oport, ouid = ctx["h" if key == "a" else "a"]
    spot = ev(H, f'var me = {chara(H, uid)}.pos; var b = EClass._map.bounds; for (var i = b.x; i <= b.maxX; i++) for (var j = b.z; j <= b.maxZ; j++) {{ '
                 'var p = new Point(i, j); var d = p.Distance(me); if (d >= 8 && d <= 14 && p.IsValid && p.IsInBounds && !p.IsBlocked && !p.HasChara '
                 '&& !p.cell.IsTopWaterAndNoSnow) return i + "," + j; } return "";')
    if spot:
        stand(oport, ouid, *(int(v) for v in spot.split(",")))
    return bool(spot)


def offer(port, at, item):
    """L'offrande comme un joueur : clic gauche sur l'autel, "Offrir" dans le menu du jeu, puis le depot dans la vraie
    fenetre (OnProcess du draglet, ce que fait le glisser, comme g10) ; "ok" ou ce qui a manque."""
    close_layers()
    awake(port)
    menu = use_menu(port, at, 'i.act is DynamicAct d && d.id == "actOffer"')
    if not eventually(lambda: "LayerDragGrid" in ev(port, LAYERS), timeout=8):
        return f"fenetre d'offrande absente ({menu})"
    return ev(port, f'var g = LayerDragGrid.Instance; var o = EClass.pc.things.Find(x => x.uid == {item}); '
                    'if (g == null || o == null || !EClass.ui.layers.Contains(g)) return "fenetre ou objet absent"; '
                    'var b = g.owner.buttons[g.currentIndex]; b.SetCardGrid(o, b.invOwner); g.owner.OnProcess(o); return "ok";')


def e6(ctx):
    """offrande sur l'autel d'un autre dieu (ligne 10) : le duel de conversion donne le meme dieu a l'autel chez l'host et
    chez l'invite, 8 fois de suite ; l'artefact du dieu de l'autel est reforge a cote de celui qui l'offre, chez les deux"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        other, ouid = ("l'host", ctx["h"][1]) if key == "a" else ("l'invite", ctx["a"][1])
        close_layers()
        clear_conditions(uid)
        # le duel suppose un dieu (sans dieu : "rien ne se passe")
        ev(port, 'if (EClass.pc.faith == null || EClass.pc.faith.IsEyth) EClass.game.religions.Wind.JoinFaith(EClass.pc, Religion.ConvertType.Campaign); "ok"')
        mine = ev(port, 'EClass.pc.faith.id')
        eventually(lambda: ev(H, f'{chara(H, uid)}.faith.id') == mine, timeout=10)
        # un autre dieu que le sien, qui a un artefact (pour la deuxieme partie) ; sinon n'importe quel autre
        pick = 'r.CanJoin && !r.IsEyth && r.id != "' + mine + '"'
        god = ev(H, f'var g = EClass.game.religions.list.FirstOrDefault(r => {pick} && EClass.sources.things.rows.Any(x => {{ '
                    'var d = EClass.game.religions.GetArtifactDeity(x.id); return d != null && d.id == r.id; })); '
                    f'if (g == null) g = EClass.game.religions.list.FirstOrDefault(r => {pick}); return g == null ? "" : g.id;')
        art = ev(H, f'var r = EClass.sources.things.rows.FirstOrDefault(x => {{ var d = EClass.game.religions.GetArtifactDeity(x.id); '
                    f'return d != null && d.id == "{god}"; }}); return r == null ? "" : r.id;')
        if not check(f"{who} (dieu {mine}) a un autre dieu pour l'autel ({god or 'aucun'})", bool(god)):
            continue
        check(f"{other} est a 8 cases ou plus de {who}", apart(ctx, key))
        t = furniture(uid, make='ThingGen.Create("altar")', extra=f'((TraitAltar)t.trait).SetDeity("{god}");')
        ax, az = (int(v) for v in ev(H, f'var a = {thing(t)}; return a.pos.x + "," + a.pos.z;').split(","))
        deity = lambda p: ev(p, f'var a = {thing(t)}; return a == null ? "absent" : ((TraitAltar)a.trait).idDeity;')  # noqa: E731
        balls = lambda p: count(p, uid, "punish_ball")  # noqa: E731
        try:
            # un objet que cet autel accepte de ce joueur, en nombre tel que la valeur d'offrande tourne autour de 200
            what = ev(H, f'var c = {chara(H, uid)}; var a = (TraitAltar){thing(t)}.trait; '
                         'foreach (var id in new[] { "figure" }.Concat(EClass.sources.things.rows.Where(x => x.value > 0 && EClass.sources.categories.map.ContainsKey(x.category) && c.faith.source.cat_offer.Any(k => EClass.sources.categories.map[x.category].IsChildOf(k))).Take(40).Select(x => x.id))) { '
                         'Thing o; try { o = ThingGen.Create(id); } catch { continue; } var v = c.faith.GetOfferingValue(o, 1); '
                         'var ok = v > 0 && a.CanOffer(c, o); o.Destroy(); if (ok) return id + "," + System.Math.Max(1, 200 / v); } return "";')
            if not check(f"{who} : l'autel accepte une offrande de lui ({what or 'rien'})", bool(what)):
                continue
            offering, num = what.split(",")
            wins = 0
            for n in range(1, 9):
                # remise a neuf : un deuxieme duel perdu avec la colere en cours tuerait le joueur
                clear_conditions(uid)
                for p in {H, port}:
                    ev(p, f'var c = {chara(p, uid)}; c.hp = c.MaxHP; "ok"')
                ev(H, f'foreach (var b in {chara(H, uid)}.things.Where(x => x.id == "punish_ball").ToList()) b.Destroy(); "ok"')
                for p in (H, A):
                    ev(p, f'((TraitAltar){thing(t)}.trait).SetDeity("{god}"); "ok"')
                item = give_made(ctx, key, f'var t = ThingGen.Create("{offering}"); t.SetNum({num});')
                r = offer(port, (ax, az), item)
                time.sleep(3)
                eventually(lambda: deity(H) == deity(A), timeout=6)
                won = deity(H) == mine
                wins += won
                wrath = ev(H, f'{chara(H, uid)}.HasCondition<ConWrath>().ToString()') == "True"
                check(f"{who}, offrande {n} ({r}) : le duel a eu lieu (l'autel {deity(H)}, colere {wrath})", r == "ok" and (won or wrath))
                check(f"{who}, offrande {n} : meme dieu a l'autel chez l'host et chez l'invite (host {deity(H)}, invite {deity(A)})", deity(H) == deity(A))
                if not won:
                    check(f"{who}, offrande {n} perdue : autant de boules de punition dans son sac chez les deux (host {balls(H)}, invite {balls(A)})",
                          eventually(lambda: balls(H) == balls(A) == 1, timeout=6))
            log(f"{who} : {wins} duels gagnes sur 8")
            # l'artefact du dieu de l'autel : reforge a cote de celui qui l'offre
            if not check(f"un artefact du dieu de l'autel existe ({art or 'aucun'})", bool(art)):
                continue
            clear_conditions(uid)
            for p in (H, A):
                ev(p, f'((TraitAltar){thing(t)}.trait).SetDeity("{god}"); "ok"')
            item = give_made(ctx, key, f'var t = ThingGen.Create("{art}"); t.c_idDeity = "{god}";')
            near = lambda p, u: int(ev(p, f'var c = {chara(p, u)}; return c == null ? "-1" : EClass._map.things.Count(m => m.id == "{art}" && m.pos.Distance(c.pos) <= 3).ToString();'))  # noqa: E731
            total = lambda p: int(ev(p, f'EClass._map.things.Count(m => m.id == "{art}").ToString()'))  # noqa: E731
            r = offer(port, (ax, az), item)
            check(cond=eventually(lambda: near(H, uid) == 1, timeout=10), label=f"{who} offre l'artefact ({r}) : il est reforge a cote de lui, chez l'host (pres de lui : {near(H, uid)}, en tout : {total(H)})")
            check(cond=eventually(lambda: near(port, uid) == 1 and total(port) == 1, timeout=10), label=f"{who} : et chez lui (pres de lui : {near(port, uid)}, en tout : {total(port)})")
            check(f"{who} : rien aux pieds de {other} (chez l'host {near(H, ouid)}, chez l'invite {near(A, ouid)})", near(H, ouid) == 0 and near(A, ouid) == 0)
        finally:
            close_layers()
            clear_conditions(uid)
            ev(H, f'var a = {thing(t)}; if (a != null) a.Destroy(); foreach (var k in EClass._map.things.Where(m => m.id == "{art}").ToList()) k.Destroy(); '
                  f'var c = {chara(H, uid)}; foreach (var k in c.things.Where(x => x.id == "punish_ball" || x.id == "{art}").ToList()) k.Destroy(); c.hp = c.MaxHP; "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [e1, e2, e3, e5, e4, e6]  # e4 apres e5 : la priere du jour (E2) doit etre passee
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
                print(f"    capture {name} : {shot(f'hunt2-{step.__name__}-{name}', port)}")
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
