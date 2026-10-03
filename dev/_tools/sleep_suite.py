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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {}
    steps = [z0, z1, z2, b1, b2, b3, y1]
    if a.only:
        steps = [s for s in (w0, z0, z1, z2, b1, b2, b3, y1, z3) if s.__name__ in a.only.split(",")]
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
