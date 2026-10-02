"""Quetes avec leur propre zone, prises par un client. Test court, sur des instances deja lancees (host + 1 client).

    python _tools/mp_test.py
    python _tools/instance_suite.py     # ~3 minutes, finit avec le client a la Prairie

I1  A prend chez l'host une quete "subjuguer" : il entre dans la zone de la quete, l'host ne fait que la lui garder
I2  A tue les monstres et ressort : il retrouve l'host, la quete est rendue, recompense et renommee pour A,
    la zone de la quete n'existe plus chez l'host, et la carte du monde de l'host n'a pas bouge
I3  A en prend une autre et ressort sans rien tuer : quete ratee, renommee en baisse pour A seulement
I4  A en prend une troisieme, se deconnecte dans la zone et revient : la quete et la zone ont disparu, sans penalite ;
    un echange en cours au moment d'entrer dans la zone est annule des deux cotes
I5  A rend une quete de defense apres 50 vagues : la prime compte ses vagues, pas celles de l'host
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from quest_suite import fame, in_log, kept, offered, things_at_pc  # noqa: E402
from travel_suite import HOME, RESULTS, both_joined, check, dismiss_dialogs, ev, eventually, scan_logs, wait  # noqa: E402
import chara_suite  # noqa: E402

H, A = 27551, 27552
T = "ElinTogether.Helper.PlayerTrade"


def world_icon():
    """L'icone de la case de la carte du monde ou se trouve l'host (0 = effacee)."""
    return ev(H, 'var z = EClass._zone.GetTopZone(); var c = EClass.scene.elomap.GetCell(z.x, z.y); return c == null ? "pas de case" : c.obj.ToString();')


def offer_subdue():
    """L'host fait proposer une quete "subjuguer" par un habitant, renvoie (numero de la quete, numero du donneur)."""
    r = ev(H, 'var c = EClass._map.charas.Find(x => !x.IsPCFaction && !x.IsPC && x.quest == null); '
              'var q = Quest.Create(EClass.sources.quests.rows.Find(r => r.type == "QuestSubdue").id, null, c); '
              'return q.uid + "|" + c.uid;')
    uid, giver = r.split("|")
    return int(uid), int(giver)


def enter(uid, giver):
    """Comme le dialogue du jeu : accepter, creer la zone de la quete, y entrer."""
    # le dialogue "quete reussie / ratee" du jeu attend un clic et retient le deplacement suivant
    dismiss_dialogs(A)
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {giver}); EClass.game.quests.Start(c.quest); '
          'var z = c.quest.CreateInstanceZone(c); EClass.pc.MoveZone(z, ZoneTransition.EnterState.Center); "ok"')
    def inside():
        dismiss_dialogs(A)
        return (state(A).get("sceneMode") == "Zone" and ev(A, "EClass._zone.IsInstance.ToString()") == "True"
                and bool(state(A).get("awayZone")))

    wait(inside, "A dans la zone de la quete", timeout=120)
    time.sleep(4)
    return int(ev(A, "EClass._zone.uid.ToString()"))


def leave():
    ev(A, 'EClass.pc.MoveZone(EClass._zone.ParentZone); "ok"')
    both_joined(H, A, HOME)
    time.sleep(4)
    dismiss_dialogs(A)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        a = state(A)["pc"]["uid"]

        log("--- I1")
        uid, giver = offer_subdue()
        check("A voit la quete proposee", eventually(lambda: offered(A, uid), timeout=10))
        home_tile = ev(H, 'var z = EClass._zone; EClass.world.region.elomap.GetZone(z.x, z.y).uid.ToString()')
        icon = world_icon()
        zuid = enter(uid, giver)
        check("A est dans la zone de sa quete, avec la quete au journal et sans delai",
              in_log(A, uid) and ev(A, f'EClass.game.quests.Get({uid}).deadline.ToString()') == "0")
        check("la zone suit la quete (des monstres a subjuguer)",
              ev(A, 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); (e != null && e.quest != null && e.enemies.Count > 0).ToString()') == "True")
        check("l'host la garde pour A, sans l'avoir dans son journal ni en offre",
              str(uid) in kept(a).split(",") and not in_log(H, uid) and not offered(H, uid))
        check("l'host connait la zone, sans toucher a sa carte du monde",
              ev(H, f'(EClass.game.spatials.Find({zuid}) != null).ToString()') == "True"
              and ev(H, 'var z = EClass._zone; EClass.world.region.elomap.GetZone(z.x, z.y).uid.ToString()') == home_tile)
        ev(H, 'EClass.game.Save(); "ok"')
        check("la zone survit a une sauvegarde de l'host", ev(H, f'(EClass.game.spatials.Find({zuid}) != null).ToString()') == "True")

        log("--- I2")
        before = {"fa": fame(A), "fh": fame(H), "a": 0, "h": things_at_pc(H)}
        ev(A, 'var e = EClass._zone.events.GetEvent<ZoneEventSubdue>(); foreach (var id in e.enemies.ToList()) '
              '{ var c = EClass._map.FindChara(id); if (c != null) c.Die(); } e.CheckClear(); "ok"')
        check("A a subjugue les monstres : la quete est reussie",
              eventually(lambda: ev(A, "EClass._zone.instance.status.ToString()") == "Success", timeout=10))
        leave()
        check("A ressort et retrouve l'host : la quete est rendue", eventually(lambda: not in_log(A, uid), timeout=15))
        check("l'host ne la garde plus", eventually(lambda: str(uid) not in kept(a).split(","), timeout=10))
        check("recompense aux pieds de A, pas de l'host",
              eventually(lambda: things_at_pc(H, a) > 0, timeout=10) and things_at_pc(H) == before["h"])
        check("renommee pour A, pas pour l'host", eventually(lambda: fame(A) > before["fa"], timeout=10) and fame(H) == before["fh"])
        check("la zone de la quete n'existe plus chez l'host", ev(H, f'(EClass.game.spatials.Find({zuid}) == null).ToString()') == "True")
        check(f"l'icone de la base sur la carte du monde de l'host n'a pas bouge ({icon})", world_icon() == icon and icon != "0")

        log("--- I3")
        uid, giver = offer_subdue()
        check("A voit la deuxieme quete proposee", eventually(lambda: offered(A, uid), timeout=10))
        zuid = enter(uid, giver)
        before = {"fa": fame(A), "fh": fame(H)}
        leave()
        check("A ressort sans rien tuer : la quete est ratee, sortie de son journal", eventually(lambda: not in_log(A, uid), timeout=15))
        check("sa renommee baisse, pas celle de l'host", eventually(lambda: fame(A) < before["fa"], timeout=10) and fame(H) == before["fh"])
        check("l'host ne la garde plus et la zone n'existe plus",
              eventually(lambda: str(uid) not in kept(a).split(","), timeout=10)
              and ev(H, f'(EClass.game.spatials.Find({zuid}) == null).ToString()') == "True")

        log("--- I4")
        uid, giver = offer_subdue()
        check("A voit la troisieme quete proposee", eventually(lambda: offered(A, uid), timeout=10))
        h = state(H)["pc"]["uid"]
        ev(A, f'var p = EClass._map.charas.Find(x => x.uid == {h}).pos.GetNearestPoint(false, false); EClass.pc.Teleport(p, true, true); "ok"')
        time.sleep(3)
        ev(A, f'{T}.Invite({h}); "ok"')
        trading = eventually(lambda: ev(H, f'{T}.Describe()').startswith("Invited"), timeout=10)
        ev(H, 'foreach (var l in EClass.ui.layers.OfType<Dialog>().ToList()) l.Close(); "ok"')
        zuid = enter(uid, giver)
        if trading:
            check("l'invitation a l'echange est oubliee des deux cotes quand A change de carte",
                  eventually(lambda: ev(A, f'{T}.Describe()') == "none" and not ev(H, f'{T}.Describe()').startswith("Invited"), timeout=15))
        before = {"fa": fame(A)}
        chara_suite.leave()
        check("A se deconnecte dans la zone : l'host detruit la zone",
              eventually(lambda: ev(H, f'(EClass.game.spatials.Find({zuid}) == null).ToString()') == "True", timeout=30))
        check("l'icone de la base n'a toujours pas bouge", world_icon() == icon)
        choices = chara_suite.connect()
        chara_suite.click(0)
        a2 = chara_suite.in_game()
        check(f"A revient avec le meme personnage ({choices})", a2 == a)
        time.sleep(4)
        dismiss_dialogs(A)
        check("la quete n'est plus dans son journal", eventually(lambda: not in_log(A, uid), timeout=15))
        check("l'host ne la garde plus", eventually(lambda: str(uid) not in kept(a).split(","), timeout=15))
        check("sans penalite de renommee", fame(A) == before["fa"])

        log("--- I5")
        r = ev(H, 'var c = EClass._map.charas.Find(x => !x.IsPCFaction && !x.IsPC && x.quest == null); '
                  'var q = Quest.Create(EClass.sources.quests.rows.Find(r => r.type == "QuestDefenseGame").id, null, c); '
                  'return q.uid + "|" + c.uid;')
        uid, giver = (int(x) for x in r.split("|"))
        check("A voit la quete de defense proposee", eventually(lambda: offered(A, uid), timeout=10))
        ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {giver}); EClass.game.quests.Start(c.quest); "ok"')
        check("A l'a dans son journal", eventually(lambda: in_log(A, uid), timeout=10))
        gold = 'EClass._map.charas.Find(x => x.uid == %d).pos.Things.Where(t => t.id == "money").Sum(t => t.Num).ToString()' % a
        before = int(ev(H, gold))
        ev(H, 'QuestDefenseGame.lastWave = 0; QuestDefenseGame.bonus = 0; "ok"')
        ev(A, f'QuestDefenseGame.lastWave = 50; QuestDefenseGame.bonus = 2; EClass.game.quests.Get({uid}).Complete(); "ok"')
        check("la quete est rendue", eventually(lambda: not in_log(A, uid) and str(uid) not in kept(a).split(","), timeout=15))
        # 50 vagues, bonus 2 : prime d'au moins 50 * 4 * 110 / 2 * 0,7 = 7700 pieces, bien plus que la recompense de base
        check("la prime compte les 50 vagues de A", eventually(lambda: int(ev(H, gold)) - before >= 7000, timeout=10))
        check("le compteur de vagues de l'host n'a pas bouge", ev(H, 'QuestDefenseGame.lastWave + "/" + QuestDefenseGame.bonus') == "0/0")
        dismiss_dialogs(A)
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {ex}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-instance-{name}', port)}")
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
