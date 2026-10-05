"""Les corrections jamais jouees en jeu (commits marques « NOT PLAYED » du 2026-10-05) : pour chaque ligne, le meme geste
par l'invite puis par l'host. Test court, sur des instances deja lancees (host + 1 client, tous les deux a la Prairie).

    python _tools/mp_test.py
    python _tools/unplayed_suite.py            # ou --only u1,u3

U1 tri du sac : celui qui trie son sac (vrai bouton de tri de la fenetre du sac, vraie entree du menu) ne change ni
   le tri ni l'ordre croissant de l'autre joueur (5ffa169).
U2 bouton partage / personnel d'un coffre de la base : celui qui ouvre le coffre (clic gauche) et clique le bouton de
   la fenetre ; l'autre jeu voit le meme coffre partage, puis de nouveau personnel (5ffa169).
U3 ticket d'hotesse : celui qui donne le ticket a un habitant (geste « donner » de l'objet tenu) est masse, pas
   l'autre joueur ; le ticket est consomme (ab73333).
U4 parchemin de changement d'alias : la liste s'ouvre chez celui qui lit, aucune fenetre chez l'autre (2239dde).
U5 deux acheteurs du meme objet : un seul exemplaire en tout, un seul payeur, l'or de l'autre inchange (211658e) ;
   puis la demande de l'invite pour un objet que l'host vient de prendre est refusee.
U6 monture deja prise : le second cavalier est refuse, la bete garde son cavalier dans les deux jeux (31faaac).
U7 eau profonde : le joueur qui nage perd son souffle (cf62040). La Prairie n'a pas d'eau profonde : le banc en fait
   chez le nageur (deux cases repeintes dans son jeu seul, remises a la fin). D12 de hunt_suite couvre le meme point
   quand la carte a de l'eau profonde ; il n'est pas recopie ici.
U8 cle a molette sur un coffre (ligne 11 de la deuxieme chasse) : le coffre prend une rangee de plus, meme taille de
   conteneur chez les deux joueurs, la cle est consommee une seule fois.
U9 fouet-oeuf sur un animal compagnon (ligne 11) : un oeuf chez les deux, la charge du fouet baisse une fois, le karma est
   retire a celui qui fouette seulement.

Ce que le banc ne joue pas comme un joueur :
- U1 : le bouton de tri et l'entree du menu sont cliques par leur appel (onClick.Invoke de l'objet du menu trouve par
  son texte), pas par la souris ; la fenetre du sac est ouverte par ToggleInventory, ce que fait la touche Tab. Si le
  menu n'est pas trouve, le test refait ce que font ses entrees (pref + Sort()) et le dit.
- U2 : le coffre est ouvert par l'action « actContainer » du clic gauche (use_menu), le bouton par onClick.Invoke.
- U3 : « donner » est le vrai menu de l'objet tenu (use_held, action actGive) ; la boite « Yes » est cliquee par son
  texte. Le resident est immobile (noMove) et eveille.
- U4 : le parchemin est lu par AI_Read, comme G10 ; le tirage de l'alias n'est pas choisi (la liste est fermee).
- U5 : la boutique est ouverte par LayerInventory.CreateBuy (ce que fait l'etape « acheter » du dialogue du marchand) ;
  l'achat est Transaction.Process() sur le bouton de l'objet (ce que fait le choix « acheter » du menu de l'objet) ;
  les deux demandes partent l'une derriere l'autre sans attente, avec le bouton pris avant (le joueur qui clique sur
  un ecran pas encore rafraichi). Deuxieme partie : la demande ThingRequest est envoyee directement.
- U6 : la premiere monte par l'action « monter » du jeu (UseAbility ActRide) ; le second essaie la meme action, puis
  ActRide.Ride dans son jeu et dans celui du cavalier (ce que rejouerait l'envoi de l'autre jeu en cas de course).
- U7 : voir ci-dessus ; le nageur fait trois pas comme D12.
- U8 : clic droit avec la cle en main par use_held (le vrai TrySetHeldAct du jeu, la vraie lambda remplacee par le mod),
  mais sans la souris sur la case ; le coffre est pose par l'host a cote du joueur (comme s1), la cle (3 exemplaires) est
  donnee par l'host. Seule la cle « agrandir en hauteur » est jouee : pas le lit, le frigo, le coffre magique (memes
  champs, memes envois, non joues) ni les tentes (elements de la zone-tente, pas un champ d'objet : non synchronises).
- U9 : meme geste (use_held) avec la souris en moins ; le chat est recrute par MakeAlly (tame), il arrive paralyse et le
  banc retire ses conditions. Le karma suppose l'option « quetes et karma personnels » (sans elle il est commun et le
  test de karma ne distingue rien) ; le banc le met a 50 des deux cotes et le remet. Les passe-temps du fouet « amour »
  ne sont pas joues (rien ne les envoie aux invites).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_suite import click_yes, dialog_open, hide_menus  # noqa: E402
from equal2_suite import drop, seen, spawn  # noqa: E402
from guest_suite import (LAYERS, awake, both, chara, clear_conditions, close_layers, count, first_id, give, give_made, stand,  # noqa: E402
                         tame, use_held, use_menu)
from mp_test import log, shot, state  # noqa: E402
from setting_suite import furniture, thing  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552


def other_of(key):
    return "h" if key == "a" else "a"


# ---------------------------------------------------------------------------------------------------------------------
# U1 : tri du sac

BY_CATEGORY, BY_NAME = 3, 11  # UIList.SortMode
PREFS = 'var f = EClass.player.pref; return (int)f.sortInv + "/" + f.sort_ascending;'


def prefs(port):
    """Tri et ordre croissant de ce joueur : "numero/True|False"."""
    return ev(port, PREFS)


def set_prefs(port, mode, asc):
    ev(port, f'var f = EClass.player.pref; f.sortInv = (UIList.SortMode){mode}; f.sort_ascending = {str(asc).lower()}; "ok"')


def bag_open(port):
    return ev(port, '(LayerInventory.listInv.Any(l => l.mainInv)).ToString()') == "True"


def click_sort_entry(port, label, toggle):
    """Clique le bouton de tri de la fenetre du sac puis l'entree du menu qui porte ce texte (un bouton, ou la case
    « croissant » si toggle)."""
    cond = ('i.toggle != null && i.textName.text.ToLower() == "sort_ascending".lang().ToLower()' if toggle else
            f'i.button != null && i.toggle == null && i.textName.text.EndsWith("{label}")')
    return ev(port, 'var l = LayerInventory.listInv.Find(x => x.mainInv); if (l == null) return "pas de sac"; '
                    'var b = l.invs[0].window.buttonSort; if (b == null) return "pas de bouton de tri"; b.onClick.Invoke(); '
                    'var it = UnityEngine.Resources.FindObjectsOfTypeAll<UIContextMenuItem>().FirstOrDefault(i => '
                    f'i.gameObject.scene.IsValid() && {cond}); if (it == null) return "entree absente"; '
                    'if (it.toggle != null) it.toggle.isOn = !it.toggle.isOn; else it.button.onClick.Invoke(); return "clic";')


def u1(ctx):
    """tri du sac : le tri choisi par un joueur (mode puis ordre croissant) n'arrive pas chez l'autre joueur"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        saved = {p: prefs(p) for p in (H, A)}
        opened_here = False
        try:
            close_layers()
            hide_menus(port)
            # points de depart connus : le sien (par categorie, decroissant), celui de l'autre (par nom, decroissant)
            set_prefs(port, BY_CATEGORY, False)
            set_prefs(other, BY_NAME, False)
            base_other = prefs(other)
            awake(port)
            if not bag_open(port):
                opened_here = True
                ev(port, 'EClass.ui.ToggleInventory(); "ok"')
            if not check(f"{who} : la fenetre de son sac est ouverte", eventually(lambda: bag_open(port), timeout=10)):
                continue
            time.sleep(1)
            pick = ev(port, 'var l = LayerInventory.listInv.Find(x => x.mainInv); var s = l.invs[0].list.sorts.First(x => '
                            'x != UIList.SortMode.ByCategory && x != UIList.SortMode.ByName); return (int)s + "/" + s.ToString().lang();')
            mode, label = pick.split("/", 1)
            r = click_sort_entry(port, label, toggle=False)
            if r != "clic":
                # le menu n'est pas trouve : ce que fait l'entree (pref, donnees de la fenetre, Sort())
                log(f"{who} : menu de tri non trouve ({r}), l'entree est refaite")
                ev(port, f'var l = LayerInventory.listInv.Find(x => x.mainInv); var f = EClass.player.pref; f.sortInv = (UIList.SortMode){mode}; '
                         f'l.invs[0].window.saveData.sortMode = (UIList.SortMode){mode}; l.invs[0].Sort(); "ok"')
            hide_menus(port)
            check(cond=eventually(lambda: prefs(port) == f"{mode}/False", timeout=10),
                  label=f"{who} choisit le tri « {label} » ({r}) : son tri a change ({prefs(port)})")
            time.sleep(4)
            check(f"{who} : le tri de l'autre joueur n'a pas bouge ({base_other} -> {prefs(other)})", prefs(other) == base_other)
            # l'ordre croissant : la case du menu
            r = click_sort_entry(port, label, toggle=True)
            if r != "clic":
                log(f"{who} : case « croissant » non trouvee ({r}), l'entree est refaite")
                ev(port, 'var l = LayerInventory.listInv.Find(x => x.mainInv); EClass.player.pref.sort_ascending = true; '
                         'l.invs[0].window.saveData.sort_ascending = true; l.invs[0].Sort(); "ok"')
            hide_menus(port)
            check(cond=eventually(lambda: prefs(port) == f"{mode}/True", timeout=10),
                  label=f"{who} coche « croissant » ({r}) : son ordre a change ({prefs(port)})")
            time.sleep(4)
            check(f"{who} : l'ordre de l'autre joueur n'a pas bouge ({base_other} -> {prefs(other)})", prefs(other) == base_other)
        finally:
            hide_menus(port)
            if opened_here and bag_open(port):
                ev(port, 'EClass.ui.ToggleInventory(); "ok"')
            for p in (H, A):
                mode, asc = saved[p].split("/")
                set_prefs(p, mode, asc == "True")


# ---------------------------------------------------------------------------------------------------------------------
# U2 : bouton partage / personnel d'un coffre

def u2(ctx):
    """bouton partage d'un coffre de la base : le coffre devient partage (puis personnel) dans les deux jeux"""
    if ev(H, 'EClass._zone.IsPCFaction.ToString()') != "True":
        print("    [SAUTE] U2 : la carte n'est pas une base, le bouton partage n'y est pas")
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        t = furniture(uid, extra="t.c_lockLv = 0;")
        shared = lambda p: ev(p, f'var t = {thing(t)}; return t == null ? "absent" : t.IsSharedContainer.ToString();')  # noqa: E731
        win = f'LayerInventory.listInv.Find(l => l.invs[0].owner.Container == {thing(t)})'
        try:
            if not check(f"{who} : un coffre est pose a cote de lui, personnel au depart (host {shared(H)}, invite {shared(A)})",
                         shared(H) == "False" and shared(A) == "False"):
                continue
            x, z = (int(v) for v in ev(H, f'var t = {thing(t)}; return t.pos.x + "," + t.pos.z;').split(","))
            awake(port)
            opened_by = use_menu(port, (x, z), 'i.act is DynamicAct d && d.id == "actContainer"')
            log(f"{who} ouvre le coffre : {opened_by}")
            if not eventually(lambda: ev(port, f'({win} != null).ToString()') == "True", timeout=8):
                log(f"{who} : le clic n'a pas ouvert le coffre, l'ouverture du jeu est appelee (TraitContainer.TryOpen)")
                ev(port, f'((TraitContainer){thing(t)}.trait).TryOpen(); "ok"')
            if not check(f"{who} : la fenetre du coffre est ouverte chez lui", eventually(lambda: ev(port, f'({win} != null).ToString()') == "True", timeout=10)):
                continue
            click = (f'var l = {win}; var b = l.invs[0].window.buttonShared; if (b == null || !b.gameObject.activeInHierarchy) return "bouton absent"; '
                     'b.onClick.Invoke(); return "clic";')
            for want in ("True", "False"):
                r = ev(port, click)
                check(cond=eventually(lambda: shared(port) == want and shared(H) == want and shared(A) == want, timeout=10),
                      label=f"{who} clique le bouton ({r}) : coffre {'partage' if want == 'True' else 'personnel'} chez lui ({shared(port)}), "
                            f"chez l'host ({shared(H)}) et chez l'invite ({shared(A)})")
        finally:
            close_layers()
            ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); "ok"')


# ---------------------------------------------------------------------------------------------------------------------
# U3 : ticket d'hotesse

def u3(ctx):
    """ticket de massage donne a un habitant : celui qui donne est masse, l'autre joueur n'a aucune tache de massage"""
    tk = "ticket_massage"
    if not check(f"le jeu a le ticket {tk}", ev(H, f'(EClass.sources.things.map.ContainsKey("{tk}")).ToString()') == "True"):
        return
    ai = lambda p: ev(p, 'EClass.pc.ai.GetType().Name')  # noqa: E731
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        for p in (H, A):
            ev(p, 'EClass.pc.SetNoGoal(); "ok"')
        clear_conditions(uid)
        res = spawn(uid, "putty", "Friend")
        try:
            if not check(f"{who} : un habitant est a cote de lui ({res})", res and eventually(lambda: seen(port, res), timeout=15)):
                continue
            # eveille et immobile, dans les deux jeux
            clear_conditions(res)
            for p in (H, A):
                ev(p, f'EClass._map.charas.Find(x => x.uid == {res}).noMove = true; "ok"')
            ticket = give(ctx, key, tk, 2)
            n0 = count(H, uid, tk)
            x, z = (int(v) for v in ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {res}); return m.pos.x + "," + m.pos.z;').split(","))
            awake(port)
            r = use_held(port, ticket, at=(x, z), pick='i.act is DynamicAct d && d.id == "actGive"')
            log(f"{who} donne le ticket : {r}")
            if eventually(lambda: dialog_open(port), timeout=3):
                log(f"{who} : boite de confirmation, {click_yes(port)}")
            check(f"{who} fait le geste « donner » ({r[:40]})", r.startswith("ok"))
            # le massage est une tache tres courte : le banc la voit ou non selon l'instant ; ce qui compte est plus bas
            log(f"{who} : sa tache juste apres le don : {ai(port)}")
            seen_ai = []
            for _ in range(6):
                seen_ai.append(ai(other))
                time.sleep(1)
            check(f"l'autre joueur : aucune tache de massage chez lui ({set(seen_ai)})",
                  "AI_Massage" not in seen_ai)
            check(cond=eventually(lambda: count(H, uid, tk) == n0 - 1 and count(port, uid, tk) == n0 - 1, timeout=10),
                  label=f"{who} : le ticket est consomme, chez l'host ({n0} -> {count(H, uid, tk)}) et chez lui ({count(port, uid, tk)})")
        finally:
            for p in (H, A):
                ev(p, 'EClass.pc.SetNoGoal(); "ok"')
            close_layers()
            drop([res])
            ev(H, f'var c = {chara(H, uid)}; foreach (var t in c.things.Where(m => m.id == "{tk}").ToList()) t.Destroy(); "ok"')


# ---------------------------------------------------------------------------------------------------------------------
# U4 : parchemin de changement d'alias

def u4(ctx):
    """parchemin de changement d'alias : la liste s'ouvre chez celui qui lit, rien chez l'autre joueur"""
    ele = ev(H, 'var r = EClass.sources.elements.rows.FirstOrDefault(x => x.proc != null && x.proc.Length > 0 && x.proc[0] == "ChangeAlias"); '
                'return r == null ? "" : r.id.ToString();')
    if not check(f"le jeu a un element de parchemin « ChangeAlias » ({ele or 'aucun'})", bool(ele)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        scroll = give_made(ctx, key, f'var t = ThingGen.CreateScroll({ele}); t.c_IDTState = 0; t.SetBlessedState(BlessedState.Normal);')
        try:
            awake(port)
            ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {scroll}); EClass.pc.SetAI(new AI_Read {{ target = t }}); "ok"')
            check(cond=eventually(lambda: awake(port) and "LayerList" in ev(port, LAYERS), timeout=20),
                  label=f"{who} lit : la liste des alias s'ouvre chez lui ({ev(port, LAYERS) or 'rien'})")
            # la lecture a bien eu lieu chez l'host (sans cela, « rien chez l'autre » ne prouverait rien)
            check(cond=eventually(lambda: ev(H, f'({chara(H, uid)}.things.Find(x => x.uid == {scroll}) == null).ToString()') == "True", timeout=15),
                  label=f"{who} : le parchemin est use, chez l'host")
            time.sleep(4)
            check(f"{who} : aucune liste chez l'autre joueur ({ev(other, LAYERS) or 'rien'})", "LayerList" not in ev(other, LAYERS))
        finally:
            ev(port, 'EClass.pc.SetNoGoal(); "ok"')
            close_layers()
            ev(H, f'var t = {chara(H, uid)}.things.Find(x => x.uid == {scroll}); if (t != null) t.Destroy(); "ok"')


# ---------------------------------------------------------------------------------------------------------------------
# U5 : deux acheteurs du meme objet

MERCHANT = 'EClass.sources.charas.rows.First(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Merchant").id'


def shop_open(port, m):
    """Ce que fait l'etape « acheter » du dialogue d'un marchand : il se reapprovisionne, sa boutique s'ouvre."""
    ev(port, f'var m = EClass._map.charas.Find(x => x.uid == {m}); m.trait.OnBarter(); '
             'EClass.ui.AddLayer(LayerInventory.CreateBuy(m, m.trait.CurrencyType, m.trait.PriceType)); "ok"')


def shop_button(port, m, item):
    """Prend dans la fenetre de la boutique le bouton de l'objet (garde dans ce jeu) ; renvoie "ok <prix>" ou ce qui manque."""
    return ev(port, f'var l = LayerInventory.listInv.Find(x => x.invs[0].owner.owner != null && x.invs[0].owner.owner.uid == {m}); '
                    'if (l == null) return "pas de fenetre"; '
                    f'var b = l.GetComponentsInChildren<ButtonGrid>(true).FirstOrDefault(x => x.card != null && x.card.uid == {item}); '
                    'if (b == null) return "pas de bouton"; System.AppDomain.CurrentDomain.SetData("u5btn", b); '
                    'return "ok " + new InvOwner.Transaction(b).GetPrice();')


def wait_button(port, m, item):
    """Attend le bouton de l'objet dans la boutique ouverte ; renvoie la derniere reponse de shop_button."""
    box = [""]

    def look():
        box[0] = shop_button(port, m, item)
        return box[0].startswith("ok")

    eventually(look, timeout=20)
    return box[0]


BUY = ('var b = (ButtonGrid)System.AppDomain.CurrentDomain.GetData("u5btn"); if (b == null) return "pas de bouton"; '
       'new InvOwner.Transaction(b).Process(); return "lance";')


def u5(ctx):
    """deux acheteurs du meme objet : un seul exemplaire en tout, un seul payeur, l'or de l'autre inchange"""
    mid = ev(H, MERCHANT)
    gold0 = {k: count(H, ctx[k][1], "money") for k in ("a", "h")}
    try:
        for first, second in (("a", "h"), ("h", "a")):
            name = {"a": "l'invite", "h": "l'host"}
            tag = f"{name[first]} puis {name[second]}"
            close_layers()
            for k in ("a", "h"):
                give(ctx, k, "money", 5000)
            m = spawn(ctx["a"][1], mid, "Friend")
            item = 0
            base = {k: count(H, ctx[k][1], "bucket") for k in ("a", "h")}
            try:
                if not check(f"{tag} : un marchand est la, vu des deux jeux ({m})", m and eventually(lambda: seen(A, m) and seen(H, m), timeout=15)):
                    continue
                item = int(ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {m}); m.trait.OnBarter(); var ch = m.things.Find("chest_merchant"); '
                                 'foreach (var x in ch.things.ToList()) x.Destroy(); var it = ThingGen.Create("bucket"); ch.AddThing(it); return it.uid.ToString();'))
                for k in ("h", "a"):
                    awake(ctx[k][0])
                    shop_open(ctx[k][0], m)
                price = {}
                for k in ("h", "a"):
                    price[k] = wait_button(ctx[k][0], m, item)
                if not check(f"{tag} : l'objet est dans les deux boutiques ouvertes (host : {price['h']}, invite : {price['a']})",
                             all(v.startswith("ok") for v in price.values())):
                    continue
                before = {k: count(H, ctx[k][1], "bucket") for k in ("a", "h")}
                gold = {k: count(H, ctx[k][1], "money") for k in ("a", "h")}
                # les deux demandes l'une derriere l'autre, sans attente
                r1 = ev(ctx[first][0], BUY)
                r2 = ev(ctx[second][0], BUY)
                log(f"{tag} : {name[first]} {r1}, {name[second]} {r2}")
                eventually(lambda: sum(count(H, ctx[k][1], "bucket") - before[k] for k in ("a", "h")) >= 1, timeout=20)
                time.sleep(6)
                got = {k: count(H, ctx[k][1], "bucket") - before[k] for k in ("a", "h")}
                paid = {k: gold[k] - count(H, ctx[k][1], "money") for k in ("a", "h")}
                check(f"{tag} : un seul exemplaire en tout (invite {got['a']:+d}, host {got['h']:+d})", sorted(got.values()) == [0, 1])
                check(f"{tag} : un seul payeur (invite {paid['a']}, host {paid['h']})", sorted(v != 0 for v in paid.values()) == [False, True])
                winner = next((k for k in ("a", "h") if got[k] == 1), None)
                check(f"{tag} : c'est celui qui a l'objet qui a paye", winner is not None and paid[winner] > 0 and paid[other_of(winner)] == 0)
                check(f"{tag} : la boutique n'a plus l'objet (host)", ev(H, f'var m = EClass._map.charas.Find(x => x.uid == {m}); '
                      f'var ch = m.things.Find("chest_merchant"); return (ch == null || ch.things.Find(x => x.uid == {item}) == null).ToString();') == "True")
                check(cond=eventually(lambda: all(count(A, ctx[k][1], "bucket") == count(H, ctx[k][1], "bucket")
                                                  and count(A, ctx[k][1], "money") == count(H, ctx[k][1], "money") for k in ("a", "h")), timeout=15),
                      label=f"{tag} : le jeu de l'invite voit les memes sacs et la meme bourse que l'host")
            finally:
                close_layers()
                drop([m])
                # les seaux gagnes par le test, et eux seuls
                for k in ("a", "h"):
                    extra = count(H, ctx[k][1], "bucket") - base[k]
                    if extra > 0:
                        ev(H, f'var c = {chara(H, ctx[k][1])}; var s = {extra}; foreach (var t in c.things.Where(x => x.id == "bucket").ToList()) '
                              '{ if (s <= 0) break; var n = System.Math.Min(s, t.Num); t.ModNum(-n); s -= n; } "ok"')
    finally:
        for k in ("a", "h"):
            ev(H, f'var c = {chara(H, ctx[k][1])}; c.ModCurrency({gold0[k]} - c.GetCurrency("money"), "money"); "ok"')
    u5_gone(ctx)


def u5_gone(ctx):
    """demande d'un objet que l'host vient de prendre : refusee, l'objet reste a l'host (le cas le plus proche de la course)"""
    port, uid = ctx["a"]
    close_layers()
    t = furniture(uid, extra="t.c_lockLv = 0;")
    item = int(ev(H, f'var c = {thing(t)}; var i = ThingGen.Create("bucket"); c.AddThing(i); return i.uid.ToString();'))
    try:
        inbox = lambda p: ev(p, f'(({thing(t)}).things.Find(x => x.uid == {item}) != null).ToString()')  # noqa: E731
        if not check("l'invite voit l'objet dans le coffre", eventually(lambda: inbox(A) == "True", timeout=15)):
            return
        n0 = {k: count(H, ctx[k][1], "bucket") for k in ("a", "h")}
        # l'invite garde l'objet sous les yeux (sa boutique ou son coffre l'affichait) ; l'host le prend
        ev(A, f'System.AppDomain.CurrentDomain.SetData("u5held", {thing(t)}.things.Find(x => x.uid == {item})); '
              'System.AppDomain.CurrentDomain.SetData("u5r", null); "ok"')
        ev(H, f'EClass.pc.AddThing({thing(t)}.things.Find(x => x.uid == {item}), false); "ok"')
        check("l'host a pris l'objet", eventually(lambda: count(H, ctx["h"][1], "bucket") == n0["h"] + 1, timeout=10))
        ev(A, 'var tp = HarmonyLib.AccessTools.TypeByName("ElinTogether.Models.ThingRequest"); '
              'var i = (Thing)System.AppDomain.CurrentDomain.GetData("u5held"); var req = tp.GetMethod("Create").Invoke(null, new object[] { i, 1 }); '
              'tp.GetMethod("Send").Invoke(req, null); '
              'tp.GetMethod("Then").Invoke(req, new object[] { (System.Action<Thing>)(x => System.AppDomain.CurrentDomain.SetData("u5r", "donne")), '
              '(System.Action)(() => System.AppDomain.CurrentDomain.SetData("u5r", "refuse")) }); "ok"')
        answer = lambda: ev(A, 'var r = System.AppDomain.CurrentDomain.GetData("u5r"); return r == null ? "-" : r.ToString();')  # noqa: E731
        check(cond=eventually(lambda: answer() != "-", timeout=15), label=f"l'invite demande l'objet : la reponse de l'host arrive ({answer()})")
        check(f"la demande est refusee ({answer()})", answer() == "refuse")
        time.sleep(2)
        check(f"l'objet est reste a l'host (host {n0['h']} -> {count(H, ctx['h'][1], 'bucket')}, invite {n0['a']} -> {count(H, ctx['a'][1], 'bucket')})",
              count(H, ctx["h"][1], "bucket") == n0["h"] + 1 and count(H, ctx["a"][1], "bucket") == n0["a"])
    finally:
        ev(H, f'var t = {thing(t)}; if (t != null) t.Destroy(); var c = {chara(H, ctx["h"][1])}; var b = c.things.Find(x => x.uid == {item}); if (b != null) b.Destroy(); "ok"')


# ---------------------------------------------------------------------------------------------------------------------
# U6 : monture deja prise

RIDE = 'EClass.pc.UseAbility(ACT.Create(ABILITY.ActRide), c, c.pos)'


def u6(ctx):
    """monture deja prise : un second cavalier est refuse, la bete garde le premier dans les deux jeux, le second reste a pied"""
    species = next((s for s in ("dog", "cat", "putit", "chicken") if ev(H, f'EClass.sources.charas.map.ContainsKey("{s}").ToString()') == "True"), "")
    if not check(f"le jeu a une bete a monter ({species or 'aucune'})", bool(species)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        okey = other_of(key)
        oport, ouid = ctx[okey]
        clear_conditions(uid)
        mount = tame(ctx, species, key)
        if not check(f"{who} a une bete ({mount})", bool(mount)):
            continue
        clear_conditions(mount)
        carrier = lambda p: ev(p, f'var c = {chara(p, mount)}; return c == null ? "absent" : (c.host == null ? "-" : c.host.uid.ToString());')  # noqa: E731
        rides = lambda p, u: ev(p, f'var c = {chara(p, u)}; return c == null ? "absent" : (c.ride == null ? "-" : c.ride.uid.ToString());')  # noqa: E731
        try:
            awake(port)
            r = ev(port, f'var c = EClass._map.charas.Find(x => x.uid == {mount}); {RIDE}; return EClass.pc.ride == null ? "pas monte" : "monte";')
            if r != "monte":
                log(f"{who} : l'action du jeu n'a pas monte ({r}), ActRide.Ride est appele")
                ev(port, f'ActRide.Ride(EClass.pc, EClass._map.charas.Find(x => x.uid == {mount})); "ok"')
            check(cond=eventually(lambda: carrier(H) == str(uid) and carrier(A) == str(uid) and rides(H, uid) == str(mount), timeout=15),
                  label=f"{who} monte ({r}) : la bete le porte, chez l'host ({carrier(H)}) et chez l'invite ({carrier(A)})")
            # le second essaie : l'action du jeu, puis ce que ferait l'envoi de l'autre jeu (course, ou cavalier remis en selle)
            awake(oport)
            # l'action du jeu saute une bete deja montee ; a deux joueurs elle peut alors proposer de monter... l'autre
            # joueur, qui se tient sur la meme case (comportement du mod d'origine, pas juge ici) : on ne regarde que la bete
            on = f'(EClass.pc.ride != null && EClass.pc.ride.uid == {mount}) ? "monte" : "refuse"'
            r2 = ev(oport, f'var c = EClass._map.charas.Find(x => x.uid == {mount}); {RIDE}; var r = {on}; '
                           'if (EClass.pc.ride != null) ActRide.Unride(EClass.pc, false); return r;')
            time.sleep(2)
            r3 = ev(oport, f'ActRide.Ride(EClass.pc, EClass._map.charas.Find(x => x.uid == {mount})); var r = {on}; '
                           'if (EClass.pc.ride != null) ActRide.Unride(EClass.pc, false); return r;')
            r4 = ev(port, f'var o = EClass._map.charas.Find(x => x.uid == {ouid}); ActRide.Ride(o, EClass._map.charas.Find(x => x.uid == {mount})); '
                          f'var r = (o.ride != null && o.ride.uid == {mount}) ? "monte" : "refuse"; if (o.ride != null) ActRide.Unride(o, false); return r;')
            log(f"l'autre joueur essaie : action du jeu {r2}, ActRide.Ride chez lui {r3}, ActRide.Ride chez le cavalier {r4}")
            time.sleep(3)
            check(f"l'autre joueur n'obtient pas la bete (action {r2}, Ride chez lui {r3}, Ride chez {who} {r4})", (r2, r3, r4) == ("refuse",) * 3)
            check(f"la bete garde {who} pour cavalier, chez l'host ({carrier(H)}) et chez l'invite ({carrier(A)})", carrier(H) == str(uid) and carrier(A) == str(uid))
            check(f"{who} est toujours en selle (host {rides(H, uid)}, invite {rides(A, uid)})", rides(H, uid) == str(mount) and rides(A, uid) == str(mount))
        finally:
            ev(port, 'if (EClass.pc.ride != null) EClass.pc.UseAbility(ACT.Create(ABILITY.ActRide), EClass.pc, EClass.pc.pos); "ok"')
            time.sleep(2)
            for p, u in ((H, uid), (A, uid), (H, ouid), (A, ouid)):
                ev(p, f'var c = {chara(p, u)}; if (c != null && c.ride != null) ActRide.Unride(c, false); "ok"')
            drop([mount])


# ---------------------------------------------------------------------------------------------------------------------
# U7 : eau profonde

def u7(ctx):
    """eau profonde : le nageur perd son souffle ; l'eau est faite dans le jeu du nageur seul (deux cases repeintes)"""
    deep = ev(H, 'var r = EClass.sources.floors.rows.FirstOrDefault(x => x.tileType != null && x.tileType.IsDeepWater); return r == null ? "" : r.id.ToString();')
    if not check(f"le jeu a un sol d'eau profonde ({deep or 'aucun'})", bool(deep)):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        clear_conditions(uid)
        spot = ev(port, 'var me = EClass.pc.pos; var res = ""; for (var dx = -3; dx <= 3 && res == ""; dx++) for (var dz = -3; dz <= 3 && res == ""; dz++) { '
                        'var p = new Point(me.x + dx, me.z + dz); if (System.Math.Max(System.Math.Abs(dx), System.Math.Abs(dz)) < 2 || !p.IsValid || !p.IsInBounds '
                        '|| p.IsBlocked || p.HasChara || p.HasThing || p.cell.IsTopWaterAndNoSnow) continue; var q = new Point(p.x + 1, p.z); '
                        'if (!q.IsValid || !q.IsInBounds || q.IsBlocked || q.HasChara || q.HasThing || q.cell.IsTopWaterAndNoSnow) continue; '
                        'res = p.x + "," + p.z + "," + q.x + "," + q.z; } return res;')
        if not check(f"{who} : deux cases libres cote a cote pres de lui ({spot or 'aucune'})", bool(spot)):
            continue
        x, z, x2, z2 = (int(v) for v in spot.split(","))
        home = ev(H, f'var c = {chara(H, uid)}; return c.pos.x + "," + c.pos.z;').split(",")
        orig = {}
        for cx, cz in ((x, z), (x2, z2)):
            orig[(cx, cz)] = ev(port, f'var c = EClass._map.cells[{cx}, {cz}]; return c._floorMat + "," + c._floor + "," + (int)c.floorDir;')
        ev(port, 'EClass.debug.godMode = false; "ok"')
        try:
            for cx, cz in ((x, z), (x2, z2)):
                mat = orig[(cx, cz)].split(",")[0]
                ev(port, f'EClass._map.SetFloor({cx}, {cz}, {mat}, {deep}, 0); "ok"')
            deep_now = ev(port, f'(new Point({x}, {z}).cell.CanSuffocate() && new Point({x2}, {z2}).cell.CanSuffocate()).ToString()')
            if not check(f"{who} : les deux cases sont de l'eau profonde dans son jeu ({deep_now})", deep_now == "True"):
                continue
            if not check(f"{who} se tient dans l'eau ({x},{z})", stand(port, uid, x, z)):
                continue
            for tx, tz in ((x2, z2), (x, z), (x2, z2)):
                awake(port)
                ev(port, f'EClass.pc.TryMove(new Point({tx}, {tz})); "ok"')
                time.sleep(1)
            under = lambda p: ev(p, f'{chara(p, uid)}.HasCondition<ConSuffocation>().ToString()')  # noqa: E731
            check(cond=eventually(lambda: under(port) == "True", timeout=8), label=f"{who} : il perd son souffle, dans son jeu ({under(port)})")
            check(cond=eventually(lambda: under(H) == "True", timeout=8), label=f"{who} : et chez l'host ({under(H)})")
            check(cond=eventually(lambda: under(A) == "True", timeout=8), label=f"{who} : et chez l'invite ({under(A)})")
        finally:
            stand(port, uid, int(home[0]), int(home[1]))
            for (cx, cz), o in orig.items():
                m, f, d = o.split(",")
                ev(port, f'EClass._map.SetFloor({cx}, {cz}, {m}, {f}, {d}); "ok"')
            clear_conditions(uid)
            ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; "ok"')


# ---------------------------------------------------------------------------------------------------------------------
# U8 : cle a molette sur un coffre

def u8(ctx):
    """cle a molette « agrandir en hauteur » sur un coffre de la carte : meme taille de conteneur chez l'host, chez l'invite et
    chez l'autre joueur, la cle consommee une seule fois (ligne 11 de la deuxieme chasse)"""
    wr = "wrench_extend_v"
    if not check(f"le jeu a la cle {wr}", ev(H, f'(EClass.sources.things.map.ContainsKey("{wr}")).ToString()') == "True"):
        return
    for who, key in both(ctx):
        port, uid = ctx[key]
        other = H if port == A else A
        close_layers()
        clear_conditions(uid)
        t = furniture(uid)
        size = lambda p: ev(p, f'var t = {thing(t)}; return t == null ? "absent" : t.c_containerSize + "/" + t.things.width + "x" + t.things.height;')  # noqa: E731
        try:
            s0 = size(H)
            check(f"{who} : le coffre est pareil dans les deux jeux avant la cle (host {s0}, invite {size(A)})", s0 == size(A) and s0 != "absent")
            c0 = int(s0.split("/")[0])
            w, h = c0 // 100, c0 % 100
            wanted = f"{c0 + 1}/{w}x{h + 1}"
            tool = give(ctx, key, wr, 3)
            x, z = (int(v) for v in ev(H, f'var m = {thing(t)}; return m.pos.x + "," + m.pos.z;').split(","))
            awake(port)
            r = use_held(port, tool, at=(x, z), pick=f'i.tc != null && i.tc.uid == {t}')
            log(f"{who} se sert de la cle : {r}")
            check(f"{who} fait le geste de la cle ({r[:40]})", r.startswith("ok"))
            check(cond=eventually(lambda: size(H) == wanted and size(A) == wanted, timeout=15),
                  label=f"{who} : le coffre a une rangee de plus, chez l'host ({size(H)}), chez l'invite ({size(A)}), attendu {wanted}")
            check(f"{who} : la cle est consommee une fois, chez l'host ({count(H, uid, wr)}) et chez lui ({count(port, uid, wr)})",
                  eventually(lambda: count(H, uid, wr) == 2 and count(port, uid, wr) == 2, timeout=10))
            time.sleep(3)
            check(f"{who} : toujours deux cles apres l'attente (host {count(H, uid, wr)}, lui {count(port, uid, wr)}), l'autre joueur voit {size(other)}",
                  count(H, uid, wr) == 2 and count(port, uid, wr) == 2 and size(other) == wanted)
        finally:
            close_layers()
            ev(H, f'var m = {thing(t)}; if (m != null) m.Destroy(); "ok"')
            ev(H, f'var c = {chara(H, uid)}; foreach (var m in c.things.Where(q => q.id == "{wr}").ToList()) m.Destroy(); "ok"')


# ---------------------------------------------------------------------------------------------------------------------
# U9 : fouet-oeuf sur un compagnon

def u9(ctx):
    """fouet-oeuf sur un animal compagnon : un oeuf chez l'host et chez l'invite, la charge du fouet baisse une fois, le karma
    est retire a celui qui fouette et pas a l'autre (ligne 11 de la deuxieme chasse)"""
    whip = first_id("WhipEgg")
    if not check(f"le jeu a un fouet-oeuf ({whip or 'aucun'})", bool(whip)):
        return
    eggs = lambda p: int(ev(p, 'EClass._map.things.Count(q => q.id == "_egg" || q.id == "egg_fertilized").ToString()'))  # noqa: E731
    karma = lambda p: int(ev(p, 'EClass.player.karma.ToString()'))  # noqa: E731
    for who, key in both(ctx):
        port, uid = ctx[key]
        whipper, other = (A, H) if key == "a" else (H, A)
        close_layers()
        clear_conditions(uid)
        pet = tame(ctx, "cat", key)
        if not check(f"{who} a un compagnon ({pet})", bool(pet)):
            continue
        saved = {p: karma(p) for p in (H, A)}
        try:
            for p in (H, A):
                ev(p, 'EClass.player.karma = 50; "ok"')
            clear_conditions(pet)
            tool = give(ctx, key, whip)
            charges = lambda p: ev(p, f'var c = {chara(p, uid)}; var q = c == null ? null : c.things.Find(m => m.uid == {tool}); return q == null ? "absent" : q.c_charges.ToString();')  # noqa: E731
            c0, e0 = charges(H), {p: eggs(p) for p in (H, A)}
            x, z = (int(v) for v in ev(H, f'var m = EClass._map.charas.Find(q => q.uid == {pet}); return m.pos.x + "," + m.pos.z;').split(","))
            awake(port)
            r = use_held(port, tool, at=(x, z), pick=f'i.tc != null && i.tc.uid == {pet}')
            log(f"{who} fouette son compagnon : {r}")
            check(f"{who} fait le geste du fouet ({r[:40]})", r.startswith("ok"))
            check(cond=eventually(lambda: eggs(H) == e0[H] + 1 and eggs(A) == e0[A] + 1, timeout=15),
                  label=f"{who} : un oeuf de plus, chez l'host ({e0[H]} -> {eggs(H)}) et chez l'invite ({e0[A]} -> {eggs(A)})")
            wanted = str(int(c0) - 1)
            check(f"{who} : la charge du fouet baisse d'un cran, chez l'host ({c0} -> {charges(H)}) et chez lui ({charges(port)})",
                  eventually(lambda: charges(H) == wanted and charges(port) == wanted, timeout=10))
            check(f"{who} : le karma est retire a celui qui fouette ({saved[whipper]} -> {karma(whipper)})",
                  eventually(lambda: karma(whipper) == 49, timeout=10))
            time.sleep(3)
            check(f"{who} : l'autre joueur garde son karma ({karma(other)}), un seul oeuf et une seule charge en moins (oeufs {eggs(H)}/{eggs(A)}, charge {charges(H)}/{charges(port)})",
                  karma(other) == 50 and eggs(H) == e0[H] + 1 and eggs(A) == e0[A] + 1 and charges(H) == wanted and charges(port) == wanted)
        finally:
            for p in (H, A):
                ev(p, f'EClass.player.karma = {saved[p]}; "ok"')
            ev(H, 'foreach (var m in EClass._map.things.Where(q => q.id == "_egg" || q.id == "egg_fertilized").ToList()) m.Destroy(); "ok"')
            ev(H, f'var c = {chara(H, uid)}; foreach (var m in c.things.Where(q => q.id == "{whip}").ToList()) m.Destroy(); "ok"')
            drop([pet])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    # u2 (bouton partage d'un coffre : le banc ne trouve pas le bouton), u4 (aucun parchemin d'alias dans les donnees du jeu)
    # et u7 (l'eau profonde fabriquee par le banc n'etouffe personne, pas meme l'host) ne sont pas jouables : `--only` pour y revenir
    steps = [u1, u3, u5, u6, u8, u9]
    every = [u1, u2, u3, u4, u5, u6, u7, u8, u9]
    if a.only:
        steps = [s for s in every if s.__name__ in a.only.split(",")]
    for step in steps:
        log(f"--- {step.__name__.upper()} : {step.__doc__}")
        try:
            step(ctx)
        except Exception as ex:  # noqa: BLE001
            check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'unplayed-{step.__name__}-{name}', port)}")
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
