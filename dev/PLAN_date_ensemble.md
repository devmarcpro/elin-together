# La date : « le temps ne saute que quand tous sautent ensemble » (conseil 10, point iv)

2026-10-06. Écrit et compilé à part (ReleaseNightly, 0 erreur, 0 avertissement). **Rien n'a été joué** : le jeu
était pris. Les tests sont écrits, pas lancés.

## Ce qui est fait

1. **Chronomètre des quêtes** (récolte, concert, mariage).
   - `Patches/DeltaEvents/World/WorldDateAdvanceEvent.cs` (postfix de `AdvanceMin`) : pendant un rattrapage
     (`IsCatchingUp`, le temps qu'un autre a fait passer ailleurs), les minutes que le jeu vient d'ajouter à
     `zone.events[].minElapsed` sont retirées. Vaut pour l'host comme pour l'invité qui tient une carte.
   - `Models/Delta/World/WorldDateAdvanceDelta.cs` : l'invité sur la carte de l'host n'ajoute plus les minutes
     d'un message marqué `CatchUp` (il suit le chronomètre de celui qui tient la carte).
2. **Le pas qui ne fait plus sauter les autres**, `Patches/Remote/RemoteTravelRegionPatch.cs`.
   - L'appel `date.AdvanceMin(pas × 6)` de `Chara._Move` est remplacé par `StepDate` : la date n'avance que si
     `DateMoves()` : case décochée, ou partie sans session, ou **host et tous les joueurs sur la carte du monde**.
   - `Net/Host/ElinNetHostTogether.cs` (fichier neuf, morceau de `ElinNetHost`) : `AllOnWorldMap()`. Un joueur
     compte comme « sur la carte du monde » s'il est sur la carte de l'host (qui y est), ou parti avec, pour
     seules cartes prêtées, des cartes du monde. En chargement, entre deux cartes, ou en visite chez un autre : non.
   - Message `emp_ui_travel_no_date`, une fois par voyage (remis à zéro au premier pas hors carte du monde), chez
     celui dont le pas aurait fait avancer la date avant : l'host, ou l'invité seul sur sa copie de la carte.
   - **Voyage express** : traité. `TravelExpressPatch` remplace l'appel `AdvanceHour` de la fonction générée de
     `LayerTravel` (trouvée par ce qu'elle appelle ; vérifié sur la DLL du jeu : une seule, `<Refresh>b__3`).
     Même règle : les heures ne passent que si tous voyagent. Le voyageur a payé ses rations ; le jeu ne joue
     aucun tour de faim pour un voyage express, en solo non plus.
3. **Le pas de l'invité aux côtés de l'host** (même fichier). Case cochée, le bloc du pas tourne aussi chez
   l'invité : ses ~120 tours sont joués dans son jeu (ils partent vers l'host comme tous ses tours), la date ne
   bouge pas. `TravelStepTurnsPatch` (préfixe de `Chara.TickConditions`, actif seulement pendant un pas) : le pas
   ne fait vivre ses tours qu'au joueur qui marche et à SES compagnons. Chez l'invité, les tours de ses compagnons
   sont demandés à l'host (`CharaTickConditionDelta`, un par tour, comme pour son personnage).
   Effet voulu chez l'host aussi : son pas ne fait plus vivre 120 tours aux compagnons des autres joueurs
   (aujourd'hui si, même quand leur joueur est parti ailleurs).

Case décochée : exactement le comportement d'avant (seul le jeu qui simule joue le pas, chaque pas ajoute ses heures).

## Textes à ajouter (pas faits : `package/LangMod/**` interdit pour ce lot)

| identifiant | anglais | japonais | chinois |
|---|---|---|---|
| `emp_ui_travel_no_date` | Your friends are elsewhere: your trip does not move the date. | 仲間は別の場所にいる。この旅では日付は進まない。 | 同伴们在别处：你的旅行不会让日期前进。 |

Tant que le texte manque, le jeu affiche sans doute l'identifiant (pas vérifié).

## Lignes ailleurs

Aucune nécessaire. Rien n'a été écrit dans `PersonalQuests.cs`, `SleepSynchronizationContext.cs`, `EmpConfig.cs`,
`NetSessionRules.cs`, `ElinDelta.cs` (pas de nouveau message réseau).

## Raccourcis assumés (`// ponytail:` dans le code)

- **La date n'avance que par les pas de l'host**, comme l'écrit le verdict. Un invité seul sur sa copie de la
  carte du monde ne la fait jamais avancer, même si tout le monde est sur la carte du monde : il faudrait lui
  dire où sont les autres (un message réseau de plus). C'est une différence host/invité qui reste : host immobile
  sur la carte du monde, invité qui marche : pas de date ; l'inverse : la date avance.
- Un joueur **mort** loin de l'host compte encore comme « ailleurs » : l'host ne sait pas qu'il est mort là-bas.

## Ce qui n'est pas sûr (pas joué)

- L'abandon du pas quand la vie tombe sous un cinquième (`regionAbortMove`) ne se déclenche sans doute pas chez
  l'invité à côté de l'host : ses dégâts de faim sont appliqués par l'host et reviennent après le pas. Un invité
  affamé peut donc enchaîner des pas sans l'avertissement que l'host reçoit.
- Les tours des compagnons de l'invité : 120 messages par compagnon et par pas vers l'host. C'est le volume que
  l'host envoie déjà pour ses propres pas, mais pas mesuré dans ce sens.
- La mer : l'invité à côté de l'host peut maintenant suffoquer en marchant sur l'eau de la carte du monde, comme
  l'host (le bloc ne tournait pas chez lui). La demande à l'host existait déjà (`CharaAddConditionEvent`).
- `player.lastZonePos` est maintenant remis à zéro par le pas de l'invité, comme en solo : en entrant sur une
  carte après avoir marché il arrive par le bord, plus à la case où il avait quitté sa dernière carte.
- Le voyage express d'un invité à côté de l'host appelait `AdvanceHour` dans son jeu ; case cochée il ne le fait
  plus. Ce que cet appel faisait chez lui n'a pas été étudié.

## Inégalités qui restent (vues, pas touchées : hors des trois étapes)

- Quand tous marchent ensemble et que l'host fait un pas : la date saute de trois heures pour tous, mais seuls le
  sac et les délais de quête de l'HOST vivent ces heures ; ceux des invités sont protégés (`LivesThisHour`,
  `PersonalQuests.Postpone`), comme avant. Pour l'égalité il faudrait un champ « saut commun » dans
  `WorldDateAdvanceDelta` et une ligne dans `LivesThisHour`.
- L'invité qui marche avec l'host pendant qu'un troisième est en ville ne lit pas le message (il ne sait pas où
  sont les autres) ; l'host le lit.
- Le voyage express de l'host, tous ensemble : les heures passent sans message (déjà vrai avant).

## Tests (`dev/_tools/time_suite.py`), écrits, pas lancés

- W7 chronomètre, deux sens ; W7e = l'ancien W7 (voyage express), sa NullReferenceException corrigée (le banc
  prenait chez l'invité une quête que l'host venait de faire proposer, avant qu'elle n'arrive) ;
- W8, W8b : cinq vrais pas d'un joueur seul sur la carte du monde ; W9 : les deux sur la carte de l'host ;
- `TOGETHER_OFF=1` : case décochée, W8, W8b, W9 doivent échouer comme avant.
- W1, W2, W4 : inchangés (minute par minute, même date au retour : toujours vrai). W3 et W6 : même code, texte
  changé : ils ne décrivent plus « une nuit » ni « un voyage » (qui ne font plus sauter la date d'un autre), mais
  la protection du corps pour les sauts qui restent (nuit commune, cases décochées).
- Pas joué par le banc : compagnons, voyage express réel, troisième joueur, invité sur sa propre copie de la
  carte du monde pendant que l'host y marche, concert et mariage.
