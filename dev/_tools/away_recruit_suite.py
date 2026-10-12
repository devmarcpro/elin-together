"""Un invite recrute SEUL, sur une carte qu'il tient, puis retrouve l'host. Host + 1 client, a la Prairie.

    python _tools/mp_test.py
    python _tools/away_recruit_suite.py

Signale par un joueur le 2026-10-12 (invite, base de l'host a Vernis) : « les PNJ que je recrute seul dans les champs
disparaissent toujours (lingot d'or, boule a monstre relachee, oeuf eclos) ; pour ceux deja dans mon equipe, mes
reglages faits dans les champs ne sont jamais pris, et ils s'en vont souvent ».

A1  l'invite part seul a Vernis, y recrute un animal ne la-bas (cree dans SON jeu, qui tient la carte)
A2  il rentre chez l'host : la recrue est a cote de lui, dans l'equipe, a lui, dans les DEUX jeux
A3  il repart seul avec elle : elle le suit la-bas
A4  seul la-bas, il regle un compagnon (« reste ici », equipement partage) ; de retour chez l'host, le reglage tient
A5  il rentre encore : la recrue est toujours la, une seule fois

Ce que le banc ne joue pas comme un joueur : la recrue est creee par CharaGen dans le jeu de l'invite et recrutee
par Chara.MakeAlly (pas le lingot, la boule ni l'oeuf) ; les reglages sont ecrits par eval ; les voyages sont des
« move » du pont ; la carte est Vernis, pas un champ sauvage cree par l'invite.
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, state  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, move, scan_logs, wait  # noqa: E402

H, A = 27551, 27552


def look(port, uid, m):
    q = (f'var r = EClass.game.cards.globalCharas.Find({uid}); var w = EClass.game.cards.globalCharas.Find({m}); '
         f'var onMap = EClass._map.charas.Find(x => x.uid == {m}); '
         'if (w == null) return "absent du monde|" + (onMap != null); '
         f'return "la|" + (onMap != null) + "|" + EClass.pc.party.members.Count(x => x != null && x.uid == {m}) + "|" + w.GetInt("emp_owner") + "|" + '
         '(onMap == null || r == null ? -1 : onMap.pos.Distance(r.pos)) + "|" + (w.currentZone == null ? "sans carte" : w.currentZone.uid.ToString()) + "|" + w.noMove + "|" + w.GetInt(113);')
    return str(ev(port, q)).split("|")


def here(step, uid, m, extra=None):
    time.sleep(4)
    for who, port in (("chez l'host", H), ("chez l'invite", A)):
        got = look(port, uid, m)
        if got[0] != "la":
            check(f"{step} {who} : la recrue existe ({got})", False)
            continue
        _, on_map, party, owner, dist, zone, no_move, shared = got
        check(f"{step} {who} : la recrue est sur la carte, a 3 cases au plus de l'invite (sur la carte {on_map}, distance {dist}, carte {zone})",
              on_map == "True" and 0 <= int(dist) <= 3)
        check(f"{step} {who} : dans l'equipe une fois ({party})", party == "1")
        if port == H:
            check(f"{step} {who} : elle appartient a l'invite (emp_owner {owner})", owner == str(uid))
        if extra:
            check(f"{step} {who} : le reglage fait seul tient (reste ici {no_move}, equipement partage {shared})", (no_move, shared) == extra)


def alone(what):
    move(A, VERNIS)
    wait(client_settled(A, VERNIS, True), what, timeout=180)
    time.sleep(3)


def back():
    move(A, HOME)
    both_joined(H, A, HOME)


def to_field(what):
    """l'invite sort par le bord et entre sur une case libre de la carte du monde : un champ que SON jeu cree"""
    from travel_suite import dismiss_dialogs, enter_at, free_spot  # noqa: PLC0415
    region = int(ev(A, 'EClass._zone.ParentZone.uid.ToString()'))
    ev(A, 'EClass.player.ExitBorder(); "ok"')
    wait(client_settled(A, region, True), "invite sur la carte du monde", timeout=120)
    time.sleep(3)
    enter_at(A, free_spot(A, HOME))
    wait(lambda: (lambda s: s.get("sceneMode") == "Zone" and s.get("awayZone"))(state(A)), what, timeout=120)
    time.sleep(3)
    dismiss_dialogs(A)
    return ev(A, '(EClass._zone is Zone_Field).ToString() + " " + EClass._zone.uid')


def field(uid):
    """F1 a F3 : la meme chose sur un champ sauvage (la carte du joueur qui l'a signale)"""
    log("--- F1 : l'invite recrute seul sur un champ sauvage")
    where = to_field("l'invite seul sur un champ")
    check(f"F1 : l'invite est seul sur un champ ({where})", where.startswith("True"))
    m = int(ev(A, 'var c = CharaGen.Create("putit"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(false, false)); c.MakeAlly(false); '
                  'return c.uid + "";'))
    got = str(ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); return (c != null && c.IsPCParty) + "|" + c.IsGlobal + "|" + '
                    '(c.homeZone == null ? "sans maison" : c.homeZone.uid.ToString()) + "|" + (c.homeBranch != null);'))
    check(f"F1 : la recrue est dans l'equipe de l'invite, dans son jeu (equipe|globale|maison|base : {got})", got.startswith("True|"))
    log("--- F2 : il rentre chez l'host")
    back()
    here("F2", uid, m)
    log("--- F3 : il retourne sur un champ avec elle, la regle, et rentre")
    where = to_field("l'invite seul sur un champ, avec sa recrue")
    got = look(A, uid, m)
    check(f"F3 : la recrue l'a suivi sur le champ ({where} ; {got})", got[0] == "la" and got[1] == "True" and got[2] == "1")
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); if (c != null) {{ c.ShowDialog(); }} return "ok";')
    time.sleep(2)
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); if (c != null) {{ c.noMove = true; c.orgPos = new Point(c.pos); c.SetInt(113, 1); }} '
          'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); return "ok";')
    time.sleep(2)
    back()
    here("F3", uid, m, extra=("True", "1"))


RESIDENT = ('var w = EClass.game.cards.globalCharas.Find({m}); if (w == null) return "absent du monde"; '
            'return "la|" + (w.currentZone == null ? "sans carte" : w.currentZone.uid.ToString()) + "|" + (EClass._map.charas.Find(x => x.uid == {m}) != null) + "|" + '
            '(w.homeBranch != null && w.homeBranch.members.Contains(w)) + "|" + EClass.pc.party.members.Count(x => x != null && x.uid == {m}) + "|" + w.isDead;')


def home_sent(uid):
    """H1 a H2 : recrute seul sur un champ puis renvoye a la base de la-bas (« rentre a la maison ») : il doit etre a
    la base chez l'host. Le banc fait ce que fait le choix du dialogue (Party.RemoveMember puis MoveZone(homeZone))"""
    log("--- H1 : l'invite recrute seul sur un champ, puis renvoie la recrue a la base")
    where = to_field("l'invite seul sur un champ")
    m = int(ev(A, 'var c = CharaGen.Create("putit"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(false, false)); c.MakeAlly(false); '
                  'return c.uid + "";'))
    sent = str(ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); var home = c.homeZone; EClass.pc.party.RemoveMember(c); c.MoveZone(home); '
                     'return (home == null ? "sans maison" : home.uid.ToString()) + "|" + (EClass._map.charas.Find(x => x.uid == ' + str(m) + ') == null);'))
    check(f"H1 : sur un champ ({where}), la recrue {m} est partie pour la base, dans le jeu de l'invite (maison|partie : {sent})", sent.endswith("|True"))
    log("--- H2 : l'invite rentre chez l'host, qui est a la base")
    back()
    time.sleep(4)
    for who, port in (("chez l'host", H), ("chez l'invite", A)):
        got = str(ev(port, RESIDENT.replace("{m}", str(m)))).split("|")
        check(f"H2 {who} : la recrue renvoyee est a la base, habitante, hors de l'equipe, sur la carte (existe|carte|sur la carte|habitante|equipe|morte : {got})",
              got[0] == "la" and got[1] == str(HOME) and got[2] == "True" and got[3] == "True" and got[4] == "0")


def home_sent_elsewhere(uid):
    """J1 a J3 : la meme chose quand l'host n'est PAS a la base (il est a Vernis) : la recrue renvoyee attend a la
    base, ou l'host la trouve en rentrant"""
    from travel_suite import zone_uid  # noqa: PLC0415
    log("--- J1 : l'host va a Vernis, l'invite recrute seul sur un champ et renvoie la recrue a la base")
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=180)
    time.sleep(4)
    if state(A).get("awayZone") is None and (state(A).get("zone") or {}).get("uid") != HOME:
        move(A, HOME)
        time.sleep(8)
    where = to_field("l'invite seul sur un champ")
    m = int(ev(A, 'var c = CharaGen.Create("putit"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(false, false)); c.MakeAlly(false); '
                  'return c.uid + "";'))
    sent = str(ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); var home = c.homeZone; EClass.pc.party.RemoveMember(c); c.MoveZone(home); '
                     'return (home == null ? "sans maison" : home.uid.ToString());'))
    check(f"J1 : sur un champ ({where}), la recrue {m} est partie pour la base {sent}", sent == str(HOME))
    log("--- J2 : l'invite rejoint l'host a Vernis")
    move(A, VERNIS)
    both_joined(H, A, VERNIS)
    time.sleep(4)
    got = str(ev(H, RESIDENT.replace("{m}", str(m)))).split("|")
    check(f"J2 chez l'host (a Vernis) : la recrue existe, a la base, habitante, pas sur cette carte (existe|carte|sur la carte|habitante|equipe|morte : {got})",
          got[0] == "la" and got[1] == str(HOME) and got[2] == "False" and got[3] == "True" and got[4] == "0")
    log("--- J3 : tout le monde rentre a la base")
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host a la base", timeout=180)
    time.sleep(4)
    s = state(A)
    if s.get("awayZone") or (s.get("zone") or {}).get("uid") != HOME:
        move(A, HOME)
    both_joined(H, A, HOME)
    time.sleep(4)
    for who, port in (("chez l'host", H), ("chez l'invite", A)):
        got = str(ev(port, RESIDENT.replace("{m}", str(m)))).split("|")
        check(f"J3 {who} : la recrue est la, a la base (existe|carte|sur la carte|habitante|equipe|morte : {got})",
              got[0] == "la" and got[1] == str(HOME) and got[2] == "True" and got[3] == "True")


# tout ce que le jeu garde d'un personnage en nombres, en textes et en cases a cocher (les reglages y sont tous)
DIGEST = ('var c = EClass.game.cards.globalCharas.Find({m}); if (c == null) return "absent"; '
          'var f = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic; '
          'var ints = typeof(Card).GetField("_ints", f).GetValue(c) as int[]; var cints = typeof(Chara).GetField("_cints", f).GetValue(c) as int[]; '
          'var parts = new System.Collections.Generic.List<string>(); '
          # (les cases a cocher vivent a part et ne sont rangees dans ints0, ints2 et cints0 qu'a la sauvegarde : lues en direct)
          'var cb = typeof(Chara).GetField("_cbits1", f).GetValue(c); '
          'parts.Add("cases1=" + c._bits1.ToInt()); parts.Add("cases2=" + c._bits2.ToInt()); '
          'parts.Add("cases3=" + cb.GetType().GetField("Bits", f).GetValue(cb)); '
          'for (var i = 0; i < ints.Length; i++) if (i != 0 && i != 2) parts.Add("ints" + i + "=" + ints[i]); '
          'for (var i = 1; i < cints.Length; i++) parts.Add("cints" + i + "=" + cints[i]); '
          'foreach (var k in c.mapInt.OrderBy(x => x.Key)) parts.Add("mapInt" + k.Key + "=" + k.Value); '
          'foreach (var k in c.mapStr.OrderBy(x => x.Key)) parts.Add("mapStr" + k.Key + "=" + k.Value); '
          'parts.Add("noMove=" + c.noMove); parts.Add("isLeashed=" + c.isLeashed); parts.Add("memberType=" + c.memberType); '
          'parts.Add("knowFav=" + c.knowFav); parts.Add("orgPos=" + (c.orgPos == null ? "-" : c.orgPos.x + "," + c.orgPos.z)); '
          'parts.Add("altName=" + c.c_altName); parts.Add("home=" + (c.homeZone == null ? 0 : c.homeZone.uid)); '
          'parts.Add("hostility=" + c.hostility + "/" + c.c_originalHostility); parts.Add("affinity=" + c._affinity); '
          'parts.Add("equip=" + string.Join("+", c.things.Where(t => t.isEquipped).Select(t => t.id).OrderBy(x => x))); '
          'parts.Add("sac=" + string.Join("+", c.things.Where(t => !t.isEquipped).Select(t => t.id + "x" + t.Num).OrderBy(x => x))); '
          'return string.Join(";", parts);')
# ce qui change tout seul d'une carte a l'autre, sans etre un reglage : la carte, la case, la direction, les tours
MOVING = ("cints1=", "ints6=", "ints7=", "ints8=", "ints9=", "ints10=", "ints11=", "ints12=", "ints13=", "ints14=", "ints15=", "ints16=", "ints17=")
SET_ALL = ('var c = EClass._map.charas.Find(x => x.uid == {m}); if (c == null) return "pas sur la carte"; '
           'c.noMove = true; c.orgPos = new Point(c.pos); foreach (var id in new[] { 106, 108, 113, 119, 123, 126 }) c.SetInt(id, 1); '
           'c.SetBool(129, true); c.knowFav = true; c.isLeashed = true; c.c_altName = "Nom du banc"; '
           'var gift = ThingGen.Create("dagger"); c.AddThing(gift); return "ok";')


def digest(port, m):
    out = str(ev(port, DIGEST.replace("{m}", str(m))))
    return dict(x.split("=", 1) for x in out.split(";") if "=" in x) if out != "absent" else None


def settings(uid):
    """T1 a T3 : TOUS les reglages d'un compagnon deja connu de l'host, faits par l'invite seul sur un champ, puis le
    retour chez l'host : l'etat complet du compagnon (nombres, textes, cases, equipement, sac) est compare entre le
    jeu de l'invite avant de rentrer et le jeu de l'host apres. Demande de l'utilisateur : « teste tous les reglages »"""
    import guest_suite as g  # noqa: PLC0415
    log("--- T1 : un compagnon recrute chez l'host (connu des deux jeux), emmene sur un champ")
    ctx = {"a": (A, uid), "h": (H, state(H)["pc"]["uid"])}
    m = g.tame(ctx, "cat", "a")
    if not check(f"T1 : l'invite a un compagnon connu de l'host ({m})", m):
        return
    g.clear_conditions(m)
    time.sleep(2)
    where = to_field("l'invite seul sur un champ, avec son compagnon")
    check(f"T1 : il l'a suivi sur le champ ({where})", look(A, uid, m)[1] == "True")
    log("--- T2 : seul, l'invite fait tous les reglages du dialogue, la laisse, un nom, et lui donne un objet")
    ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); if (c != null) c.ShowDialog(); return "ok";')
    time.sleep(2)
    done = str(ev(A, SET_ALL.replace("{m}", str(m))))
    ev(A, 'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); return "ok";')
    time.sleep(3)
    mine = digest(A, m)
    check(f"T2 : reglages faits dans le jeu de l'invite ({done})", done == "ok" and mine and mine.get("noMove") == "True")
    log("--- T3 : il rentre chez l'host ; l'etat du compagnon est compare")
    back()
    time.sleep(5)
    for who, port in (("chez l'host", H), ("chez l'invite", A)):
        got = digest(port, m)
        if not check(f"T3 {who} : le compagnon existe", got is not None):
            continue
        diff = sorted(k for k in set(mine) | set(got) if mine.get(k) != got.get(k) and not (k + "=").startswith(MOVING))
        detail = " ; ".join(f"{k} : {mine.get(k)} -> {got.get(k)}" for k in diff[:12])
        check(f"T3 {who} : tous les reglages faits seul sont la ({len(mine)} valeurs comparees ; differences : {detail or 'aucune'})", not diff)
        moved = sorted(k for k in mine if mine.get(k) != got.get(k) and (k + "=").startswith(MOVING))
        log(f"{who} : valeurs de position qui ont bouge (attendu) : {', '.join(moved) or 'aucune'}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    uid = state(A)["pc"]["uid"]
    steps = {"field": field, "home": home_sent, "elsewhere": home_sent_elsewhere, "settings": settings}
    if any(k in sys.argv[1:] for k in steps):
        try:
            for k, step in steps.items():
                if k in sys.argv[1:]:
                    step(uid)
        except Exception as ex:  # noqa: BLE001
            check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        scan_logs(start)
        failed = [label for label, good in RESULTS if not good]
        print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
        sys.exit(1 if failed else 0)
    try:
        log("--- A1 : l'invite recrute seul, sur une carte qu'il tient")
        alone("l'invite seul a Vernis")
        m = int(ev(A, 'var c = CharaGen.Create("putit"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(false, false)); c.MakeAlly(false); '
                      'return c.uid + "";'))
        got = str(ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); return (c != null && c.IsPCParty) + "|" + c.IsGlobal + "|" + c.uid;'))
        check(f"A1 : la recrue est dans l'equipe de l'invite, dans son jeu ({got})", got.startswith("True|"))
        log("--- A2 : il rentre chez l'host")
        back()
        here("A2", uid, m)
        log("--- A3 : il repart seul avec elle")
        alone("l'invite seul a Vernis, avec sa recrue")
        got = look(A, uid, m)
        check(f"A3 : la recrue l'a suivi a Vernis, dans son jeu ({got})", got[0] == "la" and got[1] == "True" and got[2] == "1")
        log("--- A4 : seul, il la regle (reste ici, equipement partage)")
        ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); if (c != null) {{ c.ShowDialog(); }} return "ok";')
        time.sleep(2)
        ev(A, f'var c = EClass._map.charas.Find(x => x.uid == {m}); if (c != null) {{ c.noMove = true; c.orgPos = new Point(c.pos); c.SetInt(113, 1); }} '
              'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); return "ok";')
        time.sleep(2)
        log("--- A5 : il rentre encore")
        back()
        here("A5", uid, m, extra=("True", "1"))
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
    scan_logs(start)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print("  ECHEC :", label)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
