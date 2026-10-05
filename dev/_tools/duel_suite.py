"""Duels entre joueurs (conseil 7, PLAN_duels_et_membres.md). Test court, sur des instances deja lancees (host + 1
client, cote a cote a la Prairie).

    python _tools/mp_test.py
    python _tools/duel_suite.py            # ou --only p1

P1  hors duel, un joueur ne peut pas tuer l'autre : la victime a 1 point de vie est frappee par l'autre joueur (le coup
    de melee du jeu, ce que fait Maj + clic) jusqu'a ce que le coup porte ; elle reste en vie, a 0 point de vie au
    plus bas, chez les deux. Dans les deux sens.

D1  le defi par le menu du jeu sur l'autre joueur (absent si l'host decoche « Duels ») : Oui (le duel commence apres
    le compte a rebours), une autre fois Non, puis sans reponse (15 s : refuse tout seul, la boite se ferme).
D2  pendant le duel, le coup qui tuerait fait perdre : personne ne meurt, les deux sont soignes (pv, mana, endurance),
    aucune perte (or, renommee, karma, sac, tombe, or au sol : compares avant / apres, au jour 100).
D3  les compagnons : ils ne se battent pas, et celui que l'autre duelliste frappe a mort reste en vie.
D4  le perdant puis le gagnant relancent un duel : il se joue jusqu'au bout.
D5  un duelliste quitte la carte : le duel s'arrete sans gagnant, un nouveau duel est possible au retour.
D6  un second defi pendant un duel est refuse : pas de boite, le duel continue et se finit.

Ce que le banc ne joue pas comme un joueur : le coup est l'acte de melee du jeu lance sur la cible (pas la souris) ;
les points de vie de la victime sont baisses par l'host et la force de celui qui frappe montee a 300 (elle le reste) ;
le menu est celui du jeu (ActPlan, « toutes les actions ») construit par le pont, pas ouvert a la souris ; les sorts,
les projectiles et les potions ne sont pas essayes ; les messages affiches ne sont pas lus (on lit l'etat du duel :
PlayerDuel.Describe) ; l'invite se place par teleportation ; le jour 100 et l'or sont poses par le banc. Pas joue du
tout : la deconnexion et la mort d'autre chose pendant un duel, l'host qui quitte la carte, un duel a trois joueurs.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base_suite import click_yes, dialog_open  # noqa: E402
from combat_suite import set_option  # noqa: E402
from death_suite import death_screen  # noqa: E402
from guest_suite import awake, chara, clear_conditions, close_layers, drop, free_next_to, give, stand, tame  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, dismiss_dialogs, ev, eventually,  # noqa: E402
                          move, scan_logs, wait)

H, A = 27551, 27552


def p1(ctx):
    """hors duel, un joueur ne peut pas tuer l'autre : le coup qui tuerait laisse la victime en vie"""
    for who, striker, victim in (("l'host", "h", "a"), ("l'invite", "a", "h")):
        sport, suid = ctx[striker]
        vport, vuid = ctx[victim]
        clear_conditions(vuid)
        alive = lambda p: ev(p, f'var c = {chara(p, vuid)}; return (c != null && !c.isDead).ToString();') == "True"  # noqa: E731
        hp = lambda p: int(ev(p, f'{chara(p, vuid)}.hp.ToString()'))  # noqa: E731
        # cote a cote : la victime vient a cote de celui qui frappe (par son propre jeu : l'host ne deplace pas un invite)
        if int(ev(H, f'{chara(H, vuid)}.pos.Distance({chara(H, suid)}.pos).ToString()')) > 1:
            stand(vport, vuid, *(int(v) for v in free_next_to(H, suid, 1).split(",")))
        time.sleep(2)
        # un coup qui fait plus d'un point de degat : sinon 1 pv - 1 = 0, et personne ne meurt a 0
        for p in (H, A):
            ev(p, f'{chara(p, suid)}.elements.SetBase(70, 300); "ok"')
        hit = False
        for n in range(1, 21):
            # 5 pv : un coup qui tuerait laisse 0 (puis 1 ou 2 en se soignant), un coup rate laisse 5
            ev(H, f'{chara(H, vuid)}.hp = 5; "ok"')
            time.sleep(1.5)
            awake(sport)
            ev(sport, f'var t = {chara(sport, vuid)}; ACT.Melee.Perform(EClass.pc, t, t.pos); "ok"')
            # un coup qui porte : mort (avant la correction) ou 0 pv (apres) ; les pv remontent vite, regarder tout de suite
            for _ in range(12):
                if not alive(H) or hp(H) < 4:
                    hit = True
                    break
                time.sleep(0.2)
            if hit:
                break
        log(f"{who} frappe l'autre joueur a 5 points de vie : touche au coup {n} (pv chez l'host {hp(H) if alive(H) else 'mort'})")
        if not check(f"{who} : un coup a porte sur l'autre joueur en {n} essais", hit):
            continue
        time.sleep(3)
        ok = check(f"{who} frappe : l'autre joueur est toujours en vie, chez l'host ({alive(H)}, pv {hp(H) if alive(H) else '-'})", alive(H))
        check(cond=eventually(lambda: alive(vport), timeout=8), label=f"{who} frappe : et dans le jeu de la victime ({alive(vport)})")
        if ok:
            check(f"{who} frappe : ses points de vie ne passent pas sous 0, dans les deux jeux ({hp(H)}, chez lui {hp(vport)})", hp(H) >= 0 and hp(vport) >= 0)
            ev(H, f'var c = {chara(H, vuid)}; c.hp = c.MaxHP; "ok"')
        else:
            # la vraie mort (avant la correction) : passer l'ecran de mort pour continuer
            try:
                log(f"ecran de mort : {death_screen(vport, 0)}")
            except Exception as ex:  # noqa: BLE001
                log(f"ecran de mort non passe : {ex}")
            time.sleep(5)
        clear_conditions(vuid)
        for p in (H, A):
            ev(p, 'EClass.pc.SetNoGoal(); "ok"')


# ---------------------------------------------------------------------------------------------------------------
# duels (etapes 2 a 4)

DUEL = 'i.act is DynamicAct d && d.id == "emp_act_duel"'


def describe(port):
    """Ou en est le duel de ce joueur, dit par son jeu : "Fighting 12 vs 34 winner 0 " (voir PlayerDuel.Describe)."""
    return ev(port, 'ElinTogether.Helper.PlayerDuel.Describe()')


def winner(port):
    return int(describe(port).split("winner ")[1].split()[0])


def other(key):
    return "h" if key == "a" else "a"


def name(key):
    return "l'invite" if key == "a" else "l'host"


def menu(port, uid, pick):
    """Le menu « toutes les actions » du jeu sur ce personnage (ActPlan._Update, ActInput.AllAction : la ou le jeu met
    « echanger ») ; on execute la premiere action qui verifie `pick` (condition C# sur `i`)."""
    return ev(port,
              f'var c = {chara(port, uid)}; var p = new ActPlan {{ input = ActInput.AllAction }}; var pt = new PointTarget(); '
              'pt.pos.Set(c.pos); p._Update(pt); '
              'var offered = string.Join(",", p.list.Select(i => i.act is DynamicAct d ? d.id : i.act.GetType().Name)); '
              f'var item = p.list.FirstOrDefault(i => {pick}); if (item == null) return "action absente, proposees : " + offered; '
              'item.Perform(); return "ok " + (item.act is DynamicAct x ? x.id : item.act.GetType().Name) + " parmi " + offered;')


def click_no(port):
    """Clique « No » dans la boite oui/non du jeu."""
    return ev(port, 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return "pas de boite"; '
                    'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(true).FirstOrDefault(x => '
                    'x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text.StartsWith("No"))); '
                    'if (b == null) return "pas de bouton"; b.onClick.Invoke(); return "clic";')


def prepare(ctx):
    """Mise en place : jour 100 dans les deux jeux (avant le jour 90 une mort ne coute rien : « aucune perte » ne
    prouverait rien), de l'or dans chaque sac, pleine forme, rien d'ouvert."""
    for p in (H, A):
        ev(p, 'if (EClass.player.stats.days < 100) EClass.player.stats.days = 100; EClass.pc.SetNoGoal(); "ok"')
    close_layers()
    for key in ("a", "h"):
        port, uid = ctx[key]
        if int(ev(H, f'{chara(H, uid)}.GetCurrency().ToString()')) < 300:
            give(ctx, key, "money", 1000)
        clear_conditions(uid)
        ev(H, f'var c = {chara(H, uid)}; c.hp = c.MaxHP; "ok"')
    time.sleep(1)


def next_to(ctx, key):
    """Ce joueur vient a cote de l'autre (par son propre jeu : l'host ne deplace pas un invite)."""
    port, uid = ctx[key]
    ouid = ctx[other(key)][1]
    if int(ev(H, f'{chara(H, uid)}.pos.Distance({chara(H, ouid)}.pos).ToString()')) > 1:
        stand(port, uid, *(int(v) for v in free_next_to(H, ouid, 1).split(",")))
        time.sleep(2)


def challenge(ctx, key):
    """Ce joueur defie l'autre par le menu du jeu ; renvoie ce que le menu a fait."""
    port, _ = ctx[key]
    next_to(ctx, key)
    awake(port)
    return menu(port, ctx[other(key)][1], DUEL)


def start_duel(ctx, key):
    """Defi par le menu, l'autre clique Oui dans la vraie boite ; vrai quand les deux jeux disent que le duel se joue."""
    oport = ctx[other(key)][0]
    r = challenge(ctx, key)
    if not check(f"{name(key)} defie par le menu ({r[:60]}) : l'autre voit la boite", eventually(lambda: dialog_open(oport), timeout=10)):
        return False
    click_yes(oport)
    started = eventually(lambda: all(describe(p).startswith("Fighting") for p in (H, A)), timeout=12)
    return check(f"{name(key)} defie, l'autre dit oui : le duel se joue chez les deux apres le compte a rebours ({describe(H)} / {describe(A)})",
                 started)


def blow(ctx, key, vuid, done):
    """Ce joueur frappe ce personnage (5 points de vie, poses par l'host) par l'acte de melee du jeu jusqu'a ce que
    `done()` soit vrai ; renvoie le nombre de coups, 0 si rien en 20 coups. Comme P1 : la force a 300 pour qu'un coup
    fasse plus d'un point de degat."""
    sport, suid = ctx[key]
    for p in (H, A):
        ev(p, f'{chara(p, suid)}.elements.SetBase(70, 300); "ok"')
    for n in range(1, 21):
        # un compagnon bouge : le joueur se remet a cote de lui avant chaque coup
        if int(ev(H, f'{chara(H, vuid)}.pos.Distance({chara(H, suid)}.pos).ToString()')) > 1:
            stand(sport, suid, *(int(v) for v in free_next_to(H, vuid, 1).split(",")))
        ev(H, f'{chara(H, vuid)}.hp = 5; "ok"')
        time.sleep(1.5)
        awake(sport)
        ev(sport, f'var t = {chara(sport, vuid)}; ACT.Melee.Perform(EClass.pc, t, t.pos); "ok"')
        for _ in range(12):
            if done():
                return n
            time.sleep(0.2)
    return 0


def finish(ctx, key):
    """Ce duelliste porte le coup qui tuerait l'autre ; vrai quand le duel est gagne par lui, dans les deux jeux."""
    uid = ctx[key][1]
    next_to(ctx, key)
    n = blow(ctx, key, ctx[other(key)][1], lambda: describe(H).startswith("Won"))
    won = n > 0 and eventually(lambda: all(describe(p).startswith("Won") and winner(p) == uid for p in (H, A)), timeout=8)
    check(f"{name(key)} porte le coup qui tuerait (coup {n}) : il a gagne le duel, dit par les deux jeux ({describe(H)} / {describe(A)})", won)
    for p in (H, A):
        ev(p, 'EClass.pc.SetNoGoal(); "ok"')
    return won


def alive(port, uid):
    return ev(port, f'var c = {chara(port, uid)}; return (c != null && !c.isDead).ToString();') == "True"


def losses(ctx):
    """Ce qu'une vraie mort ou un crime couteraient : or (vu par l'host et par soi), objets du sac, renommee et karma
    de chacun, tombes et or au sol sur la carte."""
    out = {}
    for key in ("a", "h"):
        port, uid = ctx[key]
        out[name(key)] = (int(ev(H, f'{chara(H, uid)}.GetCurrency().ToString()')),
                          int(ev(port, 'EClass.pc.GetCurrency().ToString()')),
                          int(ev(H, f'{chara(H, uid)}.things.Where(t => t.id != "money").Sum(t => t.Num).ToString()')),
                          ev(port, '"renommee " + EClass.player.fame + " karma " + EClass.player.karma'))
    out["carte"] = ev(H, 'EClass._map.things.Count(t => t.trait is TraitGrave) + " tombe(s), " + '
                         'EClass._map.things.Where(t => t.id == "money").Sum(t => t.Num) + " or au sol"')
    return out


def d1(ctx):
    """le defi par le menu : absent sans la case de l'host ; Oui, puis Non, puis sans reponse"""
    for key in ("a", "h"):
        who, port, oport = name(key), ctx[key][0], ctx[other(key)][0]
        prepare(ctx)
        next_to(ctx, key)
        # la case de l'host
        rule = lambda p: ev(p, 'ElinTogether.Net.NetSession.Instance.Rules.AllowDuels.ToString()')  # noqa: E731
        set_option("Duels", False)
        eventually(lambda: rule(port) == "False", timeout=10)
        r = menu(port, ctx[other(key)][1], "false")
        check(f"{who}, case « Duels » decochee : le menu n'offre pas le defi ({r[:90]})", "emp_act_duel" not in r)
        set_option("Duels", True)
        check(f"{who} : la case recochee arrive dans son jeu", eventually(lambda: rule(port) == "True", timeout=10))
        # oui
        if start_duel(ctx, key):
            finish(ctx, key)
        # non
        prepare(ctx)
        r = challenge(ctx, key)
        if check(f"{who} defie une deuxieme fois ({r[:40]}) : l'autre voit la boite", eventually(lambda: dialog_open(oport), timeout=10)):
            click_no(oport)
            declined = eventually(lambda: all(describe(p).endswith("emp_duel_declined") for p in (H, A)), timeout=8)
            check(f"{who} : l'autre dit non, les deux jeux disent le defi refuse ({describe(H)} / {describe(A)})", declined)
            time.sleep(5)
            check(f"{who} : aucun duel ne commence apres le non ({describe(H)})", describe(H).startswith("Cancelled"))
        # sans reponse
        r = challenge(ctx, key)
        if check(f"{who} defie une troisieme fois ({r[:40]}) : l'autre voit la boite", eventually(lambda: dialog_open(oport), timeout=10)):
            time.sleep(11)
            check(f"{who} : apres 11 s le defi attend toujours ({describe(H)})", describe(H).startswith("Invited"))
            dropped = eventually(lambda: all(describe(p).endswith("emp_duel_noanswer") for p in (H, A)), timeout=10)
            check(f"{who} : sans reponse, le defi tombe a 15 s dans les deux jeux ({describe(H)} / {describe(A)})", dropped)
            check(f"{who} : la boite de l'autre s'est fermee toute seule", eventually(lambda: not dialog_open(oport), timeout=5))


def d2(ctx):
    """pendant le duel, le coup qui tuerait fait perdre : personne ne meurt, les deux sont soignes, aucune perte"""
    for key in ("a", "h"):
        who = name(key)
        prepare(ctx)
        # entames avant le duel, chacun dans son jeu : la fin doit tout rendre
        for p in (H, A):
            ev(p, 'EClass.pc.mana.value = EClass.pc.mana.max / 2; EClass.pc.stamina.value = EClass.pc.stamina.max / 2; "ok"')
        time.sleep(2)
        before = losses(ctx)
        if not start_duel(ctx, key):
            continue
        won = finish(ctx, key)
        time.sleep(3)
        for k in ("a", "h"):
            port, uid = ctx[k]
            check(f"{who} gagne : {name(k)} est en vie, dans les deux jeux", alive(H, uid) and alive(A, uid))
            full = lambda p, u=uid: ev(p, f'var c = {chara(p, u)}; return (c.hp >= c.MaxHP).ToString();') == "True"  # noqa: E731
            check(f"{who} gagne : {name(k)} a tous ses points de vie, chez l'host et chez lui",
                  won and eventually(lambda: full(H) and full(port), timeout=8))  # noqa: B023
            vit = ev(port, 'EClass.pc.mana.value + "/" + EClass.pc.mana.max + " " + EClass.pc.stamina.value + "/" + EClass.pc.stamina.max')
            check(f"{who} gagne : {name(k)} a retrouve mana et endurance dans son jeu ({vit})",
                  won and ev(port, '(EClass.pc.mana.value >= EClass.pc.mana.max && EClass.pc.stamina.value >= EClass.pc.stamina.max).ToString()') == "True")
        after = losses(ctx)
        for what in before:
            check(f"{who} gagne, aucune perte : {what} {before[what]} -> {after[what]}", before[what] == after[what])


def d3(ctx):
    """les compagnons des duellistes ne se battent pas et ne meurent pas du coup de l'autre duelliste"""
    prepare(ctx)
    cats = {k: tame(ctx, "cat", k) for k in ("a", "h")}
    if not check(f"chaque joueur a un chat ({cats})", all(cats.values())):
        drop([c for c in cats.values() if c])
        return
    for c in cats.values():
        clear_conditions(c)
    karma = lambda: [ev(p, 'EClass.player.karma.ToString()') for p in (H, A)]  # noqa: E731
    before = karma()
    try:
        if not start_duel(ctx, "a"):
            return
        for key in ("a", "h"):
            who, cat = name(key), cats[other(key)]
            n = blow(ctx, key, cat, lambda: not alive(H, cat) or int(ev(H, f'{chara(H, cat)}.hp.ToString()')) < 4)  # noqa: B023
            if not check(f"{who} frappe le chat de l'autre a 5 points de vie : un coup a porte (coup {n})", n > 0):
                continue
            time.sleep(3)
            check(f"{who} a frappe a mort le chat de l'autre : il est en vie, dans les deux jeux", alive(H, cat) and alive(A, cat))
            ev(H, f'var c = {chara(H, cat)}; if (c != null) c.hp = c.MaxHP; "ok"')
        # qui les chats ont pris pour ennemi, chez l'host (c'est lui qui les fait agir)
        foes = ev(H, f'string.Join(",", new[] {{ {cats["a"]}, {cats["h"]} }}.Select(u => EClass._map.charas.Find(x => x.uid == u))'
                     '.Select(c => c == null ? "absent" : c.enemy == null ? "personne" : c.enemy.uid.ToString()))')
        check(f"les chats ne se battent pas : aucun n'a un joueur pour ennemi ({foes})",
              not any(str(ctx[k][1]) in foes.split(",") for k in ("a", "h")))
        check(f"le duel se joue toujours ({describe(H)})", describe(H).startswith("Fighting"))
        check(f"le karma de personne n'a bouge ({before} -> {karma()})", before == karma())
        finish(ctx, "h")
    finally:
        drop(list(cats.values()))


def d4(ctx):
    """le perdant puis le gagnant relancent un duel : il se joue jusqu'au bout"""
    prepare(ctx)
    if not (start_duel(ctx, "a") and finish(ctx, "a")):
        return
    prepare(ctx)
    log("le perdant (l'host) redefie")
    if not (start_duel(ctx, "h") and finish(ctx, "h")):
        return
    prepare(ctx)
    log("le gagnant (l'host) redefie")
    if start_duel(ctx, "h"):
        finish(ctx, "a")


def d5(ctx):
    """un duelliste quitte la carte : le duel s'arrete sans gagnant, un nouveau duel est possible au retour"""
    prepare(ctx)
    if not start_duel(ctx, "h"):
        return
    try:
        move(A, VERNIS)
        stopped = eventually(lambda: describe(H).endswith("winner 0 emp_duel_over"), timeout=60)
        check(f"l'invite quitte la carte en plein duel : chez l'host le duel s'arrete sans gagnant ({describe(H)})", stopped)
        wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
        time.sleep(3)
        dismiss_dialogs(A)
        check(f"l'invite parti n'est plus en duel dans son jeu ({describe(A)})", not describe(A).startswith(("Fighting", "Countdown", "Invited")))
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)
        time.sleep(4)
        dismiss_dialogs(A)
    prepare(ctx)
    log("de retour : personne n'est reste « en duel »")
    if start_duel(ctx, "a"):
        finish(ctx, "a")


def d6(ctx):
    """un second defi pendant un duel est refuse : pas de boite, le duel continue et se finit"""
    prepare(ctx)
    if not start_duel(ctx, "a"):
        return
    was = describe(H)
    for key in ("h", "a"):
        r = challenge(ctx, key)
        time.sleep(3)
        check(f"{name(key)} defie pendant le duel ({r[:40]}) : aucune boite chez l'autre", not dialog_open(ctx[other(key)][0]))
        check(f"{name(key)} defie pendant le duel : le meme duel continue, dans les deux jeux ({describe(H)} / {describe(A)})",
              describe(H) == was and describe(A) == was)
    finish(ctx, "h")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [p1, d1, d2, d3, d4, d5, d6]
    days = [ev(p, 'EClass.player.stats.days.ToString()') for p in (H, A)]
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
                print(f"    capture {name} : {shot(f'duel-{step.__name__}-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass
    # le jour 100 du banc (prepare) ne reste pas dans la partie
    for p, d in zip((H, A), days):
        ev(p, f'EClass.player.stats.days = {d}; "ok"')
    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
