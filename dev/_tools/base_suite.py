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
B5  servante (conseil 7, R1) : la servante choisie par un joueur dans la fenetre des habitants (clic de la ligne, entree
    « makeMaid ») ou dans le dialogue du resident (etape `_daMakeMaid`) est la servante de l'host ET de l'invite ; un
    deuxieme clic la retire des deux ; l'invite le demande a l'host (une seule fois), l'host le dit a l'invite.
B6  type d'un resident : « livestock » puis « resident » depuis le meme menu : le type change chez l'host ET chez l'invite
    (un seul changement chez l'host), dans les deux sens ; l'invite par une demande, l'host par le geste du jeu.
B7  reserve et rappel : « addToReserve » du menu d'un resident (il quitte la base et la carte chez les deux), puis la
    fenetre de la pierre de foyer (`LayerPeople.CreateReserve`, clic de la ligne) le rappelle : il revient, une seule fois,
    dans la base et sur la carte des deux jeux.
B8  renvoyer un resident (dialogue, etape `_depart1`, fin du dialogue) : ouvert a tous ; il disparait de la base et de la
    carte des deux jeux, une seule fois (un resident de moins, une seule ligne du journal chez l'AUTRE joueur).
B9  abandon et acte de propriete : refuses a l'invite avec le message (RemoteBasePaidPatch) ; l'host les fait comme avant.
B11 reserve d'un compagnon : refusee, par le menu et par une demande envoyee quand meme.
B12 poubelle de la reserve (renvoi d'un recrute) : demandee a l'host, une seule fois, vue par les deux jeux.
B10 case « seul l'host gere la base » (R2) : cochee, la demande de l'invite (politique, servante, competence du foyer) est
    refusee et sa copie est remise comme celle de l'host ; decochee, elle passe ; l'host passe dans les deux cas.

Ce que le banc ne joue pas comme un joueur :
- B5 a B7 : les fenetres sont les vraies (`AddLayer<LayerPeople>`, `LayerPeople.CreateReserve`) et la ligne du resident est
  cliquee pour de bon (ce qui fait le menu du jeu). Si le menu se referme sans souris dessus (B1), le banc le refait a
  l'identique (meme cible, meme entree) avec l'action que le jeu y met ; le journal dit « reel » ou « refait ». Pour
  l'invite l'action du banc n'est jamais jouee : le mod la remplace par la demande. Le resident est recrute par
  `Branch.Recruit` (jamais un « vrai » recrutement par le tableau des quetes) et porte un nom propre pour le journal.
- B5, B8 : le dialogue est le vrai (`ShowDialog`), le choix « servante » / « renvoyer » est le saut que fait le clic
  (`DramaSequence.Play("_daMakeMaid")`, `"_depart1"`) ; le renvoi se fait a la fermeture du dialogue.
- B8 : les lignes du journal sont comptees dans `EClass.game.log` (non verifie que le journal affiche est celui-la).
- B9 : la Prairie est la zone de depart, la pierre de foyer n'y propose pas « abandonner » ; le banc construit l'action
  par le point d'entree du jeu (`ActPlan.TrySetAct("actAbandonHome", ...)` avec une action-test) et regarde si elle est
  jouee. L'acte de propriete est lu par `OnRead` (ce que fait « lire ») APRES avoir rendu la zone reclamable dans le jeu de
  ce joueur seul (faction « Wilds », remise ensuite) : la zone etant deja reclamee, le jeu n'ouvrirait aucune boite avec ou
  sans le mod ; ainsi la boite s'ouvre chez l'host et pas chez l'invite (rouge sans le refus). Rien n'est reclame : la boite
  est fermee sans « oui ». NON JOUE : un invite SEUL sur une carte qu'il tient (sans connexion, ou session d'host de zone),
  le banc n'a pas de troisieme fenetre ; le garde est `NetSession.Transport is ElinNetClient`.
- B8 : le dialogue est parcouru par les vrais choix (« daBanish » puis « depart1 », textes du jeu) quand le banc les
  trouve, sinon par le saut a `_depart1` ; le journal dit lequel.
- B10 : la case est posee par la configuration (`EmpConfig.Server.HostManagesBase`, puis `UpdateRemoteSessionRules`),
  pas cochee dans l'onglet ; la politique est cliquee dans la vraie fenetre, la competence du foyer comme B4 ; la
  construction (`AgentTaskDelta`, suivie par la meme case) n'est pas rejouee ici (voir build2_suite). En fin de test, la
  garde CHEZ L'HOST : l'invite envoie quand meme une demande de servante et un jeu de politiques par le reseau
  (`send_raw`, delta fabrique a la main, le client est contourne) ; l'host doit les refuser. Pas rejoues : poser un objet
  tenu (`CharaBuildDelta`) et les reglages de coffre (`InvSaveDataDelta`) avec la case cochee.
- B11 : le compagnon de l'host (`party.AddMemeber`) ne va pas a la reserve par le menu (refus), ni par une demande envoyee
  quand meme par l'invite (`send_raw`, refus par l'host).
- B12 : poubelle de la reserve (vrai bouton de la ligne, vraie boite oui) ; l'host met le resident a la reserve par
  `Faction.AddReserve` (le menu est teste en B7) ; chez l'invite la boite est celle du mod, chez l'host celle du jeu.
- B5 a B10 : un resident est ajoute a la base de l'host puis recopie chez l'invite par `Recruit` (le test regarde que
  l'invite l'a bien dans ses habitants) ; l'avenir d'un resident de la Prairie deja la avant l'arrivee de l'invite n'est
  pas joue autrement qu'avec celui-la.

Ce que le banc ne joue pas comme un joueur (B1 a B4) :
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
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from combat_suite import set_option  # noqa: E402
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


# ---------------------------------------------------------------------------------------------------------------
# conseil 7 : les residents, l'abandon, la case « seul l'host gere la base »

NAME = "Zorblax"
# ce que le jeu met dans chaque entree du menu d'une ligne de LayerPeople (BaseListPeople.OnClick) ; `c` est le resident
MAID = 'if (EClass.Branch.uidMaid == c.uid) EClass.Branch.uidMaid = 0; else EClass.Branch.uidMaid = c.uid;'
LIVESTOCK = 'EClass.Branch.ChangeMemberType(c, FactionMemberType.Livestock);'
RESIDENT = 'c.SetInt(36, EClass.world.date.GetRaw() + 14400); EClass.Branch.ChangeMemberType(c, FactionMemberType.Default);'
RESERVE = 'EClass.Home.AddReserve(c);'
RESERVE_MATCH = 'i.textName.text.StartsWith(Lang.Get("addToReserve"))'


def row(cid):
    """La ligne de ce personnage dans la fenetre des habitants ouverte (code C# ; `it` est null sans)."""
    return ('var l = EClass.ui.GetLayer<LayerPeople>(); var it = l == null ? null : l.GetComponentsInChildren<ItemGeneral>(true)'
            f'.FirstOrDefault(x => x.card != null && x.card.uid == {cid}); ')


def maid_of(p):
    return int(ev(p, f'{BRANCH}.uidMaid.ToString()'))


def who_is(cid, p):
    """Ce que ce jeu sait de ce resident : « type chez les habitants (- s'il n'en est plus) | servante | dans la reserve | sur la carte »."""
    return ev(p, f'var b = {BRANCH}; var m = b.members.Find(x => x.uid == {cid}); '
                 f'return (m == null ? "-" : m.memberType.ToString()) + "|" + (b.uidMaid == {cid}) + "|" + '
                 f'EClass.Home.listReserve.Any(h => h.chara != null && h.chara.uid == {cid}) + "|" + '
                 f'(EClass._map.charas.Find(x => x.uid == {cid}) != null);')


def log_mark(p):
    return int(ev(p, 'EClass.game.log.currentLogIndex.ToString()'))


def log_lines(p, mark, needle):
    """Lignes du journal du jeu ecrites depuis `mark` qui parlent de `needle`."""
    return int(ev(p, f'EClass.game.log.dict.Where(e => e.Key >= {mark} && e.Value.text.Contains("{needle}")).Count().ToString()'))


@contextmanager
def resident():
    """L'host recrute un personnage (Branch.Recruit, le geste du jeu : l'invite le recoit par ce que l'host dit de ce geste) ;
    donne son numero une fois qu'il est habitant ET sur la carte des deux jeux (None sinon) ; a la sortie il est detruit,
    la reserve et la servante sont remises."""
    maid0 = {p: maid_of(p) for p in (H, A)}
    cid = int(ev(H, f'var c = CharaGen.Create("{healer_id()}"); c.c_altName = "{NAME}"; {BRANCH}.Recruit(c); return c.uid.ToString();'))
    here = lambda p: ev(p, f'({BRANCH}.members.Any(m => m.uid == {cid}) && EClass._map.charas.Find(x => x.uid == {cid}) != null).ToString()') == "True"  # noqa: E731
    try:
        yield cid if eventually(lambda: here(H) and here(A), timeout=15) else None
    finally:
        for p in (H, A):
            ev(p, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')
        ev(H, f'var b = {BRANCH}; var c = b.members.Find(m => m.uid == {cid}) ?? EClass._map.charas.Find(x => x.uid == {cid}) ?? '
              f'EClass.Home.listReserve.Find(h => h.chara != null && h.chara.uid == {cid})?.chara; '
              'if (c != null) { b.RemoveMemeber(c); EClass.Home.RemoveReserve(c); c.Destroy(); } "ok"')
        for p in (H, A):
            ev(p, f'var b = {BRANCH}; b.members.RemoveAll(m => m.uid == {cid}); EClass.Home.listReserve.RemoveAll(h => h.chara != null && h.chara.uid == {cid}); '
                  f'b.uidMaid = {maid0[p]}; "ok"')


def open_people(port, cid, tab=0, reserve=False):
    """Ouvre la fenetre des habitants de ce joueur (onglet `tab` : 0 habitants, 1 betail) ou celle de la reserve (l'acte de la
    pierre de foyer) ; vrai quand la ligne du resident y est."""
    ev(port, 'EClass.ui.RemoveLayer<LayerPeople>(); "ok"')
    ev(port, 'LayerPeople.CreateReserve(); "ok"' if reserve else 'EClass.ui.AddLayer<LayerPeople>(); "ok"')
    if tab:
        ev(port, f'EClass.ui.GetLayer<LayerPeople>().windows[0].SwitchContent({tab}); "ok"')
    return eventually(lambda: ev(port, row(cid) + '(it != null).ToString()') == "True", timeout=10)


def row_menu(port, cid, key, replica, idlang=None, match=None):
    """Clique la ligne du resident dans la fenetre ouverte, puis l'entree `key` du menu qui s'ouvre. Si le menu du jeu se
    referme sans souris dessus (comme en B1), il est refait a l'identique (meme cible, meme entree) avec `replica`, ce que le
    jeu y met. Renvoie « reel » ou « refait » (ou la raison de l'echec)."""
    hide_menus(port)
    match = match or f'i.textName.text == Lang.Get("{key}")'
    r = ev(port, row(cid) + 'if (it == null) return "ligne absente"; it.button1.onClick.Invoke(); '
                 'var m = UnityEngine.Object.FindObjectsOfType<UIContextMenuItem>().Where(i => i.gameObject.activeInHierarchy)'
                 f'.FirstOrDefault(i => {match}); if (m == null) return "menu ferme"; m.button.onClick.Invoke(); return "reel";')
    if r != "menu ferme":
        return r
    hide_menus(port)
    ev(port, row(cid) + 'var c = (Chara)it.card; var m = EClass.ui.CreateContextMenuInteraction().SetHighlightTarget(it.button1); '
                        f'var b = m.AddButton({idlang or chr(34) + key + chr(34)}, () => {{ {replica} }}); b.onClick.Invoke(); return "refait";')
    return "refait"


def send_raw(port, make):
    """Envoie a l'host, depuis ce jeu, ce delta tel quel, sans passer par les gardes du client (case, fenetre, message) ;
    `make` est l'expression C# qui le fabrique."""
    ev(port, f'var d = {make}; var q = HarmonyLib.Traverse.Create(ElinTogether.Net.NetSession.Instance.Connection).Field("Delta").GetValue(); '
             'HarmonyLib.Traverse.Create(q).Method("AddRemote", new object[] { d }).GetValue(); "ok"')


def b5(ctx):
    """servante : celle qu'un joueur choisit (menu de la ligne du resident, puis etape du dialogue) l'est chez les deux jeux, une fois ; le meme clic la retire"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        with resident() as cid:
            if not check(f"{who} : un resident de la base est connu des deux jeux ({cid})", cid):
                continue
            awake(port)
            maid = lambda: (maid_of(H), maid_of(A))  # noqa: E731
            if not check(f"{who} : la fenetre des habitants montre la ligne du resident", open_people(port, cid)):
                continue
            how = row_menu(port, cid, "makeMaid", MAID)
            log(f"{who} choisit la servante dans la fenetre : {how}")
            check(cond=eventually(lambda: maid() == (cid, cid), timeout=10),
                  label=f"{who} choisit la servante ({how}) : host et invite disent {cid} (maintenant {maid()})")
            time.sleep(3)  # une deuxieme execution (le menu bascule) la retirerait
            check(f"{who} : une seule fois, la servante reste {cid} ({maid()})", maid() == (cid, cid))
            how = row_menu(port, cid, "makeMaid", MAID)
            check(cond=eventually(lambda: maid() == (0, 0), timeout=10),
                  label=f"{who} la retire du meme clic ({how}) : host et invite disent 0 (maintenant {maid()})")
            # le dialogue du resident : le saut que fait le choix « servante »
            ev(port, 'EClass.ui.RemoveLayer<LayerPeople>(); "ok"')
            if not check(f"{who} : il parle au resident, l'etape de la servante existe", talk(port, cid)
                         and ev(port, 'LayerDrama.Instance.drama.sequence.steps.ContainsKey("_daMakeMaid").ToString()') == "True"):
                hang_up(port)
                continue
            ev(port, 'LayerDrama.Instance.drama.sequence.Play("_daMakeMaid"); "ok"')
            time.sleep(2)
            check(cond=eventually(lambda: maid() == (cid, cid), timeout=10),
                  label=f"{who} la choisit dans le dialogue : host et invite disent {cid} (maintenant {maid()})")
            hang_up(port)


def b6(ctx):
    """type d'un resident : betail puis resident par le menu de la ligne ; chez les deux jeux, un seul changement, dans les deux sens"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        with resident() as cid:
            if not check(f"{who} : un resident de la base est connu des deux jeux ({cid})", cid):
                continue
            awake(port)
            kind = lambda p: who_is(cid, p).split("|")[0]  # noqa: E731
            check(f"{who} : c'est un resident chez les deux jeux ({kind(H)}, {kind(A)})", kind(H) == kind(A) == "Default")
            if not check(f"{who} : la fenetre des habitants montre la ligne du resident", open_people(port, cid)):
                continue
            how = row_menu(port, cid, "daMakeLivestock", LIVESTOCK)
            check(cond=eventually(lambda: kind(H) == kind(A) == "Livestock", timeout=10),
                  label=f"{who} le met en betail ({how}) : host {kind(H)}, invite {kind(A)}")
            time.sleep(3)
            check(f"{who} : une seule fois, il reste du betail (host {kind(H)}, invite {kind(A)})", kind(H) == kind(A) == "Livestock")
            # retour : la ligne est maintenant dans l'onglet du betail
            if not check(f"{who} : la ligne du resident est dans l'onglet du betail", open_people(port, cid, tab=1)):
                continue
            how = row_menu(port, cid, "daMakeResident", RESIDENT)
            check(cond=eventually(lambda: kind(H) == kind(A) == "Default", timeout=10),
                  label=f"{who} en refait un resident ({how}) : host {kind(H)}, invite {kind(A)}")


def b7(ctx):
    """reserve et rappel : un resident part a la reserve (menu de la ligne), la fenetre de la pierre de foyer le rappelle ; chez les deux jeux, une seule fois"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        with resident() as cid:
            if not check(f"{who} : un resident de la base est connu des deux jeux ({cid})", cid):
                continue
            cap = ev(H, 'EClass.Home.listReserve.Count + "/" + EClass.Home.GetMaxReserve()')
            n, room = (int(v) for v in cap.split("/"))
            if not check(f"{who} : la reserve a de la place ({cap})", n < room):
                continue
            reserve = lambda p: int(ev(p, 'EClass.Home.listReserve.Count.ToString()'))  # noqa: E731
            on_map = lambda p: int(ev(p, f'EClass._map.charas.Count(x => x.uid == {cid}).ToString()'))  # noqa: E731
            r0 = {p: reserve(p) for p in (H, A)}
            awake(port)
            if not check(f"{who} : la fenetre des habitants montre la ligne du resident", open_people(port, cid)):
                continue
            how = row_menu(port, cid, "addToReserve", RESERVE, idlang='Lang.Get("addToReserve") + " (0/9)"', match=RESERVE_MATCH)
            gone = "-|False|True|False"
            check(cond=eventually(lambda: who_is(cid, H) == gone and who_is(cid, A) == gone, timeout=10),
                  label=f"{who} le met en reserve ({how}) : plus habitant ni sur la carte, dans la reserve (host {who_is(cid, H)}, invite {who_is(cid, A)})")
            time.sleep(3)
            check(f"{who} : une seule entree de reserve de plus (host {r0[H]} -> {reserve(H)}, invite {r0[A]} -> {reserve(A)})",
                  reserve(H) == r0[H] + 1 and reserve(A) == r0[A] + 1)
            # le rappel : la fenetre de la reserve (acte « actCallReserve » de la pierre de foyer), clic de la ligne
            if not check(f"{who} : la fenetre de la reserve montre la ligne du resident", open_people(port, cid, reserve=True)):
                continue
            r = ev(port, row(cid) + 'if (it == null) return "ligne absente"; it.button1.onClick.Invoke(); return "clic";')
            back = "Default|False|False|True"
            check(cond=eventually(lambda: who_is(cid, H) == back and who_is(cid, A) == back, timeout=15),
                  label=f"{who} le rappelle ({r}) : habitant et sur la carte, plus dans la reserve (host {who_is(cid, H)}, invite {who_is(cid, A)})")
            time.sleep(3)
            check(f"{who} : une seule fois (sur la carte host {on_map(H)}, invite {on_map(A)} ; reserve host {reserve(H)}, invite {reserve(A)})",
                  on_map(H) == on_map(A) == 1 and reserve(H) == r0[H] and reserve(A) == r0[A])


def b8(ctx):
    """renvoyer un resident (dialogue) : ouvert a tous, il disparait des deux jeux, une seule fois, et l'autre joueur en est prevenu"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        other, other_name = (H, "l'host") if port == A else (A, "l'invite")
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        with resident() as cid:
            if not check(f"{who} : un resident de la base est connu des deux jeux ({cid})", cid):
                continue
            awake(port)
            members = lambda p: int(ev(p, f'{BRANCH}.members.Count.ToString()'))  # noqa: E731
            m0 = {p: members(p) for p in (H, A)}
            marks = {p: log_mark(p) for p in (H, A)}
            if not check(f"{who} : il parle au resident, l'etape du renvoi existe", talk(port, cid)
                         and ev(port, 'LayerDrama.Instance.drama.sequence.steps.ContainsKey("_depart1").ToString()') == "True"):
                hang_up(port)
                continue
            # les vrais choix du dialogue quand le banc les trouve (« daBanish » puis « depart1 », textes du jeu) ; sinon le
            # saut que fait le dernier choix (le journal le dit). Chez l'host le renvoi se fait a la fermeture du dialogue
            real = all(pick(port, ev(port, f'Lang.Get("{k}")')) == "clic" for k in ("daBanish", "depart1"))
            log(f"{who} : renvoi par les vrais choix du dialogue : {'oui' if real else 'non, saut a _depart1'}")
            if not real:
                ev(port, 'if (LayerDrama.Instance != null) LayerDrama.Instance.drama.sequence.Play("_depart1"); "ok"')
            time.sleep(2)
            ev(port, 'if (LayerDrama.Instance != null) LayerDrama.Instance.Close(); "ok"')
            gone = lambda p: ev(p, f'({BRANCH}.members.Any(m => m.uid == {cid}) || EClass._map.charas.Any(x => x.uid == {cid} && !x.isDestroyed)).ToString()') == "False"  # noqa: E731
            check(cond=eventually(lambda: gone(H) and gone(A), timeout=15),
                  label=f"{who} le renvoie : plus habitant ni sur la carte, chez l'host ({who_is(cid, H)}) et chez l'invite ({who_is(cid, A)})")
            time.sleep(3)
            check(f"{who} : un seul resident de moins (host {m0[H]} -> {members(H)}, invite {m0[A]} -> {members(A)})",
                  members(H) == m0[H] - 1 and members(A) == m0[A] - 1)
            lines = {p: log_lines(p, marks[p], NAME) for p in (H, A)}
            check(f"{who} : {other_name} est prevenu, une seule ligne du journal qui parle du resident ({lines[other]})", lines[other] == 1)
            log(f"lignes du journal sur le resident : host {lines[H]}, invite {lines[A]}")


def b9(ctx):
    """abandon de la base et acte de propriete : refuses a l'invite (un demi-etat ne se rattrape pas), l'host les fait comme avant"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        core = ev(port, 'var t = EClass._map.things.Find(x => x.trait is TraitCoreZone); return t == null ? "" : t.uid.ToString();')
        if not check(f"{who} : la base a sa pierre de foyer ({core or 'aucune'})", bool(core)):
            continue
        # le point d'entree du jeu : l'acte « abandonner » est fabrique par ActPlan.TrySetAct avec son action ; on y met une
        # action-test, jouee ou non (l'host la joue, le mod la remplace chez l'invite par le refus)
        r = ev(port, f'var t = EClass._map.things.Find(x => x.uid == {core}); var ran = false; var p = new ActPlan {{ input = ActInput.LeftMouse }}; p.pos.Set(t.pos); '
                     'p.TrySetAct("actAbandonHome", () => { ran = true; return false; }, t); var it = p.list.LastOrDefault(); '
                     'if (it == null) return "pas d\'action"; ((DynamicAct)it.act).onPerform(); return ran.ToString();')
        check(f"{who} : l'action « abandonner » {'est jouee' if key == 'h' else 'est refusee'} ({r})", r == ("True" if key == "h" else "False"))
        # l'acte de propriete. La Prairie est deja reclamee : le jeu y dit « invalide » et n'ouvre aucune boite, avec ou sans le
        # mod, donc la lire telle quelle ne prouverait rien. Le banc la rend reclamable DANS LE JEU DE CE JOUEUR SEUL (la
        # zone passe a la faction « Wilds », comme avant une prise ; remise en fin) : la boite « reclamer ? » du jeu doit
        # alors s'ouvrir chez l'host (il peut reclamer) et PAS chez l'invite (rouge sans le refus : la boite s'ouvre aussi chez lui)
        if ev(port, 'EClass._zone.isClaimable.ToString()') != "True":
            log(f"{who} : la zone n'est pas reclamable meme libre : acte de propriete NON JOUE")
            continue
        deed = give(ctx, key, "deed")
        claimed = lambda p: ev(p, 'EClass._zone.IsPCFaction.ToString()')  # noqa: E731
        d0 = (count(H, uid, "deed"), count(port, uid, "deed"))
        owner0 = ev(port, 'EClass._zone.idMainFaction')
        try:
            ev(port, 'EClass._zone.mainFaction = EClass.Wilds; "ok"')
            ev(port, f'var t = EClass.pc.things.Find(x => x.uid == {deed}); ((TraitDeed)t.trait).OnRead(EClass.pc); "ok"')
            time.sleep(2)
            opened = dialog_open(port)
            verdict = "s'ouvre" if key == "h" else "ne s'ouvre pas"
            check(f"{who} : la boite « reclamer ? » {verdict} ({opened})", opened == (key == "h"))
        finally:
            close_layers()   # la boite se ferme sans oui : rien n'est reclame
            ev(port, f'EClass._zone.idMainFaction = "{owner0}"; "ok"')
        check(f"{who} : l'acte n'est pas consomme (host {d0[0]} -> {count(H, uid, 'deed')}, lui {d0[1]} -> {count(port, uid, 'deed')}) et la zone est remise ({claimed(port)})",
              (count(H, uid, "deed"), count(port, uid, "deed")) == d0 and claimed(port) == "True")
        ev(H, f'var c = {chara(H, uid)}; foreach (var t in c.things.Where(m => m.id == "deed").ToList()) t.Destroy(); "ok"')
    log("abandon / acte d'un invite SEUL sur une carte qu'il tient (pas de connexion, ou session d'host de zone) : NON JOUE, "
        "le banc n'a pas de troisieme fenetre ; le garde est NetSession.Transport is ElinNetClient (RemoteBasePaidPatch.IsNotWorldHost)")


def policy_id():
    """Une politique de la base connue des deux jeux (une qui ne coute rien est donnee aux deux si la base n'en a pas de libre)."""
    pid = ev(H, 'var b = EClass._zone.branch; var p = b.policies.list.FirstOrDefault(x => !x.active && b.policies.CurrentAP() + x.Cost <= b.MaxAP); '
                'return p == null ? "" : p.id.ToString();')
    if not pid:
        pid = ev(H, 'EClass.sources.elements.rows.First(r => r.category == "policy" && r.cost.Length > 0 && r.cost[0] == 0).id.ToString()')
    for p in (H, A):
        ev(p, f'var b = EClass._zone.branch; if (!b.policies.list.Any(x => x.id == {pid})) b.policies.AddPolicy({pid}, false); "ok"')
    return pid


def click_policy(port, pid):
    """Ouvre la fenetre des politiques de ce joueur et clique la politique (comme setting_suite S4)."""
    ev(port, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')
    ev(port, 'EClass.ui.AddLayer<LayerPolicy>(); "ok"')
    time.sleep(2)
    return ev(port, 'var l = EClass.ui.GetLayer<LayerPolicy>(); var b = l.GetComponentsInChildren<UIButton>(true)'
                    f'.FirstOrDefault(x => x.refObj is Policy q && q.id == {pid}); if (b == null) return "bouton absent"; b.onClick.Invoke(); return "clic";')


def b10(ctx):
    """case « seul l'host gere la base » (R2) : cochee, la demande de l'invite est refusee et sa copie remise comme l'host ; decochee elle passe ; l'host passe dans les deux cas
    (une politique de la fenetre, la servante du menu, une competence du foyer)"""
    pid = policy_id()
    on = lambda p: ev(p, f'EClass._zone.branch.policies.list.Any(x => x.id == {pid} && x.active).ToString()') == "True"  # noqa: E731
    pick_skill = (f'var b = {BRANCH}; var e = b.elements.dict.Values.Where(x => (x.Value > 0 || x.vBase > 0) && x.source.category != "policy" && x.source.category != "landfeat" && '
                  '!x.HasTag("hidden") && x.ValueWithoutLink > 0 && x.source.cost[0] != 0 && b.GetTechUpgradeCost(x) > 0).FirstOrDefault(); ')
    sid = ev(H, pick_skill + 'return e == null ? "" : e.id.ToString();')
    try:
        for rule in (True, False):
            set_option("HostManagesBase", rule)
            eventually(lambda: ev(A, 'ElinTogether.Net.NetSession.Instance.Rules.HostManagesBase.ToString()') == str(rule), timeout=10)
            if not check(f"la case est {'cochee' if rule else 'decochee'} chez l'host et chez l'invite",
                         ev(H, 'ElinTogether.Net.NetSession.Instance.Rules.HostManagesBase.ToString()') == str(rule)
                         and ev(A, 'ElinTogether.Net.NetSession.Instance.Rules.HostManagesBase.ToString()') == str(rule)):
                continue
            for who, key in both(ctx):
                port, uid = ctx[key]
                allowed = key == "h" or not rule
                tag = f"case {'cochee' if rule else 'decochee'}, {who}"
                close_layers()
                # 1) la politique, dans la vraie fenetre
                before = on(H)
                r = click_policy(port, pid)
                want = (not before) if allowed else before
                verdict = "passe" if allowed else "est refusee et la copie de l'invite remise comme celle de l'host"
                time.sleep(1 if allowed else 3)
                check(cond=eventually(lambda: on(H) == want and on(A) == want, timeout=10),
                      label=f"{tag} : la politique ({r}) {verdict} : host {on(H)}, invite {on(A)} (voulu {want})")
                if on(H) != before:
                    click_policy(H, pid)
                    eventually(lambda: on(H) == before and on(A) == before, timeout=10)
                close_layers()
                # 2) la servante, par le menu du resident
                with resident() as cid:
                    if cid and open_people(port, cid):
                        how = row_menu(port, cid, "makeMaid", MAID)
                        want = cid if allowed else 0
                        time.sleep(1 if allowed else 3)
                        check(cond=eventually(lambda: (maid_of(H), maid_of(A)) == (want, want), timeout=10),
                              label=f"{tag} : la servante ({how}) {'passe' if allowed else 'est refusee'} : host {maid_of(H)}, invite {maid_of(A)} (voulu {want})")
                    else:
                        check(f"{tag} : un resident et sa ligne pour la servante", False)
                # 3) une competence du foyer (platine du joueur), comme B4
                if not sid:
                    log(f"{tag} : le foyer n'a pas de competence a monter : demande de competence non verifiee")
                    continue
                cost = int(ev(H, f'{BRANCH}.GetTechUpgradeCost({BRANCH}.elements.GetElement({sid})).ToString()'))
                give(ctx, key, "money2", cost + 5)
                level = lambda p: int(ev(p, f'{BRANCH}.elements.Value({sid}).ToString()'))  # noqa: E731
                lv0, gold0 = (level(H), level(A)), count(H, uid, "money2")
                find = f'var it = LayerHome.Instance.listFeat.GetComponentsInChildren<ButtonElement>().FirstOrDefault(x => x.e != null && x.e.id == {sid}); '
                try:
                    awake(port)
                    ev(port, 'EClass.ui.AddLayer<LayerHome>(); "ok"')
                    eventually(lambda: ev(port, '(LayerHome.Instance != null).ToString()') == "True", timeout=10)
                    ev(port, 'LayerHome.Instance.RefreshFeat(); "ok"')
                    if eventually(lambda: ev(port, find + '(it != null).ToString()') == "True", timeout=10):
                        ev(port, find + 'it.onClick.Invoke(); "ok"')
                        if eventually(lambda: dialog_open(port), timeout=5):
                            click_yes(port)
                        want = lv0[0] + (1 if allowed else 0)
                        time.sleep(1 if allowed else 3)
                        check(cond=eventually(lambda: level(H) == want and level(A) == want, timeout=15),
                              label=f"{tag} : la competence {'monte chez les deux' if allowed else 'ne monte nulle part'} : host {lv0[0]} -> {level(H)}, invite {lv0[1]} -> {level(A)} (voulu {want})")
                        check(f"{tag} : le platine {'est debite' if allowed else 'reste intact'} chez l'host ({gold0} -> {count(H, uid, 'money2')})",
                              count(H, uid, "money2") == (gold0 - cost if allowed else gold0))
                    else:
                        check(f"{tag} : la liste des competences montre celle-la", False)
                finally:
                    ev(port, 'EClass.ui.RemoveLayer<LayerHome>(); "ok"')
                    close_layers()
                    ev(H, f'var c = {chara(H, uid)}; foreach (var t in c.things.Where(m => m.id == "money2").ToList()) t.Destroy(); "ok"')
                    for p in (H, A):
                        ev(p, f'var d = {level(p)} - {lv0[0 if p == H else 1]}; if (d != 0) {BRANCH}.elements.ModBase({sid}, -d); "ok"')
        # la garde CHEZ L'HOST : l'invite envoie quand meme (un client modifie, ou une case changee entre le clic et l'arrivee) ;
        # le client est contourne (aucun message, aucune fenetre) : seul le refus de l'host peut arreter ces deux demandes
        set_option("HostManagesBase", True)
        eventually(lambda: ev(A, 'ElinTogether.Net.NetSession.Instance.Rules.HostManagesBase.ToString()') == "True", timeout=10)
        close_layers()
        with resident() as cid:
            if check("garde chez l'host : un resident de la base est connu des deux jeux", cid):
                send_raw(A, f'new ElinTogether.Models.BaseRequestDelta {{ Kind = ElinTogether.Models.BaseRequestKind.Maid, Id = "{cid}" }}')
                time.sleep(3)
                check(f"garde chez l'host : la demande de servante envoyee quand meme est refusee (host {maid_of(H)}, invite {maid_of(A)})",
                      maid_of(H) == 0 and maid_of(A) == 0)
                # temoin : case decochee, le meme envoi passe (sinon le refus ci-dessus ne prouve rien)
                set_option("HostManagesBase", False)
                eventually(lambda: ev(A, 'ElinTogether.Net.NetSession.Instance.Rules.HostManagesBase.ToString()') == "False", timeout=10)
                send_raw(A, f'new ElinTogether.Models.BaseRequestDelta {{ Kind = ElinTogether.Models.BaseRequestKind.Maid, Id = "{cid}" }}')
                check(cond=eventually(lambda: (maid_of(H), maid_of(A)) == (cid, cid), timeout=10),
                      label=f"temoin : case decochee, le meme envoi passe (host {maid_of(H)}, invite {maid_of(A)})")
                set_option("HostManagesBase", True)
                eventually(lambda: ev(A, 'ElinTogether.Net.NetSession.Instance.Rules.HostManagesBase.ToString()') == "True", timeout=10)
        before = on(H)
        active = ev(H, 'string.Join(",", EClass._zone.branch.policies.list.Where(p => p.active).Select(p => p.id).OrderBy(i => i))')
        ids = {int(i) for i in active.split(",") if i}
        ids ^= {int(pid)}
        send_raw(A, 'new ElinTogether.Models.PolicyStateDelta { Active = new int[] { ' + ",".join(str(i) for i in sorted(ids)) + ' } }')
        time.sleep(3)
        check(f"garde chez l'host : la politique envoyee quand meme est refusee et l'host la garde (avant {before}, apres host {on(H)}, invite {on(A)})",
              on(H) == before and on(A) == before)
    finally:
        set_option("HostManagesBase", False)
        close_layers()


def b11(ctx):
    """reserve d'un compagnon : le compagnon d'un joueur (membre de son groupe) ne se met pas en reserve, ni par le menu de la ligne ni par une demande envoyee quand meme ; rien ne change, chez aucun des deux jeux"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        with resident() as cid:
            if not check(f"{who} : un resident de la base est connu des deux jeux ({cid})", cid):
                continue
            party = lambda p: ev(p, f'({chara(p, cid)}.IsPCParty).ToString()') == "True"  # noqa: E731
            try:
                ev(H, f'EClass.pc.party.AddMemeber({chara(H, cid)}); "ok"')
                if not check(f"{who} : le resident est un compagnon de l'host, vu par les deux jeux",
                             eventually(lambda: party(H) and party(A), timeout=10)):
                    continue
                awake(port)
                before = {p: who_is(cid, p) for p in (H, A)}
                reserve = lambda p: int(ev(p, 'EClass.Home.listReserve.Count.ToString()'))  # noqa: E731
                r0 = {p: reserve(p) for p in (H, A)}
                if open_people(port, cid):
                    how = row_menu(port, cid, "addToReserve", RESERVE, idlang='Lang.Get("addToReserve") + " (0/9)"', match=RESERVE_MATCH)
                    time.sleep(3)
                    check(f"{who} : « addToReserve » ({how}) ne fait rien : ni resident en moins, ni reserve en plus (host {who_is(cid, H)}, invite {who_is(cid, A)})",
                          all(who_is(cid, p) == before[p] and reserve(p) == r0[p] for p in (H, A)))
                else:
                    check(f"{who} : la fenetre des habitants montre la ligne du resident", False)
                if key == "a":
                    # le client est contourne : seule la garde de l'host (BaseRequestDelta.ExecuteResident) peut l'arreter
                    send_raw(A, f'new ElinTogether.Models.BaseRequestDelta {{ Kind = ElinTogether.Models.BaseRequestKind.Reserve, Id = "{cid}" }}')
                    time.sleep(3)
                    check(f"{who} : la demande envoyee quand meme est refusee par l'host (host {who_is(cid, H)}, invite {who_is(cid, A)}, reserve {reserve(H)}/{reserve(A)})",
                          all(who_is(cid, p) == before[p] and reserve(p) == r0[p] for p in (H, A)))
            finally:
                ev(H, f'var c = {chara(H, cid)}; if (c != null && c.IsPCParty) EClass.pc.party.RemoveMember(c); "ok"')


def b12(ctx):
    """poubelle de la reserve : quelqu'un de la reserve renvoye pour de bon (bouton poubelle de la ligne, fenetre de la pierre de foyer) disparait des reserves des deux jeux, une seule fois, quel que soit le joueur
    Ce que le banc ne joue pas comme un joueur : l'host met le resident a la reserve par `Faction.AddReserve` (le menu est teste en B7) ;
    la boite oui/non du jeu est cliquee (chez l'invite la boite du mod, chez l'host la boite a trois boutons du jeu : « Yes »)"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        close_layers()
        if not check(f"{who} : il est dans une base ({zone_name(port)})", is_base(port)):
            continue
        with resident() as cid:
            try:
                if not check(f"{who} : un resident de la base est connu des deux jeux ({cid})", cid):
                    continue
                if not check(f"{who} : le jeu peut le renvoyer (le bouton poubelle ne serait pas actif sinon)",
                             ev(H, f'({chara(H, cid)}.trait.CanBeBanished).ToString()') == "True"):
                    continue
                reserve = lambda p: int(ev(p, 'EClass.Home.listReserve.Count.ToString()'))  # noqa: E731
                ev(H, f'EClass.Home.AddReserve({chara(H, cid)}); "ok"')
                gone = "-|False|True|False"
                if not check(cond=eventually(lambda: who_is(cid, H) == gone and who_is(cid, A) == gone, timeout=10),
                             label=f"{who} : le resident est dans la reserve des deux jeux (host {who_is(cid, H)}, invite {who_is(cid, A)})"):
                    continue
                r0 = {p: reserve(p) for p in (H, A)}
                awake(port)
                if not check(f"{who} : la fenetre de la reserve montre la ligne du resident", open_people(port, cid, reserve=True)):
                    continue
                r = ev(port, row(cid) + 'if (it == null) return "ligne absente"; var b = it.GetComponentsInChildren<UIButton>(true)'
                                        '.FirstOrDefault(x => x.icon != null && x.icon.sprite == EClass.core.refs.icons.trash); '
                                        'if (b == null) return "poubelle absente"; b.onClick.Invoke(); return "clic";')
                time.sleep(1)
                log(f"{who} clique la poubelle : {r} ; il dit oui : {click_yes(port)}")
                check(cond=eventually(lambda: reserve(H) == r0[H] - 1 and reserve(A) == r0[A] - 1, timeout=15),
                      label=f"{who} : plus dans la reserve des deux jeux (host {r0[H]} -> {reserve(H)}, invite {r0[A]} -> {reserve(A)})")
                time.sleep(3)
                check(f"{who} : une seule fois, une entree de moins (host {reserve(H)}, invite {reserve(A)}) ; ni habitant ni sur la carte (host {who_is(cid, H)}, invite {who_is(cid, A)})",
                      reserve(H) == r0[H] - 1 and reserve(A) == r0[A] - 1 and who_is(cid, H) == who_is(cid, A) == "-|False|False|False")
            finally:
                # renvoye, un personnage « global » est range ailleurs par le jeu (OnBanish) : on l'enleve pour de bon
                ev(H, f'var c = EClass.game.cards.globalCharas.Find({cid}); if (c != null) {{ c.RemoveGlobal(); c.Destroy(); }} "ok"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12]
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
