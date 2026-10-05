"""Quetes a zone propre jouees a deux (PLAN_quetes_donjon_a_deux.md). T1 a T6, sens S1 : l'host prend la quete,
l'invite l'accompagne (etapes E1 a E4). T7 a T13, sens S2 : l'invite prend la quete, l'host l'accompagne et simule
la zone (etapes E5 et E6 ; "subjuguer", recolte et musique ; la defense reste a l'invite seul). Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie,
options « voyage independant » et « quetes par joueur » cochees).

    python _tools/mp_test.py
    python _tools/together_suite.py            # ou --only t1,t2   (~22 minutes en entier)

T1  l'host prend une quete "subjuguer" et entre : l'invite, reste en ville, voit la boite Oui/Non, clique Oui et
    arrive dans la zone ; memes monstres des deux cotes, pas de doublon, la quete absente de son journal
T2  l'invite tue le dernier monstre, l'host sort : les deux sont de retour en ville, une seule recompense, pour
    l'host, la zone est detruite (a la sauvegarde suivante de l'host, comme en solo)
T3  meme entree, l'invite ressort seul vers la ville avant la fin : il y arrive, la quete de l'host continue
T4  meme entree avec une quete de recolte : pas d'exception d'affichage chez l'invite, sortie a deux
T5  la boite : sans reponse au bout de 15 secondes elle se ferme et l'host lit « n'a pas repondu » ; Non, l'host
    lit « a refuse » ; dans les deux cas l'invite reste en ville

T7  l'invite prend une quete "subjuguer" et part : l'host, reste a cote de lui en ville, voit la boite Oui/Non au nom
    de l'invite et clique Oui ; les deux sont dans la zone, simulee par l'host : memes monstres, pas de doublon, la
    quete au journal de l'invite seulement
T8  l'invite tue le dernier monstre et sort : les deux sont de retour en ville, une seule recompense, aux pieds de
    l'invite, rien pour l'host, la zone est detruite
T9  la boite chez l'host : sans reponse au bout de 15 secondes, puis Non ; l'invite lit le refus et joue seul dans
    sa zone comme avant (il la simule), ressort, la quete est ratee pour lui seul
T10 l'host a dit Oui puis rentre seul en ville avant la fin : l'invite garde la zone et sa quete continue ; il la
    finit seul, ressort, recompense pour lui
T11 l'host sauvegarde dans la zone accompagnee : le fichier ecrit n'a ni evenement de quete ni numero de quete
    (la quete d'un autre n'entre pas dans la sauvegarde de l'host), et la zone en jeu n'a pas bouge ; une quete de
    defense prise par l'invite n'ouvre pas de boite (elle reste a lui seul)
T12 recolte prise par l'invite, l'host dit Oui : meme compteur des deux cotes ; l'host livre a la caisse (bouton
    « tout livrer »), puis l'invite : chaque livraison compte pour la quete de l'invite, rien n'est perdu sans
    credit ; l'invite sort : les recoltes non livrees des deux sacs sont fouillees, une recompense, pour l'invite
T13 musique prise par l'invite, l'host dit Oui : meme compteur des deux cotes, la zone de l'host lit la quete de
    l'invite ; l'invite sort, quete reglee chez lui seul. Le banc ne joue pas d'instrument : le score qui monte
    quand l'un ou l'autre joue n'est PAS verifie ici

Prendre la quete : les deux appels que fait le dialogue du jeu au choix « accepter » (DramaCustomSequence,
etape _questAccept_instance), pas le dialogue lui-meme : le banc ne sait pas derouler un LayerDrama.
Sortir de la zone : l'appel que fait Player.ExitBorder au bord de la carte, sans marcher jusqu'au bord ni passer
par la boite « quitter ? » du jeu. T12 livre par le bouton « tout livrer » de la vraie fenetre de la caisse, ouverte
par l'appel que fait la caisse quand on l'utilise ; deposer une recolte a la main sur la caisse n'est pas joue, et
les recoltes sont mises dans les sacs par l'host (marque 115). T7 a T13 ne jouent pas non plus le dialogue de remerciement du donneur chez
l'invite (le banc le ferme). T2 depend de T1, T8 de T7 (la zone ou les deux se trouvent).
"""
import argparse
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bot import choices, click  # noqa: E402
from mp_test import SAVES, log, shot, state  # noqa: E402
from quest_suite import fame, in_log, kept, offered, things_at_pc  # noqa: E402
from travel_suite import (HOME, RESULTS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually,  # noqa: E402
                          leases, log_has, marker, players, save_mtime, scan_logs, wait, zone_uid)

H, A = 27551, 27552

BOX = 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); return d == null ? "" : d.textDetail.text;'
CHARAS = 'string.Join(",", EClass._map.charas.Where(c => !c.isDead).Select(c => c.uid).OrderBy(u => u))'
TILE = 'var z = EClass.game.spatials.Find(%d); return EClass.world.region.elomap.GetZone(z.x, z.y).uid.ToString();' % HOME


def offer(kind):
    """L'host fait proposer une quete de ce type par un habitant, renvoie (numero de la quete, numero du donneur)."""
    r = ev(H, 'var c = EClass._map.charas.Find(x => !x.IsPCFaction && !x.IsPC && x.quest == null); '
              f'var q = Quest.Create(EClass.sources.quests.rows.Find(r => r.type == "{kind}").id, null, c); '
              'return q.uid + "|" + c.uid;')
    uid, giver = r.split("|")
    return int(uid), int(giver)


def host_enters(kind="QuestSubdue"):
    """L'host accepte la quete et entre dans sa zone, comme le fait le dialogue. Renvoie (quete, zone)."""
    uid, giver = offer(kind)
    dismiss_dialogs(H)
    ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {giver}); EClass.game.quests.Start(c.quest); '
          'var z = c.quest.CreateInstanceZone(c); EClass.pc.MoveZone(z, ZoneTransition.EnterState.Center); "ok"')

    def inside():
        dismiss_dialogs(H)
        return state(H).get("sceneMode") == "Zone" and ev(H, "EClass._zone.IsInstance.ToString()") == "True"

    wait(inside, "host dans la zone de la quete", timeout=120)
    return uid, int(ev(H, "EClass._zone.uid.ToString()"))


def box():
    """Le texte de la boite ouverte chez l'invite ("" s'il n'y en a pas)."""
    return ev(A, BOX)


def asked(host_name):
    return eventually(lambda: host_name in box() and len(choices(A)) == 2, timeout=30)


def follow(zuid):
    """L'invite clique Oui et arrive dans la zone de l'host."""
    click(A, choices(A)[0])
    both_joined(H, A, zuid)


def host_leaves():
    """L'host sort par le bord de la carte (ce que fait Player.ExitBorder), puis les deux se retrouvent en ville."""
    dismiss_dialogs(H)
    ev(H, 'EClass.pc.MoveZone(EClass._zone.ParentZone); "ok"')

    def home():
        dismiss_dialogs(H)
        return zone_uid(H) == HOME

    wait(home, "host de retour en ville", timeout=180)
    both_joined(H, A, HOME)
    time.sleep(3)
    dismiss_dialogs(H)
    dismiss_dialogs(A)


def free_next_to(port, uid):
    """Une case libre a cote de ce personnage, vue par ce jeu : "x,z"."""
    return ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); for (var dx = -1; dx <= 1; dx++) for (var dz = -1; dz <= 1; dz++) {{ '
                    'if (dx == 0 && dz == 0) continue; var p = new Point(c.pos.x + dx, c.pos.z + dz); '
                    'if (p.IsValid && p.IsInBounds && !p.IsBlocked && !p.HasChara) return p.x + "," + p.z; } return "";')


def t1(ctx):
    """l'host entre, l'invite voit la boite, clique Oui et arrive"""
    tile = ev(A, TILE)
    uid, zuid = host_enters()
    ctx.update(uid=uid, zuid=zuid)
    check("l'invite reste en ville et la garde", eventually(client_settled(A, HOME, True), timeout=30))
    seen = asked(ctx["host"])
    check(f"l'invite voit la boite Oui/Non au nom de l'host ({box()!r}, {choices(A)})", seen)
    check(f"la case de la ville sur la carte du monde de l'invite n'a pas bouge ({tile})", ev(A, TILE) == tile == str(HOME))
    follow(zuid)
    check("l'invite est dans la zone de l'host, pas en voyage seul", client_settled(A, zuid, False)())
    there = lambda p: ev(p, CHARAS).split(",")  # noqa: E731
    same = eventually(lambda: there(H) == there(A), timeout=20)
    h, a = there(H), there(A)
    check(f"memes personnages des deux cotes ({len(h)} chez l'host, {len(a)} chez l'invite)", same)
    check("pas de doublon", len(set(h)) == len(h) and len(set(a)) == len(a))
    n = int(ev(H, 'EClass._zone.events.GetEvent<ZoneEventSubdue>().enemies.Count.ToString()'))
    check(f"les monstres de la quete ne sont apparus qu'une fois ({n} chez l'host)",
          n > 0 and ev(A, 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); return e == null ? "-1" : e.enemies.Count.ToString();') == str(n))
    check("la quete est au journal de l'host, pas de l'invite", in_log(H, uid) and not in_log(A, uid))


def t2(ctx):
    """l'invite tue le dernier monstre, l'host sort : retour a deux, une recompense, pour l'host"""
    uid, zuid = ctx.get("uid"), ctx.get("zuid")
    if not check("les deux sont dans la zone de la quete (T1)", zuid is not None and zone_uid(H) == zuid and zone_uid(A) == zuid):
        return
    before = {"fh": fame(H), "fa": fame(A)}
    last = int(ev(H, 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); '
                     'var alive = e.enemies.Select(id => EClass._map.FindChara(id)).Where(c => c != null && !c.isDead).ToList(); '
                     'foreach (var c in alive.Skip(1)) c.Die(); var m = alive[0]; m.hp = 1; m.AddCondition<ConParalyze>(5000, true); '
                     'return m.uid.ToString();'))
    eventually(lambda: ev(A, f'(EClass._map.charas.Find(x => x.uid == {last}) != null).ToString()') == "True", timeout=10)
    spot = free_next_to(A, last)
    if check(f"une case libre a cote du dernier monstre ({spot or 'non'})", bool(spot)):
        x, z = spot.split(",")
        ev(A, f'EClass.pc.Teleport(new Point({x}, {z}), true, true); "ok"')
        time.sleep(3)
    dead = lambda: ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {last}); return (m == null || m.isDead).ToString();') == "True"  # noqa: E731
    for _ in range(40):
        if dead():
            break
        ev(A, f'var m = EClass._map.charas.Find(x => x.uid == {last}); if (m != null && !m.isDead) ACT.Melee.Perform(EClass.pc, m, m.pos); "ok"')
        time.sleep(1.5)
    check("l'invite tue le dernier monstre", dead())
    check("la quete est reussie chez l'host", eventually(lambda: ev(H, "EClass._zone.instance.status.ToString()") == "Success", timeout=15))
    host_leaves()
    check("les deux sont de retour en ville, ensemble", zone_uid(H) == HOME and client_settled(A, HOME, False)())
    check("la quete est rendue : sortie du journal de l'host", eventually(lambda: not in_log(H, uid), timeout=15))
    check(f"renommee pour l'host ({before['fh']} -> {fame(H)})", eventually(lambda: fame(H) > before["fh"], timeout=10))
    time.sleep(3)
    check(f"rien pour l'invite : ni quete ni renommee ({before['fa']} -> {fame(A)})", fame(A) == before["fa"] and not in_log(A, uid))
    ev(H, 'EClass.game.Save(); "ok"')
    check("la zone de la quete n'existe plus chez l'host apres sa sauvegarde",
          ev(H, f'(EClass.game.spatials.Find({zuid}) == null).ToString()') == "True")


def t3(ctx):
    """l'invite ressort seul vers la ville avant la fin"""
    uid, zuid = host_enters()
    if not check("l'invite voit la boite", asked(ctx["host"])):
        host_leaves()
        return
    follow(zuid)
    before = {"fa": fame(A), "fh": fame(H)}
    # ce que fait Player.ExitBorder au bord de la carte
    ev(A, 'EClass.pc.MoveZone(EClass._zone.ParentZone); "ok"')
    check("l'invite arrive seul en ville", eventually(client_settled(A, HOME, True), timeout=120))
    time.sleep(4)
    dismiss_dialogs(A)
    check("la quete de l'host continue : il est dans la zone, la quete au journal, en cours",
          zone_uid(H) == zuid and in_log(H, uid) and ev(H, "EClass._zone.instance.status.ToString()") == "Running")
    check("l'host est seul dans la zone", eventually(lambda: len(state(H).get("players", [])) == 1, timeout=15))
    check(f"rien de regle chez l'invite ({before['fa']} -> {fame(A)}), ni chez l'host", fame(A) == before["fa"] and fame(H) == before["fh"]
          and not in_log(A, uid))
    check("pas de nouvelle boite chez l'invite", box() == "")
    host_leaves()
    check("l'host sort a son tour (quete ratee pour lui seul), les deux se retrouvent en ville",
          eventually(lambda: not in_log(H, uid), timeout=15) and fame(A) == before["fa"])


def t4(ctx):
    """quete de recolte : rien ne casse a l'affichage chez l'invite"""
    uid, zuid = host_enters("QuestHarvest")
    if not check("l'invite voit la boite", asked(ctx["host"])):
        host_leaves()
        return
    follow(zuid)
    text = ev(A, 'var e = EClass._zone.events.GetEvent<ZoneEventHarvest>(); return e == null ? "pas d evenement" : "[" + e.TextWidgetDate + "]";')
    check(f"l'invite n'a pas la quete : la ligne de la recolte est vide chez lui ({text})", text == "[]" and not in_log(A, uid))
    check("l'host, lui, lit son compteur de recolte",
          ev(H, 'EClass._zone.events.GetEvent<ZoneEventHarvest>().TextWidgetDate.Length.ToString()') != "0")
    ev(A, 'WidgetDate.Refresh(); "ok"')
    time.sleep(3)
    before = fame(A)
    host_leaves()
    check("sortie a deux, la quete n'est plus au journal de l'host", eventually(lambda: not in_log(H, uid), timeout=15))
    check("rien de regle chez l'invite", fame(A) == before and not in_log(A, uid))


def t5(ctx):
    """la boite : sans reponse, puis Non"""
    for key, button in (("emp_quest_follow_no_answer", None), ("emp_quest_follow_declined", 1)):
        uid, zuid = host_enters()
        line = ev(A, f'string.Format("{key}".lang(), EClass.pc.Name)')
        if check("l'invite voit la boite", asked(ctx["host"])):
            if button is None:
                check("sans reponse, la boite se ferme toute seule (15 secondes)", eventually(lambda: box() == "", timeout=25))
            else:
                click(A, choices(A)[button])
            check(f"l'host lit « {line} »", eventually(lambda: log_has(H, line), timeout=10))
        check("l'invite est reste en ville", client_settled(A, HOME, True)() and box() == "")
        # ce que l'invite fait en ville pendant ce temps ne doit pas etre perdu au retour de l'host (la ville lui est reprise)
        seau, pos = marker(A)
        host_leaves()
        check(cond=eventually(lambda: ev(H, f'(EClass._map.things.Find(t => t.uid == {seau}) != null).ToString()') == "True", timeout=15),
              label=f"le seau pose en ville par l'invite pendant l'absence de l'host y est encore chez l'host ({pos})")
        check("l'host ressort, les deux se retrouvent en ville", eventually(lambda: not in_log(H, uid), timeout=15))


def t6(ctx):
    """recolte : l'invite qui ressort seul avec des recoltes non livrees est fouille (la moitie reprise, 1 de karma), comme en solo
    Ce que le banc ne joue pas comme un joueur : les recoltes « de la quete » sont mises dans son sac par l'host (marque 115)"""
    uid, zuid = host_enters("QuestHarvest")
    if not check("l'invite voit la boite", asked(ctx["host"])):
        host_leaves()
        return
    follow(zuid)
    a = state(A)["pc"]["uid"]
    ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {a}); for (var i = 0; i < 30; i++) {{ var t = ThingGen.Create("bucket"); '
          't.SetBool(115, true); c.AddThing(t, false); } "ok"')
    buckets = lambda: int(ev(A, 'EClass.pc.things.Count(t => t.id == "bucket").ToString()'))  # noqa: E731
    check(cond=eventually(lambda: buckets() >= 30, timeout=15), label=f"l'invite a 30 recoltes non livrees dans son sac ({buckets()})")
    n0, k0, kh = buckets(), int(ev(A, "EClass.player.karma.ToString()")), int(ev(H, "EClass.player.karma.ToString()"))
    ev(A, 'EClass.pc.MoveZone(EClass._zone.ParentZone); "ok"')
    check("l'invite arrive seul en ville", eventually(client_settled(A, HOME, True), timeout=120))
    time.sleep(4)
    dismiss_dialogs(A)
    check(f"une partie de ses recoltes a ete reprise, pas tout ({n0} -> {buckets()})", n0 - 30 < buckets() < n0)
    k1 = int(ev(A, "EClass.player.karma.ToString()"))
    check(f"il perd 1 de karma ({k0} -> {k1}), pas l'host ({kh} -> {ev(H, 'EClass.player.karma.ToString()')})",
          k1 == k0 - 1 and int(ev(H, "EClass.player.karma.ToString()")) == kh)
    host_leaves()
    ev(A, 'foreach (var t in EClass.pc.things.Where(t => t.id == "bucket").ToList()) t.Destroy(); "ok"')


# --- sens S2 : l'invite prend la quete, l'host l'accompagne

STATUS = "EClass._zone.instance.status.ToString()"
LEAVE = 'EClass.pc.MoveZone(EClass._zone.ParentZone); "ok"'
QUEST_ZONES = 'EClass.game.spatials.map.Values.Count(z => z is Zone && ((Zone)z).IsInstance).ToString()'


def guest_takes(kind="QuestSubdue"):
    """L'invite accepte la quete qu'un habitant propose (premier appel du dialogue). Renvoie (quete, donneur)."""
    uid, giver = offer(kind)
    wait(lambda: offered(A, uid), "l'invite voit la quete proposee", timeout=20)
    dismiss_dialogs(A)
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {giver}); EClass.game.quests.Start(c.quest); "ok"')
    # le joueur lit une ligne de dialogue entre les deux appels : l'host a note la quete avant le depart
    wait(lambda: in_log(A, uid), "la quete est au journal de l'invite", timeout=20)
    return uid, giver


def guest_departs(uid, giver):
    """L'invite part pour la zone de sa quete (second appel du dialogue)."""
    dismiss_dialogs(A)
    dismiss_dialogs(H)
    ev(A, f'var q = EClass.game.quests.list.Find(x => x.uid == {uid}); var c = EClass._map.charas.Find(x => x.uid == {giver}); '
          'var z = q.CreateInstanceZone(c); EClass.pc.MoveZone(z, ZoneTransition.EnterState.Center); "ok"')


def host_box():
    return ev(H, BOX)


def host_asked(guest_name):
    return eventually(lambda: guest_name in host_box() and len(choices(H)) == 2, timeout=30)


def host_comes():
    """L'host clique Oui : il entre dans la zone de la quete de l'invite, qui l'y suit. Renvoie la zone."""
    click(H, choices(H)[0])

    def inside():
        dismiss_dialogs(H)
        return state(H).get("sceneMode") == "Zone" and ev(H, "EClass._zone.IsInstance.ToString()") == "True"

    wait(inside, "host dans la zone de la quete de l'invite", timeout=120)
    zuid = int(ev(H, "EClass._zone.uid.ToString()"))
    both_joined(H, A, zuid)
    return zuid


def together(ctx, kind="QuestSubdue"):
    """L'invite prend une quete, l'host dit Oui : renvoie (quete, zone), ou None si la boite ne s'ouvre pas."""
    uid, giver = guest_takes(kind)
    guest_departs(uid, giver)
    if not check("l'host voit la boite", host_asked(ctx["guest"])):
        return None
    return uid, host_comes()


def guest_alone_inside():
    def inside():
        dismiss_dialogs(A)
        return (state(A).get("sceneMode") == "Zone" and ev(A, "EClass._zone.IsInstance.ToString()") == "True"
                and bool(state(A).get("awayZone")))

    wait(inside, "l'invite seul dans la zone de sa quete", timeout=120)
    time.sleep(4)
    return int(ev(A, "EClass._zone.uid.ToString()"))


def back_home():
    """Les deux se retrouvent en ville, ensemble."""
    def home():
        dismiss_dialogs(H)
        return zone_uid(H) == HOME

    wait(home, "host de retour en ville", timeout=180)
    both_joined(H, A, HOME)
    time.sleep(4)
    dismiss_dialogs(H)
    dismiss_dialogs(A)


def t7(ctx):
    """l'invite part en quete, l'host voit la boite, clique Oui : les deux dans la zone simulee par l'host"""
    a = ctx["a"]
    ctx["h_things"] = things_at_pc(H)
    uid, giver = guest_takes()
    check("la quete est au journal de l'invite, l'host la garde pour lui, sans l'avoir au sien",
          eventually(lambda: str(uid) in kept(a).split(","), timeout=10) and not in_log(H, uid))
    known = int(ev(A, QUEST_ZONES))
    guest_departs(uid, giver)
    seen = host_asked(ctx["guest"])
    check(f"l'host voit la boite Oui/Non au nom de l'invite ({host_box()!r}, {choices(H)})", seen)
    line = ev(H, 'string.Format("emp_quest_follow_asked".lang(), EClass.pc.Name)')
    check(f"l'invite lit « {line} »", eventually(lambda: log_has(A, line), timeout=10))
    check("pendant la question l'invite est encore en ville avec l'host, pas en voyage seul", client_settled(A, HOME, False)())
    if not seen:
        guest_alone_inside()
        ev(A, LEAVE)
        back_home()
        return
    zuid = host_comes()
    ctx.update(uid2=uid, zuid2=zuid)
    check("l'invite est dans la zone de l'host, pas en voyage seul", client_settled(A, zuid, False)())
    check(f"l'host n'a prete aucune zone a l'invite ({leases(H)})", leases(H) == 0)
    there = lambda p: ev(p, CHARAS).split(",")  # noqa: E731
    same = eventually(lambda: there(H) == there(A), timeout=20)
    h, g = there(H), there(A)
    check(f"memes personnages des deux cotes ({len(h)} chez l'host, {len(g)} chez l'invite)", same)
    check("pas de doublon", len(set(h)) == len(h) and len(set(g)) == len(g))
    n = int(ev(H, 'EClass._zone.events.GetEvent<ZoneEventSubdue>().enemies.Count.ToString()'))
    seen_by_guest = 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); return e == null ? "-1" : e.enemies.Count.ToString();'
    check(f"les monstres de la quete ne sont apparus qu'une fois ({n} chez l'host), et l'invite en connait le compte ({ev(A, seen_by_guest)})",
          n > 0 and eventually(lambda: ev(A, seen_by_guest) == str(n), timeout=15))
    check("la quete est au journal de l'invite, pas de l'host", in_log(A, uid) and not in_log(H, uid))
    check("chez l'invite la zone est une zone de quete, la sienne (meme numero que chez l'host)",
          ev(A, '(EClass._zone.instance as ZoneInstanceRandomQuest).uidQuest.ToString()') == str(uid))
    reads = 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); return (e != null && e.quest != null && e.quest.uid == %d).ToString();' % uid
    check("chez l'host, la zone lit la quete de l'invite", ev(H, reads) == "True")
    check(f"l'invite ne connait qu'une zone de quete de plus, celle de l'host, pas celle qu'il s'etait faite ({known} -> {ev(A, QUEST_ZONES)})",
          int(ev(A, QUEST_ZONES)) == known + 1)


def t8(ctx):
    """l'invite tue le dernier monstre et sort : retour a deux, une recompense, pour l'invite"""
    a, uid, zuid = ctx["a"], ctx.get("uid2"), ctx.get("zuid2")
    if not check("les deux sont dans la zone de la quete de l'invite (T7)", zuid is not None and zone_uid(H) == zuid and zone_uid(A) == zuid):
        return
    before = {"fh": fame(H), "fa": fame(A), "bag": ev(H, 'EClass.pc.things.Sum(t => t.Num).ToString()')}
    last = int(ev(H, 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); '
                     'var alive = e.enemies.Select(id => EClass._map.FindChara(id)).Where(c => c != null && !c.isDead).ToList(); '
                     'foreach (var c in alive.Skip(1)) c.Die(); var m = alive[0]; m.hp = 1; m.AddCondition<ConParalyze>(5000, true); '
                     'return m.uid.ToString();'))
    eventually(lambda: ev(A, f'(EClass._map.charas.Find(x => x.uid == {last}) != null).ToString()') == "True", timeout=10)
    spot = free_next_to(A, last)
    if check(f"une case libre a cote du dernier monstre ({spot or 'non'})", bool(spot)):
        x, z = spot.split(",")
        ev(A, f'EClass.pc.Teleport(new Point({x}, {z}), true, true); "ok"')
        time.sleep(3)
    dead = lambda: ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {last}); return (m == null || m.isDead).ToString();') == "True"  # noqa: E731
    for _ in range(40):
        if dead():
            break
        ev(A, f'var m = EClass._map.charas.Find(x => x.uid == {last}); if (m != null && !m.isDead) ACT.Melee.Perform(EClass.pc, m, m.pos); "ok"')
        time.sleep(1.5)
    check("l'invite tue le dernier monstre", dead())
    check("la quete est reussie dans la zone de l'host", eventually(lambda: ev(H, STATUS) == "Success", timeout=15))
    ev(A, LEAVE)
    back_home()
    check("l'invite sort : les deux sont de retour en ville, ensemble", zone_uid(H) == HOME and client_settled(A, HOME, False)())
    check("la quete est rendue : sortie du journal de l'invite", eventually(lambda: not in_log(A, uid), timeout=25))
    check("l'host ne la garde plus", eventually(lambda: str(uid) not in kept(a).split(","), timeout=10))
    check(f"renommee pour l'invite ({before['fa']} -> {fame(A)})", eventually(lambda: fame(A) > before["fa"], timeout=10))
    check("recompense aux pieds de l'invite", eventually(lambda: things_at_pc(H, a) > 0, timeout=10))
    time.sleep(5)
    dismiss_dialogs(A)
    won = fame(A)
    # les deux reviennent sur la meme case (celle du preneur) : « a ses pieds » ne distingue plus rien, on compte son sac
    check(f"rien pour l'host : ni renommee ({before['fh']} -> {fame(H)}), ni quete, ni rien de plus dans son sac ({before['bag']})",
          fame(H) == before["fh"] and not in_log(H, uid) and ev(H, 'EClass.pc.things.Sum(t => t.Num).ToString()') == before["bag"])
    time.sleep(5)
    check(f"une seule recompense : la renommee de l'invite ne monte pas une seconde fois ({won} -> {fame(A)})", fame(A) == won)
    ev(H, 'EClass.game.Save(); "ok"')
    check("la zone de la quete n'existe plus chez l'host apres sa sauvegarde",
          ev(H, f'(EClass.game.spatials.Find({zuid}) == null).ToString()') == "True")


def t9(ctx):
    """la boite chez l'host : sans reponse, puis Non ; l'invite joue seul comme avant"""
    a = ctx["a"]
    for key, button in (("emp_quest_follow_no_answer", None), ("emp_quest_follow_declined", 1)):
        uid, giver = guest_takes()
        line = ev(H, f'string.Format("{key}".lang(), EClass.pc.Name)')
        guest_departs(uid, giver)
        if check("l'host voit la boite", host_asked(ctx["guest"])):
            if button is None:
                check("sans reponse, la boite se ferme toute seule (15 secondes)", eventually(lambda: host_box() == "", timeout=25))
            else:
                click(H, choices(H)[button])
            check(f"l'invite lit « {line} »", eventually(lambda: log_has(A, line), timeout=15))
        zuid = guest_alone_inside()
        check("l'invite est seul dans la zone de sa quete et la simule, l'host est reste en ville",
              client_settled(A, zuid, True)() and zone_uid(H) == HOME and host_box() == "")
        check("la zone suit la quete (des monstres a subjuguer), l'host la lui garde",
              ev(A, 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); return (e != null && e.quest != null && e.enemies.Count > 0).ToString();') == "True"
              and str(uid) in kept(a).split(",") and not in_log(H, uid))
        before = {"fa": fame(A), "fh": fame(H)}
        ev(A, LEAVE)
        back_home()
        check("l'invite ressort sans rien tuer : quete ratee, sortie de son journal, l'host ne la garde plus",
              eventually(lambda: not in_log(A, uid), timeout=20) and eventually(lambda: str(uid) not in kept(a).split(","), timeout=10))
        check(f"pour lui seul ({before['fa']} -> {fame(A)}, host {before['fh']} -> {fame(H)})",
              fame(A) <= before["fa"] and fame(H) == before["fh"])
        check("la zone n'existe plus chez l'host", ev(H, f'(EClass.game.spatials.Find({zuid}) == null).ToString()') == "True")


def t10(ctx):
    """l'host a dit Oui puis rentre seul avant la fin : la quete de l'invite continue, il la finit seul
    Ce que le banc ne joue pas comme un joueur : les monstres sont tues d'un appel, pas au combat"""
    a = ctx["a"]
    r = together(ctx)
    if r is None:
        guest_alone_inside()
        ev(A, LEAVE)
        back_home()
        return
    uid, zuid = r
    before = {"fa": fame(A), "fh": fame(H)}
    n = int(ev(H, 'EClass._zone.events.GetEvent<ZoneEventSubdue>().enemies.Count.ToString()'))
    dismiss_dialogs(H)
    ev(H, LEAVE)

    def host_home():
        dismiss_dialogs(H)
        return zone_uid(H) == HOME

    wait(host_home, "host de retour en ville, seul", timeout=180)
    check("l'invite reste dans la zone et la garde", eventually(client_settled(A, zuid, True), timeout=60))
    time.sleep(4)
    dismiss_dialogs(A)
    check("l'host est seul en ville", eventually(lambda: players(H) == 1, timeout=15))
    check("la quete de l'invite continue : au journal, en cours, gardee par l'host, la zone existe toujours chez lui",
          in_log(A, uid) and ev(A, STATUS) == "Running" and str(uid) in kept(a).split(",")
          and ev(H, f'(EClass.game.spatials.Find({zuid}) != null).ToString()') == "True")
    alive = ('var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); return e == null ? "-1" : '
             'e.enemies.Select(id => EClass._map.FindChara(id)).Count(c => c != null && !c.isDead).ToString();')
    check(f"les monstres de la quete sont toujours la chez l'invite ({ev(A, alive)} sur {n})", ev(A, alive) == str(n))
    check(f"rien de regle ({before['fa']} -> {fame(A)}, host {before['fh']} -> {fame(H)})", fame(A) == before["fa"] and fame(H) == before["fh"])
    ev(A, 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); foreach (var id in e.enemies.ToList()) '
          '{ var c = EClass._map.FindChara(id); if (c != null) c.Die(); } e.CheckClear(); "ok"')
    check("l'invite finit seul : la quete est reussie", eventually(lambda: ev(A, STATUS) == "Success", timeout=10))
    ev(A, LEAVE)
    back_home()
    check("il ressort et retrouve l'host : la quete est rendue", eventually(lambda: not in_log(A, uid), timeout=25))
    check(f"renommee pour l'invite ({before['fa']} -> {fame(A)}), pas pour l'host",
          eventually(lambda: fame(A) > before["fa"], timeout=10) and fame(H) == before["fh"])
    check("l'host ne la garde plus et la zone n'existe plus",
          eventually(lambda: str(uid) not in kept(a).split(","), timeout=10)
          and ev(H, f'(EClass.game.spatials.Find({zuid}) == null).ToString()') == "True")


def t11(ctx):
    """l'host sauvegarde dans la zone accompagnee : rien de la quete de l'invite dans le fichier ; pas de boite pour une defense
    Ce que le banc ne joue pas comme un joueur : la sauvegarde est un appel (Game.Save), pas le menu"""
    a = ctx["a"]
    r = together(ctx)
    if r is None:
        guest_alone_inside()
        ev(A, LEAVE)
        back_home()
        return
    uid, zuid = r
    live = ('var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); var i = EClass._zone.instance as ZoneInstanceRandomQuest; '
            'return (e != null && e.quest != null) + "|" + i.uidQuest;')
    check("avant la sauvegarde, la zone de l'host lit la quete de l'invite", ev(H, live) == f"True|{uid}")
    before = save_mtime()
    ev(H, 'EClass.game.Save(); "ok"')
    check("l'host a sauvegarde", eventually(lambda: save_mtime() > before, timeout=30))
    text = (SAVES / "world_lab" / "game.txt").read_text(encoding="utf-8", errors="replace")
    if check("la sauvegarde est lisible (pas compressee) et contient la zone de la quete", text.lstrip().startswith("{") and "ZoneInstanceSubdue" in text):
        check("le fichier n'a pas d'evenement de quete", "ZoneEventSubdue" not in text)
        check(f"ni le numero de la quete de l'invite ({uid})", re.search(r'"uidQuest":\s*%d\b' % uid, text) is None)
    check("apres la sauvegarde, la zone en jeu n'a pas bouge : elle lit toujours la quete, rien au journal de l'host",
          ev(H, live) == f"True|{uid}" and not in_log(H, uid) and in_log(A, uid))
    fa = fame(A)
    ev(A, LEAVE)
    back_home()
    check("l'invite sort sans rien tuer : quete ratee pour lui, sortie de son journal, l'host ne la garde plus",
          eventually(lambda: not in_log(A, uid), timeout=25) and eventually(lambda: str(uid) not in kept(a).split(","), timeout=10)
          and fame(A) <= fa)

    # une defense reste a l'invite seul : pas de boite, il part tout de suite
    uid, giver = guest_takes("QuestDefenseGame")
    guest_departs(uid, giver)
    zuid = guest_alone_inside()
    check("quete de defense de l'invite : pas de boite chez l'host, l'invite est seul dans sa zone",
          host_box() == "" and zone_uid(H) == HOME and client_settled(A, zuid, True)())
    ev(A, LEAVE)
    back_home()
    check("il ressort, la quete est reglee chez lui", eventually(lambda: not in_log(A, uid), timeout=25))



DELIVER = ('var chest = EClass._map.things.Find(t => t.trait is TraitFarmChest); if (chest == null) return "pas de caisse"; '
           'var l = LayerDragGrid.CreateDeliver(InvOwnerDeliver.Mode.Crop, chest); l.buttonDeliver.onClick.Invoke(); return "ok";')


def give(who, thing, num):
    """L'host met dans le sac du personnage `who` une pile marquee « recolte de la quete ». Renvoie son poids."""
    return int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {who}); var t = ThingGen.Create("{thing}"); t.SetNum({num}); '
                     't.SetBool(115, true); var w = t.SelfWeight * t.Num; c.AddThing(t, false); return w.ToString();'))


def has(port, thing):
    return int(ev(port, f'EClass.pc.things.List(t => t.id == "{thing}").Sum(t => t.Num).ToString()'))


def t12(ctx):
    """recolte prise par l'invite, a deux : chaque livraison compte pour lui, fouille des deux sacs, une recompense
    Ce que le banc ne joue pas comme un joueur : les recoltes sont mises dans les sacs par l'host ; livraison par le bouton « tout livrer »"""
    a, h = ctx["a"], state(H)["pc"]["uid"]
    r = together(ctx, "QuestHarvest")
    if r is None:
        guest_alone_inside()
        ev(A, LEAVE)
        back_home()
        return
    uid, zuid = r
    text = 'var e = EClass._zone.events.GetEvent<ZoneEventHarvest>(); return e == null ? "pas d evenement" : e.TextWidgetDate;'
    w_guest = lambda: int(ev(A, f'((QuestHarvest)EClass.game.quests.list.Find(q => q.uid == {uid})).weightDelivered.ToString()'))  # noqa: E731
    w_host = lambda: int(ev(H, 'EClass._zone.events.GetEvent<ZoneEventHarvest>().questHarvest.weightDelivered.ToString()'))  # noqa: E731
    check(f"le compteur de la recolte s'affiche des deux cotes, le meme (host {ev(H, text)!r}, invite {ev(A, text)!r})",
          len(ev(H, text)) > 0 and eventually(lambda: ev(H, text) == ev(A, text), timeout=10))
    check("la quete est au journal de l'invite, pas de l'host", in_log(A, uid) and not in_log(H, uid))

    crop = ev(H, 'EClass.sources.things.rows.First(r => r.category == "vegi").id')
    unit = int(ev(H, f'ThingGen.Create("{crop}").SelfWeight.ToString()'))
    dest = int(ev(A, f'((QuestHarvest)EClass.game.quests.list.Find(q => q.uid == {uid})).destWeight.ToString()'))
    if not check(f"une recolte a livrer ({crop}, {unit} l'unite, {dest} demandes)", unit > 0 and dest > 0):
        ev(A, LEAVE)
        back_home()
        return

    # l'host livre le premier : il n'a pas la quete a son journal
    wh = give(h, crop, 2)
    done = ev(H, DELIVER)
    check(f"l'host livre a la caisse ({done}) : ses recoltes quittent son sac", done == "ok" and eventually(lambda: has(H, crop) == 0, timeout=10))
    check(f"ce que l'host livre compte pour la quete de l'invite ({wh} attendus, {w_guest()} chez l'invite)",
          eventually(lambda: w_guest() == wh, timeout=15))
    check(f"et l'host lit le meme poids ({w_host()})", eventually(lambda: w_host() == wh, timeout=15))

    # l'invite livre de quoi reussir la quete
    # (le poids d'une recolte creee varie : le double, pour depasser la demande a coup sur)
    wa = give(a, crop, 2 * (dest // unit) + 2)
    while wh + wa < dest:
        wa += give(a, crop, 2 * (dest // unit) + 2)
    eventually(lambda: has(A, crop) > 0, timeout=10)  # la pile mise par l'host doit etre arrivee dans le jeu de l'invite
    done = ev(A, DELIVER)
    check(f"l'invite livre a la caisse ({done}) : ses recoltes quittent son sac, chez lui et chez l'host",
          done == "ok" and eventually(lambda: has(A, crop) == 0, timeout=10)
          and eventually(lambda: ev(H, f'EClass._map.charas.Find(x => x.uid == {a}).things.List(t => t.id == "{crop}").Count.ToString()') == "0", timeout=10))
    check(f"ce que l'invite livre compte, une fois ({wh + wa} attendus, {w_guest()} chez l'invite)",
          eventually(lambda: w_guest() == wh + wa, timeout=15))
    check(f"l'host lit le meme poids ({w_host()}) et le meme compteur", eventually(lambda: w_host() == wh + wa, timeout=15)
          and eventually(lambda: ev(H, text) == ev(A, text), timeout=10))
    time.sleep(3)
    check(f"le poids ne bouge plus tout seul (pas de double compte : {w_guest()})", w_guest() == wh + wa)

    # des recoltes non livrees dans les deux sacs, puis l'invite sort
    ev(H, f'foreach (var c in new[] {{ EClass.pc, EClass._map.charas.Find(x => x.uid == {a}) }}) for (var i = 0; i < 30; i++) {{ '
          'var t = ThingGen.Create("bucket"); t.SetBool(115, true); c.AddThing(t, false); } "ok"')
    check("30 recoltes non livrees dans chaque sac", eventually(lambda: has(A, "bucket") >= 30 and has(H, "bucket") >= 30, timeout=15))
    n = {"a": has(A, "bucket"), "h": has(H, "bucket")}
    before = {"fa": fame(A), "fh": fame(H), "kh": int(ev(H, "EClass.player.karma.ToString()"))}
    ev(A, LEAVE)
    back_home()
    check(f"une partie des recoltes non livrees de l'invite a ete reprise, pas tout ({n['a']} -> {has(A, 'bucket')})",
          eventually(lambda: n["a"] - 30 < has(A, "bucket") < n["a"], timeout=15))
    check(f"celles de l'host aussi ({n['h']} -> {has(H, 'bucket')})", n["h"] - 30 < has(H, "bucket") < n["h"])
    check("la quete est rendue : sortie du journal de l'invite, l'host ne la garde plus",
          eventually(lambda: not in_log(A, uid), timeout=25) and eventually(lambda: str(uid) not in kept(a).split(","), timeout=10))
    check(f"reussie : renommee pour l'invite ({before['fa']} -> {fame(A)}), recompense a ses pieds",
          eventually(lambda: fame(A) > before["fa"], timeout=10) and eventually(lambda: things_at_pc(H, a) > 0, timeout=10))
    time.sleep(5)
    dismiss_dialogs(A)
    won = fame(A)
    check(f"rien pour l'host : ni renommee ({before['fh']} -> {fame(H)}), ni karma ({before['kh']} -> {ev(H, 'EClass.player.karma.ToString()')}), ni quete",
          fame(H) == before["fh"] and int(ev(H, "EClass.player.karma.ToString()")) == before["kh"] and not in_log(H, uid))
    time.sleep(5)
    check(f"une seule recompense ({won} -> {fame(A)})", fame(A) == won)
    for port in (H, A):
        ev(port, 'foreach (var t in EClass.pc.things.Where(t => t.id == "bucket").ToList()) t.Destroy(); "ok"')


def t13(ctx):
    """musique prise par l'invite, a deux : meme compteur, la zone de l'host lit la quete de l'invite, sortie reglee chez lui
    Ce que le banc ne joue pas : personne ne joue d'instrument, le score qui monte n'est pas verifie"""
    a = ctx["a"]
    r = together(ctx, "QuestMusic")
    if r is None:
        guest_alone_inside()
        ev(A, LEAVE)
        back_home()
        return
    uid, zuid = r
    text = 'var e = EClass._zone.events.GetEvent<ZoneEventMusic>(); return e == null ? "pas d evenement" : e.TextWidgetDate;'
    check(f"le compteur du concert s'affiche des deux cotes, le meme (host {ev(H, text)!r}, invite {ev(A, text)!r})",
          len(ev(H, text)) > 0 and eventually(lambda: ev(H, text) == ev(A, text), timeout=10))
    check("la zone de l'host lit la quete de l'invite, qui n'est pas a son journal",
          ev(H, f'var e = EClass._zone.events.GetEvent<ZoneEventMusic>(); return (e.questMusic != null && e.questMusic.uid == {uid}).ToString();') == "True"
          and in_log(A, uid) and not in_log(H, uid))
    there = lambda p: ev(p, CHARAS).split(",")  # noqa: E731
    check(f"meme public des deux cotes ({len(there(H))} chez l'host)", eventually(lambda: there(H) == there(A), timeout=20))
    before = {"fa": fame(A), "fh": fame(H)}
    ev(A, LEAVE)
    back_home()
    check("l'invite sort sans avoir joue : quete reglee (ratee) chez lui, l'host ne la garde plus",
          eventually(lambda: not in_log(A, uid), timeout=25) and eventually(lambda: str(uid) not in kept(a).split(","), timeout=10))
    check(f"rien pour l'host ({before['fh']} -> {fame(H)})", fame(H) == before["fh"] and fame(A) <= before["fa"])


TESTS = {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6, "t7": t7, "t8": t8, "t9": t9, "t10": t10, "t11": t11,
         "t12": t12, "t13": t13}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="ex. t1,t2")
    only = [x for x in ap.parse_args().only.lower().split(",") if x]
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {}
    for name, test in TESTS.items():
        if only and name not in only:
            continue
        log(f"--- {name.upper()} : {test.__doc__}")
        try:
            if "host" not in ctx:
                ctx["host"] = ev(H, "EClass.pc.Name")
                ctx["guest"] = ev(A, "EClass.pc.Name")
                ctx["a"] = state(A)["pc"]["uid"]
                both_joined(H, A, HOME)
            test(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{name} interrompu : {type(ex).__name__}: {ex}", False)
            for who, port in (("host", H), ("A", A)):
                try:
                    print(f"    capture {who} : {shot(f'fail-together-{name}-{who}', port)}")
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
