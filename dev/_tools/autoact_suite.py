"""Compatibilite avec le mod AutoAct (Redgeioz, Workshop 3370686923) : l'invite repete une recolte comme l'host.

    python _tools/mp_test.py               # une fois : host + 1 client dans la Prairie
    python _tools/autoact_suite.py         # 2 minutes ; saute tout si AutoAct n'est pas charge dans les deux jeux

A1  l'invite lance une recolte repetee : plusieurs tours de suite, chacun joue par l'host (rouge avant la
    correction : un seul tour puis arret, CharaProgressCompleteDelta remettait le joueur au repos)
A2  pendant ce temps les deux jeux voient la meme carte et le meme sac de l'invite
A3  l'invite arrete (comme un clic) : au repos des deux cotes
A4  temoin : l'host fait la meme chose, l'invite voit la carte et le sac de l'host changer

Ce que le banc ne joue pas comme un joueur : la repetition est lancee par AutoAct.TrySetAutoAct sur la tache que le
jeu propose pour la case (TaskHarvest.TryGetAct), pas par Maj + clic ; l'arret est pc.ai.Cancel() ; seule la recolte
est jouee (creuser, miner, arroser, lire, tondre passent par le meme chemin : CharaTaskRemoteEvent.OnStartUnderFake).
"""
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import log  # noqa: E402
from travel_suite import HOME, RESULTS, both_joined, check, dismiss_dialogs, ev, scan_logs  # noqa: E402
import resync_suite as rs  # noqa: E402

LOADED = ('return (System.AppDomain.CurrentDomain.GetAssemblies().Any(a => a.GetName().Name == "AutoActMod")).ToString();')
START = ('var pc = EClass.pc; Point best = null; for (int r = 1; r <= 9 && best == null; r++) '
         'for (int x = pc.pos.x - r; x <= pc.pos.x + r && best == null; x++) for (int z = pc.pos.z - r; z <= pc.pos.z + r; z++) '
         '{ var p = new Point(x, z); if (p.IsValid && p.HasObj && TaskHarvest.TryGetAct(pc, p) != null) { best = p; break; } } '
         'if (best == null) return "rien a recolter"; var task = TaskHarvest.TryGetAct(pc, best); '
         'var a = AutoActMod.Actions.AutoAct.TrySetAutoAct(pc, task); return a == null ? "refuse" : "ok";')
AI = 'var a = EClass.pc.ai; return a.GetType().Name + "|" + (a.child == null ? "-" : a.child.GetType().Name);'
BAG = '{0}.things.List(t => true, true).Sum(t => t.Num).ToString()'


def chara(uid):
    return f"EClass._map.charas.Find(x => x.uid == {uid})"


def repeat(actor, watcher, who, seconds=30):
    """`actor` lance la recolte repetee ; renvoie (tours joues chez le temoin, sac avant, sac apres des deux cotes)."""
    dismiss_dialogs(actor)
    me = ev(actor, "EClass.pc.uid.ToString()")
    bags = (int(ev(actor, BAG.format("EClass.pc"))), int(ev(watcher, BAG.format(chara(me)))))
    started = ev(actor, START)
    if not check(f"{who} : la recolte repetee demarre ({started})", started == "ok"):
        return None
    rounds, spots, end = 0, set(), time.time() + seconds
    while time.time() < end:
        top, child = ev(actor, AI).split("|")
        if not top.startswith("AutoAct"):
            break
        spots.add(ev(actor, 'EClass.pc.pos.x + "," + EClass.pc.pos.z'))
        time.sleep(1)
    rounds = len(spots)
    still = ev(actor, AI).split("|")[0].startswith("AutoAct")
    after = (int(ev(actor, BAG.format("EClass.pc"))), int(ev(watcher, BAG.format(chara(me)))))
    log(f"{who} : {rounds} cases visitees en {seconds} s, encore en cours : {still}, sac {bags} -> {after}")
    return rounds, still, bags, after


def stop(actor, who):
    ev(actor, 'if (EClass.pc.ai is AutoActMod.Actions.AutoAct a) { a.CancelRetry(); a.Cancel(); } EClass.pc.SetNoGoal(); "ok"')
    return rs.eventually(lambda: ev(actor, AI).split("|")[0] == "NoGoal", timeout=10)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    live = emp.live_ports()
    host = next(h["port"] for h in live if h["role"] == "Host")
    client = next(h["port"] for h in live if h["role"] == "Client")
    both_joined(host, client, HOME)

    if not all(ev(p, LOADED) == "True" for p in (host, client)):
        print("AutoAct n'est pas charge dans les deux jeux : rien a verifier")
        sys.exit(0)

    log("--- A1, A2 : l'invite repete une recolte")
    r = repeat(client, host, "l'invite")
    if r:
        rounds, still, bags, after = r
        check(f"A1 l'invite enchaine les tours ({rounds} cases, encore en cours : {still})", rounds >= 3)
        check(f"A2 le sac de l'invite est le meme dans les deux jeux ({after[0]} / {after[1]})",
              rs.eventually(lambda: ev(client, BAG.format('EClass.pc')) == ev(host, BAG.format(chara(ev(client, 'EClass.pc.uid.ToString()')))), timeout=10))
        check("A3 l'invite arrete : au repos chez lui", stop(client, "l'invite"))
        me = ev(client, "EClass.pc.uid.ToString()")
        check("A3 ... et chez l'host (plus de tache sous son personnage)",
              rs.eventually(lambda: ev(host, f'var a = {chara(me)}.ai; return (a.child == null || !a.child.IsRunning).ToString();') == "True", timeout=15))
        for p in (host, client):
            rs.idle(p)
        check(f"A2 memes nombres de carte dans les deux jeux (host {rs.sums(host)[0]} | invite {rs.sums(client)[0]})",
              rs.eventually(rs.equal, timeout=30))

    log("--- A4 : temoin, l'host repete une recolte")
    r = repeat(host, client, "l'host", seconds=15)
    if r:
        rounds, still, bags, after = r
        check(f"A4 l'host enchaine les tours ({rounds} cases)", rounds >= 2)
        stop(host, "l'host")
        for p in (host, client):
            rs.idle(p)
        check("A4 memes nombres de carte dans les deux jeux", rs.eventually(rs.equal, timeout=30))

    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
