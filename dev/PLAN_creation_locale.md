# Plan : création locale du personnage d'un nouveau joueur qui prend un monde en premier (6 octobre 2026)

Trou à boucher (`PLAN_personnages_sans_question.md`, « Étape 2 ») : un joueur sans personnage dans le monde, qui prend en
premier le monde d'un autre joueur connu (`SaveDepot.Take` puis `Game.Load`), joue le personnage de l'autre.
Ce document ne contient que des faits relevés dans le code et trois façons de faire. Rien n'est écrit dans le mod.
« non vérifié » = pas relevé dans le code, ou dans une DLL non lue (`ElinModdingKit`).

## 1. Comment un nouveau joueur qui REJOINT crée son personnage aujourd'hui

1. L'hôte (`ElinNetHostPlayerManager.cs:70-114`, `PreparePlayerJoin`) : pas de personnage connu pour ce compte
   (`SavedRemoteCharas`, l. 106-109) -> `peer.Send(new SessionNewPlayerRequest())`. Même envoi si le joueur choisit
   « nouveau » dans la liste (l. 145-149). Un orphelin lui est d'abord donné (`GiveOrphanTo`, l. 76).
2. Le client (`ElinNetClientPlayer.cs:106-136`, `OnSessionNewPlayerRequest`) :
   - l. 111 `AdvanceHandshake(Joined)` ; l. 113 `ui.RemoveLayer<LayerEditBio>()` ; l. 114 `ui.AddLayer<LayerEditBio>()` ;
   - l. 118 cache le bloc « Mode » ; l. 122-123 coupe l'action d'origine du bouton `ButtonEmbark`
     (`SetPersistentListenerState(0, Off)`, qui ouvrait `LayerWorldSetting`) ; l. 124-130 la remplace par :
     `Host.Send(request.Ready())`, `game.Kill()`, `ui.RemoveLayer(embark)`, `core.game = null` ;
   - l. 131-135 : si l'écran est fermé sans avoir validé (`ready` faux) -> `Socket.Disconnect(... ClientCancel)`.
3. D'où vient le `game` temporaire : de `LayerEditBio.OnAfterAddLayer` (`dev/_decomp/Elin/LayerEditBio.cs:15-20`) :
   `if (ELayer.game == null) Game.Create();`. Le client est à l'écran titre : `Scene.Init(Title)` fait `game.Kill()`
   (`Scene.cs:196-201`), donc `game` est nul. `Game.Create` (`Game.cs:751-759`) change `Game.id` (nouvel id `world_N`,
   `GameIO.GetNewId`), vide le dossier Temp (`GameIO.ResetTemp`, `GameIO.cs:54`) et crée un monde complet (`_Create`,
   `Game.cs:~790`), dont `Player.OnCreateGame` (`Player.cs:1423-1448`) qui fabrique le personnage `player.chara`
   (`CharaGen.Create("chara")`, apparence au hasard, karma 30). C'est CE personnage que l'écran édite.
4. `SessionNewPlayerRequest.Ready()` (`Models/SessionState/SessionNewPlayerRequest.cs:11-16`) : la réponse ne contient que
   `Chara = LZ4Bytes.Create(EClass.pc)`. Pas de fame/karma, pas de domaines, pas d'id de monde.
5. L'hôte (`ElinNetHostPlayerManager.cs:241-294`, `OnSessionNewPlayerResponse`) adopte, dans SON monde :
   - l. 246-249 `Decompress<Chara>()`, `IsPC` faux, `emp_creating` vrai, `game.cards.AssignUID(chara)` (l'uid du monde de l'hôte) ;
   - l. 251-287 : `player.chara = chara` (l. 253, le temps de la fonction : `EClass.pc` est `game.player.chara`,
     `EClass.cs:13-15`, donc `CreateEquip` équipe le bon personnage), même suite d'opérations que
     `Player.OnStartNewGame` (`Player.cs:1456-1495` : pv, foi, éléments, `vTempPotential`, déséquipe, `things.DestroyAll`,
     faim, endurance, `Refresh`), puis `player.CreateEquip()` (l. 282, `Player.cs:1736`) et `AddThing("purse")` ;
     `finally` : `emp_creating` faux, `player.chara = host` (l. 284-287) ;
   - l. 289-291 : `SavedRemoteCharas[peer.User] = chara.uid`, `RosterOf(peer.User)` (met le personnage dans la liste) ;
   - l. 293 `SendSaveProbe(chara, peer)`.
   Remarque : `player.RefreshDomain()` n'est pas appelé avant `CreateEquip` (domaines tirés du métier, `Player.cs`
   `RefreshDomain`) : un mage/prêtre reçoit les livres des domaines du personnage de l'hôte. Non vérifié si cela se voit.
6. `SendSaveProbe` (l. 210-236) ajoute ce qui est propre à une session et NE doit PAS être refait en local :
   `ActiveRemoteCharas`, `MakeAlly()` (l. 218, l'ajoute au groupe de `pc`), `MoveZone(pc.currentZone)`, `remote_chara` vrai,
   `GiveAxeToRemotePlayer` (l. 221, la hache de départ), `States`, `CardCache`, `Session.CurrentPlayers`, envoi des règles.
   Fame/karma d'un nouveau : donnés plus tard par `SendPersonalState` (`ElinNetHostPersonalQuests.cs:299-301`,
   `[0, NewPlayerKarma=30]`), seulement si une session existe et `UsePersonalQuests`.
7. Côté client ensuite (`OnSaveDataProbe`, `ElinNetClientPlayer.cs:141-251`) : `LayerTitle.KillActor` est mis en file
   (l. 243) : l'écran de création a instancié `LayerTitle.actor` (`LayerEditBio.cs:21-24`), à détruire après.

## 2. Ce que fait `LayerEditBio` dans le jeu

- Besoin : un `Game` en mémoire dont `pc` est le personnage à éditer (`LayerEditBio.cs:25` : `SetChara(ELayer.pc)`).
  S'il n'y en a pas, il en crée un (l. 17-20). S'il y en a un, il édite SON `pc` : ouvert avec un monde chargé, il
  modifierait le personnage de l'autre joueur. `SetChara(Chara c, UnityAction onKill)` (l. 31-39) accepte un autre
  personnage, mais `UICharaMaker` lit `EMono.pc` et `EMono.player` (`UICharaMaker.cs:165, 282, 318, 331, 339, 383` :
  tooltips, `RefreshDomain`, choix de domaine) et `EMono.game.idPrologue` (l. 74, 139, 197) : il faut que `player.chara`
  soit ce personnage, donc un `Game` à part ou l'échange de `player.chara` dans le monde chargé (dangereux : non essayé).
- Produit : le personnage modifié en place (race, métier, apparence, nom, bio), rien de sauvegardé. Le bouton d'origine
  ouvre `LayerWorldSetting` (l. 41-47) puis `Game.StartNewGame` (`Game.cs:824-833`) + `Player.OnStartNewGame`
  (`Player.cs:1456`) qui font le reste (équipement de départ, quête `main`, zone de départ) : rien de tout cela ne sert
  ici, le monde existe déjà. Le mod ne garde que le personnage (`Ready()`) et refait lui-même le départ (point 1.5).
- Écran titre ou monde chargé : conçu pour l'écran titre (`LayerTitle.Update` atténue son décor quand le layer existe,
  `LayerTitle.cs:164-185`). Ouvert sur un monde chargé : non vérifié que l'affichage soit propre (la scène est `Zone`).
- `Game.Kill` (`Game.cs:1131-1146`) : si `core.IsGameStarted` (= `game.activeZone != null`, `Core.cs:86-95`) il défait
  l'interface et la scène, puis `core.game = null`. `Game.Load` (`Game.cs:322-361`) le fait déjà pour le monde en cours.
- `Game.Load` : `GameIO.LoadGame` écrit `Game.id` (`GameIO.cs:155`), envoie `elin.game.pre_load` puis, à la fin (après
  `scene.Init(StartGame)`, qui active déjà la zone), `elin.game.post_load` : c'est là que tourne `[ElinPostLoad]`
  (`RemoveLeftOverCharas`, `ElinNetHostPlayerManager.cs:333`) ; le branchement de l'attribut est dans `ElinModdingKit` (non lu).

## 3. Garder quelque chose entre deux chargements

- Une variable `static` ordinaire survit à `Game.Load` : même processus. Le mod le fait déjà et efface à la main ce qui
  ne doit pas survivre, par `[ElinPreLoad]` (`CardCache.cs:192`, `RemoteCardHelper.cs:12`, `WorldStateSnapshot.cs:33`) ou à
  l'écran titre (`[ElinPostSceneInit]`, `GameSaveLoad.cs:42-48`). Exemples d'état gardé exprès : `SaveDepot._unsent`,
  `_saves`, `_descends`, `_nextBeat`, `_lostTold` (`SaveDepot.cs:49-63`) ; `NetSession.Instance` (un composant).
- Les propriétés `[ElinGameIOProperty]` (`PcOwners`, `PcOrphans`, `SavedRemoteCharas`, `PlayerStandings`...) sont
  relues dans le fichier `chunks/context_vars.chunkc` du dossier de la sauvegarde (LZ4 + JSON, vu sur `world_depot`,
  475 octets) à chaque chargement : une valeur changée en mémoire et pas sauvegardée est perdue au rechargement
  (c'est pourquoi `RemoveLeftOverCharas` fait `game.Save(false, true)` avant `Game.Load`, l. 340-341). Ne PAS mettre
  le personnage en attente dans une de ces propriétés : il serait écrit dans le monde.
- Le personnage en attente se garde donc dans un champ `static` (octets `LZ4Bytes.Create(pc)` + fame/karma du `Game`
  temporaire), consommé (remis à nul) dès son adoption : c'est le garde-fou contre la boucle.

## 4. Où est le trou, exactement

`TakeOverPc` (`ElinNetHostHandOver.cs:125-249`) : l. 134 `mine = OwnCharaOf(me) ?? Orphan()` ; l. 135-141 si `mine` est nul,
`SetPcOwner(me)` seulement quand `formerOwner == 0` ; si `formerOwner` est un AUTRE connu (cas du trou), `return false` :
le jeu continue avec le personnage de l'autre. C'est ce cas-là, et seulement lui (`mine is null && formerOwner != 0 &&
formerOwner != me && !SavedRemoteCharas.ContainsKey(me)`), qui déclenche la création. L'échange (l. 160-247) marche déjà
dès que `mine` existe ET que `PlayerStandings[mine.uid]` existe (l. 165 : sinon fame, karma et quêtes ne sont pas échangés).
La garde `Session.Transport is null && !EmpServer.Requested` (`ElinNetHostPlayerManager.cs:337`) reste : jamais en session
ni sur un serveur sans joueur.

Le test qui joue déjà ce cas sans le savoir : `depot_suite.py` D2 (l. 590-604) : A, jamais venu, prend le monde que H a mis
au dépôt. Aujourd'hui A y joue le personnage de H. Avec la création, D2 à D6 changent (voir B ci-dessous).

## 5. Trois façons de faire

### A. La plus petite : sans écran titre, `Kill` puis écran puis rechargement
Fichiers : `ElinNetHostHandOver.cs` (branche du trou), `ElinNetHostPlayerManager.cs` (adoption sortie en fonction), un champ static.
Événements : 1 `Take`/`Load` charge le monde ; `PostLoad` voit le trou, note `_pending = {id du monde}` ; au tour suivant
`game.Kill()` (scène restée `Zone`, jeu nul) ; `ui.AddLayer<LayerEditBio>()` (crée un `Game` temporaire, `Game.id` change) ;
clic : on garde le personnage + fame/karma du `Game` temporaire, `Kill`, `core.game = null`, `KillActor` ; `Game.Load(id)` ;
`PostLoad` : adoption ; `TakeOverPc` (échange, sauvegarde, 3e chargement).
Joueur : le monde de l'autre apparaît une seconde, puis l'écran de création, puis le monde avec son personnage.
Risques : scène `Zone` avec jeu nul (les widgets lisent `game` : non vérifié, `Scene.cs:520` protège seulement la boucle de
zone) ; pas de `LayerTitle` sous l'écran ; `Holding` (`SaveDepot.cs:99`) devient faux tant que le jeu est nul : plus de
battement (`SaveDepot.cs:670-684`), le verrou d'un dépôt dossier expire en 3 min (`_lockLife`, l. 37) ; serveur et GitHub :
non vérifié. Annulation (Échap) : il faut décider (voir B). Je ne la recommande pas.

### B. Recommandée : par l'écran titre, comme le client qui rejoint
Fichiers : `ElinNetHostHandOver.cs` (détection + adoption locale), `ElinNetHostPlayerManager.cs` (sortir l.246-291 en
`AdoptNewPlayerChara(Chara)` qui renvoie le personnage, partagée avec `OnSessionNewPlayerResponse`), un nouveau
`ElinNetHostLocalCreation.cs` (écran + état), `SaveDepot.cs` (une fonction `internal` pour le rechargement, voir risques),
texte `package/LangMod` (message d'échec/annulation, si besoin), `depot_suite.py`.
Événements :
1. `Take`/`Load` charge le monde ; `PostLoad` : `TakeOverPc` voit le trou -> note `_pending = {Game.id}`, ne fait rien d'autre.
2. Tour suivant : `scene.Init(Scene.Mode.Title)` (`Game.Kill` fait par la scène ; `ReleaseAtTitle` rend le verrou du dépôt,
   `SaveDepot.cs:693-715`, ce que fait déjà `Put`, l. 310).
3. Écran : même code que `OnSessionNewPlayerRequest` (retirer le bloc `Mode`, remplacer le clic). Au clic : copier le
   personnage (`LZ4Bytes.Create(pc)`), `player.fame`/`karma` du `Game` temporaire, `game.Kill()`, `core.game = null`,
   `ui.RemoveLayer`, `core.actionsNextFrame.Add(LayerTitle.KillActor)`.
4. Rechargement : si `id == SaveDepot.WorldId` -> `SaveDepot.Take()` (reprend le verrou : si un autre l'a pris pendant la
   création, le jeu le dit « X héberge » et le personnage reste en attente) ; sinon `Game.Load(id, false)` (jamais `Take` sur
   une sauvegarde locale).
5. `PostLoad` : `_pending` présent pour ce `Game.id` -> le consommer, `AdoptNewPlayerChara` (sans `SendSaveProbe`, sans
   `MakeAlly` ni `MoveZone` : `TakeOverPc` met le personnage dans le groupe, l. 199-203), `SavedRemoteCharas[me] = uid`,
   `PlayerStandings[uid] = [0, 30]`, `GiveAxeToRemotePlayer` (même départ qu'un invité), puis `TakeOverPc` : échange, copie de
   secours (l. 151), sauvegarde, 3e chargement. Le joueur arrive dans le monde avec son personnage, l'autre attend (règle 3).
Ce que voit le joueur : « Prendre le monde » -> monde de l'autre (1-2 s, déjà vrai pour l'échange) -> titre -> écran de
création du jeu -> monde, son personnage.
Risques :
- Perte : le personnage n'est écrit dans le monde qu'à l'étape 5, avec une copie de secours avant ; fermer le jeu pendant
  l'écran = rien n'est écrit, le prochain chargement redemande l'écran. Jamais de doublon : `_pending` est remis à nul avant
  l'adoption, et `SavedRemoteCharas[me]` existe ensuite (`mine` non nul : plus de trou).
- Boucle : si l'adoption échoue (exception) ou si `TakeOverPc` refuse (l. 144-158, copie de secours impossible), ne PAS
  rouvrir l'écran : message `Dialog.Ok`, et jouer comme aujourd'hui. Garder un drapeau « déjà demandé pour ce Game.id ».
- Annulation : Échap ferme l'écran (même `SetOnKill` que le client, l. 131-135). Choix proposé : rester à l'écran titre,
  rien de chargé, rien d'écrit, verrou déjà rendu (étape 2). Non vérifié : que la fermeture de `LayerEditBio` ne laisse pas
  `LayerTitle.actor` ni le `Game` temporaire.
- Temp : `Game.Create` vide `GameIO.Temp` ; sans effet ici (rien de joué entre les deux chargements, titre atteint avant).
- Les 3 chargements d'un coup (charge, retour titre, recharge, échange) : lent mais sans état intermédiaire joué.
- `EmpBot.cs:81` clique tout seul sur tout `LayerEditBio` : le bot validera la création, c'est voulu pour ses tests.
Test (`depot_suite.py`) : `take(A)` (l. 172) puis, au lieu de `loaded(A)` (l. 177, vrai dès le premier chargement : à ne
pas utiliser seul), attendre `EClass.ui.GetLayer<LayerEditBio>() != null` avec `eventually`, cliquer `EMBARK`
(`mp_test.py:35-37`, importable : `join_client` l. 123-145 le fait déjà), puis attendre `sceneMode == "Zone"` et
`EClass.pc.uid` différent de `uid_h`. Vérifier : `pc` de A n'est pas celui de H, H est resté dans le monde (`info()`,
l. 404), `pc_owner` = A, `remote_chara[H]` = uid de H, copie de secours faite. Cas à ajouter : annulation (`layer.Close()`
-> titre, `SavedRemoteCharas` sans A, verrou libre) ; retour de H pendant que A joue (rien ne change). D2 à D6 existants :
ajouter l'étape création dans D2 ; D4 (« A change quelque chose », l. 639) et D5 (H retrouve le changement, l. 687)
doivent être relus (H reprend alors SON personnage, pas celui de A).

### C. La plus propre : décider AVANT le premier chargement
Idée : un `[HarmonyPrefix]` sur `Game.Load(string, bool)` lit `chunks/context_vars.chunkc` du dossier avant de charger
(`pc_owner`, `remote_chara`, `pc_orphan`), voit le trou, ouvre l'écran d'abord (jeu nul, écran titre, aucun monde chargé), puis
charge UNE fois ; `PostLoad` adopte et échange (le rechargement d'échange existant : 2 chargements au lieu de 3).
Fichiers : comme B + un lecteur de `context_vars.chunkc` (format LZ4 maison d'`ElinModdingKit`, non lu : non vérifié, à
décoder à la main ou à appeler par réflexion), le préfixe, le point d'entrée annulation du dépôt (rendre le verrou pris par `Take`).
Ce que voit le joueur : jamais le personnage de l'autre. Pas de verrou rendu puis repris.
Risques : la règle `PcOwner()` (l. 58-66) a besoin de `player.uidChara` et de l'existence du personnage, qu'on ne connaît
qu'une fois le monde lu : la règle serait écrite deux fois (avant et après) et peut diverger -> un joueur qui revient sur un
vieux monde pourrait voir l'écran à tort. Annulation : il faut rendre le verrou (`Take` l'a déjà pris, `SaveDepot.cs:164-222`).
Même test que B, sans le premier `Zone`. Coût élevé pour un gain visuel de quelques secondes.

## 6. Recommandation

1. Faire B : détection exacte déjà dans `TakeOverPc` (une seule règle), écran du jeu par le chemin que le client utilise déjà.
2. Sortir l'adoption (`OnSessionNewPlayerResponse` l. 246-291) en une fonction commune ; ne pas appeler `SendSaveProbe`,
   `MakeAlly`, `MoveZone` ; écrire `PlayerStandings[uid] = [0, 30]` avant l'échange ; donner la hache comme à un invité.
3. Recharger par `SaveDepot.Take` pour `world_depot` (reprend le verrou rendu au titre), par `Game.Load` sinon.
4. Garder le personnage en attente dans un `static` (jamais dans une `[ElinGameIOProperty]`), consommé avant l'adoption,
   plus un drapeau « déjà demandé » : pas de boucle, pas de doublon ; échec ou annulation : message ou titre, jamais de silence.
5. Test rouge d'abord dans `depot_suite.py` (D2 : A voit l'écran, valide par `EMBARK`, joue un autre uid que H), puis annulation
   et retour de H ; à dire à l'utilisateur : la création se fait à la première prise d'un monde déjà joué par un autre.
