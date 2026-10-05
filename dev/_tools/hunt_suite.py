"""Chasse aux differences host / invite (PLAN_chasse_differences.md) : pour chaque ligne, le meme geste par l'invite
puis par l'host. Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/hunt_suite.py            # ou --only d1,d3

D1  peur : frappe sous 20 % de points de vie, un invite ne prend pas peur (le jeu ne le fait qu'aux habitants) et
    peut toujours frapper, comme l'host.
D2  guerisseur payant : l'invite paie et il est soigne pour de bon (chez l'host aussi), comme l'host.
D4  objets a fenetre (radio, juke-box, livres de la base, detecteur, roue, vue de carte ; le pinceau est corrige de
    la meme facon mais le banc ne voit pas son mode) : chez celui qui s'en
    sert, rien chez l'autre. Le geste est Trait.OnUse, ce que fait « utiliser » dans le sac.
D5  faucille : l'ecopo va a celui qui fauche.
D6  investir dans une boutique (vrai dialogue) : la boutique monte chez l'host.
D7  benediction d'une pretresse (vrai dialogue, ferme par Close) : le joueur et son compagnon ont le voile sacre.
D8  parchemin de retour : le retour se prepare dans le jeu du lecteur, il n'est pas teleporte au hasard chez l'host.
D9  recette lue : chacun l'apprend une fois (avant : l'autre joueur l'apprenait deux fois).
D11 carte au tresor lue : fenetre chez le lecteur seul, meme carte dans les deux jeux.
D10 rune : fenetre chez celui qui s'en sert, rune posee et consommee dans les deux jeux (le choix est l'appel que
    fait le clic dans la fenetre).
D12 eau profonde : le joueur qui y nage perd son souffle (mise en place : il est pose dans l'eau, puis il fait trois pas).
D13 pied-de-biche : le coffre force s'ouvre chez l'host aussi.
D14 consigne « ne pas s'eloigner » : celle du joueur vaut pour ses compagnons (conseil 4).
D3  rangement automatique : l'invite range son sac dans un coffre regle pour ca ; les fenetres de l'host restent
    ouvertes et les objets de l'host restent dans son sac.

Ce que le banc ne joue pas comme un joueur :
- D1 : les coups recus sont 300 appels a DamageHP (degats 0) chez l'host, points de vie remis a 10 % a chaque fois
  (le tirage de la peur est a 7 % par coup) ; le coup rendu est ACT.Melee, ce que fait le clic sur un monstre.
- D2 : le dialogue est le vrai (parler, « I need healing », « Yes ») ; les choix sont cliques par leur texte anglais.
- D3 : le reglage « ranger ici ce qui s'y trouve deja » du coffre est pose directement (dans les deux jeux) ; le
  rangement est lance par TaskDump.TryPerform, ce que fait la touche.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import awake, both, chara, clear_conditions, close_layers, count, first_id, give, give_made, stand, tame, use_held  # noqa: E402
from equal2_suite import drop, seen, spawn  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552


def d1(ctx):
    """peur : sous 20 % de points de vie, un invite frappe ne prend pas peur et peut toujours frapper, comme l'host"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        foe = spawn(uid, "putty", "Enemy", "m.hp = 100000;")
        try:
            if not check(f"{who} : un monstre est a cote de lui ({foe})", foe and eventually(lambda: seen(port, foe), timeout=15)):
                continue
            ev(H, f'var c = {chara(H, uid)}; var m = EClass._map.charas.Find(x => x.uid == {foe}); for (var i = 0; i < 300; i++) {{ '
                  'c.hp = System.Math.Max(1, c.MaxHP / 10); c.DamageHP(0, AttackSource.None, m); } "ok"')
            fear = lambda p: ev(p, f'{chara(p, uid)}.HasCondition<ConFear>().ToString()')  # noqa: E731
            time.sleep(2)
            check(f"{who} : frappe 300 fois sous 20 % de points de vie, il n'a pas peur, chez l'host ({fear(H)}) ni chez lui ({fear(port)})",
                  fear(H) == "False" and fear(port) == "False")
            hp = lambda: int(ev(H, f'EClass._map.charas.Find(x => x.uid == {foe}).hp.ToString()'))  # noqa: E731
            hp0 = hp()
            for _ in range(6):
                awake(port)
                ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {foe}); ACT.Melee.Perform(EClass.pc, m, m.pos); "ok"')
                time.sleep(1)
            check(cond=eventually(lambda: hp() < hp0, timeout=5), label=f"{who} : il peut frapper, le monstre perd des points de vie ({hp0} -> {hp()})")
        finally:
            drop([foe])
            ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; "ok"')
            clear_conditions(uid)


def talk(port, m):
    """Le joueur parle a ce personnage (le clic « parler »)."""
    awake(port)
    ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {m}); m.ShowDialog(); "ok"')
    return eventually(lambda: ev(port, '(LayerDrama.Instance != null).ToString()') == "True", timeout=10)


def pick(port, label):
    """Clique le choix du dialogue du jeu dont le texte contient `label` ; renvoie les choix proposes ensuite."""
    r = ev(port, 'var d = LayerDrama.Instance; if (d == null) return "pas de dialogue"; var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(false)'
                 f'.FirstOrDefault(x => x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.Contains("{label}"))); '
                 'if (b == null) return "pas de choix"; b.onClick.Invoke(); return "clic";')
    time.sleep(1.5)
    return r


def hang_up(port):
    ev(port, 'if (LayerDrama.Instance != null) EClass.ui.RemoveLayer<LayerDrama>(); "ok"')


def d2(ctx):
    """guerisseur payant : le joueur paie et il est soigne pour de bon, l'invite comme l'host"""
    healer = ev(H, 'EClass.sources.charas.rows.First(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Healer").id')
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        priest = spawn(uid, healer, "Friend")
        try:
            if not check(f"{who} : un guerisseur est a cote de lui ({priest})", priest and eventually(lambda: seen(port, priest), timeout=15)):
                continue
            give(ctx, key, "money", 5000)
            ev(H, f'var c = {chara(H, uid)}; c.hp = 1; "ok"')
            hp = lambda p: int(ev(p, f'{chara(p, uid)}.hp.ToString()'))  # noqa: E731
            full = int(ev(H, f'{chara(H, uid)}.MaxHP.ToString()'))
            eventually(lambda: hp(port) <= 2, timeout=10)
            gold0 = count(H, uid, "money")
            said = talk(port, priest) and pick(port, "healing") == "clic" and pick(port, "Yes") == "clic"
            if not check(f"{who} : il demande des soins au guerisseur et dit oui", said):
                continue
            check(cond=eventually(lambda: count(H, uid, "money") < gold0 and count(port, uid, "money") == count(H, uid, "money"), timeout=10),
                  label=f"{who} : il a paye, les deux jeux voient la meme bourse ({gold0} -> {count(H, uid, 'money')} et {count(port, uid, 'money')})")
            check(cond=eventually(lambda: hp(H) >= full - 1, timeout=10), label=f"{who} : il est soigne, chez l'host ({hp(H)}/{full})")
            time.sleep(3)
            check(cond=eventually(lambda: hp(port) >= full - 1, timeout=10), label=f"{who} : et chez lui, pour de bon ({hp(port)}/{full})")
        finally:
            hang_up(port)
            drop([priest])
            ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; foreach (var t in c.things.Where(m => m.id == "money").ToList()) t.Destroy(); "ok"')


def d3(ctx):
    """rangement automatique : le joueur range son sac ; les fenetres et les objets de l'autre joueur ne bougent pas"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        other_key = "h" if key == "a" else "a"
        other, other_uid = ctx[other_key]
        close_layers()
        # les memes seaux partout (un seau a une matiere tiree au hasard, et le coffre ne prend que ce qui s'empile avec
        # son contenu) : ceux de l'autre joueur et celui du coffre sont des copies de ceux du joueur
        mine = give(ctx, key, "bucket", 3)
        theirs = int(ev(H, f'var s = {chara(H, uid)}.things.Find(x => x.uid == {mine}); return {chara(H, other_uid)}.AddThing(s.Duplicate(3), false).uid.ToString();'))
        eventually(lambda: ev(other, f'(EClass.pc.things.Find(x => x.uid == {theirs}) != null).ToString()') == "True", timeout=10)
        chest = int(ev(H, f'var t = ThingGen.Create("chest3"); t.c_lockLv = 0; EClass._zone.AddCard(t, {chara(H, uid)}.pos.GetNearestPoint(false, false, false, true)).Install(); '
                          f'foreach (var x in t.things.ToList()) x.Destroy(); t.AddCard({chara(H, uid)}.things.Find(x => x.uid == {mine}).Duplicate(1)); return t.uid.ToString();'))
        inside = lambda p: int(ev(p, f'var t = EClass._map.things.Find(m => m.uid == {chest}); '  # noqa: E731
                                     'return t == null ? "-1" : t.things.Where(x => x.id == "bucket").Sum(x => x.Num).ToString();'))
        try:
            eventually(lambda: inside(port) == 1, timeout=10)
            for p in (H, A):
                ev(p, f'var t = EClass._map.things.Find(m => m.uid == {chest}); t.c_windowSaveData = new Window.SaveData {{ autodump = AutodumpFlag.existing }}; "ok"')
            ev(other, 'EClass.ui.AddLayer<LayerJournal>(); "ok"')
            opened = lambda: ev(other, '(EClass.ui.layers.OfType<LayerJournal>().Any()).ToString()') == "True"  # noqa: E731
            if not check(f"{who} : l'autre joueur a une fenetre ouverte (son journal)", opened()):
                continue
            awake(port)
            ev(port, 'EClass.pc.SetNoGoal(); "ok"')
            time.sleep(1)
            ev(port, 'TaskDump.TryPerform(); "ok"')
            check(cond=eventually(lambda: inside(H) == 4, timeout=30), label=f"{who} : ses 3 seaux sont dans le coffre, chez l'host ({inside(H)} avec celui du coffre)")
            check(cond=eventually(lambda: inside(port) == inside(other) == 4, timeout=10), label=f"{who} : les deux jeux voient le meme coffre ({inside(port)} et {inside(other)})")
            check(f"{who} : il n'a plus ses seaux ({count(H, uid, 'bucket')})", count(H, uid, "bucket") == 0)
            check(f"{who} : l'autre joueur a garde les siens ({count(H, other_uid, 'bucket')})", count(H, other_uid, "bucket") == 3)
            check(f"{who} : la fenetre de l'autre joueur est restee ouverte", opened())
        finally:
            close_layers()
            for p in (port, other):
                ev(p, 'if (EClass.pc.ai is TaskDump) EClass.pc.SetNoGoal(); "ok"')
            ev(H, f'var t = EClass._map.things.Find(m => m.uid == {chest}); if (t != null) t.Destroy(); '
                  'foreach (var c in EClass._map.charas.Where(c => c.IsPCC).ToList()) foreach (var b in c.things.Where(m => m.id == "bucket").ToList()) b.Destroy(); "ok"')
            _ = mine, theirs


WINDOWS = (("Radio", "la radio"), ("JukeBox", "le juke-box"), ("EditPlaylist", "la liste de lecture"), ("BookResident", "le livre des residents"),
           ("BookRoster", "le livre de l'equipe"), ("Detector", "le detecteur"), ("GeneratorWheel", "la roue"), ("ViewMap", "la vue de carte"))


def screen(port):
    """Mode d'action et fenetres ouvertes de ce jeu."""
    return ev(port, 'EClass.scene.actionMode.GetType().Name + "|" + string.Join(",", EClass.ui.layers.Select(l => l.GetType().Name))')


def d4(ctx):
    """objets a fenetre : la fenetre (ou le mode) s'ouvre chez celui qui s'en sert, rien ne bouge chez l'autre joueur"""
    for trait, what in WINDOWS:
        item = first_id(trait)
        if not item:
            print(f"    [SAUTE] aucun objet du jeu n'a le trait {trait}")
            continue
        for who, key in both(ctx):
            port, uid = ctx[key]
            other = H if port == A else A
            close_layers()
            for p in (H, A):
                ev(p, 'if (!(EClass.scene.actionMode is AM_Adv)) ActionMode.Adv.Activate(); "ok"')
            t = give(ctx, key, item)
            time.sleep(1)
            mine0, theirs0 = screen(port), screen(other)
            awake(port)
            ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {t}); t.trait.OnUse(EClass.pc); "ok"')
            time.sleep(2)
            mine, theirs = screen(port), screen(other)
            check(f"{who} se sert de {what} : ca s'ouvre chez lui ({mine0} -> {mine})", mine != mine0)
            check(f"{who}, {what} : rien ne bouge chez l'autre joueur ({theirs})", theirs == theirs0)
            close_layers()
            for p in (H, A):
                ev(p, 'if (!(EClass.scene.actionMode is AM_Adv)) ActionMode.Adv.Activate(); "ok"')
            ev(H, f'var t = {chara(H, uid)}.things.Find(x => x.uid == {t}); if (t != null) t.Destroy(); "ok"')


def d5(ctx):
    """faucille : l'ecopo va a celui qui fauche, l'invite comme l'host"""
    sickle = first_id("ToolSickle")
    if not check(f"le jeu a une faucille ({sickle})", bool(sickle)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other_uid = ctx["h" if key == "a" else "a"][1]
        weed = spawn(uid, "putty", "Neutral", "m.c_minionType = MinionType.Friend;")
        try:
            if not check(f"{who} : une creature a faucher est a cote de lui ({weed})", weed and eventually(lambda: seen(port, weed), timeout=15)):
                continue
            ev(port, f'EClass._map.charas.Find(x => x.uid == {weed}).c_minionType = MinionType.Friend; "ok"')
            tool = give(ctx, key, sickle)
            mine0, theirs0 = count(H, uid, "ecopo"), count(H, other_uid, "ecopo")
            x, z = (int(v) for v in ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {weed}); return m.pos.x + "," + m.pos.z;').split(","))
            awake(port)
            log(f"{who} fauche : {use_held(port, tool, at=(x, z), pick='i.act is TaskCullLife')}")
            gone = lambda: ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {weed}); return (m == null || m.isDead).ToString();') == "True"  # noqa: E731
            check(cond=eventually(lambda: awake(port) and gone(), timeout=40), label=f"{who} : la creature est fauchee, chez l'host")
            check(cond=eventually(lambda: count(H, uid, "ecopo") > mine0 and count(port, uid, "ecopo") == count(H, uid, "ecopo"), timeout=10),
                  label=f"{who} : il recoit l'ecopo, les deux jeux voient pareil ({mine0} -> {count(H, uid, 'ecopo')} et {count(port, uid, 'ecopo')})")
            check(f"{who} : l'autre joueur n'en recoit pas ({theirs0} -> {count(H, other_uid, 'ecopo')})", count(H, other_uid, "ecopo") == theirs0)
        finally:
            ev(port, 'EClass.pc.SetNoGoal(); "ok"')
            drop([weed])


def d6(ctx):
    """investir dans une boutique : le joueur paie et la boutique monte chez l'host, l'invite comme l'host
    (l'investissement dans une ville passe par le meme code, pas joue : il faut le secretaire d'une ville)"""
    shop = ev(H, 'EClass.sources.charas.rows.First(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Healer").id')
    for who, key in both(ctx):
        port, uid = ctx[key]
        keeper = spawn(uid, shop, "Friend")
        try:
            if not check(f"{who} : un marchand est a cote de lui ({keeper})", keeper and eventually(lambda: seen(port, keeper), timeout=15)):
                continue
            give(ctx, key, "money", 200000)
            level = lambda p: ev(p, f'var m = EClass._map.charas.Find(x => x.uid == {keeper}); return m.c_invest + "/" + EClass._zone.influence;')  # noqa: E731
            lv0, gold0 = level(H), count(H, uid, "money")
            said = talk(port, keeper) and pick(port, "invest") == "clic" and pick(port, "Yes") == "clic"
            if not check(f"{who} : il demande a investir et dit oui", said):
                continue
            check(cond=eventually(lambda: count(H, uid, "money") < gold0, timeout=10), label=f"{who} : il a paye ({gold0} -> {count(H, uid, 'money')})")
            n0, i0 = (int(v) for v in lv0.split("/"))
            check(cond=eventually(lambda: level(H) == f"{n0 + 1}/{i0 + 1}", timeout=10),
                  label=f"{who} : chez l'host la boutique a un niveau de plus et la zone 1 d'influence de plus ({lv0} -> {level(H)})")
        finally:
            hang_up(port)
            drop([keeper])
            ev(H, f'var c = {chara(H, uid)}; foreach (var t in c.things.Where(m => m.id == "money").ToList()) t.Destroy(); "ok"')


def d7(ctx):
    """benediction d'une pretresse : le joueur et son compagnon la recoivent, l'invite comme l'host"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        miko = spawn(uid, "miko_mifu", "Friend")
        pet = tame(ctx, "cat", key)
        try:
            if not check(f"{who} : une pretresse est a cote de lui ({miko}), il a un compagnon ({pet})",
                         miko and pet and eventually(lambda: seen(port, miko), timeout=15)):
                continue
            said = talk(port, miko) and pick(port, "blessings") == "clic"
            for _ in range(4):
                if ev(port, '(LayerDrama.Instance != null).ToString()') != "True":
                    break
                ev(port, 'LayerDrama.Instance.Close(); "ok"')
                time.sleep(1)
            if not check(f"{who} : il demande la benediction et ferme le dialogue", said):
                continue
            veil = lambda p, c: ev(p, f'var c = EClass._map.charas.Find(x => x.uid == {c}); return (c != null && c.HasCondition<ConHolyVeil>()).ToString();')  # noqa: E731
            check(cond=eventually(lambda: veil(H, uid) == "True", timeout=10), label=f"{who} : il a le voile sacre, chez l'host ({veil(H, uid)})")
            check(cond=eventually(lambda: veil(port, uid) == "True", timeout=10), label=f"{who} : et chez lui ({veil(port, uid)})")
            check(cond=eventually(lambda: veil(H, pet) == "True", timeout=10), label=f"{who} : son compagnon aussi, chez l'host ({veil(H, pet)})")
        finally:
            hang_up(port)
            drop([miko, pet])
            clear_conditions(uid)


def d8(ctx):
    """parchemin d'evacuation (meme code que le retour, qui demande une destination connue) : le lecteur prepare son depart, il n'est pas teleporte au hasard"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        scroll = give_made(ctx, key, 'var t = ThingGen.CreateScroll(EClass.sources.elements.alias["SpEvac"].id); t.c_IDTState = 0; '
                                     't.SetBlessedState(BlessedState.Normal);')
        where = lambda: ev(H, f'var c = {chara(H, uid)}; return c.pos.x + "," + c.pos.z;')  # noqa: E731
        ev(port, 'EClass.player.returnInfo = null; "ok"')
        pos0 = where()
        awake(port)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {scroll}); EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
        back = lambda: ev(port, '(EClass.player.returnInfo != null).ToString()') == "True"  # noqa: E731
        try:
            check(cond=eventually(lambda: awake(port) and back(), timeout=20), label=f"{who} lit : son retour se prepare, dans son jeu")
            time.sleep(2)
            check(f"{who} : il n'a pas bouge sur la carte, vu par l'host ({pos0} -> {where()})", where() == pos0)
            check(cond=eventually(lambda: ev(H, f'({chara(H, uid)}.things.Find(x => x.uid == {scroll}) == null).ToString()') == "True", timeout=10),
                  label=f"{who} : le parchemin est use, chez l'host")
        finally:
            ev(port, 'EClass.player.returnInfo = null; EClass.pc.SetNoGoal(); "ok"')
            close_layers()


def d9(ctx):
    """recette lue : tout le monde l'apprend (les recettes sont communes), une seule fois chacun"""
    item = first_id("Recipe")
    if not check(f"le jeu a un parchemin de recette ({item})", bool(item)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        scroll = give(ctx, key, item)
        rid = ev(H, f'((TraitRecipe){chara(H, uid)}.things.Find(x => x.uid == {scroll}).trait).recipe.id')
        known = lambda p: int(ev(p, f'EClass.player.recipes.knownRecipes.TryGetValue("{rid}", 0).ToString()'))  # noqa: E731
        mine0, theirs0 = known(port), known(other)
        awake(port)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {scroll}); EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
        check(cond=eventually(lambda: awake(port) and known(port) == mine0 + 1, timeout=20), label=f"{who} lit la recette {rid} : il l'apprend ({mine0} -> {known(port)})")
        time.sleep(2)
        check(f"{who} : l'autre joueur l'apprend aussi (les recettes sont communes), une fois, pas deux ({theirs0} -> {known(other)})",
              known(other) == theirs0 + 1)
        check(cond=eventually(lambda: ev(H, f'({chara(H, uid)}.things.Find(x => x.uid == {scroll}) == null).ToString()') == "True", timeout=10),
              label=f"{who} : le parchemin est use, chez l'host")
        ev(port, 'EClass.pc.SetNoGoal(); "ok"')


def d11(ctx):
    """carte au tresor lue : la fenetre s'ouvre chez le lecteur seul, et les deux jeux parlent de la meme carte"""
    item = first_id("ScrollMapTreasure")
    if not check(f"le jeu a une carte au tresor ({item})", bool(item)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        t = give(ctx, key, item)
        ref = lambda p: ev(p, f'var t = {chara(p, uid)}.things.Find(x => x.uid == {t}); return t == null ? "absent" : t.refVal.ToString();')  # noqa: E731
        theirs0 = screen(other)
        awake(port)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {t}); t.trait.OnUse(EClass.pc); "ok"')
        time.sleep(3)
        check(f"{who} lit sa carte : elle designe un endroit ({ref(port)})", ref(port) not in ("0", "absent"))
        check(cond=eventually(lambda: ref(H) == ref(A), timeout=10), label=f"{who} : les deux jeux parlent de la meme carte ({ref(H)} et {ref(A)})")
        check(f"{who} : rien ne bouge chez l'autre joueur ({screen(other)})", screen(other) == theirs0)
        for p in (H, A):
            ev(p, 'EClass.ui.layerFloat.RemoveLayer<LayerTreasureMap>(); "ok"')
        close_layers()
        ev(H, f'var t = {chara(H, uid)}.things.Find(x => x.uid == {t}); if (t != null) t.Destroy(); "ok"')


def d10(ctx):
    """rune : la fenetre de choix s'ouvre chez celui qui s'en sert seulement, la rune est posee sur l'objet choisi chez
    l'host et chez lui, et elle est consommee, l'invite comme l'host"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        rune = give_made(ctx, key, 'var t = ThingGen.CreateRune(66, 5);')
        # un equipement qui accepte cette rune, cree par l'host dans le sac du joueur
        gear = int(ev(H, f'var c = {chara(H, uid)}; var r = c.things.Find(x => x.uid == {rune}); for (var i = 0; i < 40; i++) {{ '
                         'var t = ThingGen.CreateFromCategory(i % 2 == 0 ? "armor" : "weapon"); if (t.CanAddRune((TraitMod)r.trait)) '
                         '{ return c.AddThing(t, false).uid.ToString(); } t.Destroy(); } return "0";'))
        if not check(f"{who} : il a une rune ({rune}) et un equipement qui l'accepte ({gear})", bool(gear)
                     and eventually(lambda: ev(port, f'(EClass.pc.things.Find(x => x.uid == {gear}) != null).ToString()') == "True", timeout=10)):
            continue
        runes = lambda p: ev(p, f'var t = {chara(p, uid)}.things.Find(x => x.uid == {gear}); return t == null ? "absent" : t.CountRune().ToString();')  # noqa: E731
        theirs0 = screen(other)
        awake(port)
        ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {rune}); t.trait.OnUse(EClass.pc); "ok"')
        opened = eventually(lambda: "LayerDragGrid" in screen(port), timeout=10)
        check(f"{who} se sert de la rune : la fenetre de choix s'ouvre chez lui ({screen(port)})", opened)
        check(f"{who} : rien ne bouge chez l'autre joueur ({screen(other)})", screen(other) == theirs0)
        r = ev(port, f'var g = LayerDragGrid.Instance; var t = EClass.pc.things.Find(x => x.uid == {gear}); '
                     'if (g == null || t == null || !EClass.ui.layers.Contains(g)) return "fenetre ou objet absent"; '
                     'var b = g.owner.buttons[g.currentIndex]; b.SetCardGrid(t, b.invOwner); g.owner.OnProcess(t); return "ok";')
        check(cond=eventually(lambda: runes(H) == "1", timeout=10), label=f"{who} choisit l'equipement ({r}) : la rune y est, chez l'host ({runes(H)})")
        check(cond=eventually(lambda: runes(A) == "1", timeout=10), label=f"{who} : et chez l'invite ({runes(A)})")
        check(cond=eventually(lambda: ev(H, f'({chara(H, uid)}.things.Find(x => x.uid == {rune}) == null).ToString()') == "True"
                              and ev(port, f'(EClass.pc.things.Find(x => x.uid == {rune}) == null).ToString()') == "True", timeout=10),
              label=f"{who} : la rune est consommee, dans les deux jeux")
        close_layers()
        ev(H, f'var c = {chara(H, uid)}; foreach (var u in new[] {{ {rune}, {gear} }}) {{ var t = c.things.Find(x => x.uid == u); if (t != null) t.Destroy(); }} "ok"')


def d12(ctx):
    """eau profonde : le joueur qui y entre perd son souffle, l'invite comme l'host"""
    spot = ev(H, 'var b = EClass._map.bounds; for (var x = b.x; x <= b.maxX; x++) for (var z = b.z; z <= b.maxZ; z++) { '
                 'var p = new Point(x, z); if (p.IsValid && p.cell.CanSuffocate() && !p.HasChara) { foreach (var q in new[] { new Point(x + 1, z), '
                 'new Point(x - 1, z), new Point(x, z + 1), new Point(x, z - 1) }) if (q.IsValid && q.IsInBounds && q.cell.CanSuffocate() && !q.HasChara) '
                 'return p.x + "," + p.z + "," + q.x + "," + q.z; } } return "";')
    if not spot:
        print("    [SAUTE] D12 : pas d'eau profonde sur cette carte, le geste ne peut pas etre joue ici")
        return
    x, z, x2, z2 = (int(v) for v in spot.split(","))
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        home = ev(H, f'var c = {chara(H, uid)}; return c.pos.x + "," + c.pos.z;').split(",")
        ev(port, 'EClass.debug.godMode = false; "ok"')
        try:
            if not check(f"{who} se tient dans l'eau profonde ({x},{z})", stand(port, uid, x, z)):
                continue
            # un pas dans l'eau, comme un joueur qui nage : le jeu regarde l'eau a chaque pas
            for tx, tz in ((x2, z2), (x, z), (x2, z2)):
                awake(port)
                ev(port, f'EClass.pc.TryMove(new Point({tx}, {tz})); "ok"')
                time.sleep(1)
            under = lambda p: ev(p, f'{chara(p, uid)}.HasCondition<ConSuffocation>().ToString()')  # noqa: E731
            check(cond=eventually(lambda: under(H) == "True", timeout=8), label=f"{who} : il perd son souffle, chez l'host ({under(H)})")
            check(cond=eventually(lambda: under(port) == "True", timeout=8), label=f"{who} : et dans son jeu ({under(port)})")
        finally:
            stand(port, uid, int(home[0]), int(home[1]))
            clear_conditions(uid)
            ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; "ok"')


def d13(ctx):
    """pied-de-biche : le coffre verrouille que le joueur force s'ouvre pour de bon (chez l'host aussi), l'invite comme l'host"""
    bar = first_id("ToolCrowbar")
    if not check(f"le jeu a un pied-de-biche ({bar})", bool(bar)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        x, z = (int(v) for v in ev(H, f'var p = {chara(H, uid)}.pos.GetNearestPoint(false, false, false, true); return p.x + "," + p.z;').split(","))
        chest = int(ev(H, f'var t = ThingGen.Create("chest3"); t.c_lockLv = 1; t.hp = 3; EClass._zone.AddCard(t, new Point({x}, {z})).Install(); return t.uid.ToString();'))
        lock = lambda p: ev(p, f'var t = EClass._map.things.Find(m => m.uid == {chest}); return t == null ? "detruit" : t.c_lockLv.ToString();')  # noqa: E731
        try:
            eventually(lambda: lock(port) == "1", timeout=10)
            tool = give(ctx, key, bar)
            awake(port)
            log(f"{who} force : {use_held(port, tool, at=(x, z), pick='i.act is AI_PryOpen')}")
            check(cond=eventually(lambda: awake(port) and lock(H) != "1", timeout=60), label=f"{who} : le coffre est force, chez l'host (verrou : {lock(H)})")
            check(cond=eventually(lambda: lock(port) == lock(H), timeout=10), label=f"{who} : son jeu voit pareil ({lock(port)})")
        finally:
            ev(port, 'EClass.pc.SetNoGoal(); "ok"')
            ev(H, f'var t = EClass._map.things.Find(m => m.uid == {chest}); if (t != null) t.Destroy(); "ok"')


def d14(ctx):
    """consigne « ne pas s'eloigner » : pour les compagnons d'un joueur, c'est SA case qui compte, pas celle de l'autre
    Ce que le banc ne joue pas comme un joueur : la case du menu tactique est posee directement ; on lit chez l'host la
    distance que l'IA accorde au compagnon (ConfigTactics.AllyDistance, ce que lit AI_Idle), pas un deplacement"""
    port, uid = ctx["a"]
    pet = tame(ctx, "cat", "a")
    mine = tame(ctx, "cat", "h")
    if not check(f"chaque joueur a un compagnon (invite {pet}, host {mine}), dans une zone ou la consigne joue",
                 pet and mine and ev(H, "EClass._zone.KeepAllyDistance.ToString()") == "True"):
        drop([pet, mine])
        return
    reach = lambda c: ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {c}); return EClass.game.config.tactics.AllyDistance(c) + "/" + c.DestDist;')  # noqa: E731
    keep = lambda p, on: ev(p, f'EClass.game.config.tactics.allyKeepDistance = {str(on).lower()}; "ok"')  # noqa: E731
    try:
        for guest_on, host_on in ((True, False), (False, True)):
            keep(port, guest_on)
            keep(H, host_on)
            want = lambda on, c: reach(c).split("/")[0] == ("5" if on else reach(c).split("/")[1])  # noqa: E731
            check(cond=eventually(lambda: want(guest_on, pet), timeout=25),
                  label=f"invite {'coche' if guest_on else 'decoche'}, host {'coche' if host_on else 'decoche'} : le compagnon de l'invite suit la case de l'invite (distance accordee / distance normale : {reach(pet)})")
            check(f"et celui de l'host suit la case de l'host ({reach(mine)})", want(host_on, mine))
    finally:
        keep(port, False)
        keep(H, False)
        drop([pet, mine])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14]
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
                print(f"    capture {name} : {shot(f'hunt-{step.__name__}-{name}', port)}")
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
