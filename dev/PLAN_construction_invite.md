# Mode construction d'un invité : les faits (lignes 1, 3 et 4 de `PLAN_chasse_differences_2.md`)

Écrit le 2026-10-05 par **lecture seule** : jeu décompilé EA 23.352 (`dev/_decomp/Elin/*.cs`, refait pour cette version),
mod `ElinTogether/`, bancs `dev/_tools/`. **Rien compilé, rien joué.** Chaque fait a son `fichier:ligne` ; ce que le code
ne permet pas d'affirmer est écrit « non vérifié ». Les numéros de ligne du plan (23.351) ont été revérifiés : ils
restent justes, sauf `AM_Designation.cs:93-99` (en fait 93-101), `GoalTask.cs:69-90` (en fait 67-95) et
`Card.cs:8288` (`SetDeconstruct` est à `Card.cs:8296`). `MOD` = `ElinTogether/ElinTogether/`, `JEU` = `dev/_decomp/Elin/`.

## 0. Ce que la lecture change dans le plan (à lire d'abord)

1. **En jeu normal, il n'y a pas de « marque » en attente.** `Player.instaComplete` vaut `true` au départ
   (`JEU/Player.cs:1228`, pas de `[JsonProperty]` : jamais sauvé) et le bouton qui le coupe est caché hors mode debug
   (`HotItemToggle.cs:34-36`). Tout geste du mode construction est donc fait **tout de suite** par un personnage
   invisible, « l'agent » (`Player._agent`, nommé « stash », `Player.cs:1440-1441`) : la marque existe quelques
   instructions puis est détruite (`AM_Designation.cs:88-101`).
2. **Personne n'exécute une marque dans ce jeu.** Les listes `mine/dig/cut/harvest/build/moveInstalled`
   (`TaskManager.cs:7-26`) n'ont qu'un lecteur : `GoalTask.TryAssignDesignations` (`GoalTask.cs:67-95`). Or `GoalTask`
   n'est **créé nulle part** dans le jeu décompilé (grep `GoalTask` : seulement son propre fichier ; aucun `new GoalTask`,
   aucun numéro `ABILITY` ; 23.351 identique). Les habitants travaillent par leurs métiers (`GoalWork`, `AIWork*`), qui ne
   lisent pas les marques (`AIWork_Lumberjack.cs` : coupe tout arbre, sans marque). Donc **l'option « envoyer les marques
   pour que les habitants de l'host les exécutent » (c) n'a rien à faire exécuter** tant que le jeu n'a pas de lecteur
   (non vérifié en jeu : il faudrait poser une marque par le menu et regarder si quelqu'un vient).
3. **Chez l'invité, c'est pire que « rien ne se construit chez l'host »** : les constructions (sol, mur, meuble neuf) ne
   se font **même pas chez lui** (`CharaProgressCompleteEvent.cs:73`, voir §2). Les gestes miner / creuser / couper se
   font **chez lui seulement** : sa carte diverge de celle de l'host sans que personne ne le sache.
4. **Qui paie quoi chez l'invité** (déduit du code, non vérifié en jeu) : l'**or** part (10 par case, l'host le retire de
   son personnage) ; les **matériaux ne descendent probablement pas** (`CardModNumEvent.cs:13-18` annule tout `ModNum` d'un
   objet connu de l'host chez un invité). Le plan disait « or, matériaux ».

---

## 1. Comment marche le mode construction en solo

### 1.1 Entrer dans le mode

- Barre d'actions n°3, remplie par `HotbarManager.cs:70-184` : elle n'a des boutons que si l'on est dans une zone avec une
  base (`EClass.Branch != null`, soit `core.game.activeZone.branch`, `EClass.cs:23`) ou en mode debug
  (`godBuild`/`ignoreBuildRule`, `HotbarManager.cs:77`). Boutons selon les éléments de la base : « Inspect » = 4006
  (`HotbarManager.cs:80`), Couper = 4000, Miner et Creuser = 4001, Terrain = 4002, Démonter (déposer) = 4004 ; Copier et
  Peupler : debug seulement (`HotbarManager.cs:77-112`).
- Bouton « Inspect » : `HotItemActionMode.Execute` (`HotItemActionMode.cs:14-27`) → `BuildMenu.Toggle()`
  (`BuildMenu.cs:93-113`) → `ActionMode.Inspect.Activate()` (ou `Terrain` si la base n'a pas 4006, `BuildMenu.cs:113`).
  Les autres boutons : `ActionMode.Cut/Mine/Dig/…Activate` (`HotItemActionMode.cs:28-78`). `ActionMode.Activate`
  (`ActionMode.cs:339-411`) montre le menu de construction (`BuildMenu.Activate`, `ActionMode.cs:384`).
- Le menu de recettes (`BuildMenu.cs:508-541`) : un clic sur une recette appelle `ActionMode.Build.StartBuild(recette,
  bouton)` (`BuildMenu.cs:534`, `AM_Build.cs:164-177`) ; l'onglet « area » appelle `ActionMode.CreateArea.SetArea` puis
  `Activate` (`BuildMenu.cs:471-474`). Le menu liste : les recettes **connues** du joueur (`BuildMenu.cs:580`), les objets du
  **stock de la carte** (`EMono._map.Stocked`, `BuildMenu.cs:596`) et ceux du **sac du joueur** (`EMono.pc.things`,
  `BuildMenu.cs:611`) : ces deux derniers sont des recettes « `UseStock` » (on déplace l'objet existant, `Recipe.cs:184`,
  `Recipe.cs:547-558`).
- **Le clic** : `BaseTileSelector.OnUpdate` → `TryProcessTiles(case)` (`BaseTileSelector.cs:241-279`) :
  `mode.CanProcessTiles()` (:247) → `mode.OnBeforeProcessTiles()` (:257) → pour chaque case valide
  `mode.OnProcessTiles(case, dir)` (:264 pour une case, :363 pour une zone rectangulaire) → `mode.OnAfterProcessTiles` (:273)
  → **`ExecuteSummary()` (:275)** qui appelle `HitSummary.Execute()` (`BaseTileSelector.cs:471-478`) = **le paiement** →
  `mode.OnFinishProcessTiles()` (:277). `ExecuteSummary` ne fait rien s'il n'y a pas de `BuildMenu.Instance` (:473).
  Les cases valides sont comptées à l'avance, au survol, par `RefreshSummary` (:482-490, lit `Scene.HitPoint` = la souris).

### 1.2 Le paiement (`HitSummary`, commun à tous les gestes)

- `HitSummary.CanExecute` (`HitSummary.cs:44-106`) : assez d'or (`EClass.pc.GetCurrency() < money`, :50) et assez de
  matériaux pour `countValid` cases ; recette « stock » : un objet par case (:99).
- `HitSummary.Execute` (`HitSummary.cs:108-144`) : `EClass.pc.ModCurrency(-money)` (:112), puis, **seulement si le geste est
  instantané** (`CanInstaComplete` du type de tuile **ou** `instaComplete`, :122), retire les matériaux : `thing.ModNum(-n)`
  (:141). Les ingrédients sont lus dans le sac du joueur puis le stock de la carte (`Recipe.Ingredient.RefreshThing`,
  `Recipe.cs:68-87`). Tout passe par `EClass.pc` : **c'est le joueur de cette fenêtre qui paie, jamais un autre**.
- Or par case : `CostMoney` = 10 pour Miner, Creuser, Couper (`AM_Mine.cs:9`, `AM_Dig.cs:7`, `AM_Cut.cs:3`) et pour Construire
  sauf recette « stock » (0, `AM_Build.cs:20-30`). Rien pour : déplacer, zones, démonter (déposer), terrain
  (`ActionMode.CostMoney` = 0, `ActionMode.cs:211`). Copier/Plan : `partialMap.value` (`AM_Copy.cs`, debug seulement).
  L'or n'est compté que si le geste est instantané et pas « forcé » (`AM_Designation.cs:114-116`). Échelles et échafaudages
  (`TileTypeLadder.cs:5`, `TileTypeScaffold.cs:9`) sont toujours instantanés et gratuits.

### 1.3 Les gestes, un par un

Tous les gestes « tâche » passent par `AM_Designation<T>.OnProcessTiles` (`AM_Designation.cs:85-101`) : crée la tâche (le
« moule »), `list.TryAdd` la pose dans `Map.tasks.designations.<liste>` (`TaskList.cs:34-63`, `DesignationList.cs:15-31`),
puis, si instantané (:94, = toujours en jeu normal, §0.1) : `tâche.owner = EClass.player.Agent` (:96), l'agent est posé sur la
case (:97), **`tâche.OnProgressComplete()` (:98)**, `tâche.Destroy()` (:99). Rien n'est « à la main » : l'agent n'a ni
animation ni délai. Tableau :

| Geste (mode) | Menu / mode | Paiement | Tâche | Qui | Ce qui change à la fin |
|---|---|---|---|---|---|
| Poser sol, mur, pont, déco, objet de terrain | `AM_Build` (`AM_Build.cs`), recette de tuile | or 10 × cases + matériaux de la recette, au `ExecuteSummary` | `TaskBuild` (`TaskBuild.cs:285-397`) | agent, tout de suite | `Recipe.Build` (`Recipe.cs:645-733`) : `Map.SetFloor` (:701), `SetBlock` (:673, après `SetObj` :671 pour ôter l'objet), `SetBridge` (:711), `SetDeco` (:704), `SetObj` (:716 et suite), `SetRoofBlock` (:665, si Alt tenu), puis `RefreshShadow/FOV`, `Kick` des personnages dessus (`TaskBuild.cs:369-391`) |
| Poser un meuble neuf | `AM_Build`, recette de carte (`RecipeCard`) | or 10 + matériaux | `TaskBuild` | agent | `RecipeCard.Build` (`RecipeCard.cs:399-459`) : **crée l'objet** (`ThingGen.Create`, :436), `Zone.AddCard` (:469), `SetPlaceState(installed)` (:475), `isPlayerCreation`, `ignoreStackHeight = Input.GetKey(Ctrl)` (:482) |
| Poser un objet pris au stock ou au sac | `AM_Build`, recette `UseStock` / `IngAsProduct` | 0 or ; l'objet est consommé (`Split(1)`, `RecipeCard.cs:416`) | `TaskBuild` | agent | même fin que le meuble, avec l'objet existant |
| Poser en tenant l'objet (clic droit, hors menu) | `HotItemHeld` (`HotItemHeld.cs:265-282`) | l'objet (`ModNum(-1)`, `TaskBuild.cs:304-306`) | `TaskBuild` avec `held` | **le joueur** (marche jusqu'à la case) | idem ; `AM_Adv`, pas le mode construction |
| Miner | `AM_Mine` (`AM_Mine.cs`) ou clic sur un mur → menu « Mine » (`InspectGroupBlock.cs:24-34`) | or 10 | `TaskMine` (`TaskMine.cs:139-189`) | agent | `Map.MineBlock` (`Map.cs:1808`, appelé `TaskMine.cs:152`) : `SetBlock` vide, pierres (`DropBlockComponent`, `Map.cs:1767` → `TrySmoothPick`), pièces au hasard, objet de mur ; mode « rampe » : `MineRamp` (`TaskMine.cs:161`) |
| Creuser / ôter un sol | `AM_Dig` | or 10 | `TaskDig` (`TaskDig.cs:148-247`) | agent | `Map.MineFloor` (`Map.cs:1892`, `TaskDig.cs:175,213`) : sol → terre, ou pont retiré (`SetBridge`) |
| Couper (arbre, herbe) | `AM_Cut` ou clic sur un objet → « Cut » (`InspectGroupObj.cs:20-30`) | or 10 | `TaskCut` (`TaskCut.cs:67-71`) | agent | `Map.MineObj` (`Map.cs:1980`) : objet de case ôté, ressources lâchées |
| Récolter | `AM_Harvest` : **aucun bouton ne l'ouvre** (grep `ActionMode.Harvest` : rien ; pas de cas « Harvest » dans `HotItemActionMode.cs`) | — | `TaskHarvest` | — | atteignable seulement à la main (outil tenu), `TaskHarvest.cs:386` |
| Déplacer un meuble installé | `AM_Inspect` (= `AM_MoveInstalled`, `AM_Inspect.cs:3`) : 1er clic choisit (`SetTarget`, `AM_MoveInstalled.cs:157`), 2e clic pose (`:247-300`) | 0 or | `TaskMoveInstalled` (`TaskMoveInstalled.cs:92-116`) | agent (`instaComplete`, `AM_MoveInstalled.cs:67`) | `Zone.RemoveCard` puis `Zone.AddCard` à la nouvelle case (:97-98), `SetPlaceState` (:108/112), `altitude` (:114) |
| Ranger un meuble (« Démonter » du bouton) | `AM_Deconstruct` (`AM_Deconstruct.cs:60-93`) | 0 | aucune | immédiat | `Map.PutAway` (`Map.cs:2718`) : l'objet part au stock (`TryAddThingInSpot`) ou dans le sac du joueur (`EClass.pc.Pick`) |
| « À démonter » (menu d'un objet) | `InspectGroupThing.cs:59-62` | 0 | aucune, un **drapeau** `isDeconstructing` + liste `Map.props.deconstructing` (`Card.cs:8296-8309`) | **personne** : le seul lecteur est `AI_Deconstruct` lancé par `GoalTask` (`GoalTask.cs:26-28`, mort) | — |
| Zone de base : créer, agrandir, rétrécir, effacer | `AM_CreateArea` (`AM_CreateArea.cs:43-46`), `AM_ExpandArea` (`:57-66`), `AM_EditArea` « delete » (`AM_EditArea.cs:44`) | 0 | aucune | immédiat | `RoomManager.AddArea` (`RoomManager.cs:76`) / `Area.AddPoint/RemovePoint` (`Area.cs:27,36`) / `RemoveArea` (`RoomManager.cs:103`). Les zones sont dans le fichier carte (`Map.rooms`, `[JsonProperty]`, `Map.cs:30-34`) |
| Enlever une marque | `AM_RemoveDesignation` (`:30-32`) | 0 | — | immédiat | `TryRemoveDesignation` (`TaskManager.cs:47-58`) |
| Terrain (monter / descendre / aplanir) | `AM_Terrain` (élément 4002) | 0 | aucune | immédiat, **règle `cell.height` directement** (`AM_Terrain.cs:62-100`) | aucun appel `Map.Set*` : rien à intercepter |
| Copier / coller un plan, peupler, marqueurs | `AM_Copy`, `AM_Blueprint`, `AM_Populate`… | `partialMap.value` | — | immédiat | `PartialMap.Apply` (`AM_Copy.cs:123`) : **debug seulement** (`HotbarManager.cs:77`), hors sujet |

Remarques :
- **Hors instaComplete** (debug seulement) : la marque reste dans la liste, l'agent n'exécute rien, `HitSummary.Execute` ne retire
  ni matériaux ni or pour les types de tuile non instantanés (`HitSummary.cs:122`). Personne ne l'exécute (§0.2). Ce chemin n'est
  pas celui d'un joueur ; il n'est pas à traiter.
- Un `TaskBuild` « tenu » (clic droit avec l'objet) est le seul geste de construction fait **par le personnage du joueur** : c'est
  pour lui que le mod a écrit `CharaBuildDelta` (§2).
- Le 2e `OnProcessTiles` d'une boîte (`BaseTileSelector.cs:281-333`) refait un `TryAdd` par case ; si la case a déjà une marque,
  `TryAdd` refuse et `AM_Designation.cs:93` exécute **la dernière marque de la liste** : détail du jeu, non vérifié, sans objet ici.

### 1.4 Ce qui est lu sur la machine de celui qui clique (à garder pour toute correction qui rejoue ailleurs)

`Input.GetKey(LeftAlt)` = « mode toit » (`AM_Build.cs:74-90`, lu par `Recipe.Build` à `Recipe.cs:663` et `RecipeCard.cs:487`) ;
`Input.GetKey(LeftControl)` (`RecipeCard.cs:53,482`, `TaskMoveInstalled.cs:115`) ; `EClass.pc` pour l'or et les ingrédients
(`HitSummary.cs:50,112`, `Recipe.cs:72-81`) ; `ActionMode.Build.IsActive/IsFillMode/IsRoofEditMode` pour la fin d'un `TaskBuild`
(`TaskBuild.cs:317,380`) ; `EClass.pc.PickOrDrop` quand l'agent mine (`Map.cs:1951-1953` : si l'acteur est l'agent, c'est `EClass.pc` qui ramasse). Rejouer le geste chez l'host le ferait donc payer et ramasser **par l'host**, et lire **ses**
touches.

---

## 2. Ce que le mod fait aujourd'hui, geste par geste

### 2.1 Pièces du mod concernées

- **`CharaProgressCompleteEvent`** (`MOD/Patches/DeltaEvents/Chara/CharaProgressCompleteEvent.cs`) : patche tout
  `OnProgressComplete` d'un `AIProgress` **et celui de `TaskBuild`** (:47-52). Avant (:55-74), si la partie est en réseau : note
  l'acteur (:61-63). Pour un `TaskBuild` : **un client qui n'est pas en train d'appliquer un delta ne l'exécute jamais**
  (`return connection.IsHost || ElinDelta.IsApplying`, :73). Seule exception envoyée : un `TaskBuild` **avec objet tenu** du
  personnage joueur → `CharaBuildDelta` à l'host (:69-71). Après (:76-129) : l'host renvoie à tous les effets « rangés »
  pendant la fin (objets créés, états posés) ; pour un `TaskBuild` sans objet tenu (= mode construction de l'host), seulement ces
  effets (:105-107) ; pour une tâche à progression (`TaskCut/Mine/Dig…`) un `CharaProgressCompleteDelta` (:113-129).
- **`CharaBuildDelta`** (`MOD/Models/Delta/Chara/CharaBuildDelta.cs`, union 210) : objet tenu, personnage, case, direction,
  altitude, hauteur de pont, effets (:11-33). L'host le rejoue (`taskBuild.OnProgressComplete()`, :71) en rangeant les effets
  (:68-76) puis le renvoie à tous ; un client le rejoue chez lui (:79) : **c'est le seul chemin qui change le terrain des deux
  côtés** (`Recipe.Build` rejoué = `SetFloor`, `SetBlock`… chez chacun). Il exige un objet tenu (`Held`, :12, :38-40).
- **`CharaTaskRemoteEvent`** (`.../CharaTaskRemoteEvent.cs`) : tout `Chara.SetAI` d'un personnage joueur devient un
  `CharaTaskDelta` (:184-187). Table (:63-177) : `TaskCut` (:69), `TaskDig` (:70), `TaskHarvest` (:74), `TaskMine` (:75),
  `TaskPlow/PourWater/Water/ChopWood` (:76-81) existent ; **`TaskBuild`, `TaskBaseBuild`, `TaskDesignation`, `TaskMoveInstalled`,
  `TaskPoint`, `BaseTaskHarvest` sont commentés** (:79-87) → `FakeTask` (:176). Les arguments : `TaskCutArgs`, `TaskMineArgs`,
  `TaskDigArgs` (avec `Mode`), `TaskHarvestArgs` (`MOD/Models/Delta/Task/`), numéros 102-107, 226 (`TaskArgsBase.cs:7-54`).
  **`TaskBuildArgs` n'existe pas.** Ces envois ne se font que pour une tâche donnée **au personnage** (`SetAI`) : **le mode
  construction n'appelle jamais `SetAI`** (il appelle `OnProgressComplete` de l'agent, §1.3), donc aucun de ces envois n'a lieu
  pour un geste de menu.
- **Pour une tâche faite à la main** (`SetAI(TaskMine)` etc.) : le client l'envoie, l'host la fait jouer par le personnage
  distant, et à la fin renvoie `CharaProgressCompleteDelta` ; chaque jeu **rejoue `OnProgressComplete`** de sa copie de la
  tâche (`CharaProgressCompleteDelta.cs:62-72`) : le terrain change donc **par rejeu chez chacun**, pas par un état envoyé
  (voir §3). `TaskCache.GetRequiredPos` (`MOD/Models/Pending/TaskCache.cs:10-17`) refuse deux joueurs sur la même case pour
  `BaseTaskHarvest`, `TaskCut`, `TaskChopWood` (pas `TaskBuild`).
- **`ZoneAddCardEvent`** (`MOD/Patches/DeltaEvents/Zone/ZoneAddCardEvent.cs`) : chez l'host, pendant un `TaskBuild`, l'objet
  ajouté à la carte est rangé dans les effets (:21-31) ; chez un client, un objet **inconnu de l'host** est détruit au tick
  suivant (:33-41, `CardCache.DelayDestroy`) ; sinon (:48-53) `ZoneAddCardDelta` envoyé (le client l'envoie à l'host, l'host
  l'applique et le renvoie, `ZoneAddCardDelta.cs:42-57`).
- **`CardSetPlacedStateEvent`** (`.../CardSetPlacedStateEvent.cs`) : pendant un `TaskBuild`, l'état « posé » est rangé dans les
  effets (:75-89) ; en dehors, `CardPlacedDelta` envoyé et, **chez un client, l'original est sauté** (`return connection.IsHost`,
  :105) : le client attend le retour de l'host. Commentaire ligne 95-97 : « so clients can help with placing stuff ».
- **Aucun patch** sur : `Map.Set*`, `MineBlock/MineFloor/MineObj` (sauf `CharaDestroyPathDelta` qui les **appelle**,
  `CharaDestroyPathDelta.cs:33-51`), `Cell`, `Point`, `TaskDesignation`, `TaskManager`, `RoomManager`, `Area`, `ActionMode`,
  `BuildMenu`, `HitSummary`, `HotbarManager`, `Card.SetDeconstruct`. Grep dans `MOD/` de `designation`, `AddArea`,
  `RemoveArea`, `isDeconstructing`, `SetDeconstruct`, `rooms`, `tasks`, `TaskManager`, `ActionMode.Build` : rien d'utile (seul
  `Emp/EmpBot.cs:396` pose `ActionMode.Build.recipe` pour imiter un clic de pose tenue). Le commentaire de
  `CharaDestroyPathDelta.cs:7-11` le dit : « Terrain has no delta of its own ». `dev/_tools/build_suite.py:135` aussi
  (« le terrain n'est pas synchronisé »).
- **Argent et matériaux** : `CardModCurrencyEvent.cs:58-77` : tout `ModCurrency` d'un joueur client est envoyé à l'host
  (`CardModCurrencyDelta`, union 302, `:71-87` : l'host déduit sur la copie du personnage de ce joueur, sous `Simulate`),
  la copie locale attend le retour de l'host. `CardModNumEvent.cs:13-18` : chez un client, `Card.ModNum` d'un objet **connu de
  l'host** (`IsResolved` = client et objet à numéro de l'host, `CardCache.cs:224`) est mis à 0 et sauté ; rien n'est envoyé
  (le postfixe, :24, sort si `a == 0`).
- **Rien ne retient l'invité d'entrer en mode construction** : aucun patch d'`ActionMode`/`BuildMenu`/`HotbarManager`. Il a les
  boutons de la barre n°3 si la base qu'il a chargée de l'host a les éléments 4000-4006 (`HotbarManager.cs:77-112`) ; le mod
  rafraîchit la barre quand l'host change ces éléments (`BaseStateDelta.cs:96-106`). Le client charge la sauvegarde de l'host
  (`ElinNetClientPlayer.cs:187-206`), donc `Player._agent` est celui de l'host (non vérifié ; s'il était nul,
  `AM_Designation.cs:96-97` lèverait une exception à chaque geste).

### 2.2 Geste par geste (état prévu d'après le code ; **rien joué**)

| Geste | Chez l'**invité** | Chez l'**host** | Envoyé ? | Qui paie | Résultat pour l'autre |
|---|---|---|---|---|---|
| Sol / mur / pont / déco (menu) | `ExecuteSummary` paie ; `TaskBuild.OnProgressComplete` **sauté** (`CharaProgressCompleteEvent.cs:73`) : rien posé, même pas chez lui | l'host construit, `Map.Set*` chez lui seul | non | invité : or part (via host), matériaux probablement pas ; host : son propre sac | l'invité ne voit pas les sols de l'host (ligne 4) ; l'host ne voit rien de l'invité (ligne 1) |
| Meuble neuf (menu) | idem : rien posé | objet créé : `CardGenDelta` + `ZoneAddCardDelta` + `CardPlacedDelta` rangés puis envoyés (`CharaProgressCompleteEvent.cs:105-107`) | **host → invité : oui** | host | l'invité voit le meuble de l'host posé (marche déjà : `build_suite.py` b1) ; l'inverse non |
| Objet du stock / du sac (menu) | idem | idem ; `Split(1)` fait chez l'host | host → invité : oui (non vérifié pour le « stock ») | host | idem |
| Pose en tenant l'objet | `CharaBuildDelta` envoyé, original sauté (:69-73) ; l'host rejoue, renvoie à tous, l'invité rejoue chez lui (`CharaBuildDelta.cs:79`) | `CharaBuildDelta` envoyé avec effets (:100-103), chacun rejoue | **oui, des deux côtés** (`build_suite.py` b2, b4, b5) | l'objet tenu (une fois) | les deux voient le sol / mur / objet posé |
| Miner | `TaskMine.OnProgressComplete` (non patché) : **mur ôté chez lui seulement** ; pierres perdues (`TrySmoothPick` client, `CharaPickThingEvent.cs:108-129`) ; or part | mur ôté chez lui ; pierres : `EClass.pc.PickOrDrop` (`CharaPickThingEvent.cs:77-106`, objets envoyés par delta) | non (le mur, non) | invité : or | l'invité marche dans un mur que l'host voit debout ; l'invité voit la pierre de l'host sans que le mur de l'host ne tombe |
| Creuser, couper | idem (`MineFloor`, `MineObj` chez lui seul) | idem | non | or | idem |
| Récolter | **sans bouton** | sans bouton | — | — | — |
| Déplacer un meuble installé | `RemoveCard` local puis `AddCard` : `ZoneAddCardDelta` envoyé à l'host (`ZoneAddCardEvent.cs:48-53`) ; `SetPlaceState` : `CardPlacedDelta` envoyé, original sauté | idem avec envoi à tous | **probablement oui** (non vérifié : `altitude` et `dir` posés par `TaskMoveInstalled.cs:114`) | personne | à tester (candidat de test, §5) |
| Ranger un meuble (`Map.PutAway`) | `RemoveCard` local puis `Pick` ou `TryAddThingInSpot` | idem | **non vérifié** (suite de `Pick` et `RemoveCard` : seul `CardRemoveThingDelta` existe) | personne | non vérifié |
| « À démonter » | drapeau chez lui seul (`SetDeconstruct`, aucun patch) | — | non | personne | sans effet visible (de toute façon personne ne lit la liste) |
| Zones de base | `AddArea/RemoveArea/AddPoint` chez lui seul | chez lui seul | non | personne | les habitants de l'host (qui lisent `Map.rooms` de l'host : zones de ferme, etc.) ne voient pas les zones de l'invité, et inversement |
| Terrain (monter/descendre) | `cell.height` chez lui seul | chez lui seul | non | personne | cartes qui divergent |

Où les écarts se réparent d'eux-mêmes : à la **prochaine entrée dans la zone** (§3.2), la carte de l'host écrase celle de
l'invité : ses murs ôtés « pour lui seul » réapparaissent, sans remboursement.

**Cas particulier du bail** : `NetSession.Connection => ZoneSession ?? (IsAway ? null : Transport)` (`MOD/Net/NetSession.cs:40`).
Dans une carte tenue par un invité (bail), celui-ci a une session « host » de la carte : les tests `Connection is ElinNetHost`
du mod y valent donc pour lui, et un host qui visite cette carte y est un `ElinNetClient { IsZoneSession: true }`
(commentaire de `Patches/Remote/RemoteBasePaidPatch.cs:11-20`). Toute correction doit donc demander « suis-je celui qui
simule cette carte ? », pas « suis-je l'host du monde ? ». Non vérifié en jeu pour le mode construction.

---

## 3. Comment les cases sont tenues à jour entre les jeux

### 3.1 Il n'y a pas de delta de case

Aucun delta ne porte un changement de **sol, bloc, objet de case (arbre, minerai), pont, toit, déco, liquide, hauteur**.
Union des deltas : `MOD/Models/Delta/ElinDelta.cs:7-130` (rien sur la carte). Les seuls chemins qui font changer les cases
des deux côtés :

1. **Rejeu d'une pose** : `CharaBuildDelta` (§2.1). Chaque jeu refait `Recipe.Build` chez lui : donc sol, mur, pont, déco,
   toit, objet de case selon la recette.
2. **Rejeu d'une tâche à la main** : `CharaProgressCompleteDelta` (`CharaProgressCompleteDelta.cs:26-92`). Pour `TaskMine`,
   `TaskDig`, `TaskCut`, `TaskHarvest`, `TaskChopWood`, `TaskPlow`, `TaskWater`, `TaskPourWater`, `TaskDrawWater`
   (`CharaTaskRemoteEvent.cs:67-81`) : chaque jeu rejoue `OnProgressComplete`, donc `MineBlock`, `MineFloor`, `MineObj`, etc.
   chez lui (les objets créés par ces rejeux sont jetés, `ZoneAddCardEvent.cs:33-41`, remplacés par ceux de l'host).
3. **Une créature qui casse un mur** : `CharaDestroyPathDelta` (union 227), l'autre jeu appelle `MineBlock/MineObj`
   (`CharaDestroyPathDelta.cs:33-51`), les objets créés sont jetés (:54-56).
4. **La carte entière**, voir §3.2.
5. Les objets posés (meubles) voyagent comme des cartes (`CardGenDelta`, `ZoneAddCardDelta`, `CardPlacedDelta`), pas comme du
   terrain.

Ne passent par **aucun** chemin : liquide posé par un habitant ou un joueur (`SetLiquid` : `AI_Bladder`, `AI_Clean`, `TaskClean`,
`TraitDrink`… sont dans des tâches dont seule une partie est envoyée ; non vérifié au cas par cas), pousse des plantes
(`GrowSystem` appelle `SetObj`, `GrowSystem.cs`), feu, toit posé hors rejeu, terrain monté/descendu (`AM_Terrain`),
zones (`Map.rooms`), marques (`Map.tasks`).

### 3.2 Quand la carte entière est renvoyée

- `ZoneDataResponse.Create(zone)` (`MOD/Models/ZoneState/ZoneDataResponse.cs:53-69`) : **sauve la carte maintenant**
  (`zone.map.Save`, :59) et envoie tous les fichiers du dossier de la zone (cases, `map` json avec `rooms`, `tasks`, `config`).
  Fichiers de cases : `blocks, blockMats, floors, floorMats, objs, objMats, objVals, decal, flags, flags2, dirs, heights,
  bridges…, roofBlocks…, decos…` (`JEU/Map.cs:381-486`).
- Envoyée quand : l'host entre dans une zone (diffusion à tous, `ElinNetHostZone.cs:16-37`) ; un client la demande
  (`MapDataRequest`, `ElinNetHostZone.cs:45-68`, à l'arrivée et en cas de zone périmée :
  `ElinNetHostZone.cs:85-91`) ; le client l'écrit dans un dossier temporaire et recharge la zone
  (`ElinNetClientZone.cs:48-120`). Le client demande aussi la carte courante après un échec de synchro
  (`RetryZoneSync`, :29-43).
- **Pas de renvoi périodique** : le « snapshot du monde » (`WorldStateSnapshot.cs:39-72`) ne contient que les personnages,
  la date, le prochain numéro de carte et la vitesse. D'où la ligne 4 : ce que l'host bâtit pendant que l'invité est dans la
  zone n'arrive qu'à sa prochaine entrée.

### 3.3 Miner un mur ou couper un arbre **à la main** (hors mode construction)

Invité qui mine (pioche tenue) : `Chara.SetAI(TaskMine)` → `CharaTaskDelta(TaskMineArgs)` envoyé à l'host
(`CharaTaskRemoteEvent.cs:75,184`) → l'host fait jouer la tâche par le personnage distant (`CharaTaskDelta.cs:42-67`,
`GoalRemote.InsertAction`) → à la fin de la progression, `OnProgressComplete` chez l'host change **sa** carte (`MineBlock`),
ses effets (pierres ramassées pour le personnage distant, `CharaPickThingEvent.cs:96-106`) sont rangés, et
`CharaProgressCompleteDelta` part (`CharaProgressCompleteEvent.cs:113-129`) → chaque client, **y compris l'invité qui mine**,
rejoue `OnProgressComplete` de sa copie de la tâche (`CharaProgressCompleteDelta.cs:62-72`) : `MineBlock` chez lui, puis
applique les effets de l'host. Même chemin pour couper, creuser, tailler un rondin, labourer. Pour l'host qui mine : sens
inverse (son `SetAI` envoie la tâche aux clients, qui la font jouer par la copie de son personnage).
→ **Le terrain suit parce que chaque jeu refait le même acte, pas parce qu'on envoie un état.** Si les deux cartes ont déjà
divergé (cas du mode construction), le rejeu est faux.

---

## 4. Options de correction (de la plus petite à la plus complète)

Vocabulaire : « demande » = delta de l'invité vers l'host, que l'host vérifie, exécute et renvoie (modèle déjà dans le
mod : `BaseRequestDelta`, union 824, `MOD/Models/Delta/Zone/BaseRequestDelta.cs:40-140` : l'invité n'envoie que la demande et
ne change rien ; l'host relit tout depuis son état, paie sur le personnage de l'expéditeur — `sender.ModCurrency`, :138 —
et répond `Done` / `Refused`). Prochain numéro d'union libre : 830 (`ElinDelta.cs`, dernier = 829 `NameDelta`).

### (a) Message « la base se construit chez l'host » avant de payer — **le plus petit**

- **Ce que l'invité obtient** : un refus clair, au clic, sans rien payer, pour les gestes cassés (construire du menu, miner,
  creuser, couper, zones, terrain, ranger, démonter). Il continue à pouvoir tenir un objet et le poser (marche), déplacer un
  meuble (probable, §2.2), inspecter.
- **Comment** : un préfixe sur `BaseTileSelector.TryProcessTiles` (`BaseTileSelector.cs:241`) qui, pour un client qui n'applique
  pas un delta, dans un mode de la liste (`AM_Build`, `AM_Mine`, `AM_Dig`, `AM_Cut`, `AM_Harvest`, `AM_Deconstruct`,
  `AM_CreateArea`, `AM_ExpandArea`, `AM_EditArea`, `AM_Terrain`), affiche `EmpPop.Information("emp_construction_host_only".lang())`
  (modèle : `RemoteBasePaidPatch.Refuse`, `Patches/Remote/RemoteBasePaidPatch.cs:41-47`, message `emp_base_host_only`) et
  renvoie `false`. Pour les marques par menu (`InspectGroupObj/Block/Thing`) : un préfixe sur `TaskList<T>.TryAdd` des six
  listes et sur `Card.SetDeconstruct` (facultatif : ces marques sont déjà sans effet, §0.2).
- **Taille** : 1 fichier de patch (~80 lignes), 1 texte en 4 langues (`package/LangMod/EN/emp_localization.xlsx`, `CN/SourceLocalization.json`,
  + supprimer `LangMod/EN/SourceLocalization.json` du mod installé, règle de `CLAUDE.md`), 1 test.
- **Risque de doublon / perte** : aucun (rien ne part). **Sauvegardes** : aucun risque (rien d'écrit). Risque : bloquer à tort
  un geste qui marche (le 1er clic de `AM_Inspect` choisit un meuble sans rien changer : ne pas le bloquer).
- **Défaut** : ne corrige rien, **ne respecte pas « zéro différence »** (le plan l'accepte comme M14 en attendant).

### (b) Rejouer chez l'host chaque geste de construction de l'invité comme une demande

- **Ce que l'invité obtient** : le même geste que l'host. Il clique, l'invité envoie une demande (recette + matériaux choisis +
  direction, altitude, hauteur de pont, indicateur toit, liste de cases) ; l'host reconstruit la tâche (`TaskBuild`, `TaskMine`,
  `TaskDig`, `TaskCut`) avec **l'agent**, vérifie case par case (`GetHitResult`), paie **une fois** (or et matériaux pris dans le
  personnage de l'invité tel que l'host le tient : `ActiveRemoteCharas[OriginPeer]`), fait `OnProgressComplete`, et diffuse le
  résultat (par (d) ou par rejeu, voir plus bas). Zones : demande « créer/étendre/rétrécir/effacer ».
- **Pièges lus dans le code** (§1.4) : `HitSummary` et `Recipe.Ingredient.RefreshThing` lisent `EClass.pc` : sur l'host ce serait
  **son** sac, **son** or. Il faut **ne pas** réutiliser `HitSummary` pour un invité et lier soi-même `ingredient.thing` aux objets
  de l'invité (`RefreshThing` rend l'objet déjà lié, `Recipe.cs:70-71`) et payer avec `sender.ModCurrency(-10 × cases)` /
  `thing.ModNum`. Les ramassages de l'agent vont à `EClass.pc` (`Map.cs:1951-1953`) : les pierres iraient à l'host ; il faut
  passer le personnage de l'invité comme `c` (alors `TrySmoothPick` jette à terre, `Map.cs:1957-1960` : petite différence avec
  le solo, où l'objet va au sac). L'état global `ActionMode.Build` (recette, moule) est celui de l'host : si l'host est lui-même en
  mode construction, ne pas y toucher ; `TaskBuild.OnProgressComplete` lit `ActionMode.Build.IsActive/IsRoofEditMode`
  (`TaskBuild.cs:317,380`) : prévoir que ce soit faux quand l'host ne construit pas (cas normal) et envoyer l'indicateur toit dans
  la demande. L'invité ne doit **ni** exécuter localement **ni** appeler `ExecuteSummary` (sinon l'or part deux fois :
  `CardModCurrencyEvent.cs:65-77`).
- **Variante qui réutilise l'existant** : étendre `CharaBuildDelta` pour qu'il n'exige plus d'objet tenu (`Held` facultatif +
  `Recipe` en JSON : `Recipe` est déjà sérialisable par le jeu, `Recipe.cs:177-190`, la sauvegarde de la carte le fait pour
  `TaskBuild.recipe`). Les deux jeux rejouent alors `TaskBuild.OnProgressComplete`, comme pour une pose tenue : le terrain est
  porté par le rejeu (aucun delta de case). Même chose possible pour miner/creuser/couper : un « rejeu de tâche à la case X »
  (`new TaskMine{pos}.OnProgressComplete()` appliqué chez chacun, comme `CharaProgressCompleteDelta` le fait déjà pour les tâches à
  la main).
- **Taille** : 4 à 6 fichiers, 500 à 800 lignes : delta de demande (~150), préfixe côté invité qui construit la demande depuis
  `ActionMode` (~120), exécuteur côté host avec vérification et paiement (~200), diffusion du résultat ((d) ou rejeu, ~100-150),
  messages, tests.
- **Risques de doublon / perte** : l'or part deux fois si l'invité exécute aussi en local (à interdire) ; deux demandes
  quasi simultanées sur la même case (déjà connu, `MODLOG.md:423`) : l'host revérifie `GetHitResult` à chaque case, la 2e est
  refusée ; demande perdue : l'invité a cliqué sans rien voir (il faut un retour « refusé / fait » comme `BaseAnswer`) ; invité
  déconnecté au milieu : l'host a payé et construit, rien d'autre. Matériaux consommés deux fois : seulement si l'invité garde
  son `ModNum` local, bloqué par `CardModNumEvent.cs:13-18` de toute façon. **Sauvegardes** : l'host exécute le vrai geste,
  la sauvegarde est celle d'une construction normale ; aucun champ nouveau n'est écrit. Les numéros d'union nouveaux changent le
  protocole : la barrière de version du mod refuse les anciens clients (comportement voulu).

### (c) Envoyer les marques vers l'host pour que les habitants de l'host les exécutent

- **Ce que l'invité obtient** : ses marques visibles chez l'host. **Rien de plus** : aucun habitant ne lit les marques (§0.2), et
  en jeu normal il n'y a pas de marque (§0.1). **Sans objet** tant que le jeu n'a pas de lecteur. À ne pas faire, sauf pour
  garder les marques de menu (`InspectGroupObj/Block`) visibles chez l'autre : alors ~2 fichiers, ~150 lignes, aucun risque de
  duplication si la marque est envoyée avec sa case (`TryAdd` refuse la case déjà marquée, `DesignationList.cs:15-31`), et
  `Map.tasks` est déjà dans la carte envoyée à l'entrée.

### (d) Diffuser tout changement de case fait chez l'host (patch de `Map.Set*`) — règle aussi la ligne 4

- **Ce que l'invité obtient** : tout ce que l'host (ou une créature, ou un rejeu) change sur les cases lui arrive, sans
  rentrer dans la zone : sols, murs, minerais, arbres, ponts, toits, déco, liquide.
- **Comment** : un delta « état d'une case » (jamais « le clic » : l'état final de ce que la case a pour cet aspect : sol
  `(mat, id, dir)`, bloc `(mat, id, dir)`, objet `(mat, id, valeur, dir)`, pont, toit, déco, liquide, hauteur) comme
  `CardSettingDelta` (`MOD/Models/Delta/Card/CardSettingDelta.cs:11`, « the whole state is sent, not the click: applying it
  twice changes nothing ») ; des postfixes sur `Map.SetFloor` (`Map.cs:1068`), `SetBlock` (:1117), `SetObj` (:1680), `SetBridge`
  (:1087), `SetRoofBlock` (:1103), `SetDeco` (:1079), `SetBlockDir` (:1281), `SetLiquid` (:1626), qui lisent la case **après**
  l'appel et envoient si : on est l'host (ou le teneur du bail), zone active, pas en train de charger ni d'activer la zone
  (`ZoneActivateEvent.IsHappening`, `game.isLoading`), pas en train d'appliquer un delta (`ElinDelta.IsApplying`).
- **À savoir** : (1) beaucoup d'appelants (génération des cartes : `MapGen`, `MapGenDungen`, `Zone_Dungeon`, `GenRoom` ; pousse :
  `GrowSystem` ; habitants : `AI_Bladder`, `AI_Clean`… ; sorts : `ActEffect`) : sans les bonnes gardes, trafic inutile ;
  idempotent donc sans danger de doublon, mais volumineux. (2) Les rejeux existants (`CharaBuildDelta`,
  `CharaProgressCompleteDelta`, `CharaDestroyPathDelta`) feraient le même changement chez chacun : double application
  inoffensive (état absolu), ou à éviter en supprimant l'envoi quand `CharaProgressCompleteEvent.IsHappening` pour un joueur
  distant. (3) **Ne couvre pas** `AM_Terrain` (règle `cell.height` sans appeler `Map.Set*`, `AM_Terrain.cs:62-100`) ni
  `blockDir` écrit à la main (`TaskBuild.cs:343`, `Cell.RotateBlock`) ni `Map.rooms` (zones). (4) **Ne règle pas l'invité**
  tout seul : sens host → invités seulement ; combiné à une demande (b), tout passe par l'host et revient à tous.
- **Taille** : 2 fichiers, ~250 lignes (delta + patch) + gardes + tests. **Risque de duplication** : aucun (état absolu) ;
  **perte** : un delta envoyé avant la carte entière à l'entrée est rejoué sur la carte neuve (inoffensif : même état) ;
  prévoir qu'il soit **retenu** pendant le chargement (comme `Delta.HoldForIncomingMap`, `ElinNetClientZone.cs:75`).
  **Sauvegardes** : aucun champ nouveau ; côté invité c'est une carte temporaire.

### Ce qui se combine

| Combinaison | Résultat | Reste cassé |
|---|---|---|
| (a) seul | l'invité est prévenu, ne paie rien | tout (host → invité : ligne 4 ; invité → host : ligne 1) |
| **(a) + (d)** | ce que l'host bâtit apparaît chez l'invité tout de suite (lignes 4) ; l'invité est prévenu | l'invité ne construit toujours pas |
| (d) seul | ligne 4 réglée pour les cases | l'invité continue de payer l'or et de modifier sa carte à lui |
| **(b) + (d)** (ou (b) par rejeu) | zéro différence : l'invité demande, l'host exécute, tous voient | zones, terrain `AM_Terrain`, ranger : à ajouter comme demandes |
| (c) | sans objet | — |

Ordre qui me paraît le plus sûr (à décider avec l'utilisateur) : **(a) tout de suite** (arrête de prendre de l'or pour rien),
puis **(d) host → invités** (ligne 4), puis **(b) par-dessus (d)**. (a) se retire quand (b) arrive, geste par geste.

---

## 5. Comment un test peut faire le geste comme un joueur (par le pont `eval`)

### 5.1 Ce que le pont permet (lu dans `MOD/Emp/EmpDebugListener.cs:299-314`, `dev/_tools/emp.py`)

`emp.py eval "<C#>"` (`travel_suite.ev(port, code)`) exécute du C# **dans le fil principal** du jeu, avec `System`,
`System.Linq`, `Newtonsoft`, `UnityEngine`, `HarmonyLib`, et les types du jeu. L'état est gardé entre deux appels
(`ScriptState = "dev"`). `return x;` renvoie une chaîne. Ports : host 27551, invité 27552 (`hunt2_suite.py:H, A`).

### 5.2 Le geste, étape par étape (noms lus dans le décompilé, **à essayer** : rien n'a été exécuté)

1. **Entrer dans le mode** (ce que fait le menu) : choisir la recette puis `ActionMode.Build.StartBuild(recette, () => null)`
   (`AM_Build.cs:164-177`) ; elle active le mode (`Activate`) donc crée `BuildMenu.Instance`, **nécessaire au paiement**
   (`BaseTileSelector.cs:473`). Pour miner : `ActionMode.Mine.Activate(false)` (`ActionMode.cs:339`). Pour une zone :
   `ActionMode.CreateArea.SetArea(Area.Create("public")); ActionMode.CreateArea.Activate()`. Sortie : `ActionMode.DefaultMode.Activate(false)`
   (`HotItemActionMode.cs:73-75`, « ExitBuild »).
2. **Choisir la recette** : `RecipeManager.BuildList(); var src = RecipeManager.list.First(r => r.type == "Floor" && !r.isBridge
   && r.row.factory.IsEmpty()); var recipe = Recipe.Create(src); recipe.BuildIngredientList();`
   (`Recipe.cs:310-335,539-546`). Lier les matériaux comme le menu : `recipe.ingredients[0].SetThing(EClass.pc.things.Find(uid))`
   (`Recipe.cs:98-103`) ; l'ingrédient demandé est `recipe.ingredients[0].id` / `.req`. Les recettes « connues » ne comptent que
   pour la liste du menu, pas pour ce chemin.
3. **Le clic** : `Scene.HitPoint.Set(x, z)` (champ statique, `Scene.cs:21`) ; `var sel = EClass.screen.tileSelector;`
   `sel.start = null;` (une case) ; `sel.RefreshSummary();` (compte les cases valides et le coût, `BaseTileSelector.cs:482-490`) ;
   `sel.TryProcessTiles(Scene.HitPoint.Copy());` (`:241-279`) : c'est le clic gauche d'un joueur. Il appelle `CanProcessTiles`,
   `OnBeforeProcessTiles`, `OnProcessTiles` (→ `AM_Designation.OnProcessTiles` ou `AM_Build.OnProcessTiles`, `AM_Build.cs:294-315`),
   `ExecuteSummary` (paiement), `OnFinishProcessTiles`. Pour un mode « zone » (`SelectType.Multiple` : miner, creuser, sols), le
   clic du jeu pose d'abord `start`, puis un 2e `TryProcessTiles` : pour une case, mettre `sel.start = Scene.HitPoint.Copy()` puis
   `TryProcessTiles` du même point. Sa première instruction sort si `EInput.skipFrame > 0` (`:243`) ; `Activate` appelle
   `EInput.Consume` : **faire l'activation et le clic dans deux `eval` séparés, avec une seconde entre**.
4. **Pièges** : le test doit remettre `Scene.HitPoint` à la main au début de chaque `eval` (la souris le réécrit à chaque image) ;
   tout le « geste » se fait dans **un seul `eval`** après l'activation. `HitSummary.CanExecute` exige l'or et les matériaux
   avant le clic (`HitSummary.cs:44-106`). Dans la zone de départ, vérifier `EClass.Branch != null` (la Prairie est-elle une
   base ? non vérifié) : sinon l'activation programmatique marche quand même (rien ne la garde), mais ce n'est plus « ce que
   voit le joueur ».
5. **Raccourci sans souris ni menu** (modèle `build_suite.py` b1, :54-64), pour tester **la correction** sans le paiement :
   `new TaskBuild { recipe = …, pos = p.Copy(), owner = EClass.player.Agent }.OnProgressComplete();` ne passe pas par le
   paiement ni `AM_Designation` : il prouve seulement le raccourci (règle de `CLAUDE.md`).

### 5.3 Quoi regarder dans l'autre fenêtre

| Quoi | Code C# (dans le jeu voulu) |
|---|---|
| sol de la case | `var c = new Point(x, z).cell; return c._floor + "/" + c._floorMat + "/" + c.floorDir;` |
| bloc (mur) | `var c = new Point(x, z).cell; return c._block + "/" + c._blockMat + "/" + new Point(x, z).HasBlock;` |
| objet de case (arbre) | `new Point(x, z).HasObj.ToString()` ou `c._obj` |
| or de l'invité, vu par l'host | `ev(H, f'{chara(H, uid)}.GetCurrency().ToString()')` ; vu par l'invité : `EClass.pc.GetCurrency()` |
| matériaux | `count(port, uid, ingredient_id)` (`guest_suite.py:60-62`) |
| marques en attente | `EClass._map.tasks.designations.mine.items.Count` (attendu 0 : instantané) |
| zones | `EClass._map.rooms.listArea.Count` |

Préparer les cases des **deux** côtés : le terrain n'est pas synchronisé (`build_suite.py:135`), donc mettre le même mur chez les deux
avant le geste et le remettre après (`EClass._map.SetBlock(x, z, 0, 0)`), comme `b3`. Donner l'or et les matériaux par l'host
avec `give(ctx, key, id, n)` (`guest_suite.py:51-57`) et un or suffisant (`ThingGen.Create("money")`, `SetNum`).

### 5.4 Brouillon de trois tests rouges (dans `hunt2_suite.py`, après E5 ; **non exécutés, non compilés**)

```python
# --- aides (a mettre en tete, comme SPOT dans build_suite.py) ---
FLOOR = ('RecipeManager.BuildList(); '
         'var src = RecipeManager.list.FirstOrDefault(r => r.type == "Floor" && !r.isBridge && r.row.factory.IsEmpty() && !r.noListing); '
         'if (src == null) return "pas de recette de sol"; var recipe = Recipe.Create(src); recipe.BuildIngredientList(); ')

def spot(uid):
    """une case libre a 2 cases du joueur (vue de l'host), en terre, sans objet ni mur"""
    return ev(H, f'var p = {chara(H, uid)}.pos; var s = EClass._map.ListPointsInCircle(p, 4f, false, true)'
                 '.Where(q => q.Distance(p) >= 2 && !q.HasBlock && !q.HasObj && !q.HasChara && q.Things.Count == 0 '
                 '&& q.IsInBounds && !q.cell.IsTopWater).FirstOrDefault(); return s == null ? "" : s.x + "," + s.z;')

def floor_at(port, x, z):
    return ev(port, f'var c = new Point({x}, {z}).cell; return c._floor + "/" + c._floorMat;')

def block_at(port, x, z):
    return ev(port, f'new Point({x}, {z}).HasBlock.ToString()')

def gold(port, uid, mine=False):
    return int(ev(port, 'EClass.pc.GetCurrency().ToString()' if mine else f'{chara(port, uid)}.GetCurrency().ToString()'))

def click(port, x, z, mode_code):
    """activer le mode, attendre, puis un clic (deux eval : EInput.skipFrame)"""
    ev(port, mode_code)
    time.sleep(1.2)
    return ev(port, f'Scene.HitPoint.Set({x}, {z}); var sel = EClass.screen.tileSelector; sel.start = Scene.HitPoint.Copy(); '
                    'sel.RefreshSummary(); var ok = EClass.scene.actionMode.CanProcessTiles(); var n = sel.summary.countValid; '
                    'var m = sel.summary.money; if (ok) sel.TryProcessTiles(Scene.HitPoint.Copy()); '
                    'return ok + "|" + n + "|" + m;')


def e6(ctx):
    """l'invite pose un sol en mode construction (ligne 1) : le sol est pose chez l'host, l'or part une fois, les matieres aussi"""
    port, uid = ctx["a"]
    x, z = spot(uid).split(",")
    before_floor = floor_at(H, x, z)
    ing = ev(H, FLOOR + 'return recipe.ingredients[0].id + "," + recipe.ingredients[0].req;')
    ing_id, req = ing.split(",")
    mats = give(ctx, "a", ing_id, 10)        # matieres dans le sac de l'invite, vues de ses deux jeux
    ev(H, f'var c = {chara(H, uid)}; c.ModCurrency(500); "ok"')
    time.sleep(2)
    g0, m0 = gold(H, uid), count(H, uid, ing_id)
    try:
        r = click(port, x, z, FLOOR + f'var t = EClass.pc.things.Find(q => q.uid == {mats}); recipe.ingredients[0].SetThing(t); '
                              'ActionMode.Build.StartBuild(recipe, () => null); "ok"')
        log(f"invite clique en {x},{z} : {r}")
        check(f"le clic est accepte par le jeu ({r})", r.startswith("True|1|"))
        check(f"host : le sol de l'invite est pose en {x},{z} ({before_floor} -> {floor_at(H, x, z)})",
              eventually(lambda: floor_at(H, x, z) != before_floor, timeout=15))
        check(f"invite : il le voit aussi ({floor_at(port, x, z)})", floor_at(port, x, z) == floor_at(H, x, z))
        check(f"l'or part une seule fois : 10 (host voit {g0} -> {gold(H, uid)})",
              eventually(lambda: g0 - gold(H, uid) == 10, timeout=10))
        check(f"les matieres partent une seule fois : {req} (host voit {m0} -> {count(H, uid, ing_id)})",
              eventually(lambda: m0 - count(H, uid, ing_id) == int(req), timeout=10))
    finally:
        ev(port, 'ActionMode.DefaultMode.Activate(false); "ok"')
        # le terrain n'est pas synchronise : remettre l'ancien sol des DEUX cotes (lu avant le clic : before_floor = "id/mat")
        fid, fmat = before_floor.split("/")
        for p in (H, port):
            ev(p, f'EClass._map.SetFloor({x}, {z}, {fmat}, {fid}); "ok"')
        # + detruire les matieres qui restent dans le sac de l'invite


def e7(ctx):
    """l'invite marque un mur "miner" (ligne 1) : le mur tombe chez l'host, l'or part une fois, aucune marque ne reste"""
    port, uid = ctx["a"]
    x, z = spot(uid).split(",")
    for p in (H, port):                        # meme mur des deux cotes (le terrain n'est pas synchronise)
        ev(p, f'EClass._map.SetBlock({x}, {z}, 3, 1); new Point({x}, {z}).cell.isSeen = true; "ok"')
    ev(H, f'{chara(H, uid)}.ModCurrency(500); "ok"')
    time.sleep(2)
    g0 = gold(H, uid)
    try:
        r = click(port, x, z, 'ActionMode.Mine.Activate(false); "ok"')
        log(f"invite marque {x},{z} : {r}")
        check(f"host : le mur est tombe ({block_at(H, x, z)})", eventually(lambda: block_at(H, x, z) == "False", timeout=15))
        check(f"invite : son mur est tombe aussi ({block_at(port, x, z)})", block_at(port, x, z) == "False")
        check(f"l'or part une seule fois : 10 ({g0} -> {gold(H, uid)})", eventually(lambda: g0 - gold(H, uid) == 10, timeout=10))
        check("aucune marque ne reste en attente, des deux cotes",
              ev(H, 'EClass._map.tasks.designations.mine.items.Count.ToString()') == "0"
              and ev(port, 'EClass._map.tasks.designations.mine.items.Count.ToString()') == "0")
    finally:
        ev(port, 'ActionMode.DefaultMode.Activate(false); "ok"')
        for p in (H, port):
            ev(p, f'if (new Point({x}, {z}).HasBlock) EClass._map.SetBlock({x}, {z}, 0, 0); "ok"')


def e8(ctx):
    """l'host pose un sol en mode construction (ligne 4) : l'invite le voit sans rentrer a nouveau dans la zone"""
    uid = ctx["h"][1]
    x, z = spot(uid).split(",")
    before = floor_at(A, x, z)
    ev(H, FLOOR + f'var t = ThingGen.Create(recipe.ingredients[0].id); t.SetNum(10); EClass.pc.AddThing(t); '
                  'recipe.ingredients[0].SetThing(t); "ok"')
    try:
        r = click(H, x, z, FLOOR + 'ActionMode.Build.StartBuild(recipe, () => null); "ok"')   # recette de l'etape (voir e6)
        check(f"host : le sol est pose ({floor_at(H, x, z)})", floor_at(H, x, z) != before)
        check(f"invite : il voit le sol de l'host ({before} -> {floor_at(A, x, z)})",
              eventually(lambda: floor_at(A, x, z) == floor_at(H, x, z), timeout=15))
    finally:
        ev(H, 'ActionMode.DefaultMode.Activate(false); "ok"')
```

Notes sur le brouillon :
- `e6` : deux `ev` pour la recette (celle du `FLOOR` est recréée dans l'`eval` du clic ; il faut qu'elle soit la même que celle dont on lit
  l'ingrédient : prendre le même `src`). La remise en état du sol est écrite ; celle des matières restantes dans le sac de l'invité reste à écrire avant d'exécuter.
- Rouge attendu **aujourd'hui** : `e6` : sol absent chez l'host et chez l'invité (`CharaProgressCompleteEvent.cs:73`), or retiré, matières
  inchangées ; `e7` : mur tombé chez l'invité **seulement**, or retiré ; `e8` : sol posé chez l'host, absent chez l'invité.
- Quatrième test utile, cheap, **pour vérifier ce que ce document n'a pas pu** : l'invité déplace un meuble installé
  (`ActionMode.Inspect.Activate(thing)` puis clic sur une case libre) → vérifier la position chez l'host et chez l'autre invité
  (§2.2 « probablement oui »).
- Une première exécution de ces trois tests **sans correction** est la preuve de tout le §2.2 (elle dira aussi si
  `Player._agent` est nul chez l'invité : exception dans le journal `scan_logs`).

---

## Ce qui n'a pas pu être vérifié

1. **Rien n'a été joué** : ni le paiement (or réellement retiré chez l'invité, matériaux réellement non retirés), ni le fait que
   `TaskBuild.OnProgressComplete` soit sauté chez l'invité (Harmony exécute bien les postfixes quand le préfixe renvoie `false`,
   mais le journal n'a pas été regardé), ni l'état exact de la carte de l'invité après miner/creuser/couper.
2. `Player._agent` chez l'invité : lu comme « celui de l'host » parce que le client charge la sauvegarde de l'host
   (`ElinNetClientPlayer.cs:187-206`) ; non vérifié (s'il est nul, chaque geste lève une exception, `AM_Designation.cs:96-97`).
3. Que les objets du sac de l'invité soient « connus de l'host » au sens de `CardCache.IsHostOwned` (donc que `ModNum` y soit
   annulé) : déduit de `CardModNumEvent.cs`, `CardCache.cs:224`.
4. Que la Prairie (zone de départ des bancs) soit une zone avec une base, donc que la barre n°3 s'y affiche ;
   l'origine des éléments 4000-4006 de la base (`FactionBranch.cs:1276` pose 4002 ; les autres : non cherché).
5. Qu'aucun habitant n'exécute jamais une marque : conclu d'un grep sur tout `_decomp/Elin` (23.352) ; une exécution par un
   mécanisme que le décompilateur ne montre pas (reflet, données) n'est pas exclue. À confirmer en jeu : poser une marque « Cut »
   par le menu d'un arbre, attendre une journée.
6. Le chemin d'un meuble **déplacé** ou **rangé** par un invité (`ZoneAddCardDelta` vers l'host, `CardPlacedDelta`,
   `Map.PutAway` → `Pick` / `TryAddThingInSpot`) : lu jusqu'aux patchs, pas jusqu'au bout ; altitude et direction du meuble déplacé non
   vérifiées.
7. Les noms de méthodes du §5.2 (`StartBuild`, `Scene.HitPoint.Set`, `RefreshSummary`, `TryProcessTiles`, `sel.start`) sont lus dans le
   décompilé, **jamais exécutés** par le pont ; l'ordre `Activate` puis clic en deux `eval`, et `EInput.skipFrame`, sont des
   hypothèses. Les ids de recette (`type == "Floor"`) ne sont pas vérifiés dans les données du jeu.
8. Les liquides, le feu, la pousse des plantes et les sorts qui changent des cases (`ActEffect` appelle `MineBlock/MineObj`) : leur
   passage chez l'autre joueur n'a été regardé que par recherche d'appelants, pas suivi.
9. Le comportement d'une zone tenue par un invité (bail) pour le mode construction : seulement déduit de `NetSession.cs:40`.
10. `AM_Copy`, `AM_Blueprint`, `AM_Populate`, `AM_Paint`, `AM_EditMarker`, `AM_FlagCell`, `AM_StateEditor`, `AM_Visibility`,
    `AM_Cinema` : réservés au debug ou sans effet sur les cases (`HotbarManager.cs:77`, `:185-250`) ; lus en surface, non étudiés.
