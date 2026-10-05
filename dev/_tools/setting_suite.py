"""Reglages d'un objet de la carte faits par un joueur (conseil 4) : ils arrivent chez l'autre joueur, dans les deux sens.
Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/setting_suite.py            # ou --only s1,s3

S1  note ecrite sur un meuble.   S2  etiquette de vente (posee puis retiree, avec l'etiquette tenue en main).
S3  lit : le reclamer, en changer le type.   S4  politiques de la base (vraie fenetre, vrai clic sur la politique).
Avant : chaque jeu ne changeait que sa copie (l'host, qui fait vivre les habitants et sauvegarde, ne voyait rien).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import awake, both, chara, first_id, give, use_held  # noqa: E402
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [s1, s2, s3, s4]
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
