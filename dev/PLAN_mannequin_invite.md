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

Correction générale possible (pas faite, fichiers hors de ce lot) : pour une tâche partie comme `FakeTask`, ne pas
annoncer la progression (`CharaProgressBeginEvent.cs:42-58`) et laisser l'invité arrêter seul
(`CharaTaskCancelEvent.cs:25-28`).
