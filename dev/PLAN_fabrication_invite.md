# Fabrication « flottante » (`TaskCraft`), rangement, meuble déplacé : pour un invité

Suite de `PLAN_mannequin_invite.md`. **Rien n'a tourné en jeu** : tout est lu dans le code (jeu décompilé
`dev/_decomp/Elin_23351`, et le `Elin.dll` installé pour un point, voir plus bas). Compile (`ReleaseNightly`, 0 erreur).

## 1. `TaskCraft` : ce que c'est

Une fabrication **sans ouvrir d'établi** : une petite liste flottante (`LayerCraftFloat`) qui montrerait, en marchant, ce
qu'on peut fabriquer tout de suite avec ce qu'on a dans le sac et ce qui traîne sur les 9 cases autour de soi, les
établis posés à côté et un feu allumé comptant comme outils (`RecipeUpdater.RunRecipe`, `RecipeUpdater.cs:66-200`).
Un clic sur une ligne fabrique un exemplaire, sans autre fenêtre (`LayerCraftFloat.cs:71-108`) ; garder le bouton enfoncé
recommence (`:49-56`).

**Un joueur ne peut pas la lancer aujourd'hui.** Deux verrous dans le jeu lui-même :

- la liste n'existe que si le réglage `altCraft` est vrai (`Scene.cs:258-270`) ; rien dans le code du jeu ne le met à vrai
  (trois mentions en tout : `CoreConfig.cs:156`, `Game.cs:272`, `Scene.cs:258`) ;
- la liste est remplie par `Thing.GetRecipes`, qui est **vide** (`Thing.cs:1869-1871`). Vérifié aussi dans le `Elin.dll`
  installé (23.352 du 2026-10-06) : la méthode fait 1 octet (un simple retour), comme `GetDisassembles` et `Disassemble`.
  Liste toujours vide, donc aucune ligne à cliquer, donc `LayerCraftFloat.cs:105` (le seul `new TaskCraft` du jeu) n'est
  jamais atteint. `FactoryData.queues` (une file de `TaskCraft`) n'est lue par personne.

C'est une fonction que le jeu n'a pas finie. Seul un autre mod pourrait lancer `TaskCraft` (aucun des mods installés sur
cette machine ne parle de `altCraft` ni de `LayerCraftFloat`).

### En solo, si elle était lancée (`TaskCraft.cs`)

- Progression de 5 pas (`:72-75`), arrêt à la main permis (`:48`). À chaque pas : son de la matière, +20 d'expérience dans
  la compétence de la recette (`:81-86`).
- À la fin (`:142-166`), pour chaque exemplaire : vérification puis **prise des ingrédients** (`Split(req)` puis `Destroy`,
  `:111-140`), `recipe.Craft(blessed, …)` **sans établi et sans la liste des ingrédients** (`:157`), +200 d'expérience,
  puis une fois : sons, fumée, endurance `-costSP` (jamais renseigné par `LayerCraftFloat` : 0).
- Le produit (`RecipeCard.Craft`, `RecipeCard.cs:154-349`) : qualité = niveau de la recette + bonus des ingrédients ;
  matière = celle du premier ingrédient ; « raté » (qualité basse) tiré selon la compétence **du joueur** (`EClass.pc`) ;
  nombre = `CraftNum` de l'objet (pas de doublement de sorcière : il demande un établi) ; l'objet arrive **tenu en main**
  (`EClass.pc.HoldCard`, `:316-319`), ou empilé sur ce qui est déjà en main. Les blocs et sols (`Recipe.Craft`,
  `Recipe.cs:566-592`) : ajoutés au sac puis tenus.
- Pas de bonus de première fabrication (c'est la fenêtre de l'établi qui le donne).

### Pour un invité sur la carte de l'host, aujourd'hui (lu)

Rien : la tâche part comme inconnue (`CharaTaskRemoteEvent.cs:84` en commentaire, donc `FakeTask`), elle est **exclue** de
la correction générale (`:184`, `g is not TaskCraft`), donc ancien comportement : au premier pas la progression est
annoncée et retenue (`CharaProgressBeginEvent.cs`), l'host répond « Progress begin TaskCraft … has no matching act,
requesting cancel », l'invité s'arrête. `OnProgressComplete` n'est jamais appelé : **aucun ingrédient pris, aucun
produit, aucune expérience**. Sûr pour les sauvegardes, et inatteignable de toute façon.

**Décision : pas de code.** Écrire une prise en charge d'un chemin que le jeu ne peut pas emprunter, sans pouvoir la jouer,
c'est du risque sans gain. L'exclusion reste. `craft_suite.py` C1 devient rouge le jour où le jeu remplit la liste : c'est
le signal pour réaliser le plan ci-dessous.

## 2. Comment marche déjà la fabrication à l'établi (`AI_UseCrafter`)

1. L'invité clique « fabriquer » : `SetAI(AI_UseCrafter)`. `AIUseCrafterArgs.Create` (`Models/Delta/Task/AI/AIUseCrafterArgs.cs:42-60`)
   écrit la demande : l'établi, la durée, le nombre, **les ingrédients choisis** (numéros des objets) et combien de chacun,
   la recette et sa matière, « jamais fabriquée par ce joueur ». Elle part dans `CharaTaskDelta`.
2. Chez l'invité, la tâche est accrochée à sa demande (`RemoteCraft.Attach`, `CharaTaskRemoteEvent.cs:198-201`) et son
   déroulement est remplacé (`AIUseCrafterPatch.RunClient`, `:32-79`) : une progression « retenue » qui **attend l'host** ;
   rien n'est pris, rien n'est créé chez lui. À la fin il s'applique l'expérience et l'endurance par la même formule.
3. Chez l'host, la copie de l'invité reçoit une vraie `AI_UseCrafter` (`AIUseCrafterArgs.CreateSubAct`, `:62-100`),
   déroulée par `RunRemote` (`AIUseCrafterPatch.cs:193-469`) : il vérifie les ingrédients, les **prend** (`Split`, jamais
   plus que la pile), allume l'établi, calcule la durée, puis à la fin appelle `recipe.Craft` avec l'invité « à la place du
   joueur » (`RemoteCraft.AsCrafter` : `EClass.pc` est l'invité le temps de l'appel, donc **la qualité, le raté, le don de
   sorcière sont tirés chez l'host avec les compétences de l'invité**), et avec `RemoteCraft.ProductReceiver` : ce que le
   jeu veut mettre dans le sac ou la main « du joueur » va dans **le sac de l'invité** (`OnAddProduct`, `OnHoldProduct`,
   `:127-153`). Messages redirigés vers l'invité (`MsgRelayContext`). Bonus de première fois donné par l'host, noté chez
   l'invité par `CraftFirstTimeDelta`.
4. Tout cela se fait « comme un geste de l'host » (`ElinDelta.Simulate`) : l'objet créé, les piles diminuées, l'état de
   l'établi partent à tout le monde par les deltas ordinaires des cartes, rangés dans la fin de progression
   (`CharaProgressCompleteDelta`, `CharaProgressCompleteEvent.cs:132-136`), qui débloque aussi l'attente de l'invité.

Donc : **un seul jeu prend les ingrédients et crée l'objet (l'host)**, l'invité le reçoit comme n'importe quel objet mis
dans son sac. Joué par `player_suite.py` (F1/F2 : potion et don de sorcière ; F6 : bonus de première fois).

## 3. Plan pour `TaskCraft` (à faire seulement si C1 devient rouge)

Réutiliser le chemin de l'établi, pas en inventer un.

| Ordre | Fichier | Quoi |
|---|---|---|
| 1 | `Models/Delta/Task/TaskCraftArgs.cs` (neuf), `TaskArgsBase.cs` : `[Union(229, typeof(TaskCraftArgs))]` | `RecipeId`, `RecipeMat`, `Targets` (les `recipe.ingredients[i].thing`), `Required` (`reqs`), `Num`. `CreateSubAct` chez l'host : `Recipe.Create` + liaison des ingrédients comme `AIUseCrafterArgs.BindIngredients` (à sortir en commun), puis `new TaskCraft { recipe, num, floatMode = true }` + `ResetReq()` ; ailleurs `DelegateProgress.Create(typeof(TaskCraft))` |
| 2 | `CharaTaskRemoteEvent.cs:84` | activer `TaskCraft task => TaskCraftArgs.Create(task)` ; retirer `&& g is not TaskCraft` (`:184`) |
| 3 | `Patches/DeltaEvents/Task/TaskCraftPatch.cs` (neuf) | préfixe + finaliseur sur `TaskCraft.OnProgressComplete` : chez l'host, pour la copie d'un autre joueur, entourer l'appel de `RemoteCraft.AsCrafter(owner)`, `RemoteCraft.ProductReceiver = owner`, `MsgRelayContext.RedirectTo(owner)`, `ElinDelta.Simulate()`. Chez l'invité (rejeu de la fin, `CharaProgressCompleteDelta.IsReplaying`) : **ne pas** rejouer l'original (il prendrait et créerait une deuxième fois), seulement +200 × `num` d'expérience et l'endurance, comme `RunClient`. Préfixe sur `TaskCraft.OnProgress` : la copie d'un autre joueur ne donne pas les +20 (modèle `AIPracticeDummyPatch`) |
| 4 | `craft_suite.py` | passer `GUEST_CRAFTS = True` : C2 attend alors ingrédients partis une fois, produit une fois dans le sac de l'invité dans les deux jeux, expérience |

Points à trancher en jouant : `CraftPos` et les sons lisent `EClass.pc` ; `LayerCraftFloat.Instance.OnCompleteCraft()` dans
`Run` chez l'host ; le produit arrive dans le sac et non en main (comme à l'établi aujourd'hui : petite différence avec
le solo) ; ingrédients pris au sol (la liste flottante les accepte).

## 4. `TaskDump` (rangement automatique)

- Part comme `FakeTask` : pas de ligne dans la table (le commentaire `CharaTaskRemoteEvent.cs:74-75`, resté sans sa ligne,
  dit pourquoi : elle lit le sac « du joueur » et ferme « ses » fenêtres là où elle tourne ; `TaskDumpArgs` existe mais
  ne sert pas). Chez l'host la copie de l'invité ne fait rien : voulu.
- **Pas de progression** : elle marche (`DoGoto`, un `AI_Goto`) puis range d'un coup (`TaskDump.cs:84-121`). Ni l'annonce
  de progression ni l'arrêt retenu ne la concernaient (`CharaTaskCancelEvent.cs:16` : seulement si l'acte courant est une
  progression). Elle tournait déjà seule chez l'invité avant la correction générale ; le marquage de ce soir ne change rien.
- Les objets arrivent chez l'host un par un par le chemin ordinaire « mettre dans un coffre » (`c.AddCard`,
  `CardAddThingEvent`). Joué par `hunt_suite.py` D3 et D3b, pour l'invité puis pour l'host.
- Rien à corriger. (Le coffre d'expédition, `TaskDump.cs:103-106` : domaine interdit, pas regardé.)

## 5. `DynamicAIAct` (« marcher jusque-là puis faire l'acte », `ActPlan.cs:104` ; `Chara.DoAI`, `Chara.cs:6617`)

- Inconnue de la table, donc `FakeTask`, donc marquée chez l'invité depuis ce soir.
- Sa propre course : `DoGotoInteraction` (`AI_Goto`), `DoWait` (`AI_Wait`), puis `onPerform` (`DynamicAIAct.cs:51-63`).
  **Aucune progression dessous.** L'acte final est un `Act` ordinaire, rejoué chez l'host par `CharaActPerformEvent`
  (qui écarte `DynamicAIAct` elle-même, `:24`). S'il lance une tâche (`SetAI`), c'est une tâche neuve, sans parent : elle
  n'est pas sous l'acte marqué (`FakeTask.IsMarked` remonte les `parent`, que seul `Do`/`SetChild` pose) et passe par la
  table comme d'habitude.
- Donc le marquage est sans effet pour elle. Rien à corriger.

## 6. Meuble installé déplacé par un invité (`TaskMoveInstalled`)

- Le mode est **ouvert à un invité** : `RemoteBuildModePatch` laisse passer `AM_Inspect` (= `AM_MoveInstalled`), même
  quand l'host a coupé la construction pour les autres (`RemoteBuildModePatch.cs:28-35`, écrit dans son commentaire).
- `AgentTaskDelta.TrySend` n'est jamais appelé pour lui (seuls `TaskMine/Dig/Cut` et `TaskBuild` sont accrochés), et ce
  n'est pas nécessaire : **le déplacement ne reste pas local**. L'agent de l'invité finit la tâche chez lui
  (`TaskMoveInstalled.cs:92-119`) : `Zone.AddCard` à la nouvelle case envoie `ZoneAddCardDelta` (l'host déplace l'objet
  et relaie, `ZoneAddCardDelta.cs:42-57`), `SetPlaceState` envoie `CardPlacedDelta` avec la direction.
- **Ce qui restait local (défaut certain, lu)** : la **hauteur** (`target.altitude = altitude`, `:114`, écrite à la main
  après), « ignorer l'empilement » (`:115`), la **pose libre** (`freePos`, `fx`, `fy`) et le drapeau de toit
  (`AM_MoveInstalled.cs:301-304`, `:318`). Aucun delta ne portait ces champs (recherche `altitude` : seulement les
  constructions). Pour un invité c'est perdu pour de bon : la sauvegarde est celle de l'host. Dans l'autre sens (l'host
  déplace), les invités ne le voyaient qu'à leur prochaine arrivée.
- **Corrigé** (pas sur le modèle des quatre autres, qui demandent à l'host de faire la tâche : ici la tâche est déjà
  faite, il manque quatre champs) :

| Fichier | Changement |
|---|---|
| `ElinTogether/Models/Delta/Card/CardPoseDelta.cs` (neuf) | hauteur, pose libre, empilement, toit d'un objet posé ; l'host relaie |
| `ElinTogether/Patches/DeltaEvents/Task/MoveInstalledPatch.cs` (neuf) | après le clic qui pose (`AM_MoveInstalled.OnProcessTiles`), dans le jeu de celui qui déplace, host ou invité |
| `ElinTogether/Models/Delta/ElinDelta.cs` (**à faire, pas touché**) | `[Union(843, typeof(CardPoseDelta))]` |

  Tant que la ligne 843 n'est pas dans `ElinDelta.cs`, le patch **n'envoie rien** (il regarde si le delta a son numéro) :
  compiler sans elle ne casse rien. Rien de neuf dans les sauvegardes : ce sont les champs que le jeu écrit en solo.
- Si `player.instaComplete` est coupé chez l'invité, la tâche reste une « marque » que personne n'exécute
  (`AM_Designation.cs:92-100`) : comme en solo, pas regardé plus loin.

## 7. Pas sûr

- Rien n'a été joué. `dev/_tools/craft_suite.py` (C1 à C4) est écrit, jamais lancé.
- `altCraft` : aucun code ne le met à vrai, mais un bouton de l'écran des options branché dans Unity (hors du code)
  n'est pas exclu. Sans `GetRecipes`, la liste reste vide même alors.
- `CardPoseDelta` : l'ordre d'arrivée (après `ZoneAddCardDelta` et `CardPlacedDelta`, même lot) est supposé gardé ;
  `SetPlaceState` remet la hauteur à zéro quand un objet installé change d'état (`Card.cs:3941-3950`), d'où l'envoi en
  dernier. Le mode toit (touche Alt) et la pose libre ne sont pas dans le test.
- L'host accepte ces champs de n'importe quel invité pour n'importe quel objet posé, comme il accepte déjà la direction
  et la position (`CardSetDirDelta`, `ZoneAddCardDelta`) : pas de droit vérifié.
