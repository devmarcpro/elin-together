# Et si l'host part ? Les faits pour le conseil (6 octobre 2026)

Demande de l'utilisateur (il joue invité) : « le joueur 1 se déconnecte, aucun problème ; il se reconnecte pendant que le joueur 2 joue, aucun problème », puis
« si l'host se déconnecte, est-ce qu'un invité devient l'host ? ». Réponse d'aujourd'hui : **non**. Méthode : lecture seule du code, des plans et du journal ; rien
lancé, rien compilé. Chemins sous `ElinTogether/ElinTogether/` sauf mention ; `D` = `dev/`. Ce qui n'est pas prouvé est marqué « non vérifié » ; « estimé » = pas mesuré.

## Les faits en neuf lignes

1. Quand le lien avec l'host tombe, le jeu de l'invité est **détruit** (`game.Kill`), sa copie des cartes est **effacée**, il retourne au titre et quitte le salon
   Steam (`Net/NetSession.cs:135-183`). Rien n'est gardé. Aucun code ne se reconnecte, ni ne reprend le monde tout seul (B1, B4, `PLAN_sans_friction.md:113-130`).
2. L'invité n'a **pas** un monde jouable : une copie du `Game` reçue à la connexion, quelques changements, et les fichiers des **seules cartes visitées**. Une carte
   sans fichier est **régénérée** par le jeu (`D/_decomp/Elin/Zone.cs:664-668`). Les registres par joueur (`remote_chara`, `player_standing`, `personal_quests`,
   `pc_owner`...) sont chez l'host seulement.
3. L'host n'enregistre pas le monde à intervalle régulier (sauf en mode `-empserver`). Un plantage perd tout depuis sa dernière sauvegarde, invités compris.
4. Avec dépôt, un invité peut reprendre le monde **à la main** après un départ propre ; après un plantage, attente de jusqu'à 3 minutes (verrou).
5. Sans dépôt (partie Steam simple) : personne d'autre que l'host ne peut reprendre le monde ; aucune copie complète ailleurs.
6. Le mod **connaît** la migration de propriétaire d'un salon Steam mais la traite comme une erreur : il se déconnecte (`Net/Steam/SteamNetLobby/SteamNetLobbyManager.cs:380-384`).
7. Un invité est déjà « host d'une carte » (voyage indépendant), mais sous l'autorité de l'host du monde : si celui-ci disparaît, la carte tenue disparaît avec lui.
8. Un invité qui revient trouve l'écran « Who do you want to play? » à chaque connexion (défaut, `Emp/EmpConfig.cs:231-237`) : un retour automatique s'y arrêterait.
9. Aucun test ne couvre « l'host disparaît » : `leave_suite.py` teste l'host qui **change de carte**, pas qui quitte la session.

---

## 1. Ce qui se passe aujourd'hui

### 1.0 Le mécanisme commun

- **Détection côté invité.** Seule une fermeture annoncée est traitée (`ClosedByPeer`, `Net/Steam/SteamNetManager/SteamNetManager.cs:236-243`). Plantage ou coupure : l'invité voit
  seulement `IsConnected` devenir faux (`Net/Steam/SteamNetPeer/SteamNetPeer.cs:87-91`) et attend `Timeout` = 15 s (`Net/Client/ElinNetClient.cs:57-63`, `EmpConfig.cs:29-37`).
  **Ce délai n'existe qu'en Release** (`#if !DEBUG`) : au banc (build de test) l'invité attend sans fin. Avant, Steam met son propre délai (10 s par défaut : non vérifié).
- **Fin de session côté invité** : `OnPeerDisconnected` (`ElinNetClient.cs:172-193`) -> `ResetSession` (`NetSession.cs:160-183`) -> `RemoveComponent` (`:135-158` : `game.Kill`, titre,
  **session de zone détruite** `:137`) ; `LeaveLobby` (`:173`) ; `InvalidateTemp` (`:175`, `Helper/ResourceFetch.cs:35-55` : efface `world_emp`) ; message « Disconnected from host ».
  `Patches/GameSaveLoad.cs:36-46` refait `ResetSession` à chaque chargement et retour au titre.
- **Côté host** : `DisconnectInactive` (`Net/Host/ElinNetHost.cs:108-141`) : lien mort + plus de 25 images (`:129`, durée : non vérifié) -> `OnPeerDisconnected` (`:164-204`) : le personnage
  de l'invité quitte la carte mais **reste dans la sauvegarde** (`remote_chara`). Voyageur seul : on garde son dernier point de sauvegarde et le jeu est sauvé (`Net/Host/ElinNetHostTravel.cs:1485-1514`).
- **Rejoindre** : invitation Steam ou « Join Game » (`SteamNetLobbyManager.cs:269-289`) ; la liste n'est pas cliquable (B2). L'host renvoie toute la copie du `Game` puis la carte
  (`ElinNetHostPlayerManager.cs:210-236`). L'écran de choix du personnage s'ouvre si le joueur a déjà un personnage (`:81-104`, `Net/Client/ElinNetClientPlayer.cs:29-63`) ; le fermer déconnecte.

### 1.1 L'host quitte proprement (retour au titre, ou ferme le jeu)

Côté host : le titre détruit le composant, qui ferme chaque lien avec `emp_dc_host_shutdown` (`Net/Base/ElinNetBase.cs:74-86`, `SteamNetManager.cs:109-117`) ; fermer la fenêtre :
`Net/NetShutdown.cs:16-39`. Le jeu n'enregistre pas tout seul (la boîte « retour au titre » du jeu le fait si on répond oui, `Game.cs:1032-1040` décompilé).

| | Avec dépôt (dossier, serveur, GitHub) | Sans dépôt (Steam simple) |
|---|---|---|
| Invité | Fermeture reçue tout de suite : message, jeu détruit, titre, salon quitté. | Idem. |
| Dépôt | GitHub : dernier envoi puis `RELEASE`, le jeu attend jusqu'à 30 s à la fermeture (`Helper/SaveDepot.cs:107-119`, `:691-714`). **Dossier et serveur : verrou rendu seulement au retour au titre** (`:691-714`) ; fermer la fenêtre ne le rend pas (`OnQuit` ne vaut que pour GitHub, `:110`) : 3 minutes (`:37`). Lu, non joué. | Aucun. |
| Ensuite | L'invité clique « Take the world » (`Components/Tabs/TabLobbyBrowser.cs:22-29`, `SaveDepot.Take` `:164-223`) : téléchargement, dézippage, chargement. **Prendre le monde d'un autre le charge deux fois** (chargement, échange des personnages, sauvegarde, rechargement, `ElinNetHostPlayerManager.cs:342-360`). Puis « Start Server » à la main (`TabLobbyBrowser.cs:48-50`, B8) : **nouveau salon** (`ElinNetHost.cs:34`), l'autre invité doit être ré-invité. | Rien à prendre : l'invité reste au titre, le monde est sur le PC de l'host. |
| Perdu | Rien de ce que l'host a sauvegardé. | Idem. |

### 1.2 L'host plante ou perd Internet

- **Invité** : rien n'est annoncé. Steam déclare le lien mort (~10 s, non vérifié) puis 15 s en Release : environ 25 s (estimé) de jeu sans réponse, puis titre. Au banc : jamais de fin.
  S'il tenait une carte avec d'autres invités : sa session de zone est détruite avec le reste ; ses invités attendent une passation qui ne viendra pas
  (`ElinNetClientTravel.cs:385-415`), puis leur lien avec l'host tombe aussi.
- **Dépôt** : plus de battement (60 s, `SaveDepot.cs:38`, `:669-689`) ; verrou valable 3 minutes (`:37`). Un invité qui clique avant lit « X héberge le monde » (`:164-172`). **Attente de 3 à 4 minutes**
  (estimé). Le monde du dépôt est le dernier envoi : pour GitHub au plus un toutes les 5 minutes (`:42`, `:676`) ; la sauvegarde la plus récente de l'host reste sur son PC (`world_depot.unsent`, `:628-636`).
- **Sans dépôt** : tout est sur le PC de l'host ; rien à reprendre.
- **Perdu** : tout depuis la dernière sauvegarde de l'host (voir 3), pour tous ; les points de sauvegarde de voyageurs (60 s) si l'host n'a pas sauvé après les avoir reçus.

### 1.3 L'invité perd Internet 20 secondes puis revient

- **Invité** : un lien Steam déclaré mort ne reprend pas. Retour au titre vers 25 s (estimé), avec ou sans Internet ; ensuite invitation Steam ou « Join Game » (B1, B2). Pas de reconnexion
  automatique (`Rejoin`, `LastLobby` : rien, `PLAN_sans_friction.md:113-115`).
- **Host** : l'invité disparaît au bout de 25 images (`ElinNetHost.cs:129`), ses compagnons suivent (`TakeCompanionsAlong`), son personnage reste dans la sauvegarde ; à son retour : toute la copie et
  la carte (1 à 2 s au banc, jamais mesuré à deux PC, `MODLOG.md:2042`). Rien n'est perdu côté host (voyage seul : 60 s, `EmpConfig.cs:250-258`). Non vérifié : retour **avant** que l'host lâche l'ancien lien (`PLAN_sans_friction.md:209-210`).
- **Sans dépôt** : pareil tant que l'host vit. C'est le seul cas qui marche sans dépôt.

### 1.4 L'host revient après qu'un invité a repris le monde

- **Avec dépôt** : « Take the world » est refusé, « X héberge » (`SaveDepot.cs:164-172`, `:314-326`). Sa copie locale n'écrase jamais un monde plus récent : elle reste de côté (`.unsent`,
  `.replaced-<date>` pour le dossier, `:174-186`, `:390-400`) ; un message le dit une fois (`Lost`, `:652-664`). Quand l'invité quitte, l'host prend le monde et retrouve **son** personnage
  (`pc_owner`, `PLAN_personnages_sans_question.md`). **Ce que l'host a joué depuis son dernier envoi est abandonné** (gardé de côté, jamais fusionné).
- **Sans dépôt** : il recharge sa sauvegarde, clique « Start Server », ré-invite tout le monde. Il n'y a pas eu de reprise.

---

## 2. Ce que le jeu de chaque invité possède quand l'host disparaît

**Une copie du `Game` prise à la connexion, pas tenue à jour pour toutes les cartes.**
- Le probe est `LZ4Bytes.Create(EClass.game)` (`Models/SessionState/SaveDataProbe.cs:25-27`), envoyé à la connexion (`ElinNetHostPlayerManager.cs:210-236`) et au retour d'un voyage seul
  (`ElinNetHostTravel.cs:1131`). Il contient les objets zone, les personnages globaux, les quêtes, la date, les factions ; **pas** les fichiers de carte.
- Ensuite : des deltas (`Models/Delta/*`, ~146 fichiers) et l'instantané de la carte active. Ce qui arrive dans une carte où il n'est pas n'arrive pas chez lui ; ses copies des autres joueurs datent de la connexion.
- Cartes : fichiers reçus **à chaque entrée** (`Models/ZoneState/ZoneDataResponse.cs:34-80`, écrits dans `Save/world_emp/<uid>/`), effacés par `InvalidateTemp`. Carte jamais visitée : aucun fichier.
- L'invité **ne peut pas sauvegarder** : `Game.Save` rend « réussi » sans rien faire (`GameSaveLoad.cs:12-20`) ; charger est refusé (`:23-34`). Son `Game.id` est `world_emp` (`ElinNetClientPlayer.cs:187`).

**Ce qui lui manque pour devenir host sur-le-champ**
1. Les cartes jamais visitées : régénérées si le fichier manque (`Zone.cs:664-668`). Une base ou ville bâtie perdrait ses constructions (non vérifié : le code lu n'excepte pas une zone de la faction).
2. Les registres par joueur : propriétés statiques écrites dans le morceau `context_vars` de la sauvegarde (`D/_decomp/Elin/ElinGameIOPropertyAttribute.cs`, `PLAN_creation_locale.md:72-76`, 475 octets sur un monde d'essai) :
   `remote_chara`, `remote_chara_roster` (`ElinNetHostPlayerManager.cs:25-40`), `personal_quests`, `player_standing` (`ElinNetHostPersonalQuests.cs:23-37`), `pc_owner`, `pc_orphan`
   (`ElinNetHostHandOver.cs:27,48`), `shipping_owed` (`ElinNetHostShipping.cs:26`), `lease_range_floor` (`ElinNetHostTravel.cs:44`). Le probe est le `Game` seul : il ne les porte pas. L'invité ne garde que
   **ses** quêtes et sa renommée (`ElinNetClientPlayer.cs:206`).
3. L'état du serveur en mémoire (qui est où, baux, invités de zone : `ElinNetHostTravel.cs:63-91`) : se reconstruit à la reconnexion de chacun.
4. Le rôle de gardien du monde : `WorldKeeper.IsKeeper` = « pas un client » (`Patches/WorldKeeper.cs:21`), seul endroit déjà préparé (`PLAN_serveur_depot.md`, étape 2).
5. Une sauvegarde sur disque, sous un nom de monde du dépôt (les gardes de `GameSaveLoad.cs`).

**Voyage indépendant : un invité est déjà host d'une zone, sous l'autorité de l'host du monde**
- L'host du monde **accorde le bail** : carte, état, plage de 50 000 numéros d'objets et de 10 000 de quêtes (`ElinNetHostTravel.cs:20-29`, `:760-783`). L'invité simule seul, ouvre une session de zone
  (`ElinNetHostZoneSession.cs:33-68`, écoute Steam SDR, pas de salon) que d'autres invités rejoignent.
- Point de sauvegarde toutes les 60 s vers l'host : état, fichiers de carte, personnage, compagnons, personnages de ses invités (`ElinNetClientTravel.cs:867-900`, `:935-948`). Seulement pour qui tient une zone.
- Si le tenant part ou plante : l'host passe le bail au premier invité de la zone, qui garde sa copie vivante, les autres le rejoignent (`HandOverZone` `ElinNetHostTravel.cs:908-965`, `TakeOverZone`
  `ElinNetClientTravel.cs:420`). **C'est une migration à chaud, mais pour une carte, arbitrée par l'host du monde.**
- Si l'host du monde disparaît : voir 1.2. Ne survit que le dernier point (60 s) **si** l'host l'avait écrit sur disque (`ElinNetHostTravel.cs:1129`) ; cohérence avec `game.txt` après plantage : non vérifié.

---

## 3. Les sauvegardes

- **Qui sauvegarde** : seulement l'host (`GameSaveLoad.cs:12-20`). Le mod n'ajoute aucun enregistrement périodique chez un host normal. Sauvegardes de l'host : menu et fermeture (`Game.cs:1032-1056`),
  changement de zone vers une zone de la faction ou à sauvegarde (`Chara.cs:3616-3624`), repos (`LayerSleep.cs:85`), option « autoSave » (`Scene.cs:284`, réglage de l'utilisateur : non vérifié) ; par le mod, après
  le retour ou la perte d'un voyageur (`ElinNetHostTravel.cs:1136`, `:1510`) et à la reprise d'un monde (`ElinNetHostPlayerManager.cs:357`). Exception : `-empserver`, toutes les 5 minutes tant qu'un invité est là (`Emp/EmpServer.cs:20`, `:111-116`).
- **Dépôt dossier ou serveur** : copie à chaque sauvegarde (`SaveDepot.cs:639-645`) + battement 60 s. **GitHub** : marqueur à chaque sauvegarde, envoi en arrière-plan **au plus toutes les 5 minutes**
  (`:42`, `:628-636`, `:676`), dernier envoi à la sortie.
- **Perdu si l'host plante** : tout depuis sa dernière sauvegarde ; avec GitHub, en plus, ce qui est sauvé mais pas envoyé (jusqu'à 5 minutes, sur son PC seulement). Les invités perdent la même chose : leur
  personnage vit dans le monde de l'host. De quelques minutes à plus d'une heure selon ses habitudes (non mesuré).
- **Poids** : monde d'essai 1,03 Mo (28 fichiers, `game.txt` 853 Ko) ; sauvegarde réelle de l'utilisateur dans le nuage 1,56 Mo (`PLAN_depot_github.md:64-68`) ; un long monde : non vérifié ; refus au-delà de 20 Mo de zip
  pour GitHub (`:194-199`).
- **Durées connues** : envois réels de 1,6 et 2,1 Mo à GitHub réussis hors du jeu (`depot_github_real.py`, `DOCUMENTATION.md:299`, durée non notée) ; demande GitHub 0,3 à 1 s, la première du jeu ~7 s (`PLAN_depot_github.md:103`,
  `MODLOG.md:2300`) ; dossier ou serveur : quelques dixièmes de seconde pour 74 Ko (`DOCUMENTATION.md:~409`). **Chargement d'un monde : jamais mesuré seul** ; au banc, host en jeu en 48 s (lancement compris), client 2 min 20 plus tard
  (`MODLOG.md:562-565`). Une reprise = deux chargements. **GitHub jamais joué depuis le jeu avec une vraie clé** (`HANDOFF.md:268-270`).

---

## 4. Steam

- **Changer le propriétaire d'un salon** : l'API le permet (`SetLobbyOwner` par le propriétaire ; Steam en désigne un autre quand il part ; seul le propriétaire écrit les données du salon ; le salon meurt avec son dernier membre :
  `PLAN_depot_steam.md:91`) : connaissance de l'API, **non relue** pour ce plan. **Le mod ne s'en sert pas** : « propriétaire sans être prêt = l'host a migré vers moi » -> `ResetSession` (`SteamNetLobbyManager.cs:380-384`).
- **Ce que l'host met dans le salon** : `SetGameServer` = son identifiant Steam (`:255`), version du mod, build, carte (`:257-262`), une clé de connexion par ami qui entre (`:368-373`). L'invité se connecte à `GameServer.id`
  quand sa clé apparaît (`ElinNetClient.cs:50-55`). L'host n'accepte que les identifiants d'une table en mémoire remplie à l'entrée (`SteamNetManagerServer.cs:14`, `:114`) : **un nouvel host devrait la remplir pour tous les membres déjà là**.
- **Retrouver le nouvel host** : (1) le propriétaire du salon, si le salon survit (des invités y sont encore) ; (2) son identifiant Steam et celui du salon écrits dans le dépôt : **aujourd'hui `lock.json` ne porte que
  machine:processus, nom, battement** (`Helper/GitHubDepot.cs:276`), le serveur et le dossier pareil (B3). Salon créé public, amis seulement admis (`SteamNetLobbyManager.cs:79-100`, `:368-378`).
- **Relais SDR** : lien `CreateListenSocketP2P(0)` / `ConnectP2P(identité, 0)` (`SteamNetManagerServer.cs:41`, `SteamNetManagerClient.cs:21`) : **par identifiant Steam, sans port à ouvrir** ; un nouvel host peut écouter tout de suite.
  Les zones de voyage seul passent déjà par là. **Deux fenêtres ne le prouvent pas** : le banc utilise un port UDP local et un seul compte Steam (`MODLOG.md`, conseil 6).
- **Serveur avec adresse** (`-empserver`) : connexion IP directe (`SteamNetManagerClient.cs:34-41`), UDP 55556 à ouvrir, pas de salon, pas de relais (`ElinNetClient.cs:77-83`).

---

## 5. Conceptions possibles, de la plus petite à la plus complète

Tailles = lignes de C# estimées, sans les tests ; jamais une mesure.

### E (e). Retour automatique après coupure, seul (l'host ne change pas) : 150 à 300 lignes
- **Voit** : l'invité coupé : « reconnexion… » 25 à 40 s (estimé), puis retour à sa place, sans question. L'autre : « X est parti », « X est revenu ». Si l'host est mort : après quelques essais, titre (ou A).
- **Écrire** : garder l'identifiant du salon avant `ResetSession` (`NetSession.cs:173`) ; reconnexion par `ConnectLobby` (`SteamNetLobbyManager.cs:115-142`) à essais espacés, pas après renvoi, refus de version ou annulation ;
  **A1** (supprimer l'écran de choix, `ElinNetHostPlayerManager.cs:81-104`) ; côté host, tolérer l'ancien lien encore ouvert (non vérifié) ; textes EN/JP/CN.
- **Perdu ou doublé** : rien côté host ; voyageur seul : jusqu'à 60 s. À vérifier : personnage en double si l'ancien lien n'est pas encore lâché. **Sauvegardes** : aucun risque (l'invité n'écrit rien).
- **Sans dépôt** : oui, tant que l'host vit. Ne répond pas à « l'host part ».
- **Test** : 2 fenêtres (`mp_test.py`) ; couper l'invité 20 s (suspendre son processus, ou une commande de pont qui ferme le lien : à écrire, aucun outil de coupure réseau n'existe) ; vérifier même position, même sac, un seul
  personnage de lui sur la carte de l'host, durée notée. **Build Release** pour le délai de 15 s (`ElinNetClient.cs:57`), ou un crochet de test.

### A (a). Reprise automatique par un invité depuis la dernière sauvegarde du dépôt : 500 à 900 lignes
- **Voit** : départ propre : « X est parti, Y reprend le monde », compte à rebours, 30 à 90 s plus tard (estimé : téléchargement, **deux chargements**, ouverture) tous sont dans le monde, à la dernière sauvegarde, avec leur
  personnage. Après plantage : détection 25 s + verrou 3 min (`SaveDepot.cs:37`) = **3 à 5 minutes** si le verrou n'est pas raccourci.
- **Écrire** : E ; une règle sans élection de qui reprend (plus petit identifiant Steam des présents, ou propriétaire du salon) ; `Take` + `Start Server` automatiques (`SaveDepot.cs:164`, `ElinNetHost.cs:22-72`, B8) ;
  identifiant Steam et salon dans le dépôt (trois protocoles : `GitHubDepot.cs:276`, `host.txt` du dossier, `D/server/ElinTogetherServer.cs`) ; **enregistrement périodique chez l'host** (2 à 5 minutes, sinon la reprise rembobine
  beaucoup) ; verrou plus court quand les invités savent l'host mort ; A1 ; `OnQuit` pour dossier et serveur ; textes.
- **Perdu ou doublé** : tout depuis la dernière sauvegarde envoyée, pour tous ; jamais de doublon (un seul fil du temps, tout recule ensemble). Un voyageur seul perd ses 60 s s'ils n'étaient pas dans la sauvegarde.
- **Sauvegardes** : l'host qui revient ne peut pas écraser (prouvé : `depot_suite` P1, D5) ; deux reprises simultanées : GitHub tranche par le `sha` (`DOCUMENTATION.md:~203`) ; sa partie reste de côté, jamais fusionnée.
- **Sans dépôt** : **non**. Variante A' : l'host pousse son monde (zip 1 à 2 Mo) à chaque invité toutes les 5 minutes par Steam, en morceaux de 256 Ko avec numéro de version (`PLAN_depot_steam.md:117-122`, 200 à 300 lignes) ;
  le premier invité reprend de cette copie. Marche seulement si l'host a sauvé et envoyé avant de tomber.
- **Test** : `depot_suite.py` étendu, 2 fenêtres : A héberge, B joint ; **tuer A par son numéro de processus** (déjà fait en G4, `depot_suite.py:344`) ; B reprend sans clic ; compter les secondes ; monde juste (seau posé avant
  la dernière sauvegarde présent, après absent) ; personnage de B à B ; retour de A refusé et gardé de côté. « Les autres se rattachent » : **3 fenêtres**, accord à demander (`CLAUDE.md` limite à 2).

### B (b). La même, mais l'invité qui reprend part de SA copie, plus fraîche que le dépôt : A + 400 à 800 lignes
- **Voit** : comme A, mais ce qu'il a gagné dans les dernières minutes (or, objets, la carte où il est) est là ; l'autre invité retrouve son personnage tel qu'il l'avait.
- **Écrire** : avant `ResetSession`, un colis de secours sur disque : personnage, compagnons, fichiers de la carte où il est, date (le contenu d'un point de sauvegarde de voyage, `CreateLeaseRelease`
  `ElinNetClientTravel.cs:867-900`) ; ne plus effacer `world_emp` aussitôt (`ResourceFetch.cs:35-55`) ; poser le colis sur le monde du dépôt avant le chargement (`CharaImport`, `ReplaceRemoteChara` existent) ; chaque autre
  invité apporte le sien en revenant.
- **Perdu ou doublé** : les **coutures** : un objet donné ou échangé entre la dernière sauvegarde et la chute est dans deux sacs (la vieille copie chez le donneur, la neuve chez le receveur) ; or payé deux fois ; coffres,
  expédition, base : rien d'autre que le personnage et la carte tenue n'est frais. Piste non vérifiée : chaque objet a un numéro unique, la copie fraîche gagne, les mêmes numéros sont retirés ailleurs.
- **Sauvegardes** : risque plus élevé que A (un mélange de deux instants) ; garder le dépôt d'avant de côté (le dossier le fait déjà, `SaveDepot.cs:390-400`).
- **Sans dépôt** : seulement avec A' (sinon il manque les cartes jamais visitées).
- **Test** : A héberge, B joint, ramasse un objet marqué et gagne de l'or **après** la dernière sauvegarde ; A tué ; B reprend ; objet et or présents ; personnage de A intact à son retour ; **aucun numéro d'objet en double**
  dans le monde ; cas piège : A donne un objet à B après la sauvegarde puis tombe.

### C (c). Migration à chaud : un invité devient host sans rechargement : 2 000 à 4 000 lignes (étapes 3 et 4 de `PLAN_serveur_depot.md`, « grosses »)
- **Voit** : départ propre planifié (l'host désigne l'héritier avant de partir) : **rien**. Plantage : ~25 s de jeu figé, puis tout le monde au même endroit, sans rechargement.
- **Écrire** : l'héritier passe de `ElinNetClient` à `ElinNetHost` sans toucher à son jeu ; propriétaire du salon = héritier (retourner `SteamNetLobbyManager.cs:380-384`, clés de connexion de tous les membres, `SetGameServer`) ;
  **copie continue des registres par joueur chez tous les invités** (quelques Ko) ; cartes jamais visitées prises au dépôt ou à une copie A' ; reprise du bail de toutes les zones (modèle `HandOverZone`) ; plages d'uid
  (`ElinNetHostTravel.cs:20-57`) ; gardien (`WorldKeeper.cs:21`) ; ~50 endroits « si je suis l'host » (`PLAN_serveur_depot.md:36-37`) ; sauvegarde sous un nom de monde (`GameSaveLoad.cs:12-20`) ; les autres se rattachent par
  le chemin « rejoindre ».
- **Perdu ou doublé** : presque rien sur la carte active (l'héritier a reçu chaque delta) ; perdues : cartes jamais visitées (sans dépôt), la dernière seconde de l'host. Doublé : **cerveau fendu** si deux invités se croient héritiers ;
  règle sans ambiguïté obligatoire.
- **Sauvegardes** : risque le plus grand : le monde de l'héritier est une copie reconstruite (`Game.id = world_emp`) ; l'écrire comme monde du dépôt demande de réparer `pc`, `pc_owner`, `remote_chara`. Toujours garder l'ancien dépôt de côté.
- **Sans dépôt** : possible pour ce qui est en mémoire ; le reste est régénéré : **sans dépôt, il faut A'**.
- **Test** : 2 fenêtres : tuer le host ; le jeu de B ne se recharge pas (même identité d'objet `pc`, `pc_id` de `leave_suite.py:24-26`), la date avance, B sauve sous un nom de dépôt, A relancé rejoint B. « Les autres se rattachent » :
  **3 fenêtres**. Deux fenêtres ne prouvent pas le salon Steam ni le relais SDR : deux PC, deux comptes.

### D (d). Plus d'host : un petit serveur toujours allumé : existe en partie, 100 à 300 lignes pour le rendre agréable
- **Voit** : il tape l'adresse et joue ; un joueur qui part ou revient n'arrête rien.
- **Déjà là** : `Elin.exe -empserver <sauvegarde>` + `Serveur.bat` (`Emp/EmpServer.cs`), sauvegarde toutes les 5 minutes tant qu'un invité est là (`:111-116`), « Elin Together Server » (dépôt seul, sans jeu). `server_suite.py` 9/9.
- **Reste** : un PC allumé avec Elin et Steam ; **UDP 55556 à ouvrir** (pas de relais, `SteamNetManagerClient.cs:34-41`) ; pas sur un NAS (`DOCUMENTATION.md:673-674`) ; base fondée exigée (`EmpServer.cs:84-87`) ; le personnage de l'host
  reste planté à la base ; **jamais essayé entre deux PC par Internet** (`DOCUMENTATION.md:410-414`) ; le serveur peut planter comme un host (même perte de 5 minutes, sauf A pour lui) ; E pour que les invités reviennent seuls.
- **Sans dépôt** : oui, le monde est sur le PC du serveur. **Test** : `server_suite.py` : tuer le jeu serveur par son numéro de processus, le relancer, vérifier le monde et la reconnexion des invités (E).

**Dépendances** : E et A1 d'abord (utiles seuls) ; l'enregistrement périodique et les identifiants Steam dans le dépôt servent A, B, C ; A' sert tous les cas sans dépôt ; C réutilise A et A' ; D est indépendant.

---

## 6. Questions que le conseil doit trancher

1. **Quel but ?** « L'host part sans que personne ne le remarque » (C) ou « on perd quelques minutes mais on reprend seul » (A, B) ?
2. **Sans dépôt** : accepte-t-on qu'aucune reprise ne soit possible, ou construit-on la copie du monde chez chaque invité (A') ?
3. **Qui reprend** : le propriétaire du salon (Steam choisit), le plus petit identifiant, ou le dernier à avoir parlé à l'host ? Et à égalité ?
4. **Perte acceptée** : combien de minutes de jeu peut-on rembobiner pour tous ? Enregistrement périodique de l'host toutes les 2 ou 5 minutes, dans un fil séparé pour ne pas figer le jeu ?
5. **Fraîcheur ou cohérence** : B (copie fraîche, doublons possibles aux coutures) ou A (rembobinage cohérent) ? Quelle règle de doublon ?
6. **Verrou du dépôt** : le raccourcir (3 min -> 30 s ?) quand les invités constatent que l'host est mort, au risque de deux hosts ? Qui a le dernier mot ?
7. **Retour de l'host** : il rejoint comme invité (son jeu depuis la chute est gardé de côté) ? Faut-il le lui dire, et comment ?
8. **Écran « Who do you want to play? »** (A1) : supprimé avant tout retour automatique ? (Aucun automatisme ne tient avec lui.)
9. **Nouveau salon ou même salon** pour les invités après une reprise ? (Le même salon demande l'API de propriétaire de Steam, à essayer sur deux PC.)
10. **Tests** : accord pour 3 fenêtres Elin pour « les autres se rattachent » ? un build Release pour les délais ? un essai réel à deux PC et deux comptes Steam avant de promettre quoi que ce soit sur Steam ?
11. **Serveur toujours allumé** (D) : est-ce déjà la réponse pour l'utilisateur, s'il a un PC et un port ouvert ?

## Non vérifié (à ne pas croire sans test)

- Tout le comportement Steam : délai de mort d'un lien (10 s ?), migration de propriétaire, `SetLobbyOwner`, durée de vie du salon, relais SDR entre deux comptes.
- Que les registres par joueur ne voyagent jamais dans le probe (lu dans `SaveDataProbe.cs`, pas capturé en jeu) ; que `autoSave` soit actif chez l'host de l'utilisateur ; la taille et le temps de chargement d'un vrai long monde ; la durée de 25 images.
- Retour d'un invité avant que l'host ait lâché l'ancien lien ; cohérence des fichiers de point de sauvegarde avec `game.txt` après plantage ; zone de la faction régénérée si son fichier manque ; verrou non rendu à la fermeture de la fenêtre
  pour dossier et serveur (lu, pas joué). Toutes les durées « estimé » et toutes les tailles en lignes de code.
