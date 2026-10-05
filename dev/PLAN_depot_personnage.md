# Plan : que chacun retrouve SON personnage quand le monde passe de main en main (dépôt)

Date : 2026-10-05. Lecture seule : rien compilé, rien lancé, rien modifié. Chemins du mod relatifs à
`ElinTogether/ElinTogether/`, code du jeu = `dev/_decomp/Elin/`. Ce que je n'ai pas pu vérifier est marqué « non vérifié ».

## Le problème en une phrase (prouvé)

`dev/_shots/depot-p1.log` : avant, H joue uid 1 et A joue uid 469. Après la reprise par A, `EClass.pc` = uid 1 (or 8,
sac de H) ; uid 469 (or 261, seau) est « global (pas sur la carte) », `joueur=False`. Le test donne 17/20 : 3 échecs.
Cause en 3 faits :
- Le jeu choisit son personnage joué par `player.uidChara` écrit dans la sauvegarde (`Game.cs:780-784` : dans
  `OnGameInstantiated`, le personnage global dont l'uid == `player.uidChara` devient `player.chara`).
- `EClass.pc` n'est que `core.game.player.chara` (`EClass.cs:15`) et `Chara.IsPC` n'est que `this == player.chara` (`Chara.cs:632`).
- Dans la sauvegarde de l'host, `player.uidChara` = le personnage de l'host (uid 1). Le mod ne le change jamais côté host.

## 1. Comment le mod relie un joueur à son personnage

1. Identité = **identifiant Steam (ulong)** : `peer.User` (`Net/Host/ElinNetHostPlayerManager.cs:75,81,117`) ;
   la source est `UserData.Me` / `SteamUser.GetSteamID()` (`Helper/Steam/PlayerUidMaker.cs:17-20`). Ni nom ni clé
   (la « clé de connexion » `MakeConnectionKey` sert à autre chose). Le nom n'est que pour l'affichage.
2. Enregistré dans la sauvegarde de l'HOST, comme propriétés du jeu (`[ElinGameIOProperty]`, défini dans la
   bibliothèque ElinModdingKit : où exactement dans les fichiers de la sauvegarde = non vérifié, mais c'est lu et
   écrit avec la sauvegarde, `Net/Host/ElinNetHost.cs:176`) :
   - `remote_chara` : Steam id -> uid du personnage joué en dernier (`ElinNetHostPlayerManager.cs:25-30`) ;
   - `remote_chara_roster` : Steam id -> liste des uid de ses personnages (`:35-40`) ;
   - `player_standing` : uid du personnage -> [renommée, karma] (`ElinNetHostPersonalQuests.cs:31-38`) ;
   - `personal_quests` : uid du personnage -> ses quêtes aléatoires (`:21-28`).
   Tout est clé par **uid de personnage**, sauf `remote_chara*` clé par Steam id.
3. **L'host n'est dans aucune de ces tables.** Son personnage est `player.uidChara` et il est inscrit à l'état 0 avec
   `User = UserData.Me` seulement pour la session (`Net/Host/ElinNetHost.cs:51-55`), rien n'est écrit pour la
   prochaine fois. Conséquence (déduite du code, non testée) : quand H, devenu simple invité, rejoint A, la ligne
   `SavedRemoteCharas.TryGetValue(peer.User, ...)` ne le trouve pas (`ElinNetHostPlayerManager.cs:102-105`) et il se
   verrait demander un NOUVEAU personnage, alors que uid 1 existe.
4. Un client qui rejoint : `PreparePlayerJoin` (`ElinNetHostPlayerManager.cs:70-110`). Avec `ChooseCharacter`
   (option host, `Emp/EmpConfig.cs:234`, `:334`) et au moins un personnage dans son roster : l'host envoie
   `SessionCharaSelectRequest` avec la liste (`RosterOf`, `:115-130`, ceux qui ne sont pas déjà joués) ; la réponse
   `OnSessionCharaSelectResponse` (`:135-155`) fixe `SavedRemoteCharas[user]` puis envoie la sauvegarde. Sans
   `ChooseCharacter` : le dernier personnage joué, sans question. Aucun cas : `SessionNewPlayerRequest` (création).
   Le choix est refusé si `IsZoneSession` (`:82`). Import d'une autre sauvegarde : `OnSessionCharaImportResponse`
   (`:160-201`, option `ImportCharacter`, `Helper/CharaImport.cs`).
5. Départ d'un invité : `OnPeerDisconnected` (`Net/Host/ElinNetHost.cs:162-198`) -> `RemoveRemoteChara`
   (`ElinNetHostPlayerManager.cs:42-65`) : sorti de la carte (`_zone.RemoveCard`) et du groupe, **gardé dans
   `game.cards.globalCharas`** (commentaire `:175`). Il n'est pas rangé dans un sac ni détruit : c'est un personnage
   global sans carte. Ses affaires (sac, or) restent sur lui. À chaque chargement, `RemoveLeftOverCharas`
   (`:329-346`, `[ElinPostLoad]`) retire de la carte tout `remote_chara` qui n'est pas `pc`.
   Écart avec ton énoncé : le journal dit bien « global (pas sur la carte) » pour 469, pas « sur la carte comme un
   personnage ordinaire ».
6. Le personnage d'un invité garde `IsPC=false` (`SetBool(CINT.IsPC,false)`, `:243`) et `remote_chara=true` (`:216`).

## 2. Ce qui est au « joueur » (classe Player) et pas au personnage

`dev/_decomp/Elin/Player.cs` : `uidChara` (:936), `uidSpawnZone` (:939), `karma` (:945), `fame` (:948),
`uidLastTravelZone/LastZone/LastShippedZone` (:963-969), `hotbarPage` (:990), `uidLastTown` (:1005),
`questRerollCost` (:1029), `questTracker` (:1059), `hotbars` (:1155), `flags` (:1164), `recipes` (:1167),
`uidPickOnLoad` (:1191) ; plus `nums`, `codex`, et les quêtes/factions du `Game` (`game.quests`). `player.chara` (:1278).
Ce que le mod garde par joueur et où :
- **Rien d'autre que fame/karma et quêtes aléatoires** (tables ci-dessus, dans la sauvegarde de l'host, par uid de personnage).
- Recettes, raccourcis, drapeaux, codex, `uidSpawnZone`, etc. : **un seul jeu pour tout le monde**. Un invité reçoit
  la copie du `Game` de l'host (`Models/SessionState/SaveDataProbe.cs:22-28` : `LZ4Bytes.Create(EClass.game)` +
  l'uid du personnage), l'ouvre dans son jeu (`Net/Client/ElinNetClientPlayer.cs:175-198` : `core.game = probeGame`,
  `player.uidChara = remoteChara.uid; player.chara = remoteChara`) ; il a donc les recettes/raccourcis de l'host.
  Les recettes apprises circulent par `AddRecipeDelta` (`Models/Delta/Misc/AddRecipeDelta.cs:25`), les drapeaux de
  dialogue par `Helper/DialogFlagSync.cs`. Aucun fichier à part côté invité (non vérifié par une recherche
  exhaustive, mais je n'ai trouvé aucun stockage local de ces données).
- À la connexion, l'invité reçoit : le `Game` entier de l'host (avec SON `Player`) + `Rules` ; puis
  `PersonalStateDelta` (ses quêtes, le « déjà pris », fame, karma : `ElinNetHostPersonalQuests.cs:290-321`, si
  `UsePersonalQuests`). Le client remplace quêtes + fame/karma de l'host par les siens
  (`Helper/PersonalQuests.cs:197-210`, `Restore :339-369`) et les renvoie à l'host (`:185-190`).
- Donc l'host, lui, garde dans `player.fame/karma/quests` SES données, sans entrée dans `player_standing`.

## 3. Ce que fait `SaveDepot.Take` / `TakeFrom`

`Helper/SaveDepot.cs` :
- `Take` (:162-221) : vérifie le verrou (`HeldBy`), gère une copie non envoyée (`.unsent`), puis télécharge (`Ask("TAKE")`,
  :187) ou copie (:207) le monde dans `CorePath.RootSave + "world_depot"` (:68, :33), puis `Game.Load(WorldId, false)` (:220).
  `TakeFrom` (:229-260) règle `DepotPath` à l'adresse puis appelle `Take`.
- Aucune ligne de `SaveDepot` ne touche au personnage : `Game.Load` fait son travail normal -> `player.uidChara` de
  la sauvegarde -> `player.chara`. La sauvegarde est celle que l'ancien host a écrite par `Game.Save` (:619-645) : son
  `uidChara` = uid 1. D'où `pc` = personnage de H, quel que soit le preneur.
- Au chargement, `GameSaveLoad.TerminateConnectionOnLoad` ferme toute session (`Patches/GameSaveLoad.cs:36-40`).
  Puis le preneur ouvre la session « comme avec n'importe quelle sauvegarde » (commentaire `:160-161`).
- Seul état lié au joueur dans `SaveDepot` : `MyName` (nom du pc, pour l'affichage du verrou, :95) et `Me`
  (machine:processus, :93). Aucun Steam id.

## 4. Le mode serveur sans joueur (`-empserver`)

- `Emp/EmpServer.cs:29-139` : charge la sauvegarde (:62-66, ou `Take` pour `world_depot` :60-61), exige que
  `EClass.player.chara.homeBranch.owner` existe (:80-83 : « pas de base »), ouvre `ElinNetHost.StartServer(true)` (:91),
  sauvegarde toutes les 5 min si plus d'une personne est là (:117). Le dossier `ElinMP/server.txt` dit l'état.
- **Il n'évite rien activement** : personne ne joue la fenêtre, voilà tout (`DOCUMENTATION.md:413` : « Le personnage de
  l'host de la sauvegarde reste planté à la base »). Tous les joueurs rejoignent comme invités distants et passent par
  `PreparePlayerJoin` ; le pc de la sauvegarde reste inscrit à l'état 0 (`Count > 1` :117 le prend en compte).
- Réutilisable ? La partie « personne ne joue le pc » : oui mais **elle exige un 2e processus Elin** (une fenêtre =
  un seul `Game`/`EClass.pc`, `EClass.cs:15`), et un joueur doit s'y connecter comme client. Elle ne sert pas à un
  repreneur qui veut JOUER dans la fenêtre qui héberge. Mise en garde (`DOCUMENTATION.md:409-412`) : second Elin avec le
  même compte Steam pas testé, Steam peut refuser. Le serveur sans Elin (`dev/server`) ne fait tourner aucun jeu.
- `Patches/WorldKeeper.cs:15,24` : le « gardien du monde » = l'host (`IsKeeper` = pas un client). Il fait avancer le
  monde ; sans rapport avec l'identité du pc. Le plan de déplacer ce rôle : `dev/PLAN_serveur_depot.md`.

## 5. Code existant qui change de personnage joué

- **Échange temporaire de `player.chara`** (le précédent le plus proche) : `Helper/PersonalQuests.cs:396-425`
  (`PlayerStandIn.For` : met `EClass.player.chara = actor` le temps d'une action, puis remet ; envoie au joueur la
  renommée/karma gagnés) ; `Models/RemoteCraft.cs:32-35` ; `Net/Host/ElinNetHostShipping.cs:143-146` ;
  `ElinNetHostPlayerManager.cs:249/282` (création d'un personnage d'invité avec `player.chara = chara` puis retour).
- **Échange définitif, côté invité** : `Net/Client/ElinNetClientPlayer.cs:196-197` (`player.uidChara = ...; player.chara = ...`
  juste après avoir ouvert la copie du `Game` de l'host). C'est exactement ce qu'il faudrait faire pour le repreneur,
  mais sur sa propre sauvegarde chargée.
- Import d'un personnage d'une autre sauvegarde : `Helper/CharaImport.cs:105-115` (lecture seule, `Detach` pour
  couper les liens de zone), `Adopt` (:196-215 : `IsPC=false`, nouveaux uid, `c_uidAttune` recopié, factures détruites).
- `SetPC` : n'existe pas (recherche faite dans le mod et dans `Chara.cs`/`Player.cs` : seule `SetPCCState`, qui est autre chose).
- Remarque : `Card._IsPC` (`CINT.IsPC`, `Card.cs:2199`) est un drapeau SAUVÉ sur le personnage, distinct de `IsPC`
  (qui se calcule). Il sert à peu d'endroits (`Chara.cs:10866`, `ABILITY.cs:384`, `ConDrunk`, `ConHallucination`).
  Un échange propre doit le déplacer d'un personnage à l'autre.

## 6. Les options

Besoin commun aux options A et B : **le mod doit apprendre qui est le propriétaire du pc de la sauvegarde** (aujourd'hui
nulle part, cf. §1 point 3). Ajouter une propriété de sauvegarde (même mécanisme que `remote_chara`) :
`SavedRemoteCharas[UserData.Me] = player.uidChara` et le roster, écrits quand l'host ouvre la session
(`Net/Host/ElinNetHost.cs:51` est l'endroit naturel).

### Option A — échanger le pc juste après le chargement (la plus petite)

Écrire : un `[ElinPostLoad]` (ou dans `SaveDepot.Take` après `Game.Load`, mais un hook est plus sûr car le monde est déjà
instancié) qui, si le monde vient du dépôt (`Game.id == WorldId`) et que `SavedRemoteCharas[UserData.Me]` existe et
diffère de `player.uidChara` : (1) écrit la renommée/karma/quêtes aléatoires du pc sortant dans `player_standing`/
`personal_quests` sous son uid ; (2) met `player.uidChara`/`player.chara` = mon personnage (comme
`ElinNetClientPlayer.cs:196-197`) ; (3) déplace `CINT.IsPC` ; (4) charge mon karma/fame/quêtes ; (5) pose mon personnage
là où est le pc (il est global sans carte : `currentZone`/`pos` à fixer, sinon `Zone.AddGlobalCharasOnActivate`
`Zone.cs:1710-1777` le place au centre selon `currentZone`) ; (6) l'ancien pc devient un personnage « distant » inactif :
`SetBool("remote_chara", true)` + `SavedRemoteCharas[ancien Steam id] = uid 1`, pour que H, qui rejoint ensuite A,
reprenne uid 1 par le chemin normal (`PreparePlayerJoin`). Cas sans correspondance (monde jamais hébergé, première fois) :
ne rien changer.
- Fichiers : `Net/Host/ElinNetHost.cs` (écrire l'identité du pc), `Net/Host/ElinNetHostPlayerManager.cs` (échange +
  `RemoveLeftOverCharas` qui exclut déjà `pc`), éventuellement `Helper/SaveDepot.cs` (lancer le hook seulement pour le dépôt).
- Sauvegardes existantes : sans la nouvelle propriété, aucun échange (comportement actuel inchangé). Les mondes déjà
  passés par le dépôt n'ont pas l'identité de l'ancien host : non réparés automatiquement (à demander une fois ?).
- Perte/duplication : aucun objet copié, juste `uidChara` qui change : pas de duplication. Risque de perte : l'or et le
  sac de l'invité sont ceux **vus par l'host** ; le test P1 montre qu'ils n'arrivaient pas à l'host (échec 1 : or 138 mais
  0 seau) tant que le jeu de l'invité n'a pas tout remonté. Il faut donc d'abord comprendre ce décalage (non vérifié :
  quand exactement l'host reçoit le sac de l'invité). Autre risque : le pc porte la base (`homeZone/homeBranch`,
  factions : `Chara.cs:432-436,1115`, `Zone.cs:480`) ; le personnage de A, un invité, n'est peut-être pas du camp de la
  base (non vérifié) : sinon `IsPCFaction` serait faux et la base ne serait plus « à lui ».
- Devenir de l'ancien host : personnage ordinaire au repos dans le monde, redevient le sien quand il rejoint.
- Dépôt GitHub / copie par Steam : rien à changer, le dépôt reste une copie de dossier. L'échange vit côté jeu.
  Avec le plan Steam (`PLAN_depot_steam.md`, option c, copies de pair à pair) il faut seulement que le Steam id du
  repreneur soit celui de `remote_chara`, ce qui est déjà le cas.

### Option B — échanger à l'ENTRÉE du monde par un choix (variante de A avec dialogue)

Après le chargement, ouvrir la liste de personnages (réutiliser `SessionCharaSelectRequest`/`ShowCharaChoice`,
`Net/Client/ElinNetClientPlayer.cs:29-66`, mais en local, le preneur étant l'host) : le repreneur choisit lui-même (ses
personnages = `RosterOf`, + le pc sortant s'il en est le propriétaire). Mêmes écritures qu'en A + une fenêtre.
- Plus de code (fenêtre locale), aucun avantage tant que A retrouve seul son personnage ; utile quand le Steam id est
  inconnu (anciens mondes) ou qu'un joueur a plusieurs personnages. Mêmes risques de perte/duplication que A.

### Option C — héberger « comme un serveur » : le pc de la sauvegarde planté, tout le monde est invité distant

Au premier dépôt, le pc devient un « gardien » que personne ne joue ; le repreneur et H rejoignent tous deux comme
clients de l'host. Écrire : un 2e processus Elin lancé en `-empserver world_depot` par le jeu du repreneur, puis le jeu du
repreneur se connecte à `127.0.0.1` (client normal). Rien à changer dans `PreparePlayerJoin`.
- Écart parité parfait (tout le monde est client), mais : deux Elin par PC (`CLAUDE.md` : « deux fenêtres au plus ») ; le
  même compte Steam peut être refusé (`DOCUMENTATION.md:409-412`) ; il faut que le pc du gardien ait une base
  (`EmpServer.cs:80-83`) ; H, ancien host, devrait alors choisir/créer un autre personnage (son uid 1 est le gardien) ou
  on convertit uid 1 en personnage « remote » (même travail que A, point 6) ; le gardien reste planté pour toujours.
- Risque sauvegardes : monde existant -> le gardien est le pc de H, donc H perd son personnage tant que rien n'est converti.
  Perte/duplication : aucune copie. Dépôt : inchangé (GitHub = le même dossier ; Steam : le processus serveur doit lire la
  copie).

### Option D — une sauvegarde par joueur, fusionnée à la reprise

Chaque joueur dépose son propre personnage (sac, or, fame/karma, quêtes) ; le repreneur fusionne les autres dans le monde.
Gros : plusieurs sources de vérité, risque de dupliquer des objets/de l'or à la fusion (même uid de cartes), réécrit le dépôt
(GitHub : un fichier par joueur ; Steam : un objet par joueur). `CharaImport.Adopt` donne la mécanique de fusion, mais
elle réattribue des uid et n'a pas été prévue pour revenir. **Pas recommandé.**

### Recommandation

**A**, précédée de l'écriture de l'identité du propriétaire du pc à l'ouverture de la session. C'est le plus petit
(un hook + une propriété de sauvegarde), il réutilise le code déjà éprouvé de l'invité (`ElinNetClientPlayer.cs:196-197`)
et ne change rien aux dépôts. B s'ajoute si on veut un choix explicite.

## 7. Comment prouver la correction avec `depot_suite.py` P1

Le test P1 existe déjà (`dev/_tools/depot_suite.py:418-487`) et contient les vérifications cibles :
1. `P1 A joue son propre personnage` : après `take(A)`, `EClass.pc.uid == uid_a` et même nom (:476-478). Rouge aujourd'hui, vert si A.
2. `P1 il a son seau et son or` : le pc de A a le seau et or + 123 (:479-481).
3. `P1 le personnage de H est toujours dans le monde, même sac, même or, et ne bouge pas` (:482-487) : prouve qu'il n'y a ni
   perte ni duplication de H (déjà vert, doit le rester, à regarder aussi avec H devenu `remote_chara`).
À ajouter (pas encore écrit) : (a) la boucle complète : H rejoint ensuite A et joue uid 1 SANS question de création
(`SessionNewPlayerRequest` ne doit pas arriver) avec son or 8 et son sac d'avant ; (b) compter les objets du monde
avant/après (aucun objet en double : uid distincts, `bucket` = 1 exemplaire) ; (c) un monde ancien sans la propriété :
le chargement se passe comme avant, sans exception ; (d) fame/karma de chacun restitués (poser un karma différent à H et A
avant le départ). Avant tout : régler l'échec 1 du journal (le seau de A n'arrive pas à l'host, or arrive) ou le contourner
comme le test le fait aujourd'hui (« donné par l'host »), faute de quoi on ne sait pas si A ré-hébergé retrouve son sac réel.
