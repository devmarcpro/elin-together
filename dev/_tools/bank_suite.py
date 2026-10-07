"""La banque et la caisse d'expedition pour un invite : rien ne se perd, rien ne se double, il revoit ce qu'il a depose.
Retour d'une vraie partie (0.26.506, 6 octobre 2026) : « un invite a depose 1500 orens a la banque, il a ferme et rouvert,
les orens avaient disparu » ; meme chose pour la caisse d'expedition. Faits et choix : dev/PLAN_banque_invite.md.
Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/bank_suite.py            # ou --only b3,s1 ; ~4 minutes, finit avec le client a la Prairie

B1 invite sur la carte de l'host : il depose 1500 pieces, ferme, rouvre : elles y sont, chez lui et chez l'host ; sa
   bourse + la banque n'ont pas change ; il les reprend : sa bourse revient au montant de depart.
B2 la meme chose par l'host ; l'invite voit la banque changer.
B3 invite seul sur une autre carte (le cas de la vraie partie) : la meme chose. La banque est celle de l'host : le
   depot y arrive, la fenetre de l'invite le montre, rouverte elle le montre encore, avec ce que l'host y a mis
   entre-temps ; la reprise rend les pieces, une seule fois.
B4 deux joueurs sur les memes pieces : l'host vide la banque pendant que la fenetre de l'invite (seul ailleurs) montre
   encore la pile ; l'invite clique : il ne recoit rien, aucune piece n'est creee.
B5 invite seul ailleurs, banque et caisse ouvertes ensemble : il ferme la caisse, la fenetre de la banque montre encore
   ses pieces (fermer une fenetre ne vide que son conteneur).
S1 caisse d'expedition, invite seul ailleurs : il y met une planche, ferme, rouvre : elle y est ; il la reprend : elle
   est dans son sac, plus dans la caisse de l'host, un seul exemplaire.
S2 caisse d'expedition de l'HOST (retour 22, 0.26.532 : « le shipping chest de l'host ne fonctionne pas ») : il y met
   une planche, ferme, rouvre : elle y est ; la vente du matin (GameDate.ShipGoods, appelee directement : pas la nuit) :
   vendue, l'or dans SA bourse, un rapport de plus, rien « du » dans la sauvegarde.
S3 la meme chose pour un host dont le personnage a ete echange (TakeOverPc) : seule la trace de l'echange est ecrite a
   la main (son personnage dans PlayerRosters ; le vrai chemin est depot_suite P1), avec 266 pieces « dues » par les
   ventes d'avant : elles sont versees avec la vente. ROUGE attendu sur la 0.26.532 : rapport, or, « du ».
   S2 et S3 se jouent en premier, les deux joueurs a la Prairie (la vente lit la base de l'host).
B6 (seulement avec --only b6, laisse l'invite deconnecte) invite seul ailleurs : une reprise normale ne revient pas en banque
   (l'host la garde de cote jusqu'au point de sauvegarde de l'invite, puis la lache) ; puis demande de reprise et lien
   coupe par l'host aussitot : banque + sac garde de l'invite inchange, rien de perdu ni de double. Le moment de la
   coupure est une course : si la demande n'est pas arrivee, la verification est verte sans avoir rien prouve.

Pas joue (relecture du 6 octobre, ElinNetHostShipping.SettleTaken) : un point de sauvegarde de l'invite qui traine plus
de trois intervalles (l'objet n'est plus remis sur delai tant que l'invite est connecte et absent, seulement a la coupure
ou au retour sans la marque) ; une vieille marque plus haute que le jeton neuf (monde repris par un host en retard) ;
une exception pendant la remise (l'entree est retiree dans tous les cas). Il faudrait un invite dont on retient les
points de sauvegarde (TravelCheckpointSeconds tres grand) pour le premier cas.

Les lignes « X a depose / retire N pieces » (BillPayDelta.LastLine) sont lues dans B1, B2, B3 pour chaque depot et chaque
retrait : chez l'host, et chez l'invite quand il est sur la carte de l'host (pas quand il est seul ailleurs).

ROUGE sur la 0.26.506 (attendu, pas encore joue) : B3 « la fenetre montre », « rouverte », « avec le depot de l'host »,
« reprise » et « bourse revenue » ; B4 « la fenetre montre la pile » ; S1 « rouverte » et « reprise ». B1 et B2 sont
attendus verts des deux cotes (le chemin des coffres ordinaires) : s'ils sont rouges, la cause n'est pas la bonne.

Ce que le banc ne joue pas comme un joueur :
- la banque est ouverte par LayerInventory.CreateContainer(container_deposit), ce que fait l'etape « _deposit » du
  dialogue du banquier (DramaCustomSequence.cs:1718) : pas de banquier, pas de dialogue (la Prairie n'en a pas) ;
- la caisse est ouverte par LayerInventory.CreateContainer(un coffre d'expedition), ce que fait le clic sur le
  coffre ; le coffre est fabrique par le banc et n'est pas pose sur la carte ;
- le depot est InvOwner.Transaction.Process sur le bouton de la pile du sac et une case libre de la fenetre (ce que
  fait le lacher), la reprise Transaction.Process sur le bouton de la pile de la fenetre (ce que fait le clic), sans
  souris ; le curseur de partage n'est pas joue (le nombre est donne a la transaction) ;
- le changement de carte est un MoveZone direct ; une seule machine, connexion locale.
Pas joue : l'invite dans la zone d'un autre invite (depot envoye a l'host, rien ne s'affiche : message), la boite de
livraison, la vente du lendemain (economy_suite), l'invite qui se deconnecte juste apres une reprise, trois joueurs.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mp_test import log, shot, state  # noqa: E402
from travel_suite import HOME, LUMIEST, RESULTS, both_joined, check, client_settled, ev, eventually, move, scan_logs, wait  # noqa: E402

H, A = 27551, 27552
BANK = "EClass.game.cards.container_deposit"
SHIP = "EClass.game.cards.container_shipping"
SUM = 1500


def win(box):
    return f'LayerInventory.listInv.FirstOrDefault(q => q.invs.Count > 0 && q.invs[0].owner.Container == {box})'


def open_box(port, box):
    """Ouvre la fenetre de la banque (etape « _deposit » du banquier) ou de la caisse (clic sur un coffre d'expedition)."""
    if ev(port, f'({win(box)} != null).ToString()') == "True":
        return
    if ev(port, '(LayerInventory.listInv.Any(q => q.mainInv)).ToString()') != "True":
        ev(port, 'EClass.ui.OpenFloatInv(true); "ok"')
        time.sleep(1.5)
    if box == BANK:
        ev(port, f'LayerInventory.CreateContainer({BANK}); "ok"')
    else:
        ev(port, 'LayerInventory.CreateContainer(ThingGen.Create("container_shipping")); "ok"')
    time.sleep(1.5)


def close_box(port, box):
    ev(port, f'var w = {win(box)}; if (w != null) w.Close(); "ok"')
    time.sleep(1)


def reopen(port, box):
    close_box(port, box)
    open_box(port, box)


def shown(port, box, item):
    """Ce que la fenetre ouverte montre de cet objet (somme des piles de ses boutons), -1 sans fenetre."""
    return int(ev(port, f'var w = {win(box)}; if (w == null) return "-1"; '
                        f'return w.GetComponentsInChildren<ButtonGrid>(true).Where(g => g.card != null && g.card.id == "{item}" '
                        f'&& g.invOwner == w.invs[0].owner).Sum(g => g.card.Num).ToString();'))


def held(port, box, item):
    """Ce que le conteneur de ce jeu contient de cet objet."""
    return int(ev(port, f'{box}.things.Where(t => t.id == "{item}").Sum(t => t.Num).ToString()'))


def purse(port):
    return int(ev(port, 'EClass.pc.GetCurrency("money").ToString()'))


def bag(port, item):
    return int(ev(port, f'EClass.pc.things.List(t => t.id == "{item}").Sum(t => t.Num).ToString()'))


def deposit(port, box, item, num):
    """Le lacher de `num` de la pile du sac sur une case libre de la fenetre. L'or est dans la bourse (un sac du
    sac) : sa fenetre est ouverte d'abord, comme un joueur l'ouvre."""
    if item == "money":
        ev(port, 'var purse = EClass.pc.things.List(t => t.id == "money", true).OrderByDescending(t => t.Num).Select(t => t.parent as Thing).FirstOrDefault(); '
                 'if (purse != null && !LayerInventory.listInv.Any(q => q.invs.Count > 0 && q.invs[0].owner.Container == purse)) LayerInventory.CreateContainer(purse); return "ok";')
        time.sleep(1.5)
    return ev(port, f'var w = {win(box)}; if (w == null) return "fenetre absente"; '
                    'var src = LayerInventory.listInv.Where(q => q != w).SelectMany(q => q.GetComponentsInChildren<ButtonGrid>(true))'
                    f'.FirstOrDefault(g => g.card != null && g.card.id == "{item}" && g.card.Num >= {num} && g.card.GetRootCard() == EClass.pc); '
                    'var dst = w.GetComponentsInChildren<ButtonGrid>(true).FirstOrDefault(g => g.card == null && g.invOwner == w.invs[0].owner); '
                    'if (src == null) return "bouton de la pile du sac absent"; if (dst == null) return "case libre de la fenetre absente"; '
                    f'new InvOwner.Transaction(new DragItemCard.DragInfo(src), new DragItemCard.DragInfo(dst), {num}).Process(); return "ok";')


def take(port, box, item, num):
    """Le clic sur la pile de la fenetre, pour `num`."""
    return ev(port, f'var w = {win(box)}; if (w == null) return "fenetre absente"; '
                    f'var btn = w.GetComponentsInChildren<ButtonGrid>(true).FirstOrDefault(g => g.card != null && g.card.id == "{item}" '
                    f'&& g.card.Num >= {num} && g.invOwner == w.invs[0].owner); if (btn == null) return "bouton de la pile absent"; '
                    f'new InvOwner.Transaction(btn, {num}).Process(); return "ok";')


def fund(port, least):
    """Le joueur a au moins `least` pieces (il les gagne lui-meme : sa monnaie est a lui)."""
    if purse(port) < least:
        ev(port, f'EClass.pc.ModCurrency({least}); "ok"')
        eventually(lambda: purse(port) >= least, timeout=10)
    return purse(port)


LINE = 'HarmonyLib.AccessTools.Field(HarmonyLib.AccessTools.TypeByName("ElinTogether.Models.BillPayDelta"), "LastLine")'


def line(port):
    """La derniere ligne de facture ou de banque montree dans ce jeu (BillPayDelta.LastLine)."""
    return ev(port, f'(string){LINE}.GetValue(null)')


def clear_lines():
    for p in (H, A):
        ev(p, f'{LINE}.SetValue(null, ""); "ok"')


def told(who, port, away, deposit):
    """La ligne « X a depose / retire N pieces » est montree a tous ceux qui sont sur la carte de l'host (l'invite seul
    ailleurs ne recoit pas les lignes en voyage : la liste de ce qu'il laisse entrer ne contient pas BillPayDelta)."""
    name = ev(port, 'EClass.pc.NameSimple')
    ids, words = ("emp_ui_bank_deposit", "in the bank") if deposit else ("emp_ui_bank_withdraw", "out of the bank")
    for label, p in (("chez l'host", H), ("chez l'invite", A)):
        if p == A and away:
            continue
        ok = eventually(lambda p=p: name in line(p) and "500" in line(p) and (ids in line(p) or words in line(p)), timeout=10)
        check(f"{who} : la ligne {'de depot' if deposit else 'de retrait'} est montree {label} : « {line(p)} »", ok)


def round_trip(who, port, other, away=False):
    """Depot, fermeture, reouverture, reprise par `port` ; `other` est l'autre jeu (ce qu'il voit de la banque)."""
    p0 = fund(port, SUM + 500)
    b0 = held(H, BANK, "money")
    open_box(port, BANK)
    clear_lines()
    sent = deposit(port, BANK, "money", SUM)
    check(f"{who} : le depot part ({SUM} pieces lachees dans la fenetre : {sent})", sent == "ok")
    check(f"{who} : sa bourse a {SUM} pieces de moins", eventually(lambda: purse(port) == p0 - SUM, timeout=15))
    check(f"{who} : la banque de l'host a {SUM} pieces de plus", eventually(lambda: held(H, BANK, "money") == b0 + SUM, timeout=15))
    told(who, port, away, True)
    check(f"{who} : sa fenetre montre les pieces deposees", eventually(lambda: shown(port, BANK, "money") == b0 + SUM, timeout=15))
    reopen(port, BANK)
    check(f"{who} : fenetre fermee puis rouverte, les pieces y sont", eventually(lambda: shown(port, BANK, "money") == b0 + SUM, timeout=15))
    if not away:
        check(f"{who} : l'autre joueur les voit dans sa banque", eventually(lambda: held(other, BANK, "money") == b0 + SUM, timeout=15))
    check(f"{who} : bourse + banque inchange", purse(port) + held(H, BANK, "money") == p0 + b0)
    clear_lines()
    check(f"{who} : la reprise part (clic sur la pile)", take(port, BANK, "money", SUM) == "ok")
    check(f"{who} : sa bourse est revenue au montant de depart", eventually(lambda: purse(port) == p0, timeout=15))
    check(f"{who} : la banque de l'host est revenue au montant de depart", eventually(lambda: held(H, BANK, "money") == b0, timeout=15))
    told(who, port, away, False)
    # the host keeps a copy of what an away player took until its checkpoint carries it (ElinNetHost.SettleTaken):
    # long enough for that settling, which must not put it back
    time.sleep(8 if away else 3)
    check(f"{who} : rien en double (bourse + banque inchange apres la reprise)", purse(port) + held(H, BANK, "money") == p0 + b0)
    close_box(port, BANK)
    return p0, b0


def b1(ctx):
    """invite sur la carte de l'host : depot, fermeture, reouverture, reprise"""
    p0, _ = round_trip("invite", A, H)
    check("l'host connait la meme bourse a l'invite", eventually(
        lambda: int(ev(H, f'EClass.game.cards.globalCharas.Find({ctx["a"]}).GetCurrency("money").ToString()')) == p0, timeout=15))


def b2(ctx):
    """host : depot, fermeture, reouverture, reprise"""
    round_trip("host", H, A)


def away(ctx):
    if not state(A).get("awayZone"):
        move(A, LUMIEST)
        wait(client_settled(A, LUMIEST, True), "A seul a Lumiest")
        time.sleep(3)


def b3(ctx):
    """invite seul sur une autre carte : la banque est celle de l'host, il la voit et y reprend son or"""
    away(ctx)
    p0, b0 = round_trip("invite seul ailleurs", A, H, away=True)
    open_box(A, BANK)
    ev(H, f'{BANK}.ModCurrency(300); "ok"')
    reopen(A, BANK)
    check("rouverte, sa fenetre montre aussi ce que l'host a depose entre-temps (300)",
          eventually(lambda: shown(A, BANK, "money") == b0 + 300, timeout=15))
    close_box(A, BANK)
    check("fenetre fermee, la copie de l'invite est vide (rien d'autre de son jeu ne compte dessus)", held(A, BANK, "money") == 0)
    ev(H, f'{BANK}.ModCurrency(-300); "ok"')
    check("le sac que l'host garde pour l'invite a la meme bourse (sauvegarde demandee a la reprise)", eventually(
        lambda: int(ev(H, f'EClass.game.cards.globalCharas.Find({ctx["a"]}).GetCurrency("money").ToString()')) == p0, timeout=30))


def b4(ctx):
    """deux joueurs sur les memes pieces : l'host les prend d'abord, l'invite ne recoit rien"""
    away(ctx)
    p0 = purse(A)
    b0 = held(H, BANK, "money")
    ev(H, f'{BANK}.ModCurrency(700); "ok"')
    open_box(A, BANK)
    reopen(A, BANK)
    check("la fenetre de l'invite montre la pile de l'host", eventually(lambda: shown(A, BANK, "money") == b0 + 700, timeout=15))
    ev(H, f'{BANK}.ModCurrency(-{b0 + 700}); "ok"')
    check("la banque de l'host est vide", held(H, BANK, "money") == 0)
    check("l'invite clique sur la pile qu'il voit encore", take(A, BANK, "money", 700) == "ok")
    time.sleep(5)
    check("il ne recoit rien : sa bourse n'a pas change", purse(A) == p0)
    check("et la banque de l'host est toujours vide", held(H, BANK, "money") == 0)
    check("sa fenetre ne montre plus la pile", eventually(lambda: shown(A, BANK, "money") == 0, timeout=15))
    close_box(A, BANK)
    if b0:
        ev(H, f'{BANK}.ModCurrency({b0}); "ok"')


def b5(ctx):
    """deux fenetres ouvertes (banque et caisse), invite seul ailleurs : fermer l'une laisse les images de l'autre"""
    away(ctx)
    b0 = held(H, BANK, "money")
    h0 = held(H, SHIP, "plank")
    ev(H, f'{BANK}.ModCurrency(400); "ok"')
    ev(H, f'{SHIP}.AddThing(ThingGen.Create("plank")); "ok"')
    try:
        open_box(A, BANK)
        open_box(A, SHIP)
        check("les deux fenetres montrent ce que l'host y tient", eventually(
            lambda: shown(A, BANK, "money") == b0 + 400 and shown(A, SHIP, "plank") == h0 + 1, timeout=15))
        close_box(A, SHIP)
        time.sleep(2)
        check("caisse fermee : sa copie est vide", held(A, SHIP, "plank") == 0)
        check("caisse fermee : la fenetre de la banque montre encore ses pieces", shown(A, BANK, "money") == b0 + 400)
        check("caisse fermee : la copie de la banque garde ses images", held(A, BANK, "money") == b0 + 400)
    finally:
        close_box(A, BANK)
        ev(H, f'{BANK}.ModCurrency(-400); "ok"')
        ev(H, f'var p = {SHIP}.things.Find(t => t.id == "plank"); if (p != null) p.ModNum(-1); "ok"')


def kept_purse(uid):
    """La bourse du sac que l'host garde pour ce joueur (remplace par chaque point de sauvegarde de l'invite seul)."""
    return int(ev(H, f'EClass.game.cards.globalCharas.Find({uid}).GetCurrency("money").ToString()'))


def b6(ctx):
    """objet repris par un invite seul, lien coupe entre la demande et la reponse : l'or n'est ni perdu ni double.
    Laisse l'invite DECONNECTE (relancer mp_test.py apres) : a ne jouer qu'avec --only b6, en dernier."""
    away(ctx)
    p0 = purse(A)
    # a normal take first: the host holds the gold aside, then lets go of it once the checkpoint carries the mark
    b0 = held(H, BANK, "money")
    ev(H, f'{BANK}.ModCurrency(900); "ok"')
    open_box(A, BANK)
    reopen(A, BANK)
    check("sa fenetre montre la banque (900 de plus)", eventually(lambda: shown(A, BANK, "money") == b0 + 900, timeout=15))
    check("la reprise part", take(A, BANK, "money", 900) == "ok")
    check("l'or est dans sa bourse", eventually(lambda: purse(A) == p0 + 900, timeout=15))
    time.sleep(10)
    check(f"dix secondes apres, l'or n'est pas revenu dans la banque (bourse {purse(A)}, banque {held(H, BANK, 'money')})",
          purse(A) == p0 + 900 and held(H, BANK, "money") == b0)
    check("et le sac que l'host garde pour lui le sait (pas de remise en banque a tort)",
          eventually(lambda: kept_purse(ctx["a"]) == p0 + 900, timeout=30))
    close_box(A, BANK)
    # then the cut: the guest asks for 400 and the host drops its link at once
    total = held(H, BANK, "money") + kept_purse(ctx["a"])
    open_box(A, BANK)
    reopen(A, BANK)
    check("la fenetre montre la pile", eventually(lambda: shown(A, BANK, "money") == b0, timeout=15))
    ev(A, f'var b = NetSession.Instance.Transport as ElinNetClient; var m = EClass.game.cards.container_deposit.things.Find(t => t.id == "money"); '
          'b.AskWorldBox(2, m.GetInt("emp_box_uid"), 400); "ok"')
    ev(H, 'var h = NetSession.Instance.Transport as ElinNetHost; h.DisconnectPeer(h.States.Keys.First(i => i != 0), "bank_suite"); "ok"')
    time.sleep(15)
    after = held(H, BANK, "money") + kept_purse(ctx["a"])
    log(f"or banque + sac garde de l'invite : {total} -> {after}")
    check(f"rien de perdu ni de double apres la coupure (banque + sac garde : {total} -> {after})", after == total)


def s1(ctx):
    """caisse d'expedition, invite seul ailleurs : il revoit sa planche et peut la reprendre"""
    if not state(A).get("awayZone") and bag(A, "plank") == 0:
        ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {ctx["a"]}); c.AddThing(ThingGen.Create("plank")); "ok"')
        check("l'invite a recu une planche", eventually(lambda: bag(A, "plank") >= 1, timeout=10))
    away(ctx)
    if bag(A, "plank") == 0:
        # alone away the game is single player: the plank is its own
        ev(A, 'EClass.pc.AddThing(ThingGen.Create("plank")); "ok"')
    n0 = bag(A, "plank")
    h0 = held(H, SHIP, "plank")
    open_box(A, SHIP)
    check("le depot part (une planche lachee dans la caisse)", deposit(A, SHIP, "plank", 1) == "ok")
    check("elle arrive dans la caisse de l'host", eventually(lambda: held(H, SHIP, "plank") == h0 + 1, timeout=15))
    check("elle n'est plus dans le sac de l'invite", eventually(lambda: bag(A, "plank") == n0 - 1, timeout=10))
    reopen(A, SHIP)
    check("caisse fermee puis rouverte, la planche y est", eventually(lambda: shown(A, SHIP, "plank") == h0 + 1, timeout=15))
    check("la reprise part (clic sur la planche)", take(A, SHIP, "plank", 1) == "ok")
    check("elle est revenue dans le sac de l'invite", eventually(lambda: bag(A, "plank") == n0, timeout=15))
    check("elle n'est plus dans la caisse de l'host", eventually(lambda: held(H, SHIP, "plank") == h0, timeout=15))
    time.sleep(3)
    check("un seul exemplaire (sac + caisse de l'host inchange)", bag(A, "plank") + held(H, SHIP, "plank") == n0 + h0)
    close_box(A, SHIP)


HOST_T = 'var t = HarmonyLib.Traverse.Create(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetHost")); '
OWED = HOST_T + 'var d = t.Property("ShippingAccounts").GetValue<System.Collections.Generic.Dictionary<int, long[]>>(); '
ROSTER = (HOST_T + 'var me = t.Property("LocalUser").GetValue<ulong>(); '
          'var r = t.Property("PlayerRosters").GetValue<System.Collections.Generic.Dictionary<ulong, System.Collections.Generic.List<int>>>(); ')


def owed(uid="EClass.pc.uid"):
    """Ce que l'expedition « doit » a ce personnage dans la sauvegarde de l'host (or, lingots)."""
    return ev(H, OWED + f'long[] a; return d.TryGetValue({uid}, out a) && a.Length >= 2 ? a[0] + "," + a[1] : "0,0";')


def host_ships(who, due=0):
    """L'host depose une planche dans SA caisse, ferme, rouvre, la nuit passe : vendue, payee a l'host, rapport affiche.
    `due` : ce que la sauvegarde lui devait deja (ventes d'avant la correction), verse en meme temps."""
    ev(H, 'EClass.pc.AddThing(ThingGen.Create("plank")); "ok"')
    h0 = held(H, SHIP, "plank")
    open_box(H, SHIP)
    check(f"{who} : le depot part (une planche lachee dans sa caisse)", deposit(H, SHIP, "plank", 1) == "ok")
    check(f"{who} : elle est dans la caisse", eventually(lambda: held(H, SHIP, "plank") == h0 + 1, timeout=10))
    reopen(H, SHIP)
    check(f"{who} : caisse fermee puis rouverte, la planche y est (fenetre et conteneur)",
          eventually(lambda: shown(H, SHIP, "plank") == h0 + 1 and held(H, SHIP, "plank") == h0 + 1, timeout=10))
    close_box(H, SHIP)
    time.sleep(1)
    check(f"{who} : fenetre fermee, la planche est toujours dans la caisse", held(H, SHIP, "plank") == h0 + 1)
    tag = ev(H, f'{SHIP}.things.Where(t => t.id == "plank").Select(t => t.GetInt("emp_shipper")).Last().ToString()')
    log(f"{who} : marque de la planche = {tag}, personnage de l'host = {ev(H, 'EClass.pc.uid.ToString()')}")

    p0 = purse(H)
    r0 = int(ev(H, 'EClass.player.shippingResults.Count.ToString()'))
    ev(H, 'EClass.player.showShippingResult = false; "ok"')
    # the 5 o'clock sale (GameDate.AdvanceHour calls exactly this), not the night itself. The flag is read and
    # put down in the same call: the report window itself would stand in the way of the next steps
    asked = ev(H, 'EClass.world.date.ShipGoods(); var s = EClass.player.showShippingResult; EClass.player.showShippingResult = false; '
                  'return (s == EClass.core.config.game.showShippingResult).ToString();')
    check(f"{who} : la nuit passe, la caisse n'a plus de planche", eventually(lambda: held(H, SHIP, "plank") == 0, timeout=10))
    check(f"{who} : un rapport de vente de plus chez l'host",
          int(ev(H, 'EClass.player.shippingResults.Count.ToString()')) == r0 + 1)
    income = int(ev(H, 'EClass.player.shippingResults.Count == 0 ? "0" : EClass.player.shippingResults.LastItem().GetIncome().ToString()'))
    check(f"{who} : le rapport est demande a l'ecran (comme le reglage du jeu le veut ; la fenetre elle-meme n'est pas lue)",
          asked == "True")
    got = purse(H) - p0
    check(f"{who} : l'or de la vente est dans la bourse de l'host (recu {got}, vente {income}, du d'avant {due})",
          income > 0 and got == income + due)
    check(f"{who} : rien n'est garde « du a l'host » dans la sauvegarde ({owed()})", owed().startswith("0,"))
    check(f"{who} : l'invite voit la caisse vide", eventually(lambda: held(A, SHIP, "plank") == 0, timeout=10))


def s2(ctx):
    """caisse d'expedition de l'HOST : depot, fermeture, reouverture, vente du matin, or et rapport chez l'host"""
    host_ships("host")


def s3(ctx):
    """la meme chose pour un host dont le personnage a ete echange (monde repris, ElinNetHost.TakeOverPc), et l'or
    que les ventes d'avant lui devaient (retour 22, LemiWinks, 0.26.532 : 95 + 171 pieces) lui est verse.
    Le vrai chemin (depot, echange, rechargement) est depot_suite P1 ; ici seule la trace qu'il laisse est ecrite a
    la main : le personnage de l'host reste dans la liste des personnages de son compte (PlayerRosters)."""
    uid = ev(H, 'EClass.pc.uid.ToString()')
    log("tables : " + ev(H, ROSTER + OWED.replace(HOST_T, "") +
                         f'if (!r.ContainsKey(me)) r[me] = new System.Collections.Generic.List<int>(); if (!r[me].Contains({uid})) r[me].Add({uid}); '
                         f'd[{uid}] = new long[] {{ 266, 2 }}; return "roster " + string.Join(",", r[me]) + " | du " + d[{uid}][0];'))
    try:
        host_ships("host echange", due=266)
    finally:
        ev(H, ROSTER + f'if (r.ContainsKey(me)) {{ r[me].Remove({uid}); if (r[me].Count == 0) r.Remove(me); }} "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="liste de scenarios, ex. b1,b3")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": state(A)["pc"]["uid"], "h": state(H)["pc"]["uid"]}
    steps = [s2, s3, b1, b2, b3, b4, b5, s1]
    # b6 leaves the guest disconnected: only asked for by name
    if a.only and "b6" in a.only.split(","):
        steps.append(b6)
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
                    print(f"    capture {name} : {shot(f'bank-{step.__name__}-{name}', port)}")
                except Exception:  # noqa: BLE001
                    pass
        for port in (H, A):
            try:
                close_box(port, BANK)
                close_box(port, SHIP)
            except Exception:  # noqa: BLE001
                pass

    try:
        if state(A).get("awayZone"):
            move(A, HOME)
            both_joined(H, A, HOME)
    except Exception as ex:  # noqa: BLE001
        check(f"retour a la Prairie interrompu : {type(ex).__name__}: {ex}", False)

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
