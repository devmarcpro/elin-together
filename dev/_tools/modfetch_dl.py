"""Les mods de la partie chez l'invite, AVEC un vrai telechargement Steam sans abonnement (tranche M2).

    python _tools/mp_test.py
    python _tools/modfetch_dl.py 3811305522     # numero Workshop d'un mod d'Elin que ce compte ne suit pas

D1  l'host publie sa liste plus ce mod (donnee par le banc) ; l'invite, case « FetchMods » cochee, rejoint : le mod est
    telecharge, le jeu de l'invite se ferme tout seul
D2  sur le disque : le dossier du mod dans le Workshop de Steam, le lien dans `Package/` si le jeu ne charge que les
    abonnements, la liste de la session, la liste du joueur de cote avec ce dossier eteint ; le compte Steam ne suit
    pas un mod de plus
D3  relance : ce jeu a le mod, la liste du joueur est revenue (dossier eteint), et il revient chez l'host
D4  relance suivante : le mod n'est pas charge, le lien est parti

Ce que le banc ne joue pas comme un joueur : l'host n'a pas vraiment ce mod (un mod a actes serait refuse au retour) ;
la relance est faite par le banc, pas par Steam ; retour par le port local. Le dossier telecharge reste dans le
Workshop de Steam : le banc ne supprime rien la-bas.
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
import modfetch_suite as mf  # noqa: E402
from modlist_suite import PAGE, bench, text  # noqa: E402
from mp_test import join_client, log, state, wait  # noqa: E402
from travel_suite import RESULTS, check, ev  # noqa: E402

H = mf.H
SUBS = 'Steamworks.SteamUGC.GetNumSubscribedItems().ToString()'
ROOT = 'return EClass.core.mods.dirWorkshop == null ? "" : EClass.core.mods.dirWorkshop.FullName;'
SYNC = '(EClass.core.config.other.syncMods && !EClass.debug.skipModSync).ToString()'


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    number = sys.argv[1]
    live = emp.live_ports()
    a = next(h["port"] for h in live if h["port"] != H)
    pid = next(h["pid"] for h in live if h["port"] == a)
    root = Path(ev(H, ROOT))
    folder = root / number
    link = mf.LAB / "Package" / ("EmpSession_" + number)
    if not check(f"ce mod n'est pas sur ce PC au depart ({folder})", not folder.exists()):
        return
    subs = ev(H, SUBS)
    import subprocess
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    time.sleep(5)
    shutil.copyfile(mf.ORDER, mf.BACKUP)
    mine = mf.lines(mf.ORDER)
    client = None
    try:
        log(f"--- D1 : l'host publie sa liste plus le mod {number}, l'invite rejoint avec la case cochee")
        bench(text(H, "Text") + f"Mod du banc\n    {PAGE}{number}\n")
        client, a = mf.start()
        sync = ev(a, SYNC)
        log(f"le jeu de l'invite ne charge que les abonnements : {sync} ; abonnements du compte : {subs}")
        ev(a, mf.FETCH.format("true"))
        try:
            emp.call(a, "command", {"cmd": "emp.connect_udp"}, timeout=60)
        except OSError:
            pass
        closed = True
        try:
            client.wait(timeout=900)
        except subprocess.TimeoutExpired:
            closed = False
        check("le jeu de l'invite s'est ferme tout seul", closed)
        time.sleep(2)

        log("--- D2 : ce qui est sur le disque")
        check(f"le mod est dans le Workshop de Steam ({folder})", (folder / "package.xml").exists())
        if sync == "True":
            check(f"un lien vers lui dans Package/ ({link.name})", (link / "package.xml").exists())
        else:
            check("pas de lien : ce jeu charge tout le Workshop", not link.exists())
        check("loadorder.txt est la liste de la session", (mf.lines(mf.ORDER) or [""])[0] == mf.MARKER)
        kept = mf.lines(mf.KEPT)
        hidden = [l for l in kept if l not in mine]
        check(f"la liste du joueur, de cote, est la sienne plus ce mod eteint ({[h[-40:] for h in hidden]})",
              all(l in kept for l in mine) and hidden and all(number in h and h.endswith(",0") for h in hidden))
        check(f"le compte Steam ne suit pas un mod de plus ({subs} -> {ev(H, SUBS)})", ev(H, SUBS) == subs)

        log("--- D3 : relance : ce jeu a le mod et revient chez l'host")
        client, a = mf.start()
        check("ce jeu a le mod", ev(a, mf.HAS.format(number)) == "True")
        check("loadorder.txt est de nouveau la liste du joueur (mod eteint)", mf.lines(mf.ORDER) == kept)
        back = True
        try:
            wait(lambda: state(a).get("connected") and state(a).get("sceneMode") == "Zone" and len(state(H).get("players", [])) == 2,
                 "retour chez l'host", timeout=240, every=3.0)
        except TimeoutError:
            back = False
        check("il est revenu chez l'host tout seul", back)
        mf.stop(client)

        log("--- D4 : relance suivante : le mod n'est pas charge")
        client, a = mf.start()
        check("le mod n'est pas charge", ev(a, mf.HAS.format(number)) == "False")
        check("le lien est parti", not link.exists())
        check("le dossier du Workshop est toujours la (rien n'est supprime)", folder.exists())
        check("la liste du joueur n'a pas change", mf.lines(mf.ORDER) == kept)
    finally:
        bench(None)
        if client is not None:
            mf.stop(client)
        for leftover in (mf.KEPT, mf.TICKET):
            if leftover.exists():
                log(f"reste sur le disque, retire par le banc : {leftover.name}")
                leftover.unlink()
        # la liste d'origine plus le dossier eteint : ce mod ne se charge pas dans la copie de test
        mf.ORDER.write_text("\n".join(mine + [f"{folder},0"]) + "\n", encoding="utf-8")
        mf.BACKUP.unlink()
        client, a = mf.start()
        ev(a, mf.FETCH.format("false"))
        join_client(H, a, "invite")

    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
