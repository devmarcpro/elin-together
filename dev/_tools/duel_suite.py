"""Duels entre joueurs (conseil 7, PLAN_duels_et_membres.md). Test court, sur des instances deja lancees (host + 1
client, cote a cote a la Prairie).

    python _tools/mp_test.py
    python _tools/duel_suite.py            # ou --only p1

P1  hors duel, un joueur ne peut pas tuer l'autre : la victime a 1 point de vie est frappee par l'autre joueur (le coup
    de melee du jeu, ce que fait Maj + clic) jusqu'a ce que le coup porte ; elle reste en vie, a 0 point de vie au
    plus bas, chez les deux. Dans les deux sens.

Ce que le banc ne joue pas comme un joueur : le coup est l'acte de melee du jeu lance sur la cible (pas la souris) ;
les points de vie de la victime sont baisses par l'host ; les sorts et les projectiles ne sont pas essayes.
"""
import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from death_suite import death_screen  # noqa: E402
from guest_suite import awake, chara, clear_conditions, free_next_to, stand  # noqa: E402
from mp_test import log, shot, state  # noqa: E402
from travel_suite import RESULTS, check, ev, eventually, scan_logs  # noqa: E402

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"a": (A, state(A)["pc"]["uid"]), "h": (H, state(H)["pc"]["uid"])}
    steps = [p1]
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
    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
