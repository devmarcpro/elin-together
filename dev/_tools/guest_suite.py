"""Ce qu'un invite perd par rapport a l'host, sur la meme carte. Test court, sur des instances deja lancees
(host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/guest_suite.py            # ou --only g5,g3

Demande de l'utilisateur (2026-10-02, apres une soiree jouee en invite) : chercher ce que le jeu ne fait que
pour "le joueur" et qu'un invite perd. Liste et causes : PLAN_egalite_invites.md. Chaque test fait le meme geste
deux fois, par l'invite puis par l'host, et compare ce que chacun obtient.

G1  se reposer rend des points de vie a l'invite comme a l'host
G2  a la peche, l'invite a les memes chances de prise bonus que l'host
G3  la baguette de l'invite agit sur le monde et s'use
G4  coffres de pari : l'invite les ouvre lui-meme, ils s'usent, l'host n'est pas interrompu
    (vu le 2026-10-02 : les coffres de l'invite ne s'usaient jamais, il continuait jusqu'a mourir d'epuisement)
G5  l'invite remplit une bouteille vide a un point d'eau

La torche a allumer (TraitToolTorch) n'est portee par aucun objet du jeu en EA 23.351 : pas de test.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, dismiss_dialogs, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552


def chara(port, uid):
    """Le personnage de ce joueur, vu par ce jeu (expression C#)."""
    return f"EClass._map.charas.Find(x => x.uid == {uid})"


def first_id(trait):
    """Premier objet du jeu qui a ce trait."""
    return ev(H, f'var r = EClass.sources.things.rows.FirstOrDefault(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "{trait}"); '
                 'return r == null ? "" : r.id;')


def give(ctx, who, thing_id, num=1, extra=""):
    """L'host met un objet dans le sac de ce joueur ; renvoie son numero une fois arrive chez lui."""
    port, uid = ctx[who]
    made = ev(H, f'var c = {chara(H, uid)}; var t = ThingGen.Create("{thing_id}"); t.SetNum({num}); {extra} '
                 'var r = c.AddThing(t, false); return r.uid.ToString();')
    eventually(lambda: ev(port, f'(EClass.pc.things.Find(x => x.uid == {made}) != null).ToString()') == "True", timeout=10)
    return int(made)


def count(port, uid, thing_id):
    """Nombre d'objets de ce type dans le sac de ce joueur, vu par ce jeu."""
    return int(ev(port, f'var c = {chara(port, uid)}; return c == null ? "-1" : c.things.Where(t => t.id == "{thing_id}").Sum(t => t.Num).ToString();'))


def use_held(port, uid, at=None, pick="true"):
    """Clic droit avec cet objet en main, sur une case (la sienne par defaut), comme un joueur : le jeu construit
    la liste des actions possibles, on prend la premiere qui verifie `pick` (condition C# sur `i`), on l'execute."""
    target = "EClass.pc.pos" if at is None else f"new Point({at[0]}, {at[1]})"
    return ev(port,
              f'var t = EClass.pc.things.Find(x => x.uid == {uid}); if (t == null) return "objet absent du sac"; '
              'EClass.pc.HoldCard(t); var hot = new HotItemHeld(t); hot.OnSetCurrentItem(); '
              f'var p = new ActPlan {{ input = ActInput.RightMouse }}; p.pos.Set({target}); p.dist = EClass.pc.pos.Distance(p.pos); '
              'HarmonyLib.AccessTools.Field(typeof(ActPlan), "_canInteractNeighbor").SetValue(p, p.dist <= 1); '
              'hot.TrySetAct(p); var offered = string.Join(",", p.list.Select(i => i.act is DynamicAct d ? d.id : i.act.GetType().Name)); '
              f'var item = p.list.FirstOrDefault(i => {pick}); if (item == null) return "action absente, proposees : " + offered; '
              'item.Perform(); return "ok " + (item.act is DynamicAct x ? x.id : item.act.GetType().Name) + " parmi " + offered;')


def both(ctx):
    """Les deux joueurs, l'invite d'abord : (nom, cle)."""
    return (("l'invite", "a"), ("l'host", "h"))


# ---------------------------------------------------------------------------------------------------------------

def water_spot(ctx):
    """Une case d'eau de la carte et, a cote, une case ou se tenir : "x,z,x,z" ou ""."""
    return ev(H, 'var b = EClass._map.bounds; for (var x = b.x; x <= b.maxX; x++) for (var z = b.z; z <= b.maxZ; z++) { '
                 'var p = new Point(x, z); if (!p.cell.IsTopWaterAndNoSnow) continue; '
                 'for (var dx = -1; dx <= 1; dx++) for (var dz = -1; dz <= 1; dz++) { var n = new Point(p.x + dx, p.z + dz); '
                 'if (n.IsValid && n.IsInBounds && !n.cell.IsTopWaterAndNoSnow && !n.IsBlocked && !n.HasChara) return p.x + "," + p.z + "," + n.x + "," + n.z; } } '
                 'return "";')


def stand(port, uid, x, z):
    """Le joueur va sur cette case (deplacement direct, pour la mise en place seulement)."""
    ev(port, f'EClass.pc.Teleport(new Point({x}, {z}), true, true); "ok"')
    return eventually(lambda: ev(H, f'var c = {chara(H, uid)}; return c.pos.x + "," + c.pos.z;') == f"{x},{z}", timeout=10)


def g5(ctx):
    """bouteille vide : au bord de l'eau, « remplir » use une bouteille et donne une bouteille d'eau, pour l'invite comme pour l'host"""
    spot = water_spot(ctx)
    if not check(f"la carte a de l'eau avec une case libre a cote ({spot or 'non'})", bool(spot)):
        return
    wx, wz, sx, sz = (int(v) for v in spot.split(","))
    for who, key in both(ctx):
        port, uid = ctx[key]
        if not check(f"{who} se place au bord de l'eau", stand(port, uid, sx, sz)):
            continue
        bottle = give(ctx, key, "potion_empty", 3)
        # l'eau puisee est une potion tiree au hasard : on compte tout ce qui se boit, hors bouteilles vides
        full = lambda p, u=uid: int(ev(p, f'{chara(p, u)}.things.Where(t => t.trait is TraitDrink && !(t.trait is TraitPotionEmpty)).Sum(t => t.Num).ToString()'))  # noqa: E731
        before = (count(H, uid, "potion_empty"), full(H))
        r = use_held(port, bottle, at=(wx, wz))
        log(f"{who} : {r}")
        time.sleep(3)
        after = (count(H, uid, "potion_empty"), full(H))
        mine = (count(port, uid, "potion_empty"), full(port))
        check(f"{who} : une bouteille vide en moins (chez l'host : {before[0]} -> {after[0]})", after[0] == before[0] - 1)
        check(f"{who} : une bouteille d'eau en plus (chez l'host : {before[1]} -> {after[1]})", after[1] == before[1] + 1)
        check(f"{who} : son propre jeu dit pareil (vides {mine[0]}, eau {mine[1]})", mine == after)
        # la place pour le suivant
        ev(port, f'EClass.pc.Teleport(EClass.pc.pos.GetNearestPoint(false, false, false, true), true, true); "ok"')
        time.sleep(1)


def g4(ctx):
    """coffres de pari : celui qui les utilise les ouvre lui-meme, un par un, jusqu'au dernier ; personne d'autre n'est interrompu"""
    chest = first_id("GambleChest")
    if not check(f"le jeu a un coffre de pari ({chest})", bool(chest)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        c = give(ctx, key, chest, 4, extra="t.c_lockLv = 1;")
        ev(port, 'EClass.pc.stamina.Set(EClass.pc.stamina.max); "ok"')
        tired = int(ev(port, 'EClass.pc.stamina.value.ToString()'))
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {c}); t.trait.OnUse(EClass.pc); "ok"')
        time.sleep(1)
        busy = ev(other, 'EClass.pc.ai.GetType().Name')
        check(f"{who} ouvre ses coffres : l'autre joueur n'est pas mis a l'ouvrage (il fait : {busy})", busy != "AI_OpenGambleChest")
        left = lambda p, u=uid: count(p, u, chest)  # noqa: E731
        used = eventually(lambda: left(H) == 0, timeout=15)
        # occupe = l'action tourne encore (une action finie reste affichee jusqu'au prochain geste du joueur)
        busy_now = 'return EClass.pc.ai is AI_OpenGambleChest && EClass.pc.ai.IsRunning ? "AI_OpenGambleChest en cours" : "libre";'
        # le dernier coffre use arrive chez lui un instant apres : c'est la qu'il s'arrete
        if used:
            eventually(lambda: ev(port, busy_now) == "libre", timeout=5)
        doing = ev(port, busy_now)
        # sans attendre : des coffres qui ne s'usent pas se rouvrent sans fin, et chaque essai fatigue
        ev(port, 'if (EClass.pc.ai is AI_OpenGambleChest) EClass.pc.SetNoGoal(); "ok"')
        tired -= int(ev(port, 'EClass.pc.stamina.value.ToString()'))
        check(f"{who} : les 4 coffres sont uses (reste chez l'host : {left(H)})", used)
        check(f"{who} : chez lui aussi (reste : {left(port)})", eventually(lambda: left(port) == 0, timeout=10))
        check(f"{who} : il s'arrete une fois les coffres finis ({doing})", doing == "libre")
        check(f"{who} : 4 coffres ne coutent pas plus de 4 points d'endurance (perdus : {tired})", tired <= 4)
        ev(port, 'EClass.pc.stamina.Set(EClass.pc.stamina.max); "ok"')


BONUS = ('new[] { "book_ancient", "medal", "plat", "scratchcard", "casino_coin", "gacha_coin", "659", "758", "759", "806", "828", "1190", "1191" }')


def g2(ctx):
    """peche : sur 4000 prises, l'invite a autant de prises bonus (livres anciens, medailles, platine, jetons) que l'host"""
    rates = {}
    for who, key in both(ctx):
        _, uid = ctx[key]
        r = ev(H, f'var c = {chara(H, uid)}; var bonus = {BONUS}; var n = 0; var got = 0; var fished = EClass.player.fished; '
                  'var artifact = EClass.player.fishArtifact; '
                  'for (var i = 0; i < 4000; i++) { var t = AI_Fish.Makefish(c); if (t == null) continue; n++; if (bonus.Contains(t.id)) got++; t.Destroy(); } '
                  'EClass.player.fished = fished; EClass.player.fishArtifact = artifact; return got + "/" + n;', timeout=300)
        got, n = (int(v) for v in r.split("/"))
        rates[key] = got / max(1, n)
        log(f"{who} : {got} prises bonus sur {n} prises ({100 * rates[key]:.1f} %)")
    check(f"l'invite a au moins la moitie des prises bonus de l'host ({100 * rates['a']:.1f} % contre {100 * rates['h']:.1f} %)",
          rates["a"] >= rates["h"] / 2)
    # et une vraie peche de l'invite, canne en main au bord de l'eau, jusqu'a la premiere prise
    spot = water_spot(ctx)
    rod = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.elements != null && x.elements.Length > 0 && x.elements[0] == 245); return r == null ? "" : r.id;')
    bait = first_id("Bait")
    if not check(f"de quoi pecher pour de vrai (eau : {spot or 'non'}, canne : {rod}, appat : {bait})", bool(spot and rod and bait)):
        return
    port, uid = ctx["a"]
    wx, wz, sx, sz = (int(v) for v in spot.split(","))
    stand(port, uid, sx, sz)
    tool = give(ctx, "a", rod)
    give(ctx, "a", bait, 10)
    ev(port, 'EClass.pc.elements.SetBase(245, 40); EClass.pc.stamina.Set(EClass.pc.stamina.max); "ok"')
    bag = lambda p: int(ev(p, f'{chara(p, uid)}.things.Sum(t => t.Num).ToString()'))  # noqa: E731
    time.sleep(2)
    before = bag(H)
    log(f"l'invite : {use_held(port, tool, at=(wx, wz))}")
    check("l'invite se met a pecher", eventually(lambda: ev(port, 'EClass.pc.ai.GetType().Name') == "AI_Fish", timeout=10))
    # une prise coute un appat et rapporte au moins un objet : le sac change
    caught = eventually(lambda: bag(H) != before and ev(H, f'{chara(H, uid)}.things.Find(t => t.id == "{bait}") == null ? "0" : '
                                                         f'{chara(H, uid)}.things.Find(t => t.id == "{bait}").Num.ToString()') != "10", timeout=150)
    check(f"l'invite attrape quelque chose (sac chez l'host : {before} -> {bag(H)} objets)", caught)
    ev(port, 'EClass.pc.SetNoGoal(); "ok"')
    time.sleep(2)
    check(f"son jeu et celui de l'host voient le meme sac ({bag(port)} et {bag(H)} objets)", eventually(lambda: bag(port) == bag(H), timeout=10))


def rest(ctx, key, seconds=25):
    """Ce joueur, blesse, se repose (touche « mediter ») : points de vie gagnes et tours passes, vus de chez l'host."""
    port, uid = ctx[key]
    dismiss_dialogs(port)
    ev(H, f'var c = {chara(H, uid)}; c.hp = 1; "ok"')
    ev(port, 'EClass.pc.sleepiness.Set(0); EClass.pc.SetNoGoal(); "ok"')
    time.sleep(2)
    hp0 = int(ev(H, f'{chara(H, uid)}.hp.ToString()'))
    turn0 = int(ev(port, 'EClass.pc.turn.ToString()'))
    ev(port, 'EClass.pc.UseAbility("AI_Meditate", EClass.pc); "ok"')
    time.sleep(seconds)
    doing = ev(port, 'EClass.pc.ai.GetType().Name')
    asleep = ev(port, '(EClass.pc.conSleep != null).ToString()') == "True"
    hp1 = int(ev(H, f'{chara(H, uid)}.hp.ToString()'))
    turn1 = int(ev(port, 'EClass.pc.turn.ToString()'))
    ev(port, 'EClass.pc.SetNoGoal(); "ok"')
    return {"hp": hp1 - hp0, "turns": turn1 - turn0, "doing": doing, "asleep": asleep,
            "max": int(ev(H, f'{chara(H, uid)}.MaxHP.ToString()'))}


def g1(ctx):
    """repos : blesse, l'invite qui medite regagne ses points de vie au meme rythme que l'host"""
    got = {}
    for who, key in both(ctx):
        got[key] = r = rest(ctx, key)
        log(f"{who} : +{r['hp']} points de vie en {r['turns']} tours (max {r['max']}), il fait : {r['doing']}, endormi : {r['asleep']}")
        check(f"{who} se repose sans s'endormir ni demander a dormir", not r["asleep"])
    per = {k: 100 * v["hp"] / max(1, v["turns"]) for k, v in got.items()}
    check(f"les tours passent pour les deux (invite {got['a']['turns']}, host {got['h']['turns']})",
          got["a"]["turns"] > 20 and got["h"]["turns"] > 20)
    check(f"l'invite regagne au moins la moitie de ce que regagne l'host, par 100 tours ({per['a']:.0f} contre {per['h']:.0f})",
          per["a"] >= per["h"] / 2)


def g3(ctx):
    """baguette : l'invite vise un monstre, la baguette le blesse et perd une charge, comme pour l'host"""
    # une baguette quelconque, reglee sur la fleche de feu (element 50500, effet Arrow), 5 charges
    # (7004 est le modele "fleche de <element>", sans element : la baguette plante)
    rod, fire = "rod_random", 50500
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        r = give(ctx, key, rod, extra=f"TraitRod.Create(t, {fire}, 5);")
        check(f"{who} a une baguette de fleche de feu a 5 charges",
              ev(port, f'var x = EClass.pc.things.Find(y => y.uid == {r}); return x.refVal + "/" + x.c_charges;') == f"{fire}/5")
        # une cible a cote, qui ne se defend pas (un monstre qui riposte tue un personnage tout neuf)
        mob = ev(H, f'var c = {chara(H, uid)}; var p = c.pos.GetNearestPoint(false, false, true, true); '
                    'var m = CharaGen.Create("putty"); EClass._zone.AddCard(m, p); m.hostility = Hostility.Neutral; '
                    'm.c_originalHostility = Hostility.Neutral; m.hp = m.MaxHP; m.AddCondition<ConParalyze>(2000, true); '
                    'return m.uid + "," + m.pos.x + "," + m.pos.z + "," + m.hp;')
        muid, mx, mz, mhp = (int(v) for v in mob.split(","))
        try:
            time.sleep(2)
            res = use_held(port, r, at=(mx, mz), pick="i.act is ActZap")
            log(f"{who} : {res}")
            time.sleep(3)
            hp = ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {muid}); return m == null || m.isDead ? "mort" : m.hp.ToString();')
            charges = lambda p, u=uid, t=r: ev(p, f'var c = {chara(p, u)}; var x = c.things.Find(y => y.uid == {t}); return x == null ? "absente" : x.c_charges.ToString();')  # noqa: E731
            check(f"{who} : la cible est touchee (points de vie chez l'host : {mhp} -> {hp})", hp == "mort" or int(hp) < mhp)
            check(f"{who} : la baguette a perdu une charge chez l'host (5 -> {charges(H)})", charges(H) == "4")
            check(f"{who} : et chez l'autre joueur ({charges(other)}), comme chez lui ({charges(port)})",
                  charges(A) == "4" and charges(H) == "4")
        finally:
            ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {muid}); if (m != null) m.Destroy(); "ok"')
            ev(port, 'EClass.pc.SetNoGoal(); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [g5, g3, g2, g1, g4]
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
                print(f"    capture {name} : {shot(f'guest-{step.__name__}-{name}', port)}")
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
