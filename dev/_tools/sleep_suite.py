"""Dormir a plusieurs. Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/sleep_suite.py        # ~2 minutes, a la Prairie
    python _tools/sleep_suite.py --only w0,z0,z1,z2      # la meme nuit sur une carte sauvage

Signale par l'utilisateur le 2026-10-02 (vraie partie a deux PC) : les deux joueurs dorment, et au reveil l'un
des deux "ne peut plus rien faire", bloque dans une vue etrange. Le sommeil vient du mod d'origine : l'invite
demande a dormir, l'host dort quand tout le monde est pret, ouvre l'ecran de sommeil chez tous, puis reveille
tout le monde. Aucune suite ne le couvrait.

Z1  l'invite demande a dormir, l'host se couche : l'ecran de sommeil s'ouvre des deux cotes
Z2  au reveil : plus d'ecran de sommeil ni de voile, plus personne n'est endormi, chacun peut agir, l'heure a avance
B1  l'invite dort avec le lit et l'oreiller de son sac : au reveil ils sont revenus dans son sac, des deux cotes
B2  pareil s'il se couche puis renonce
B3  un lit deja installe sur la carte, lui, reste ou il est
Y1  l'invite, seul sur une carte qu'il tient (voyage seul), y dort : l'ecran de sommeil s'ouvre chez lui, il se
    reveille et peut agir ; l'host, lui, n'a pas dormi (note dans la documentation comme impossible)
P1  (avant Z1) l'host et l'invite ont chacun un chat, loin des lits, endormis et prets a « dormir a cote »
P2  (apres Z1) la nuit commune est lancee : le chat de l'host vient a l'host, celui de l'invite vient a l'invite,
    aucun ne saute chez l'autre (plan : dev/PLAN_sommeil_teleportations.md, causes A et B)
Y2  l'invite, seul sur un champ qu'il tient, y dort : sa carte n'est pas rechargee, il n'a pas bouge, aucune
    base n'est parcourue
K1  (nuit commune) l'invite a SON grimoire, SON oreiller, SON lit : au reveil il a joue son propre reveil (livre lu,
    sort appris chez lui et chez l'host, un tirage de recette, un sort en reve, oreiller, puissance de son lit) et
    l'host n'a rien recu de son livre (plan : dev/PLAN_retours_soiree_6_octobre.md, point 10)

    python _tools/sleep_suite.py --only z0,p1,z1,p2,z2      # la nuit des chats
    python _tools/sleep_suite.py --only y2                  # a lancer a la Prairie, host et invite ensemble
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from companion_suite import dist, info, recruit, walk_away  # noqa: E402
from guest_suite import first_id  # noqa: E402
from travel_suite import RESULTS, check, dismiss_dialogs, ev, eventually, scan_logs, session_log_lines  # noqa: E402

H, A = 27551, 27552

# ce qu'un joueur voit et peut faire : ecrans ouverts, endormi ou non, entrees bloquees ou non, heure du monde
VIEW = ('return string.Join(",", EClass.ui.layers.Select(l => l.GetType().Name)) + "|" + (EClass.pc.conSleep != null) + "|" '
        '+ EInput.haltInput + "|" + EClass.scene.actionMode.GetType().Name + "|" + EClass.world.date.GetRaw() + "|" + EClass.pc.isDead;')


def view(port):
    # un dialogue du jeu (le tutoriel "tu as l'air fatigue") retient le temps tant qu'on ne clique pas : un joueur
    # le ferme d'un clic, le test aussi
    dismiss_dialogs(port)
    layers, asleep, halted, mode, now, dead = ev(port, VIEW).split("|")
    return {"layers": layers, "asleep": asleep == "True", "halted": halted == "True", "mode": mode, "now": int(now), "dead": dead == "True"}


def w0(ctx):
    """tout le monde part sur une carte sauvage (une case libre de la carte du monde), l'host d'abord
    (cas signale : les deux joueurs dormaient sur une carte sauvage, l'host est reste bloque)"""
    from travel_suite import both_joined, client_settled, enter_at, free_spot, wait, zone_uid
    home = zone_uid(H)
    region = int(ev(H, 'EClass._zone.ParentZone.uid.ToString()'))
    ev(H, 'EClass.player.ExitBorder(); "ok"')
    wait(lambda: zone_uid(H) == region, "host sur la carte du monde", timeout=120)
    time.sleep(3)
    spot = free_spot(H, home)
    enter_at(H, spot)
    wait(lambda: zone_uid(H) not in (region, home) and state(H)["sceneMode"] == "Zone", "host sur une carte sauvage", timeout=120)
    wild = zone_uid(H)
    kind = ev(H, 'EClass._zone.GetType().Name + " " + EClass._zone.ZoneFullName')
    log(f"carte sauvage : {kind} (uid {wild}), case {spot}")
    time.sleep(3)
    # l'invite, reste a la base, fait le meme chemin a pied : la carte du monde, puis la meme case
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(A, region, True), "invite sur la carte du monde", timeout=120)
    time.sleep(3)
    enter_at(A, spot)
    both_joined(H, A, wild)
    check("l'host et l'invite sont ensemble sur la carte sauvage",
          zone_uid(A) == wild and not state(A).get("awayZone") and "Field" in kind)
    ctx["wild"] = wild


def z0(ctx):
    """comme une vraie soiree : il est 22 h, tout le monde est epuise, chacun a mis un objet dans la caisse
    d'expedition (la nuit passe alors minuit et la vente de 5 h)"""
    me = state(A)["pc"]["uid"]
    ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); c.AddThing(ThingGen.Create("log").SetNum(3)); '
          'EClass.pc.AddThing(ThingGen.Create("log").SetNum(3)); "ok"')
    time.sleep(2)
    for port in (A, H):
        ev(port, 'var t = EClass.pc.things.Find(x => x.id == "log"); if (t != null) EClass.game.cards.container_shipping.AddThing(t); "ok"')
    ev(H, 'var d = EClass.world.date; d.AdvanceMin(60 * ((22 - d.hour + 24) % 24) - d.min); "ok"')
    for port in (H, A):
        ev(port, 'EClass.pc.sleepiness.Set(EClass.pc.sleepiness.max); "ok"')
    time.sleep(3)
    clock = 'var d = EClass.world.date; return d.day + "j " + d.hour + "h" + d.min;'
    log(f"heure chez l'host : {ev(H, clock)} ; chez l'invite : {ev(A, clock)}")
    check("il est 22 h des deux cotes", ev(H, 'EClass.world.date.hour.ToString()') == "22"
          and eventually(lambda: ev(A, 'EClass.world.date.hour.ToString()') == "22", timeout=10))


def park(ctx, cat, owner):
    """le chat dort a 12 cases de son proprietaire : un chat endormi ne suit personne, il ne peut donc arriver
    pres d'un lit que par le tour « dormir a cote » ; le drapeau 123 est celui que pose le dialogue « dors a cote »"""
    ev(H, f'var o = EClass._map.charas.Find(x => x.uid == {owner}); var c = EClass._map.charas.Find(x => x.uid == {cat}); '
          'var p = o.pos.Copy(); p.z += 12; if (!p.IsValid) p.z -= 24; p = p.GetNearestPoint(allowChara: false) ?? o.pos; '
          'c.MoveImmediate(p); c.SetBool(123, true); c.AddCondition<ConSleep>(300, true); "ok"')


def p1(ctx):
    """l'host et l'invite ont chacun un chat, loin des lits, endormis, prets a « dormir a cote »
    Ce que le banc ne joue pas comme un joueur : les chats naissent par eval et sont recrutes par MakeAlly (ni
    apprivoisement ni achat) ; ils sont poses a 12 cases par MoveImmediate et endormis par eval ; le drapeau « dors
    a cote » est pose sans le dialogue, donc le tirage d'une chance sur cinq et l'etiquette de race du jeu ne sont
    pas joues ici ; l'invite s'eloigne de l'host par TryMoveTowards ; les chats restent dans le groupe apres"""
    ctx["h"] = int(ev(H, 'EClass.pc.uid.ToString()'))
    ctx["a"] = state(A)["pc"]["uid"]
    ctx["hc"] = recruit(H, ctx["h"])
    ctx["ac"] = recruit(A, ctx["a"])
    check("le chat de l'host lui appartient (chef du groupe), celui de l'invite appartient a l'invite",
          eventually(lambda: (i := info(H, ctx["hc"])) is not None and i[2] == 0
                     and (j := info(H, ctx["ac"])) is not None and j[2] == ctx["a"], timeout=20))
    walk_away(A)
    check("l'invite s'est eloigne de l'host (6 cases ou plus, vu de l'host)",
          eventually(lambda: dist(H, ctx["a"], ctx["h"]) >= 6, timeout=20))
    park(ctx, ctx["hc"], ctx["h"])
    park(ctx, ctx["ac"], ctx["a"])
    time.sleep(2)
    far = [dist(H, cat, who) for cat in (ctx["hc"], ctx["ac"]) for who in (ctx["h"], ctx["a"])]
    log(f"distances chat de l'host / chat de l'invite aux lits (host, invite) : {far}")
    check("les deux chats sont a 6 cases ou plus des deux lits", min(far) >= 6)


def p2(ctx):
    """la nuit commune vient de commencer, le tour « dormir a cote » est passe : chaque chat est pres de SON dormeur
    L'host et l'invite se couchent dans le meme tour (la nuit n'a lieu que quand tous sont prets) : cette nuit
    couvre « l'host dort » et « l'invite dort ». Meme limites que p1 ; l'invite dort par pc.Sleep() et non dans un
    lit. Rouge avant la correction : le chat de l'invite est sur le lit de l'host, rien ne vient a l'invite"""
    d = ev(H, f'var h = EClass.pc; var g = EClass._map.charas.Find(x => x.uid == {ctx["a"]}); '
              f'var ch = EClass._map.charas.Find(x => x.uid == {ctx["hc"]}); var cg = EClass._map.charas.Find(x => x.uid == {ctx["ac"]}); '
              'if (g == null || ch == null || cg == null) return "-1,-1,-1,-1"; '
              'return ch.Dist(h) + "," + ch.Dist(g) + "," + cg.Dist(h) + "," + cg.Dist(g);')
    ch_h, ch_g, cg_h, cg_g = (int(x) for x in d.split(","))
    log(f"chat de l'host : {ch_h} du lit de l'host, {ch_g} de celui de l'invite ; chat de l'invite : {cg_h} / {cg_g}")
    check("les deux chats et l'invite sont sur la carte de l'host", min(ch_h, ch_g, cg_h, cg_g) >= 0)
    check(f"l'host dort : son chat est venu a cote de lui ({ch_h} case(s))", 0 <= ch_h <= 1)
    check(f"l'host dort : le chat de l'invite n'a pas saute sur son lit ({cg_h} cases)", cg_h > 2)
    check(f"l'invite dort : SON chat est venu a cote de lui ({cg_g} case(s))", 0 <= cg_g <= 1)
    check(f"l'invite dort : le chat de l'host n'est pas venu chez lui ({ch_g} cases)", ch_g > 2)


def z1(ctx):
    """l'invite demande a dormir, l'host se couche : l'ecran de sommeil s'ouvre des deux cotes"""
    ctx["before"] = {"H": view(H), "A": view(A)}
    log(f"avant : host {ctx['before']['H']}")
    log(f"avant : client {ctx['before']['A']}")
    for port in (H, A):
        dismiss_dialogs(port)
    ev(A, 'EClass.pc.Sleep(); "ok"')
    me = state(A)["pc"]["uid"]
    check("l'host note que l'invite veut dormir",
          eventually(lambda: ev(H, f'(EClass._map.charas.Find(x => x.uid == {me}).conSleep != null).ToString()') == "True", timeout=10))
    ev(H, 'EClass.pc.Sleep(); "ok"')
    ok = eventually(lambda: "LayerSleep" in view(H)["layers"], timeout=60)
    check(f"l'ecran de sommeil s'ouvre chez l'host ({view(H)['layers'] or 'rien'})", ok)
    ok = eventually(lambda: "LayerSleep" in view(A)["layers"], timeout=20)
    check(f"et chez l'invite ({view(A)['layers'] or 'rien'})", ok)


def awake(port):
    v = view(port)
    if "LayerSleep" in v["layers"]:
        return False
    # le rapport d'expedition de 5 h retient le temps tant qu'il est ouvert : le joueur le ferme
    ev(port, 'foreach (var l in EClass.ui.layers.ToList()) if (l is LayerShippingResult) l.Close(); "ok"')
    if v["asleep"]:
        # la nuit est finie mais le personnage somnole encore tant que les autres ne dorment plus : le mod
        # attend que le joueur bouge (comme une touche de deplacement), ce qui le reveille
        ev(port, STEP)
    return not v["asleep"]


# une touche de deplacement : un pas vers la case libre la plus proche
STEP = ('var p = EClass.pc.pos.GetNearestPoint(allowChara: false, ignoreCenter: true); '
        'if (p != null) EClass.pc.SetAIImmediate(new AI_Goto(p.Copy(), 0)); "ok"')


def z2(ctx):
    """au reveil : plus d'ecran de sommeil, plus personne n'est endormi, chacun peut agir"""
    for port, who in ((H, "l'host"), (A, "l'invite")):
        ok = eventually(lambda port=port: awake(port), timeout=180)
        v = view(port)
        log(f"{who} : {v}")
        check(f"{who} se reveille : ni ecran de sommeil ni sommeil (ecrans : {v['layers'] or 'aucun'}, endormi : {v['asleep']})", ok)
        check(f"{who} peut agir (entrees {'bloquees' if v['halted'] else 'libres'}, mode {v['mode']})",
              not v["halted"] and v["mode"] == ctx["before"]["H" if port == H else "A"]["mode"] and not v["dead"])
        check(f"{who} : l'heure a avance", v["now"] > ctx["before"]["H" if port == H else "A"]["now"])
    # un pas, comme un joueur qui reprend la main
    for port, who in ((H, "l'host"), (A, "l'invite")):
        before = ev(port, 'EClass.pc.pos.x + "," + EClass.pc.pos.z')
        ev(port, 'var p = EClass.pc.pos.GetNearestPoint(allowChara: false, ignoreCenter: true); if (p != null) EClass.pc._Move(p); "ok"')
        check(f"{who} fait un pas", eventually(lambda port=port, before=before: ev(port, 'EClass.pc.pos.x + "," + EClass.pc.pos.z') != before, timeout=10))


def bedding(ctx):
    """un lit et un oreiller dans le sac de l'invite (donnes par l'host s'il n'en a pas), l'invite fatigue"""
    me = state(A)["pc"]["uid"]
    held = ('var b = EClass.pc.things.Find<TraitBed>(); var p = EClass.pc.things.Find<TraitPillow>(); '
            'return (b == null ? 0 : b.uid) + "," + (p == null ? 0 : p.uid);')
    if "0" in ev(A, held).split(","):
        ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {me}); if (c.things.Find<TraitBed>() == null) c.AddThing(ThingGen.Create("bed")); '
              'if (c.things.Find<TraitPillow>() == null) c.AddThing(ThingGen.Create("pillow_body")); "ok"')
        eventually(lambda: "0" not in ev(A, held).split(","), timeout=10)
    ctx["me"] = me
    ctx["bedding"] = [int(u) for u in ev(A, held).split(",")]
    ev(A, 'EClass.pc.sleepiness.Set(EClass.pc.sleepiness.max); "ok"')
    dismiss_dialogs(A)
    return ctx["bedding"]


def where(ctx, port):
    """ou sont le lit et l'oreiller, vus par ce jeu : "sol", "sac" (celui de l'invite), ou les deux, ou rien"""
    holder = "EClass.pc" if port == A else f'EClass._map.charas.Find(x => x.uid == {ctx["me"]})'
    uids = ", ".join(str(u) for u in ctx["bedding"])
    return ev(port, f'var h = {holder}; return string.Join(",", new[] {{ {uids} }}.Select(u => '
                    '(EClass._map.things.Any(t => t.uid == u) ? "sol" : "") + (h.things.Find(t => t.uid == u) != null ? "sac" : "")));')


def lie_down(ctx):
    """l'invite fait « Dormir » depuis sa barre : le jeu pose le lit et l'oreiller du sac a ses pieds"""
    ev(A, 'new HotItemActionSleep().Perform(); "ok"')
    ok = eventually(lambda: ev(H, f'(EClass._map.charas.Find(x => x.uid == {ctx["me"]}).conSleep != null).ToString()') == "True", timeout=10)
    return ok and eventually(lambda: where(ctx, H) == "sol,sol" and where(ctx, A) == "sol,sol", timeout=10)


def b1(ctx):
    """l'invite dort avec le lit et l'oreiller de son sac : au reveil ils sont revenus dans son sac
    (signale par l'utilisateur le 2026-10-02 : le lit restait pose par terre)"""
    bedding(ctx)
    ev(H, 'EClass.pc.sleepiness.Set(EClass.pc.sleepiness.max); "ok"')
    dismiss_dialogs(H)
    ok = lie_down(ctx)
    check(f"l'invite se couche : lit et oreiller poses au sol des deux cotes (host : {where(ctx, H)})", ok)
    ev(H, 'EClass.pc.Sleep(); "ok"')
    check("la nuit commence", eventually(lambda: "LayerSleep" in view(H)["layers"], timeout=60))
    for port, who in ((H, "l'host"), (A, "l'invite")):
        check(f"{who} se reveille", eventually(lambda port=port: awake(port), timeout=180))
    ok = eventually(lambda: where(ctx, A) == "sac,sac", timeout=15)
    check(f"chez l'invite, lit et oreiller sont revenus dans son sac (lit, oreiller : {where(ctx, A)})", ok)
    ok = eventually(lambda: where(ctx, H) == "sac,sac", timeout=15)
    check(f"chez l'host aussi, ils sont dans le sac de l'invite et plus au sol ({where(ctx, H)})", ok)


def b2(ctx):
    """l'invite se couche puis renonce (il bouge avant que l'host dorme) : lit et oreiller reviennent aussi"""
    bedding(ctx)
    ok = lie_down(ctx)
    check(f"l'invite se couche : lit et oreiller poses au sol des deux cotes (host : {where(ctx, H)})", ok)
    ev(A, STEP)
    check("l'invite n'attend plus le sommeil", eventually(lambda: not view(A)["asleep"], timeout=15))
    ok = eventually(lambda: where(ctx, A) == "sac,sac", timeout=15)
    check(f"chez l'invite, lit et oreiller sont revenus dans son sac ({where(ctx, A)})", ok)
    ok = eventually(lambda: where(ctx, H) == "sac,sac", timeout=15)
    check(f"chez l'host aussi ({where(ctx, H)})", ok)


def b3(ctx):
    """un lit deja installe sur la carte reste ou il est : l'invite s'y couche, renonce, le lit ne bouge pas"""
    bed = bedding(ctx)[0]
    ctx["bedding"] = [bed]
    ev(A, f'var b = EClass.pc.things.Find(t => t.uid == {bed}); EClass._zone.AddCard(b, EClass.pc.pos).Install(); "ok"')
    check("le lit est installe sur la carte des deux cotes",
          eventually(lambda: where(ctx, H) == "sol" and where(ctx, A) == "sol", timeout=10))
    # comme un clic sur un lit de la carte (AI_Sleep) : dormir dans ce lit, sans le reprendre
    ev(A, f'EClass.pc.Sleep(EClass._map.things.Find(t => t.uid == {bed})); "ok"')
    check("l'host note que l'invite veut dormir",
          eventually(lambda: ev(H, f'(EClass._map.charas.Find(x => x.uid == {ctx["me"]}).conSleep != null).ToString()') == "True", timeout=10))
    ev(A, STEP)
    check("l'invite n'attend plus le sommeil", eventually(lambda: not view(A)["asleep"], timeout=15))
    time.sleep(3)
    check(f"le lit est reste sur la carte (invite : {where(ctx, A)}, host : {where(ctx, H)})",
          where(ctx, A) == "sol" and where(ctx, H) == "sol")


def said(port, key):
    """combien de fois le jeu de ce joueur a dit ce message dans son journal (son texte vient du jeu, dans la langue
    de la fenetre : on cherche son plus long morceau fixe, sans les #1 des noms)"""
    return int(ev(port, """var k = Msg.GetGameText("%s").ToLower().Split(new[] { '#', '$', '{' }).OrderByDescending(s => s.Length).First().Trim(); """
                        """return EClass.game.log.dict.Values.Count(l => l.text != null && l.text.ToLower().Contains(k)).ToString();""" % key))


def k1(ctx):
    """nuit commune, l'invite a son grimoire, son oreiller (de Jure) et son lit : il joue SON reveil
    Ce que le banc ne joue pas comme un joueur : le livre, le grimoire et l'oreiller naissent chez l'host par eval
    (pas d'achat, pas de pillage) ; le sort du livre est un sort que ni l'invite ni l'host ne connaissent, tire par
    ThingGen ; l'invite dort par la barre (HotItemActionSleep) mais l'host par pc.Sleep() sans lit ; la lecture
    est sure (EClass.debug.godMode chez l'invite : aucun echec, donc aucun monstre ni teleportation) ; le sort en
    reve est force (le don 1653 et le domaine du feu chez l'invite) et le tirage de recette aussi (stats.slept
    remis a 0 des deux cotes : jusqu'a trois nuits le jeu apprend toujours une recette) ; le lit de l'invite a
    +500 de puissance (element 750) pour que ses PV reviennent au maximum, ce qui ne peut pas venir de la
    puissance du lit de l'host (20). Les echecs de lecture (un livre use sans rien lire) ne sont pas joues"""
    me = state(A)["pc"]["uid"]
    ctx["me"] = me
    grimoire, jure = first_id("Grimoire"), first_id("PillowJure")
    if not check(f"le jeu a un grimoire et un oreiller de Jure ({grimoire!r}, {jure!r})", grimoire and jure):
        return
    chars = f'EClass._map.charas.Find(x => x.uid == {me})'
    made = ev(H, f'var c = {chars}; foreach (var t in c.things.Where(x => x.trait is TraitPillow || x.trait is TraitGrimoire).ToList()) t.Destroy(); '
                 'Thing b = null; for (var i = 0; i < 30; i++) { b = ThingGen.Create("spellbook"); b.c_charges = 3; b.SetBlessedState(BlessedState.Normal); '
                 'if (!c.HasElement(b.refVal) && !EClass.pc.HasElement(b.refVal)) break; b.Destroy(); b = null; } '
                 'if (b == null) return "0,0"; '
                 f'var g = ThingGen.Create("{grimoire}"); g.AddThing(b); c.AddThing(g, false); c.AddThing(ThingGen.Create("{jure}"), false); '
                 'return b.uid + "," + b.refVal;')
    book, spell = (int(x) for x in made.split(","))
    if not check(f"un livre de sort inconnu des deux est dans le grimoire de l'invite (livre {book}, sort {spell})", book):
        return
    in_book = lambda p, who: ev(p, f'var g = {who}.things.Find<TraitGrimoire>(); var t = g == null ? null : g.things.Find(x => x.uid == {book}); '  # noqa: E731
                                   'return t == null ? "disparu" : t.c_charges.ToString();')
    check("le livre est dans le grimoire de l'invite, chez lui (3 charges)",
          eventually(lambda: in_book(A, "EClass.pc") == "3", timeout=15))
    bedding(ctx)
    domain = ev(A, 'var r = EClass.sources.elements.alias["eleFire"]; if (EClass.player.domains.Contains(r.id)) return "0"; '
                   'EClass.player.domains.Add(r.id); return r.id.ToString();')
    rec = lambda p: int(ev(p, 'EClass.player.recipes.knownRecipes.Values.Sum().ToString()'))  # noqa: E731
    knows = lambda p, who: ev(p, f'{who}.HasElement({spell}).ToString()') == "True"  # noqa: E731
    san = lambda p: int(ev(p, 'EClass.pc.SAN.value.ToString()'))  # noqa: E731
    try:
        for port in (H, A):
            ev(port, 'EClass.player.stats.slept = 0; "ok"')
        ev(A, 'EClass.debug.godMode = true; EClass.pc.elements.SetBase(1653, 1); EClass.pc.hp = 1; EClass.pc.SAN.Set(EClass.pc.SAN.max); '
              'EClass.pc.things.Find<TraitBed>().elements.SetBase(750, 100); "ok"')
        ev(H, 'EClass.pc.sleepiness.Set(EClass.pc.sleepiness.max); "ok"')
        dismiss_dialogs(H)
        before = {"rec": (rec(H), rec(A)), "recipe": said(A, "learnRecipeSleep"), "dream": said(A, "dream_spell"),
                  "san": (san(H), san(A))}
        check("avant la nuit : l'invite ne connait pas le sort, l'host non plus",
              not knows(A, "EClass.pc") and not knows(H, "EClass.pc"))
        check("l'invite se couche avec son lit et son oreiller", lie_down(ctx))
        ev(H, 'EClass.pc.Sleep(); "ok"')
        check("la nuit commence", eventually(lambda: "LayerSleep" in view(H)["layers"], timeout=60))
        for port, who in ((H, "l'host"), (A, "l'invite")):
            check(f"{who} se reveille", eventually(lambda port=port: awake(port), timeout=180))
        time.sleep(5)
        check("l'invite connait le sort de son livre, chez lui", eventually(lambda: knows(A, "EClass.pc"), timeout=15))
        check("et chez l'host, sur son personnage", eventually(lambda: knows(H, chars), timeout=15))
        check("l'host n'a rien recu de ce livre : il ne connait pas ce sort", not knows(H, "EClass.pc"))
        check(f"le livre a perdu ses charges chez l'invite, et chez l'host (invite : {in_book(A, 'EClass.pc')}, host : {in_book(H, chars)})",
              eventually(lambda: in_book(A, "EClass.pc") in ("0", "disparu") and in_book(H, chars) in ("0", "disparu"), timeout=15))
        check(f"un seul tirage de recette pour l'invite, dans son jeu ({said(A, 'learnRecipeSleep') - before['recipe']} message)",
              said(A, "learnRecipeSleep") - before["recipe"] == 1)
        check(f"recettes connues : +2 des deux cotes, celle de l'host et celle de l'invite, communes (host {rec(H) - before['rec'][0]}, "
              f"invite {rec(A) - before['rec'][1]})",
              eventually(lambda: rec(H) - before["rec"][0] == 2 and rec(A) - before["rec"][1] == 2, timeout=15))
        check(f"un seul sort en reve pour l'invite ({said(A, 'dream_spell') - before['dream']} message)",
              said(A, "dream_spell") - before["dream"] == 1)
        check(f"son oreiller de Jure a joue : sa raison a baisse de 15 (de {before['san'][1]} a {san(A)}), pas celle de l'host ({before['san'][0]} -> {san(H)})",
              before["san"][1] - san(A) >= 15 and san(H) == before["san"][0])
        hp, top = (int(x) for x in ev(A, 'EClass.pc.hp + "," + EClass.pc.MaxHP').split(","))
        check(f"la puissance de SON lit : ses PV sont au maximum ({hp} sur {top}), pas ceux d'un lit de 20", hp >= top)
    finally:
        ev(A, 'EClass.debug.godMode = false; EClass.pc.elements.SetBase(1653, 0); '
              + (f'EClass.player.domains.Remove({domain}); ' if domain != "0" else "") + '"ok"')


def z3(ctx):
    """panne provoquee : la fin de la nuit plante chez l'host. Personne ne doit rester dans l'ecran de sommeil
    (a lancer seul : --only z3 ; les exceptions des journaux sont voulues, elles ne sont pas comptees)"""
    me = state(A)["pc"]["uid"]
    for port in (H, A):
        ev(port, 'EClass.pc.sleepiness.Set(EClass.pc.sleepiness.max); "ok"')
    ctx["before"] = {"H": view(H), "A": view(A)}
    ev(A, 'EClass.pc.Sleep(); "ok"')
    eventually(lambda: ev(H, f'(EClass._map.charas.Find(x => x.uid == {me}).conSleep != null).ToString()') == "True", timeout=10)
    ev(H, 'EClass.pc.Sleep(); "ok"')
    try:
        # des que la nuit commence : un membre "vide" dans le groupe de l'host, le reveil du groupe plantera
        check("l'ecran de sommeil s'ouvre chez l'host",
              eventually(lambda: ev(H, 'if (EClass.ui.GetLayer<LayerSleep>() == null) return "non"; '
                                       'EClass.pc.party.members.Add(null); return "oui";') == "oui", timeout=60))
        for port, who in ((H, "l'host"), (A, "l'invite")):
            ok = eventually(lambda port=port: "LayerSleep" not in view(port)["layers"] and not view(port)["asleep"], timeout=120)
            v = view(port)
            check(f"{who} ne reste pas bloque (ecrans : {v['layers'] or 'aucun'}, endormi : {v['asleep']}, "
                  f"entrees {'bloquees' if v['halted'] else 'libres'})", ok and not v["halted"])
    finally:
        ev(H, 'EClass.pc.party.members.RemoveAll(m => m == null); "ok"')
        ctx["faulty"] = True


def y1(ctx):
    """l'invite seul sur une carte qu'il tient y dort ; l'host ne dort pas"""
    from travel_suite import HOME, VERNIS, both_joined, client_settled, move, wait
    move(A, VERNIS)
    wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
    time.sleep(3)
    dismiss_dialogs(A)
    ev(A, 'EClass.pc.sleepiness.Set(EClass.pc.sleepiness.max); "ok"')
    before = {"H": view(H), "A": view(A)}
    ev(A, 'EClass.pc.Sleep(); "ok"')
    ok = eventually(lambda: "LayerSleep" in view(A)["layers"], timeout=60)
    check(f"l'ecran de sommeil s'ouvre chez l'invite ({view(A)['layers'] or 'rien'}, endormi : {view(A)['asleep']})", ok)
    if ok:
        woke = eventually(lambda: awake(A), timeout=180)
        v = view(A)
        check(f"l'invite se reveille et peut agir (ecrans : {v['layers'] or 'aucun'}, entrees "
              f"{'bloquees' if v['halted'] else 'libres'})", woke and not v["halted"])
        check("chez lui, l'heure a avance", v["now"] > before["A"]["now"])
    h = view(H)
    check("l'host n'a pas dormi", not h["asleep"] and "LayerSleep" not in h["layers"])
    move(A, HOME)
    both_joined(H, A, HOME)


def lease_requests():
    try:
        return sum("Requesting zone lease" in line for line in session_log_lines(""))
    except OSError:
        return 0


def y2(ctx):
    """l'invite, seul sur un champ qu'il tient, y dort : sa carte n'est pas rechargee, il est a la meme case au reveil,
    aucun bail n'est demande a l'host
    Ce que le banc ne joue pas comme un joueur : la sortie par le bord (ExitBorder) et l'entree sur la case libre
    (EnterLocalZone) sont appelees par eval, sans le dialogue ni la marche ; la fatigue est forcee ; l'invite dort
    par pc.Sleep() et non dans un lit ; le retard d'une base (pendingSimHours = 5 sur la Prairie) est pose par eval,
    il n'y a qu'une base et une vraie partie en aurait une de plus ; un champ seulement, pas une base ni la carte du
    monde. Rouge avant la correction : le jeu parcourt la base en retard au reveil (bail demande, carte relue)"""
    from travel_suite import HOME, both_joined, client_settled, enter_at, free_spot, move, wait
    region = int(ev(A, 'EClass._zone.ParentZone.uid.ToString()'))
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(A, region, True), "invite sur la carte du monde", timeout=120)
    time.sleep(3)
    enter_at(A, free_spot(A, HOME))
    wait(lambda: (lambda s: s.get("sceneMode") == "Zone" and s.get("awayZone"))(state(A)), "invite seul sur un champ", timeout=120)
    time.sleep(3)
    dismiss_dialogs(A)
    check("l'invite est seul sur un champ (le sommeil y simule les bases)",
          ev(A, '(EClass._zone is Zone_Field).ToString()') == "True")
    base = f'((Zone)EClass.game.spatials.Find({HOME}))'
    ev(A, f'{base}.pendingSimHours = 5; EClass.pc.sleepiness.Set(EClass.pc.sleepiness.max); "ok"')
    probe = ('return EClass._zone.uid + "|" + EClass.pc.pos.x + "," + EClass.pc.pos.z + "|" + '
             'System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(EClass._map) + "|" + ' + base + '.pendingSimHours;')
    before, leases = ev(A, probe), lease_requests()
    ev(A, 'EClass.pc.Sleep(); "ok"')
    ok = eventually(lambda: "LayerSleep" in view(A)["layers"], timeout=60)
    check(f"l'ecran de sommeil s'ouvre chez l'invite ({view(A)['layers'] or 'rien'})", ok)
    if ok:
        woke = eventually(lambda: "LayerSleep" not in view(A)["layers"] and not view(A)["asleep"], timeout=180)
        time.sleep(2)
        v, after = view(A), ev(A, probe)
        log(f"avant : {before} ; apres : {after}")
        check(f"l'invite se reveille et peut agir (ecrans : {v['layers'] or 'aucun'}, entrees "
              f"{'bloquees' if v['halted'] else 'libres'})", woke and not v["halted"])
        check("meme carte, meme case, carte non rechargee, base en retard non parcourue (zone | case | carte | retard)",
              after == before)
        check("aucun bail demande a l'host pendant la nuit", lease_requests() == leases)
    ev(A, f'{base}.pendingSimHours = 0; "ok"')
    move(A, HOME)
    both_joined(H, A, HOME)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {}
    steps = [z0, p1, z1, p2, z2, b1, b2, b3, k1, y1, y2]
    if a.only:
        steps = [s for s in (w0, z0, p1, z1, p2, z2, b1, b2, b3, k1, y1, y2, z3) if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'sleep-{step.__name__}-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass

    if not ctx.get("faulty"):
        scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
