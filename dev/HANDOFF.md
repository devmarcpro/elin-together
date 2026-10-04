# Passation — ElinTogether « indépendance », état au 2026-10-04, 19h20

> **Mise à jour 19h20** : le test `depot_suite` avec `DEPOT_SERVER=1` a été relancé : **20/20**. L'étape « lire `depot_suite-srv4.log` » est donc faite ; la suite commence à la passe large.


À lire en premier par la session suivante. Le détail daté est dans `MODLOG.md` (fin du fichier), le mode d'emploi
dans `DOCUMENTATION.md`, les règles dans `../CLAUDE.md`.

## Où on en est

- Branche `feat/independent-travel`. Dernière version **publiée** : **0.26.390** (préversion
  `independance-0.26.390`). Elle ne contient **pas** les corrections de ce soir. Avec elle, « Join by address » ne
  marche que pour le mode avec Elin ; contournement pour le mode sans Elin : « Client Settings », champ « Depot » =
  `192.168.1.28:55557`, puis « Lobby », prendre le monde.
- **État de cette machine** : la session précédente a remis la version publiée 0.26.390 dans le jeu (dossier
  `Mod_ElinTogether`, venu de `dev/_release/ElinTogether-independance-0.26.390.zip`) pour que l'utilisateur joue
  avec son ami. **Donc : lancer `dev/build.ps1` avant tout test.** Son logiciel serveur à lui est dans
  `Documents\ElinTogether-independance\` (0.26.390, en français) ; son dossier de monde est
  `Documents\ElinTogetherServer` (il y a son vieux monde `world.zip`, la sauvegarde du nuage Steam `world_3`).
- Ce soir : « Join by address » marche avec les deux modes (`018091d`), le logiciel serveur est en anglais
  (`6ad16ab`), le mot de passe faux est dit clairement (`899b221`, **fait**), et les trous du parcours du premier
  joueur sont bouchés (`ab57854` et le commit « the server path », voir `MODLOG.md`, dernière section). Un nouveau
  test existe : `dev/_tools/depot_proto_test.py` (parle au serveur sans le jeu, 10 secondes ; rouge 5/11 puis
  vert 11/11).
- Les trous trouvés puis corrigés (chacun vérifié dans le code) :
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
- Tests sur ce code : `depot_proto_test.py` 11/11 ; `depot_suite` mode dossier 13/13 ; `depot_suite` avec
  `DEPOT_SERVER=1` 19/20 (le seul échec est le compte du test lui-même : des piles d'objets comptées comme une
  seule, corrigé, relancé : résultat à lire dans `dev/_shots/depot_suite-srv4.log`) ; `server_suite` sans
  fenêtre 9/9 (V1–V6, rejoint par le même bouton que le joueur).
- Les changements du jeu (`SaveDepot.cs`, `EmpServer.cs`, `ElinNetHostCompanions.cs`, textes, `depot_suite.py`,
  le logiciel serveur) sont dans le commit « the server path » (fait par la session principale juste après cette
  passation : vérifier avec `git log`).
- **Pas testé (à dire tel quel)** : le mode avec Elin sur une sauvegarde sans base (aucune sauvegarde de ce genre
  sous la main) ; un port UDP déjà pris n'empêche pas la prise réseau de Steam (essayé : le serveur arrive quand
  même à « running »), ce cas n'est donc pas détecté.
- Quêtes « Dummy / Mokyu » : pas le mod. 6 quêtes `dmp_quest_*` d'un autre mod étaient déjà écrites `QuestDummy`
  dans sa sauvegarde du nuage du 2026-10-01. Il repart d'une partie neuve. Question ouverte : quel mod les fournit.
- Elin : EA 23.351 Patch 2, canal Nightly. Si Steam met le jeu à jour : `make_lab.py Elin2 2` (3, 4), sinon le
  client de test est refusé (« invalid version ») sans message clair.
- Un test de jeu tournait au moment de la passation : vérifier qu'aucun Elin ni serveur ne reste ouvert (par
  numéro de processus, jamais un jeu lancé par l'utilisateur).

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
| **Elin Together Server**, le logiciel (`dev/server/`, `ElinTogetherServer.exe`, 26 Ko) : mode sans Elin et mode avec Elin (sans fenêtre) | `7e0a4ea`, `452f89e` | `depot_suite` avec `DEPOT_SERVER=1` 11/11 |
| « Join by address » marche avec les deux serveurs ; texte `emp_ui_timeout` | `018091d` | `depot_suite` `DEPOT_SERVER=1` : rouge 3/4, puis vert 11/11 |
| Logiciel serveur en anglais, documents à jour | `6ad16ab` | — |
| Mot de passe faux dit clairement (« The server refused the password… ») | `899b221` | test du protocole |
| Trous du parcours du premier joueur (monde remplacé, sauvegardes de secours, hébergeur prévenu, messages du deuxième joueur, erreurs du mode avec Elin, confirmations du logiciel) | `ab57854`, puis le commit « the server path » | `depot_proto_test.py` rouge 5/11 → vert 11/11 ; `server_suite` 9/9 ; `depot_suite` voir plus haut |

Dernière passe large (sur le code de 0.26.375) : 24 suites sur 25 vertes. Ce soir, la passe large sur le code
final a été **commencée puis arrêtée exprès** après 3 suites (server 9/9, travel 54/54, depot 11/11), parce que le
code changeait encore. Elle est à refaire (point 2 de « À faire ensuite »).

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
- Travail : skills **ponytail** (la plus petite solution qui marche) et `universal-modder` ; réponses courtes en
  français simple ; **pas plus de deux fenêtres Elin à la fois** sur cette machine (« c'est trop 4 clients »,
  une autre session y travaille sur un serveur privé Dofus) : pas de `trio_suite`.
- Trois dépôts GitHub qu'il veut voir utilisés comme « skills » (état) :
  - `DeusData/codebase-memory-mcp` : index local du code, très utile pour chercher dans le code décompilé du
    jeu. **Il l'installe lui-même** (`powershell -ExecutionPolicy Bypass -File .\install.ps1`, dans
    `Documents\ElinMods`) puis relance Claude Code. La nouvelle session doit regarder si ses outils existent
    (ToolSearch « codebase-memory ») et, s'ils sont là, s'en servir à la place des agents haiku pour chercher dans
    le code : indexer le mod et `Documents\ElinMods\_decomp`.
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
- Les boutons du logiciel ne sont pas joués par un test (le test le lance par sa ligne de commande :
  `--depot <dossier> --port N --import <sauvegarde>`). « Browse… », « Put this save on the server », les trois
  boîtes de confirmation, Start/Stop en mode avec Elin et le message d'erreur n'ont pas été essayés à la main.
- Le mot de passe du dépôt n'est pas chiffré (en clair sur le réseau). Sans Elin, quand l'hébergeur part pendant
  que d'autres jouent, ils reviennent à l'écran titre et l'un d'eux reprend le monde au serveur.
- La passe large sur le code final (voir plus haut). `trio_suite` (4 fenêtres) : verte sur `a76d6a9`, pas rejouée.
- Fluidité : mesurée au banc, pas entre deux PC ; marche touche enfoncée non testée.
- Import d'un personnage : essayé au niveau 1 et avec un vrai personnage de niveau 4, pas avec une grosse sauvegarde.

## À faire ensuite (dans cet ordre, sauf avis contraire de l'utilisateur)

1. **Lire `dev/_shots/depot_suite-srv4.log`** (le test `depot_suite` avec `DEPOT_SERVER=1` relancé après la
   correction de son compte ; attendu 20/20). Avant : `dev/build.ps1`.
2. **Passe large de régression sur le code final** (deux fenêtres, PC libre, 1 à 2 heures ; pas de `trio_suite`,
   ni shared/economy/combat/party qui ouvrent trois fenêtres) :
   `bash _tools/run_all.sh <nom> travel_suite companion_suite server_suite` puis
   `bash _tools/run_short.sh <nom> depot_suite quest_suite chara_suite parity_suite trade_suite build_suite player_suite instance_suite leave_suite transfer_suite death_suite sleep_suite guest_suite recruit_suite compat_suite import_suite time_suite world_suite move_suite`.
3. **Essayer les boutons du logiciel à la main** : Browse…, « Put this save on the server », les trois boîtes de
   confirmation, Start/Stop en mode avec Elin, le message « The server could not start: … ».
4. **Publier une nouvelle version** (`make_release.ps1`, `publish_release.py`) et la mettre dans le jeu de cette
   machine. Mettre à jour les numéros de version dans les documents.
5. **Sa soirée d'essai réelle** : un deuxième joueur qui rejoint par Steam, l'hébergeur qui part, le mode avec
   Elin entre deux PC, Internet (avec mot de passe). Lui demander ce qu'il en dit et quel mod fournit `dmp_quest_*`.
6. Au début de la session : activer Remote Control ; chercher les outils `codebase-memory` ; charger `ponytail:ponytail`.
7. **Décisions qui restent à lui (demander avant)** :
   - le **relais sans coupure** quand l'hébergeur part (gros ; le mode avec Elin évite déjà le problème) ;
   - que faire quand un joueur **meurt sur la carte de l'host**, et quand la **connexion tombe** ;
   - les six inégalités invité/host en attente (`PLAN_egalite_invites.md` : M3, M5, M9, L1, L7, M13) ;
   - retour de l'host sans rechargement (plan B), profil de mods (`PLAN_profil_mods.md`), touche « signaler un
     problème », bot qui rejoue une vraie soirée, faux réseau lent ;
   - **retirer les neuf anciennes préversions** de la page GitHub (0.26.388, .385, .382, .375, .366, .362, .349,
     .337, .309) : jamais sans son accord.
8. Idées notées, pas commencées : le deuxième joueur rejoint l'hébergeur tout seul depuis « Join by address » (le
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
