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
D5b (entre D5 et D6) le premier tient le monde mais n'a pas encore ouvert sa partie : l'autre, a l'ecran titre,
    "clique le bouton du depot" : une ligne lui dit de reessayer dans un instant, il reste au titre, rien n'est pris
    (avec le logiciel : le serveur ne dit qu'un nom, c'est le message "X heberge" d'avant)
D6  il ouvre la session, l'autre le rejoint : les deux jouent dans le monde du depot
D7  (dossier et GitHub) REDIRECTION : le verrou dit ou rejoindre celui qui tient le monde ; l'autre quitte, revient a
    l'ecran titre, "clique le bouton du depot" : il rejoint la partie du premier sans invitation, joue SON
    personnage, et le monde du depot n'a toujours qu'un teneur (avec le logiciel : le message "X heberge" d'avant,
    puis il rejoint par le port local comme en D6). Finit comme D6 : H heberge, A l'a rejoint.
    Ce que D5b et D7 ne jouent PAS :
      - le vrai salon Steam : les deux fenetres ont le meme compte Steam ; en build DEBUG celui qui heberge sur le
        port local ecrit ce port dans le verrou ("steam salon port", le port seulement en DEBUG) et l'autre s'y
        connecte (ConnectLocalPort, comme emp.connect_udp). Lobby.ConnectLobby, le salon reserve aux amis, la cle de
        connexion donnee par l'hebergeur : jamais joues ici
      - le bouton : SaveDepot.Take, la fonction qu'il appelle ; son libelle "Join X" n'est pas lu, seulement
        SaveDepot.Joinable, qui le choisit
      - A quitte par ResetSession, pas par le menu ; H ouvre sa partie par emp.add_local, pas par l'ouverture
        automatique
      - le plantage de H (verrou tenu 3 minutes, connexion qui echoue, message, puis verrou perime) n'est pas joue

D8  (depot dossier seulement, joue EN DERNIER de la passe complete, apres P1 et P2 qui ont besoin de l'etat que laisse D7 ;
    seule : DEPOT_ONLY=d8 ou --only d8, sur n'importe quel etat des fenetres : la suite les ramene au titre)
    PRENDRE LE MONDE DU DEPOT OUVRE LA PARTIE TOUT SEUL (demande de l'utilisateur : "quand un joueur prend la sauvegarde
    sur le repo il devrait automatiquement lancer le serveur" ; EmpAutoHost.OpenSession : ouvre si IsSharedWorld OU
    SaveDepot.Holding). Un monde JAMAIS partage (la copie vierge world_lab.pristine : aucune table remote_chara /
    pc_owner / pc_orphan) est mis au depot a la place du monde de la passe, puis pris par A (SaveDepot.Take, ce que
    fait le bouton) avec emp.auto_open 1 (sans quoi une fenetre du banc n'ouvre jamais rien) et AutoHost coche :
      - IsSharedWorld est faux (sinon le test ne prouverait rien : le monde s'ouvrirait pour une autre raison) et
        SaveDepot.Holding est vrai ;
      - apres le chargement, sans emp.add_local ni clic, A est Host, seul, et le verrou du depot dit que sa partie est
        ouverte ;
      - le contraire : A quitte (le depot est libre), n'a plus de depot regle, et recharge ce meme monde comme un
        monde ordinaire (Game.Load "world_depot" : Holding est faux sans depot regle) avec emp.auto_open 1 toujours
        allume : rien ne s'ouvre (role None, aucun joueur).
    Ce que D8 ne joue PAS : les boutons (Take est appele, pas clique ; le chargement par Game.Load, la question "mods
    manquants" passee par CONTINUE comme le fait la suite partout) ; l'ouverture est sur le port local du banc (comme
    D7), pas par Steam : le salon Steam et "amis seulement" ne sont pas joues ; un monde solo vraiment ordinaire
    (une sauvegarde locale d'un autre nom, sans aucun depot) n'est pas joue, c'est le meme monde sans depot regle ;
    le monde jamais partage est la copie vierge posee dans le depot par le banc, pas un monde mis au depot par le
    bouton "Put" d'un joueur ; avec le logiciel (DEPOT_SERVER) et GitHub, non joue (le monde du depot n'y est pas un
    dossier que le banc peut remplacer) : un message le dit. A finit au titre, H aussi : un monde du depot et des
    fenetres au titre, pas l'etat que P1/P2 attendent (les rejouer demande la passe complete).

P1  (depot dossier seulement, a la fin ; seule : DEPOT_ONLY=p1 ou --only p1, sur les fenetres telles que la passe
    complete les laisse : H heberge le monde du depot, A l'a rejoint avec son personnage) ETAT DES LIEUX, sans code
    nouveau dans le mod : quand l'invite prend a son tour le monde du depot et l'heberge, quel personnage joue-t-il ?
    Le sien, ou le personnage principal de la sauvegarde (celui de l'ancien hebergeur) ? Le journal donne les noms,
    uid, positions, or et sacs de H et de A vus des deux jeux avant, puis ce que A trouve apres. Les trois
    verifications finales (A joue son personnage ; il a son seau et ses 123 or ; le personnage de H est toujours la,
    meme sac, meme or, immobile) PEUVENT ETRE ROUGES : c'est la reponse, lire les lignes "avant :" et "apres :".
    Pas joue comme un joueur : le seau et l'or sont donnes par le pont dans le sac de A (AddThing, ModCurrency), pas
    ramasses ni gagnes en jouant ; la sauvegarde, la fin de session (ResetSession) et "prendre le monde" sont les
    fonctions du jeu et du mod, pas les menus ; "ne bouge pas" = deux lectures a 10 s d'ecart sur un jeu au tour par
    tour que personne ne joue : si le personnage de H est celui que A controle, ce test est sans objet ; un seul
    depot dossier, un seul passage, deux fenetres.
    Commande seule : DEPOT_ONLY=p1 python _tools/depot_suite.py (PowerShell : $env:DEPOT_ONLY="p1")
P2  (depot dossier seulement, apres P1 ; seule : DEPOT_ONLY=p2, sur les fenetres telles qu'une passe ou P1 les laisse :
    un jeu heberge le monde du depot, l'autre l'a rejoint) un joueur SANS personnage dans le monde d'un autre le prend :
    il passe par l'ecran de creation du jeu, joue un personnage neuf (sac de depart), le personnage de l'autre attend
    hors de la carte avec son sac et son or, puis l'autre rejoint et retrouve le sien. Ce qui n'est pas joue comme un
    joueur est ecrit en tete de p2() (le "sans personnage" est fabrique par le pont).

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
from mp_test import (CONTINUE, EMBARK, LAB_EXE, PICK_CHARA, PRISTINE, SAVES, SHOTS, WINDOW, bridge_for, join_client,  # noqa: E402
                     log, ok, shot, state, wait)
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
GET = ('var e = HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Client"), "%s").GetValue(null); '
       'return (string)HarmonyLib.AccessTools.Property(e.GetType(), "Value").GetValue(e);')
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
# (tous les sacs des personnages du monde : celui qui reprend le monde joue SON personnage, pas celui qui a pose le seau)
BUCKETS = ('EClass.game.cards.globalCharas.Values.Sum(c => c.things.Flatten().Where(t => t.id == "bucket").Sum(t => t.Num))'
           '.ToString()')
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
# D8 : la case "la partie s'ouvre toute seule" (Server/AutoHost) ; l'etat du monde pour EmpAutoHost.OpenSession
AUTOHOST = ('var e = (BepInEx.Configuration.ConfigEntry<bool>)HarmonyLib.AccessTools.Property('
            'HarmonyLib.AccessTools.TypeByName("ElinTogether.EmpConfig+Server"), "AutoHost").GetValue(null); ')
SHARED = ('((bool)HarmonyLib.AccessTools.Property(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetHost"), '
          '"IsSharedWorld").GetValue(null)).ToString()')
HOLDING = '((bool)HarmonyLib.AccessTools.Property(' + DEP + ', "Holding").GetValue(null)).ToString()'


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
        # un joueur sans personnage dans le monde d'un autre : l'ecran de creation s'ouvre, valide tel quel (P2 le verifie)
        emp.call(port, "eval", {"code": EMBARK}, timeout=180)
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


def lock_now():
    """(qui tient le monde, ou le rejoindre) tels que le depot les garde ; ("", "") avec le logiciel."""
    if GITHUB:
        held = gh_files().get("lock.json")
        held = json.loads(held["text"]) if held else {}
        return held.get("id", ""), held.get("join", "")
    lines = (DEPOT / "host.txt").read_text(encoding="utf-8").splitlines() if not REMOTE and (DEPOT / "host.txt").exists() else []
    return (lines + ["", "", ""])[0], (lines + ["", "", ""])[2]


def redirect_closed():
    log("--- D5b")
    check(f"le verrou dit que la partie du premier n'est pas ouverte ({lock_now()[1]!r})",
          REMOTE or eventually(lambda: lock_now()[1].endswith(" 0"), timeout=15))
    worlds = version()
    take(A)
    said = ev(A, DIALOG)
    log(f"l'autre joueur : {said}")
    check("partie pas encore ouverte : une ligne claire, il reste a l'ecran titre, rien n'est pris",
          ("is hosting" if REMOTE else "not open yet") in said and state(A).get("sceneMode") == "Title"
          and not state(A)["connected"] and version() == worlds)
    click(A)


def redirect():
    log("--- D7")
    uid_a = int(state(A)["pc"]["uid"])
    check(f"la partie ouverte, le verrou dit ou rejoindre celui qui tient le monde ({lock_now()[1]!r})",
          REMOTE or eventually(lambda: lock_now()[1].endswith(" 55556"), timeout=20))
    ev(A, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
    time.sleep(3)
    if state(A).get("sceneMode") != "Title":
        to_title(A)
    wait(lambda: state(A).get("sceneMode") == "Title" and not state(A)["connected"], "A a l'ecran titre", timeout=60)
    eventually(lambda: len(state(H).get("players", [])) == 1, timeout=30)
    who, worlds, held = holder(A), version(), lock_now()[0]
    joinable = ev(A, '((bool)HarmonyLib.AccessTools.Property(' + DEP + ', "Joinable").GetValue(null)).ToString()')
    check(f"a l'ecran titre, le depot dit qui tient le monde ({who}) et le bouton propose de le rejoindre ({joinable})",
          who != "" and (joinable == "True") != REMOTE)
    take(A)
    said = ev(A, DIALOG)
    if REMOTE:
        check("avec le logiciel, pas de redirection : le message d'avant", "is hosting" in said)
        click(A)
        join_client(H, A, "client")
    else:
        check(f"aucun message a lire ({said!r})", "is hosting" not in said and "not open yet" not in said)

        def in_zone():
            if state(A)["sceneMode"] == "Zone" and state(A)["connected"]:
                return True
            emp.call(A, "eval", {"code": PICK_CHARA}, timeout=180)
            emp.call(A, "eval", {"code": EMBARK}, timeout=180)
            return False
        wait(in_zone, "A rejoint la partie de H", timeout=300, every=3.0)
        time.sleep(3)
    check("il a rejoint celui qui tient le monde, sans invitation : deux joueurs chez H",
          eventually(lambda: len(state(H).get("players", [])) == 2 and state(A)["connected"]
                     and state(A)["role"] == "Client", timeout=30))
    check(f"il joue son personnage (uid {state(A)['pc']['uid']}, attendu {uid_a})", int(state(A)["pc"]["uid"]) == uid_a)
    check("le monde du depot n'a qu'un teneur, le meme, et l'autre n'y a rien ecrit",
          state(H)["role"] == "Host" and game_id(H) == "world_depot" and lock_now()[0] == held and version() == worlds
          and (REMOTE or held != ""))


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


# ---- P1 : quel personnage joue l'invite qui prend a son tour le monde du depot ? (etat des lieux, depot dossier)

# un personnage, par son uid, vu par ce jeu : sur la carte, ou a defaut parmi les personnages globaux
CHARA_INFO = ('var u = UID; var place = "carte"; var c = EClass._map.charas.Find(x => x.uid == u); '
              'if (c == null) { c = EClass.game.cards.globalCharas.Find(u); place = "global (pas sur la carte)"; } '
              'if (c == null) return "introuvable"; '
              'return c.Name + " | uid " + c.uid + " | " + place + " | mort=" + c.isDead + " | pos " + '
              '(c.pos == null ? "?" : c.pos.x + "," + c.pos.z) + " | or " + c.GetCurrency() + " | seaux " + '
              'c.things.Flatten().Where(t => t.id == "bucket").Sum(t => t.Num) + " | joueur=" + c.IsPC + " | sac " + '
              'string.Join(",", c.things.Flatten().Select(t => t.id + "x" + t.Num).OrderBy(n => n));')


def info(port, uid):
    """Ce que le jeu `port` sait du personnage `uid` (uid peut etre une expression C#, ex. EClass.pc.uid)."""
    raw = ev(port, CHARA_INFO.replace("UID", str(uid)))
    out = {"raw": raw, "place": raw, "name": "?", "uid": None, "dead": None, "pos": "?", "gold": None, "buckets": None,
           "pc": None, "bag": "?"}
    try:
        f = [x.strip() for x in raw.split(" | ")]
        out.update(name=f[0], uid=int(f[1][4:]), place=f[2], dead=f[3] == "mort=True", pos=f[4][4:],
                   gold=int(f[5][3:]), buckets=int(f[6][6:]), pc=f[7] == "joueur=True", bag=f[8][4:])
    except (IndexError, ValueError):
        pass
    return out


def p1():
    log("--- P1")
    uid_h = int(ev(H, "EClass.pc.uid.ToString()"))
    uid_a = int(state(A)["pc"]["uid"])
    seen = {"H vu de H": info(H, uid_h), "H vu de A": info(A, uid_h), "A vu de A": info(A, uid_a), "A vu de H": info(H, uid_a)}
    for label, it in seen.items():
        log(f"avant : {label} : {it['raw']}")
    check(f"P1 depart : H et A jouent deux personnages distincts (H = {seen['H vu de H']['name']} uid {uid_h}, "
          f"A = {seen['A vu de A']['name']} uid {uid_a})", uid_h != uid_a)
    a0 = seen["A vu de A"]

    # (2) A gagne 123 pieces d'or (sa demande a l'host, comme en jeu) et recoit un seau, pose dans son sac par l'host :
    # un objet cree par le pont dans le jeu de l'invite n'est pas un geste de joueur, l'host ne le verrait pas
    ev(A, 'EClass.pc.ModCurrency(123); "ok"')
    ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {uid_a}); c.AddThing(ThingGen.Create("bucket"), false); "ok"')
    want = lambda it: it["gold"] == a0["gold"] + 123 and it["buckets"] == a0["buckets"] + 1  # noqa: E731
    check(cond=eventually(lambda: want(info(H, uid_a)) and want(info(A, uid_a)), timeout=15),
          label=f"P1 les deux jeux voient le seau et l'or de A ({info(H, uid_a)['raw']})")
    log(f"A apres le seau et l'or : {info(A, uid_a)['raw']}")

    # DEPOT_OLD=1 : un monde d'avant, qui ne sait pas a qui est son personnage local (et qui a pu recevoir de la 0.26.494 un
    # proprietaire faux : DEPOT_OLD=2 l'ecrit, au nom de A). Le jeu doit s'en sortir seul, sans rien demander
    old = os.environ.get("DEPOT_OLD", "")
    if old:
        T = 'var t = HarmonyLib.Traverse.Create(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetHost")); '
        wrong = (f'var who = t.Property("SavedRemoteCharas").GetValue<System.Collections.Generic.Dictionary<ulong, int>>().First(p => p.Value == {uid_a}).Key; '
                 f'd[who] = {uid_h}; ' if old == "2" else '')
        log("monde d'avant : " + ev(H, T + 'var d = t.Property("PcOwners").GetValue<System.Collections.Generic.Dictionary<ulong, int>>(); d.Clear(); d[0UL] = 0; '
                                      + wrong + 'return "pc_owner = " + string.Join(",", d.Select(p => p.Key + ":" + p.Value));'))

    # (3) H sauvegarde et rend le monde ; A est deconnecte
    pre_h = info(H, uid_h)
    stamp = WORLD.stat().st_mtime
    ev(H, 'EClass.game.Save(false, true).ToString()')
    check("P1 H sauvegarde : le monde du depot change", eventually(lambda: WORLD.stat().st_mtime > stamp, timeout=20))
    ev(H, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
    time.sleep(3)
    if state(H).get("sceneMode") != "Title":
        to_title(H)
    if state(A).get("sceneMode") != "Title":
        ev(A, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
        time.sleep(3)
        if state(A).get("sceneMode") != "Title":
            emp.call(A, "eval", {"code": 'EClass.scene.Init(Scene.Mode.Title); "ok"'}, timeout=60)
    wait(lambda: state(A).get("sceneMode") == "Title" and not state(A)["connected"], "A a l'ecran titre", timeout=60)
    check("P1 le monde est rendu (plus de verrou dans le depot)", eventually(lambda: holder(A) == "", timeout=10))

    # (4) A prend le monde du depot et l'heberge
    take(A)
    wait(loaded(A), "A charge le monde du depot", timeout=180, every=3.0)
    # le monde d'un autre : le jeu echange les personnages, sauvegarde et recharge une fois (ElinNetHostHandOver)
    eventually(lambda: state(A).get("sceneMode") == "Zone" and ev(A, "EClass.pc.uid.ToString()") == str(uid_a), timeout=90)
    dismiss_dialogs(A)
    time.sleep(3)

    # (5) ce que A trouve
    me = info(A, "EClass.pc.uid")
    mine = info(A, uid_a)
    theirs = info(A, uid_h)
    time.sleep(10)
    theirs_later = info(A, uid_h)
    log(f"apres : le personnage que A joue (EClass.pc) : {me['raw']}")
    log(f"apres : le personnage de A (uid {uid_a}) : {mine['raw']}")
    log(f"apres : le personnage de H (uid {uid_h}) : {theirs['raw']}")
    log(f"apres : le personnage de H, 10 s plus tard : {theirs_later['raw']}")

    # (6) verifications (un etat des lieux : elles peuvent etre rouges, le journal dit ce qui a ete trouve)
    check(f"P1 A joue son propre personnage : il joue {me['name']} (uid {me['uid']}) ; son personnage etait "
          f"{a0['name']} (uid {uid_a}), celui de H est {pre_h['name']} (uid {uid_h})",
          me["uid"] == uid_a and me["name"] == a0["name"])
    check(f"P1 il a son seau et son or : le personnage qu'il joue a {me['buckets']} seau(x) et {me['gold']} or "
          f"(attendu {a0['buckets'] + 1} et {a0['gold'] + 123}) ; son sac : {me['bag']}",
          me["buckets"] == a0["buckets"] + 1 and me["gold"] == a0["gold"] + 123)
    # comme celui de tout joueur parti : garde dans le monde, hors de la carte, jusqu'a son retour
    same = (theirs["place"] != "carte" and theirs["uid"] == uid_h and theirs["dead"] is False and theirs["bag"] == pre_h["bag"]
            and theirs["gold"] == pre_h["gold"] and theirs["pc"] is False and theirs_later["place"] == theirs["place"])
    check(f"P1 le personnage de H attend dans le monde, hors de la carte, meme sac, meme or, joue par personne : "
          f"avant {pre_h['name']} ({pre_h['place']}, mort={pre_h['dead']}, pos {pre_h['pos']}, or {pre_h['gold']}, "
          f"sac {pre_h['bag']}) ; apres ({theirs['place']}, mort={theirs['dead']}, pos {theirs['pos']}, "
          f"puis {theirs_later['pos']}, or {theirs['gold']}, sac {theirs['bag']}, joue par A : {theirs['pc']})", same)

    # (7) A heberge, H le rejoint : H retrouve SON personnage (pas de creation), avec son sac et son or
    ok(emp.call(A, "command", {"cmd": "emp.add_local"}))
    wait(lambda: state(A)["role"] == "Host", "A demarre le serveur")
    join_client(A, H, "H (invite a son tour)")
    eventually(lambda: len(state(A).get("players", [])) == 2 and state(H)["connected"] and state(H).get("sceneMode") == "Zone", timeout=60)
    back = info(H, "EClass.pc.uid")
    check(f"P1 H rejoint A et retrouve son personnage : il joue {back['name']} (uid {back['uid']}, attendu {uid_h}), "
          f"or {back['gold']} (avant {pre_h['gold']}), sac {back['bag']}",
          back["uid"] == uid_h and back["gold"] == pre_h["gold"] and back["bag"] == pre_h["bag"])
    still = info(A, "EClass.pc.uid")
    check(f"P1 A joue toujours le sien (uid {still['uid']}), et voit H sur sa carte ({info(A, uid_h)['place']})",
          still["uid"] == uid_a and info(A, uid_h)["place"] == "carte")


def p2():
    """Un joueur sans personnage dans le monde d'un autre le prend : il cree le sien, celui de l'autre attend.
    Pas joue comme un joueur :
      - "sans personnage" est fabrique : le banc n'a que deux fenetres et l'invite a deja un personnage dans ce monde ;
        son entree est retiree de la table remote_chara par le pont (Traverse) juste avant la sauvegarde de
        l'hebergeur. Son ancien personnage reste donc dans le monde, a personne (un vrai nouveau n'en a jamais eu),
        et une entree bidon (1:0) est ajoutee pour que la table ne soit jamais vide (piege du plan)
      - l'ecran de creation est valide par l'appel du bouton (EMBARK), personnage tire au hasard tel quel : aucun
        choix de race, de metier, de nom ; fermer l'ecran sans valider (rester au titre) n'est PAS joue
      - sauvegarde, fin de session (ResetSession), "prendre le monde" et heberger sont les fonctions, pas les menus
      - depot dossier seulement ; ni logiciel, ni GitHub, ni sauvegarde locale ordinaire (Game.Load), ni Steam Cloud
      - un seul passage, deux fenetres : pas de troisieme joueur, pas de reprise du monde par un autre pendant l'ecran
    Depart : l'un des deux jeux heberge le monde du depot, l'autre l'a rejoint (ce que laissent la passe ou P1)."""
    log("--- P2")
    hosts = [p for p in (H, A) if game_id(p) == "world_depot" and state(p)["role"] == "Host"
             and len(state(p).get("players", [])) == 2]
    if len(hosts) != 1 or not state(A if hosts[0] == H else H)["connected"]:
        raise RuntimeError("P2 : un des deux jeux doit heberger le monde du depot avec l'autre connecte (deux joueurs) ; "
                           "lancer d'abord la passe complete, qui finit dans cet etat")
    O = hosts[0]              # celui a qui est le monde (son personnage est le personnage local)
    N = A if O == H else H    # le nouveau
    uid_o = int(ev(O, "EClass.pc.uid.ToString()"))
    uid_n = int(state(N)["pc"]["uid"])
    pre_o = info(O, uid_o)
    log(f"avant : l'hebergeur (port {O}) : {pre_o['raw']}")
    log(f"avant : l'ancien personnage du nouveau (port {N}) : {info(O, uid_n)['raw']}")

    # (1) le nouveau n'a plus de personnage dans ce monde ; l'hebergeur sauvegarde aussitot (meme appel : rien ne
    # reecrit la table entre les deux) et rend le monde
    T = 'var t = HarmonyLib.Traverse.Create(HarmonyLib.AccessTools.TypeByName("ElinTogether.Net.ElinNetHost")); '
    DICT = 'GetValue<System.Collections.Generic.Dictionary<ulong, int>>()'
    TABLES = ('"remote_chara = " + string.Join(",", t.Property("SavedRemoteCharas").' + DICT + '.Select(p => p.Key + ":" + p.Value))'
              ' + " | pc_owner = " + string.Join(",", t.Property("PcOwners").' + DICT + '.Select(p => p.Key + ":" + p.Value))'
              ' + " | pc_orphan = " + string.Join(",", t.Property("PcOrphans").GetValue<System.Collections.Generic.Dictionary<int, int>>().Keys)')
    stamp = WORLD.stat().st_mtime
    log("table : " + ev(O, T + 'var d = t.Property("SavedRemoteCharas").' + DICT + '; '
                        f'foreach (var k in d.Where(p => p.Value == {uid_n}).Select(p => p.Key).ToList()) d.Remove(k); d[1UL] = 0; '
                        'var saved = EClass.game.Save(false, true); return ' + TABLES + ' + " | sauvegarde " + saved;'))
    check("P2 l'hebergeur sauvegarde : le monde du depot change", eventually(lambda: WORLD.stat().st_mtime > stamp, timeout=20))
    for port in (O, N):
        if state(port).get("sceneMode") != "Title":
            ev(port, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
            time.sleep(3)
        if state(port).get("sceneMode") != "Title":
            to_title(port)
    wait(lambda: state(N).get("sceneMode") == "Title" and not state(N)["connected"], "le nouveau a l'ecran titre", timeout=60)
    check("P2 le monde est rendu (plus de verrou dans le depot)", eventually(lambda: holder(N) == "", timeout=10))

    # (2) le nouveau prend le monde : le jeu le charge, voit qu'il est a un autre, revient au titre et ouvre l'ecran
    # de creation, sans rien demander
    take(N)

    def creating():
        emp.call(N, "eval", {"code": CONTINUE}, timeout=180)
        return ev(N, '(EClass.ui.GetLayer<LayerEditBio>() != null).ToString()') == "True"
    seen = eventually(creating, timeout=180)
    check(f"P2 le nouveau passe par l'ecran de creation du jeu (scene {state(N).get('sceneMode')})", seen)
    check("P2 pendant l'ecran, le monde du depot n'est tenu par personne", holder(O) == "")
    clicked = emp.call(N, "eval", {"code": EMBARK}, timeout=180).get("result")
    log(f"le nouveau valide la creation : {clicked}")

    # (3) le meme monde est recharge, le personnage adopte, echange avec celui de l'hebergeur, sauvegarde, recharge
    def playing():
        emp.call(N, "eval", {"code": CONTINUE}, timeout=180)
        return (state(N).get("sceneMode") == "Zone" and game_id(N) == "world_depot"
                and ev(N, "EClass.pc.uid.ToString()") != str(uid_o))
    eventually(playing, timeout=240)
    time.sleep(5)
    eventually(playing, timeout=120)
    dismiss_dialogs(N)
    time.sleep(3)

    # (4) ce que le nouveau trouve
    me = info(N, "EClass.pc.uid")
    theirs = info(N, uid_o)
    standing = ev(N, 'EClass.player.fame + "," + EClass.player.karma')
    tables = ev(N, T + 'return ' + TABLES + ';')
    log(f"apres : le personnage que le nouveau joue : {me['raw']}")
    log(f"apres : le personnage de l'hebergeur (uid {uid_o}) : {theirs['raw']}")
    log(f"apres : renommee,karma = {standing} ; {tables}")
    check(f"P2 il a bien vu l'ecran ({clicked}) et joue un personnage NEUF : uid {me['uid']} (hebergeur {uid_o}, son ancien {uid_n})",
          clicked == "embark clicked" and me["uid"] not in (None, uid_o, uid_n) and me["pc"] is True)
    items = [x.rsplit("x", 1)[0] for x in me["bag"].split(",")]
    check(f"P2 avec le sac de depart d'un nouveau joueur (hache comprise), renommee 0 et karma 30 : sac {me['bag']} ; {standing}",
          "axe" in items and len(items) >= 2 and standing == "0,30")
    same = (theirs["place"] != "carte" and theirs["uid"] == uid_o and theirs["dead"] is False and theirs["bag"] == pre_o["bag"]
            and theirs["gold"] == pre_o["gold"] and theirs["pc"] is False)
    check(f"P2 le personnage de l'hebergeur attend hors de la carte, meme sac, meme or : avant ({pre_o['place']}, or {pre_o['gold']}, "
          f"sac {pre_o['bag']}) ; apres ({theirs['place']}, mort={theirs['dead']}, or {theirs['gold']}, sac {theirs['bag']}, "
          f"joue par le nouveau : {theirs['pc']})", same)
    check(f"P2 la sauvegarde sait qui est a qui : le personnage local est au nouveau, celui de l'hebergeur a son nom ({tables})",
          f":{me['uid']} " in tables.split("pc_owner = ")[1]
          and any(e.endswith(f":{uid_o}") for e in tables.split(" | ")[0].split(",")))
    check("P2 le monde du depot est tenu par le nouveau", eventually(lambda: holder(O) != "", timeout=10))

    # (5) le nouveau heberge, l'ancien hebergeur le rejoint : il retrouve SON personnage, sans ecran de creation
    ok(emp.call(N, "command", {"cmd": "emp.add_local"}))
    wait(lambda: state(N)["role"] == "Host", "le nouveau demarre le serveur")
    join_client(N, O, "l'ancien hebergeur (invite a son tour)")
    eventually(lambda: len(state(N).get("players", [])) == 2 and state(O)["connected"] and state(O).get("sceneMode") == "Zone", timeout=60)
    back = info(O, "EClass.pc.uid")
    check(f"P2 l'ancien hebergeur rejoint et retrouve son personnage : il joue {back['name']} (uid {back['uid']}, attendu {uid_o}), "
          f"or {back['gold']} (avant {pre_o['gold']}), sac {back['bag']}",
          back["uid"] == uid_o and back["gold"] == pre_o["gold"] and back["bag"] == pre_o["bag"])
    still = info(N, "EClass.pc.uid")
    check(f"P2 le nouveau joue toujours le sien (uid {still['uid']}), et voit l'autre sur sa carte ({info(N, uid_o)['place']})",
          still["uid"] == me["uid"] and info(N, uid_o)["place"] == "carte")


def d8():
    """Prendre le monde du depot ouvre la partie tout seul ; le meme monde charge sans depot regle n'ouvre rien.
    Voir D8 en tete du fichier (ce qui n'est pas joue comme un joueur y est ecrit)."""
    log("--- D8")
    DEPOT.mkdir(parents=True, exist_ok=True)
    if REMOTE or GITHUB or not PRISTINE.exists():
        log("D8 non jouee : seulement avec le depot dossier et la copie vierge world_lab.pristine du banc")
        return

    # (1) depart : les deux jeux au titre, le depot libre (ce que la passe laisse n'est pas ce dont D8 a besoin)
    for port in (H, A):
        if state(port).get("sceneMode") != "Title":
            ev(port, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
            time.sleep(3)
        if state(port).get("sceneMode") != "Title":
            to_title(port)
    wait(lambda: all(state(p).get("sceneMode") == "Title" and not state(p)["connected"] for p in (H, A)),
         "les deux jeux au titre", timeout=60)
    ev(A, SET % str(DEPOT))
    check("D8 depart : le monde du depot est libre", eventually(lambda: holder(A) == "" and holder(H) == "", timeout=15))

    # (2) un monde jamais partage dans le depot, a la place du monde de la passe ; la copie locale de A est effacee :
    # le monde vient bien du depot
    shutil.rmtree(DEPOT / "world", ignore_errors=True)
    shutil.copytree(PRISTINE, DEPOT / "world")
    shutil.rmtree(LOCAL, ignore_errors=True)

    # (3) A prend le monde, avec la case "s'ouvre toute seule" cochee et la commande du banc qui la rallume
    was_on = ev(A, AUTOHOST + "e.Value.ToString()")
    try:
        ev(A, AUTOHOST + "e.Value = true; e.Value.ToString()")
        log(ok(emp.call(A, "command", {"cmd": "emp.auto_open 1"})))
        take(A)
        wait(loaded(A), "A charge le monde jamais partage du depot", timeout=240, every=3.0)
        dismiss_dialogs(A)
        opened = eventually(lambda: state(A).get("role") == "Host", timeout=60)
        shared, holding = ev(A, SHARED), ev(A, HOLDING)
        check(f"D8 le monde pris est un monde jamais partage (IsSharedWorld {shared}) que le depot tient (Holding {holding}) : "
              "la seule raison d'ouvrir est le depot", shared == "False" and holding == "True")
        s = state(A)
        check(f"D8 apres le chargement, sans emp.add_local ni clic, la partie de A est ouverte : role {s.get('role')}, "
              f"{len(s.get('players', []))} joueur(s), connected {s.get('connected')}",
              opened and s.get("role") == "Host" and len(s.get("players", [])) == 1)
        check(f"D8 le verrou du depot dit ou rejoindre A ({lock_now()[1]!r})",
              eventually(lambda: lock_now()[1].endswith(" 55556"), timeout=30))

        # (4) le contraire : A quitte, n'a plus de depot, recharge ce meme monde comme un monde ordinaire
        ev(A, 'ElinTogether.Net.NetSession.Instance.ResetSession(); "ok"')
        time.sleep(3)
        if state(A).get("sceneMode") != "Title":
            to_title(A)
        check("D8 A quitte : le depot est libre", eventually(lambda: holder(H) == "", timeout=15))
        ev(A, SET % "")
        asked = ev(A, 'Game.TryLoad("world_depot", false, () => Game.Load("world_depot", false)).ToString()')
        if asked != "True":
            log("Game.TryLoad refuse a l'ecran titre : chargement direct par Game.Load")
            ev(A, 'Game.Load("world_depot", false); "ok"')
        wait(loaded(A), "A recharge le meme monde sans depot regle", timeout=240, every=3.0)
        dismiss_dialogs(A)
        time.sleep(15)  # (l'ouverture, si elle devait avoir lieu, vient une image apres le chargement)
        s = state(A)
        holding, shared = ev(A, HOLDING), ev(A, SHARED)
        free = ev(A, '(ElinTogether.Net.NetSession.Instance.Transport == null).ToString()')
        check(f"D8 le meme monde sans depot regle, emp.auto_open toujours allume : rien ne s'ouvre "
              f"(Holding {holding}, IsSharedWorld {shared}, role {s.get('role')}, aucune session {free})",
              holding == "False" and shared == "False" and s.get("role") == "None" and free == "True")
        to_title(A)
    finally:
        for cmd in ("emp.auto_open 0",):
            try:
                emp.call(A, "command", {"cmd": cmd})
            except Exception:  # noqa: BLE001
                pass
        try:
            ev(A, AUTOHOST + f"e.Value = {was_on.lower()}; e.Value.ToString()")
        except Exception:  # noqa: BLE001
            pass


def main():
    global A
    sys.stdout.reconfigure(encoding="utf-8")
    t0 = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    start_ts = time.time()
    unsent = SAVES / "world_depot.unsent"
    # les reglages de depot du joueur (la fenetre host lit son vrai fichier de reglages) : gardes en memoire, jamais
    # affiches, et remis a la fin quoi qu il arrive (le 6 octobre la suite avait efface son depot et sa cle)
    kept = {}
    for port in (H, A):
        try:
            kept[port] = (ev(port, GET % "DepotPath"), ev(port, GET % "DepotPassword"))
        except Exception:  # noqa: BLE001
            pass
    only = os.environ.get("DEPOT_ONLY", "").lower()
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].lower()
    if only not in ("", "p1", "p2", "d8"):
        sys.exit("DEPOT_ONLY / --only : seulement p1, p2 ou d8")
    if only and (REMOTE or GITHUB):
        sys.exit("P1, P2 et D8 se jouent avec le depot dossier (ni DEPOT_SERVER ni DEPOT_GITHUB)")
    server = fake = None
    fake_state = {}
    try:
        if only:
            # les fenetres sont la ou une passe les laisse (un jeu heberge le monde du depot, l'autre l'a rejoint)
            for port in (H, A):
                dismiss_dialogs(port)
                ev(port, SET % str(DEPOT))
            if only == "p1" and not (game_id(H) == "world_depot" and state(H)["role"] == "Host" and len(state(H).get("players", [])) == 2
                    and state(A)["connected"]):
                raise RuntimeError("DEPOT_ONLY=p1 : H doit heberger le monde du depot avec A connecte (deux joueurs) ; "
                                   "lancer d'abord la passe complete, qui finit dans cet etat")
        else:
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
            # s'il n'a pas de personnage dans ce monde, le jeu repasse par le titre et l'ecran de creation, puis recharge
            time.sleep(5)
            wait(loaded(A), "l'autre joueur joue dans le monde du depot", timeout=240, every=3.0)
            dismiss_dialogs(A)
            check("l'autre joueur prend le monde du depot et le charge", game_id(A) == "world_depot")
            check(f"le depot dit qui heberge ({holder(H)})", eventually(lambda: holder(H) != "", timeout=10))

            log("--- D3")
            to_title(H)
            worlds = gh_worlds() if GITHUB else 0
            take(H)
            said = ev(H, DIALOG)
            log(f"le premier joueur : {said}")
            # celui qui tient le monde n'a pas ouvert sa partie (banc) : pas de redirection, on dit qui l'a (D7 joue la redirection)
            check("pendant ce temps le premier joueur ne peut pas le prendre : on lui dit qui a le monde",
                  ("is hosting" in said or "has the world" in said) and state(H).get("sceneMode") == "Title")
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
                # (raccourci du banc : quand celui qui prend le monde y joue son propre personnage, l'echange sauvegarde et
                # envoie deja une fois ; l'envoi suivant attendrait 5 minutes, on remet le delai a zero)
                ev(A, 'HarmonyLib.Traverse.Create(' + DEP + ').Field("_nextSend").SetValue(0f); "ok"')
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

            redirect_closed()

            log("--- D6")
            ok(emp.call(H, "command", {"cmd": "emp.add_local"}))
            wait(lambda: state(H)["role"] == "Host", "demarrage du serveur")
            join_client(H, A, "client")
            check("il ouvre la session, l'autre le rejoint : les deux jouent dans le monde du depot",
                  eventually(lambda: len(state(H).get("players", [])) == 2 and state(A)["connected"], timeout=30))

            redirect()
        if REMOTE or GITHUB:
            log("--- P1, P2 et D8 non jouees : seulement avec le depot dossier")
        else:
            if only in ("", "p1"):
                p1()
            if only in ("", "p2"):
                p2()
            # en dernier : D8 remplace le monde du depot et laisse les deux jeux au titre
            if only in ("", "d8"):
                d8()
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
                path, key = kept.get(port, ("", ""))
                ev(port, SET % path.replace('"', '""'))
                ev(port, PASSWORD % key.replace('"', '""'))
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
