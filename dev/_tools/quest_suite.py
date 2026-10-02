"""Quetes communes, y compris en voyage seul. Test court, sur des instances deja lancees (host + 1 client).

    python _tools/mp_test.py             # une fois : host + 1 client dans la Prairie
    python _tools/quest_suite.py         # 2 a 3 minutes (finit avec tout le monde a la Prairie)

Q1  A part seul a Lumiest et y accepte une quete : elle arrive dans le journal de l'host
Q2  A la termine la-bas : il recoit les recompenses, l'host la voit terminee, sans recompense chez lui
Q3  l'host accepte une quete pendant que A est en voyage : A la voit dans son journal
Q4  A rentre et termine cette quete chez l'host : les recompenses tombent aux pieds de A, pas de l'host
Q5  A, chez l'host, lance une quete d'histoire (comme un dialogue) : demarree pour tous, ce qu'elle donne va a A
Q6  A et l'host la font avancer tour a tour, A la termine
Q7  les souvenirs de dialogue sont communs, sur la meme carte et en voyage
Q8  un objet offert par un dialogue a A est cree par l'host, aux pieds de A
Q9  ce qu'un dialogue declenche dans le monde, demande par A, se produit chez l'host
P1-P4, P11 remplacent Q1-Q4, Q11 quand l'option "quetes aleatoires et renommee par joueur" est cochee (defaut) :
    P1  A prend une quete en voyage : dans son journal seulement, l'host la garde pour lui
    P2  A la termine la-bas : recompenses et renommee pour A, rien chez l'host
    P3  l'host prend une quete : A ne l'a pas
    P4  A prend une quete chez l'host, voyage, revient, la rend : tout est a A, la quete le suit partout
    P11 A rate une quete : sa renommee baisse, pas celle de l'host
Q11 une quete ratee l'est pour tout le monde ; le delai d'une quete prise en voyage est le meme chez l'host
Q10 drapeaux d'histoire, objets cles et dette communs ; les reglages personnels restent personnels
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from travel_suite import (HOME, LUMIEST, RESULTS, both_joined, check, client_settled, ev, eventually, move,  # noqa: E402
                          scan_logs, wait)

H, A = 27551, 27552


def offer(port):
    """Une quete proposee par un habitant de la carte (creee au besoin), renvoie son uid."""
    r = ev(port, 'var c = EClass._map.charas.Find(x => x.quest != null && !EClass.game.quests.list.Contains(x.quest)); '
                 'if (c == null) { EClass._zone.UpdateQuests(true); '
                 'c = EClass._map.charas.Find(x => x.quest != null && !EClass.game.quests.list.Contains(x.quest)); } '
                 'c == null ? "" : c.quest.uid + "|" + c.quest.id')
    if not r:
        # pas d'habitant qui donne des quetes (base vide) : un personnage de la carte en propose une
        r = ev(port, 'var c = EClass._map.charas.Find(x => !x.IsPCFaction && x.quest == null); '
                     'var q = Quest.Create("huntRace", null, c); q.uid + "|" + q.id')
    uid, qid = r.split("|")
    return int(uid), qid


def accept(port, uid):
    ev(port, f'var c = EClass._map.charas.Find(x => x.quest != null && x.quest.uid == {uid}); EClass.game.quests.Start(c.quest); "ok"')


def in_log(port, uid):
    return ev(port, f'EClass.game.quests.list.Exists(q => q.uid == {uid}).ToString()') == "True"


def complete(port, uid):
    ev(port, f'EClass.game.quests.list.Find(q => q.uid == {uid}).Complete(); "ok"')


def things_at_pc(port, uid=None):
    """Nombre d'objets poses a la position du joueur local, ou (vu de ce jeu) du perso uid."""
    who = "EClass.pc" if uid is None else f"EClass.game.cards.globalCharas.Find({uid})"
    return int(ev(port, f'var p = {who}.pos; EClass._map.things.Count(t => t.pos.x == p.x && t.pos.z == p.z).ToString()'))


def q1(ctx):
    move(A, LUMIEST)
    wait(client_settled(A, LUMIEST, True), "A seul a Lumiest")
    time.sleep(3)
    uid, qid = offer(A)
    ctx["q1"] = uid
    host_next = int(ev(H, 'EClass.game.quests.uid.ToString()'))
    log(f"quete de Lumiest : {qid} uid {uid} (compteur de l'host : {host_next})")
    check("la quete creee chez A a un numero reserve (pas ceux de l'host)", uid >= host_next + 1000)
    accept(A, uid)
    check("A accepte une quete a Lumiest : elle est dans son journal", eventually(lambda: in_log(A, uid), timeout=10))
    check("elle arrive dans le journal de l'host", eventually(lambda: in_log(H, uid), timeout=15))


def q2(ctx):
    uid = ctx["q1"]
    before = {"a": things_at_pc(A), "h": things_at_pc(H), "fame": int(ev(H, 'EClass.player.fame.ToString()'))}
    complete(A, uid)
    check("A termine la quete a Lumiest : il recoit les recompenses a ses pieds",
          eventually(lambda: things_at_pc(A) > before["a"], timeout=10))
    check("l'host la voit terminee", eventually(lambda: not in_log(H, uid), timeout=15))
    check("pas de recompense en double chez l'host", things_at_pc(H) == before["h"])
    check("la renommee, commune, monte chez l'host", int(ev(H, 'EClass.player.fame.ToString()')) > before["fame"])


def q3(ctx):
    uid, qid = offer(H)
    ctx["q3"] = uid
    log(f"quete de la Prairie : {qid} uid {uid}")
    accept(H, uid)
    check("l'host accepte une quete : elle est dans son journal", eventually(lambda: in_log(H, uid), timeout=10))
    check("A, en voyage, la voit dans son journal", eventually(lambda: in_log(A, uid), timeout=15))


def q4(ctx):
    uid = ctx["q3"]
    move(A, HOME)
    both_joined(H, A, HOME)
    check("A rentre : la quete de l'host est toujours dans son journal", in_log(A, uid))
    before = {"a": things_at_pc(H, ctx["a"]), "h": things_at_pc(H)}
    complete(A, uid)
    check("A termine la quete chez l'host : terminee pour l'host aussi", eventually(lambda: not in_log(H, uid), timeout=15))
    check("les recompenses tombent aux pieds de A", eventually(lambda: things_at_pc(H, ctx["a"]) > before["a"], timeout=10))
    check("pas aux pieds de l'host", things_at_pc(H) == before["h"])


STORY = "QuestFiamaLock"   # donne un crochet et un coffre des qu'elle commence


def phase(port, qid):
    return int(ev(port, f'var q = EClass.game.quests.Get("{qid}"); (q == null ? -1 : q.phase).ToString()'))


def quest_uid(port, qid):
    return int(ev(port, f'var q = EClass.game.quests.Get("{qid}"); (q == null ? 0 : q.uid).ToString()'))


def flag(port, name):
    return int(ev(port, f'EClass.player.dialogFlags.GetValueOrDefault("{name}", -1).ToString()'))


def set_flag(port, name, value):
    ev(port, f'EClass.player.dialogFlags["{name}"] = {value}; "ok"')


def q5(ctx):
    qid = ev(A, f'EClass.sources.quests.rows.Find(r => r.type == "{STORY}").id')
    ctx["story"] = qid
    before = {"a": things_at_pc(H, ctx["a"]), "h": things_at_pc(H)}
    # comme le fait un dialogue : la quete est creee chez le joueur, puis demarree
    ev(A, f'EClass.game.quests.Start(Quest.Create("{qid}")); "ok"')
    check("A lance une quete d'histoire : elle est tout de suite dans son journal", quest_uid(A, qid) != 0)
    check("l'host la demarre pour tout le monde", eventually(lambda: quest_uid(H, qid) > 0, timeout=15))
    check("A a la quete de l'host (meme numero), une seule fois",
          eventually(lambda: quest_uid(A, qid) == quest_uid(H, qid), timeout=10)
          and ev(A, f'EClass.game.quests.list.Count(q => q.id == "{qid}").ToString()') == "1")
    check("ce que la quete donne tombe aux pieds de A", eventually(lambda: things_at_pc(H, ctx["a"]) > before["a"], timeout=10))
    check("pas aux pieds de l'host", things_at_pc(H) == before["h"])
    check("A voit ces objets chez lui", eventually(lambda: things_at_pc(A) >= things_at_pc(H, ctx["a"]), timeout=10))


def q6(ctx):
    qid = ctx["story"]
    ev(A, f'EClass.game.quests.Get("{qid}").NextPhase(); "ok"')
    check("A fait avancer la quete : l'host suit", eventually(lambda: phase(H, qid) == 1, timeout=15))
    # cette quete n'a que deux etapes : l'host la remet a la premiere
    ev(H, f'EClass.game.quests.Get("{qid}").ChangePhase(0); "ok"')
    check("l'host change l'etape : A suit", eventually(lambda: phase(A, qid) == 0, timeout=15))
    ev(A, f'EClass.game.quests.Get("{qid}").Complete(); "ok"')
    check("A la termine : terminee pour l'host",
          eventually(lambda: ev(H, f'EClass.game.quests.completedIDs.Contains("{qid}").ToString()') == "True", timeout=15))
    check("et sortie des deux journaux", quest_uid(H, qid) == 0 and quest_uid(A, qid) == 0)


def q7(ctx):
    set_flag(A, "emp_test_a", 3)
    check("un dialogue vu par A est retenu chez l'host", eventually(lambda: flag(H, "emp_test_a") == 3, timeout=10))
    set_flag(H, "emp_test_h", 5)
    check("un dialogue vu par l'host est retenu chez A", eventually(lambda: flag(A, "emp_test_h") == 5, timeout=10))
    move(A, LUMIEST)
    wait(client_settled(A, LUMIEST, True), "A seul a Lumiest")
    time.sleep(2)
    set_flag(A, "emp_test_a", 4)
    check("pareil quand A est en voyage", eventually(lambda: flag(H, "emp_test_a") == 4, timeout=10))
    set_flag(H, "emp_test_h", 6)
    check("et dans l'autre sens", eventually(lambda: flag(A, "emp_test_h") == 6, timeout=10))
    move(A, HOME)
    both_joined(H, A, HOME)
    check("de retour, A a toujours les deux", flag(A, "emp_test_a") == 4 and flag(A, "emp_test_h") == 6)


def here(port, thing_id, uid=None):
    """Objets de ce type a la position du joueur local (ou du perso uid) : "uid:charges,..." tries."""
    who = "EClass.pc" if uid is None else f"EClass.game.cards.globalCharas.Find({uid})"
    return ev(port, f'var p = {who}.pos; string.Join(",", EClass._map.things.Where(t => t.id == "{thing_id}" && t.pos.x == p.x '
                    '&& t.pos.z == p.z).OrderBy(t => t.uid).Select(t => t.uid + ":" + t.c_charges))')


def q8(ctx):
    before = here(H, "lockpick", ctx["a"])
    # comme un dialogue qui offre un objet : cree chez le joueur, puis modifie apres l'avoir pose
    ev(A, 'var t = EClass.player.DropReward(ThingGen.Create("lockpick")); t.c_charges = 7; "ok"')
    check("un cadeau de dialogue recu par A existe chez l'host, aux pieds de A",
          eventually(lambda: here(H, "lockpick", ctx["a"]) != before, timeout=10))
    check("tel que le dialogue l'a fini (7 charges)", here(H, "lockpick", ctx["a"]).endswith(":7"))
    check("A a le meme objet que l'host, pas sa copie provisoire",
          eventually(lambda: here(A, "lockpick") == here(H, "lockpick", ctx["a"]), timeout=10))
    check("pas aux pieds de l'host", here(H, "lockpick") == "" or ev(H, "EClass.pc.pos.ToString()") == ev(H, f'EClass.game.cards.globalCharas.Find({ctx["a"]}).pos.ToString()'))


def logs_at_tutorial(port):
    return int(ev(port, 'EClass._map.things.Count(t => t.id == "log" && t.pos.x == 53 && t.pos.z == 52).ToString()'))


def q9(ctx):
    before = logs_at_tutorial(H)
    # ce qu'un dialogue declenche dans le monde (ici le decor du tutoriel) : A le demande, l'host le fait
    ev(A, 'var o = new UnityEngine.GameObject("emp_test_outcome").AddComponent<DramaOutcome>(); o.Tutorial1(); '
          'UnityEngine.Object.Destroy(o.gameObject); "ok"')
    check("un effet de dialogue demande par A se produit chez l'host", eventually(lambda: logs_at_tutorial(H) == before + 1, timeout=10))
    check("et A le voit", eventually(lambda: logs_at_tutorial(A) == before + 1, timeout=10))


def story(port, expr):
    return ev(port, f'({expr}).ToString()')


def q10(ctx):
    ev(A, 'EClass.player.flags.loytelEscaped = true; EClass.player.ModKeyItem("backpack", 1, false); EClass.player.flags.isShoesOff = true; "ok"')
    ev(H, 'EClass.player.flags.storyFiama = 7; EClass.player.debt = 12345; "ok"')
    check("un drapeau d'histoire leve chez A l'est chez l'host", eventually(lambda: story(H, "EClass.player.flags.loytelEscaped") == "True", timeout=10))
    key = 'EClass.player.keyItems.GetValueOrDefault(EClass.sources.keyItems.alias["backpack"].id, 0)'
    check("un objet cle recu par A est compte chez l'host", eventually(lambda: story(H, key) == story(A, key), timeout=10))
    check("l'avancee d'histoire de l'host arrive chez A", eventually(lambda: story(A, "EClass.player.flags.storyFiama") == "7", timeout=10))
    check("la dette aussi", eventually(lambda: story(A, "EClass.player.debt") == "12345", timeout=10))
    check("un reglage personnel (chaussures) reste personnel", story(H, "EClass.player.flags.isShoesOff") == "False")
    ev(A, 'EClass.player.flags.isShoesOff = false; "ok"')


def hours(port, uid):
    return int(ev(port, f'EClass.game.quests.list.Find(q => q.uid == {uid}).Hours.ToString()'))


def q11(ctx):
    move(A, LUMIEST)
    wait(client_settled(A, LUMIEST, True), "A seul a Lumiest")
    time.sleep(3)
    # en voyage, A a sa propre horloge : ici deux jours d'avance sur l'host
    ev(A, 'for (var i = 0; i < 48; i++) EClass.world.date.AdvanceHour(); "ok"')
    uid = int(ev(A, 'var c = EClass._map.charas.Find(x => x.quest != null && x.quest.deadline > 0 && !EClass.game.quests.list.Contains(x.quest)); '
                    'if (c == null) return "0"; EClass.game.quests.Start(c.quest); return c.quest.uid.ToString();'))
    if check("A accepte a Lumiest une quete a delai", uid != 0):
        check("elle arrive chez l'host", eventually(lambda: in_log(H, uid), timeout=15))
        left = hours(A, uid)
        check(f"avec le meme temps restant ({left} h chez A, {hours(H, uid)} h chez l'host)", abs(hours(H, uid) - left) <= 2)
        fame = int(ev(H, 'EClass.player.fame.ToString()'))
        ev(A, f'EClass.game.quests.list.Find(q => q.uid == {uid}).Fail(); "ok"')
        check("A la rate : elle sort du journal de l'host", eventually(lambda: not in_log(H, uid), timeout=15))
        check("et l'host compte la perte de renommee", int(ev(H, 'EClass.player.fame.ToString()')) < fame or fame == 0)

    uid, qid = offer(H)
    accept(H, uid)
    check("l'host accepte une quete, A en voyage la voit", eventually(lambda: in_log(A, uid), timeout=15))
    ev(H, f'EClass.game.quests.list.Find(q => q.uid == {uid}).Fail(); "ok"')
    check("l'host la rate : elle sort du journal de A", eventually(lambda: not in_log(A, uid), timeout=15))
    move(A, HOME)
    both_joined(H, A, HOME)


# ---------------------------------------------------------------- quetes aleatoires et renommee par joueur

KEPT = ('var logs = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetHost"), '
        '"PersonalQuestLogs").GetValue(null) as System.Collections.Generic.Dictionary<int, System.Collections.Generic.Dictionary<int, byte[]>>; ')


def kept(uid):
    """Numeros des quetes que l'host garde pour le joueur uid, tries."""
    return ev(H, KEPT + f'return logs.ContainsKey({uid}) ? string.Join(",", logs[{uid}].Keys.OrderBy(k => k)) : "";')


def fame(port):
    return int(ev(port, 'EClass.player.fame.ToString()'))


def offered(port, uid):
    """Ce jeu voit-il encore la quete uid proposee par un habitant de la carte ?"""
    return ev(port, f'EClass._map.charas.Exists(c => c.quest != null && c.quest.uid == {uid} && !EClass.game.quests.list.Contains(c.quest)).ToString()') == "True"


def p1(ctx):
    move(A, LUMIEST)
    wait(client_settled(A, LUMIEST, True), "A seul a Lumiest")
    time.sleep(3)
    uid, qid = offer(A)
    ctx["p1"] = uid
    log(f"quete de Lumiest : {qid} uid {uid}")
    accept(A, uid)
    check("A accepte une quete a Lumiest : elle est dans son journal", eventually(lambda: in_log(A, uid), timeout=10))
    check("l'host la garde pour A", eventually(lambda: str(uid) in kept(ctx["a"]).split(","), timeout=15))
    check("mais elle n'est pas dans le journal de l'host", not in_log(H, uid))


def p2(ctx):
    uid = ctx["p1"]
    before = {"a": things_at_pc(A), "h": things_at_pc(H), "fa": fame(A), "fh": fame(H)}
    complete(A, uid)
    check("A la termine a Lumiest : il recoit les recompenses a ses pieds", eventually(lambda: things_at_pc(A) > before["a"], timeout=10))
    check("sa renommee monte", fame(A) > before["fa"])
    check("l'host ne la garde plus", eventually(lambda: str(uid) not in kept(ctx["a"]).split(","), timeout=15))
    check("rien chez l'host : ni recompense, ni renommee", things_at_pc(H) == before["h"] and fame(H) == before["fh"])
    check("l'host connait la renommee de A",
          eventually(lambda: ev(H, 'var s = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetHost"), '
                                   '"PlayerStandings").GetValue(null) as System.Collections.Generic.Dictionary<int, int[]>; '
                                   f'return s.ContainsKey({ctx["a"]}) ? s[{ctx["a"]}][0].ToString() : "-1";') == str(fame(A)), timeout=10))


def p3(ctx):
    uid, qid = offer(H)
    ctx["p3"] = uid
    accept(H, uid)
    check("l'host accepte une quete : elle est dans son journal", eventually(lambda: in_log(H, uid), timeout=10))
    time.sleep(3)
    check("A, en voyage, ne l'a pas dans le sien", not in_log(A, uid))


def p4(ctx):
    fa = fame(A)
    move(A, HOME)
    both_joined(H, A, HOME)
    time.sleep(3)
    check("A rentre : la quete de l'host n'est ni dans son journal, ni proposee", not in_log(A, ctx["p3"]) and not offered(A, ctx["p3"]))
    check("A a garde sa renommee en revenant", fame(A) == fa)

    # un habitant propose une quete (creee par l'host), A la prend
    uid = int(ev(H, 'var c = EClass._map.charas.Find(x => !x.IsPCFaction && !x.IsPC && x.quest == null); '
                    'var q = Quest.Create("huntRace", null, c); return q.uid.ToString();'))
    check("A voit la quete proposee", eventually(lambda: offered(A, uid), timeout=10))
    accept(A, uid)
    check("A la prend : dans son journal, pas dans celui de l'host", eventually(lambda: in_log(A, uid), timeout=10) and not in_log(H, uid))
    check("elle n'est plus proposee chez l'host", eventually(lambda: not offered(H, uid), timeout=10))
    check("l'host la garde pour A", str(uid) in kept(ctx["a"]).split(","))

    # elle suit A en voyage et au retour
    move(A, LUMIEST)
    wait(client_settled(A, LUMIEST, True), "A seul a Lumiest")
    time.sleep(3)
    check("elle suit A en voyage", in_log(A, uid) and not in_log(A, ctx["p3"]))
    move(A, HOME)
    both_joined(H, A, HOME)
    time.sleep(3)
    check("et au retour", in_log(A, uid))

    before = {"a": things_at_pc(H, ctx["a"]), "h": things_at_pc(H), "fa": fame(A), "fh": fame(H)}
    complete(A, uid)
    check("A la rend chez l'host : les recompenses tombent aux pieds de A", eventually(lambda: things_at_pc(H, ctx["a"]) > before["a"], timeout=10))
    check("pas aux pieds de l'host", things_at_pc(H) == before["h"])
    check("la renommee va a A, pas a l'host", eventually(lambda: fame(A) > before["fa"], timeout=10) and fame(H) == before["fh"])
    check("l'host ne la garde plus", eventually(lambda: str(uid) not in kept(ctx["a"]).split(","), timeout=10))

    ev(H, f'EClass.game.quests.list.Find(q => q.uid == {ctx["p3"]}).Complete(); "ok"')


def p11(ctx):
    move(A, LUMIEST)
    wait(client_settled(A, LUMIEST, True), "A seul a Lumiest")
    time.sleep(3)
    uid, qid = offer(A)
    accept(A, uid)
    check("A prend une quete a Lumiest, l'host la garde", eventually(lambda: str(uid) in kept(ctx["a"]).split(","), timeout=15))
    before = {"fa": fame(A), "fh": fame(H)}
    ev(A, f'EClass.game.quests.list.Find(q => q.uid == {uid}).Fail(); "ok"')
    check("A la rate : sa renommee baisse, pas celle de l'host", (fame(A) < before["fa"] or before["fa"] == 0) and fame(H) == before["fh"])
    check("l'host ne la garde plus", eventually(lambda: str(uid) not in kept(ctx["a"]).split(","), timeout=15))
    move(A, HOME)
    both_joined(H, A, HOME)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": state(A)["pc"]["uid"]}
    personal = ev(H, 'ElinTogether.Net.NetSession.Instance.Rules.UsePersonalQuests.ToString()') == "True"
    log("quetes aleatoires et renommee : " + ("par joueur" if personal else "communes"))
    steps = ([p1, p2, p3, p4] if personal else [q1, q2, q3, q4]) + [q5, q6, q7, q8, q9, q10] + [p11 if personal else q11]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A)):
                try:
                    print(f"    capture {name} : {shot(f'fail-{step.__name__}-{name}', port)}")
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
