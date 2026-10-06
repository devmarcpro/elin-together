# Ramassage en marchant, sac plein : l'objet « disparaît » chez l'invité

Retour d'une vraie partie, 0.26.510 : « un invité marche sur des items et ils disparaissent alors qu'il a
l'inventaire plein ». Écrit le 2026-10-06. Rien n'a été lancé en jeu : tout ce qui suit est **lu dans le code**, sauf
mention « supposé ». Jeu : `dev/_decomp/Elin_23351`. Mod : `ElinTogether/`.

## 1. Ce que fait le jeu en solo

- Le ramassage en marchant est dans `Chara._Move`, pour le joueur seulement : chaque objet libre de la case
  (`placeState == roaming`, pas `ignoreAutoPick`) passe par `Pick` (`Chara.cs:3279-3332`). (`TryPickGroundItem`,
  `Chara.cs:4724`, ne sert qu'à la pêche.)
- `Chara.Pick` (`Chara.cs:4606-4654`) demande d'abord une place : `things.GetDest(t, tryStack)` (`:4618`).
  - Pas de place et l'objet est par terre : message « sac plein » (`backpack_full`), **l'objet reste par terre**
    (`:4630-4634`).
  - Pas de place et l'objet vient d'ailleurs (main, coffre, objet neuf) : « sac plein », il **tombe aux pieds**
    (`_zone.AddCard(t, pos)`, `:4621-4628`).
  - Une pile du même objet existe : il la rejoint, même sac plein (`:4636-4644`).
- `GetDest` (`ThingContainer.cs:413-453`) : piles d'abord (sac et sacs dans le sac), puis une case libre ;
  `IsFull()` (`:293-320`) lit la grille du sac (`GetFreeGridIndex`), et sans grille compte tous les objets.
- `Card.AddThing` (`Card.cs:3285`) ne vérifie rien : dans un sac sans case libre l'objet est ajouté quand même,
  sans case (`ThingContainer.OnAdd`, `:275-285`). Il n'est dessiné nulle part ; il reprend une case dès qu'une se
  libère et que la fenêtre du sac se redessine (`RefreshGrid`, `ThingContainer.cs:106-142`, `UIInventory.cs:1362`).

## 2. Cause (lue dans le code) : l'invité annonce le ramassage avant de savoir s'il a la place

Invité sur la carte de l'host, sac plein, il marche sur un objet :

1. Jeu de l'invité, `CharaPickThingEvent.OnCharaPickThingy` (avant correction) : le `CharaPickThingDelta` part vers
   l'host **avant** que le jeu ait regardé le sac, puis `Pick` tourne : « sac plein », l'objet reste par terre.
2. Jeu de l'host, `CharaPickThingDelta.OnApply` : `chara.Pick(thing)` (`CharaPickThingDelta.cs:65`). L'host aussi
   trouve le sac plein, l'objet reste par terre… puis le bloc « force add » le range **de force** dans le sac de
   l'invité (`:67-74`, `chara.AddThing` sous `Simulate()`), ce qui envoie un `CardAddThingDelta` à tout le monde
   (`CardAddThingEvent.cs:157`).
3. Jeu de l'invité, `CardAddThingDelta.OnApply` : `parent.AddThing(thing…)` (`CardAddThingDelta.cs:82`) dans un
   sac sans case libre. L'objet quitte le sol et entre dans le sac **sans case** : il n'est plus visible nulle part.

Ce que le joueur voit : « sac plein », l'objet encore par terre un instant, puis plus rien. L'objet n'est pas
détruit : il est dans le sac (poids compté, sauvegardé) et réapparaît quand une case se libère. Trace dans le
journal de l'host : `Mirror pick of … failed to store, forcing into chara …`.

Le « force add » a une raison : l'host n'a pas la grille du sac d'un invité et compte aussi ce qu'il porte sur
lui (`PlayerTrade.cs:478-484`), il croit donc le sac plein plus tôt que l'invité. Quand l'invité a vraiment pris
l'objet, il faut que l'host suive. Le défaut est en amont : l'annonce part même quand l'invité ne prend rien.

Variante (lue) : si l'host trouve une place que l'invité n'a pas (un sac dans le sac), il range l'objet sans rien
renvoyer (`CardAddThingEvent.cs:116`, on est dans un delta) : l'objet reste par terre chez l'invité mais n'existe
plus chez l'host, et sera dans le sac au prochain alignement.

## 3. Les trois situations

| Situation | Avant correction (lu) |
|---|---|
| Invité sur la carte de l'host | le défaut ci-dessus |
| Invité seul sur une autre carte | `Connection` vaut `null` (`NetSession.cs:40`), tous les patchs de ramassage rendent la main : **comme en solo**, pas de défaut |
| Visiteur sur la carte tenue par un autre invité | celui qui tient la carte est `ElinNetHost` d'une session de zone : même code, **même défaut** pour le visiteur |
| L'host (ou celui qui tient la carte), sac plein | il annonce aussi avant de regarder ; chez les invités, `CharaPickThingDelta.cs:94-98` range l'objet de force dans leur copie de son sac : l'objet quitte le sol **chez les invités seulement** |

## 4. Autres causes possibles (supposées, moins probables)

- Objet rendu par une récolte ou une mine faite pour un invité (`PickOrDrop` / `TrySmoothPick` empaquetés,
  `CharaPickThingEvent.cs`, rejoués chez l'invité) : sac plein, le jeu de l'invité le pose par terre et le dit à
  l'host (`CharaPickThingDelta.cs:101-105`). Avant correction, si le rejeu passait par `Pick`, l'annonce partait
  aussi et l'host rangeait de force avant de recevoir « par terre » : ordre des deux messages non vérifié en jeu.
- Objet inconnu de l'host dans le jeu de l'invité (`!CardCache.Contains(t)`, `CharaPickThingEvent.cs:33-37`) :
  `Pick` ne fait rien et rend l'objet. Il reste par terre, il ne disparaît pas.
- Récompense ou don fait par l'host dans un sac plein (`AddThing` direct) : sans case aussi, mais c'est ce que fait
  le jeu en solo.

## 5. Correction faite (un seul fichier)

`ElinTogether/Patches/DeltaEvents/Chara/CharaPickThingEvent.cs` :

- `:14-23` `WillStore` : ce que `Chara.Pick` vérifie avant de ranger (déjà dans le sac, carte à collectionner
  ramassée d'office, sinon `things.GetDest(t, tryStack).IsValid`).
- `:58-64` : pour son propre personnage (`__instance.IsPC`, invité comme host), si `WillStore` est faux, le
  `CharaPickThingDelta` **ne part pas** ; le jeu fait ensuite ce qu'il fait en solo : « sac plein », objet laissé
  par terre, ou posé aux pieds par `Zone.AddCard`, que `ZoneAddCardEvent.cs:48-53` transmet déjà.

Rien d'autre ne change : sac avec de la place ou pile existante, l'annonce part comme avant. Aucun format de
message ni de sauvegarde touché. Compilation `ReleaseNightly` hors du jeu : 0 erreur.

Durcissement possible, **non fait** (fichier hors de la liste autorisée, `Models/Delta/Chara/CharaPickThingDelta.cs`) :
rien à changer si tous les joueurs ont la même version ; un invité resté en 0.26.510 chez un host corrigé garde le
défaut (il annonce toujours).

Objets déjà « disparus » dans une partie en cours : ils sont dans le sac de l'invité, sans case. Libérer des cases
puis rouvrir le sac les fait réapparaître (lu, pas vu).

## 6. Test : `dev/_tools/pickup_suite.py` (jamais lancé)

P1 invité sur la carte de l'host (seau : reste par terre dans les deux jeux ; caillou avec des cailloux dans le
sac : entre dans le sac), P2 host (témoin), P3 invité seul à Vernis puis retour. Attendu sur la 0.26.510 : P1 rouge
sur le seau, P2 rouge sur le seau côté invité, P3 vert. Ce que le banc ne joue pas : en tête du fichier (sac rempli
par l'host, marche par `AI_Goto`, pas de visiteur chez un autre invité, pas de récolte sac plein).

## 7. Pas sûr

- Rien n'a tourné en jeu : la chaîne du point 2 est une lecture, pas une observation.
- Le cas « pile » sur la 0.26.510 est supposé vert (l'invité envoie aussi un `CardTryStackToDelta`,
  `CardTryStackToEvent.cs:37-44`, l'host empile de son côté).
- Une potion ramassée par un personnage qui a le don 1565 peut être changée avant le calcul de la place
  (`TryPoisonPotion`, `Chara.cs:4617`) : `WillStore` regarde la potion d'origine. Écart ignoré.

## 8. Deux questions pour le joueur

1. Après avoir vidé quelques cases et rouvert le sac, les objets « disparus » sont-ils revenus ?
   (oui : c'est la cause du point 2)
2. Était-il sur la même carte que l'host (ou qu'un autre joueur) quand c'est arrivé, ou seul ailleurs ?
   (seul ailleurs : ce n'est pas cette cause, il faut chercher autre chose)
