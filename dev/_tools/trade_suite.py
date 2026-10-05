"""Echange entre joueurs. Test court, sur des instances deja lancees (host + 1 client).

    python _tools/mp_test.py
    python _tools/trade_suite.py     # ~2 minutes

R1  A invite l'host, l'host accepte ; A met une torche et 50 pieces, l'host met deux planches ; les deux confirment :
    les objets et l'or changent de mains, rien n'existe en double, les totaux sont conserves
R2  changer son offre apres la confirmation de l'autre efface cette confirmation
R3  s'eloigner annule l'echange, rien n'a bouge
R4  A recoit des planches alors qu'il en a deja dans un sac : son jeu les voit toutes, comme l'host
R5  A confirme et s'equipe de l'objet offert au meme instant : l'objet est bien a l'host, pas repris
R6  boule de punition (non lachable) : refuse a la confirmation, dans les deux sens, rien n'a bouge, motif emp_trade_nodrop
R7  propriete de PNJ : meme chose, motif emp_trade_npcprop
R8  cadeau recu : meme chose, motif emp_trade_gifted
R9  objet lie a un personnage : meme chose, motif emp_trade_bound
R10 sac plein de celui qui recoit (dans les deux sens) : refuse avant tout transfert (motif emp_trade_full, rien n'a bouge,
    rien par terre) ; une case libre de plus et l'echange passe
R11 objet propose puis equipe avant la confirmation (dans les deux sens) : annule avec le motif emp_trade_equipped
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
T = "ElinTogether.Helper.PlayerTrade"


def give(chara_uid, item, num=1):
    return int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {chara_uid}); var t = ThingGen.Create("{item}").SetNum({num}); '
                     'return c.AddThing(t).uid.ToString();'))  # la pile qui le contient, s'il s'est empile


def has(port, chara_uid, thing_uid):
    """Nombre d'exemplaires de cet objet dans le sac de ce personnage, vu par ce jeu (0 s'il n'y est pas)."""
    return int(ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {chara_uid}); var t = c.things.Find({thing_uid}); '
                        'return (t == null ? 0 : t.Num).ToString();'))


def count_in_bag(port, chara_uid, item):
    return int(ev(port, f'EClass._map.charas.Find(x => x.uid == {chara_uid}).things.Where(t => t.id == "{item}").Sum(t => t.Num).ToString()'))


def count_deep(port, chara_uid, item):
    """Comme count_in_bag, en comptant aussi ce qui est range dans les sacs."""
    return int(ev(port, f'EClass._map.charas.Find(x => x.uid == {chara_uid}).things.List(t => t.id == "{item}", false).Sum(t => t.Num).ToString()'))


def count_id(port, item):
    """Exemplaires de ce type d'objet dans tous les sacs des joueurs et au sol, vus par ce jeu."""
    return int(ev(port, f'(EClass._map.things.Where(t => t.id == "{item}").Sum(t => t.Num) + EClass._map.charas.Where(c => c.IsPC || '
                        f'c.IsPCParty || c.GetBool("remote_chara")).Sum(c => c.things.Where(t => t.id == "{item}").Sum(t => t.Num))).ToString()'))


def money(port, chara_uid):
    return int(ev(port, f'EClass._map.charas.Find(x => x.uid == {chara_uid}).GetCurrency().ToString()'))


def describe(port):
    return ev(port, f'{T}.Describe()')


def together(h):
    """Met A a cote de l'host (un echange demande d'etre a 3 cases)."""
    ev(A, f'var p = EClass._map.charas.Find(x => x.uid == {h}).pos.GetNearestPoint(false, false); EClass.pc.Teleport(p, true, true); "ok"')
    time.sleep(3)


def open_trade(h):
    ev(A, f'{T}.Invite({h}); "ok"')
    check("A invite l'host : l'host recoit l'invitation", eventually(lambda: describe(H).startswith("Invited"), timeout=10))
    ev(H, 'foreach (var l in EClass.ui.layers.OfType<Dialog>().ToList()) l.Close(); "ok"')
    ev(H, f'{T}.Accept(); "ok"')
    check("l'host accepte : l'echange est ouvert des deux cotes",
          eventually(lambda: describe(H).startswith("Open") and describe(A).startswith("Open"), timeout=10))


def make(owner, item, mark=""):
    """Un exemplaire neuf (jamais empile) de cet objet dans le sac de ce personnage ; `mark` : du C# sur `t` (l'objet) et `c`
    (le personnage), execute apres l'ajout (un sac de joueur efface isNPCProperty/isGifted a l'ajout)."""
    uid = int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {owner}); var t = c.AddThing(ThingGen.Create("{item}"), false); '
                    f'{mark} return t.uid.ToString();'))
    check(f"l'objet {uid} ({item}) est dans le sac de {owner}, vu des deux jeux",
          eventually(lambda: has(H, owner, uid) == 1 and has(A, owner, uid) == 1, timeout=10))
    return uid


def destroy(owner, thing):
    ev(H, f'var t = EClass._map.charas.Find(x => x.uid == {owner}).things.Find({thing}); if (t != null) t.Destroy(); "ok"')


def offer_and_confirm(owner_port, thing, confirm_first=None):
    """L'echange est ouvert : le proprietaire met l'objet sur la table, puis les deux confirment (la seconde confirmation declenche
    l'echange). `confirm_first` : un code a lancer entre l'offre et les confirmations (par ex. s'equiper)."""
    ev(owner_port, f'{T}.Offer({thing}, 1); "ok"')
    check(f"l'objet {thing} est sur la table, vu des deux cotes",
          eventually(lambda: f"{thing}x1" in describe(H) and f"{thing}x1" in describe(A), timeout=10))
    if confirm_first:
        confirm_first()
    ev(A, f'{T}.Confirm(); "ok"')
    time.sleep(1)
    ev(H, f'{T}.Confirm(); "ok"')


def cancelled_with(key, label):
    """Les deux joueurs voient l'echange annule avec ce motif (texte `key`)."""
    good = eventually(lambda: all(describe(p).startswith("Cancelled") and key in describe(p) for p in (H, A)), timeout=10)
    check(cond=good, label=f"{label} : annule des deux cotes avec {key} (host : {describe(H)} / A : {describe(A)})")


def stayed(owner, other, thing, label):
    check(f"{label} : rien n'a bouge, l'objet est toujours chez son proprietaire, vu des deux jeux",
          has(H, owner, thing) == 1 and has(H, other, thing) == 0 and has(A, owner, thing) == 1 and has(A, other, thing) == 0)


def refusal(h, a, tag, what, item, mark, key):
    """Un objet que le jeu solo ne donne pas a un allie : refuse a la confirmation, dans les deux sens, avec son motif."""
    for owner, other, port, who in ((h, a, H, "host -> A"), (a, h, A, "A -> host")):
        log(f"--- {tag} {what}, {who}")
        thing = make(owner, item, mark)
        open_trade(h)
        offer_and_confirm(port, thing)
        cancelled_with(key, f"{tag} {what} ({who})")
        stayed(owner, other, thing, f"{tag} {what} ({who})")
        destroy(owner, thing)


def free_cells(port, chara_uid):
    """Cases libres du niveau superieur du sac, comptees comme le mod : ni equipe ni barre rapide, contre GridSize."""
    return int(ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {chara_uid}); '
                        'return (c.things.GridSize - c.things.Count(t => t.invY != 1 && !t.isEquipped)).ToString();'))


def fill(chara_uid, leave=0):
    """Remplit le sac de ce personnage d'objets non empiles jusqu'a ne laisser que `leave` cases libres ; renvoie leurs numeros."""
    n = free_cells(H, chara_uid) - leave
    out = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {chara_uid}); var s = ""; '
                f'for (var i = 0; i < {n}; i++) s += c.AddThing(ThingGen.Create("plank"), false).uid + ","; return s;')
    return [int(u) for u in out.split(",") if u]


def full_case(h, a, owner, receiver, who):
    """Le sac de celui qui recoit est plein : refuse avant tout transfert ; une case de plus et ca passe."""
    log(f"--- R10 sac plein, {who}")
    rname = "A" if receiver == a else "host"
    thing = make(owner, "torch")
    filler = fill(receiver)
    check(f"R10 ({who}) le sac de {rname} est plein ({len(filler)} objets ajoutes), vu des deux jeux",
          bool(filler) and eventually(lambda: free_cells(H, receiver) == 0 and has(A, receiver, filler[-1]) == 1, timeout=20))
    owner_port = A if owner == a else H
    torches = count_id(H, "torch")

    open_trade(h)
    offer_and_confirm(owner_port, thing)
    cancelled_with("emp_trade_full", f"R10 ({who}) sac plein")
    stayed(owner, receiver, thing, f"R10 ({who}) sac plein")
    now, free = count_id(H, "torch"), free_cells(H, receiver)
    check(cond=now == torches and free == 0,
          label=f"R10 ({who}) rien n'est tombe par terre ni n'est en depassement ({now} torches pour {torches}, {free} case libre)")

    last = filler.pop()
    destroy(receiver, last)
    check(f"R10 ({who}) une case libre de plus, vue des deux jeux",
          eventually(lambda: free_cells(H, receiver) == 1 and has(A, receiver, last) == 0, timeout=10))
    open_trade(h)
    offer_and_confirm(owner_port, thing)
    check(f"R10 ({who}) avec une case libre : echange fait", eventually(lambda: describe(H).startswith("Done") and describe(A).startswith("Done"), timeout=10))
    check(f"R10 ({who}) l'objet est arrive chez {rname}, vu des deux jeux",
          eventually(lambda: has(H, receiver, thing) == 1 and has(A, receiver, thing) == 1 and has(H, owner, thing) == 0, timeout=10))
    for u in filler:
        destroy(receiver, u)
    destroy(receiver, thing)
    eventually(lambda: free_cells(H, receiver) > 0 and has(A, receiver, thing) == 0, timeout=15)


def is_equipped(port, owner, thing):
    return ev(port, f'var t = EClass._map.charas.Find(x => x.uid == {owner}).things.Find({thing}); return (t != null && t.isEquipped).ToString();').lower() == "true"


def equipped_case(h, a, owner, other, who):
    """Un objet est propose, puis son proprietaire s'en equipe avant la confirmation du second : annule, et le motif le dit."""
    log(f"--- R11 objet equipe, {who}")
    owner_port, other_port = (A, H) if owner == a else (H, A)
    sword = int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {owner}); var id = EClass.sources.things.rows.First(r => r.category == "sword").id; '
                      'return c.AddThing(ThingGen.Create(id), false).uid.ToString();'))
    check(f"R11 ({who}) l'epee est dans le sac, vue des deux jeux", eventually(lambda: has(H, owner, sword) == 1 and has(A, owner, sword) == 1, timeout=10))
    open_trade(h)
    ev(owner_port, f'{T}.Offer({sword}, 1); "ok"')
    check(f"R11 ({who}) l'epee est sur la table", eventually(lambda: f"{sword}x1" in describe(H) and f"{sword}x1" in describe(A), timeout=10))
    ev(other_port, f'{T}.Confirm(); "ok"')
    check(f"R11 ({who}) l'autre a confirme", eventually(lambda: "ready=True" in describe(H), timeout=10))
    ev(owner_port, f'EClass.pc.body.Equip(EClass.pc.things.Find({sword})); "ok"')
    check(f"R11 ({who}) l'epee est equipee, vu par l'autorite", eventually(lambda: is_equipped(H, owner, sword), timeout=10))
    ev(owner_port, f'{T}.Confirm(); "ok"')
    cancelled_with("emp_trade_equipped", f"R11 ({who}) objet equipe")
    stayed(owner, other, sword, f"R11 ({who}) objet equipe")
    ev(owner_port, f'EClass.pc.body.Unequip(EClass.pc.things.Find({sword})); "ok"')
    eventually(lambda: not is_equipped(H, owner, sword), timeout=10)
    destroy(owner, sword)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    try:
        a, h = state(A)["pc"]["uid"], state(H)["pc"]["uid"]
        torch = give(a, "torch")
        plank = give(h, "plank", 3)
        ev(H, f'EClass._map.charas.Find(x => x.uid == {a}).ModCurrency(100); "ok"')
        check("A a recu une torche et 100 pieces", eventually(lambda: has(A, a, torch) >= 1 and money(A, a) >= 100, timeout=10))
        together(h)
        total = {"gold": money(H, a) + money(H, h), "torch": count_id(H, "torch"), "plank": count_id(H, "plank")}
        ma, mh = money(H, a), money(H, h)
        pa, ph = count_in_bag(H, a, "plank"), count_in_bag(H, h, "plank")
        ta, th = count_in_bag(H, a, "torch"), count_in_bag(H, h, "torch")

        log("--- R1")
        open_trade(h)
        ev(A, f'{T}.Offer({torch}, 1); {T}.SetGold(50); "ok"')
        ev(H, f'{T}.Offer({plank}, 2); "ok"')
        check("les deux offres sont sur la table, vues des deux cotes",
              eventually(lambda: f"{torch}x1" in describe(H) and f"{plank}x2" in describe(A) and "+50" in describe(H), timeout=10))
        ev(A, f'{T}.Confirm(); "ok"')
        time.sleep(1)
        ev(H, f'{T}.Confirm(); "ok"')
        check("les deux confirment : echange fait", eventually(lambda: describe(H).startswith("Done") and describe(A).startswith("Done"), timeout=10))
        check("une torche est passee de A a l'host (vu des deux jeux)",
              eventually(lambda: count_in_bag(H, h, "torch") == th + 1 and count_in_bag(A, h, "torch") == th + 1
                         and count_in_bag(H, a, "torch") == ta - 1 and count_in_bag(A, a, "torch") == ta - 1, timeout=10))
        check("A a 2 planches de plus, l'host 2 de moins",
              eventually(lambda: count_in_bag(A, a, "plank") == pa + 2 and count_in_bag(H, a, "plank") == pa + 2
                         and count_in_bag(H, h, "plank") == ph - 2, timeout=10))
        check("50 pieces sont passees de A a l'host",
              eventually(lambda: money(H, a) == ma - 50 and money(H, h) == mh + 50 and money(A, a) == ma - 50, timeout=10))
        check("rien n'est cree ni perdu (or, torches, planches)",
              money(H, a) + money(H, h) == total["gold"] and count_id(H, "torch") == total["torch"] and count_id(H, "plank") == total["plank"]
              and count_id(A, "torch") == total["torch"] and count_id(A, "plank") == total["plank"])

        log("--- R2")
        open_trade(h)
        ev(H, f'var t = EClass.pc.things.Where(x => x.id == "torch").First(); {T}.Offer(t.uid, 1); "ok"')
        time.sleep(1)
        ev(A, f'{T}.Confirm(); "ok"')
        check("A confirme l'offre de l'host", eventually(lambda: "ready=True" in describe(H), timeout=10))
        ev(H, f'{T}.SetGold(10); "ok"')
        check("l'host change son offre : la confirmation de A est effacee", eventually(lambda: "ready=True" not in describe(A), timeout=10))

        log("--- R3")
        before = (count_in_bag(H, h, "torch"), money(H, h), money(H, a))
        ev(A, 'var p = EClass.pc.pos.Copy(); p.x += 8; EClass.pc.Teleport(p.GetNearestPoint(false, false) ?? EClass.pc.pos, true, true); "ok"')
        check("A s'eloigne : echange annule des deux cotes",
              eventually(lambda: describe(H).startswith("Cancelled") and describe(A).startswith("Cancelled"), timeout=15))
        check("rien n'a bouge", (count_in_bag(H, h, "torch"), money(H, h), money(H, a)) == before)

        log("--- R4")
        together(h)
        # un sac dans le sac de A, avec une pile de bois dedans : le jeu de A empile dedans, pas celui de l'host
        ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {a}); var id = EClass.sources.things.rows.First(r => r.trait.Length > 0 '
              '&& r.trait[0] == "Container" && r.category == "container").id; var bag = ThingGen.Create(id); '
              'bag.AddThing(ThingGen.Create("log").SetNum(1)); c.AddThing(bag); "ok"')
        logs = give(h, "log", 3)
        check("A a un sac avec du bois dedans", eventually(lambda: count_deep(A, a, "log") >= 1, timeout=10))
        la = count_deep(H, a, "log")
        open_trade(h)
        ev(H, f'{T}.Offer({logs}, 2); "ok"')
        check("l'offre de bois est sur la table", eventually(lambda: f"{logs}x2" in describe(A), timeout=10))
        ev(A, f'{T}.Confirm(); "ok"')
        time.sleep(1)
        ev(H, f'{T}.Confirm(); "ok"')
        check("echange fait", eventually(lambda: describe(H).startswith("Done") and describe(A).startswith("Done"), timeout=10))
        check("A voit ses 2 buches de plus, comme l'host",
              eventually(lambda: count_deep(H, a, "log") == la + 2 and count_deep(A, a, "log") == la + 2, timeout=10))

        log("--- R5")
        together(h)
        sword = int(ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {a}); var id = EClass.sources.things.rows.First(r => r.category == "sword").id; '
                          'return c.AddThing(ThingGen.Create(id)).uid.ToString();'))
        check("A a recu une epee", eventually(lambda: has(A, a, sword) == 1, timeout=10))
        open_trade(h)
        ev(A, f'{T}.Offer({sword}, 1); "ok"')
        check("l'epee est sur la table", eventually(lambda: f"{sword}x1" in describe(H), timeout=10))
        ev(H, f'{T}.Confirm(); "ok"')
        check("l'host a confirme", eventually(lambda: "ready=True" in describe(A), timeout=10))
        ev(A, f'{T}.Confirm(); EClass.pc.body.Equip(EClass.pc.things.Find({sword})); "ok"')
        check("echange fait", eventually(lambda: describe(H).startswith("Done"), timeout=10))
        time.sleep(2)
        check("l'epee est dans le sac de l'host, et y reste", has(H, h, sword) == 1 and has(H, a, sword) == 0)

        together(h)
        for tag, what, item, mark, key in (
                ("R6", "non lachable (boule de punition)", "punish_ball", "", "emp_trade_nodrop"),
                ("R7", "propriete de PNJ", "torch", "t.isNPCProperty = true;", "emp_trade_npcprop"),
                ("R8", "cadeau recu", "torch", "t.isGifted = true;", "emp_trade_gifted"),
                ("R9", "lie a un personnage", "torch", "t.c_uidAttune = c.uid;", "emp_trade_bound")):
            refusal(h, a, tag, what, item, mark, key)

        full_case(h, a, h, a, "host -> A")
        full_case(h, a, a, h, "A -> host")

        equipped_case(h, a, h, a, "host -> A")
        equipped_case(h, a, a, h, "A -> host")
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {ex}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-trade-{name}', port)}")
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
