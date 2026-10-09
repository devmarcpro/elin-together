"""Reglages d'un objet de la carte faits par un joueur (conseil 4) : ils arrivent chez l'autre joueur, dans les deux sens.
Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/setting_suite.py            # ou --only s1,s3

S1  note ecrite sur un meuble.   S2  etiquette de vente (posee puis retiree, avec l'etiquette tenue en main).
S3  lit : le reclamer, en changer le type.   S5  nom de la base.   S6  nom d'un teleporteur.
S4  politiques de la base (vraie fenetre, vrai clic sur la politique).
S7  reglages d'un coffre de la base (menu du bouton de tri : priorite, pas de pourri, categories, filtre, drapeaux).
Avant : chaque jeu ne changeait que sa copie (l'host, qui fait vivre les habitants et sauvegarde, ne voyait rien).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import awake, both, chara, close_layers, first_id, give, use_held, use_menu  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552


def furniture(uid, make='ThingGen.Create("chest3")', extra=""):
    """L'host pose un meuble a cote de ce joueur ; renvoie son numero une fois vu par les deux jeux."""
    t = int(ev(H, f'var t = {make}; {extra} EClass._zone.AddCard(t, {chara(H, uid)}.pos.GetNearestPoint(false, false, false, true)).Install(); '
                  'return t.uid.ToString();'))
    eventually(lambda: ev(A, f'(EClass._map.things.Find(m => m.uid == {t}) != null).ToString()') == "True", timeout=10)
    return t


def thing(t):
    return f"EClass._map.things.Find(m => m.uid == {t})"


def s1(ctx):
    """note ecrite sur un meuble : ce qu'un joueur ecrit est lu par l'autre, dans les deux sens
    Ce que le banc ne joue pas comme un joueur : la saisie du texte ; il pose la note comme le fait la validation de la
    boite de saisie (`owner.c_note = texte`)"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        t = furniture(uid)
        try:
            text = f"note de {key}"
            ev(port, f'{thing(t)}.c_note = "{text}"; "ok"')
            read = lambda p: ev(p, f'var t = {thing(t)}; return t == null ? "absent" : (t.c_note ?? "");')  # noqa: E731
            check(cond=eventually(lambda: read(other) == text, timeout=10), label=f"{who} ecrit une note : l'autre joueur la lit ({read(other)!r})")
            check(f"{who} : et lui aussi ({read(port)!r})", read(port) == text)
        finally:
            ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); "ok"')


def s2(ctx):
    """etiquette de vente : l'objet qu'un joueur met en vente l'est dans les deux jeux, et quand il la retire aussi"""
    tag = first_id("SalesTag")
    if not check(f"le jeu a une etiquette de vente ({tag})", bool(tag)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        t = furniture(uid)
        try:
            x, z = (int(v) for v in ev(H, f'var t = {thing(t)}; return t.pos.x + "," + t.pos.z;').split(","))
            held = give(ctx, key, tag)
            sale = lambda p: ev(p, f'var t = {thing(t)}; return t == null ? "absent" : t.isSale + "/" + EClass._map.props.sales.Contains(t);')  # noqa: E731
            for want in ("True/True", "False/False"):
                awake(port)
                log(f"{who} : {use_held(port, held, at=(x, z))}")
                check(cond=eventually(lambda: sale(H) == want and sale(A) == want, timeout=10),
                      label=f"{who} {'met en vente' if want.startswith('T') else 'retire de la vente'} : les deux jeux disent pareil (host {sale(H)}, invite {sale(A)})")
        finally:
            ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); var c = {chara(H, uid)}; '
                  f'foreach (var k in c.things.Where(m => m.id == "{tag}").ToList()) k.Destroy(); "ok"')


def s3(ctx):
    """lit : le joueur qui reclame un lit, ou qui en change le type, le fait dans les deux jeux
    Ce que le banc ne joue pas comme un joueur : le menu du lit ; il fait ce que font ses entrees « reclamer » et « type »
    (ClearHolders + AddHolder(joueur), SetBedType)"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        t = furniture(uid, 'ThingGen.Create("bed")')
        try:
            bed = lambda p: ev(p, f'var t = {thing(t)}; return t == null ? "absent" : t.c_bedType + "/" + '  # noqa: E731
                                  '(t.c_charaList == null ? "" : string.Join(",", t.c_charaList.list));')
            ev(port, f'var b = (TraitBed){thing(t)}.trait; b.ClearHolders(); b.AddHolder(EClass.pc); "ok"')
            check(cond=eventually(lambda: bed(H).endswith(f"/{uid}") and bed(A) == bed(H), timeout=10),
                  label=f"{who} reclame le lit : il est a lui dans les deux jeux (host {bed(H)}, invite {bed(A)})")
            ev(port, f'((TraitBed){thing(t)}.trait).SetBedType(BedType.guest); "ok"')
            check(cond=eventually(lambda: bed(H) == "guest/" and bed(A) == "guest/", timeout=10),
                  label=f"{who} en fait un lit d'invite : type change et lit libere dans les deux jeux (host {bed(H)}, invite {bed(A)})")
        finally:
            ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); "ok"')


def s4(ctx):
    """politiques de la base : celle qu'un joueur active ou coupe dans la fenetre des politiques l'est dans les deux jeux"""
    acts = 'string.Join(",", EClass._zone.branch.policies.list.Where(p => p.active).Select(p => p.id).OrderBy(i => i))'
    pid = ev(H, 'var b = EClass._zone.branch; var p = b.policies.list.FirstOrDefault(x => !x.active && b.policies.CurrentAP() + x.Cost <= b.MaxAP); '
                'return p == null ? "" : p.id.ToString();')
    if not pid:
        # la base de test n'a pas de politique libre : une politique sans cout est donnee aux deux jeux (comme une recherche le ferait)
        pid = ev(H, 'EClass.sources.elements.rows.First(r => r.category == "policy" && r.cost.Length > 0 && r.cost[0] == 0).id.ToString()')
        for p in (H, A):
            ev(p, f'var b = EClass._zone.branch; if (!b.policies.list.Any(x => x.id == {pid})) b.policies.AddPolicy({pid}, false); "ok"')
    if not check(f"la base a une politique a activer ({pid}), connue des deux jeux",
                 bool(pid) and all(ev(p, f'EClass._zone.branch.policies.list.Any(x => x.id == {pid}).ToString()') == "True" for p in (H, A))):
        return
    click = ('var l = EClass.ui.GetLayer<LayerPolicy>() ?? EClass.ui.AddLayer<LayerPolicy>(); var b = l.GetComponentsInChildren<UIButton>(true)'
             f'.FirstOrDefault(x => x.refObj is Policy q && q.id == {pid}); if (b == null) return "bouton absent"; b.onClick.Invoke(); return "clic";')
    for who, key in both(ctx):
        port, uid = ctx[key]
        try:
            for p in (H, A):
                ev(p, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')
            ev(port, 'EClass.ui.AddLayer<LayerPolicy>(); "ok"')
            time.sleep(2)
            for want in (True, False):
                r = ev(port, click)
                on = lambda p: str(pid) in ev(p, acts).split(",")  # noqa: E731
                check(cond=eventually(lambda: on(H) == want and on(A) == want, timeout=10),
                      label=f"{who} {'active' if want else 'coupe'} la politique ({r}) : les deux jeux disent pareil (host [{ev(H, acts)}], invite [{ev(A, acts)}])")
        finally:
            for p in (H, A):
                ev(p, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')


def s5(ctx):
    """nom de la base : celui qu'un joueur lui donne est lu par l'autre
    Ce que le banc ne joue pas comme un joueur : la saisie ; il pose le nom comme la validation de la boite le fait"""
    name0 = ev(H, "EClass._zone.name ?? \"\"")
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        name = f"Base de {key}"
        ev(port, f'EClass._zone.name = "{name}"; EClass._zone.idPrefix = 0; WidgetDate.Refresh(); "ok"')
        read = lambda p: ev(p, "EClass._zone.name ?? \"\"")  # noqa: E731
        check(cond=eventually(lambda: read(other) == name, timeout=10), label=f"{who} renomme la base : l'autre joueur lit le nouveau nom ({read(other)!r})")
    if name0:
        ev(H, f'EClass._zone.name = "{name0}"; "ok"')
        eventually(lambda: ev(A, "EClass._zone.name ?? \"\"") == name0, timeout=10)


def s6(ctx):
    """nom d'un teleporteur : celui qu'un joueur lui donne arrive chez l'autre, avec le registre qui relie les teleporteurs
    Ce que le banc ne joue pas comme un joueur : la saisie ; il fait ce que fait la validation (id puis teleports.SetID)"""
    tp = first_id("Teleporter")
    if not check(f"le jeu a un teleporteur ({tp})", bool(tp)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        t = furniture(uid, f'ThingGen.Create("{tp}")')
        try:
            name = f"porte-{key}"
            ev(port, f'var t = (TraitTeleporter){thing(t)}.trait; t.id = "{name}"; EClass.game.teleports.SetID(t, EClass._zone.uid); "ok"')
            read = lambda p: ev(p, f'var t = {thing(t)}; if (t == null) return "absent"; var i = EClass.game.teleports.items.TryGetValue(t.uid); '  # noqa: E731
                                   'return ((TraitTeleporter)t.trait).id + "/" + (i == null ? "" : i.id);')
            check(cond=eventually(lambda: read(other) == f"{name}/{name}", timeout=10),
                  label=f"{who} nomme le teleporteur : l'autre joueur a le nom et le registre ({read(other)})")
        finally:
            ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); "ok"')


def s7(ctx):
    """reglages d'un coffre de la base (priorite, pas de pourri, categories, filtre, drapeaux) : lus par l'autre jeu, dans les deux sens ;
    la mise en page de la fenetre reste a chacun ; l'objet pourri est refuse chez l'host (ce que verifient ses habitants qui rangent)
    Ce que le banc ne joue pas comme un joueur : il ne clique pas les curseurs et les cases du sous-menu, il pose les valeurs que leurs
    lambdas posent (window.saveData), puis ferme le vrai menu (UIContextMenu.Hide, par ou passe onDestroy) ; la boite de saisie du
    filtre (Dialog.InputName), le bouton de collage, les boutons d'autodump et la fermeture du menu d'un clic a cote ne sont pas joues ;
    ce ne sont pas les habitants de l'host qui rangent (AI_Haul) mais Zone.FindSharedContainer appele a la main"""
    if ev(H, 'EClass._zone.IsPCFaction.ToString()') != "True":
        print("    [SAUTE] S7 : la carte n'est pas une base, les reglages de rangement n'y servent pas")
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        t = furniture(uid, extra="t.c_lockLv = 0;")
        win = f'LayerInventory.listInv.Find(l => l.invs[0].owner.Container == {thing(t)})'
        rules = lambda p: ev(p, f'var d = {thing(t)}.c_windowSaveData; return d == null ? "aucun" : d.priority + "/" + d.noRotten + "/" + (int)d.flag + "/" + d.sharedType + "/" '  # noqa: E731
                                '+ d.filter + "/" + string.Join(",", d.cats.OrderBy(i => i));')
        # ce qu'un joueur regle sur le coffre lui-meme : nom, icone, taille et tri de sa grille (retour du 2026-10-09 :
        # « les parametres de coffres modifies par un invite ne sont pas sauvegardes »)
        look = lambda p: ev(p, f'var t = {thing(t)}; var d = t.c_windowSaveData; return d == null ? "aucun" : t.c_altName + "/" + t.c_indexContainerIcon + "/" '  # noqa: E731
                               '+ d.size + "/" + d.columns + "/" + d.alwaysSort + "/" + d.sort_ascending + "/" + d.excludeDump;')
        # un objet que le rangement de l'host pose dans ce coffre (ou pas) : Zone.FindSharedContainer, comme AI_Haul
        goes_in = lambda decay: ev(H, f'var m = ThingGen.Create("meat"); for (var i = 0; i < 40 && !m.Name.Contains("meat"); i++) {{ m.Destroy(); m = ThingGen.Create("meat"); }} m.decay = {decay}; var c = EClass._zone.FindSharedContainer(m); '  # noqa: E731
                                      f'var r = (c != null && c.uid == {t}) + " " + m.Name + " cat " + m.category.id + " -> " + (c == null ? "aucun coffre" : c.Name + " " + c.uid); m.Destroy(); return r;')
        try:
            x, z = (int(v) for v in ev(H, f'var t = {thing(t)}; return t.pos.x + "," + t.pos.z;').split(","))
            awake(port)
            opened_by = use_menu(port, (x, z), 'i.act is DynamicAct d && d.id == "actContainer"')
            log(f"{who} ouvre le coffre : {opened_by}")
            if not eventually(lambda: ev(port, f'({win} != null).ToString()') == "True", timeout=8):
                log(f"{who} : le clic n'a pas ouvert le coffre, l'ouverture du jeu est appelee (TraitContainer.TryOpen)")
                ev(port, f'((TraitContainer){thing(t)}.trait).TryOpen(); "ok"')
            if not check(f"{who} : la fenetre du coffre est ouverte chez lui", eventually(lambda: ev(port, f'({win} != null).ToString()') == "True", timeout=10)):
                continue
            # le vrai menu : le bouton de tri le fabrique ; on fait ce que font ses entrees (elles changent window.saveData), puis on le ferme
            ev(port, f'{win}.invs[0].window.buttonSort.onClick.Invoke(); "ok"')
            ev(port, f'var d = {win}.invs[0].window.saveData; d.priority = 7; d.noRotten = true; d.sharedType = ContainerSharedType.Shared; '
                     'd.flag |= ContainerFlag.weapon; d.filter = "meat"; d.cats.Add(EClass.sources.categories.map["food"].uid); d.size = 5; "ok"')
            ev(port, 'EClass.ui.contextMenu.currentMenu.Hide(); "ok"')    # c'est la fermeture qui envoie (a l'image suivante)
            want = rules(port)
            check(cond=eventually(lambda: rules(other) == want and rules(H) == want and rules(A) == want, timeout=10),
                  label=f"{who} regle le coffre : les deux jeux disent pareil (voulu {want}, host {rules(H)}, invite {rules(A)})")
            # nom et icone : poses comme le font la boite de saisie et le menu des icones, fenetre ouverte, menu ferme
            ev(port, f'var t = {thing(t)}; var d = {win}.invs[0].window.saveData; t.c_altName = "Coffre de {key}"; t.c_indexContainerIcon = 3; '
                     'd.columns = 4; d.alwaysSort = true; d.sort_ascending = true; "ok"')
            mine = look(port)
            check(cond=eventually(lambda: look(H) == mine and look(A) == mine, timeout=10),
                  label=f"{who} nomme le coffre, change son icone, sa taille et son tri : les deux jeux disent pareil (voulu {mine}, host {look(H)}, invite {look(A)})")
            check(f"{who} : le nom est celui qu'il a donne ({mine})", mine.startswith(f"Coffre de {key}/3/5/4/True/True"))
            check(f"{who} : les regles de rangement n'ont pas bouge ({rules(other)})", rules(other) == want)
            # ce que fait un habitant de l'host : l'objet pourri est refuse par ce coffre, un frais est accepte (priorite 7, filtre « meat »)
            rotten, fresh = goes_in(99999), goes_in(0)
            check(f"{who} : l'host refuse l'objet pourri pour ce coffre ({rotten})", rotten.startswith("False"))
            check(f"{who} : l'host range un objet frais dans ce coffre ({fresh})", fresh.startswith("True"))
        finally:
            close_layers()
            ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [s1, s2, s3, s4, s5, s6, s7]
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
                print(f"    capture {name} : {shot(f'setting-{step.__name__}-{name}', port)}")
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
