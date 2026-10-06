"""Entrainement au mannequin (retour d'une vraie partie, 0.26.524 : « ne marche pas en tant qu'invite »).
Test court, sur des instances deja lancees (host + 1 client, tous les deux sur la meme carte).

    python _tools/mp_test.py
    python _tools/dummy_suite.py            # ou --only m1,m2

M1  l'invite, sur la carte de l'host : un mannequin est pose a cote de lui, il s'entraine par le menu du mannequin
    pendant 20 coups. Il s'entraine toujours (avant la correction : arrete tout de suite par l'host, « Progress
    begin AI_PracticeDummy ... has no matching act »), ses coups touchent, il gagne de l'experience dans son jeu,
    son endurance baisse (au plus 1 par coup, comme en solo), pas de coup en double, le mannequin est toujours la ;
    il arrete (le geste d'arret du joueur) et l'arret prend ; sa copie chez l'host a la meme experience et la meme
    endurance.
M2  l'host (temoin) : la meme chose, la copie est lue chez l'invite.
M3  l'invite seul sur une autre carte (Vernis) : la meme chose dans son seul jeu, puis il revient.
M4  tache INCONNUE de la table (AI_Paint, peindre sur un chevalet : pas de ligne dans CharaTaskRemoteEvent, elle part
    comme FakeTask). Correction generale (PLAN_mannequin_invite.md, « Correction generale ») : l'invite ne l'annonce pas
    a l'host et l'arrete seul. Deux temps : (a) il peint jusqu'au bout (avant : l'host repondait « no matching act »
    et la peinture s'arretait) ; (b) un arret demande en pleine peinture prend tout de suite, sans attendre l'host
    (avant : l'arret etait retenu). La toile peinte est lue chez l'host a titre d'information seulement.
M5  l'invite s'entraine, la copie de sa tache est effacee chez l'host (SetNoGoal sur sa copie), puis il arrete : l'arret
    prend (l'host renvoie l'ordre d'arret quand il ne trouve pas la tache ; sinon le filet de 2 s chez l'invite).
    Avant : l'arret restait retenu pour toujours. Le delai lu dit lequel des deux a joue (< 1 s : l'host). Pas joue :
    que SetNoGoal sur la copie de l'host efface bien la tache comme une disparition reelle.

Ce que le banc appelle : le clic gauche sur la case du mannequin (ActPlan._Update, la liste que le jeu propose),
l'entree AI_PracticeDummy, puis Item.Perform() : ce que fait le clic. L'arret : AIAct.Cancel() apres
CanManualCancel(), ce que fait une touche pendant une tache (AM_Adv).

Ce que le banc ne joue pas comme un joueur :
- le mannequin est cree et installe par le banc (ZoneAddCard + Install), a cote du joueur : pas de marche jusqu'a lui ;
- l'endurance est remise au maximum avant de commencer (dans le jeu du joueur) ;
- M4 : la tache est lancee par SetAI (le dernier appel d'AM_Paint), sans passer par le mode de peinture et le clic ;
  l'arret de M4 est un appel direct a AIAct.Cancel() apres quelques Tick() (le joueur ne peut pas arreter une
  peinture a la main : CanManualCancel est faux) ;
- pas de tir ni de lancer sur le mannequin (ActRanged / ActThrow lancent la meme tache, pas joue) ;
- pas de prisonnier attache (meme tache, pas joue) ; pas de fin par epuisement (endurance sous zero) ;
- « pas de coup en double » compare les coups qui touchent au nombre de tours et d'armes : un enchantement de coups
  en chaine peut le fausser.
Jamais lance : ecrit sans avoir tourne.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guest_suite import awake, chara, clear_conditions, first_id, free_next_to, use_menu  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from guest_suite import give  # noqa: E402
from travel_suite import (HOME, RESULTS, VERNIS, both_joined, check, client_settled, ev, eventually, move, scan_logs,  # noqa: E402
                          session_log_lines, wait)

H, A = 27551, 27552
BLOWS = 20


def skills(port, uid):
    """Experience de chaque competence de ce personnage, vue par ce jeu : {id: "niveau:exp"}."""
    raw = ev(port, f'var c = {chara(port, uid)}; return c == null ? "" : '
                   'string.Join(";", c.elements.dict.Values.Select(e => e.id + "=" + e.vBase + ":" + e.vExp));')
    return dict(x.split("=") for x in raw.split(";") if x)


def stamina(port, uid):
    return int(ev(port, f'{chara(port, uid)}.stamina.value.ToString()'))


def practice(port):
    """Ou en est l'entrainement de ce joueur, dans son jeu : (tours, coups qui touchent), (-1, -1) s'il ne s'entraine pas."""
    turn, hit = ev(port, 'var p = EClass.pc.ai as AI_PracticeDummy; return p != null && p.IsRunning ? p.turn + "|" + p.hit : "-1|-1";').split("|")
    return int(turn), int(hit)


def train(who, port, uid, maker, other):
    """Ce joueur s'entraine sur un mannequin pose a cote de lui par `maker` (le jeu qui tient la carte).
    `other` : le jeu ou lire sa copie (None : il est seul)."""
    dummy_id = first_id("TrainingDummy")
    spot = free_next_to(port, uid, 1)
    if not check(f"{who} : un mannequin existe dans le jeu ({dummy_id}) et une case est libre a cote de lui ({spot})", dummy_id and spot):
        return
    x, z = spot.split(",")
    dummy = int(ev(maker, f'var t = ThingGen.Create("{dummy_id}"); EClass._zone.AddCard(t, new Point({x}, {z})).Install(); return t.uid.ToString();'))
    there = lambda p: ev(p, f'var t = EClass._map.things.Find(m => m.uid == {dummy}); '  # noqa: E731
                            'return t == null ? "absent" : (t.isDestroyed ? "detruit" : t.IsInstalled ? "pose" : "pas pose");')
    try:
        if not check(f"{who} : le mannequin est pose a cote de lui, dans son jeu ({there(port)})",
                     eventually(lambda: there(port) == "pose", timeout=15)):
            return
        ev(port, 'EClass.pc.SetNoGoal(); EClass.pc.stamina.value = EClass.pc.stamina.max; "ok"')
        time.sleep(3)
        exp0, sta0 = skills(port, uid), stamina(port, uid)
        weapons = int(ev(port, 'EClass.pc.body.slots.Count(s => s.elementId == 35 && s.thing != null && s.thing.source.offense.Length >= 2).ToString()'))
        awake(port)
        did = use_menu(port, (x, z), "i.act is AI_PracticeDummy")
        if not check(f"{who} : le menu du mannequin propose l'entrainement et il le lance ({did})", did.startswith("ok AI_PracticeDummy")):
            return
        reached = eventually(lambda: awake(port) and practice(port)[0] >= BLOWS, timeout=90)
        turn, hit = practice(port)
        check(f"{who} : il s'entraine toujours apres {BLOWS} coups (tours : {turn})", reached)
        if turn < 0:
            return
        check(f"{who} : ses coups touchent le mannequin ({hit} sur {turn} tours)", hit > 0)
        check(f"{who} : pas de coup en double ({hit} touches, {turn} tours, {max(1, weapons)} arme(s))", hit <= turn * max(1, weapons) + 2)
        check(f"{who} : le mannequin est toujours la, dans son jeu ({there(port)}) et chez celui qui tient la carte ({there(maker)})",
              there(port) == "pose" and there(maker) == "pose")

        ev(port, 'if (EClass.pc.ai.CanManualCancel()) EClass.pc.ai.Cancel(); "ok"')
        check(cond=eventually(lambda: practice(port)[0] < 0, timeout=15), label=f"{who} : il arrete, et l'arret prend")
        time.sleep(2)
        exp1, sta1 = skills(port, uid), stamina(port, uid)
        gained = {k: f"{exp0.get(k, '0:0')} -> {v}" for k, v in exp1.items() if exp0.get(k) != v}
        check(f"{who} : il a gagne de l'experience dans son jeu ({gained or 'rien'})", bool(gained))
        check(f"{who} : son endurance a baisse, au plus de 1 par coup ({sta0} -> {sta1}, {turn} coups au moins)", 0 < sta0 - sta1 <= turn + 5)
        if other is None:
            return
        same = lambda: all(skills(other, uid).get(k) == exp1[k] for k in gained)  # noqa: E731
        check(cond=eventually(same, timeout=20),
              label=f"{who} : sa copie chez l'autre joueur a la meme experience ({ {k: skills(other, uid).get(k) for k in gained} })")
        check(cond=eventually(lambda: stamina(other, uid) == stamina(port, uid), timeout=30),
              label=f"{who} : et la meme endurance ({stamina(other, uid)} pour {stamina(port, uid)})")
    finally:
        ev(port, 'if (EClass.pc.ai is AI_PracticeDummy) EClass.pc.SetNoGoal(); "ok"')
        ev(maker, f'var t = EClass._map.things.Find(m => m.uid == {dummy}); if (t != null) t.Destroy(); "ok"')


def m1(ctx):
    """l'invite s'entraine au mannequin sur la carte de l'host"""
    port, uid = ctx["a"]
    clear_conditions(uid)
    train("l'invite", port, uid, H, H)


def m2(ctx):
    """l'host s'entraine au mannequin (temoin)"""
    port, uid = ctx["h"]
    clear_conditions(uid)
    train("l'host", port, uid, H, A)


def m3(ctx):
    """l'invite seul sur une autre carte s'entraine au mannequin"""
    port, uid = ctx["a"]
    move(A, VERNIS)
    try:
        wait(client_settled(A, VERNIS, True), "invite seul a Vernis", timeout=180)
        time.sleep(3)
        train("l'invite seul", port, uid, A, None)
    finally:
        move(A, HOME)
        both_joined(H, A, HOME)


def m5(ctx):
    """la copie de la tache de l'invite a disparu chez l'host : son arret prend quand meme (reponse de l'host, sinon filet de 2 s)"""
    port, uid = ctx["a"]
    clear_conditions(uid)
    dummy_id = first_id("TrainingDummy")
    spot = free_next_to(port, uid, 1)
    if not check(f"un mannequin existe ({dummy_id}) et une case est libre a cote de l'invite ({spot})", dummy_id and spot):
        return
    x, z = spot.split(",")
    dummy = int(ev(H, f'var t = ThingGen.Create("{dummy_id}"); EClass._zone.AddCard(t, new Point({x}, {z})).Install(); return t.uid.ToString();'))
    try:
        check("le mannequin est pose chez l'invite", eventually(
            lambda: ev(port, f'var t = EClass._map.things.Find(m => m.uid == {dummy}); return (t != null && t.IsInstalled).ToString();') == "True",
            timeout=15))
        ev(port, 'EClass.pc.SetNoGoal(); EClass.pc.stamina.value = EClass.pc.stamina.max; "ok"')
        time.sleep(3)
        awake(port)
        did = use_menu(port, (x, z), "i.act is AI_PracticeDummy")
        if not check(f"il lance l'entrainement ({did})", did.startswith("ok AI_PracticeDummy")):
            return
        if not check("il s'entraine (4 tours)", eventually(lambda: awake(port) and practice(port)[0] >= 4, timeout=60)):
            return
        # the host's copy of the player loses its task, then the player asks to stop
        ev(H, f'{chara(H, uid)}.SetNoGoal(); "ok"')
        ev(port, 'if (EClass.pc.ai.CanManualCancel()) EClass.pc.ai.Cancel(); "ok"')
        t0 = time.time()
        stopped = eventually(lambda: practice(port)[0] < 0, timeout=12)
        check(f"son arret prend alors que l'host n'a plus la tache ({time.time() - t0:.1f} s ; reponse de l'host ou filet de 2 s)", stopped)
        # tied to the act: a task started right after is not stopped by the old request
        time.sleep(3)
        check("pas d'arret en retard sur la suite (il est au repos)", practice(port)[0] < 0)
    finally:
        ev(port, 'if (EClass.pc.ai is AI_PracticeDummy) EClass.pc.SetNoGoal(); "ok"')
        ev(H, f'var t = EClass._map.things.Find(m => m.uid == {dummy}); if (t != null) t.Destroy(); "ok"')


def m4(ctx):
    """l'invite peint sur un chevalet : une tache inconnue de la table va au bout et s'arrete sans l'host"""
    port, uid = ctx["a"]
    clear_conditions(uid)
    easel_id, canvas_id = first_id("Painter"), first_id("Canvas")
    spot = free_next_to(port, uid, 1)
    if not check(f"un chevalet ({easel_id}), une toile ({canvas_id}) et une case libre a cote de l'invite ({spot})",
                 easel_id and canvas_id and spot):
        return
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    x, z = spot.split(",")
    easel = int(ev(H, f'var t = ThingGen.Create("{easel_id}"); EClass._zone.AddCard(t, new Point({x}, {z})).Install(); return t.uid.ToString();'))
    canvas = give(ctx, "a", canvas_id)
    painted = lambda p: ev(p, 'var t = EClass.pc.things.Find(m => m.uid == %d) ?? (EClass.pc.held as Thing); '  # noqa: E731
                              'return t != null && t.c_textureData != null ? "peint" : "vierge";' % canvas)
    running = lambda: ev(port, 'var p = EClass.pc.ai as AI_Paint; return (p != null && p.IsRunning).ToString();') == "True"  # noqa: E731
    # ce que fait AM_Paint une fois la toile choisie
    start = ('var e = EClass._map.things.Find(m => m.uid == %d); var c = EClass.pc.things.Find(m => m.uid == %d); '
             'var p = new AI_Paint { painter = (TraitPainter)e.trait, canvas = (TraitCanvas)c.trait, data = new byte[] { 1, 2, 3, 4 } }; '
             'EClass.pc.SetAI(p); ' % (easel, canvas))
    try:
        if not check("le chevalet est pose chez l'invite",
                     eventually(lambda: ev(port, 'EClass._map.things.Find(m => m.uid == %d) != null ? "oui" : "non"' % easel) == "oui", timeout=15)):
            return
        ev(port, 'EClass.pc.SetNoGoal(); "ok"')
        time.sleep(2)
        awake(port)

        # (b) un arret en pleine peinture : pris tout de suite par le jeu de l'invite
        res = ev(port, start + 'var n = 0; while (!(EClass.pc.ai.Current is AIProgress) && ++n < 30) EClass.pc.ai.Tick(); '
                              'var inProgress = EClass.pc.ai.Current is AIProgress; EClass.pc.ai.Cancel(); '
                              'return inProgress + "|" + p.IsRunning;')
        in_progress, still = res.split("|")
        check(f"l'invite est entre dans la progression de la peinture ({in_progress})", in_progress == "True")
        check(f"son arret prend tout de suite, sans reponse de l'host (la tache tourne encore : {still})", still == "False")
        ev(port, 'EClass.pc.SetNoGoal(); "ok"')
        time.sleep(2)
        check(f"arretee, la peinture n'a rien produit ({painted(port)})", painted(port) == "vierge")

        # (a) puis jusqu'au bout : l'host ne l'arrete pas
        awake(port)
        ev(port, start + '"ok"')
        check("la peinture est lancee", eventually(running, timeout=10))
        check("elle va au bout (avant : arretee par l'host apres un instant)",
              eventually(lambda: not running() and painted(port) == "peint", timeout=60))
        host_copy = ev(H, 'var c = %s; var t = c == null ? null : c.things.Find(m => m.uid == %d); '
                          'return t == null ? "absente" : (t.c_textureData != null ? "peinte" : "vierge");' % (chara(H, uid), canvas))
        log(f"(information, pas une regle) la toile de l'invite chez l'host : {host_copy}")
        refused = [line for line in session_log_lines(t0) if "no matching act" in line and "AI_Paint" in line]
        check(f"l'host n'a pas refuse la peinture (« no matching act » : {len(refused)} fois)", not refused)
    finally:
        ev(port, 'if (EClass.pc.ai is AI_Paint) EClass.pc.SetNoGoal(); "ok"')
        ev(H, 'var c = %s; var t = c == null ? null : c.things.Find(m => m.uid == %d); if (t != null) t.Destroy(); '
              'var e = EClass._map.things.Find(m => m.uid == %d); if (e != null) e.Destroy(); "ok"' % (chara(H, uid), canvas, easel))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [m1, m2, m3, m4, m5]
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
                print(f"    capture {name} : {shot(f'dummy-{step.__name__}-{name}', port)}")
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
