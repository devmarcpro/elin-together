"""Suite de verification complete du voyage independant.

    python _tools/travel_suite.py              # relance tout depuis zero (mp_test) puis enchaine les scenarios
    python _tools/travel_suite.py --reuse      # sur des instances deja connectees (host + client dans la Prairie)

Scenarios (dans l'ordre, chacun part de l'etat laisse par le precedent) :
  S1  aller-retour vers une zone jamais generee chez l'host, depot d'objets, retour
  S2  apres le retour, la synchro normale marche encore (deplacement, ramassage)
  S3  l'host entre dans la zone et y trouve les objets du client
  S4  2e visite : le client recoit la carte de l'host, ramasse un objet, en depose un autre
  S5  enchainement de deux zones sans repasser par l'host
  S6  chemin reel : sortie par le bord -> carte du monde -> ville -> carte du monde -> retour
  S7  l'host entre dans la zone ou se trouve le client : rappel, puis l'host y entre
  S8  voyage refuse par l'host : le client reste en place, rien n'est casse
  S9  aucune sauvegarde ecrite par le client pendant ses absences
  S10 deconnexion pendant une absence, puis reconnexion
  S11 persistance : l'host sauvegarde, recharge, et retrouve tout
  S17 equipement : l'host ajoute un objet a son sac et l'equipe dans le meme tick, puis le retire ; le client
      voit le meme emplacement (correctif CharaEquipDelta ; python _tools/travel_suite.py --reuse --only s17)
Les logs (Unity host/client, ElinTogether) sont scannes a la fin.
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import (LAB_EXE, ROOT, SAVES, SHOTS, WINDOW, bridge_for, join_client, log, ok, shot, state,  # noqa: E402
                     wait)

HOME, VERNIS, LUMIEST = 7, 16, 42
LOCALLOW = SAVES.parent
RESULTS = []


def ev(port, code, timeout=180):
    return ok(emp.call(port, "eval", {"code": code}, timeout=timeout))


def check(label, cond):
    RESULTS.append((label, bool(cond)))
    print(f"    [{'OK' if cond else 'ECHEC'}] {label}", flush=True)
    return cond


def zone_uid(port):
    # a game dialog (tutorial, story) holds zone changes until clicked away
    dismiss_dialogs(port)
    return (state(port).get("zone") or {}).get("uid")


def dismiss_dialogs(port):
    """Ferme un dialogue du jeu (tutoriel, histoire) comme le joueur le ferait d'un clic."""
    if drama(port):
        ev(port, 'EClass.ui.RemoveLayer<LayerDrama>(); "ok"')
        log(f"dialogue du jeu ferme sur le port {port}")


def client_settled(client, uid, away):
    def cond():
        dismiss_dialogs(client)
        s = state(client)
        return (s.get("sceneMode") == "Zone" and (s.get("zone") or {}).get("uid") == uid
                and bool(s.get("awayZone")) == away and s.get("connected"))
    return cond


def move(port, uid):
    ev(port, f'EClass.pc.MoveZone(EClass.game.spatials.Find({uid})); "ok"')


def marker(port):
    """Seau cree a quelques cases du joueur, renvoie (uid, "x,z").
    Ni nourriture ni sur le point d'arrivee : les compagnons ramassent et mangent ce qui y traine."""
    uid, pos = ev(port, 'var t = ThingGen.Create("bucket"); var p = EClass.pc.pos.Copy(); p.x += 4; '
                        'p = p.GetNearestPoint(allowChara: false) ?? EClass.pc.pos; EClass._zone.AddCard(t, p); '
                        't.uid + "|" + p.x + "," + p.z').split("|")
    return int(uid), pos


def on_map(port, uids):
    """uid -> "x,z" des objets presents sur la carte active."""
    if not uids:
        return {}
    res = ev(port, 'string.Join(";", EClass._map.things.Where(t => new[] {' + ",".join(map(str, uids)) + '}'
                   '.Contains(t.uid)).Select(t => t.uid + "@" + t.pos.x + "," + t.pos.z))')
    return {int(x.split("@")[0]): x.split("@")[1] for x in res.split(";") if x}


def client_chara_has(host, chara_uid, thing_uid):
    return ev(host, f'EClass.game.cards.globalCharas.Find({chara_uid}).things.Find({thing_uid}) != null ? "y" : "n"') == "y"


def drama(port):
    return ev(port, 'LayerDrama.IsActive().ToString()') == "True"


def uid_next(port):
    return int(ev(port, 'EClass.game.cards.uidNext.ToString()'))


def leases(host):
    return int(ev(host, 'HarmonyLib.Traverse.Create(ElinTogether.Net.NetSession.Instance.Transport)'
                        '.Field("_leases").GetValue<System.Collections.Generic.Dictionary<int, System.Collections.Generic.Dictionary<int, int>>>()'
                        '.Values.Sum(z => z.Count).ToString()'))


def save_mtime():
    f = SAVES / "world_lab" / "game.txt"
    return f.stat().st_mtime if f.exists() else 0


def players(port):
    return len(state(port).get("players", []))


def both_joined(host, client, zone):
    wait(client_settled(client, zone, False), f"client rejoint en zone {zone}", timeout=180)
    wait(lambda: players(host) == 2 and players(client) == 2, "2 joueurs des deux cotes", timeout=60)
    time.sleep(3)


def host_goto(host, client, uid):
    """L'host change de carte, le client le rejoint.
    Depuis que l'host ne traine plus les joueurs, le client reste ou il est (et herite de la carte) : il rejoint
    l'host de lui-meme, sauf si l'host revient sur la carte qu'il tient (rappel, le client suit tout seul)."""
    move(host, uid)
    wait(lambda: zone_uid(host) == uid, f"host en zone {uid}", timeout=180)
    time.sleep(4)
    s = state(client)
    if s.get("awayZone") or (s.get("zone") or {}).get("uid") != uid:
        move(client, uid)
    both_joined(host, client, uid)


# --------------------------------------------------------------------------------------------------

def s1(ctx):
    host, client = ctx["host"], ctx["client"]
    ctx["chara"] = state(client)["pc"]["uid"]
    u0 = uid_next(host)
    move(client, VERNIS)
    wait(client_settled(client, VERNIS, True), "client seul a Vernis")
    check("client seul a Vernis, host reste a la Prairie", zone_uid(host) == HOME and players(host) == 1)
    shot("s1-client-away", client)
    axe, axe_pos = ev(client, 'var a = EClass.pc.things.Find("axe"); if (a == null) return "-1|"; var u = a.uid; EClass.pc.DropThing(a); '
                              'u + "|" + EClass.pc.pos.x + "," + EClass.pc.pos.z').split("|")
    axe = int(axe)
    apple, pos = marker(client)
    ctx.update(axe=axe, axe_pos=axe_pos, s1_apple=apple, s1_pos=pos)
    check(f"objet cree dans la plage reservee (uid {apple} >= {u0} + 50000)", apple >= u0 + 50_000)
    saved = save_mtime()
    # deux demandes de retour d'affilee : une seule doit partir
    move(client, HOME)
    move(client, HOME)
    both_joined(host, client, HOME)
    time.sleep(3)
    check("retour demande deux fois : toujours 2 joueurs, aucun bail restant", players(host) == 2 and leases(host) == 0)
    check("host : sauvegarde automatique au retour du client", save_mtime() > saved)
    check("host : aucun jeton de competence du client dans son inventaire",
          ev(host, f'EClass.game.cards.globalCharas.Find({ctx["chara"]}).things.List(t => t.trait is TraitAbility).Count.ToString()') == "0")
    check("host : le perso du client n'a plus la hache", not client_chara_has(host, ctx["chara"], axe))
    check("host : Vernis marquee generee", ev(host, f'EClass.game.spatials.Find({VERNIS}).isGenerated.ToString()') == "True")
    check("host : compteur d'uid au-dela de la pomme", int(ev(host, 'EClass.game.cards.uidNext.ToString()')) > apple)


def s2(ctx):
    host, client = ctx["host"], ctx["client"]
    before = ev(host, f'var c = EClass.game.cards.globalCharas.Find({ctx["chara"]}); c.pos.x + "," + c.pos.z')
    target = ev(client, 'var p = EClass.pc.pos.GetNearestPoint(allowChara: false, ignoreCenter: true); EClass.pc._Move(p); p.x + "," + p.z')
    wait(lambda: ev(host, f'var c = EClass.game.cards.globalCharas.Find({ctx["chara"]}); c.pos.x + "," + c.pos.z') == target,
         "host voit le client bouger", timeout=30)
    check(f"deplacement du client vu par l'host ({before} -> {target})", True)
    bread = int(ev(host, f'var c = EClass.game.cards.globalCharas.Find({ctx["chara"]}); var t = ThingGen.Create("apple"); '
                         'EClass._zone.AddCard(t, c.pos); t.uid.ToString()'))
    time.sleep(3)
    ev(client, f'var t = EClass._map.things.Find(x => x.uid == {bread}); if (t != null) EClass.pc.Pick(t); "ok"')
    wait(lambda: client_chara_has(host, ctx["chara"], bread), "host voit le ramassage", timeout=30)
    check("objet pose par l'host ramasse par le client, vu par l'host", True)


def s3(ctx):
    host, client = ctx["host"], ctx["client"]
    host_goto(host, client, VERNIS)
    found = on_map(host, [ctx["axe"], ctx["s1_apple"]])
    check(f"host a Vernis : hache au sol en {ctx['axe_pos']} et objet en {ctx['s1_pos']}",
          found.get(ctx["axe"]) == ctx["axe_pos"] and found.get(ctx["s1_apple"]) == ctx["s1_pos"])
    check("client suit l'host a Vernis (replique, pas absent)", not state(client).get("awayZone"))
    shot("s3-host-vernis", host)
    host_goto(host, client, HOME)


def s4(ctx):
    host, client = ctx["host"], ctx["client"]
    move(client, VERNIS)
    wait(client_settled(client, VERNIS, True), "client seul a Vernis (2e visite)")
    found = on_map(client, [ctx["axe"], ctx["s1_apple"]])
    check("2e visite : le client voit la carte de l'host (hache au sol)", found.get(ctx["axe"]) == ctx["axe_pos"])
    ev(client, f'var t = EClass._map.things.Find(x => x.uid == {ctx["axe"]}); if (t != null) EClass.pc.Pick(t); "ok"')
    apple, pos = marker(client)
    ctx.update(s4_apple=apple, s4_pos=pos)
    move(client, HOME)
    both_joined(host, client, HOME)
    check("host : le perso du client a repris la hache", client_chara_has(host, ctx["chara"], ctx["axe"]))


def apples(host, chara):
    return int(ev(host, f'EClass.game.cards.globalCharas.Find({chara}).things.List(t => t.id == "apple").Sum(t => t.Num).ToString()'))


def s5(ctx):
    host, client = ctx["host"], ctx["client"]
    ctx["s5_apples"] = apples(host, ctx["chara"])
    last = int(ev(host, f'var c = EClass.game.cards.globalCharas.Find({ctx["chara"]}); var t = ThingGen.Create("apple"); '
                        'EClass._zone.AddCard(t, c.pos); t.uid.ToString()'))
    time.sleep(3)
    # ramassage et depart dans la meme frame
    ev(client, f'var t = EClass._map.things.Find(x => x.uid == {last}); if (t != null) EClass.pc.Pick(t); '
               f'EClass.pc.MoveZone(EClass.game.spatials.Find({VERNIS})); "ok"')
    wait(client_settled(client, VERNIS, True), "client a Vernis")
    check("action juste avant le depart appliquee par l'host (objet plus au sol chez l'host)",
          not on_map(host, [last]))
    ctx["s5_last"] = last
    a, apos = marker(client)
    move(client, LUMIEST)
    wait(client_settled(client, LUMIEST, True), "client passe directement a Lumiest")
    check("Vernis -> Lumiest sans repasser par l'host", zone_uid(host) == HOME and players(host) == 1)
    b, bpos = marker(client)
    ctx.update(s5_vernis=(a, apos), s5_lumiest=(b, bpos))
    move(client, HOME)
    both_joined(host, client, HOME)
    check("host : Lumiest marquee generee", ev(host, f'EClass.game.spatials.Find({LUMIEST}).isGenerated.ToString()') == "True")
    n = apples(host, ctx["chara"])
    check(f"host : l'objet ramasse juste avant le depart est dans l'inventaire du client (pommes {ctx['s5_apples']} -> {n})",
          n == ctx["s5_apples"] + 1)


def s6(ctx):
    host, client = ctx["host"], ctx["client"]
    region = int(ev(client, 'EClass._zone.ParentZone.uid.ToString()'))
    ev(client, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(client, region, True), "client sur la carte du monde")
    check("sortie par le bord : client seul sur la carte du monde", zone_uid(host) == HOME)
    shot("s6-client-worldmap", client)
    enter = ('var z = EClass.game.spatials.Find({uid}); var em = EClass.scene.elomap; '
             'EClass.player.EnterLocalZone(new Point(z.x - em.minX, z.y - em.minY)); "ok"')
    ev(client, enter.format(uid=VERNIS))
    wait(client_settled(client, VERNIS, True), "client entre a Vernis depuis la carte du monde")
    c, cpos = marker(client)
    ctx["s6"] = (c, cpos)
    ev(client, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(client, region, True), "client ressort sur la carte du monde")
    ev(client, enter.format(uid=HOME))
    both_joined(host, client, HOME)
    check("retour a pied dans la Prairie : client rejoint l'host", True)


def s7(ctx):
    host, client = ctx["host"], ctx["client"]
    move(client, VERNIS)
    wait(client_settled(client, VERNIS, True), "client seul a Vernis")
    d, dpos = marker(client)
    ctx["s7"] = (d, dpos)
    move(host, VERNIS)
    wait(lambda: zone_uid(host) == VERNIS, "host entre a Vernis apres rappel", timeout=180)
    both_joined(host, client, VERNIS)
    found = on_map(host, [d, ctx["s4_apple"], ctx["s5_vernis"][0], ctx["s6"][0], ctx["axe"]])
    check("rappel : l'host a Vernis voit la pomme posee juste avant", found.get(d) == dpos)
    check("... et celles des visites precedentes (S4, S5, S6)",
          found.get(ctx["s4_apple"]) == ctx["s4_pos"] and found.get(ctx["s5_vernis"][0]) == ctx["s5_vernis"][1]
          and found.get(ctx["s6"][0]) == ctx["s6"][1])
    check("... et plus la hache (reprise en S4)", ctx["axe"] not in found)
    shot("s7-host-recall", host)
    host_goto(host, client, LUMIEST)
    found = on_map(host, [ctx["s5_lumiest"][0]])
    check("host a Lumiest : pomme deposee en S5", found.get(ctx["s5_lumiest"][0]) == ctx["s5_lumiest"][1])
    ghosts = ev(host, f'EClass.pc.homeBranch.members.Count(c => c.uid == {ctx["chara"]}).ToString()')
    check(f"base de l'host : le client n'y figure qu'une fois apres plusieurs voyages ({ghosts})", ghosts == "1")
    host_goto(host, client, HOME)


def s8(ctx):
    host, client = ctx["host"], ctx["client"]
    toggle = ('var t = HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Server"); '
              'var e = (BepInEx.Configuration.ConfigEntry<bool>)HarmonyLib.AccessTools.Property(t, "IndependentTravel").GetValue(null); '
              'e.Value = {v}; e.Value.ToString()')
    ev(host, toggle.format(v="false"))
    move(client, LUMIEST)
    time.sleep(8)
    s = state(client)
    check("voyage refuse : client toujours a la Prairie, pas absent, connecte",
          (s.get("zone") or {}).get("uid") == HOME and not s.get("awayZone") and s.get("connected"))
    ev(host, toggle.format(v="true"))
    before = ev(host, f'var c = EClass.game.cards.globalCharas.Find({ctx["chara"]}); c.pos.x + "," + c.pos.z')
    target = ev(client, 'var p = EClass.pc.pos.GetNearestPoint(allowChara: false, ignoreCenter: true); EClass.pc._Move(p); p.x + "," + p.z')
    try:
        wait(lambda: ev(host, f'var c = EClass.game.cards.globalCharas.Find({ctx["chara"]}); c.pos.x + "," + c.pos.z') == target,
             "synchro apres refus", timeout=30)
        check(f"synchro normale apres le refus ({before} -> {target})", True)
    except TimeoutError:
        check("synchro normale apres le refus", False)


def s12(ctx):
    """mort d'un client pres de l'host : pas de voyage, l'host gere la resurrection"""
    host, client = ctx["host"], ctx["client"]
    ev(client, f'EClass.player.deathZoneMove = true; EClass.pc.MoveZone(EClass.game.spatials.Find({LUMIEST})); '
               'EClass.player.deathZoneMove = false; "ok"')
    time.sleep(6)
    s = state(client)
    check("deplacement apres la mort : pas de bail, client reste chez l'host",
          (s.get("zone") or {}).get("uid") == HOME and not s.get("awayZone") and leases(host) == 0 and players(host) == 2)


def s13(ctx):
    """aller-retour sur la carte du monde sans rien creer : le compteur d'uid de l'host ne saute pas"""
    host, client = ctx["host"], ctx["client"]
    u0 = uid_next(host)
    region = int(ev(client, 'EClass._zone.ParentZone.uid.ToString()'))
    ev(client, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(client, region, True), "client sur la carte du monde")
    ev(client, f'var z = EClass.game.spatials.Find({HOME}); var em = EClass.scene.elomap; '
               'EClass.player.EnterLocalZone(new Point(z.x - em.minX, z.y - em.minY)); "ok"')
    both_joined(host, client, HOME)
    u1 = uid_next(host)
    check(f"compteur d'uid de l'host : +{u1 - u0} (pas de saut de reserve)", u1 - u0 < 50_000)


FREE_SPOT = (
    'var z = EClass.game.spatials.Find(__UID__); var r = EClass._zone.Region; '
    'foreach (var d in new[] { 3, 4, 5, 6, 7 }) foreach (var o in new[] { new[] { d, 0 }, new[] { 0, d }, new[] { -d, 0 }, new[] { 0, -d } }) { '
    'var w = new Point(z.x + o[0], z.y + o[1]); if (r.GetZoneAt(w.x, w.z) == null && r.CanCreateZone(w)) return w.x + "," + w.z; } return "";')
ENTER_AT = ('var em = EClass.scene.elomap; EClass.player.EnterLocalZone(new Point(__X__ - em.minX, __Y__ - em.minY)); "ok"')


def free_spot(port, near_uid, taken=()):
    spot = ev(port, FREE_SPOT.replace("__UID__", str(near_uid)))
    return spot


def enter_at(port, spot):
    x, y = spot.split(",")
    ev(port, ENTER_AT.replace("__X__", x).replace("__Y__", y))


def zone_at(port, spot):
    x, y = spot.split(",")
    r = ev(port, f'var z = EClass._zone.Region.GetZoneAt({x}, {y}); z == null ? "" : z.uid + "|" + z.ZoneFullName')
    return r


def s14(ctx):
    """client absent sur la carte du monde : entre sur une case libre (zone creee chez lui)"""
    host, client = ctx["host"], ctx["client"]
    region = int(ev(client, 'EClass._zone.ParentZone.uid.ToString()'))
    ev(client, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(client, region, True), "client sur la carte du monde")
    spot = free_spot(client, HOME)
    check(f"case libre trouvee pres de la Prairie ({spot})", bool(spot))
    enter_at(client, spot)
    wait(lambda: (lambda s: s.get("sceneMode") == "Zone" and "field" in ((s.get("zone") or {}).get("name") or "")
                  and s.get("awayZone"))(state(client)), "client dans la zone creee", timeout=120)
    uid = zone_uid(client)
    host_view = ev(host, f'var z = EClass.game.spatials.Find({uid}); z == null ? "" : z.ZoneFullName + "@" + z.x + "," + z.y')
    check(f"host : zone creee par le client connue sous le meme uid {uid} ({host_view})", host_view.endswith("@" + spot))
    m, mpos = marker(client)
    ev(client, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(client, region, True), "client ressort sur la carte du monde")
    enter_at(client, ev(client, f'var z = EClass.game.spatials.Find({HOME}); z.x + "," + z.y'))
    both_joined(host, client, HOME)
    # l'host va voir
    ev(host, 'EClass.player.ExitBorder(); "ok"')
    wait(lambda: zone_uid(host) == region, "host sur la carte du monde", timeout=120)
    time.sleep(3)
    enter_at(host, spot)
    wait(lambda: zone_uid(host) == uid, "host entre dans la zone du client", timeout=120)
    # le client est reste a la Prairie quand l'host est parti : il le rejoint de lui-meme
    time.sleep(3)
    move(client, uid)
    both_joined(host, client, uid)
    found = on_map(host, [m])
    check("host : la pomme posee par le client dans sa zone est la", found.get(m) == mpos)
    ctx.update(region=region, s14_spot=spot)


def s15(ctx):
    """host et client sur la carte du monde, le client entre seul sur une case libre"""
    host, client = ctx["host"], ctx["client"]
    region = ctx["region"]
    ev(host, 'EClass.player.ExitBorder(); "ok"')
    wait(lambda: zone_uid(host) == region, "host sur la carte du monde", timeout=120)
    # l'host ne traine plus les joueurs : le client, reste a la Prairie, sort de lui-meme
    time.sleep(4)
    st = state(client)
    if st.get("awayZone") or (st.get("zone") or {}).get("uid") != region:
        ev(client, 'EClass.player.ExitBorder(); "ok"')
    both_joined(host, client, region)
    spot = free_spot(client, HOME)
    if spot == ctx["s14_spot"]:
        spot = free_spot(client, VERNIS)
    enter_at(client, spot)
    wait(lambda: (lambda s: s.get("sceneMode") == "Zone" and s.get("awayZone"))(state(client)), "client seul dans sa zone", timeout=120)
    uid = zone_uid(client)
    check(f"client seul dans une zone creee chez lui, host sur la carte du monde (uid {uid})",
          zone_uid(host) == region and ev(host, f'(EClass.game.spatials.Find({uid}) != null).ToString()') == "True")
    m, mpos = marker(client)
    ev(client, 'EClass.player.ExitBorder(); "ok"')
    both_joined(host, client, region)
    check("sortie sur la carte du monde ou est l'host : client rejoint l'host", True)
    enter_at(host, spot)
    wait(lambda: zone_uid(host) == uid, "host entre dans la zone du client", timeout=120)
    # le client est reste sur la carte du monde quand l'host est parti : il le rejoint de lui-meme
    time.sleep(3)
    move(client, uid)
    both_joined(host, client, uid)
    check("host : la pomme du client est dans cette zone", on_map(host, [m]).get(m) == mpos)
    host_goto(host, client, HOME)


def say(port, text):
    """Comme un message tape avec Entree : ligne dans le journal puis envoi par le chat."""
    ev(port, f'Msg.Say("{text}"); ActionMode.Adv.OnEnterChat("{text}"); "ok"')


def log_has(port, text):
    # Msg.Say capitalizes the line
    return ev(port, f'EClass.game.log.dict.Values.Any(l => l.text != null && l.text.ToLower().Contains("{text.lower()}")).ToString()') == "True"


def eventually(cond, timeout=20):
    try:
        wait(cond, "", timeout=timeout, every=1.0)
        return True
    except TimeoutError:
        return False


def s16(ctx):
    """chat : un joueur parti seul discute avec l'host dans les deux sens"""
    host, client = ctx["host"], ctx["client"]
    move(client, VERNIS)
    wait(client_settled(client, VERNIS, True), "client seul a Vernis")
    say(client, "coucou depuis Vernis")
    check("chat : l'host recoit le message du joueur parti seul", eventually(lambda: log_has(host, "coucou depuis Vernis")))
    say(host, "coucou depuis la Prairie")
    check("chat : le joueur parti seul recoit le message de l'host", eventually(lambda: log_has(client, "coucou depuis la Prairie")))
    move(client, HOME)
    both_joined(host, client, HOME)


def worn(port, chara_uid, thing_uid):
    """Vu de ce jeu : "<emplacement du perso qui tient l'objet, -1 si aucun>|<c_equippedSlot de l'objet>"."""
    return ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {chara_uid}); if (c == null) return "absent"; '
                    f'var t = c.things.Find({thing_uid}); if (t == null) return "none"; '
                    'c.body.slots.FindIndex(s => s.thing == t) + "|" + t.c_equippedSlot')


def equip_new(host, item):
    """L'host cree un objet, le met dans son sac et l'equipe dans la meme evaluation (donc le meme tick reseau,
    comme equiper depuis un coffre ou le sol). Renvoie (uid, etat vu par l'host, voir worn).
    Etat normal force : un objet cree maudit ne pourrait plus etre remplace."""
    uid, on = ev(host, f'var t = ThingGen.Create("{item}"); t.SetBlessedState(BlessedState.Normal); EClass.pc.AddThing(t); '
                       'EClass.pc.body.Equip(t); t.uid + "#" + EClass.pc.body.slots.FindIndex(s => s.thing == t) + "|" '
                       '+ t.c_equippedSlot').split("#")
    return int(uid), on


def s17(ctx):
    """equipement : objet ajoute au sac et equipe dans le meme tick par l'host, puis retire"""
    host, client = ctx["host"], ctx["client"]
    me = state(host)["pc"]["uid"]
    helm, on = equip_new(host, "helm_knight")
    slot = int(on.split("|")[0])
    check(f"host : casque {helm} ajoute et equipe d'un coup (emplacement {slot})", slot >= 0 and on == f"{slot}|{slot + 1}")
    check(f"client : l'emplacement du perso de l'host tient le casque ({on})", eventually(lambda: worn(client, me, helm) == on))
    # un 2e casque prend la place du premier, toujours dans le meme tick
    helm2, on2 = equip_new(host, "helm_knight")
    check(f"host : 2e casque {helm2} equipe a la place du premier", on2 == on and worn(host, me, helm) == "-1|0")
    check("client : l'emplacement tient le 2e casque, le premier est dans le sac, plus equipe",
          eventually(lambda: worn(client, me, helm2) == on and worn(client, me, helm) == "-1|0"))
    ev(host, f'EClass.pc.body.Unequip(EClass.pc.things.Find({helm2})); "ok"')
    check("host : casque retire", worn(host, me, helm2) == "-1|0")
    check("client : casque retire (emplacement vide, c_equippedSlot a 0)",
          eventually(lambda: worn(client, me, helm2) == "-1|0")
          and ev(client, f'(EClass._map.charas.Find(x => x.uid == {me}).body.slots[{slot}].thing == null).ToString()') == "True")


def s9(ctx):
    emp_save = SAVES / "world_emp"
    written = [p.name for p in (emp_save.glob("*.txt") if emp_save.exists() else [])]
    check(f"aucune sauvegarde du client dans world_emp ({written or 'rien'})", not written)
    blocked = sum("Blocked saving game as client" in l for l in session_log_lines(ctx["t0"]))
    check(f"sauvegardes du client bloquees pendant les absences ({blocked} blocages)", True)


def s10(ctx):
    host, client = ctx["host"], ctx["client"]
    # short checkpoint interval for the test (host setting sent to clients, 60 s by default)
    ev(client, 'ElinTogether.Net.NetSession.Instance.Rules.TravelCheckpointSeconds = 5; "ok"')
    move(client, LUMIEST)
    wait(client_settled(client, LUMIEST, True), "client seul a Lumiest")
    axe_pos = ev(client, f'var a = EClass.pc.things.Find({ctx["axe"]}); if (a == null) return ""; EClass.pc.DropThing(a); '
                         'EClass.pc.pos.x + "," + EClass.pc.pos.z')
    m, mpos = marker(client)
    ctx["s10"] = (axe_pos, m, mpos)
    check("checkpoint automatique : l'host voit que le client a lache sa hache, sans qu'il soit revenu",
          eventually(lambda: not client_chara_has(host, ctx["chara"], ctx["axe"]), timeout=20))
    saved = save_mtime()
    pid = next(h["pid"] for h in emp.live_ports() if h["port"] == client)
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    log(f"client tue (pid {pid}) pendant son absence")
    wait(lambda: players(host) == 1 and ev(host, 'HarmonyLib.Traverse.Create(ElinTogether.Net.NetSession.Instance.Transport)'
                                               '.Field("_leases").Property("Count").GetValue().ToString()') == "0",
         "host : bail libere", timeout=60)
    check("host : toujours host, bail libere apres la deconnexion", state(host)["role"] == "Host")
    check("host : sauvegarde automatique apres la deconnexion (dernier checkpoint conserve)", save_mtime() > saved)
    proc = subprocess.Popen([str(LAB_EXE), *WINDOW, "-logFile", str(SHOTS / "elin2-player.log")], cwd=LAB_EXE.parent)
    client = ctx["client"] = wait(lambda: bridge_for(proc.pid), "pont du client relance")
    # like a player at the title screen: connect once the freshly started game stopped loading
    wait(lambda: state(client).get("sceneMode") == "Title", "ecran titre du client", timeout=180)
    time.sleep(20)
    # l'host demande avec quel personnage jouer : join_client reprend celui d'avant (le premier de la liste)
    join_client(host, client, "client")
    both_joined(host, client, HOME)
    check("client reconnecte et de retour chez l'host", True)
    check("apres reconnexion : l'inventaire vient du dernier checkpoint (plus de hache)",
          not client_chara_has(host, ctx["chara"], ctx["axe"]))


def s11(ctx):
    host = ctx["host"]
    ev(host, 'EClass.game.Save(); "ok"')
    # TryLoad is blocked in game while hosting (GameSaveLoad), end the session and load directly
    ev(host, 'ElinTogether.Net.NetSession.Instance.ResetSession(); Game.Load("world_lab", false); "ok"')
    wait(lambda: state(host)["gameStarted"] and state(host)["sceneMode"] == "Zone", "host recharge la partie", timeout=240)
    move(host, VERNIS)
    wait(lambda: zone_uid(host) == VERNIS and state(host)["sceneMode"] == "Zone", "host a Vernis apres rechargement", timeout=240)
    time.sleep(3)
    found = on_map(host, [ctx["s7"][0], ctx["s4_apple"], ctx["s6"][0]])
    check("apres sauvegarde + rechargement, les objets deposes a Vernis sont la",
          found.get(ctx["s7"][0]) == ctx["s7"][1] and found.get(ctx["s4_apple"]) == ctx["s4_pos"]
          and found.get(ctx["s6"][0]) == ctx["s6"][1])
    axe_pos, m, mpos = ctx["s10"]
    move(host, LUMIEST)
    wait(lambda: zone_uid(host) == LUMIEST and state(host)["sceneMode"] == "Zone", "host a Lumiest apres rechargement", timeout=240)
    time.sleep(3)
    found = on_map(host, [ctx["axe"], m])
    check("apres le plantage du client : sa hache et son objet sont a Lumiest (dernier checkpoint)",
          found.get(ctx["axe"]) == axe_pos and found.get(m) == mpos)


# --------------------------------------------------------------------------------------------------

def session_log_lines(t0):
    f = LOCALLOW / "ElinMP" / "Logs" / f"Session_{datetime.now():%Y%m%d}.log"
    out = []
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("@t", "") >= t0:
            out.append(json.dumps(d, ensure_ascii=False))
    return out


def scan_logs(t0):
    print("\nLogs :")
    logs = [("host Player.log", LOCALLOW / "Player.log"), ("client Player.log", SHOTS / "elin2-player.log")]
    for i, name in ((2, "elin3-player.log"), (3, "elin4-player.log")):
        if (SHOTS / name).exists() and (SHOTS / name).stat().st_mtime > time.time() - 7200:
            logs.append((f"client {i} Player.log", SHOTS / name))
    for name, path in logs:
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        # le jeu lui-meme, a sa fermeture (Heathen App.Application_quitting ferme Steam Input apres Steam) :
        # vu le 2026-10-01 et le 2026-10-04, apres la sauvegarde, pas le mod
        exc = [l for l in text.splitlines() if "Exception" in l and "Steamworks is not initialized" not in l]
        check(f"{name} : {len(exc)} exception(s)", not exc)
        for l in exc[:8]:
            print("       ", l[:220])
    problems = []
    for l in session_log_lines(t0):
        d = json.loads(l)
        if d.get("@l") in ("Warning", "Error", "Fatal") and "Dropping" not in d["@mt"]:
            problems.append(f'{d["@t"][11:19]} {d["@l"]} {d["@mt"][:110]}')
    for p in problems:
        print("       ", p)
    print(f"    (ElinTogether : {len(problems)} avertissement(s)/erreur(s), a lire ci-dessus)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--only", help="liste de scenarios, ex. s1,s2")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py")], check=True)

    live = emp.live_ports()
    ctx = {"host": next(h["port"] for h in live if h["role"] == "Host"),
           "client": next(h["port"] for h in live if h["role"] == "Client"), "t0": t0}

    steps = [s1, s2, s3, s4, s5, s6, s7, s8, s12, s13, s14, s15, s16, s17, s9, s10, s11]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__ or ''}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name in ("host", "client"):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', ctx[name])}")
                except Exception:  # noqa: BLE001
                    pass
            break

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
