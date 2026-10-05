"""La base (le foyer) : quatre gestes qui se paient. La recherche et les competences du foyer sont de vraies demandes a
l'host (BaseRequestDelta, etape 2 du conseil 4) : l'host verifie le paiement dans son etat, paie, fait, repond, et l'etat
de la base revient chez tous les joueurs (BaseStateDelta). Les plans du marchand et l'amelioration du foyer (etapes de
dialogue `_buyPlan` et `_upgradeHearth`) restent refuses a l'invite avec un message (RemoteBasePaidPatch) : ils payaient
pour rien. Pour chaque ligne, le meme geste par l'invite puis par l'host. Test court, sur des instances deja lancees
(host + 1 client, tous les deux a la Prairie, qui est une base).

    python _tools/mp_test.py
    python _tools/base_suite.py            # ou --only b1,b3

B1  recherche : la fenetre du tableau de recherche (LayerTech), clic sur un plan puis « buy » : l'host paie en connaissance
    et le plan avance ; l'invite aussi, par une demande a l'host : payee une fois chez l'host, le plan avance chez l'host
    ET dans la copie de l'invite (connaissance, plans, fenetre rafraichie) ; l'host refuse quand sa connaissance ne suffit
    pas (la copie de l'invite, en retard, le croyait riche) : rien ne change nulle part ; sans de quoi payer le menu ne
    s'ouvre pas. Apres une recherche de l'HOST, l'invite voit la meme connaissance et les memes plans.
B2  plans du marchand : l'argent de la base paie un plan (ResearchManager.AddPlan) : l'host l'achete ; l'invite est refuse,
    ni argent de la base debite, ni plan en plus.
B3  amelioration du foyer : l'or du joueur paie, le foyer monte de niveau : l'host l'obtient ; l'invite est refuse, ni or
    debite ni niveau en plus.
B4  competence du foyer (fenetre du foyer, onglet competences) : le platine du joueur paie, la competence monte de un :
    l'host l'obtient ; l'invite aussi, par une demande a l'host (la boite « oui / non » du jeu reste) : platine debite une
    fois (chez l'host et dans son sac), competence montee chez l'host ET dans la copie de l'invite ; sans de quoi payer la
    boite ne s'ouvre pas. Apres la competence de l'HOST, l'invite voit le meme niveau.

Ce que le banc ne joue pas comme un joueur :
- B1 : le menu « buy » du jeu se referme sans souris dessus ; le banc refait ce menu a l'identique (meme cible, meme
  entree, meme action que le clic du plan) et clique son bouton.
- B1, B4 : les fenetres s'ouvrent par l'appel que font le tableau de recherche et le bouton du foyer (AddLayer<LayerTech>,
  AddLayer<LayerHome> puis RefreshFeat, ce que fait l'onglet « skills ») ; les clics sont les vrais (le plan, le menu
  « buy » ou son clic sur le bouton du menu, la competence, « Yes » de la boite). Les ressources de la base sont posees
  directement (champ `value`, sans passer par Mod, donc sans delta) dans les deux jeux, et remises ensuite. Si le menu
  « buy » de l'host n'est pas retrouve, le banc fait ce que fait « buy » (Mod puis CompletePlan).
- B2, B3 : aucun personnage du jeu installe ne propose ces deux choix (le dialogue du foyer et du marchand de plans :
  etapes `_buyPlan` et `_upgradeHearth` de DramaCustomSequence, aucune feuille de dialogue du jeu n'y saute ; le foyer monte
  tout seul avec son experience). Le banc parle a un guerisseur (vrai dialogue) puis fait le saut que ferait le choix :
  DramaSequence.Play("_buyPlan") ; ce qui suit (fenetre des plans, clic sur un plan ; « Yes » du foyer, fermeture du
  dialogue qui fait monter le foyer) est comme un joueur.
- ce que le banc ne verifie pas : les textes affiches a l'invite (« Only the host can do this for now. », la ligne de refus
  de l'host, « une demande attend sa reponse » : des fenetres du mod, pas des lignes du journal du jeu) ; il les voit a
  l'ecran. Ni les recettes, regles ou talents du foyer qu'une recherche peut donner (cela depend du plan choisi).
- les ressources et les plans sont remis a la fin ; le niveau et l'experience du foyer aussi (le reste de Upgrade() ne l'est pas).
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import awake, both, chara, close_layers, count, give  # noqa: E402
from equal2_suite import drop, seen, spawn  # noqa: E402
from hunt_suite import hang_up, pick, talk  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552

BRANCH = "EClass._zone.branch"
MENU = "UnityEngine.Object.FindObjectsOfType<UIContextMenuItem>().Where(i => i.gameObject.activeInHierarchy)"


def snap(port):
    """La copie de la base de ce jeu : connaissance, argent de la base, plans, plans finis, somme des rangs, niveau du foyer, experience."""
    r = ev(port, f'var b = {BRANCH}; return b.resources.knowledge.value + "," + b.resources.money.value + "," + b.researches.plans.Count + "," + '
                 'b.researches.finished.Count + "," + b.researches.plans.Sum(x => x.rank) + "," + b.lv + "," + b.exp;')
    return dict(zip(("kn", "money", "plans", "done", "ranks", "lv", "exp"), (int(v) for v in r.split(","))))


def put(port, **res):
    """Pose directement ces ressources de la base (`kn`, `money`) dans ce jeu : le champ, pas Mod, donc aucun delta."""
    for key, name in (("kn", "knowledge"), ("money", "money")):
        if key in res:
            ev(port, f'{BRANCH}.resources.{name}.value = {res[key]}; "ok"')


def is_base(port):
    return ev(port, 'EClass._zone.IsPCFaction.ToString()') == "True"


def menu_items(port):
    return int(ev(port, f'{MENU}.Count().ToString()'))


def hide_menus(port):
    ev(port, 'foreach (var m in UnityEngine.Object.FindObjectsOfType<UIContextMenu>()) if (m.gameObject.activeInHierarchy) m.Hide(); "ok"')


def click_yes(port):
    """Clique « Yes » dans la boite oui/non du jeu."""
    return ev(port, 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return "pas de boite"; '
                    'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(true).FirstOrDefault(x => '
                    'x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.StartsWith("Yes"))); '
                    'if (b == null) return "pas de bouton"; b.onClick.Invoke(); return "clic";')


def dialog_open(port):
    return ev(port, '(EClass.ui.layers.OfType<Dialog>().Any()).ToString()') == "True"


def healer_id():
    return ev(H, 'EClass.sources.charas.rows.First(x => x.trait != null && x.trait.Length > 0 && x.trait[0] == "Healer").id')


def step_played(port, step):
    """Jouer l'etape de dialogue que le choix ferait sauter ; renvoie la derniere etape jouee (celle qui est a l'ecran)."""
    ev(port, f'LayerDrama.Instance.drama.sequence.Play("{step}"); "ok"')
    time.sleep(1.5)
    return ev(port, 'LayerDrama.Instance.drama.sequence.lastStep ?? "-"')


def same_research(a, b):
    """Les deux copies de la recherche d'une base : connaissance, plans, plans finis, somme des rangs."""
    return all(a[k] == b[k] for k in ("kn", "plans", "done", "ranks"))


def open_plan(port, pid):
    """Ouvre le tableau de recherche de ce joueur et clique le plan : le nombre de choix du menu « buy » qui s'ouvre (None si la fenetre ne montre pas le plan)."""
    hide_menus(port)
    ev(port, 'EClass.ui.RemoveLayer<LayerTech>(); EClass.ui.AddLayer<LayerTech>(); "ok"')
    find = f'var l = EClass.ui.layers.OfType<LayerTech>().FirstOrDefault(); var it = l == null ? null : l.GetComponentsInChildren<ItemResearch>().FirstOrDefault(x => x.plan != null && x.plan.id == "{pid}"); '
    if not eventually(lambda: ev(port, find + '(it != null).ToString()') == "True", timeout=10):
        return None
    # le menu « buy » du jeu se referme tout de suite quand aucune souris n'est dessus : le banc ne peut pas le cliquer.
    # On regarde la porte que le clic du plan regarde (CanCompletePlan), et `buy` refait ce menu a l'identique
    return 1 if ev(port, find + 'EClass.Branch.researches.CanCompletePlan(it.plan).ToString()') == "True" else 0


def window_shows(port, pid):
    """La fenetre de recherche ouverte de ce joueur montre-t-elle encore ce plan ?"""
    return ev(port, f'var l = EClass.ui.layers.OfType<LayerTech>().FirstOrDefault(); (l != null && l.GetComponentsInChildren<ItemResearch>().Any(x => x.plan != null && x.plan.id == "{pid}")).ToString()') == "True"


def b1(ctx):
    """recherche : le joueur ouvre le tableau, clique un plan puis « buy » ; l'host paie (une fois) et le plan avance, la copie de l'invite suit ; refus propre sans de quoi payer"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        saved = {p: snap(p) for p in (H, A)}
        # un plan a finir : le moins cher de ceux de l'host (ajoute dans les deux jeux s'il n'y en a pas)
        pid = ev(H, f'var b = {BRANCH}; if (b.researches.plans.Count == 0) {{ b.researches.AddPlan(EClass.sources.researches.rows.First(x => !b.researches.HasPlan(x.id)).id); }} '
                    'return b.researches.plans.OrderBy(x => x.source.tech).First().id;')
        tech = int(ev(H, f'EClass.sources.researches.map["{pid}"].tech.ToString()'))
        added, kept = [], {}
        for p in (H, A):
            if ev(p, f'{BRANCH}.researches.HasPlan("{pid}").ToString()') != "True":
                ev(p, f'{BRANCH}.researches.AddPlan("{pid}"); "ok"')
                added.append(p)
            else:
                kept[p] = ev(p, f'var x = {BRANCH}.researches.plans.First(y => y.id == "{pid}"); return x.rank + "," + x.exp;')

        def put_plan(p, present=True):
            """Remet ce plan, tel qu'au depart (rang et experience d'avant, ou tout neuf), dans ce jeu ; ou l'en retire."""
            ev(p, f'var b = {BRANCH}; b.researches.finished.RemoveAll(x => x.id == "{pid}"); b.researches.plans.RemoveAll(x => x.id == "{pid}"); "ok"')
            if present and p in added:
                ev(p, f'{BRANCH}.researches.AddPlan("{pid}"); "ok"')
            elif present:
                rank, exp = kept[p].split(",")
                ev(p, f'var n = ResearchPlan.Create("{pid}"); n.rank = {rank}; n.exp = {exp}; {BRANCH}.researches.AddPlan(n); "ok"')
            ev(p, f'{BRANCH}.researches.newPlans.Clear(); "ok"')

        def setup(kn_host, kn_guest):
            """Le plan neuf dans les deux jeux et la connaissance de chacun (le champ, pas Mod : aucun delta) ; renvoie ce que voit chacun."""
            for p, kn in ((H, kn_host), (A, kn_guest)):
                put_plan(p)
                put(p, kn=kn)
            return {p: snap(p) for p in (H, A)}

        def buy():
            # le menu que fait le clic du plan dans le jeu (ItemResearch) : meme cible, meme entree « buy », meme action ;
            # le banc clique son bouton sans attendre l'affichage
            ev(port, f'var l = EClass.ui.layers.OfType<LayerTech>().First(); var it = l.GetComponentsInChildren<ItemResearch>().First(x => x.plan != null && x.plan.id == "{pid}"); '
                     'var m = EClass.ui.CreateContextMenuInteraction().SetHighlightTarget(it.button1); '
                     'var b = m.AddButton("buy", () => { var br = EClass.Branch; br.resources.knowledge.Mod(-it.plan.source.tech); br.researches.CompletePlan(it.plan); l.RefreshTech(); }); '
                     'b.onClick.Invoke(); "ok"')

        try:
            if who == "l'invite":
                # 1) de quoi payer : le menu « buy » s'ouvre ; la demande part a l'host, qui paie une fois et fait avancer le plan
                before = setup(tech * 3 + 100, tech * 3 + 100)
                check(f"{who} : le plan {pid} ({tech} de connaissance) est dans les deux jeux, la connaissance suffit ({before[H]['kn']} et {before[A]['kn']})",
                      before[H]["plans"] > 0 and before[A]["plans"] > 0 and before[A]["kn"] >= tech)
                awake(port)
                n = open_plan(port, pid)
                if not check(f"{who} : le menu « buy » s'ouvre ({n} choix)", n == 1):
                    continue
                buy()
                if not check(f"{who} : la connaissance de la base est debitee chez l'host",
                             eventually(lambda: snap(H)["kn"] != before[H]["kn"], timeout=15)):
                    continue
                time.sleep(3)  # un deuxieme paiement, s'il y en avait un, arriverait ici
                after = {p: snap(p) for p in (H, A)}
                check(f"{who} : payee une fois, chez l'host (connaissance {before[H]['kn']} -> {after[H]['kn']}, plan a {tech})", after[H]["kn"] == before[H]["kn"] - tech)
                check(f"{who} : le plan avance chez l'host ({before[H]['done']},{before[H]['ranks']} -> {after[H]['done']},{after[H]['ranks']})",
                      after[H]["done"] > before[H]["done"] or after[H]["ranks"] > before[H]["ranks"])
                check(f"{who} : sa copie de la base suit l'host ({snap(A)} / {snap(H)})",
                      eventually(lambda: same_research(snap(A), snap(H)), timeout=10))
                check(f"{who} : sa fenetre de recherche est rafraichie (plan encore liste : {window_shows(port, pid)}, encore a faire : {snap(A)['plans'] > 0})",
                      window_shows(port, pid) == (ev(A, f'{BRANCH}.researches.plans.Any(x => x.id == "{pid}").ToString()') == "True"))
                # 2) l'invite croit pouvoir payer (sa copie de la connaissance), l'host non : refus, rien ne change nulle part
                before = setup(tech - 1, tech * 3 + 100)
                n = open_plan(port, pid)
                if check(f"{who} : (sa copie le croit riche) le menu « buy » s'ouvre ({n} choix)", n == 1):
                    buy()
                    time.sleep(3)
                    after = {p: snap(p) for p in (H, A)}
                    check(f"{who} : l'host refuse : rien n'est debite ni ne change chez lui ({before[H]} -> {after[H]})", after[H] == before[H])
                    check(f"{who} : rien ne change dans sa copie ({before[A]} -> {after[A]})", after[A] == before[A])
                # 3) pas de quoi payer, meme dans sa copie : le prix est rouge, le jeu ne propose rien
                before = setup(tech - 1, tech - 1)
                n = open_plan(port, pid)
                check(f"{who} : sans de quoi payer le menu « buy » ne s'ouvre pas ({n} choix)", n == 0)
                after = {p: snap(p) for p in (H, A)}
                check(f"{who} : rien ne change chez l'host ni chez lui ({before} -> {after})", after == before)
            else:
                before = setup(tech * 3 + 100, tech * 3 + 100)
                check(f"{who} : le plan {pid} ({tech} de connaissance) est dans les deux jeux, la connaissance suffit ({before[H]['kn']} et {before[A]['kn']})",
                      before[H]["plans"] > 0 and before[A]["plans"] > 0 and before[H]["kn"] >= tech)
                awake(port)
                n = open_plan(port, pid)
                if n:
                    buy()
                else:
                    # le banc ne retrouve pas toujours le menu « buy » de l'host (menu contextuel du jeu) : on verifie que le jeu lui
                    # laisse la recherche, puis on fait ce que fait « buy »
                    allowed = ev(port, f'var b = {BRANCH}; return b.researches.CanCompletePlan(b.researches.plans.First(x => x.id == "{pid}")).ToString();')
                    if not check(f"{who} : la recherche lui reste permise ({allowed})", allowed == "True"):
                        continue
                    ev(port, f'var b = {BRANCH}; var q = b.researches.plans.First(x => x.id == "{pid}"); b.resources.knowledge.Mod(-q.source.tech); b.researches.CompletePlan(q); "ok"')
                time.sleep(1)
                after = {p: snap(p) for p in (H, A)}
                check(f"{who} : la connaissance est debitee ({before[H]['kn']} -> {after[H]['kn']}, plan a {tech})", after[H]["kn"] == before[H]["kn"] - tech)
                check(f"{who} : le plan avance ({before[H]['done']},{before[H]['ranks']} -> {after[H]['done']},{after[H]['ranks']})",
                      after[H]["done"] > before[H]["done"] or after[H]["ranks"] > before[H]["ranks"])
                # la base revient chez l'invite : sa copie n'avait pas bouge (connaissance posee a part), elle prend celle de l'host
                check(f"{who} : l'invite voit la meme chose ({snap(A)} / {snap(H)})",
                      eventually(lambda: same_research(snap(A), snap(H)), timeout=10))
        finally:
            hide_menus(port)
            ev(port, 'EClass.ui.RemoveLayer<LayerTech>(); "ok"')
            for p in (H, A):
                put_plan(p, present=p not in added)
                put(p, kn=saved[p]["kn"])


def zone_name(port):
    return ev(port, 'EClass._zone.Name')


def b2(ctx):
    """plans du marchand : l'argent de la base paie un plan ; l'host l'achete, l'invite est refuse (ni argent debite, ni plan en plus)"""
    healer = healer_id()
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        saved = {p: snap(p) for p in (H, A)}
        known = {p: ev(p, f'string.Join(",", {BRANCH}.researches.plans.Concat({BRANCH}.researches.finished).Select(x => x.id))') for p in (H, A)}
        for p in (H, A):
            put(p, money=1_000_000)
        before = {p: snap(p) for p in (H, A)}
        priest = spawn(uid, healer, "Friend")
        try:
            if not check(f"{who} : un personnage est a cote de lui ({priest}), le jeu a des plans a vendre",
                         priest and eventually(lambda: seen(port, priest), timeout=15)
                         and ev(port, f'EClass.sources.researches.rows.Any(r => r.money > 0 && !{BRANCH}.researches.HasPlan(r.id)).ToString()') == "True"):
                continue
            if not check(f"{who} : il parle a ce personnage, l'etape des plans existe", talk(port, priest)
                         and ev(port, 'LayerDrama.Instance.drama.sequence.steps.ContainsKey("_buyPlan").ToString()') == "True"):
                continue
            step = step_played(port, "_buyPlan")
            opened = lambda: ev(port, '(EClass.ui.layers.OfType<LayerList>().Any()).ToString()') == "True"  # noqa: E731
            if who == "l'invite":
                time.sleep(1.5)
                check(f"{who} : la liste des plans ne s'ouvre pas (etape a l'ecran : {step})", not opened() and step != "_buyPlan")
            else:
                if not check(f"{who} : la liste des plans s'ouvre (etape a l'ecran : {step})", step == "_buyPlan" and eventually(opened, timeout=10)):
                    continue
                r = ev(port, 'var it = EClass.ui.layers.OfType<LayerList>().Last().GetComponentsInChildren<ItemGeneral>().FirstOrDefault(x => x.gameObject.activeInHierarchy); '
                             'if (it == null) return "pas de plan"; it.button1.onClick.Invoke(); return "clic";')
                log(f"{who} clique le premier plan : {r}")
                time.sleep(1.5)
            after = {p: snap(p) for p in (H, A)}
            if who == "l'invite":
                check(f"{who} : l'argent de la base n'est pas debite chez l'host ({before[H]['money']} -> {after[H]['money']})", after[H]["money"] == before[H]["money"])
                check(f"{who} : aucun plan en plus chez l'host ({before[H]['plans']} -> {after[H]['plans']})", after[H]["plans"] == before[H]["plans"])
                check(f"{who} : rien ne change dans sa copie ({before[A]} -> {after[A]})", after[A] == before[A])
            else:
                check(f"{who} : l'argent de la base est debite ({before[H]['money']} -> {after[H]['money']})", after[H]["money"] < before[H]["money"])
                check(f"{who} : un plan en plus ({before[H]['plans']} -> {after[H]['plans']})", after[H]["plans"] == before[H]["plans"] + 1)
        finally:
            ev(port, 'EClass.ui.RemoveLayer<LayerList>(); "ok"')
            hang_up(port)
            drop([priest])
            for p in (H, A):
                ev(p, f'var b = {BRANCH}; var keep = "{known[p]}".Split(\',\'); b.researches.plans.RemoveAll(x => !keep.Contains(x.id)); b.researches.newPlans.Clear(); "ok"')
                put(p, money=saved[p]["money"])


def b3(ctx):
    """amelioration du foyer : l'or du joueur paie, le foyer monte ; l'host l'obtient, l'invite est refuse (ni or debite, ni niveau en plus)"""
    healer = healer_id()
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        saved = {p: snap(p) for p in (H, A)}
        cost = int(ev(H, f'{BRANCH}.GetUpgradeCost().ToString()'))
        give(ctx, key, "money", cost + 1000)
        gold0 = count(H, uid, "money")
        before = {p: snap(p) for p in (H, A)}
        priest = spawn(uid, healer, "Friend")
        try:
            if not check(f"{who} : un personnage est a cote de lui ({priest}), il a de quoi payer ({gold0} pour {cost})",
                         priest and gold0 >= cost and eventually(lambda: seen(port, priest), timeout=15)):
                continue
            if not check(f"{who} : il parle a ce personnage, l'etape du foyer existe", talk(port, priest)
                         and ev(port, 'LayerDrama.Instance.drama.sequence.steps.ContainsKey("_upgradeHearth").ToString()') == "True"):
                continue
            step = step_played(port, "_upgradeHearth")
            if who == "l'invite":
                check(f"{who} : le dialogue du foyer ne se joue pas (etape a l'ecran : {step})", step != "_upgradeHearth")
                time.sleep(1)
            else:
                # aucun choix du jeu installe ne mene a cette etape : si le banc n'arrive pas a la jouer chez l'host, on le dit
                if step != "_upgradeHearth":
                    log(f"{who} : le banc n'a pas pu jouer l'etape du foyer (a l'ecran : {step}) : pas verifie cote host")
                    continue
                said = pick(port, "Yes") == "clic"
                check(f"{who} : il dit oui", said)
                time.sleep(2)
                ev(port, 'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); "ok"')
                time.sleep(2)
            after = {p: snap(p) for p in (H, A)}
            gold1 = count(H, uid, "money")
            if who == "l'invite":
                check(f"{who} : l'or n'est pas debite chez l'host ({gold0} -> {gold1}) ni chez lui ({count(port, uid, 'money')})", gold1 == gold0 == count(port, uid, "money"))
                check(f"{who} : le foyer ne monte pas, chez l'host ({before[H]['lv']} -> {after[H]['lv']}) ni chez lui ({before[A]['lv']} -> {after[A]['lv']})",
                      after[H]["lv"] == before[H]["lv"] and after[A]["lv"] == before[A]["lv"])
            else:
                check(f"{who} : l'or est debite ({gold0} -> {gold1}, prix {cost})", gold1 == gold0 - cost)
                check(f"{who} : le foyer monte ({before[H]['lv']} -> {after[H]['lv']})",
                      eventually(lambda: snap(H)["lv"] == before[H]["lv"] + 1, timeout=10))
        finally:
            hang_up(port)
            drop([priest])
            for p in (H, A):
                ev(p, f'var b = {BRANCH}; b.lv = {saved[p]["lv"]}; b.exp = {saved[p]["exp"]}; "ok"')
            ev(H, f'var c = {chara(H, uid)}; foreach (var t in c.things.Where(m => m.id == "money").ToList()) t.Destroy(); "ok"')


def b4(ctx):
    """competence du foyer : le platine du joueur paie, la competence monte de un ; payee une fois chez l'host, la copie de l'invite suit ; refus propre sans de quoi payer"""
    pick_skill = (f'var b = {BRANCH}; var e = b.elements.dict.Values.Where(x => (x.Value > 0 || x.vBase > 0) && x.source.category != "policy" && x.source.category != "landfeat" && '
                  '!x.HasTag("hidden") && x.ValueWithoutLink > 0 && x.source.cost[0] != 0 && b.GetTechUpgradeCost(x) > 0).FirstOrDefault(); ')
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        sid = ev(H, pick_skill + 'return e == null ? "" : e.id.ToString();')
        if not check(f"{who} : le foyer a une competence a monter ({sid or 'aucune'})", bool(sid)):
            continue
        price = lambda: int(ev(H, f'{BRANCH}.GetTechUpgradeCost({BRANCH}.elements.GetElement({sid})).ToString()'))  # noqa: E731
        cost = price()
        give(ctx, key, "money2", cost + 5)
        gold0 = count(H, uid, "money2")
        level = lambda p: int(ev(p, f'{BRANCH}.elements.Value({sid}).ToString()'))  # noqa: E731
        before = (level(H), level(A))
        # le bouton de la competence dans la liste du foyer de ce joueur (la liste est refaite quand l'etat de la base change)
        find = f'var it = LayerHome.Instance.listFeat.GetComponentsInChildren<ButtonElement>().FirstOrDefault(x => x.e != null && x.e.id == {sid}); '
        try:
            check(f"{who} : il a de quoi payer ({gold0} de platine pour {cost})", gold0 >= cost)
            awake(port)
            ev(port, 'EClass.ui.AddLayer<LayerHome>(); "ok"')
            if not check(f"{who} : la fenetre du foyer est ouverte", eventually(lambda: ev(port, '(LayerHome.Instance != null).ToString()') == "True", timeout=10)):
                continue
            ev(port, 'LayerHome.Instance.RefreshFeat(); "ok"')
            if not check(f"{who} : la liste des competences montre celle-la", eventually(lambda: ev(port, find + '(it != null).ToString()') == "True", timeout=10)):
                continue
            ev(port, find + 'it.onClick.Invoke(); "ok"')
            time.sleep(1)
            if not check(f"{who} : la boite « oui / non » s'ouvre", eventually(lambda: dialog_open(port), timeout=5)):
                continue
            log(f"{who} dit oui : {click_yes(port)}")
            if who == "l'invite":
                # la demande part a l'host : il debite le platine de l'invite (dans le sac qu'il tient) et monte la competence
                if not check(f"{who} : la competence monte chez l'host", eventually(lambda: level(H) == before[0] + 1, timeout=15)):
                    continue
                time.sleep(3)  # un deuxieme paiement, s'il y en avait un, arriverait ici
                gold1 = count(H, uid, "money2")
                check(f"{who} : le platine est debite une fois chez l'host ({gold0} -> {gold1}, prix {cost})", gold1 == gold0 - cost)
                check(f"{who} : le platine est debite dans son sac ({gold0} -> {count(port, uid, 'money2')})",
                      eventually(lambda: count(port, uid, "money2") == gold0 - cost, timeout=10))
                check(f"{who} : la competence a monte de un chez l'host ({before[0]} -> {level(H)}) et dans sa copie ({before[1]} -> {level(A)})",
                      level(H) == before[0] + 1 and eventually(lambda: level(A) == level(H), timeout=10))
                # pas de quoi payer la suivante : le jeu refuse avant la boite, rien ne part
                left = count(port, uid, "money2")
                if left < price():
                    mark = (level(H), level(A), count(H, uid, "money2"))
                    eventually(lambda: ev(port, find + '(it != null).ToString()') == "True", timeout=10)
                    ev(port, find + 'it.onClick.Invoke(); "ok"')
                    time.sleep(2)
                    check(f"{who} : sans de quoi payer ({left} de platine pour {price()}) la boite ne s'ouvre pas", not dialog_open(port))
                    check(f"{who} : rien ne change nulle part ({mark} -> {(level(H), level(A), count(H, uid, 'money2'))})",
                          (level(H), level(A), count(H, uid, "money2")) == mark)
                else:
                    log(f"{who} : il lui reste assez de platine ({left}) : refus sans de quoi payer non verifie")
            else:
                time.sleep(1.5)
                gold1 = count(H, uid, "money2")
                check(f"{who} : le platine est debite ({gold0} -> {gold1}, prix {cost})", gold1 == gold0 - cost)
                check(f"{who} : la competence monte de un, chez l'host ({before[0]} -> {level(H)})", level(H) == before[0] + 1)
                # la base revient chez l'invite : sa copie prend la valeur de l'host
                check(f"{who} : l'invite voit la meme competence ({before[1]} -> {level(A)})", eventually(lambda: level(A) == level(H), timeout=10))
        finally:
            ev(port, 'EClass.ui.RemoveLayer<LayerHome>(); "ok"')
            close_layers()
            ev(H, f'var c = {chara(H, uid)}; foreach (var t in c.things.Where(m => m.id == "money2").ToList()) t.Destroy(); "ok"')
            for p in (H, A):
                ev(p, f'var b = {BRANCH}; var d = {level(p)} - {before[0 if p == H else 1]}; if (d != 0) b.elements.ModBase({sid}, -d); "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [b1, b2, b3, b4]
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
                print(f"    capture {name} : {shot(f'base-{step.__name__}-{name}', port)}")
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
