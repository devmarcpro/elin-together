"""Le depot de sauvegarde : un dossier garde le monde, le premier arrive le prend et l'heberge.
Test court (host + 1 client a la Prairie). Finit avec les deux jeux dans le monde du depot.

    python _tools/mp_test.py
    python _tools/depot_suite.py      # ~4 minutes

Idee de l'utilisateur (2026-10-03) : un serveur qui est juste la sauvegarde. Premiere forme : un dossier partage.

D1  l'host depose sa sauvegarde dans le depot (avec le logiciel : par-dessus le monde qui s'y trouve, qui est
    garde a part) ; son jeu la recharge depuis le depot : c'est lui qui l'heberge, ses sauvegardes y vont
D2  l'autre joueur, a l'ecran titre, prend le monde du depot (avec le logiciel : par "Join by address", sans
    avoir regle de depot) : il le charge, le depot dit que c'est lui qui heberge
D3  pendant ce temps le premier ne peut pas le prendre (on lui dit qui heberge)
    (avec le logiciel : un mauvais mot de passe est dit comme tel)
D4  celui qui heberge change quelque chose et sauvegarde : le monde du depot change
    (avec le logiciel : le serveur est arrete pendant une sauvegarde ; elle reste sur le PC du joueur, qui la
    renvoie quand il revient : rien n'est perdu)
D5  il quitte : le depot est libre ; le premier joueur le prend a son tour et retrouve le changement (sa copie
    locale a ete effacee avant : le monde vient bien du depot)
D6  il ouvre la session, l'autre le rejoint : les deux jouent dans le monde du depot

    DEPOT_SERVER=1 python _tools/depot_suite.py
Le meme scenario avec Elin Together Server a la place du dossier : l'application (aucun jeu, aucun dossier partage)
garde le monde et le verrou, les jeux lui parlent par son adresse.

    DEPOT_GITHUB=1 python _tools/depot_suite.py        # ~10 minutes
Le meme scenario avec un depot GitHub prive, sans GitHub : la suite lance _tools/fake_github.py (port 55561, ou
DEPOT_GITHUB_PORT) avec un jeton tire au hasard, cree le depot "essai/monde", et regle dans les deux jeux
Depot = github:essai/monde et le mot de passe du depot = le jeton. L'adresse du faux serveur est donnee au jeu par
la variable d'environnement ELINTOGETHER_GITHUB_API (acceptee seulement pour 127.0.0.1) :
  - les fenetres deja ouvertes la recoivent par le pont (Environment.SetEnvironmentVariable) AVANT que GitHubDepot
    ne soit utilise ; la suite relit ensuite le champ _api du jeu et s'arrete s'il n'a pas pris la bonne adresse
    (alors : relancer la fenetre avec la variable dans son environnement, voir G4) ;
  - la fenetre A est fermee puis relancee en G4 : elle est lancee avec la variable dans l'environnement du
    processus, et la suite verifie que le jeu l'a lue, sans l'avoir poussee par le pont.
Les memes etapes D1 a D6 que pour les autres depots (A prend le monde par "Join by address" github:essai/monde,
sans depot regle, comme avec le logiciel ; D3 ajoute une mauvaise cle), plus, propres a GitHub, entre D4 et D5 :
  G1  (dans D4) une sauvegarde part en arriere-plan : GitHub est ralenti (3 s par demande), le jeu repond au pont
      pendant tout l'envoi (nombre de reponses et la plus lente), puis le monde arrive
  G3  GitHub en panne (connexions coupees) pendant une sauvegarde : le jeu continue, le marqueur .unsent existe,
      GitHub n'a rien recu ; quand il revient l'envoi repart, arrive, et le marqueur disparait
  G2  deux sauvegardes a moins de 5 minutes de l'envoi : rien ne part (marqueur present) ; a la sortie vers le
      titre une seule partie, la derniere ; le verrou est rendu ; en reprenant le monde, pas de boite "envoyer ?"
      et les deux sauvegardes y sont
  G4  fermeture du jeu pendant un envoi (Application.Quit pendant que GitHub est lent) : le jeu attend la fin de
      l'envoi, GitHub a la sauvegarde, le verrou est rendu ; la fenetre est relancee, reprend le monde : pas de
      fausse boite "envoyer ?", et la derniere sauvegarde y est (DEPOT_GITHUB_NOQUIT=1 saute G4)
  G5  (a la fin) la cle n'est dans aucun journal : Player.log des deux fenetres (A : avant et apres la relance),
      journaux du mod (ElinMP/Logs), dossier de la sauvegarde ; et, vu du faux GitHub, elle n'est que dans
      l'en-tete Authorization (ni adresse, ni corps, ni autre en-tete, ni depot). Les journaux doivent parler du
      depot (sinon la verification ne prouverait rien)

Ce que ce test ne joue PAS comme un joueur (a lire avant de croire le vert) :
  - pas de vrai GitHub : ni TLS, ni limite de debit, ni la pause d'une seconde entre deux ecritures, ni les 7 s de
    la premiere demande ; les pannes sont celles du faux serveur (connexion coupee, lenteur)
  - le joueur ne tape rien : Depot et mot de passe sont poses par le pont (pas par l'onglet Client Configuration),
    et prendre / mettre / "Join by address" sont les fonctions du mod (SaveDepot.Take, Put, JoinAddress), pas les
    boutons
  - les sauvegardes sont EClass.game.Save(false, true), pas le menu ni la sauvegarde automatique du jeu
  - HeldBy garde 15 s sa derniere reponse : la suite force une nouvelle question (champ _whoAt) pour lire qui
    heberge
  - G3 : l'attente de 5 minutes avant le nouvel envoi est court-circuitee (champ _nextSend remis a 0) ; avec
    DEPOT_GITHUB_FULL_WAIT=1 la suite attend vraiment (jusqu'a 5,5 minutes)
  - G4 : fermeture par Application.Quit(), pas par la croix de la fenetre ; la fermeture brutale pendant un envoi
    (taskkill) n'est PAS jouee : le verrou reste pris 3 minutes (il faudrait l'horloge du faux GitHub) et la
    boite "envoyer ?" y est alors normale ; la fenetre est relancee par la suite, pas par un joueur
  - la cle reste dans le fichier de reglages du mod (c'est voulu) : ce fichier n'est pas fouille
  - le texte exact des boites n'est pas lu sauf "is hosting" (tenu) et "never reached" (boite "envoyer ?")
"""
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import emp  # noqa: E402
from chara_suite import leave  # noqa: E402
from mp_test import (CONTINUE, LAB_EXE, PRISTINE, SAVES, SHOTS, WINDOW, bridge_for, join_client, log, ok,  # noqa: E402
                     shot, state, wait)
from travel_suite import LOCALLOW, RESULTS, check, dismiss_dialogs, ev, eventually, scan_logs  # noqa: E402

H, A = 27551, 27552
DEPOT = SHOTS / "depot"
REMOTE = bool(os.environ.get("DEPOT_SERVER"))
GITHUB = bool(os.environ.get("DEPOT_GITHUB"))
if REMOTE and GITHUB:
    sys.exit("DEPOT_SERVER et DEPOT_GITHUB : l'un ou l'autre")
SERVER_EXE = Path(__file__).resolve().parent.parent / "_release" / "template" / "ElinTogetherServer.exe"
# pas le port habituel (55557) : un vrai serveur de l'utilisateur peut tourner sur cette machine
PORT = "55558"
ADDRESS = "127.0.0.1:" + PORT
FAKE = Path(__file__).resolve().parent / "fake_github.py"
GPORT = int(os.environ.get("DEPOT_GITHUB_PORT", "55561"))  # (pas 55560 : depot_github_test.py)
API = f"http://127.0.0.1:{GPORT}"
GREPO = "essai/monde"
GDEPOT = "github:" + GREPO
# une cle tiree au hasard a chaque passage : si elle est quelque part, c'est que ce passage l'y a mise
TOKEN = "ghp_TESTJETON_" + secrets.token_hex(8)
FALSE_KEY = "ghp_FAUSSE_" + secrets.token_hex(8)
FULL_WAIT = bool(os.environ.get("DEPOT_GITHUB_FULL_WAIT"))
NOQUIT = bool(os.environ.get("DEPOT_GITHUB_NOQUIT"))
SNAP = []  # (nom, octets) : journal d'une fenetre avant sa fermeture (la relance ecrase le fichier)
WORLD = DEPOT / "world.zip" if REMOTE else DEPOT / "world" / "game.txt"
HELD = ('var who = HarmonyLib.AccessTools.Method(' + 'HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.SaveDepot")' +
        ', "HeldBy").Invoke(null, null); return who == null ? "" : who.ToString();')
LOCAL = SAVES / "world_depot"
DEP = 'HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.SaveDepot")'
SET = ('var e = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Client"), "DepotPath").GetValue(null); '
       'HarmonyLib.AccessTools.Property(e.GetType(), "Value").SetValue(e, @"%s"); "ok"')
PASSWORD = SET.replace("DepotPath", "DepotPassword")
CALL = 'HarmonyLib.AccessTools.Method(' + DEP + ', "%s").Invoke(null, null); "ok"'
DIALOG = 'var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); return d == null ? "" : d.textDetail.text;'
JOIN = ('HarmonyLib.AccessTools.Method(HarmonyLib.AccessTools.TypeByName("ElinTogether.Components.TabLobbyBrowser"), '
        '"JoinAddress").Invoke(null, new object[] { "%s" }); "ok"')
# le bouton n du dernier dialogue (0 : "OK" ou "Oui", 1 : "Non"), comme le joueur clique
CLICK = ('var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return "no dialog"; '
         'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(true).Where(x => x.name.StartsWith("ButtonGeneral(Clone)")).ToList(); '
         'if (b.Count <= %d) return "no button"; b[%d].onClick.Invoke(); return "clicked";')
YES = ('var d = EClass.ui.layers.OfType<Dialog>().LastOrDefault(); if (d == null) return "no dialog"; '
       'var b = d.GetComponentsInChildren<UnityEngine.UI.Button>(true).FirstOrDefault(x => x.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t => t.text == Lang.Get("yes"))); '
       'if (b == null) return "no yes button"; b.onClick.Invoke(); return "clicked";')
BUCKETS = 'EClass.pc.things.Flatten().Where(t => t.id == "bucket").Sum(t => t.Num).ToString()'
SAVE_BUCKET = 'EClass.pc.AddThing(ThingGen.Create("bucket")); EClass.game.Save(false, true).ToString()'
# GitHub : l'adresse de test est donnee par l'environnement du processus ; GitHubDepot la lit a sa premiere utilisation
SET_API = 'System.Environment.SetEnvironmentVariable("ELINTOGETHER_GITHUB_API", @"%s"); "ok"'
USED_API = ('(string)HarmonyLib.AccessTools.Field(HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.GitHubDepot"), '
            '"_api").GetValue(null)')
# ce que garde la fenetre d'un passage precedent (la meme fenetre sert a plusieurs passages) : tout repart de zero
RESET = ('var s = ' + DEP + '; var g = HarmonyLib.AccessTools.TypeByName("ElinTogether.Helper.GitHubDepot"); '
         'HarmonyLib.AccessTools.Field(s, "_unsent").SetValue(null, false); '
         'HarmonyLib.AccessTools.Field(s, "_lostTold").SetValue(null, false); '
         'HarmonyLib.AccessTools.Field(s, "_who").SetValue(null, null); '
         'HarmonyLib.AccessTools.Field(s, "_whoAt").SetValue(null, -1000f); '
         'HarmonyLib.AccessTools.Field(s, "_nextSend").SetValue(null, 0f); '
         'HarmonyLib.AccessTools.Field(g, "_repo").SetValue(null, ""); "ok"')
# HeldBy ne reposerait pas sa question avant 15 s : on la lui fait redemander
WHO_NOW = 'HarmonyLib.AccessTools.Field(' + DEP + ', "_whoAt").SetValue(null, -1000f); '
NEXT_SEND0 = 'HarmonyLib.AccessTools.Field(' + DEP + ', "_nextSend").SetValue(null, 0f); "ok"'
QUIT = 'UnityEngine.Application.Quit(); "ok"'


def game_id(port):
    return ev(port, '(EClass.core.IsGameStarted ? Game.id : "")')


def to_title(port):
    emp.call(port, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
    wait(lambda: state(port).get("sceneMode") == "Title", "ecran titre", timeout=60)
    time.sleep(3)


def take(port):
    emp.call(port, "eval", {"code": CALL % "Take"}, timeout=180)
    time.sleep(2)


def loaded(port):
    def cond():
        emp.call(port, "eval", {"code": CONTINUE}, timeout=180)
        return state(port).get("sceneMode") == "Zone" and game_id(port) == "world_depot"
    return cond


def click(port, n=0):
    return ev(port, CLICK % (n, n))


def start_server(*more):
    return subprocess.Popen([str(SERVER_EXE), "--depot", str(DEPOT), "--port", PORT, *more])


def holder(asker):
    """Qui heberge le monde, vu du jeu `asker` ("" si personne, ou si c'est lui)."""
    if GITHUB:
        ev(asker, WHO_NOW + HELD)  # (GitHub est interroge en arriere-plan : la reponse arrive aux images suivantes)
        time.sleep(1.5)
    return ev(asker, HELD)


# ---- le faux GitHub (GitHub seulement)

def ctl(where, **asked):
    request = urllib.request.Request(API + where, json.dumps(asked).encode() if where != "/__state" else None)
    with urllib.request.urlopen(request, timeout=30) as reply:
        return json.loads(reply.read())


def gh_files():
    return ctl("/__state")["repos"][GREPO]["files"]


def gh_worlds():
    """Combien de mondes GitHub a recus (son historique les garde tous)."""
    return len([h for h in ctl("/__state")["repos"][GREPO]["history"] if h["path"] == "world.zip"])


def gh_holder():
    lock = gh_files().get("lock.json")
    return json.loads(lock["text"])["name"] if lock else ""


def gh_requests():
    return len(ctl("/__state")["log"])


def version():
    """Ce qui grandit quand le monde du depot change."""
    return gh_worlds() if GITHUB else WORLD.stat().st_mtime


def world_there():
    return "world.zip" in gh_files() if GITHUB else WORLD.exists()


def depot_for(port):
    # avec le logiciel ou GitHub, l'autre joueur ne regle pas de depot : il tape l'adresse dans "Join by address"
    if REMOTE:
        return "" if port == A else ADDRESS
    if GITHUB:
        return "" if port == A else GDEPOT
    return str(DEPOT)


def probe(port, until, limit=90):
    """Questions au pont pendant qu'un envoi dure : (nombre de reponses, la plus lente en secondes). Un jeu qui
    attend GitHub sur son fil ne repond plus avant la fin de l'envoi."""
    n, worst, end = 0, 0.0, time.time() + limit
    while time.time() < end and not until():
        t = time.time()
        state(port)
        worst = max(worst, time.time() - t)
        n += 1
        time.sleep(0.3)
    return n, worst


def alive(pid):
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"], capture_output=True, text=True).stdout
    return f'"{pid}"' in out


def exe_of(pid):
    out = subprocess.run(["powershell", "-NoProfile", "-Command", f"(Get-Process -Id {pid}).Path"],
                         capture_output=True, text=True).stdout.strip()
    return Path(out) if out else LAB_EXE


def github_outage(unsent):
    log("--- G3")
    worlds = gh_worlds()
    ctl("/__fault", drop=1000)  # (chaque demande est coupee sans reponse)
    ev(A, SAVE_BUCKET)
    check("G3 GitHub en panne pendant une sauvegarde : le marqueur .unsent est la tout de suite", unsent.exists())
    dropped = lambda: len([e for e in ctl("/__state")["log"] if e["status"] == -1])  # noqa: E731
    d0 = dropped()
    ev(A, NEXT_SEND0)  # (l'attente de 5 minutes est court-circuitee, voir l'en-tete)
    check("G3 le jeu tente l'envoi : GitHub coupe la connexion", eventually(lambda: dropped() > d0, timeout=30))
    time.sleep(3)
    check("G3 le jeu continue (il repond, c'est toujours le monde du depot), rien n'est perdu : marqueur present, rien recu",
          state(A).get("sceneMode") == "Zone" and game_id(A) == "world_depot" and unsent.exists() and gh_worlds() == worlds)
    ctl("/__fault")
    if not FULL_WAIT:
        ev(A, NEXT_SEND0)
    check("G3 GitHub revient : l'envoi repart, le monde arrive et le marqueur disparait",
          eventually(lambda: gh_worlds() == worlds + 1 and not unsent.exists(), timeout=330 if FULL_WAIT else 40))


def github_two_saves(unsent, before):
    log("--- G2")
    worlds = gh_worlds()
    ev(A, SAVE_BUCKET)
    ev(A, SAVE_BUCKET)
    time.sleep(15)
    check("G2 deux sauvegardes a moins de 5 minutes du dernier envoi : GitHub ne recoit rien, le marqueur reste",
          gh_worlds() == worlds and unsent.exists())
    to_title(A)
    check("G2 a la sortie vers le titre, une seule partie pour les deux : la derniere",
          eventually(lambda: gh_worlds() == worlds + 1 and not unsent.exists(), timeout=40))
    check("G2 et le verrou est rendu", eventually(lambda: gh_holder() == "", timeout=15))
    take(A)
    said = ev(A, DIALOG)
    wait(loaded(A), "A reprend le monde du depot", timeout=180, every=3.0)
    dismiss_dialogs(A)
    check(f"G2 en reprenant le monde : pas de boite \"envoyer ?\" ({said!r}), et les deux sauvegardes y sont "
          f"({ev(A, BUCKETS)} seaux, {before} au depart)",
          "never reached" not in said and int(ev(A, BUCKETS)) == before + 4)


def github_quit(unsent, before):
    global A
    log("--- G4")
    worlds = gh_worlds()
    n = gh_requests()
    ctl("/__fault", slow=2)
    ev(A, SAVE_BUCKET)  # (premiere sauvegarde depuis la prise du monde : elle part tout de suite)
    check("G4 un envoi est en route (GitHub a recu une demande, pas encore le monde)",
          eventually(lambda: gh_requests() > n and gh_worlds() == worlds, timeout=20))
    pid = next(h["pid"] for h in emp.live_ports() if h["port"] == A)
    exe = exe_of(pid)
    logfile = SHOTS / ("elin2-player.log" if exe.resolve() == LAB_EXE.resolve() else f"depot-{exe.parent.name}-player.log")
    try:
        SNAP.append(("A avant la fermeture", logfile.read_bytes()))
    except OSError:
        pass
    log(f"fermeture de A (pid {pid}) pendant l'envoi")
    try:
        ev(A, QUIT)
    except Exception:  # noqa: BLE001  (le jeu se ferme : la reponse peut ne pas venir)
        pass
    closed = eventually(lambda: not alive(pid), timeout=120)
    check("G4 le jeu se ferme", closed)
    if not closed:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)  # (ce pid-la, pas un autre)
    ctl("/__fault")
    check("G4 il a attendu la fin de l'envoi : GitHub a la sauvegarde, le verrou est rendu, plus de marqueur",
          gh_worlds() == worlds + 1 and gh_holder() == "" and not unsent.exists())

    proc = subprocess.Popen([str(exe), *WINDOW, "-logFile", str(logfile)], cwd=exe.parent,
                            env=dict(os.environ, ELINTOGETHER_GITHUB_API=API))
    log(f"A relance (pid {proc.pid})")
    A = wait(lambda: bridge_for(proc.pid), "pont de A relance", timeout=600)
    wait(lambda: state(A).get("sceneMode") == "Title", "ecran titre de A", timeout=300)
    time.sleep(15)
    used = ev(A, USED_API)  # (premiere utilisation de GitHubDepot dans ce processus : le pont n'a rien pousse)
    check(f"G4 la fenetre relancee a lu l'adresse de test dans l'environnement de son processus ({used})", used == API)
    ev(A, SET % GDEPOT)
    ev(A, PASSWORD % TOKEN)
    take(A)
    said = ev(A, DIALOG)
    log(f"A relance : {said!r}")
    check("G4 au relancement, pas de fausse boite \"envoyer ?\" : l'envoi etait arrive",
          "never reached" not in said and not unsent.exists())
    wait(loaded(A), "A reprend le monde du depot", timeout=180, every=3.0)
    dismiss_dialogs(A)
    check(f"G4 la derniere sauvegarde est dans le monde repris ({ev(A, BUCKETS)} seaux, {before} au depart)",
          int(ev(A, BUCKETS)) == before + 5)


def github_key(fake_state, start_ts):
    log("--- G5")
    keys = [TOKEN.encode(), FALSE_KEY.encode()]
    files = [("host Player.log", LOCALLOW / "Player.log"), ("A Player.log", SHOTS / "elin2-player.log")]
    files += [(f"ElinMP/Logs/{p.name}", p) for p in (LOCALLOW / "ElinMP" / "Logs").glob("*.log")
              if p.stat().st_mtime >= start_ts]
    texts = list(SNAP)
    for name, path in files:
        try:
            texts.append((name, path.read_bytes()))
        except OSError:
            pass
    leaks = [name for name, data in texts if any(k in data for k in keys)]
    size = sum(len(d) for _, d in texts)
    check(f"G5 la cle n'est dans aucun journal ({len(texts)} fichiers, {size // 1024} Ko : {leaks or 'rien trouve'})",
          not leaks)
    check("G5 ces journaux parlent bien du depot GitHub (sinon rien n'est prouve)",
          any(GDEPOT.encode() in data for name, data in texts if name.startswith("ElinMP")))
    saved = [p for p in LOCAL.rglob("*") if p.is_file()] if LOCAL.exists() else []
    check(f"G5 ni dans le dossier de la sauvegarde ({len(saved)} fichiers)",
          not any(k in p.read_bytes() for p in saved for k in keys))
    requests = fake_state.get("log", [])
    check(f"G5 pour le faux GitHub ({len(requests)} demandes) la cle n'est que dans l'en-tete Authorization",
          bool(requests) and not any(e["token_in_url"] or e["token_in_body"] or e["token_in_other_header"]
                                     for e in requests))
    check("G5 ni dans le depot (fichiers et messages de l'historique)",
          bool(fake_state) and TOKEN not in json.dumps(fake_state.get("repos", {})))
    exc = [l for name, data in SNAP for l in data.decode("utf-8", "replace").splitlines()
           if "Exception" in l and "Steamworks is not initialized" not in l]
    if SNAP:
        check(f"A avant sa fermeture : {len(exc)} exception(s)", not exc)


def main():
    global A
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    start_ts = time.time()
    unsent = SAVES / "world_depot.unsent"
    server = fake = None
    fake_state = {}
    try:
        shutil.rmtree(DEPOT, ignore_errors=True)
        shutil.rmtree(LOCAL, ignore_errors=True)
        unsent.unlink(missing_ok=True)
        DEPOT.mkdir(parents=True)
        if REMOTE:
            # la sauvegarde est choisie dans le logiciel (ici par sa ligne de commande, comme le bouton "Mettre
            # cette sauvegarde sur le serveur") : aucun joueur n'a a la deposer
            server = start_server("--import", str(PRISTINE))
            log(f"Elin Together Server lance (pid {server.pid}), depot a {ADDRESS}")
            time.sleep(3)
        if GITHUB:
            fake = subprocess.Popen([sys.executable, str(FAKE), "--port", str(GPORT), "--token", TOKEN])
            log(f"faux GitHub lance (pid {fake.pid}), {API}")
            wait(lambda: ctl("/__state"), "faux GitHub", timeout=20, every=0.5)
            ctl("/__repo", name=GREPO, private=True)
            for port in (H, A):
                # l'adresse d'abord, avant que GitHubDepot soit utilise ; ensuite on relit ce que le jeu en a retenu
                ev(port, SET_API % API)
                used = ev(port, USED_API)
                if used != API:
                    raise RuntimeError(f"le jeu {port} parle a {used} : GitHubDepot etait deja utilise ; relancer la fenetre "
                                       f"avec ELINTOGETHER_GITHUB_API={API} dans son environnement")
                ev(port, RESET)
            log("les deux jeux parlent au faux GitHub")
        for port in (H, A):
            dismiss_dialogs(port)
            ev(port, SET % depot_for(port))
            if GITHUB:
                ev(port, PASSWORD % TOKEN)

        log("--- D1")
        if REMOTE:
            check("la sauvegarde choisie dans le logiciel est le monde du serveur", eventually(WORLD.exists, timeout=15))
        ev(H, CALL % "Put")
        time.sleep(3)
        log(f"l'host : {ev(H, DIALOG)}")
        check("l'host depose sa sauvegarde : le depot contient un monde", world_there())
        if REMOTE:
            check("le monde qui s'y trouvait est garde a part", any(DEPOT.glob("replaced-*.zip")))
        click(H)
        wait(loaded(H), "l'host recharge le monde depuis le depot", timeout=180, every=3.0)
        dismiss_dialogs(H)
        check("son jeu la recharge depuis le depot : c'est le monde du depot qu'il joue", game_id(H) == "world_depot")
        stamp = version()
        ev(H, 'EClass.game.Save(false, true).ToString()')
        check("et ses sauvegardes y vont", eventually(lambda: version() > stamp, timeout=30 if GITHUB else 20))
        to_title(H)
        if GITHUB:
            check("l'host revient au titre : GitHub a sa derniere sauvegarde et le monde est libre",
                  eventually(lambda: gh_holder() == "" and not unsent.exists(), timeout=30))

        log("--- D2")
        to_title(A)
        if REMOTE:
            emp.call(A, "eval", {"code": JOIN % ADDRESS}, timeout=180)
            time.sleep(2)
        elif GITHUB:
            emp.call(A, "eval", {"code": JOIN % GDEPOT}, timeout=180)
            time.sleep(2)
        else:
            take(A)
        wait(loaded(A), "l'autre joueur charge le monde du depot", timeout=180, every=3.0)
        dismiss_dialogs(A)
        check("l'autre joueur prend le monde du depot et le charge", game_id(A) == "world_depot")
        check(f"le depot dit qui heberge ({holder(H)})", eventually(lambda: holder(H) != "", timeout=10))

        log("--- D3")
        to_title(H)
        worlds = gh_worlds() if GITHUB else 0
        take(H)
        said = ev(H, DIALOG)
        log(f"le premier joueur : {said}")
        check("pendant ce temps le premier joueur ne peut pas le prendre : on lui dit qui heberge",
              "is hosting" in said and state(H).get("sceneMode") == "Title")
        dismiss_dialogs(H)
        if GITHUB:
            click(H)
            check("(et GitHub n'a rien recu : le monde n'a pas change)", gh_worlds() == worlds)
            # une mauvaise cle : refus clair, aucune ecriture, et le jeu ne dit pas qu'un joueur heberge
            ev(H, PASSWORD % FALSE_KEY)
            take(H)
            said = ev(H, DIALOG)
            log(f"le premier joueur, mauvaise cle : {said}")
            refused = [e for e in ctl("/__state")["log"] if not e["auth"]]
            check("mauvaise cle : GitHub la refuse (401), le jeu le dit autrement que \"is hosting\", rien n'est ecrit",
                  bool(refused) and all(e["status"] == 401 for e in refused) and said != "" and "is hosting" not in said
                  and gh_worlds() == worlds and state(H).get("sceneMode") == "Title")
            click(H)
            ev(H, PASSWORD % TOKEN)
        if REMOTE:
            # un mauvais mot de passe : on le dit, au lieu de "password heberge le monde"
            ev(H, PASSWORD % "faux")
            check(f"mauvais mot de passe : personne ne s'appelle \"password\" ({holder(H)!r})", holder(H) == "")
            take(H)
            said = ev(H, DIALOG)
            log(f"le premier joueur : {said}")
            check("mauvais mot de passe : le jeu dit que le serveur refuse le mot de passe", "refused" in said.lower())
            dismiss_dialogs(H)
            ev(H, PASSWORD % "")

        log("--- D4")
        before = int(ev(A, BUCKETS))
        stamp = version()
        if GITHUB:
            # G1 : GitHub met 3 s a repondre a chaque demande ; l'envoi (verrou, monde...) dure bien plus de 10 s
            ctl("/__fault", slow=3)
            ev(A, SAVE_BUCKET)
            n, worst = probe(A, lambda: version() > stamp)
            ctl("/__fault")
            check(f"G1 la sauvegarde part en arriere-plan : le jeu a repondu {n} fois pendant l'envoi, "
                  f"la plus lente en {worst:.1f} s", version() > stamp and n >= 8 and worst < 4)
            check("celui qui heberge sauvegarde : le monde du depot change, et le marqueur .unsent disparait",
                  eventually(lambda: not unsent.exists(), timeout=20))
        else:
            ev(A, SAVE_BUCKET)
            check("celui qui heberge sauvegarde : le monde du depot change", eventually(lambda: version() > stamp, timeout=20))
            check("pas de reste de copie dans le depot", not any(DEPOT.glob("*.new")) and not (DEPOT / "world.old").exists())

        if REMOTE:
            # le serveur s'arrete pendant qu'il joue : la sauvegarde suivante n'arrive pas, elle n'est pas perdue
            server.kill()
            server.wait()
            ev(A, SAVE_BUCKET)
            check("serveur arrete : la sauvegarde est notee comme non recue", eventually(unsent.exists, timeout=30))
            to_title(A)
            server = start_server()
            time.sleep(3)
            stamp = WORLD.stat().st_mtime
            emp.call(A, "eval", {"code": JOIN % ADDRESS}, timeout=180)
            time.sleep(2)
            said = ev(A, DIALOG)
            log(f"l'autre joueur : {said}")
            check("a son retour, le jeu propose de l'envoyer", "never reached" in said)
            log(f"clic sur Oui : {emp.call(A, 'eval', {'code': YES}, timeout=180)}")
            wait(loaded(A), "l'autre joueur recharge le monde", timeout=180, every=3.0)
            dismiss_dialogs(A)
            check("elle est envoyee : le monde du serveur change, rien n'est perdu",
                  WORLD.stat().st_mtime > stamp and int(ev(A, BUCKETS)) == before + 2 and not unsent.exists())

        if GITHUB:
            github_outage(unsent)
            github_two_saves(unsent, before)
            if not NOQUIT:
                github_quit(unsent, before)
            else:
                log("G4 saute (DEPOT_GITHUB_NOQUIT) : non jouee")

        buckets = int(ev(A, BUCKETS))
        log("--- D5")
        to_title(A)
        check("il quitte : le depot est libre", eventually(lambda: holder(H) == "", timeout=15 if GITHUB else 10))
        shutil.rmtree(LOCAL, ignore_errors=True)
        take(H)
        wait(loaded(H), "le premier joueur charge le monde du depot", timeout=180, every=3.0)
        dismiss_dialogs(H)
        check(f"le premier joueur le prend a son tour et retrouve le changement ({ev(H, BUCKETS)} seaux, {before} avant)",
              int(ev(H, BUCKETS)) == buckets > before)

        log("--- D6")
        ok(emp.call(H, "command", {"cmd": "emp.add_local"}))
        wait(lambda: state(H)["role"] == "Host", "demarrage du serveur")
        join_client(H, A, "client")
        check("il ouvre la session, l'autre le rejoint : les deux jouent dans le monde du depot",
              eventually(lambda: len(state(H).get("players", [])) == 2 and state(A)["connected"], timeout=30))
    except Exception as ex:  # noqa: BLE001
        check(f"interrompu : {type(ex).__name__}: {str(ex)[:300]}", False)
        for name, port in (("host", H), ("A", A)):
            try:
                print(f"    capture {name} : {shot(f'fail-depot-{name}', port)}")
            except Exception:  # noqa: BLE001
                pass
    finally:
        if server is not None:
            server.kill()
        if fake is not None:
            try:
                fake_state.update(ctl("/__state"))  # (pour G5, avant d'arreter le faux GitHub)
            except Exception:  # noqa: BLE001
                pass
            fake.kill()
            fake.wait()
        for port in (H, A):
            try:
                ev(port, SET % "")
                if GITHUB:
                    ev(port, PASSWORD % "")  # (la cle de test ne reste pas dans les reglages du mod)
            except Exception:  # noqa: BLE001
                pass

    if GITHUB:
        github_key(fake_state, start_ts)
    scan_logs(t0)
    failed = [label for label, good in RESULTS if not good]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} verifications OK")
    for label in failed:
        print(f"  ECHEC : {label}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
