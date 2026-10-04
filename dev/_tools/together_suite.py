"""Quetes a zone propre jouees a deux, sens S1 : l'host prend la quete, l'invite l'accompagne
(PLAN_quetes_donjon_a_deux.md, etapes E1 a E4). Test court, sur des instances deja lancees (host + 1 client,
tous les deux a la Prairie, options « voyage independant » et « quetes par joueur » cochees).

    python _tools/mp_test.py
    python _tools/together_suite.py            # ou --only t1,t2   (~8 minutes en entier)

T1  l'host prend une quete "subjuguer" et entre : l'invite, reste en ville, voit la boite Oui/Non, clique Oui et
    arrive dans la zone ; memes monstres des deux cotes, pas de doublon, la quete absente de son journal
T2  l'invite tue le dernier monstre, l'host sort : les deux sont de retour en ville, une seule recompense, pour
    l'host, la zone est detruite (a la sauvegarde suivante de l'host, comme en solo)
T3  meme entree, l'invite ressort seul vers la ville avant la fin : il y arrive, la quete de l'host continue
T4  meme entree avec une quete de recolte : pas d'exception d'affichage chez l'invite, sortie a deux
T5  la boite : sans reponse au bout de 15 secondes elle se ferme et l'host lit « n'a pas repondu » ; Non, l'host
    lit « a refuse » ; dans les deux cas l'invite reste en ville

Prendre la quete : les deux appels que fait le dialogue du jeu au choix « accepter » (DramaCustomSequence,
etape _questAccept_instance), pas le dialogue lui-meme : le banc ne sait pas derouler un LayerDrama.
T2 depend de T1 (la zone ou les deux se trouvent).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bot import choices, click  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from quest_suite import fame, in_log, things_at_pc  # noqa: E402
from travel_suite import (HOME, RESULTS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually,  # noqa: E402
                          log_has, marker, scan_logs, wait, zone_uid)

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


TESTS = {"t1": t1, "t2": t2, "t3": t3, "t4": t4, "t5": t5, "t6": t6}


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
