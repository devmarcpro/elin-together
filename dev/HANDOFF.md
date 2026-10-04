# Passation — ElinTogether « indépendance », état au 2026-10-04, 22h

À lire en premier par la session suivante. Le détail daté est dans `MODLOG.md` (fin du fichier), le mode d'emploi
dans `DOCUMENTATION.md`, les règles dans `../CLAUDE.md`.

## Où on en est

- Branche `feat/independent-travel`. Dernière version **publiée** : **0.26.399** (préversion
  `independance-0.26.399`, https://github.com/devmarcpro/elin-together/releases/tag/independance-0.26.399, zip
  1 122 367 octets). Elle contient les corrections du soir (« Join by address » pour les deux modes, logiciel serveur
  en anglais, trous du parcours du premier joueur, boîte « port déjà pris » en anglais). Elle **ne se connecte pas**
  à la 0.26.390 : l'ami doit installer le même zip.
- **État de cette machine** : le jeu a la version publiée **0.26.399** (dossier `Mod_ElinTogether`, venu de
  `dev/_release/ElinTogether-independance-0.26.399.zip`). **Donc : lancer `dev/build.ps1` avant tout test.** Le
  logiciel serveur de l'utilisateur, dans `Documents\ElinTogether-independance\`, est **encore celui de la 0.26.390
  (en français)** : il doit le remplacer par celui du nouveau zip (pas fait à sa place). Son dossier de monde est
  `Documents\ElinTogetherServer` (vieux monde `world.zip`, la sauvegarde du nuage Steam `world_3`).
- Ce soir : la passe large sur le code final est faite (22 suites, voir plus bas), les boutons du logiciel serveur
  sont essayés par un test (`server_ui_test.ps1`, 15/15 et 6/6), une nouvelle version est publiée.
- Les trous du parcours du premier joueur, corrigés plus tôt (chacun vérifié dans le code) :
  - une partie neuve ne pouvait jamais remplacer le monde du serveur : maintenant oui quand personne n'héberge
    (le joueur devient l'hébergeur), refusé avec le nom de l'hébergeur sinon ;
  - après « Put this save on the server », le jeu gardait sa propre sauvegarde : maintenant le dialogue renvoie
    au titre et recharge le monde depuis le serveur, donc chaque sauvegarde part au serveur ;
  - les trois sauvegardes de secours étaient effacées par quatre sauvegardes automatiques (20 minutes) : un monde
    remplacé est gardé pour de bon (`replaced-<date>.zip`, dans le dossier du serveur), et pas plus d'une
    sauvegarde de secours par 30 minutes ;
  - fermer ou arrêter le logiciel pendant qu'un joueur héberge, ou remplacer un monde depuis le logiciel :
    il demande d'abord ;
  - 300 Mo de mémoire pouvaient être réservés sans mot de passe : le mot de passe est vérifié d'abord ;
  - l'hébergeur n'était jamais prévenu quand ses sauvegardes n'arrivaient plus : maintenant une fenêtre, un
    repère (`Save\world_depot.unsent`), et à la prochaine prise du monde le jeu propose d'envoyer la sauvegarde
    (le monde du serveur est gardé à part) ; si un autre joueur a repris le monde entre-temps, une fenêtre le dit ;
  - deuxième joueur : le message « X héberge » dit de rejoindre par Steam (invitation, ou « Join Game » dans la
    liste d'amis Steam) et d'attendre jusqu'à 3 minutes si l'hébergeur vient de partir ; le message du serveur
    vide dit quoi faire ;
  - mode avec Elin : une sauvegarde sans base, ou une session qui ne s'ouvre pas, fait écrire au jeu sans fenêtre
    `state=error:<raison>` puis quitter, et le logiciel affiche « The server could not start: … » ;
  - bogue trouvé par le test : exception quand l'hébergeur retourne au titre avec un invité encore connecté
    (`TakeCompanionsAlong`), corrigée ;
  - quatre défauts de plus trouvés par une relecture (sonnet), tous corrigés : un monde entier mis de côté à
    chaque sauvegarde après un verrou périmé pendant une mise en veille ; en mode dossier, une sauvegarde tardive
    pouvait détruire le monde plus récent d'un autre joueur (maintenant gardé à côté : `world.replaced-<date>`) ;
    un vieux repère « non envoyé » pouvait revenir sur une partie neuve ; un serveur sans fenêtre bloqué sur une
    question à laquelle personne ne peut répondre.
- **Tests sur le code final** (commit `2dba2fd`, journaux `dev/_shots/<suite>-final.log`) : 22 suites, 19 vertes au
  premier passage. travel 54/54, companion 28/28, server 8/9 puis 9/9, depot (dossier) 13/13, quest 59/59, chara
  11/11, parity 15/15, trade 30/30, build 19/19, player 38/38, instance 32/32, leave 12/13 puis 13/13, transfer 9/9,
  death 11/11, sleep 32/32, guest 216/216, recruit 45/45, compat 5/5, import 25/25, time 11/12 puis 12/12, world
  9/9, move 16/16. Autres : `depot_proto_test.py` 11/11 ; `depot_suite` avec `DEPOT_SERVER=1` 20/20 ;
  `server_ui_test.ps1` `-Part depot` 15/15 et `-Part elin` 6/6. **Non rejouées** : `trio_suite` et
  shared/economy/combat/party (trois ou quatre fenêtres).
- Les trois échecs du premier passage :
  - `server_suite` : `InvalidOperationException: Steamworks is not initialized.` à la fermeture du serveur, après
    la sauvegarde (pile : `Steamworks.SteamInput.Shutdown` ← Heathen ← `Application_quitting`). C'est le jeu
    lui-même, pas le mod ; déjà vu le 2026-10-01. Le compteur d'exceptions des suites (`scan_logs` dans
    `dev/_tools/travel_suite.py`) ignore maintenant cette ligne (`7a4c2d1`) : 9/9.
  - `leave_suite` : l'host est revenu à 1 case de l'invité au lieu d'être loin. Rejouée : 13/13. **Cause non
    établie**, test noté fragile.
  - `time_suite` W3 : faim 31 → 31 après le saut de 5 heures (la date, elle, avait sauté de +300 min). Rejouée :
    12/12 (31 → 32). Marge d'un seul point, faim lue tout de suite : test noté fragile, **cause non établie** (pas
    exclu : heures appliquées chez l'host avec un petit retard).
- Quêtes « Dummy / Mokyu » : pas le mod. 6 quêtes `dmp_quest_*` d'un autre mod étaient déjà écrites `QuestDummy`
  dans sa sauvegarde du nuage du 2026-10-01. Il repart d'une partie neuve. Question ouverte : quel mod les fournit.
- Elin : EA 23.351 Patch 2, canal Nightly. Si Steam met le jeu à jour : `make_lab.py Elin2 2` (3, 4), sinon le
  client de test est refusé (« invalid version ») sans message clair.
- Vérifier qu'aucun Elin ni serveur ne reste ouvert au début (par numéro de processus, jamais un jeu lancé par
  l'utilisateur).
- Outils : `codebase-memory` (MCP) est installé et les deux projets sont indexés (le mod :
  `C-Users-steamdeckwin-Documents-ElinMods-ElinTogether-ElinTogether` ; le code décompilé :
  `C-Users-steamdeckwin-Documents-ElinMods-_decomp`, 54 391 nœuds). `gh` (GitHub CLI) n'est pas installé ; aucune
  issue ni PR ouverte sur le fork.

## Ce qui a été fait depuis la reprise sur cette machine (3 au soir → 4 octobre)

| Sujet | Commit clé | Test |
|---|---|---|
| Cinq corrections de la première vraie partie (habitant recruté, retour de l'host, première fabrication, Somewhat Enhanced Display, sommeil) | publiées en 0.26.349 | passe complète 21/21 |
| Déplacements d'un invité aussi fluides que ceux de l'host (`PlayerClock`), « chacun marche comme en solo » (`PlayerStepPace`), accéléré partagé | `48930ce`, `5584c51`, `6af7ffa` | `move_suite` 18/18 |
| Rejoindre avec un personnage d'une sauvegarde solo, nuage Steam compris (`ImportCharacter`, décochée par défaut) | `6d43567`, puis la correction du nuage | `import_suite` 27/27 |
| Compagnons d'un invité : boule à monstre, monture, achat, brosse (avec son propre charisme), marque de l'animal de Fiama | `7b0c70e`, `d3d5622`, `d7a83ab` | `recruit_suite` 45/45 |
| Une seule date pour le monde (`SharedWorldTime`) | `a76d6a9` | `time_suite` 14/14 |
| Ce que le temps fait au monde n'arrive qu'une fois : météo, impôts, salaires, colis, chance du jour (`WorldKeeper`) | `1b0f5c3`, `856d878` | `world_suite` 11/11 |
| Dépôt de sauvegarde : le monde vit dans un dépôt, le premier arrivé l'héberge (`SaveDepot.cs`, réglage « Depot ») | « a save depot » | `depot_suite` 11/11 |
| Serveur « comme Minecraft » : `Elin.exe -empserver <sauvegarde>`, « Join by address » | « a server like a Minecraft server » | `server_suite` 9/9 |
| **Elin Together Server**, le logiciel (`dev/server/`, `ElinTogetherServer.exe`, 27 Ko) : mode sans Elin et mode avec Elin (sans fenêtre) | `7e0a4ea`, `452f89e` | `depot_suite` avec `DEPOT_SERVER=1` 11/11 |
| « Join by address » marche avec les deux serveurs ; texte `emp_ui_timeout` | `018091d` | `depot_suite` `DEPOT_SERVER=1` : rouge 3/4, puis vert 11/11 |
| Logiciel serveur en anglais, documents à jour | `6ad16ab` | — |
| Mot de passe faux dit clairement (« The server refused the password… ») | `899b221` | test du protocole |
| Trous du parcours du premier joueur (monde remplacé, sauvegardes de secours, hébergeur prévenu, messages du deuxième joueur, erreurs du mode avec Elin, confirmations du logiciel) | `ab57854`, puis le commit « the server path » | `depot_proto_test.py` rouge 5/11 → vert 11/11 ; `server_suite` 9/9 ; `depot_suite` `DEPOT_SERVER=1` 20/20 |
| Passe large sur le code final : 22 suites, 19 vertes au premier passage, les 3 échecs rejoués ou expliqués | `2dba2fd` | journaux `dev/_shots/<suite>-final.log` |
| Faux échec de `server_suite` (erreur de fermeture de Steam Input, dans le jeu) ignoré par le compteur d'exceptions | `7a4c2d1` | `server_suite` 9/9 (`server_suite-final3.log`) |
| Boutons du logiciel serveur essayés par un test (UI Automation + clics postés) ; boîte « port déjà pris » passée en anglais ; exe 27 136 octets | `3c6ca9c` | `server_ui_test.ps1` `-Part depot` 15/15, `-Part elin` 6/6 |
| **Version 0.26.399 publiée** (zip 1 122 367 octets, SHA-256 `7b6bb319…284645`), mise dans le jeu de cette machine | `3c6ca9c` | Release lancé une fois : 0 exception |

## Ce que l'utilisateur veut (dans ses mots)

- But du fork : en jeu, aucune différence entre l'host et les autres joueurs.
- Serveur : « un programme qui héberge une sauvegarde et les joueurs s'y connectent, toute la simulation est
  gérée par les joueurs, un joueur simule une carte ». Puis : « héberger un serveur comme un serveur Minecraft »
  sur son PC de dev, « un vrai logiciel avec une interface, le plus light possible », « pas besoin d'avoir une
  copie d'Elin pour que ça tourne », et « sélectionner la sauvegarde, c'est un peu tout l'intérêt ».
- **Carte blanche (4 octobre, « j'autorise tout »)** : ne pas s'arrêter pour demander, prendre le choix
  recommandé et le noter ; utiliser plusieurs agents en parallèle pour décider et pour relire ; **activer
  Remote Control au début de chaque session** ; **tout ce qu'il voit dans le logiciel serveur doit être en
  anglais** ; **toujours écrire tout ce qui reste à faire**.
- 4 octobre au soir : il a collé un second message « traiter le backlog en autonomie » (une issue = une branche
  `fix/` = une PR, pas de release) ; demandé lequel suivre, il a répondu « Liste HANDOFF, comme avant » : donc la
  branche `feat/independent-travel`, publication comprise. Il a dit oui pour ouvrir deux fenêtres alors que
  `idle.ps1` donnait 0 s (il se servait du PC).
- Il a demandé si un serveur pouvait tourner sur son **NAS Synology** : oui pour le mode sans Elin (voir « À faire
  ensuite », point 4). Idée notée, pas commencée.
- Travail : skills **ponytail** (la plus petite solution qui marche) et `universal-modder` ; réponses courtes en
  français simple ; **pas plus de deux fenêtres Elin à la fois** sur cette machine (« c'est trop 4 clients »,
  une autre session y travaille sur un serveur privé Dofus) : pas de `trio_suite`.
- Trois dépôts GitHub qu'il veut voir utilisés comme « skills » (état) :
  - `DeusData/codebase-memory-mcp` : index local du code, très utile pour chercher dans le code décompilé du
    jeu. **Installé** par lui ; les outils `codebase-memory` sont là et le mod et `Documents\ElinMods\_decomp` sont
    indexés : s'en servir à la place des agents haiku pour chercher dans le code (il a trouvé `Application_quitting`
    dans Heathen en une requête).
  - `trailhq/Graft` : même idée en plus lourd (clé d'API, mesures envoyées par défaut) : jugé en double, **pas
    installé**.
  - `msitarzewski/agency-agents` : 230 fiches de rôles. Les deux lues sont sûres ; la fiche « multijoueur Unity »
    ne convient pas à ce mod. Un relecteur propre au projet, inspiré de sa fiche « Code Reviewer », a été écrit :
    `Documents\ElinMods\.claude\agents\relecteur-elintogether.md` (modèle sonnet) : à utiliser pour les relectures.
  - Claude n'installe jamais un programme tiers lui-même : c'est l'utilisateur qui lance les installateurs.
  - Le serveur `fal` du plugin `universal-modder` n'a pas pu se connecter (jeton refusé, HTTP 401) : à renouveler
    par lui si on veut de l'art ou du son générés.

## Ce qui n'est pas testé (à dire tel quel si on en parle)

- Le mode sans Elin a été joué **une fois entre deux PC sur un réseau local** (connexion, prise du monde), avant
  les corrections de ce soir. Pas essayé : par **Internet**, le mode **avec Elin** entre deux PC, un **deuxième
  joueur** qui rejoint par Steam, **l'hébergeur qui part**. Le nouveau « Join by address » et les nouveaux
  messages n'ont été essayés que par les tests, pas encore par l'utilisateur. Le texte du délai (`emp_ui_timeout`)
  n'est pas testé (seul un build Release l'affiche), ni le figement possible de 5 secondes.
  Ports : TCP 55557 (sans Elin), UDP 55556 (avec Elin), ou un réseau privé (Tailscale, ZeroTier).
- Mode avec Elin : sauvegarde sans base (pas de sauvegarde sous la main) ; port UDP déjà pris (non détecté) ; le
  même compte Steam sur le PC serveur et sur le PC où il joue en même temps (Steam peut refuser). Le test local a
  marché avec serveur et joueur sur le même compte, sur une seule machine.
- Logiciel serveur : **« Browse… » avec un vrai choix de dossier** (le test l'ouvre puis annule) ; le message
  **« The server could not start: … »** (aucune sauvegarde sans base sous la main). Les boutons Oui/Non des boîtes
  et la fenêtre de choix de dossier restent dans la langue de Windows ; si `Depot.Import` échoue sur une erreur
  système, son texte vient aussi de Windows.
- **Deux tests fragiles** (verts au deuxième passage, cause non établie) : `leave_suite` L2 (l'host revenu à 1 case
  de l'invité) et `time_suite` W3 (faim 31 → 31 après le saut de 5 heures, marge d'un point).
- Le mot de passe du dépôt n'est pas chiffré (en clair sur le réseau). Sans Elin, quand l'hébergeur part pendant
  que d'autres jouent, ils reviennent à l'écran titre et l'un d'eux reprend le monde au serveur.
- `trio_suite` (4 fenêtres) : verte sur `a76d6a9`, pas rejouée ; shared/economy/combat/party pas rejouées sur le
  code final.
- Fluidité : mesurée au banc, pas entre deux PC ; marche touche enfoncée non testée.
- Import d'un personnage : essayé au niveau 1 et avec un vrai personnage de niveau 4, pas avec une grosse sauvegarde.
- Un serveur sur NAS : rien d'écrit, rien testé.

## À faire ensuite (dans cet ordre, sauf avis contraire de l'utilisateur)

1. **Sa soirée d'essai réelle avec la 0.26.399** : un deuxième joueur qui rejoint par Steam, l'hébergeur qui part,
   le mode avec Elin entre deux PC, Internet (avec mot de passe). L'ami installe le même zip (lien de la
   préversion `independance-0.26.399`). Il remplace le logiciel serveur de `Documents\ElinTogether-independance\`
   par celui du nouveau zip. Lui demander ce qu'il en dit et quel mod fournit `dmp_quest_*`.
2. **Comprendre les deux tests fragiles** s'ils reviennent : `leave_suite` L2 (position de l'host au retour) et
   `time_suite` W3 (faim lue tout de suite après le saut).
3. Au début de la session : activer Remote Control ; charger `ponytail:ponytail` ; utiliser les outils
   `codebase-memory` (les deux projets sont indexés ; réindexer si le code a changé).
4. **Décisions qui restent à lui (demander avant)** :
   - le **relais sans coupure** quand l'hébergeur part (gros ; le mode avec Elin évite déjà le problème) ;
   - que faire quand un joueur **meurt sur la carte de l'host**, et quand la **connexion tombe** ;
   - les six inégalités invité/host en attente (`PLAN_egalite_invites.md` : M3, M5, M9, L1, L7, M13) ;
   - retour de l'host sans rechargement (plan B), profil de mods (`PLAN_profil_mods.md`), touche « signaler un
     problème », bot qui rejoue une vraie soirée, faux réseau lent ;
   - **un serveur sur son NAS Synology** : (a) tout de suite, sans rien écrire, un dossier partagé du NAS comme
     dépôt (réglage « Depot » = chemin du dossier ; réseau local ou réseau privé comme Tailscale ; pas d'adresse dans
     « Join by address ») ; (b) une **version sans fenêtre du dépôt** pour le NAS (petit script Python d'environ
     150 lignes, ou Docker, testable par `depot_proto_test.py`). Le mode avec Elin ne peut pas tourner sur un NAS ;
   - **retirer les dix anciennes préversions** de la page GitHub (0.26.390, .388, .385, .382, .375, .366, .362,
     .349, .337, .309) : jamais sans son accord.
5. Idées notées, pas commencées : le deuxième joueur rejoint l'hébergeur tout seul depuis « Join by address » (le
   serveur donnerait l'identifiant Steam de l'hébergeur ; il faut deux comptes Steam pour tester, donc pas
   testable sur une machine) ; chiffrer le mot de passe du dépôt (TLS) ; un journal visible dans le logiciel.

## Aide-mémoire

```
powershell -ExecutionPolicy Bypass -File dev\build.ps1            # build de test dans le jeu (jeu fermé)
cd dev && set PYTHONPATH=_tools/pylib
python _tools/mp_test.py                                         # host + 1 client
python _tools/depot_proto_test.py       # le protocole du serveur sans le jeu (10 secondes)
python _tools/depot_suite.py            (DEPOT_SERVER=1 : à travers Elin Together Server)
python _tools/server_suite.py           (SERVER_ARGS="-batchmode -nographics" : serveur sans fenêtre)
powershell -ExecutionPolicy Bypass -File dev\_tools\server_ui_test.ps1 -Part depot   # boutons du logiciel, mode sans Elin (port 55558, dossier %TEMP%\ets-ui-depot)
powershell -ExecutionPolicy Bypass -File dev\_tools\server_ui_test.ps1 -Part elin    # boutons du logiciel, mode avec Elin (world_lab, sans fenêtre)
bash _tools/run_short.sh <nom> quest_suite chara_suite ...        # suites à 2 fenêtres, monde neuf à chaque fois
bash _tools/run_all.sh <nom> travel_suite companion_suite ...     # suites qui lancent leurs fenêtres
powershell -ExecutionPolicy Bypass -File dev\server\build.ps1     # recompile ElinTogetherServer.exe
powershell -ExecutionPolicy Bypass -File dev\make_release.ps1     # zip (contient le logiciel) ; laisse le build Release dans le jeu
python dev/_tools/publish_release.py <version> <commit entier> <note.md> dev/_release/ElinTogether-independance.zip
```

Pièges, à relire dans `MODLOG.md` avant de tomber dedans : l'outil Bash casse `\\n` dans un Python en ligne
(écrire un fichier script) ; dans les dialogues à deux boutons du jeu, « Yes » n'est pas le premier de la
hiérarchie (cliquer par son libellé) ; `Dialog.Ok(texte, action)` lance l'action à **toute** fermeture du
dialogue ; des objets du même genre s'empilent (compter avec `Sum(t => t.Num)`) ; arrêter une tâche de fond
(`run_short.sh`, `run_all.sh`) ne ferme ni les scripts ni les jeux : les fermer par numéro de processus ;
`Player.log` et `_shots/elin2-player.log` sont écrasés par le test suivant ; `mp_test.py` lancé juste après
`run_short.sh` échoue (« Elin tourne déjà ») ; `EClass.pc` lève une exception sans jeu ; plusieurs
`[HarmonyPatch]` sur une méthode ne font qu'une cible ; `move_suite` est sensible à la souris et au clavier.

Pièges de `server_ui_test.ps1` : en PowerShell `$T` et `$t` sont la même variable ; `return` dans `ForEach-Object`
ne sort pas de la fonction ; les contrôles WinForms sont vus comme `ControlType.Pane` (filtrer par ClassName
`*BUTTON*`, `*COMBOBOX*`, `*LISTBOX*`), ceux des boîtes par ClassName `Button` ; `InvokePattern.Invoke` bloquerait
sur une boîte modale : les clics sont postés (`PostMessage BM_CLICK`). Le test n'utilise jamais le dossier
`Documents\ElinTogetherServer` de l'utilisateur. Le compteur d'exceptions des suites (`scan_logs`) ignore l'erreur
de fermeture « Steamworks is not initialized » : elle vient du jeu (Heathen), pas du mod.
