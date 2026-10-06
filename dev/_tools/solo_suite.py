"""Un host seul dans sa session vit le jeu solo, puis le jeu a plusieurs revient quand un invite arrive
(dev/PLAN_joueur_seul.md, corrections S1 a S16 ; la porte commune est ElinTogether.Net.NetCompany.HasCompany).

    python _tools/mp_test.py                   # host + 1 client dans la Prairie (la suite fait partir le client au debut)
    python _tools/solo_suite.py                # ~15 minutes ; ou --only z2,z3
    python _tools/mp_test.py --clients 0       # variante : host seul, pas de fenetre client
    python _tools/solo_suite.py                # sans fenetre client sur 27552, seule la partie « seul » est jouee

Le host a sa session ouverte (le banc l'ouvre par emp.add_local, une vraie partie par l'ouverture automatique) et se tient
dans la Prairie, qui est une base. Quatre temps :
  1. SEUL (aucun pair)         : chaque geste donne ce que donnerait le jeu sans le mod
  2. UN INVITE ARRIVE          : le comportement a plusieurs est revenu (le combat a ete lance AVANT l'arrivee)
  3. L'INVITE PART             : tout est revenu comme en 1
  4. L'INVITE VOYAGE SEUL      : retire de CurrentPlayers mais toujours un pair : la porte reste a « plusieurs »

Z0  la porte : HasCompany faux seul, vrai des l'arrivee d'un invite (meme en poignee de main), vrai quand il voyage seul
    alors que CurrentPlayers n'a plus que l'host (le piege du plan : Count <= 1 ne suffit pas)
Z1  S16  menu ouvert : UI.IsPauseGame reste vrai seul (le jeu pause dans les menus), faux a plusieurs
Z2  S16  vitesse partagee : une vitesse commune donnee par la session ne change la vitesse du joueur qu'a plusieurs
Z3  S4   « mettre en reserve » sur un compagnon du groupe : clic sur la ligne de la fenetre des habitants puis sur l'entree
         du menu ; seul : le compagnon est en reserve et hors du groupe ; a plusieurs : refuse, rien ne bouge
Z4  S2   couper : un compagnon vise deja la case ; seul : le clic du joueur est accepte ; a plusieurs : refuse (regle
         gardee). NB le plan §6 dit « refuse seulement si l'invite vise la case » : le code refuse pour tout perso de la
         carte (TaskCache.IsPosTaken), c'est ce que la suite attend a plusieurs
Z5  S3   un coup d'allie sur le joueur : seul, aucun bouclier (le coup peut tuer) ; a plusieurs, le bouclier du mod
Z6  S1   brosser : le joueur tient une brosse de zone (effet 770) et brosse un animal a cote d'un autre ; seul, le compteur
         de brosses monte (la copie du mod ne le faisait pas) ; la porte de AIFuckPatch.OnRun rend « le jeu fait » seul
Z7  S5   Ctrl+clic sur une pile de 10 planches puis 1 : seul, c'est la pile d'origine qui est glissee (uid inchange) ;
         a plusieurs, le nouveau morceau
Z8  S6   changement de zone : seul, aucune ligne « Dispatching zone to all players » ; a plusieurs, une par zone
Z9  S7   une valeur de competence modifiee : seul, aucune ligne « Element ... changed » ; a plusieurs, au moins une
Z10 S12/S15  combat tour par tour avec un ennemi en vue : seul, ActionModeCombat.Phase reste Inactive ; a l'arrivee de
         l'invite elle passe a Deciding en moins de 10 s ; au depart elle revient a Inactive

Sans test ici (voir l'etat dans le plan) : S13 (cartes creees), S14 (cases de terrain), S10 (hors suite : fichier interdit), S8
(le cote CardAddThingEvent est a faire), le cout en images par seconde (perf_probe.py).

Ce que le banc ne joue pas comme un joueur :
- Z1 le menu est ouvert par AddLayer (journal, capacites, aide : le premier dont l'option pauseGame est vraie), pas par la
  touche ; Z2 la vitesse commune est posee dans NetSession.SharedSpeed (internal set) par Traverse, la case « vitesse
  partagee » du host reste decochee
- Z3 les clics sont ceux de la souris sur le bouton de la ligne et sur l'entree du menu contextuel (vrais, pas refaits : si le
  menu se referme, la suite le dit et ne remplace pas par le lambda du jeu) ; le compagnon est recrute par Branch.Recruit puis
  Party.AddMemeber, pas par un dialogue
- Z4 le compagnon recoit TaskCut par SetAI sur un arbre voisin (le joueur le lui donne par un designateur) ; le clic du joueur
  est pc.SetAI(new TaskCut) comme le fait le curseur ; recolter (TaskHarvest) n'est pas joue
- Z5 aucun coup n'est porte (le joueur mourrait) : la suite appelle l'avant et l'apres de RemotePlayerKillPatch.OnDamage
  avec l'allie comme auteur et rend le joueur intact
- Z6 AI_TendAnimal est donne par pc.SetAI ; la brosse est creee avec l'effet 770 (le jeu n'en vend pas qui l'ait forcement)
- Z7 Ctrl+clic = InvOwner.OnCtrlClick sur le bouton de la pile, le menu est ferme comme le fait un clic dehors (Hide)
- Z10 le monstre est paralyse et hostile (il ne tue pas le joueur du banc) ; la decision du joueur en phase Deciding n'est
  pas jouee
- une seule machine, connexion locale ; un invite « en poignee de main » (connecte sans personnage) n'est pas joue
- pas joues : combat avec l'invite qui part en Executing (decision en attente perdue), sommeil, chargement rapide pendant
  l'arrivee, ConWait de SetAI (S2 :46), le plan §5 « menu ouvert au moment ou l'invite arrive » (voir Z1 : le menu est
  ouvert APRES l'arrivee, pas pendant)
"""
import argparse
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from base_suite import BRANCH, RESERVE_MATCH, healer_id, hide_menus, open_people, row  # noqa: E402
from combat_suite import set_option  # noqa: E402
from guest_suite import awake, close_layers  # noqa: E402
from mp_test import join_client, log, shot, state, wait  # noqa: E402
from travel_suite import HOME, RESULTS, VERNIS, both_joined, check, ev, eventually, move, players, scan_logs, session_log_lines, zone_uid  # noqa: E402

H, A = 27551, 27552
ZONE_LINE = "Dispatching zone to all players"
ELEMENT_LINE = "Element {ElementId} changed on chara"

COMPANY = ('HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.NetCompany"), '
           '"HasCompany").GetValue(null).ToString()')
PHASE = ('HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.Patches.ActionModeCombat"), '
         '"Phase").GetValue(null).ToString()')


def company(port=H):
    time.sleep(0.3)  # the gate looks at the peers at most every 50 ms
    return ev(port, COMPANY) == "True"


def counted(port=H):
    """Ce que CurrentPlayers dit : le nombre de joueurs sur la carte de l'host."""
    return players(port)


def log_count(since, needle):
    return sum(1 for line in session_log_lines(since) if needle in line)


def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def host_alone():
    """Aucun pair : le client n'est pas connecte (ou n'existe pas)."""
    try:
        return not state(A)["connected"]
    except OSError:
        return True


def has_client():
    try:
        return bool(emp.call(A, "hello", timeout=2.0).get("ok"))
    except OSError:
        return False


# ---------------------------------------------------------------------------------------------------------------
# arrivee et depart de l'invite

def leave():
    """L'invite quitte (bouton « se deconnecter » du mod : ResetSession) et revient a l'ecran titre."""
    ev(A, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
    time.sleep(3)
    if state(A).get("sceneMode") != "Title":
        emp.call(A, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
    wait(lambda: state(A).get("sceneMode") == "Title" and not state(A)["connected"], "client a l'ecran titre", timeout=60)
    wait(lambda: players(H) == 1, "l'host ne voit plus le client", timeout=60)
    time.sleep(2)


def arrive():
    join_client(H, A, "client 1")
    wait(lambda: players(H) == 2, "l'host voit le client", timeout=60)
    both_joined(H, A, HOME)


# ---------------------------------------------------------------------------------------------------------------
# sondes : chacune rend ce que ce jeu fait, la comparaison est faite par run_probes

def pause_probe():
    """(la couche pause le jeu, UI.IsPauseGame) pour le premier menu qui le fait."""
    try:
        for layer in ("LayerJournal", "LayerAbility", "LayerHelp"):
            r = ev(H, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); '
                      f'var y = EClass.ui.AddLayer<{layer}>(); return y.option.pauseGame + "|" + EClass.ui.IsPauseGame;')
            pauses, ui = r.split("|")
            if pauses == "True":
                return layer, ui == "True"
        return None, None
    finally:
        close_layers_host()


def close_layers_host():
    ev(H, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')


def speed_probe():
    """Vitesse du joueur quand la session annonce une vitesse commune de 777."""
    return int(ev(H, 'var s = ElinTogether.Net.NetSession.Instance; var old = s.SharedSpeed; '
                     'HarmonyLib.Traverse.Create(s).Property("SharedSpeed").SetValue(777); var v = EClass.pc.Speed; '
                     'HarmonyLib.Traverse.Create(s).Property("SharedSpeed").SetValue(old); return v.ToString();'))


@contextmanager
def ally():
    """Un compagnon du groupe de l'host, habitant de la base (Branch.Recruit, Party.AddMemeber) ; retire a la sortie."""
    uid = int(ev(H, f'var c = CharaGen.Create("{healer_id()}"); c.c_altName = "Zorblax"; {BRANCH}.Recruit(c); '
                    'EClass.pc.party.AddMemeber(c); return c.uid.ToString();'))
    try:
        eventually(lambda: ev(H, f'(EClass._map.charas.Find(x => x.uid == {uid}) != null && EClass.Home.listReserve.Count >= 0).ToString()') == "True",
                   timeout=15)
        yield uid
    finally:
        ev(H, f'var b = {BRANCH}; var c = EClass._map.charas.Find(x => x.uid == {uid}) ?? '
              f'EClass.Home.listReserve.Find(h => h.chara != null && h.chara.uid == {uid})?.chara; '
              'if (c != null) { if (c.IsPCParty) EClass.pc.party.RemoveMember(c); b.RemoveMemeber(c); EClass.Home.RemoveReserve(c); c.Destroy(); } '
              f'b.members.RemoveAll(m => m.uid == {uid}); EClass.Home.listReserve.RemoveAll(h => h.chara != null && h.chara.uid == {uid}); "ok"')


def reserve_probe():
    """Le joueur met son compagnon en reserve par la fenetre des habitants : (clic, reserve avant, apres, dans le groupe apres)."""
    with ally() as uid:
        close_layers_host()
        awake(H)
        if not open_people(H, uid):
            return "ligne absente", 0, 0, True
        hide_menus(H)
        r0 = int(ev(H, 'EClass.Home.listReserve.Count.ToString()'))
        how = ev(H, row(uid) + 'if (it == null) return "ligne absente"; it.button1.onClick.Invoke(); '
                    'var m = UnityEngine.Object.FindObjectsOfType<UIContextMenuItem>().Where(i => i.gameObject.activeInHierarchy)'
                    f'.FirstOrDefault(i => {RESERVE_MATCH}); if (m == null) return "menu ferme"; m.button.onClick.Invoke(); return "reel";')
        time.sleep(2)
        r1 = int(ev(H, 'EClass.Home.listReserve.Count.ToString()'))
        party = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {uid}) ?? EClass.Home.listReserve.Find(h => h.chara != null && h.chara.uid == {uid})?.chara; '
                      'return (c != null && c.IsPCParty).ToString();') == "True"
        close_layers_host()
        return how, r0, r1, party


def tree_near(hp):
    """Un arbre (ou ce qui se coupe) a moins de 12 cases et une case libre a cote : "x,z,x,z" ou ""."""
    return ev(H, 'var pc = EClass.pc; for (var d = 2; d <= 12; d++) for (var dx = -d; dx <= d; dx++) for (var dz = -d; dz <= d; dz++) { '
                 'if (System.Math.Max(System.Math.Abs(dx), System.Math.Abs(dz)) != d) continue; '
                 'var p = new Point(pc.pos.x + dx, pc.pos.z + dz); '
                 f'if (!p.IsValid || !p.IsInBounds || !p.HasObj || p.HasMinableBlock || p.HasChara || p.cell.sourceObj.hp < {hp}) continue; '
                 'for (var ax = -1; ax <= 1; ax++) for (var az = -1; az <= 1; az++) { var q = new Point(p.x + ax, p.z + az); '
                 'if ((ax == 0 && az == 0) || !q.IsValid || !q.IsInBounds || q.IsBlocked || q.HasChara || q.HasObj) continue; '
                 'return p.x + "," + p.z + "," + q.x + "," + q.z; } } return "";')


def cut_probe():
    """Un compagnon coupe un arbre ; le joueur donne la meme coupe : « accepted » ou « refused » (None : pas de banc)."""
    spot = tree_near(100) or tree_near(0)
    if not spot:
        return None
    px, pz, qx, qz = (int(v) for v in spot.split(","))
    with ally() as uid:
        ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); c.Teleport(new Point({qx}, {qz}), true, true); '
              f'c.SetAI(new TaskCut {{ pos = new Point({px}, {pz}) }}); "ok"')
        outcome = {}

        def asked():
            r = ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); var taken = false; '
                      'for (var a = c.ai; a != null; a = a.child) if (a is TaskCut && a.status == AIAct.Status.Running) taken = true; '
                      'if (!taken) return "free"; '
                      f'EClass.pc.SetAI(new TaskCut {{ pos = new Point({px}, {pz}) }}); '
                      'var r = EClass.pc.ai is TaskCut ? "accepted" : "refused"; if (EClass.pc.ai is TaskCut) EClass.pc.ai.Cancel(); return r;')
            outcome["r"] = r
            return r != "free"

        if not eventually(asked, timeout=40):
            return "no-ally-on-the-tree"
        ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {uid}); c.ai.Cancel(); "ok"')
        return outcome["r"]


def kill_probe():
    """L'avant et l'apres de RemotePlayerKillPatch.OnDamage, le joueur frappe par son allie : « mortel » ou « bouclier »."""
    with ally() as uid:
        return ev(H, f'var a = EClass._map.charas.Find(x => x.uid == {uid}); '
                     'var t = HarmonyLib.AccessTools.TypeByName("ElinTogether.Patches.RemotePlayerKillPatch"); '
                     'var args = new object[] { EClass.pc, a, null }; '
                     'HarmonyLib.AccessTools.Method(t, "OnDamage").Invoke(null, args); var st = args[2] as string; '
                     'HarmonyLib.AccessTools.Method(t, "OnDamageEnd").Invoke(null, new object[] { EClass.pc, a, st }); '
                     'return st == null ? "mortel" : "bouclier";')


def fuck_gate():
    """AIFuckPatch.OnRun rend vrai (le jeu fait l'acte) ou faux (la copie du mod)."""
    return ev(H, 'var m = HarmonyLib.AccessTools.Method(HarmonyLib.AccessTools.TypeByName("ElinTogether.Patches.AIFuckPatch"), "OnRun"); '
                 'var args = new object[] { new AI_Fuck(), null }; return m.Invoke(null, args).ToString();') == "True"


def brush_probe():
    """Le joueur brosse un animal a cote d'un autre qui n'a presque plus d'interet : combien de brosses de plus."""
    made = ev(H, 'var pc = EClass.pc; var t = ThingGen.Create("brush"); t.elements.SetBase(770, 20); pc.AddThing(t); pc.HoldCard(t); '
                 'var a = CharaGen.Create("putty"); var b = CharaGen.Create("putty"); '
                 'foreach (var m in new[] { a, b }) { m.hostility = Hostility.Neutral; m.c_originalHostility = Hostility.Neutral; '
                 'm.AddCondition<ConParalyze>(5000, true); EClass._zone.AddCard(m, pc.pos.GetNearestPoint(allowChara: false)); } '
                 'b.interest = 1; return t.uid + "|" + a.uid + "|" + b.uid;')
    tool, a, b = (int(v) for v in made.split("|"))
    try:
        before = int(ev(H, 'EClass.player.stats.brush.ToString()'))
        ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {a}); EClass.pc.SetAI(new AI_TendAnimal {{ target = c }}); "ok"')
        eventually(lambda: int(ev(H, 'EClass.player.stats.brush.ToString()')) > before, timeout=60)
        return int(ev(H, 'EClass.player.stats.brush.ToString()')) - before
    finally:
        ev(H, 'if (EClass.pc.ai != null) EClass.pc.ai.Cancel(); '
              f'foreach (var u in new[] {{ {a}, {b} }}) EClass._map.charas.Find(x => x.uid == u)?.Destroy(); '
              f'EClass.pc.things.Find(x => x.uid == {tool})?.Destroy(); "ok"')


def split_probe():
    """Ctrl+clic sur une pile de 10 planches, 1 glissee : la pile glissee est-elle celle d'origine ?"""
    uid = int(ev(H, 'var t = ThingGen.Create("plank"); t.SetNum(10); EClass.pc.AddThing(t); return t.uid.ToString();'))
    try:
        ev(H, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); if (!EClass.ui.IsInventoryOpen) EClass.ui.ToggleInventory(); "ok"')
        time.sleep(1)
        r = ev(H, f'var inv = LayerInventory.listInv.FirstOrDefault(q => q.mainInv); if (inv == null) return "pas d inventaire"; '
                  f'var b = inv.GetComponentsInChildren<ButtonGrid>(true).FirstOrDefault(x => x.card != null && x.card.uid == {uid}); '
                  'if (b == null) return "pas de bouton"; b.invOwner.OnCtrlClick(b); '
                  'foreach (var m in UnityEngine.Object.FindObjectsOfType<UIContextMenu>()) if (m.gameObject.activeInHierarchy) m.Hide(); '
                  'var d = EClass.ui.currentDrag as DragItemCard; if (d == null) return "rien glisse"; '
                  f'return d.from.thing.uid == {uid} ? "origine" : "nouveau";')
        return r
    finally:
        ev(H, 'if (EClass.ui.currentDrag != null) EClass.ui.EndDrag(true); '
              f'EClass.pc.things.Where(x => x.id == "plank").ToList().ForEach(x => x.Destroy()); "ok"')
        close_layers_host()


def zone_probe():
    """Lignes « Dispatching zone to all players » pour un aller-retour a Vernis (le joueur a la Prairie ne bouge pas)."""
    since = stamp()
    move(H, VERNIS)
    wait(lambda: zone_uid(H) == VERNIS, "host a Vernis", timeout=240)
    time.sleep(4)
    move(H, HOME)
    wait(lambda: zone_uid(H) == HOME, "host de retour a la Prairie", timeout=240)
    time.sleep(4)
    return log_count(since, ZONE_LINE)


def element_probe():
    """Lignes « Element ... changed » pour une force modifiee de 1 puis rendue."""
    since = stamp()
    ev(H, 'EClass.pc.elements.ModBase(70, 1); "ok"')
    time.sleep(1.5)
    ev(H, 'EClass.pc.elements.ModBase(70, -1); "ok"')
    time.sleep(1.5)
    return log_count(since, ELEMENT_LINE)


def combat_phase():
    return ev(H, PHASE)


def spawn_enemy():
    """Un monstre hostile et paralyse a cote du joueur, en vue ; renvoie son numero."""
    return int(ev(H, 'var p = EClass.pc; var m = CharaGen.Create("putty"); m.hostility = Hostility.Enemy; '
                     'm.c_originalHostility = Hostility.Enemy; m.AddCondition<ConParalyze>(5000, true); '
                     'EClass._zone.AddCard(m, p.pos.GetNearestPoint(allowChara: false)); return m.uid.ToString();'))


def drop_enemy(uid):
    ev(H, f'EClass._map.charas.Find(x => x.uid == {uid})?.Destroy(); "ok"')


def get_option(name):
    return ev(H, 'var entry = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Server"), '
                 f'"{name}").GetValue(null); return HarmonyLib.AccessTools.Property(entry.GetType(), "Value").GetValue(entry).ToString();') == "True"


# ---------------------------------------------------------------------------------------------------------------

def run_probes(label, together):
    """Les gestes Z1 a Z9 dans l'etat courant ; `together` : attendu a plusieurs (sinon : comme le jeu seul)."""
    log(f"--- gestes, {label}")
    expect = "a plusieurs" if together else "seul"

    layer, ui = pause_probe()
    if check(f"{label} : un menu qui pause le jeu a ete trouve ({layer})", layer is not None):
        check(f"{label} Z1 S16 : IsPauseGame {'faux' if together else 'vrai'} dans le menu {layer}", ui is (not together))

    fast = speed_probe()
    check(f"{label} Z2 S16 : vitesse commune 777 {'prise' if together else 'ignoree'} (vitesse du joueur {fast})",
          (fast == 777) is together)

    how, r0, r1, party = reserve_probe()
    if check(f"{label} Z3 S4 : le clic sur « reserve » a joue le vrai menu ({how})", how == "reel"):
        if together:
            check(f"{label} Z3 S4 : refuse a plusieurs, rien ne bouge (reserve {r0} -> {r1}, dans le groupe : {party})", r1 == r0 and party)
        else:
            check(f"{label} Z3 S4 : seul, le compagnon est en reserve et hors du groupe (reserve {r0} -> {r1}, dans le groupe : {party})",
                  r1 == r0 + 1 and not party)

    cut = cut_probe()
    if check(f"{label} Z4 S2 : un compagnon coupe un arbre voisin et le joueur peut demander la meme coupe ({cut})",
             cut in ("accepted", "refused")):
        check(f"{label} Z4 S2 : coupe du joueur {'refusee (la case est prise)' if together else 'acceptee'} : {cut}",
              cut == ("refused" if together else "accepted"))

    shield = kill_probe()
    check(f"{label} Z5 S3 : coup d'allie sur le joueur : {'bouclier du mod' if together else 'aucun bouclier'} ({shield})",
          shield == ("bouclier" if together else "mortel"))

    check(f"{label} Z6 S1 : AIFuckPatch.OnRun rend {'faux (la copie du mod)' if together else 'vrai (le jeu fait l acte)'}",
          fuck_gate() is (not together))
    if not together:
        brushes = brush_probe()
        check(f"{label} Z6 S1 : seul, le compteur de brosses monte pour un animal brosse a cote d'un autre ({brushes} de plus)",
              brushes >= 1)

    kind = split_probe()
    if check(f"{label} Z7 S5 : Ctrl+clic sur une pile, un morceau glisse ({kind})", kind in ("origine", "nouveau")):
        check(f"{label} Z7 S5 : la pile glissee est {'le nouveau morceau' if together else 'celle d origine'} ({kind})",
              kind == ("nouveau" if together else "origine"))

    lines = zone_probe()
    check(f"{label} Z8 S6 : aller-retour a Vernis : {lines} ligne(s) « {ZONE_LINE} » (attendu : "
          f"{'au moins 2' if together else 'aucune'})", lines >= 2 if together else lines == 0)
    if together:
        both_joined(H, A, HOME)

    lines = element_probe()
    check(f"{label} Z9 S7 : competence modifiee : {lines} ligne(s) « Element changed » (attendu : "
          f"{'au moins 1' if together else 'aucune'})", lines >= 1 if together else lines == 0)


# ---------------------------------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="phases : alone, arrive, leave, travel")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = stamp()
    phases = a.only.split(",") if a.only else ["alone", "arrive", "leave", "travel"]
    guest = has_client()
    if not guest:
        log("pas de fenetre client sur 27552 : seule la partie « seul » est jouee")
        phases = [p for p in phases if p == "alone"]

    pre = {k: get_option(k) for k in ("TurnBasedCombat", "PlayerCombatTime")}
    enemy = 0
    try:
        # --- 1. seul ---------------------------------------------------------------------------------------
        if guest and not host_alone():
            log("un client est connecte : il part pour le temps « seul »")
            leave()
        close_layers()
        check("Z0 le host a sa session ouverte, seul (aucun pair)",
              state(H)["role"] == "Host" and not state(H)["connected"] and counted() == 1)
        check("Z0 la porte HasCompany est fausse seul", not company())
        check("la Prairie est une base (la fenetre des habitants y existe)", ev(H, 'EClass._zone.IsPCFaction.ToString()') == "True")
        set_option("TurnBasedCombat", True)
        set_option("PlayerCombatTime", False)
        # un ennemi paralyse en vue : il y sera avant, pendant et apres l'arrivee de l'invite
        enemy = spawn_enemy()
        time.sleep(3)
        check(f"Z10 S12/S15 : seul, combat tour par tour avec un ennemi en vue : Phase {combat_phase()} (attendu Inactive)",
              combat_phase() == "Inactive")
        drop_enemy(enemy)
        enemy = 0
        if "alone" in phases:
            run_probes("seul", together=False)

        if not guest:
            return finish(t0)

        # --- 2. l'invite arrive, le combat deja la ----------------------------------------------------------
        if "arrive" in phases or "leave" in phases or "travel" in phases:
            enemy = spawn_enemy()
            time.sleep(2)
            log("l'invite arrive")
            arrive()
            check("Z0 la porte HasCompany est vraie des que l'invite est la", company() and counted() == 2)
            check("Z10 S12/S15 : l'invite arrive en plein combat : Phase quitte Inactive en moins de 10 s",
                  eventually(lambda: combat_phase() != "Inactive", timeout=10))
            drop_enemy(enemy)
            enemy = 0
            time.sleep(2)
            set_option("TurnBasedCombat", False)
            run_probes("avec un invite", together=True)

        # --- 3. l'invite part ------------------------------------------------------------------------------
        if "leave" in phases:
            set_option("TurnBasedCombat", True)
            enemy = spawn_enemy()
            time.sleep(3)
            check(f"Z10 : avec l'invite et un ennemi en vue, Phase = {combat_phase()} (pas Inactive)", combat_phase() != "Inactive")
            log("l'invite part")
            leave()
            check("Z0 la porte HasCompany est fausse apres le depart", not company() and counted() == 1)
            check(f"Z10 : l'invite est parti en combat : Phase revient a Inactive ({combat_phase()})",
                  eventually(lambda: combat_phase() == "Inactive", timeout=10))
            drop_enemy(enemy)
            enemy = 0
            run_probes("redevenu seul", together=False)

        # --- 4. l'invite voyage seul -----------------------------------------------------------------------
        if "travel" in phases:
            if host_alone():
                arrive()
            move(A, VERNIS)
            from travel_suite import client_settled  # noqa: E402
            wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=240)
            time.sleep(3)
            check(f"Z0 le piege : l'invite voyage seul, CurrentPlayers n'a plus que l'host ({counted()}) mais la porte est vraie",
                  counted() == 1 and company())
            layer, ui = pause_probe()
            check(f"Z1 regle choisie : pendant qu'un invite voyage, le menu {layer} ne met pas le jeu en pause "
                  f"(le plan voulait le contraire : decision, voir l'etat du plan) : IsPauseGame {ui}", ui is False)
            check("Z6 AIFuckPatch.OnRun rend faux tant qu'un invite existe (copie du mod gardee)", not fuck_gate())
            move(A, HOME)
            both_joined(H, A, HOME)
            leave()
            check("Z0 retour a « seul » apres le voyage de l'invite", not company())
    finally:
        if enemy:
            drop_enemy(enemy)
        for name, value in pre.items():
            set_option(name, value)
        close_layers()
    finish(t0)


def finish(t0):
    for name, port in (("host", H), ("A", A)):
        try:
            print(f"    capture {name} : {shot(f'solo-{name}', port)}")
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
