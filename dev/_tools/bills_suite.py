"""Les factures du monde (conseil 10, point v ; faits : dev/PLAN_factures.md). Test court, sur des instances deja
lancees (host + 1 client, tous les deux a la Prairie), finit a la Prairie.

    python _tools/mp_test.py
    python _tools/bills_suite.py            # ou --only c1,c3,p1

Retour d'une vraie partie (0.26.506) : « la base a recu 2 bills, une de 500 et une de 35 ». Les factures sont comptees
par IDENTIFIANT (bill_tax, bill), pas par compteur : en route (listPackage), par terre, dans les conteneurs, dans les
sacs des deux jeux.

C1  fin de mois passee par l'host, l'invite present : UNE facture d'impot en tout (+1 bill_tax, +0 bill)
C2  fin de mois passee par l'invite seul a Vernis : UNE facture d'impot en tout, chez l'host
C3  trois objets dans le coffre de livraison, 5 h passees : UNE facture de livraison de 35 (20 + 5 x 3), +0 impot ;
    deposes par l'invite puis par l'host. Le test affiche aussi le NOM que le jeu donne aux deux objets
P1  l'invite met la facture d'impot dans le coffre des impots : 500 de moins dans SA bourse (les deux jeux la voient),
    facture detruite, compteur de l'host a moins un, la ligne « X a paye » dans les deux jeux
    (ROUGE avant GuestPaysBillPatch : « mauvaise idee », l'invite ne paie rien)
P1h meme chose par l'host (temoin : deja bon)
P2  deux joueurs paient en meme temps, un seul impot a payer (deux factures, compteur a 1) : une seule est payee, l'autre
    joueur garde son or ; aucun or perdu ni cree

Ce que le banc ne joue pas comme un joueur :
- la date est posee au 30 a 23 h 50 (jour, heure, minute) dans les DEUX jeux, puis le temps passe par GameDate.AdvanceMin
  (ce que fait une attente) : le monde avance d'environ un jour et d'un mois, a chaque essai ;
- C2 : l'invite va a Vernis par MoveZone direct (world_suite.away), comme K2 ;
- C3 : le depot est InvOwner.Transaction.Process sur le bouton de l'objet du sac et la case libre de la fenetre du
  coffre de livraison (ce que fait le lacher), mais la fenetre est ouverte par LayerInventory.CreateContainer
  (container_deliver), pas par un clic sur un coffre de livraison de la carte ; l'invite est a la Prairie, pas de loin ;
- P1, P1h, P2 : la facture est fabriquee par ThingGen.CreateBill (ce que fait la fin du mois) et mise dans le sac du
  joueur ; le coffre « chest_tax » est pose par le banc ; le clic sur le coffre est trait.OnUse (TraitTaxChest) ; le
  lacher est InvOwner.Transaction.Process entre le bouton de la facture dans le sac et la case de la fenetre (comme
  bank_suite) ; l'or du joueur est mis par ModCurrency ;
- si la politique 2705 (payer les factures par la banque) est active, la facture est payee a sa naissance : C1 a C3
  le disent et ne peuvent pas compter ;
- la ligne « X a paye » est lue dans BillPayDelta.LastLine (la derniere ligne montree), pas lue a l'ecran ;
- P2 : les deux gestes partent de deux fils du banc au meme instant, pas de deux machines ; le delai reseau est nul ;
- le banc detruit toutes les factures du monde de test avant et apres chaque etape et remet les deux compteurs a leur valeur
  de depart (monde de test seulement, pas une vraie partie) ;
- ecrit sans avoir tourne.
"""
import argparse
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bank_suite import deposit, fund, win  # noqa: E402
from guest_suite import awake, chara, close_layers, give_made  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402
from world_suite import away, home, jump  # noqa: E402

H, A = 27551, 27552
DELIV = "EClass.game.cards.container_deliver"
LINE = 'HarmonyLib.AccessTools.Field(HarmonyLib.AccessTools.TypeByName("ElinTogether.Models.BillPayDelta"), "LastLine")'
ALL = ('System.Func<Card, System.Collections.Generic.IEnumerable<Card>> f = null; f = c => new[] { c }.Concat(c.things.SelectMany(x => f(x))); '
       'var all = new System.Collections.Generic.List<Card>(); all.AddRange(EClass.game.cards.listPackage); all.AddRange(EClass._map.things); '
       'all.AddRange(EClass._map.charas); var bills = all.SelectMany(f).Where(c => c.id == "bill_tax" || c.id == "bill").ToList(); ')


def count(port, bill_id):
    """Nombre de factures de ce type que ce jeu connait (en route, par terre, dans les conteneurs, dans les sacs)."""
    return int(ev(port, ALL + f'return bills.Where(c => c.id == "{bill_id}").Sum(c => c.Num).ToString();'))


def amounts(port, bill_id):
    return ev(port, ALL + f'return string.Join(",", bills.Where(c => c.id == "{bill_id}").Select(c => c.c_bill));')


def counters(port=H):
    """(factures d'impot impayees, factures de livraison impayees) du monde, vues par ce jeu."""
    return tuple(int(v) for v in ev(port, 'EClass.player.taxBills + "," + EClass.player.unpaidBill').split(","))


def names():
    """Le NOM que le jeu donne aux deux objets : (source, objet fabrique) pour chacun."""
    return ev(H, 'var a = ThingGen.Create("bill_tax"); var b = ThingGen.Create("bill"); '
                 'var r = EClass.sources.things.map["bill_tax"].GetName() + "|" + a.Name + "|" + EClass.sources.things.map["bill"].GetName() + "|" + b.Name; '
                 'a.Destroy(); b.Destroy(); return r;').split("|")


def reset(base):
    """Remet le monde de l'host comme il etait : les factures du test detruites, les compteurs au depart."""
    ev(H, ALL + 'bills.ForEach(c => c.Destroy()); EClass.game.cards.listPackage.RemoveAll(c => c.isDestroyed); '
                f'EClass.player.taxBills = {base[0]}; EClass.player.unpaidBill = {base[1]}; "ok"')


def set_date(day, hour, minute):
    for p in (H, A):
        ev(p, f'var d = EClass.world.date; d.day = {day}; d.hour = {hour}; d.min = {minute}; "ok"')


def bank_pays():
    return ev(H, 'EClass.pc.homeBranch.policies.IsActive(2705).ToString()') == "True"


def c1(ctx):
    """fin de mois par l'host, l'invite present : une seule facture d'impot"""
    base = counters()
    log(f"noms du jeu (source | objet fabrique | source | objet fabrique) : {' | '.join(names())}")
    named = names()
    check(f"les deux objets ont deux noms differents dans le jeu (« {named[0]} » et « {named[2]} »)", named[0] != named[2])
    t0, d0 = count(H, "bill_tax"), count(H, "bill")
    ta0, da0 = count(A, "bill_tax"), count(A, "bill")
    try:
        if not check("la politique « payer par la banque » est eteinte (sinon la facture est payee a sa naissance)", not bank_pays()):
            return
        set_date(30, 23, 50)
        jump(H, 20)
        time.sleep(3)
        t1, d1 = count(H, "bill_tax"), count(H, "bill")
        log(f"factures d'impot {t0} -> {t1} ({amounts(H, 'bill_tax')}), de livraison {d0} -> {d1} ; compteurs {base} -> {counters()} ; invite : {ta0} -> {count(A, 'bill_tax')}")
        check(f"fin de mois par l'host : UNE facture d'impot en tout (+{t1 - t0})", t1 - t0 == 1)
        check(f"et aucune facture de livraison (+{d1 - d0})", d1 == d0)
        check(f"l'invite n'en voit pas plus que l'host ({count(A, 'bill_tax') - ta0} contre {t1 - t0})", count(A, "bill_tax") - ta0 <= 1)
        check(f"le compteur de l'host a monte de un ({base[0]} -> {counters()[0]})", counters()[0] == base[0] + 1)
    finally:
        reset(base)


def c2(ctx):
    """fin de mois par l'invite seul a Vernis : une seule facture d'impot, chez l'host"""
    base = counters()
    t0 = count(H, "bill_tax")
    try:
        if not check("la politique « payer par la banque » est eteinte", not bank_pays()):
            return
        away()
        set_date(30, 23, 50)
        jump(A, 20)
        time.sleep(5)
        t1 = count(H, "bill_tax")
        log(f"factures d'impot chez l'host {t0} -> {t1} ({amounts(H, 'bill_tax')}) ; compteurs {base} -> {counters()} ; chez l'invite {count(A, 'bill_tax')}")
        check(f"fin de mois par l'invite seul : UNE facture d'impot en tout, chez l'host (+{t1 - t0})", t1 - t0 == 1)
        check(f"aucune dans la copie de l'invite ({count(A, 'bill_tax')})", count(A, "bill_tax") == 0)
    finally:
        home()
        reset(base)


def open_window(port, box):
    if ev(port, f'({win(box)} != null).ToString()') == "True":
        return
    if ev(port, '(LayerInventory.listInv.Any(q => q.mainInv)).ToString()') != "True":
        ev(port, 'EClass.ui.OpenFloatInv(true); "ok"')
        time.sleep(1.5)
    ev(port, f'LayerInventory.CreateContainer({box}); "ok"')
    time.sleep(1.5)


def c3(ctx):
    """trois objets livres par le coffre de livraison : une facture de 35, pas d'impot"""
    base = counters()
    for who, key in (("l'invite", "a"), ("l'host", "h")):
        port, uid = ctx[key]
        close_layers()
        reset(base)
        ev(H, f'foreach (var t in {DELIV}.things.ToList()) t.Destroy(); "ok"')
        try:
            if not check(f"{who} : la politique « payer par la banque » est eteinte", not bank_pays()):
                continue
            ids = ("log", "bucket", "potion_empty")
            for item in ids:
                give_made(ctx, key, f'var t = ThingGen.Create("{item}"); t.SetNum(1);')
            open_window(port, DELIV)
            sent = [deposit(port, DELIV, item, 1) for item in ids]
            check(f"{who} depose ses trois objets dans le coffre de livraison ({sent})", all(r == "ok" for r in sent))
            check(f"le coffre de l'host en contient trois", eventually(lambda: int(ev(H, f"{DELIV}.things.Count.ToString()")) == 3, timeout=15))
            close_layers()
            set_date(4, 4, 50)
            t0, d0 = count(H, "bill_tax"), count(H, "bill")
            jump(H, 20)
            time.sleep(3)
            t1, d1 = count(H, "bill_tax"), count(H, "bill")
            log(f"{who} : factures d'impot {t0} -> {t1}, de livraison {d0} -> {d1} ({amounts(H, 'bill')}) ; compteurs {base} -> {counters()}")
            check(f"{who} : UNE facture de livraison (+{d1 - d0}), de 35 ({amounts(H, 'bill')})", d1 - d0 == 1 and amounts(H, "bill") == "35")
            check(f"{who} : et pas d'impot en plus (+{t1 - t0})", t1 == t0)
        finally:
            close_layers()
            reset(base)
            ev(H, 'foreach (var p in EClass.game.cards.listPackage.Where(p => p.things.Any(x => x.id == "log" || x.id == "bucket" || x.id == "potion_empty")).ToList()) p.Destroy(); '
                  'EClass.game.cards.listPackage.RemoveAll(p => p.isDestroyed); "ok"')


def say(port):
    return ev(port, f'(string){LINE}.GetValue(null)')


def open_tax_chest(port, chest):
    """Le clic sur le coffre des impots (trait.OnUse) ; la fenetre du sac est ouverte avant."""
    if ev(port, '(LayerInventory.listInv.Any(q => q.mainInv)).ToString()') != "True":
        ev(port, 'EClass.ui.OpenFloatInv(true); "ok"')
        time.sleep(1.5)
    ev(port, f'EClass._map.things.Find(m => m.uid == {chest}).trait.OnUse(EClass.pc); "ok"')
    return eventually(lambda: ev(port, '(LayerDragGrid.Instance != null).ToString()') == "True", timeout=10)


def drop_bill(port, bill):
    """Le lacher de la facture du sac sur la case de la fenetre (InvOwner.Transaction.Process)."""
    return ev(port, 'var g = LayerDragGrid.Instance; if (g == null) return "fenetre absente"; '
                    'var src = LayerInventory.listInv.SelectMany(q => q.GetComponentsInChildren<ButtonGrid>(true))'
                    f'.FirstOrDefault(b => b.card != null && b.card.uid == {bill} && b.card.GetRootCard() == EClass.pc); '
                    'if (src == null) return "bouton de la facture absent du sac"; '
                    'new InvOwner.Transaction(new DragItemCard.DragInfo(src), new DragItemCard.DragInfo(g.CurrentButton), 1).Process(); return "ok";')


def tax_chest(uid):
    chest = int(ev(H, 'var t = ThingGen.Create("chest_tax"); '
                      f'EClass._zone.AddCard(t, {chara(H, uid)}.pos.GetNearestPoint(false, false, false, true)).Install(); return t.uid.ToString();'))
    for p in (H, A):
        eventually(lambda: ev(p, f'(EClass._map.things.Find(m => m.uid == {chest}) != null).ToString()') == "True", timeout=10)
    return chest


def gold(port, uid):
    return int(ev(port, f'var c = {chara(port, uid)}; return c == null ? "-1" : c.GetCurrency("money").ToString();'))


def exists(port, bill):
    return ev(port, f'(EClass._map.things.Find(m => m.uid == {bill}) != null || EClass._map.charas.Any(c => c.things.Find(x => x.uid == {bill}) != null)).ToString()') == "True"


def pays(ctx, who, key):
    """Le joueur met la facture d'impot dans le coffre des impots."""
    port, uid = ctx[key]
    close_layers()
    base = counters()
    reset(base)
    chest = 0
    try:
        bill = give_made(ctx, key, 'var t = ThingGen.CreateBill(500, true);')
        bill_name = ev(H, f'EClass._map.charas.SelectMany(c => c.things).First(t => t.uid == {bill}).Name')
        log(f"{who} : facture {bill} : « {bill_name} » ; compteur {base[0]} -> {counters()[0]}")
        fund(port, 1500)
        chest = tax_chest(uid)
        g0 = gold(port, uid)
        tax0 = counters()[0]
        ev(H, f'{LINE}.SetValue(null, ""); "ok"')
        ev(A, f'{LINE}.SetValue(null, ""); "ok"')
        awake(port)
        opened = open_tax_chest(port, chest)
        if not check(f"{who} : la fenetre des impots s'ouvre chez lui (comme le clic sur le coffre)", opened):
            return
        r = drop_bill(port, bill)
        check(f"{who} depose la facture dans la fenetre ({r})", r == "ok")
        check(f"{who} : sa bourse a 500 de moins ({g0} -> {gold(port, uid)})", eventually(lambda: gold(port, uid) == g0 - 500, timeout=15))
        if key == "a":
            check(f"{who} : l'host voit la meme bourse ({gold(H, uid)})", eventually(lambda: gold(H, uid) == g0 - 500, timeout=15))
        check(f"{who} : la facture a disparu, chez l'host et chez l'invite",
              eventually(lambda: not exists(H, bill) and not exists(A, bill), timeout=15))
        check(f"{who} : le compteur d'impots de l'host est a moins un ({tax0} -> {counters()[0]})", eventually(lambda: counters()[0] == tax0 - 1, timeout=15))
        name = ev(H, f'{chara(H, uid)}.NameSimple')
        for label, p in (("chez l'host", H), ("chez l'invite", A)):
            line = ev(p, f'(string){LINE}.GetValue(null)')
            check(f"{who} : la ligne s'affiche {label} : « {line} »", eventually(lambda p=p: name in say(p) and "500" in say(p), timeout=10))
        time.sleep(3)
        check(f"{who} : rien en double ensuite (bourse {gold(port, uid)}, compteur {counters()[0]})",
              gold(port, uid) == g0 - 500 and counters()[0] == tax0 - 1)
    finally:
        close_layers()
        ev(H, f'var t = EClass._map.things.Find(m => m.uid == {chest}); if (t != null) t.Destroy(); "ok"')
        reset(base)


def p1(ctx):
    """l'invite paie l'impot avec son or"""
    pays(ctx, "l'invite", "a")


def p1h(ctx):
    """l'host paie l'impot avec son or (temoin)"""
    pays(ctx, "l'host", "h")


def p2(ctx):
    """deux joueurs paient au meme instant un impot qui ne tient que pour un : l'autre garde son or"""
    close_layers()
    base = counters()
    reset(base)
    chest = 0
    try:
        bills = {k: give_made(ctx, k, 'var t = ThingGen.CreateBill(500, true);') for k in ("h", "a")}
        ev(H, 'EClass.player.taxBills = 1; "ok"')
        for k in ("h", "a"):
            fund(ctx[k][0], 1500)
        chest = tax_chest(ctx["a"][1])
        before = {k: gold(ctx[k][0], ctx[k][1]) for k in ("h", "a")}
        for k in ("h", "a"):
            awake(ctx[k][0])
            if not check(f"la fenetre des impots s'ouvre chez {k}", open_tax_chest(ctx[k][0], chest)):
                return
        results = {}

        def go(k):
            results[k] = drop_bill(ctx[k][0], bills[k])

        threads = [threading.Thread(target=go, args=(k,)) for k in ("h", "a")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        time.sleep(5)
        after = {k: gold(ctx[k][0], ctx[k][1]) for k in ("h", "a")}
        delta = {k: after[k] - before[k] for k in after}
        log(f"gestes {results} ; or {before} -> {after} ; compteur 1 -> {counters()[0]} ; factures restantes {count(H, 'bill_tax')}")
        check(f"un seul des deux a paye 500, l'autre garde tout son or ({delta})", sorted(delta.values()) == [-500, 0])
        check(f"aucun or perdu ni cree : l'ensemble a perdu exactement 500 ({sum(delta.values())})", sum(delta.values()) == -500)
        check(f"le compteur de l'host a baisse UNE fois (1 -> {counters()[0]})", counters()[0] == 0)
    finally:
        close_layers()
        ev(H, f'var t = EClass._map.things.Find(m => m.uid == {chest}); if (t != null) t.Destroy(); "ok"')
        reset(base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [c1, c2, c3, p1, p1h, p2]
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
                print(f"    capture {name} : {shot(f'bills-{step.__name__}-{name}', port)}")
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
