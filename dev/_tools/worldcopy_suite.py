"""Copie du monde chez l'invite (conseil 9, etape 3, A' : PLAN_conseil9_verdict.md, notes PLAN_hote_copie_monde.md).
Test court, sur des instances deja lancees (host + 1 client, dans la meme carte).

    python _tools/mp_test.py
    python _tools/worldcopy_suite.py            # ~6 minutes, ou --only c1,c4

C1  apres une sauvegarde automatique de l'host, l'invite a sur son disque une copie complete : memes fichiers, memes
    tailles et memes sommes que le dossier de sauvegarde de l'host ; pendant la reception son jeu n'a jamais gele
    plus de 200 ms (perf_probe) ; une ligne « World copy kept » dans le journal du mod.
C2  a la sauvegarde suivante, l'host n'envoie que les fichiers qui ont change (moins que tout le dossier) ; la
    copie d'avant est toujours la, la nouvelle est juste.
C3  copie interrompue : l'envoi est ralenti, l'invite perd son lien au milieu (emp.cut_link) ; la copie d'avant
    reste la copie, entiere et lisible ; l'invite revient seul et la copie suivante se termine.
C4  rien de ce que l'invite a recu n'a touche une sauvegarde : le dossier Save (hors monde de l'host et copie de
    travail de l'invite) et « Cloud Save » sont tels qu'au depart, et les copies sont rangees ailleurs.
(Joues dans l'ordre C1, C2, C3, C4 : C2 et C3 ont besoin de la copie de C1, C4 compare avec le depart.)

Ce que le banc ne joue pas comme un joueur :
- deux fenetres sur un seul PC : l'envoi passe par un port local, pas par le relais Steam ; le debit reel, la file
  d'envoi de Steam qui se remplit sur une liaison lente et le retard des autres messages ne sont PAS mesures ;
- world_lab est un petit monde (environ 1 Mo) : la duree lue ici ne dit rien d'un monde de 5 ou 20 Mo ;
- l'intervalle de sauvegarde est raccourci par emp.autosave_every (une fenetre du banc ne sauvegarde pas seule) ;
- C3 : la coupure est la perte de paquets simulee de Steam dans le jeu de l'invite, pas un host qui plante ; l'envoi
  est ralenti par WorldCopyBench.PieceSize (Debug) pour que la coupure tombe au milieu ;
- les deux fenetres partagent le dossier Save : « aucune sauvegarde de l'invite touchee » se lit sur tout ce qui
  n'est ni world_lab (le monde de l'host) ni world_emp* (la copie de travail de l'invite, effacee a chaque coupure) ;
- pas joues : la case decochee, un invite parti seul sur une autre carte (il ne recoit rien tant que la ligne de
  ElinNetClientTravel.ShouldReceiveWhileAway n'est pas ajoutee), le mode serveur (-empserver), un deuxieme invite,
  un disque plein, la reprise du monde depuis la copie (etape 4, pas ecrite).
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
import perf_probe  # noqa: E402
from mp_test import SAVES, log, ok, shot, state  # noqa: E402
from travel_suite import (RESULTS, check, dismiss_dialogs, ev, eventually, players, save_mtime, scan_logs,  # noqa: E402
                          session_log_lines)

H, A = 27551, 27552
WORLD = SAVES / "world_lab"
BENCH = "ElinTogether.Net.WorldCopyBench"


def every(seconds):
    log(ok(emp.call(H, "command", {"cmd": f"emp.autosave_every {seconds}"})))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files_of(folder, skip=()):
    """chemin relatif -> (taille, somme) de chaque fichier du dossier."""
    out = {}
    for f in folder.rglob("*"):
        rel = f.relative_to(folder).as_posix()
        if f.is_file() and not any(rel == s or rel.startswith(s + "/") for s in skip):
            out[rel] = (f.stat().st_size, sha(f))
    return out


def host_files():
    # ce que le jeu lui-meme ne met pas dans ses copies de secours : la visite en cours, l'archive du nuage Steam
    return files_of(WORLD, skip=("Temp", "cloud.zip"))


def world_folder():
    """Le dossier ou l'invite range ses copies de ce monde (un par host et par monde)."""
    root = Path(ev(A, f"{BENCH}.Root"))
    found = list(root.glob("*_world_lab")) if root.exists() else []
    # (un dossier par host : celui d'un ancien lancement du banc peut trainer)
    return max(found, key=lambda d: d.stat().st_mtime) if found else root / "_world_lab"


def copies():
    """Les copies entieres, la plus ancienne d'abord (une copie n'a son copy.json qu'une fois verifiee)."""
    return sorted(d for d in world_folder().glob("copy-*") if (d / "copy.json").exists())


def manifest(copy):
    return json.loads((copy / "copy.json").read_text(encoding="utf-8"))


def same_as_host(copy):
    try:
        return files_of(copy, skip=("copy.json",)) == host_files()
    except OSError:
        # une sauvegarde ou une copie en cours d'ecriture
        return False


def whole(copy):
    """La copie est ce que dit son propre copy.json : memes fichiers, tailles et sommes."""
    told = {f["Path"]: (f["Size"], f["Hash"]) for f in manifest(copy)["Files"]}
    return files_of(copy, skip=("copy.json",)) == told


def save_once(timeout=40):
    """Une sauvegarde automatique de l'host, puis plus aucune : le dossier ne bouge plus pendant qu'on compare."""
    before = save_mtime()
    every(5)
    good = eventually(lambda: save_mtime() > before, timeout=timeout)
    every(600)
    time.sleep(1)
    return good


def guest_saves():
    """Tout ce qui est a l'invite dans les dossiers de sauvegarde du jeu : (taille, date) par fichier."""
    out = {}
    for root in (SAVES, SAVES.parent / "Cloud Save"):
        if not root.exists():
            continue
        for f in root.rglob("*"):
            rel = f.relative_to(root.parent).as_posix()
            parts = f.relative_to(root).parts
            # (Save/config.txt est le reglage du jeu, reecrit par le jeu lui-meme : pas une sauvegarde)
            if f.is_file() and len(parts) > 1 and parts[0] != "world_lab" and not parts[0].startswith("world_emp"):
                out[rel] = (f.stat().st_size, f.stat().st_mtime)
    return out


def copy_lines(t0, start):
    out = []
    for line in session_log_lines(t0):
        d = json.loads(line)
        if d.get("@mt", "").startswith(start):
            out.append(d)
    return out


def c1(ctx):
    """apres une sauvegarde de l'host, l'invite a une copie complete, sans gel"""
    dismiss_dialogs(H)
    if not check("depart : deux joueurs dans la partie", players(H) == 2 and players(A) == 2):
        return
    had = copies()[-1:]
    with perf_probe.Probe([A]) as probe:
        if not check("l'host sauvegarde sans geste (intervalle de 5 s)", save_once()):
            return
        t = time.time()
        arrived = eventually(lambda: copies()[-1:] != had and same_as_host(copies()[-1]), timeout=120)
        time.sleep(1)
    res = probe.report()[A]
    if not check(f"l'invite a une copie entiere en {time.time() - t:.0f} s : {world_folder()}", arrived):
        log("etat chez l'invite : " + ev(A, f"{BENCH}.State"))
        return
    copy = copies()[-1]
    theirs, mine = host_files(), files_of(copy, skip=("copy.json",))
    check(f"memes fichiers que le dossier de l'host ({len(theirs)}), memes tailles, memes sommes "
          f"({sum(s for s, _ in theirs.values())} octets)", theirs == mine and len(theirs) > 0)
    m = manifest(copy)
    check(f"copy.json : monde {m['World']}, numero de reprise {m['Handover']}, {len(m['Files'])} fichiers",
          m["World"] == "world_lab" and m["Handover"] == 0 and len(m["Files"]) == len(theirs))
    check(f"le jeu de l'invite n'a pas gele plus de 200 ms pendant la reception (plus long trou : "
          f"{res['max_gap_s'] * 1000:.0f} ms)", res["gaps_over_200ms"] == 0)
    check("une ligne « World copy kept » dans le journal du mod",
          eventually(lambda: copy_lines(ctx["t0"], "World copy kept"), timeout=15))
    check("aucune fenetre ouverte chez l'invite", ev(A, 'EClass.ui.IsActive.ToString()') == "False")


def c2(ctx):
    """la sauvegarde suivante n'envoie que ce qui a change"""
    before = copies()
    if not check("depart : une copie entiere chez l'invite", before):
        return
    asked = len(copy_lines(ctx["t0"], "World copy: {Count} files"))
    if not check("l'host sauvegarde encore", save_once()):
        return
    if not check("une nouvelle copie, juste",
                 eventually(lambda: copies() and copies()[-1] != before[-1] and same_as_host(copies()[-1]), timeout=120)):
        log("etat chez l'invite : " + ev(A, f"{BENCH}.State"))
        return
    total = len(manifest(copies()[-1])["Files"])
    sent = copy_lines(ctx["t0"], "World copy: {Count} files")[asked:]
    count = sent[-1].get("Count") if sent else None
    check(f"l'host n'a envoye que {count} fichier(s) sur {total} ({sent[-1].get('Bytes') if sent else '?'} octets)",
          isinstance(count, int) and 0 < count < total)
    check("la copie d'avant est toujours la, entiere", before[-1] in copies() and whole(before[-1]))
    check("deux copies gardees au plus", len(copies()) <= 2)


def c3(ctx):
    """une copie interrompue ne remplace pas la precedente"""
    before = copies()
    if not check("depart : une copie entiere chez l'invite", before and whole(before[-1])):
        return
    kept = files_of(before[-1])
    incoming = world_folder() / "incoming"
    # 2 Ko par morceau, 4 par seconde : game.txt met plus d'une minute
    ev(H, f'{BENCH}.PieceSize = 2048; "ok"')
    try:
        if not check("l'host sauvegarde", save_once()):
            return
        if not check("la reception commence (un fichier grandit dans « incoming »)",
                     eventually(lambda: any(f.is_file() and f.stat().st_size > 0 for f in incoming.rglob("*")), timeout=40)):
            log("etat chez l'invite : " + ev(A, f"{BENCH}.State"))
            return
        log(ok(emp.call(A, "command", {"cmd": "emp.cut_link 20"})))
        time.sleep(10)
        check("lien coupe au milieu : la copie d'avant est toujours la derniere", copies()[-1] == before[-1])
        check("et elle n'a pas change d'un octet", files_of(before[-1]) == kept and whole(before[-1]))
    finally:
        ev(H, f'{BENCH}.PieceSize = 0; "ok"')
    back = eventually(lambda: state(A).get("sceneMode") == "Zone" and state(A).get("connected") and players(H) == 2,
                      timeout=180)
    if not check("l'invite revient seul dans la partie", back):
        return
    check("pendant tout ce temps la copie d'avant est restee entiere", before[-1] in copies() and whole(before[-1]))
    # l'host a sauvegarde quand il s'est retrouve seul : l'invite revenu recoit la sauvegarde suivante
    save_once()
    done = eventually(lambda: copies()[-1] != before[-1] and same_as_host(copies()[-1]), timeout=120)
    if not check("apres le retour, la copie suivante se termine et elle est juste", done):
        log("etat chez l'invite : " + ev(A, f"{BENCH}.State"))


def c4(ctx):
    """aucune sauvegarde de l'invite n'est touchee"""
    now = guest_saves()
    changed = sorted(k for k in set(now) | set(ctx["saves"]) if now.get(k) != ctx["saves"].get(k))
    check(f"dossiers de sauvegarde du jeu (hors world_lab et world_emp*) comme au depart : {len(now)} fichier(s)"
          + (f", change : {changed[:5]}" if changed else ""), not changed)
    root = Path(ev(A, f"{BENCH}.Root")).resolve()
    outside = all(s.resolve() not in root.parents and s.resolve() != root for s in (SAVES, SAVES.parent / "Cloud Save"))
    check(f"les copies sont rangees hors des sauvegardes : {root}", outside)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    ctx = {"t0": t0, "saves": guest_saves()}
    steps = [c1, c2, c3, c4]
    if a.only:
        steps = [s for s in steps if s.__name__ in a.only.split(",")]
    try:
        for step in steps:
            log(f"--- {step.__name__.upper()} : {step.__doc__}")
            try:
                step(ctx)
            except Exception as ex:  # noqa: BLE001
                check(f"{step.__name__} interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
                for name, port in (("host", H), ("A", A)):
                    try:
                        print(f"    capture {name} : {shot(f'fail-worldcopy-{step.__name__}-{name}', port)}")
                    except Exception:  # noqa: BLE001
                        pass
                break
    finally:
        # le banc repart comme il est venu : pas de sauvegarde toute seule, envoi au vrai rythme, pas de delai de coupure
        for port, call in ((H, ("command", {"cmd": "emp.autosave_every 0"})),
                           (H, ("eval", {"code": f'{BENCH}.PieceSize = 0; "ok"'})),
                           (A, ("command", {"cmd": "emp.link_timeout 0"}))):
            try:
                emp.call(port, *call)
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
