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


def awake(port):
    """Un dialogue du jeu (tutoriel) retient le temps de ce joueur tant qu'on ne clique pas : on le ferme, comme
    lui le ferait d'un clic. Toujours vrai, pour s'enchainer dans une attente."""
    dismiss_dialogs(port)
    return True


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
        used = eventually(lambda: awake(port) and left(H) == 0, timeout=15)
        # occupe = l'action tourne encore (une action finie reste affichee jusqu'au prochain geste du joueur)
        busy_now = 'return EClass.pc.ai is AI_OpenGambleChest && EClass.pc.ai.IsRunning ? "AI_OpenGambleChest en cours" : "libre";'
        # le dernier coffre use arrive chez lui un instant apres : c'est la qu'il s'arrete
        if used:
            eventually(lambda: awake(port) and ev(port, busy_now) == "libre", timeout=8)
        doing = ev(port, busy_now)
        if doing != "libre":
            probe = ('var ai = EClass.pc.ai as AI_OpenGambleChest; return "tour " + EClass.pc.turn + " statut " + EClass.pc.ai.status + '
                     '(ai == null ? "" : " coffre " + ai.target.Num + " detruit " + ai.target.isDestroyed + " valide " + ai.IsValid()) + '
                     '" temps " + EClass.pc.roundTimer.ToString("0.00") + "/" + EClass.pc.actTime.ToString("0.00") + '
                     '" pause " + EClass.scene.paused + " fenetres " + string.Join(",", EClass.ui.layers.Select(l => l.GetType().Name));')
            log(f"{who} encore occupe : {ev(port, probe)}")
            time.sleep(3)
            log(f"{who} 3 s plus tard : {ev(port, probe)}")
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
    awake(port)
    # chez un invite l'appat s'equipe par une demande a l'host : au tout premier clic le jeu dit parfois
    # « pas d'appat » et l'appat arrive un instant apres ; le joueur reclique (petite inegalite, notee au plan)
    fishing = False
    for click in (1, 2, 3):
        log(f"l'invite, clic {click} : {use_held(port, tool, at=(wx, wz))}")
        time.sleep(3)
        if ev(port, 'EClass.pc.ai.GetType().Name') == "AI_Fish":
            fishing = True
            break
    check(f"l'invite se met a pecher (au clic {click})", fishing)
    # une prise coute un appat et rapporte au moins un objet : le sac change
    caught = eventually(lambda: awake(port) and bag(H) != before and
                        ev(H, f'{chara(H, uid)}.things.Find(t => t.id == "{bait}") == null ? "0" : '
                              f'{chara(H, uid)}.things.Find(t => t.id == "{bait}").Num.ToString()') != "10", timeout=150)
    if not caught:
        log("l'invite n'a rien pris : " + ev(port, 'var ai = EClass.pc.ai; return ai.GetType().Name + " " + ai.status + " enfant " + '
                                                  '(ai.child == null ? "aucun" : ai.child.GetType().Name + " " + ai.child.status) + " tour " + EClass.pc.turn + '
                                                  '" appat " + (EClass.player.eqBait == null ? "aucun" : EClass.player.eqBait.Num.ToString()) + '
                                                  '" fenetres " + string.Join(",", EClass.ui.layers.Select(l => l.GetType().Name));'))
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


def bag_size(port, uid):
    """Nombre total d'objets dans le sac de ce joueur, vu par ce jeu."""
    return int(ev(port, f'{chara(port, uid)}.things.Sum(t => t.Num).ToString()'))


def g6(ctx):
    """colis, maquette, paquet cadeau : ce qu'il y a dedans va dans le sac de celui qui ouvre, pas dans celui de l'host"""
    # (objet, ce que le sac gagne en l'ouvrant : le contenu moins l'objet lui-meme)
    boxes = (("Parcel", "un colis qui contient une piece de platine", 0, 't.AddCard(ThingGen.Create("plat"));'),
             ("PlamoBox", "une boite de maquette", 0, ""),
             ("GiftPack", "un paquet cadeau (3 objets)", 2, ""))
    for trait, what, gain, extra in boxes:
        box = first_id(trait)
        if not check(f"le jeu a un objet {trait} ({box})", bool(box)):
            continue
        for who, key in both(ctx):
            port, uid = ctx[key]
            okey = "h" if key == "a" else "a"
            other_port, other_uid = ctx[okey]
            b = give(ctx, key, box, extra=extra)
            time.sleep(1)
            mine, theirs = bag_size(H, uid), bag_size(H, other_uid)
            ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {b}); t.trait.OnUse(EClass.pc); "ok"')
            ok = eventually(lambda: bag_size(H, uid) == mine + gain and count(H, uid, box) == 0, timeout=10)
            check(f"{who} ouvre {what} : son sac passe de {mine} a {bag_size(H, uid)} objets (attendu {mine + gain})", ok)
            check(f"{who} : rien n'arrive dans le sac de l'autre joueur ({theirs} -> {bag_size(H, other_uid)})",
                  bag_size(H, other_uid) == theirs)
            check(f"{who} : son propre jeu voit le meme sac ({bag_size(port, uid)} objets)",
                  eventually(lambda: bag_size(port, uid) == bag_size(H, uid), timeout=10))


def g7(ctx):
    """boule de gacha : le lot tombe aux pieds de celui qui l'ouvre"""
    ball = first_id("GachaBall")
    if not check(f"le jeu a une boule de gacha ({ball})", bool(ball)):
        return
    on_tile = lambda u: int(ev(H, f'var c = {chara(H, u)}; return EClass._map.things.Count(t => t.pos.Equals(c.pos)).ToString();'))  # noqa: E731
    for who, key in both(ctx):
        port, uid = ctx[key]
        _, other_uid = ctx["h" if key == "a" else "a"]
        b = give(ctx, key, ball)
        time.sleep(1)
        mine, theirs = on_tile(uid), on_tile(other_uid)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {b}); t.trait.OnUse(EClass.pc); "ok"')
        ok = eventually(lambda: on_tile(uid) == mine + 1, timeout=10)
        check(f"{who} ouvre une boule : un objet de plus a ses pieds ({mine} -> {on_tile(uid)})", ok)
        check(f"{who} : rien aux pieds de l'autre joueur ({theirs} -> {on_tile(other_uid)})", on_tile(other_uid) == theirs)
        check(f"{who} : la boule est usee", eventually(lambda: count(H, uid, ball) == 0, timeout=10))


KNOWN = 'return string.Join(",", EClass.player.recipes.knownRecipes.Keys.OrderBy(k => k));'


def g9(ctx):
    """recette trouvee en creusant : l'idee qui vient a l'invite est connue de l'host aussi (sinon elle est
    oubliee a sa prochaine reconnexion, ou le carnet de recettes de l'host remplace le sien)"""
    port, uid = ctx["a"]
    shovel = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.elements != null && x.elements.Length > 0 && x.elements[0] == 230); return r == null ? "" : r.id;')
    if not check(f"le jeu a une pelle ({shovel})", bool(shovel)):
        return
    tool = give(ctx, "a", shovel)
    before = {p: set(ev(p, KNOWN).split(",")) for p in (H, A)}
    # le jeu tire l'idee au sort (une fois sur dix) : en mode debug du jeu, chez l'invite seulement, elle vient a coup sur
    ev(port, 'EClass.debug.enable = true; EClass.pc.stamina.Set(EClass.pc.stamina.max); "ok"')
    try:
        learnt = set()
        # les cases autour de lui, jusqu'a en trouver ou le jeu propose de creuser (pas une plante a recolter)
        around = ev(port, 'var r = new System.Collections.Generic.List<string>(); for (var dx = -1; dx <= 1; dx++) for (var dz = -1; dz <= 1; dz++) { '
                          'if (dx == 0 && dz == 0) continue; var p = new Point(EClass.pc.pos.x + dx, EClass.pc.pos.z + dz); '
                          'if (p.IsValid && p.IsInBounds && !p.IsBlocked && !p.HasChara && !p.cell.IsTopWaterAndNoSnow) r.Add(p.x + "," + p.z); } '
                          'return string.Join(";", r);')
        for spot in [s for s in around.split(";") if s]:
            x, z = (int(v) for v in spot.split(","))
            awake(port)
            r = use_held(port, tool, at=(x, z), pick="i.act is TaskDig")
            log(f"l'invite creuse en {spot} : {r}")
            if not r.startswith("ok"):
                continue
            if eventually(lambda: awake(port) and set(ev(port, KNOWN).split(",")) - before[A], timeout=20):
                learnt = set(ev(port, KNOWN).split(",")) - before[A]
                break
            ev(port, 'EClass.pc.SetNoGoal(); "ok"')
    finally:
        ev(port, 'EClass.debug.enable = false; EClass.pc.SetNoGoal(); "ok"')
    if not check(f"une idee de recette vient a l'invite en creusant ({', '.join(sorted(learnt)) or 'aucune'})", bool(learnt)):
        return
    ok = eventually(lambda: learnt <= set(ev(H, KNOWN).split(",")), timeout=10)
    check(f"l'host la connait aussi (il lui manque : {', '.join(sorted(learnt - set(ev(H, KNOWN).split(',')))) or 'rien'})", ok)


LAYERS = 'return string.Join(",", EClass.ui.layers.Select(l => l.GetType().Name));'


def g8(ctx):
    """ce qui ouvre une fenetre ou agit sur « le joueur » : chez celui qui s'en sert, pas chez l'autre
    (banque, coffre des impots, panneau des politiques, corde ; puis la pierre de retour, qui l'emmene, lui)"""
    for trait, what in (("Bank", "la banque"), ("TaxChest", "le coffre des impots"), ("PolicyBoard", "le panneau des politiques"),
                        ("Rope", "la corde")):
        item = first_id(trait)
        if not check(f"le jeu a un objet {trait} ({item})", bool(item)):
            continue
        for who, key in both(ctx):
            port, uid = ctx[key]
            other = H if port == A else A
            for p in (H, A):
                ev(p, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')
            t = give(ctx, key, item)
            time.sleep(1)
            ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {t}); t.trait.OnUse(EClass.pc); "ok"')
            time.sleep(2)
            mine, theirs = ev(port, LAYERS), ev(other, LAYERS)
            check(f"{who} se sert de {what} : la fenetre s'ouvre chez lui ({mine or 'rien'})", bool(mine))
            check(f"{who} : rien ne s'ouvre chez l'autre joueur ({theirs or 'rien'})", not theirs)
            for p in (H, A):
                ev(p, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')
            ev(H, f'var t = {chara(H, uid)}.things.Find(x => x.uid == {t}); if (t != null) t.Destroy(); "ok"')
    # la pierre de retour temporaire, en dernier : l'invite s'en va
    stone = first_id("Waystone")
    if not check(f"le jeu a une pierre de retour temporaire ({stone})", bool(stone)):
        return
    port, uid = ctx["a"]
    home = state(H)["zone"]["uid"]
    t = give(ctx, "a", stone)
    time.sleep(1)
    ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {t}); t.trait.OnUse(EClass.pc); "ok"')
    left = eventually(lambda: (state(A).get("zone") or {}).get("uid") != home and state(A).get("sceneMode") == "Zone", timeout=60)
    check(f"l'invite se sert de sa pierre : il quitte la carte (il est en : {(state(A).get('zone') or {}).get('uid')})", left)
    check(f"l'host, lui, reste sur sa carte ({(state(H).get('zone') or {}).get('uid')})", (state(H).get("zone") or {}).get("uid") == home)
    gone = ev(H, f'(EClass.game.cards.globalCharas.Find({uid}).things.Find(x => x.uid == {t}) == null).ToString()')
    check("la pierre de l'invite est usee", gone == "True")


def give_made(ctx, who, make):
    """Comme give, pour un objet que l'host fabrique par du C# (il doit laisser l'objet dans `t`)."""
    port, uid = ctx[who]
    made = ev(H, f'var c = {chara(H, uid)}; {make} var r = c.AddThing(t, false); return r.uid.ToString();')
    eventually(lambda: ev(port, f'(EClass.pc.things.Find(x => x.uid == {made}) != null).ToString()') == "True", timeout=10)
    return int(made)


def close_layers():
    for p in (H, A):
        ev(p, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')


def g10(ctx):
    """parchemin d'identification : rien n'est identifie avant que le joueur choisisse, puis l'objet choisi, lui seul"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        items = [give_made(ctx, key, 'var t = ThingGen.CreateFromCategory("armor"); t.c_IDTState = 5;') for _ in range(3)]
        # 8230 : l'identification ; ni beni (plusieurs choix) ni maudit (oubli)
        scroll = give_made(ctx, key, 'var t = ThingGen.CreateScroll(8230); t.c_IDTState = 0; t.SetBlessedState(BlessedState.Normal);')
        unknown = lambda p, u=uid: int(ev(p, f'{chara(p, u)}.things.Count(t => !t.IsIdentified).ToString()'))  # noqa: E731
        time.sleep(1)
        before = unknown(H)
        awake(port)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {scroll}); EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
        opened = eventually(lambda: "LayerDragGrid" in ev(port, LAYERS), timeout=15)
        check(f"{who} lit : la fenetre de choix s'ouvre chez lui ({ev(port, LAYERS) or 'rien'})", opened)
        check(f"{who} : rien ne s'ouvre chez l'autre joueur ({ev(other, LAYERS) or 'rien'})", "LayerDragGrid" not in ev(other, LAYERS))
        time.sleep(2)
        check(f"{who} : rien n'est identifie avant son choix (inconnus chez l'host : {before} -> {unknown(H)})", unknown(H) == before)
        pick = items[1]
        r = ev(port, f'var g = LayerDragGrid.Instance; var t = EClass.pc.things.Find(x => x.uid == {pick}); '
                     'if (g == null || t == null || !EClass.ui.layers.Contains(g)) return "fenetre ou objet absent"; '
                     'var b = g.owner.buttons[g.currentIndex]; b.SetCardGrid(t, b.invOwner); g.owner.OnProcess(t); return "ok";')
        known = lambda p: ev(p, f'var t = {chara(p, uid)}.things.Find(x => x.uid == {pick}); return t == null ? "absent" : t.IsIdentified.ToString();')  # noqa: E731
        check(f"{who} choisit un objet ({r}) : il est identifie chez l'host", eventually(lambda: known(H) == "True", timeout=10))
        check(f"{who} : un seul objet identifie en tout (inconnus : {before} -> {unknown(H)})", unknown(H) == before - 1)
        check(f"{who} : son propre jeu dit pareil", eventually(lambda: unknown(port) == unknown(H), timeout=10))
        close_layers()
        ev(H, f'var c = {chara(H, uid)}; foreach (var u in new[] {{ {", ".join(map(str, items))} }}) {{ var t = c.things.Find(x => x.uid == u); if (t != null) t.Destroy(); }} "ok"')


def g11(ctx):
    """appat : au bord de l'eau, le premier clic de peche de l'invite equipe l'appat et lance la peche, comme pour l'host"""
    spot = water_spot(ctx)
    rod = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.elements != null && x.elements.Length > 0 && x.elements[0] == 245); return r == null ? "" : r.id;')
    bait = first_id("Bait")
    if not check(f"de quoi pecher (eau : {spot or 'non'}, canne : {rod}, appat : {bait})", bool(spot and rod and bait)):
        return
    wx, wz, sx, sz = (int(v) for v in spot.split(","))
    port, uid = ctx["a"]
    stand(port, uid, sx, sz)
    tool = give(ctx, "a", rod)
    b = give(ctx, "a", bait, 10)
    worn = lambda: ev(H, f'{chara(H, uid)}.things.Any(t => t.trait is TraitBait x && x.EQ == t).ToString()')  # noqa: E731
    # appat pas encore equipe : c'est le premier clic qui doit l'equiper et lancer la peche
    ev(port, 'if (EClass.player.eqBait != null) EClass.player.eqBait.trait.OnUse(EClass.pc); "ok"')
    time.sleep(2)
    awake(port)
    r = use_held(port, tool, at=(wx, wz))
    time.sleep(2)
    doing = ev(port, 'EClass.pc.ai.GetType().Name')
    check(f"l'invite se met a pecher des le premier clic ({r} ; il fait : {doing})", doing == "AI_Fish")
    check("son appat est equipe chez lui tout de suite", ev(port, '(EClass.player.eqBait != null).ToString()') == "True")
    check("et chez l'host", eventually(lambda: worn() == "True", timeout=5))
    ev(port, 'EClass.pc.SetNoGoal(); "ok"')
    # l'appat equipe (il peut en avoir plusieurs paquets) : le retirer, puis le remettre
    worn_uid = ev(port, 'EClass.player.eqBait == null ? "0" : EClass.player.eqBait.uid.ToString()')
    for want in ("False", "True"):
        ev(port, f'EClass.pc.things.Find(x => x.uid == {worn_uid}).trait.OnUse(EClass.pc); "ok"')
        check(f"l'invite {'remet' if want == 'True' else 'retire'} son appat : pareil chez l'host",
              eventually(lambda: worn() == want and ev(port, '(EClass.player.eqBait != null).ToString()') == want, timeout=5))


def g12(ctx):
    """arrosoir : l'invite le remplit au bord de l'eau puis arrose une case, pour de vrai chez l'host"""
    can = first_id("ToolWaterCan")
    spot = water_spot(ctx)
    if not check(f"un arrosoir et de l'eau (arrosoir : {can}, eau : {spot or 'non'})", bool(can and spot)):
        return
    wx, wz, sx, sz = (int(v) for v in spot.split(","))
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        if not check(f"{who} se place au bord de l'eau", stand(port, uid, sx, sz)):
            continue
        c = give(ctx, key, can, extra="t.c_charges = 0;")
        left = lambda p, u=uid, t=c: ev(p, f'var x = {chara(p, u)}.things.Find(y => y.uid == {t}); return x == null ? "absent" : x.c_charges + "/" + (x.trait as TraitToolWaterCan).MaxCharge;')  # noqa: E731
        awake(port)
        log(f"{who} : {use_held(port, c, at=(wx, wz), pick='i.act is ActDrawWater')}")
        is_full = lambda v: "/" in v and v.split("/")[0] == v.split("/")[1] != "0"  # noqa: E731
        full = eventually(lambda: is_full(left(H)), timeout=6)
        check(f"{who} puise : l'arrosoir est plein chez l'host ({left(H)})", full)
        check(f"{who} : et chez l'autre joueur ({left(other)}), comme chez lui ({left(port)})",
              eventually(lambda: left(A) == left(H) == left(port), timeout=6))
        dry = ev(H, f'var c = {chara(H, uid)}; for (var dx = -1; dx <= 1; dx++) for (var dz = -1; dz <= 1; dz++) {{ var p = new Point(c.pos.x + dx, c.pos.z + dz); '
                    'if (p.IsValid && !p.cell.IsTopWater && !p.cell.isWatered && !p.HasChara && !p.IsFarmField) return p.x + "," + p.z; } return "";')
        if not check(f"{who} : une case seche a cote ({dry or 'aucune'})", bool(dry)):
            continue
        x, z = (int(v) for v in dry.split(","))
        n0 = int(left(H).split("/")[0] or 0) if "/" in left(H) else 0
        log(f"{who} : {use_held(port, c, at=(x, z), pick='i.act is ActWater')}")
        wet = lambda p: ev(p, f'new Point({x}, {z}).cell.isWatered.ToString()')  # noqa: E731
        check(f"{who} arrose : la case est mouillee chez l'host", eventually(lambda: wet(H) == "True", timeout=6))
        check(f"{who} : et chez l'autre joueur ({wet(other)})", eventually(lambda: wet(other) == "True", timeout=6))
        check(f"{who} : l'arrosoir a perdu de l'eau chez l'host ({n0} -> {left(H)})", int(left(H).split("/")[0]) < n0)
        ev(H, f'new Point({x}, {z}).cell.isWatered = false; "ok"')
        ev(port, 'EClass.pc.Teleport(EClass.pc.pos.GetNearestPoint(false, false, false, true), true, true); "ok"')


def read_book(ctx, key, book, timeout=90):
    port, uid = ctx[key]
    awake(port)
    ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {book}); EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
    time.sleep(2)
    return eventually(lambda: awake(port) and ev(port, 'EClass.pc.ai is AI_Read && EClass.pc.ai.IsRunning ? "lit" : "libre"') == "libre", timeout=timeout)


def g14(ctx):
    """livres : le livre ancien dechiffre reste a celui qui l'a lu ; le livre d'un dieu ne le convertit pas"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        ev(port, 'EClass.pc.elements.SetBase(285, 100); EClass.pc.RemoveCondition<ConConfuse>(); "ok"')
        eventually(lambda: int(ev(H, f'{chara(H, uid)}.Evalue(285).ToString()')) >= 100, timeout=10)
        seen = lambda p, b, u=uid: ev(p, f'var t = {chara(p, u)}.things.Find(x => x.uid == {b}); return t == null ? "disparu" : (t.isOn ? "dechiffre" : "intact") + "/" + t.c_charges;')  # noqa: E731

        book = give_made(ctx, key, 'var t = ThingGen.Create("book_ancient"); t.refVal = 0; t.c_charges = 3; t.SetBlessedState(BlessedState.Normal);')
        check(f"{who} lit un livre ancien jusqu'au bout", read_book(ctx, key, book))
        check(f"{who} : il le garde, dechiffre (chez l'host : {seen(H, book)})", seen(H, book).startswith("dechiffre"))
        check(f"{who} : chez lui aussi ({seen(port, book)})", eventually(lambda: seen(port, book).startswith("dechiffre"), timeout=10))

        faith = lambda p, u=uid: ev(p, f'{chara(p, u)}.faith.id')  # noqa: E731
        god = faith(H)
        dojin = give_made(ctx, key, 'var t = ThingGen.CreateUsuihon(EClass.game.religions.Healing); t.c_charges = 3; t.SetBlessedState(BlessedState.Normal);')
        book_god = ev(H, f'var t = {chara(H, uid)}.things.Find(x => x.uid == {dojin}); return t.c_idRefName;')
        if not check(f"{who} n'est pas deja du dieu du livre ({god} / {book_god})", god != book_god):
            continue
        check(f"{who} lit le livre d'un dieu jusqu'au bout", read_book(ctx, key, dojin))
        check(f"{who} : il garde son dieu (chez l'host : {god} -> {faith(H)})", faith(H) == god)
        check(f"{who} : son jeu et l'host disent le meme dieu ({faith(port)})", faith(port) == faith(H))
        check(f"{who} : le livre a perdu une charge, pas toutes ({seen(H, dojin)})", seen(H, dojin).endswith("/2"))
        # le livre rend fou et assomme : on remet le joueur sur pied, et son dieu si le test etait rouge
        ev(H, f'var c = {chara(H, uid)}; c.RemoveCondition<ConInsane>(); c.RemoveCondition<ConFaint>(); '
              f'if (c.faith.id != "{god}" && !c.IsPC) EClass.game.religions.Find("{god}").JoinFaith(c); '
              f'foreach (var u in new[] {{ {book}, {dojin} }}) {{ var t = c.things.Find(x => x.uid == u); if (t != null) t.Destroy(); }} "ok"')


SEEDS = ('var row = EClass.sources.objs.rows.First(o => o.HasTag(CTAG.seed) && o.growth != null && o.growth.CanLevelSeed); '
         'var seed = TraitSeed.MakeSeed(row); var plant = new PlantData { seed = seed }; var up = 0; '
         'for (var i = 0; i < 1000; i++) { var s = TraitSeed.MakeSeed(row, plant); if (s.encLV > seed.encLV) up++; s.Destroy(); } '
         'seed.Destroy(); return up.ToString();')
AS_TASK_OF = ('var prop = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.Patches.CharaProgressCompleteEvent"), "Chara"); '
              'prop.SetValue(null, c); try { %s } finally { prop.SetValue(null, null); }')


def g15(ctx):
    """graines : sur 1000 graines recoltees, celles de l'invite montent de niveau selon son Agriculture, pas celle de l'host"""
    if not check("la carte est une base (ailleurs les graines ne montent pas de niveau)", ev(H, 'EClass._zone.IsPCFactionOrTent.ToString()') == "True"):
        return
    port, uid = ctx["a"]
    mine = ev(H, 'EClass.pc.elements.Base(286).ToString()')
    theirs = ev(port, 'EClass.pc.elements.Base(286).ToString()')
    try:
        # l'invite bon fermier, l'host debutant
        ev(port, 'EClass.pc.elements.SetBase(286, 50); "ok"')
        ev(H, 'EClass.pc.elements.SetBase(286, 1); "ok"')
        eventually(lambda: int(ev(H, f'{chara(H, uid)}.Evalue(286).ToString()')) >= 50, timeout=10)
        guest = int(ev(H, f'var c = {chara(H, uid)}; ' + AS_TASK_OF % SEEDS, timeout=120))
        ev(H, 'EClass.pc.elements.SetBase(286, 50); "ok"')
        host = int(ev(H, SEEDS, timeout=120))
    finally:
        ev(H, f'EClass.pc.elements.SetBase(286, {mine}); "ok"')
        ev(port, f'EClass.pc.elements.SetBase(286, {theirs}); "ok"')
    log(f"graines montees de niveau sur 1000 : l'invite {guest}, l'host a talent egal {host}")
    check(f"l'invite a au moins la moitie de ce qu'a l'host a talent egal ({guest} contre {host})", guest >= host / 2)


def g16(ctx):
    """voeu : ce qui est souhaite tombe aux pieds de celui qui fait le voeu, pour de vrai"""
    at_feet = 'var c = {who}; return EClass._map.things.Where(t => t.id == "medal" && t.pos.Equals(c.pos)).Sum(t => t.Num).ToString();'
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        medals = lambda p, u=uid: int(ev(p, at_feet.replace("{who}", chara(p, u))))  # noqa: E731
        before = medals(H)
        # la reponse au voeu : ce que fait le bouton OK de la fenetre
        ev(port, 'ActEffect.Wish(EClass.sources.cards.map["medal"].GetName(), EClass.pc.NameTitled, 100, BlessedState.Normal); "ok"')
        ok = eventually(lambda: medals(H) > before, timeout=10)
        check(f"{who} souhaite des medailles : elles sont a ses pieds chez l'host ({before} -> {medals(H)})", ok)
        check(f"{who} : et dans son propre jeu ({medals(port)})", eventually(lambda: medals(port) == medals(H), timeout=10))
        ev(H, f'var c = {chara(H, uid)}; foreach (var t in EClass._map.things.Where(t => t.id == "medal" && t.pos.Equals(c.pos)).ToList()) t.Destroy(); "ok"')


def g19(ctx):
    """outil de fabrication utilise depuis le sac : la fenetre s'ouvre chez celui qui s'en sert, pas chez l'autre"""
    tool = ev(H, 'foreach (var r in EClass.sources.things.rows.Where(x => x.trait != null && x.trait.Length > 0 && x.trait[0].StartsWith("Tool"))) { '
                 'var t = ThingGen.Create(r.id); var ok = t.trait is TraitCrafter c && c.CanUseFromInventory && !c.IsFactory; t.Destroy(); '
                 'if (ok) return r.id; } return "";')
    if not check(f"le jeu a un outil de fabrication de sac ({tool})", bool(tool)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        t = give(ctx, key, tool)
        time.sleep(1)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {t}); t.trait.OnUse(EClass.pc); "ok"')
        opened = eventually(lambda: bool(ev(port, LAYERS)), timeout=5)
        time.sleep(1)
        check(f"{who} se sert de l'outil : la fenetre s'ouvre chez lui ({ev(port, LAYERS) or 'rien'})", opened)
        check(f"{who} : rien ne s'ouvre chez l'autre joueur ({ev(other, LAYERS) or 'rien'})", not ev(other, LAYERS))
        close_layers()
        ev(H, f'var x = {chara(H, uid)}.things.Find(y => y.uid == {t}); if (x != null) x.Destroy(); "ok"')


def g21(ctx):
    """manger repu : le jeu dit « repu » et la nourriture reste dans le sac, pour l'invite comme pour l'host"""
    food = ev(H, 'var r = EClass.sources.things.rows.FirstOrDefault(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Food" && x.weight > 0 && x.weight < 100); '
                 'return r == null ? "" : r.id;')
    if not check(f"le jeu a une nourriture legere ({food})", bool(food)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        f = give(ctx, key, food, 3)
        ev(port, 'EClass.pc.hunger.value = 0; "ok"')
        time.sleep(1)
        before = count(H, uid, food)
        awake(port)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {f}); EClass.pc.SetAI(new AI_Eat {{ target = t, cook = false }}); "ok"')
        time.sleep(2)
        done = eventually(lambda: awake(port) and ev(port, 'EClass.pc.ai is AI_Eat && EClass.pc.ai.IsRunning ? "mange" : "libre"') == "libre", timeout=30)
        time.sleep(2)
        check(f"{who} repu essaie de manger, puis s'arrete", done)
        check(f"{who} : la nourriture est toujours la chez l'host ({before} -> {count(H, uid, food)})", count(H, uid, food) == before)
        check(f"{who} : son propre jeu dit pareil ({count(port, uid, food)})", count(port, uid, food) == count(H, uid, food))
        ev(H, f'var t = {chara(H, uid)}.things.Find(x => x.uid == {f}); if (t != null) t.Destroy(); "ok"')


def g23(ctx):
    """mannequin : il prend l'equipement de celui qui s'en sert, puis le lui rend ; l'autre joueur garde le sien"""
    mq = first_id("Mannequin")
    if not check(f"le jeu a un mannequin ({mq})", bool(mq)):
        return
    worn = lambda p, u: int(ev(p, f'{chara(p, u)}.body.slots.Count(s => s.thing != null && s.elementId != 44).ToString()'))  # noqa: E731
    for who, key in both(ctx):
        port, uid = ctx[key]
        _, other_uid = ctx["h" if key == "a" else "a"]
        armor = give_made(ctx, key, 'var t = ThingGen.CreateFromCategory("armor"); t.SetBlessedState(BlessedState.Normal);')
        ev(port, f'EClass.pc.body.Equip(EClass.pc.things.Find(x => x.uid == {armor})); "ok"')
        time.sleep(2)
        mine0, theirs0 = worn(H, uid), worn(H, other_uid)
        m = ev(H, f'var c = {chara(H, uid)}; var t = ThingGen.Create("{mq}"); EClass._zone.AddCard(t, c.pos.GetNearestPoint(false, false, false, true)).Install(); return t.uid.ToString();')
        time.sleep(2)
        inside = lambda p: int(ev(p, f'var t = EClass._map.things.Find(x => x.uid == {m}); return t == null ? "-1" : t.things.Count.ToString();'))  # noqa: E731
        use = f'EClass._map.things.Find(x => x.uid == {m}).trait.OnUse(EClass.pc); "ok"'
        ev(port, use)
        check(f"{who} : le mannequin prend ce qu'il porte (dedans : {inside(H)}, il portait {mine0}, porte {worn(H, uid)})",
              eventually(lambda: inside(H) > 0 and worn(H, uid) == mine0 - inside(H), timeout=10))
        check(f"{who} : l'autre joueur garde tout ({theirs0} -> {worn(H, other_uid)})", worn(H, other_uid) == theirs0)
        check(f"{who} : son propre jeu dit pareil", eventually(lambda: worn(port, uid) == worn(H, uid) and inside(port) == inside(H), timeout=10))
        ev(port, use)
        check(f"{who} : il reprend ses affaires ({worn(H, uid)} sur {mine0})", eventually(lambda: worn(H, uid) == mine0 and inside(H) == 0, timeout=10))
        ev(H, f'var t = EClass._map.things.Find(x => x.uid == {m}); if (t != null) t.Destroy(); "ok"')


TECH = ('var r = EClass.sources.elements.rows.FirstOrDefault(a => a.category == "tech" && a.chance > 0 && a.cost.Length > 0 && a.cost[0] != 0 '
        '&& !a.tag.Contains("hidden") && !a.tag.Contains("unused") && !EClass.Branch.elements.HasBase(a.id)); return r == null ? "0" : r.id.ToString();')


def g24(ctx):
    """livre de plan : la base apprend le plan et le livre est use, que ce soit l'invite ou l'host qui le lise"""
    if not check("la carte est une base", ev(H, 'EClass._zone.IsPCFaction.ToString()') == "True"):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        ele = int(ev(H, TECH))
        if not check(f"un plan que la base ne connait pas ({ele})", ele != 0):
            continue
        book = give_made(ctx, key, f'var t = ThingGen.CreatePlan({ele});')
        check(f"{who} lit le plan jusqu'au bout", read_book(ctx, key, book))
        check(f"{who} : la base de l'host connait le plan", eventually(lambda: ev(H, f'EClass.Branch.elements.HasBase({ele}).ToString()') == "True", timeout=10))
        gone = lambda p, u=uid: ev(p, f'({chara(p, u)}.things.Find(x => x.uid == {book}) == null).ToString()')  # noqa: E731
        check(f"{who} : le livre est use chez l'host", eventually(lambda: gone(H) == "True", timeout=10))
        check(f"{who} : et dans son propre jeu", eventually(lambda: gone(port) == "True", timeout=10))


STATUE = ('foreach (var r in EClass.sources.things.rows.Where(x => x.trait != null && x.trait.Length > 1 && x.trait[0] == "GodStatue")) { '
          'var gift = r.trait[1] == "wind" ? "blood_angel" : r.trait[1] == "harvest" ? "book_kumiromi" : (r.trait[1] == "earth" || r.trait[1] == "element") ? "mathammer" : ""; '
          'if (gift != "") return r.id + "," + gift; } return "";')


def g25(ctx):
    """paquets du Nouvel An et de Jure, statue doree d'un dieu : ce qu'ils donnent va a celui qui les ouvre, l'allie du Nouvel An le suit lui"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        _, other_uid = ctx["h" if key == "a" else "a"]
        mine = "0" if key == "h" else str(uid)
        # en fin de suite le sac est plein de ce que les tests precedents ont donne : un sac plein pose a terre ce
        # qu'un paquet donne. On le vide (monde de test), sauf ce qui est porte
        ev(H, f'var c = {chara(H, uid)}; foreach (var t in c.things.ToList()) if (!t.isEquipped) t.Destroy(); "ok"')
        time.sleep(2)
        for trait, gain in (("GiftNewYear", 2), ("GiftJure", 20)):
            box = first_id(trait)
            if not check(f"le jeu a un {trait} ({box})", bool(box)):
                continue
            b = give(ctx, key, box)
            time.sleep(1)
            n0, other0, own0 = bag_size(H, uid), bag_size(H, other_uid), bag_size(port, uid)
            ev(port, f'EClass.pc.things.Find(x => x.uid == {b}).trait.OnUse(EClass.pc); "ok"')
            grew = eventually(lambda: bag_size(H, uid) >= n0 + gain, timeout=10)
            check(f"{who} ouvre {trait} : son sac gagne au moins {gain} objets ({n0} -> {bag_size(H, uid)})", grew)
            check(f"{who} : rien chez l'autre joueur ({other0} -> {bag_size(H, other_uid)})", bag_size(H, other_uid) == other0)
            # le gain, pas le total : le sac vide au debut du test l'a ete par l'host
            same = eventually(lambda: bag_size(port, uid) - own0 == bag_size(H, uid) - n0, timeout=10)
            check(f"{who} : son propre jeu voit le meme gain ({bag_size(port, uid) - own0} et {bag_size(H, uid) - n0})", same)
            if trait == "GiftNewYear":
                owners = lambda p: ev(p, 'return string.Join(",", EClass.pc.party.members.Where(m => m != null && m.id == "putty_snow").Select(m => m.GetInt("emp_owner")));')  # noqa: E731
                check(f"{who} : la boule de neige est dans le groupe, a lui (proprietaires : {owners(H)}, attendu {mine})",
                      eventually(lambda: owners(H) == mine, timeout=10))
                check(f"{who} : son jeu la voit sur la carte", eventually(lambda: ev(port, 'EClass._map.charas.Any(c => c.id == "putty_snow").ToString()') == "True", timeout=10))
                ev(H, 'foreach (var m in EClass._map.charas.Where(c => c.id == "putty_snow" || c.id == "bell_silver").ToList()) { if (m.IsPCParty) EClass.pc.party.RemoveMember(m); m.Destroy(); } "ok"')
        found = ev(H, STATUE)
        if not check(f"le jeu a une statue de dieu qui donne un objet ({found})", bool(found)):
            continue
        sid, gift = found.split(",")
        s = ev(H, f'var c = {chara(H, uid)}; var t = ThingGen.Create("{sid}"); t.ChangeMaterial("gold"); (t.trait as TraitGodStatue).OnChangeMaterial(); '
                  'EClass._zone.AddCard(t, c.pos.GetNearestPoint(false, false, false, true)).Install(); return t.uid.ToString();')
        time.sleep(2)
        g0, other0 = count(H, uid, gift), count(H, other_uid, gift)
        ev(port, f'EClass._map.things.Find(x => x.uid == {s}).trait.OnUse(EClass.pc); "ok"')
        check(f"{who} prie la statue : {gift} dans son sac ({g0} -> {count(H, uid, gift)})", eventually(lambda: count(H, uid, gift) == g0 + 1, timeout=10))
        check(f"{who} : rien chez l'autre joueur", count(H, other_uid, gift) == other0)
        spent = lambda p: ev(p, f'var t = EClass._map.things.Find(x => x.uid == {s}); return t == null ? "absent" : t.isOn.ToString();')  # noqa: E731
        check(f"{who} : la statue est eteinte partout ({spent(H)}, {spent(port)})", eventually(lambda: spent(H) == spent(port) == "False", timeout=10))
        ev(H, f'var t = EClass._map.things.Find(x => x.uid == {s}); if (t != null) t.Destroy(); "ok"')


PAIR = ('foreach (var g in EClass.sources.things.rows.Where(x => x.trait != null && x.trait.Length > 0 && x.trait[0].StartsWith("ToolRange")).Take(20)) { var gun = ThingGen.Create(g.id); '
        'foreach (var a in EClass.sources.things.rows.Where(x => x.trait != null && x.trait.Length > 0 && x.trait[0].StartsWith("Ammo")).Take(20)) { var am = ThingGen.Create(a.id); '
        'var ok = (gun.trait as TraitToolRange)?.IsAmmo(am) ?? false; am.Destroy(); if (ok) { gun.Destroy(); return g.id + "," + a.id; } } gun.Destroy(); } return "";')


def g30(ctx):
    """munitions utilisees depuis le sac : elles rechargent l'arme de celui qui s'en sert, jamais celle de l'autre"""
    pair = ev(H, PAIR)
    if not check(f"une arme a distance et ses munitions ({pair})", bool(pair)):
        return
    gid, aid = pair.split(",")
    guns = {}
    for key in ("a", "h"):
        port, uid = ctx[key]
        guns[key] = give(ctx, key, gid, extra="t.c_ammo = 0; t.ammoData = null;")
        ev(port, f'EClass.pc.body.Equip(EClass.pc.things.Find(x => x.uid == {guns[key]})); "ok"')
    time.sleep(2)
    loaded = lambda k: int(ev(H, f'var t = {chara(H, ctx[k][1])}.things.Find(x => x.uid == {guns[k]}); return t == null ? "-1" : t.c_ammo.ToString();'))  # noqa: E731
    for who, key in both(ctx):
        port, uid = ctx[key]
        okey = "h" if key == "a" else "a"
        ammo = give(ctx, key, aid, 50)
        ev(H, f'foreach (var k in new[] {{ {guns["a"]}, {guns["h"]} }}) {{ var t = EClass._map.charas.SelectMany(c => c.things).FirstOrDefault(x => x.uid == k); if (t != null) {{ t.c_ammo = 0; t.ammoData = null; }} }} '
              f'{chara(H, uid)}.RemoveCondition<ConReload>(); "ok"')
        ev(port, f'EClass.pc.things.Find(x => x.uid == {ammo}).trait.OnUse(EClass.pc); "ok"')
        check(f"{who} recharge : son arme est chargee chez l'host ({loaded(key)})", eventually(lambda: loaded(key) > 0, timeout=6))
        check(f"{who} : l'arme de l'autre joueur reste vide ({loaded(okey)})", loaded(okey) == 0)
        check(f"{who} : des munitions ont quitte son sac ({count(H, uid, aid)} sur 50)", count(H, uid, aid) < 50)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    # G8 en dernier : l'invite y quitte la carte
    steps = [g5, g3, g2, g11, g1, g4, g6, g7, g9, g10, g12, g14, g15, g16, g19, g21, g23, g24, g25, g30, g8]
    if a.only:
        steps = [s for s in (g1, g2, g3, g4, g5, g6, g7, g9, g10, g11, g12, g14, g15, g16, g19, g21, g23, g24, g25, g30, g8)
                 if s.__name__ in a.only.split(",")]
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
