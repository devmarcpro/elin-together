# Entraînement au mannequin : ne marche pas pour un invité

Retour d'une vraie partie (0.26.524, joueur invité). Rien n'a tourné en jeu : tout ce qui suit est **lu dans le code**.

## En solo (code du jeu, `dev/_decomp/Elin_23351`)

- Le menu : `TraitTrainingDummy.TrySetAct` (`TraitTrainingDummy.cs:20-29`) propose `AI_PracticeDummy` si le mannequin est
  installé. Aussi lancé par un tir (`ActRanged.cs:75-83`, `range = true`), par un lancer (`ActThrow.cs:431-438`,
  `throwItem`) et sur un prisonnier attaché (`ActPlan.cs:576-585`).
- La tâche : `AI_PracticeDummy.cs:11-70`. Une progression de 10 000 pas, un coup tous les 2 pas (`ACT.Melee.Perform`,
  ou tir, ou lancer), endurance -1 deux fois sur cinq (`:57-60`), arrêt si l'endurance passe sous zéro (`:61-64`), si la
  cible disparaît (`:13`), si le joueur bouge ou appuie sur une touche (`AI_Practice.cs:13`, `AM_Adv.cs:952`).
  À l'arrêt : le message du bilan (`AI_Practice.cs:18-26`).
- L'expérience : dans `AttackProcess.Perform`, à chaque coup qui touche : compétence d'arme, tactique (132) ou tir (133),
  style de combat (`AttackProcess.cs:806-822`, `ModExpAtk` `:952-966`).
- Le mannequin : `Card.DamageHP` compte le coup pour le bilan (`Card.cs:4562-4566`) puis remet ses points de vie au
  maximum (`Card.cs:4666-4674`). Pas d'usure, jamais détruit.

## La cause (lue)

Un invité frappe dans **son** jeu (expérience et endurance chez lui), chaque coup est rejoué chez l'host
(`CharaActPerformEvent.cs:28-49`, `CharaActPerformDelta.cs:95-123`), les dégâts reviennent de l'host
(`CardDamageHpEvent.cs:36-52`). Ça, c'est en ordre : la cible objet est bien désignée (`RemoteCard.cs:60-67`).

Ce qui casse, c'est la tâche :

1. `AI_PracticeDummy` n'est pas dans la table des tâches : la ligne était en commentaire
   (`Patches/DeltaEvents/Chara/CharaTaskRemoteEvent.cs:127`), donc elle part comme « tâche inconnue » (`:178`,
   `FakeTask`). Chez l'host, la copie de l'invité ne fait rien (`FakeTask.cs:10-13`).
2. Au premier pas, le jeu de l'invité annonce le début de la progression avec le vrai nom de la tâche
   (`CharaProgressBeginEvent.cs:37-58`).
3. L'host ne trouve pas cette tâche sur la copie : « Progress begin AI_PracticeDummy … has no matching act, requesting
   cancel » (`Models/Delta/Chara/CharaProgressBeginDelta.cs:56-66`) et renvoie un ordre d'arrêt.
4. L'invité l'applique (`Models/Delta/Chara/CharaTaskCancelDelta.cs:43-81`) : **l'entraînement s'arrête après zéro ou un
   coup**, le temps d'un aller-retour réseau.

Même message déjà vu au banc pour une autre tâche (`MODLOG.md:1856`, `TaskDig`). `PLAN_chasse_differences_2.md:88`
disait « tourne chez l'invité » : c'était lu, pas joué.

Deuxième défaut caché derrière : même sans l'étape 3, l'invité n'aurait jamais pu arrêter. Son arrêt est retenu et
demandé à l'host (`CharaTaskCancelEvent.cs:25-28`), qui ne relaie que s'il connaît la tâche
(`CharaTaskCancelDelta.cs:43-56`).

- **Invité sur la carte de l'host** (ou sur la carte tenue par un autre invité) : cassé, comme ci-dessus.
- **Host (témoin)** : marche. Il n'attend personne pour progresser ni pour arrêter (`CharaTaskCancelEvent.cs:32-33`).
- **Invité seul sur une autre carte** : il tient la carte, il est « host » pour elle (`DOCUMENTATION.md:170-178`) : même
  chemin que l'host, donc marche (lu).

## La correction (faite)

L'host connaît maintenant la tâche, mais sa copie ne frappe pas : les coups viennent toujours du jeu de celui qui
s'entraîne, un par un. Donc ni perte ni doublon d'expérience, rien d'écrit dans les sauvegardes.

| Fichier | Changement |
|---|---|
| `ElinTogether/Models/Delta/Task/AI/AIPracticeDummyArgs.cs` (neuf) | la tâche et sa cible |
| `ElinTogether/Models/Delta/Task/TaskArgsBase.cs:50` | `[Union(228, typeof(AIPracticeDummyArgs))]` |
| `ElinTogether/Patches/DeltaEvents/Chara/CharaTaskRemoteEvent.cs:127` | la ligne `AI_PracticeDummy ai => AIPracticeDummyArgs.Create(ai),` n'est plus en commentaire |
| `ElinTogether/Patches/DeltaEvents/Task/AIPracticeDummyPatch.cs` (neuf) | la copie d'un autre joueur ne frappe pas (`onProgress` vidé si le propriétaire n'est pas « le joueur » de ce jeu) |

Sans la dernière ligne, l'host (et chaque autre joueur) frapperait une deuxième fois pour l'invité, et le lancer se
ferait au nom du joueur local (`AI_PracticeDummy.cs:33-38` lit `EClass.pc`).

Les deux jeux doivent avoir la même version (un numéro de tâche de plus).

## Pas sûr

- Jamais joué. `dev/_tools/dummy_suite.py` (M1 invité, M2 host, M3 invité seul) est écrit, pas lancé.
- La fin par épuisement : l'arrêt passe par l'host, l'invité peut donner un ou deux coups de plus qu'en solo.
- L'arrêt chez l'host range l'objet que la copie tient en main (`AIAct.cs:308-311`), comme pour toutes les tâches
  connues : à regarder pour le lancer sur mannequin.
- La fin au bout de 10 000 pas est comptée par l'host (un pas par tour de l'invité) : même durée qu'en solo, à un
  ou deux pas près.

## Même cause probable (pas corrigé, pas vérifié)

Toute tâche à progression lancée par un joueur et absente de la table (`CharaTaskRemoteEvent.cs:65-179`) est arrêtée de
la même façon pour un invité :

- `AI_Paint` (peindre sur une toile, `AM_Paint.cs:78`) ;
- `AI_Torture` (un joueur qui s'attache lui-même, `ActRestrain.cs:48`) ;
- `TaskCraft`, `TaskDesignation`, `TaskMoveInstalled` (en commentaire, `:81-88`) si un geste de joueur les lance sans
  passer par un autre chemin du mod ;
- `AI_Sleep` hérite d'une tâche à progression (`AI_TargetCard`) : annoncé vert par `sleep_suite`, à ne pas toucher.

Déjà dans la table (donc pas concernés) : pêche, lecture, musique, artisanat à l'établi, cuisine, crochetage, tonte,
abattage, vol.

Correction générale : faite, voir la section suivante.

## Correction générale (faite, compile, jamais jouée)

Pour une tâche du joueur d'un invité partie comme `FakeTask` (inconnue de la table) : (1) l'invité ne l'annonce pas à
l'host, (2) il l'arrête seul. Les tâches de la table ne changent pas : la règle ne s'applique qu'aux actes marqués.

### Ce qui a été lu avant d'écrire

- Pour une tâche inconnue, `CharaProgressBeginEvent` ne faisait pas qu'annoncer : chez un invité il posait aussi
  `progress = HeldProgress.Held` (`CharaProgressBeginEvent.cs`, ancien `:42-45`). Une progression « retenue » n'avance
  jamais d'elle-même, elle attend la fin envoyée par l'host. Pour une tâche inconnue cette fin ne vient jamais :
  même sans l'ordre d'arrêt de l'host, la tâche d'un invité n'aurait pas fini.
- `AIAct.Cancel` (`CharaTaskCancelEvent`) lit l'acte COURANT du joueur (`owner.ai.Current`), pas l'acte qu'on annule,
  et pour un invité il retient l'arrêt (`prevent`) dès que le type de la progression est dans la table des actes
  (`ActMappingValidator`, qui contient tous les `Act` de tous les mods, pas seulement la table des tâches). L'host ne
  relaie que s'il trouve l'acte (`CharaTaskCancelDelta.cs:43-56`) : pour une copie `FakeTask` (un `NoGoal`,
  `FakeTask.cs`) il ne le trouve pas.
- `SetAI` annule l'ancienne tâche APRÈS notre préfixe (`Chara.SetAI`, `ai.Cancel()` puis `ai = g`) : un simple drapeau
  « la tâche en cours est inconnue » posé dans le préfixe serait déjà celui de la tâche suivante quand l'ancienne
  s'arrête (un arrêt de tâche connue serait pris pour un arrêt local, ou l'inverse). D'où un marquage par acte.
- Fin de progression : `CharaProgressCompleteEvent.OnProgressCompleteEnd` n'émet `CharaProgressCompleteDelta` que
  chez l'host (`:121`), à la fin d'une progression qui tourne chez lui. Une copie `FakeTask` ne tourne pas : l'host
  n'émet rien. L'invité qui finit seul n'émet rien non plus (`:121`, il n'est pas l'host) : l'host ne rejoue pas la
  fin et ne la refuse pas. Rien à changer dans cet événement. (Côté invité, `IsHappening` passe à vrai pendant la fin
  locale ; les lecteurs de ce drapeau — karma, abattage, semis, ajout de carte — ne s'en servent que chez l'host ou pour
  des joueurs distants.)
- `AI_Sleep` n'est pas touchée : `AI_TargetCard.HasProgress` est faux, pas de `AIProgress`, donc ni l'annonce ni l'arrêt
  retenu ne la concernent (le sommeil a son propre chemin, `Chara.Sleep`).

### Ce qui a changé

| Fichier | Changement |
|---|---|
| `ElinTogether/Models/Delta/Task/FakeTask.cs` | `Mark(act)` / `IsMarked(act)` : table faible des actes partis comme `FakeTask`, `IsMarked` remonte les `parent` (la progression d'une tâche, ou d'une sous-tâche, d'un acte marqué) |
| `ElinTogether/Patches/DeltaEvents/Chara/CharaTaskRemoteEvent.cs:181-184` | chez un invité, pour son propre personnage, un acte qui sort en `FakeTask` est marqué (la ligne `AI_PracticeDummy` du `:127` est gardée) |
| `ElinTogether/Patches/DeltaEvents/Chara/CharaProgressBeginEvent.cs:37-41` | chez un invité, une progression sous un acte marqué ne fait rien : ni annonce à l'host, ni `Held` (elle avance et finit seule) |
| `ElinTogether/Patches/DeltaEvents/Chara/CharaTaskCancelEvent.cs:25-30` | chez un invité, l'arrêt d'une progression sous un acte marqué est exécuté tout de suite, sans delta ni attente |
| `dev/_tools/dummy_suite.py` | étape M4 : peinture (`AI_Paint`) |

Le marquage est par objet (`ConditionalWeakTable`) : pas de remise à zéro à faire, rien ne reste accroché quand l'acte
disparaît, et l'arrêt de l'ancienne tâche pendant `SetAI` voit encore son propre marquage.

### Tâche par tâche : ce qui arrive chez l'host (lu dans le jeu et le mod, rien joué)

| Tâche | Qui la lance (jeu) | Avant | Maintenant chez l'invité | Ce qui passe chez l'host | Ce qui ne passe pas |
|---|---|---|---|---|---|
| `AI_Paint` | `AM_Paint.cs:78`, `pc.SetAI` | annoncée, retenue, arrêtée par l'host | va au bout (10 pas ; 2 pour l'appareil photo) | l'expérience et l'endurance : aucune dans cette tâche | la toile peinte : `Split(1)` + `c_textureData` + `isModified` + `TryHoldCard` (`AI_Paint.cs`) restent dans le jeu de l'invité. Le mod n'a aucun delta pour `c_textureData` (recherche : aucune occurrence). Si la pile compte plus d'une toile, `Split` d'une carte de l'host est « en attente » (`CardSplitEvent`) et l'original n'est pas touché (`CardModNumEvent.cs:13-16`) : l'host ne voit rien |
| `AI_Torture` | `ActRestrain.cs:48` : la cible reçoit la tâche. Un invité la reçoit seulement s'il s'attache lui-même (si la cible est un allié, c'est une tâche d'un personnage non joueur, `CharaTaskRemoteEvent.cs:40-42`, pas concernée) | annoncée, arrêtée | tourne (10 000 pas, `CanManualCancel` vrai : arrêt seul) | l'état de l'invité par les chemins ordinaires (endurance : `CharaSynchronizationContext.cs:65-73`) ; `ConInvulnerable` à la fin (`AI_Torture.cs`, condition : chemin ordinaire, pas suivi jusqu'au bout) | l'effet de la tâche : la progression envoie les alliés attaquer (`item.SetEnemy(owner)`), dans le jeu de l'invité seulement. Les alliés sont joués par l'host, dont la copie de la tâche est vide : personne ne vient. L'invité « s'entraîne » sans rien subir |
| `TaskCraft` | `LayerCraftFloat.cs:105`, `pc.SetAI(taskCraft)` : seul chemin | annoncée, arrêtée (rien ne se passait) | **tourne et finit** (5 pas) | l'expérience : 3 x 20 à la progression et 200 à la fin (`TaskCraft.OnProgress/OnProgressComplete`, `ElementChangeDelta` comme au mannequin) ; l'endurance (`costSP`, même chemin) ; les ingrédients d'une pile ENTIÈRE : `Split(n == Num)` rend la carte même, `Destroy()` part en `CardModNumDelta` Num = 0 (`CardDestroyEvent`) | **le produit** : `recipe.Craft` crée l'objet avec `ThingGen` chez l'invité, hors contexte « en attente » : `CardGenEvent` le met en `DelayDestroy`, `CardCache.Update` le détruit à l'image suivante, l'host ne le voit jamais. Les ingrédients d'une pile PARTIELLE : `Split` crée une copie en attente, la pile de l'host n'est pas diminuée (`CardModNumEvent`) |
| `TaskDesignation` (tâches de désignation du mode construction) | je n'ai trouvé aucun `SetAI` du joueur sur elles dans le jeu (`ActPlan` ne lance que les actes proposés, les connus de la table pour la coupe, la mine…) | — | pas concernée | — | — |
| `TaskMoveInstalled` | aucun `new TaskMoveInstalled` dans le jeu. `AM_Designation.cs:94-100` : le mode construction la fait finir par l'agent (`owner = Agent`, `OnProgressComplete()` appelé directement), ou la laisse en désignation pour des travailleurs | — | pas concernée par ce correctif (ce n'est pas la tâche du joueur) | — | le déplacement fait par l'agent d'un invité : `AgentTaskDelta.TrySend` ne connaît que `TaskBuild/Mine/Dig/Cut` (`AgentTaskDelta.cs:50-56`) et `CharaProgressCompleteEvent` ne rattrape que ces cas : le meuble bouge dans le jeu de l'invité seul. Hors table et hors de ce lot ; pas vérifié que le mode soit ouvert à un invité |

Tâches d'un autre mod : si elles passent par `SetAI` du joueur et sont absentes de la table, elles tournent maintenant
chez l'invité sans que l'host le sache (même règle : ce que leurs effets font et qu'aucun delta ne porte reste chez
l'invité).

Autre tâche inconnue vue en passant : `TaskDump` (`TaskDump.cs:15`, `pc.SetAIImmediate`) : `TaskDumpArgs` existe mais
n'est pas dans la table (`CharaTaskRemoteEvent.cs`). Non regardée. `DynamicAIAct` (le déplacement puis l'acte de
`ActPlan.cs:104`) est aussi inconnue de la table : sa tâche enveloppe n'a pas de progression, mais une progression lancée
dessous est maintenant locale.

### Pas sûr, à ne pas oublier

- **Rien n'a tourné.** Compile seulement (`ReleaseNightly`, 0 erreur, 0 avertissement).
- **`TaskCraft` : avant, l'invité n'obtenait rien ; maintenant il peut perdre ses ingrédients (piles entières) sans produit.**
  À régler avant publication : soit une vraie prise en charge (voir `AI_UseCrafter` / `RemoteCraft`), soit garder
  `TaskCraft` hors de la règle (une ligne : ne pas marquer `TaskCraft` dans `CharaTaskRemoteEvent`, elle retombe dans
  l'ancien comportement, arrêtée par l'host).
- Plus généralement : une tâche inconnue qui ne finissait jamais finit maintenant, et ce qu'elle change sans delta
  reste dans le jeu de l'invité (une divergence possible, au lieu d'un arrêt). C'est le prix du « seul » ; seule la
  liste ci-dessus dit lesquelles sont connues.
- Un invité seul sur une autre carte : `NetSession.Instance.Connection` est nul (`CharaTaskRemoteEvent.cs:18`,
  `CharaProgressBeginEvent.cs:24`, tous les événements rendent la main), le jeu tourne comme en solo : inchangé. Un
  invité qui tient une carte avec d'autres joueurs : sa session de zone est un host (`NetSession.InitializeZoneSession`),
  `connection.IsClient` est faux. Les deux cas lus dans le code, jamais joués.
- M4 de `dummy_suite.py` : `first_id("Painter")` / `first_id("Canvas")` supposent que les lignes d'objet du chevalet et
  de la toile ont ces traits (nom de classe sans `Trait`) ; sinon la première vérification échoue en le disant. L'arrêt
  de (b) est un `Cancel()` direct après quelques `Tick()` (pas un arrêt de joueur). Rouge attendu avant la correction :
  (b) « la tâche tourne encore : True », (a) « no matching act ».
