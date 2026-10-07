"""Les mods de la partie chez l'invite, sans abonnement (tranche M2 de PLAN_mods_de_l_host.md), SANS telechargement :
un mod du Workshop que l'invite a sur son disque mais eteint dans sa liste, et que l'host a allume.

    python _tools/mp_test.py
    python _tools/modfetch_suite.py        # 6 a 10 minutes : la fenetre de l'invite est relancee quatre fois

F1  l'invite, relance avec ce mod eteint dans son `loadorder.txt`, ne l'a plus ; case « FetchMods » cochee, il rejoint
F2  son jeu se ferme tout seul ; sur le disque : la liste de la session (marqueur, ce mod allume), sa liste a lui mise
    de cote (ce mod eteint), le ticket de retour
F3  relance : sa liste a lui est revenue dans `loadorder.txt` (ce mod eteint), la copie et le ticket sont partis, ce jeu
    a le mod, et il revient chez l'host tout seul
F4  relance suivante : le mod est de nouveau eteint, rien ne le ramene chez l'host

Ce que le banc ne joue pas comme un joueur :
- aucun telechargement Steam (`SteamUGC.DownloadItem`), aucun lien dans `Package/` : le mod est deja sur le disque ;
- la relance n'est pas faite par Steam : la copie de test demarre sans Steam (`steam_appid.txt`), le mod le voit et
  laisse la relance au joueur, c'est le banc qui relance ;
- le retour se fait par le port local, pas par le salon Steam ni par le depot ;
- seule la copie `_lab/Elin2` est touchee (son `loadorder.txt`, remis a la fin) ; le jeu de l'host ne redemarre pas.
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from mp_test import LAB_EXE, SHOTS, WINDOW, bridge_for, join_client, log, state, wait  # noqa: E402
from travel_suite import LOCALLOW, RESULTS, check, ev  # noqa: E402

H = 27551
LAB = LAB_EXE.parent
ORDER = LAB / "loadorder.txt"
KEPT = LAB / "loadorder.elintogether-player.txt"
BACKUP = LAB / "loadorder.banc.txt"
TICKET = LOCALLOW / "ElinMP" / "modsession.txt"
MARKER = "# elintogether session"
HAS = ('var l = (System.Collections.IEnumerable)HarmonyLib.Traverse.Create(HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.ModList"))'
       '.Property("Here").GetValue(); foreach (var m in l) if (HarmonyLib.Traverse.Create(m).Property("Workshop").GetValue<string>() == "{0}") return "True"; return "False";')
FETCH = ('HarmonyLib.Traverse.Create(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Client")).Property("FetchMods")'
         '.GetValue<BepInEx.Configuration.ConfigEntry<bool>>().Value = {0}; "ok"')
PICK = ('var p = EClass.core.mods.packages.Find(x => x.activated && !x.builtin && x is EMod && ((EMod)x).workshopId != null '
        '&& ((EMod)x).workshopId.Length > 0 && x.id != "dk.elinplugins.elintogether" && !x.id.Contains("yk-framework")); '
        'return p == null ? "" : ((EMod)p).workshopId + "\\t" + p.dirInfo.FullName + "\\t" + p.id + "\\t" + p.title;')


def start():
    client = subprocess.Popen([str(LAB_EXE), *WINDOW, "-logFile", str(SHOTS / "elin2-player.log")], cwd=LAB)
    port = wait(lambda: bridge_for(client.pid), "pont de l'invite", timeout=600)
    wait(lambda: state(port).get("sceneMode") in ("Title", "Zone"), "ecran titre de l'invite", timeout=300)
    time.sleep(10)
    return client, port


def stop(client):
    if client.poll() is None:
        subprocess.run(["taskkill", "/PID", str(client.pid), "/F"], capture_output=True)
        client.wait(timeout=30)
    time.sleep(3)


def lines(path):
    return path.read_text(encoding="utf-8", errors="replace").splitlines() if path.exists() else []


def switch(folder):
    """'1', '0' ou '' (pas de ligne) : ce dossier dans la liste."""
    start_ = folder.replace("\\", "/").lower() + ","
    for line in lines(ORDER):
        if line.replace("\\", "/").lower().startswith(start_):
            return line.split(",")[1]
    return ""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    live = emp.live_ports()
    a = next(h["port"] for h in live if h["port"] != H)
    pid = next(h["pid"] for h in live if h["port"] == a)
    picked = ev(H, PICK)
    if not check(f"un mod du Workshop allume chez l'host ({picked.split(chr(9))[-1]})", bool(picked)):
        return
    workshop, folder, mod_id, title = picked.split("\t")
    check("l'invite l'a aussi, au depart", ev(a, HAS.format(workshop)) == "True")

    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    time.sleep(5)
    shutil.copyfile(ORDER, BACKUP)
    client = None
    try:
        log(f"--- F1 : {title} eteint dans la liste de l'invite, il rejoint avec la case cochee")
        kept = [l for l in lines(ORDER) if not l.replace("\\", "/").lower().startswith(folder.replace("\\", "/").lower() + ",")]
        ORDER.write_text("\n".join(kept + [f"{folder},0,{mod_id}"]) + "\n", encoding="utf-8")
        mine = lines(ORDER)
        client, a = start()
        check("relance : l'invite n'a plus ce mod", ev(a, HAS.format(workshop)) == "False")
        check("sa liste n'a pas change au demarrage", lines(ORDER) == mine)
        ev(a, FETCH.format("true"))
        try:
            emp.call(a, "command", {"cmd": "emp.connect_udp"}, timeout=60)
        except OSError:
            pass

        log("--- F2 : son jeu se ferme tout seul, la liste de la session est sur le disque")
        closed = True
        try:
            client.wait(timeout=120)
        except subprocess.TimeoutExpired:
            closed = False
        check("le jeu de l'invite s'est ferme tout seul", closed)
        time.sleep(2)
        check(f"loadorder.txt est la liste de la session ({(lines(ORDER) or [''])[0]!r})", (lines(ORDER) or [""])[0] == MARKER)
        check(f"ce mod y est allume ({switch(folder)!r})", switch(folder) == "1")
        check("la liste du joueur est mise de cote, telle quelle", lines(KEPT) == mine)
        ticket = lines(TICKET)
        check(f"le ticket dit ou revenir ({ticket[1] if len(ticket) > 1 else ''!r})", len(ticket) > 1 and ticket[1].startswith("port "))
        check("l'host n'a plus que lui-meme", len(state(H).get("players", [])) == 1)

        log("--- F3 : relance : sa liste revient, ce jeu a le mod, il rejoint l'host tout seul")
        client, a = start()
        check("loadorder.txt est de nouveau la liste du joueur", lines(ORDER) == mine)
        check("la copie mise de cote et le ticket sont partis", not KEPT.exists() and not TICKET.exists())
        check("ce jeu a le mod", ev(a, HAS.format(workshop)) == "True")
        back = True
        try:
            wait(lambda: state(a).get("connected") and state(a).get("sceneMode") == "Zone" and len(state(H).get("players", [])) == 2,
                 "retour chez l'host", timeout=240, every=3.0)
        except TimeoutError:
            back = False
        check("il est revenu chez l'host tout seul, sans rien cliquer", back)
        stop(client)
        check("apres sa fermeture : toujours la liste du joueur", lines(ORDER) == mine)

        log("--- F4 : relance suivante : le mod est eteint, rien ne ramene chez l'host")
        client, a = start()
        check("le mod est de nouveau eteint", ev(a, HAS.format(workshop)) == "False")
        time.sleep(20)
        check("il reste a l'ecran titre", state(a).get("sceneMode") == "Title" and not state(a).get("connected"))
        check("la liste du joueur n'a pas change", lines(ORDER) == mine)
    finally:
        if client is not None:
            stop(client)
        for leftover in (KEPT, TICKET):
            if leftover.exists():
                log(f"reste sur le disque, retire par le banc : {leftover.name}")
                leftover.unlink()
        shutil.copyfile(BACKUP, ORDER)
        BACKUP.unlink()
        client, a = start()
        ev(a, FETCH.format("false"))
        join_client(H, a, "invite")

    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
