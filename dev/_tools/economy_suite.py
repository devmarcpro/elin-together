"""Expedition par joueur (coffre d'expedition) : host + 2 clients A, B.

    python _tools/economy_suite.py            # relance tout (mp_test --clients 2) puis les scenarios
    python _tools/economy_suite.py --reuse    # sur host + 2 clients deja connectes dans la Prairie

E1  A, B et l'host mettent chacun des seaux dans le coffre : marques par deposant, jamais fusionnes
E2  vente du matin : chacun est paye pour les siens (argent, rapport, totaux), le coffre est vide
E3  A en voyage seul : son coffre est vide (copie), ce qu'il y depose arrive chez l'host ; il est paye la-bas ;
    la vente ne se fait pas dans sa copie (pas d'argent en double)
E4  B invite de A depose : paye a son retour chez l'host
E5  option decochee : tout va a l'host, comme avant
"""
import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import ROOT, log, shot, state  # noqa: E402
from shared_suite import A, B, H, settled, with_host  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, check, ev, eventually, move, scan_logs, wait  # noqa: E402

GOODS = "bucket"
BOX = "EClass.game.cards.container_shipping"


def money(port, uid=None):
    """Argent du joueur local, ou (vu de ce jeu) du perso uid."""
    who = "EClass.pc" if uid is None else f"EClass.game.cards.globalCharas.Find({uid})"
    return int(ev(port, f'{who}.GetCurrency("money").ToString()'))


def give(uid, num):
    """L'host donne des marchandises au joueur (sur sa carte)."""
    ev(H, f'EClass.game.cards.globalCharas.Find({uid}).AddThing(ThingGen.Create("{GOODS}").SetNum({num})); "ok"')


def ship(port, num=None):
    """Le joueur met ses marchandises dans le coffre d'expedition (comme en le faisant glisser dedans)."""
    split = "" if num is None else f'if (t.Num > {num}) t = t.Split({num}); '
    return ev(port, f'var t = EClass.pc.things.Find("{GOODS}"); if (t == null) return "none"; {split}'
                    f'{BOX}.AddThing(t); "ok"')


def box(port):
    """Contenu du coffre : liste triee de "deposant:nombre"."""
    r = ev(port, f'string.Join(";", {BOX}.things.Where(t => t.id == "{GOODS}").Select(t => t.GetInt("emp_shipper") + ":" + t.Num)'
                 '.OrderBy(x => x))')
    return r.split(";") if r else []


def value(shipper):
    """Ce que rapportera la vente des lots de ce deposant (les seaux n'ont pas tous la meme matiere, donc pas le meme prix)."""
    return int(ev(H, f'{BOX}.things.Where(t => t.GetInt("emp_shipper") == {shipper})'
                     '.Sum(t => (long)t.GetPrice(CurrencyType.Money, true, PriceType.Shipping) * t.Num).ToString()'))


def sell():
    ev(H, 'EClass.world.date.ShipGoods(); "ok"')


def e1(ctx):
    ctx["a"], ctx["b"] = state(A)["pc"]["uid"], state(B)["pc"]["uid"]
    give(ctx["a"], 2)
    give(ctx["b"], 2)
    ev(H, f'EClass.pc.AddThing(ThingGen.Create("{GOODS}").SetNum(1)); "ok"')
    wait(lambda: ev(A, f'(EClass.pc.things.Find("{GOODS}") != null).ToString()') == "True"
         and ev(B, f'(EClass.pc.things.Find("{GOODS}") != null).ToString()') == "True", "A et B ont recu les seaux", timeout=30)
    ship(A)
    ship(B)
    ship(H)
    expected = sorted([f'{ctx["a"]}:2', f'{ctx["b"]}:2', "1:1"])
    check(f"host : 3 lots separes, marques par deposant ({expected})", eventually(lambda: box(H) == expected))
    check("A et B voient les memes 3 lots", eventually(lambda: box(A) == expected and box(B) == expected))


def e2(ctx):
    before = {"h": money(H), "a": money(A), "b": money(B)}
    va, vb, vh = value(ctx["a"]), value(ctx["b"]), value(1)
    log(f"valeur des lots : A {va}, B {vb}, host {vh}")
    reports = int(ev(A, 'EClass.player.shippingResults.Count.ToString()'))
    sell()
    check(f"vente : A touche ses 2 seaux (+{va})", eventually(lambda: money(A) == before["a"] + va))
    check(f"vente : B touche ses 2 seaux (+{vb})", eventually(lambda: money(B) == before["b"] + vb))
    check(f"vente : l'host touche son seau, pas ceux des autres (+{vh})", money(H) == before["h"] + vh)
    check("vente : l'host voit le meme argent chez A et B", money(H, ctx["a"]) == money(A) and money(H, ctx["b"]) == money(B))
    check("vente : le coffre est vide partout", eventually(lambda: box(H) == [] and box(A) == [] and box(B) == []))
    check("A recoit son propre rapport d'expedition (2 seaux)",
          eventually(lambda: int(ev(A, 'EClass.player.shippingResults.Count.ToString()')) == reports + 1)
          and int(ev(A, 'EClass.player.shippingResults.LastItem().GetIncome().ToString()')) == va)
    total = int(ev(H, 'EClass.player.stats.shipMoney.ToString()'))
    check(f"total d'expedition commun : A et B voient celui de l'host ({total})",
          eventually(lambda: int(ev(A, 'EClass.player.stats.shipMoney.ToString()')) == total
                     and int(ev(B, 'EClass.player.stats.shipMoney.ToString()')) == total) and total >= va + vb + vh)


def e3(ctx):
    ev(H, f'EClass.pc.AddThing(ThingGen.Create("{GOODS}").SetNum(1)); "ok"')
    ship(H)
    give(ctx["b"], 1)  # pour E4
    wait(lambda: box(A) == ["1:1"], "A voit le seau de l'host dans le coffre", timeout=30)
    move(A, VERNIS)
    wait(settled(A, VERNIS, away=True, guest=False), "A seul a Vernis")
    time.sleep(3)
    check("A en voyage : sa copie du coffre est vide (pas d'objets a ressortir en double)",
          ev(A, f'{BOX}.things.Count.ToString()') == "0")
    before = {"h": money(H), "a": money(A)}
    ev(A, 'EClass.world.date.ShipGoods(); "ok"')
    check("A en voyage : la vente du matin ne se fait pas dans sa copie", money(A) == before["a"])
    ev(A, f'EClass.pc.AddThing(ThingGen.Create("{GOODS}").SetNum(3)); "ok"')
    ship(A)
    expected = sorted(["1:1", f'{ctx["a"]}:3'])
    check(f"A depose 3 seaux depuis Vernis : ils arrivent dans le coffre de l'host ({expected})",
          eventually(lambda: box(H) == expected))
    check("A : les seaux ont quitte son sac et sa copie du coffre",
          ev(A, f'(EClass.pc.things.Find("{GOODS}") == null && {BOX}.things.Count == 0).ToString()') == "True")
    va, vh = value(ctx["a"]), value(1)
    sell()
    check(f"vente : A est paye a Vernis (+{va})", eventually(lambda: money(A) == before["a"] + va))
    check(f"vente : l'host touche son seau seulement (+{vh})", money(H) == before["h"] + vh)
    ctx["a_money"] = money(A)


def e4(ctx):
    move(B, VERNIS)
    wait(settled(B, VERNIS, away=True, guest=True, zone_session="Client"), "B invite de A", timeout=240)
    time.sleep(3)
    before = money(B)
    ship(B)
    expected = [f'{ctx["b"]}:1']
    check(f"B (invite) depose 1 seau : il arrive chez l'host a son nom ({expected})", eventually(lambda: box(H) == expected))
    vb = value(ctx["b"])
    sell()
    time.sleep(5)
    check("vente : B, invite, n'est pas encore paye", money(B) == before)
    move(B, HOME)
    with_host(B)
    check(f"B rentre chez l'host : il touche sa vente (+{vb})", eventually(lambda: money(B) == before + vb, timeout=30))
    move(A, HOME)
    with_host(A, B)
    check("A rentre : l'argent gagne en voyage est toujours la", eventually(lambda: money(H, ctx["a"]) == ctx["a_money"]))


def set_option(value):
    """Coche ou decoche « Expedition par joueur » chez l'host (comme la case des reglages), regles renvoyees aux clients."""
    ev(H, 'var entry = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Server"), '
          '"PlayerShipping").GetValue(null); '
          f'HarmonyLib.AccessTools.Property(entry.GetType(), "Value").SetValue(entry, {str(value).lower()}); '
          'HarmonyLib.Traverse.Create(ElinTogether.Net.NetSession.Instance.Transport).Method("UpdateRemoteSessionRules").GetValue(); "ok"')


def e5(ctx):
    set_option(False)
    time.sleep(3)
    try:
        give(ctx["a"], 2)
        wait(lambda: ev(A, f'(EClass.pc.things.Find("{GOODS}") != null).ToString()') == "True", "A a recu les seaux", timeout=30)
        before = {"h": money(H), "a": money(A)}
        ship(A)
        check("option decochee : le depot n'est pas marque", eventually(lambda: box(H) == ["0:2"]))
        v = value(0)
        sell()
        time.sleep(3)
        check(f"option decochee : l'host touche tout (+{v}), A rien", money(H) == before["h"] + v and money(A) == before["a"])
    finally:
        set_option(True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if not a.reuse:
        subprocess.run([sys.executable, str(ROOT / "_tools" / "mp_test.py"), "--clients", "2"], check=True)

    ctx = {}
    steps = [e1, e2, e3, e4, e5]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {ex}", False)
            for name, port in (("host", H), ("A", A), ("B", B)):
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
