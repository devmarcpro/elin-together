# Plan — « donjon conquis alors que le boss n'est pas vaincu »

Retour n° 15 (partie réelle, trois joueurs ou plus). Enquête en lecture seule : rien compilé, rien lancé.
Chemins du jeu : `dev/_decomp/Elin_23351/` (écrit `J/…`). Chemins du mod : `ElinTogether/…` (écrit `M/…`).
**Lu** = vu dans le code. **Supposé** = déduit, pas vu tourner.

## 1. Solo : comment le jeu décide qu'une Nefia est conquise (lu)

- Le boss est créé à la génération de l'étage le plus profond de la Nefia : `Zone_RandomDungeon.OnGenerateMap`
  (`J/Zone_RandomDungeon.cs:61-75`). Étage du boss = `LvBoss` = -2 moins 0 à 3, tiré avec la graine = numéro du
  sommet (`J/Zone_RandomDungeon.cs:30-38`). Il n'existe donc que sur un des étages -2 à -5.
- Le boss n'est pas un objet de la zone : seul son numéro est gardé dans la zone, `Spatial._ints[18]` = `uidBoss`
  (`J/Spatial.cs:273-284`). `Zone.Boss` le cherche à chaque fois dans la carte chargée :
  `EClass._map.FindChara(uidBoss)` (`J/Zone.cs:90-100`, `J/Map.cs:2766-2776`). Carte sans ce personnage = `Boss` nul.
- « Conquis » = un seul drapeau, `isConquered` = `bits[10]` du **sommet** de la Nefia (`J/Spatial.cs:381-390`).
  Il passe à vrai à DEUX endroits seulement :
  1. **Mort du boss** : `Chara.TryDropBossLoot` (`J/Chara.cs:6006-6023`, appelé par `Die`, `J/Chara.cs:5834`) :
     coffre de boss (`TreasureType.BossNefia`, 2 à 3 butins), message `boss_win`, `nefiaBeaten++`, fanfare, renommée.
  2. **Le boss « s'enfuit »** : `Zone.Simulate` (`J/Zone.cs:1297-1306`) :
     `if (!game.isLoading && visitCount > 0) { if (Boss != null && IsNefia) { message bossLeave; RemoveCard(Boss);
     top.isConquered = true; } ... }`. Aucun coffre, aucune renommée, mais la Nefia est marquée conquise.
  Un troisième cas, rare : le boss lit un parchemin d'évasion (`J/ActEffect.cs:1157-1165`, 1 chance sur 30).
- `Simulate` est appelé par chaque `Zone.Activate` (`J/Zone.cs:1172-1176`) ; `visitCount++` vient APRÈS, à la fin
  de `Activate`, sauf pendant un chargement de partie (`J/Zone.cs:1189-1192`). Donc : première visite = rien ;
  **toute entrée suivante dans un étage dont le boss vit = le boss s'enfuit**. C'est voulu : le jeu demande
  confirmation en sortant (`TraitNewZone.cs:155-163`, texte `ExitZoneBoss`). Charger une sauvegarde ne le déclenche pas.
- Affichage : suffixe « conquis » du nom (`J/Zone.cs:424-432`), icône de victoire sur la carte du monde
  (`J/ActionMode.cs:431-436`). Le message « beware » à l'arrivée n'apparaît que si `Boss` existe (`J/Scene.cs:321`).

## 2. Ce que le mod fait autour (lu)

- **Aucun code du mod ne parle de boss, `isConquered`, `uidBoss`, `visitCount`** (recherche dans `ElinTogether/`,
  hors `obj/` : rien). `Zone.Simulate` n'est pas touché. Seul le jeu décide, dans chaque jeu séparément.
- Mais le mod copie l'état entier d'une zone d'un jeu à l'autre : `ZoneLeaseState.GetState/ApplyState`
  (`M/Models/ZoneLease/ZoneLeaseState.cs:46-67`) copie TOUTES les valeurs `_ints` sauf 1, 3, 4 (numéro, x, y,
  `_hostOwnedInts`, l.14). Donc **`visitCount` (`_ints[8]`) et `uidBoss` (`_ints[18]`) voyagent avec la carte**.
- Où l'état est appliqué puis la carte activée :
  - Invité qui prend un bail : `TravelTo` : `WriteMap`, `ApplyState` (`M/Net/Client/ElinNetClientTravel.cs:295`),
    puis `pc.MoveZone` (l.307) = `Zone.Activate` chez l'invité. L'état envoyé est celui de la zone de l'host
    (`M/Net/Host/ElinNetHostTravel.cs:784`).
  - Host qui rappelle un étage tenu : `ApplyLeasedZone` (`ElinNetHostTravel.cs:1232-1260`, `ApplyState` l.1252),
    puis `ResumePendingHostMove` (l.1218-1230) = `Activate` chez l'host. L'état reçu est celui de l'invité
    (point de passage toutes les 60 s `ApplyCheckpoint` l.1164, ou rendu du bail l.1072).
  - Zone créée par l'invité : `CreateClientZone` (`ElinNetHostTravel.cs:1370-1405`), état pris AVANT la génération
    (visitCount 0, pas de boss) : sans effet ici.
- `KeepAlive`/`IsHeld` (`ElinNetHostTravel.cs:1438-1470`, `M/Patches/DeltaEvents/Zone/ZoneActivateEvent.cs:19-22`,
  `M/Patches/LeasedZonePatch.cs`) ne touchent que les dates d'expiration. Ils ne créent ni ne retirent de boss.
- Mort : `CharaDieEvent` (`M/Patches/DeltaEvents/Chara/CharaDieEvent.cs:12-33`) : l'host (ou l'invité qui tient la
  carte) fait mourir, les autres reçoivent `CharaDieDelta` (`M/Models/Delta/Chara/CharaDieDelta.cs:24-46`) qui
  rejoue `Die`, donc `TryDropBossLoot`. Rien ne touche le drapeau `isConquered` à part le jeu.
- Nettoyage : `RemoveUnplayedCharas` (`M/Net/Host/ElinNetHostPlayerManager.cs:76-91`) ne retire que les
  personnages marqués `remote_chara` : jamais un boss. `CharaRemoveFromGameDelta` : idem (personnages de joueurs).
- Invité sur la carte de l'host : sa zone vient de `SpatialGenDelta` (`M/Models/Delta/Zone/SpatialGenDelta.cs:46-79`),
  créée vide (`uidBoss` 0, `visitCount` 0) ; l'état envoyé avec la carte n'est lu que si la zone est inconnue
  (`M/Net/Client/ElinNetClientZone.cs:81-110`). Donc chez cet invité `Boss` reste nul (supposé : pas de « boss
  s'enfuit » ici, mais pas de message « beware » ni de coffre de boss non plus, voir 6).

## 3. Scénarios, du plus probable au moins probable

**A. (la plus probable, lu pour le mécanisme, jamais vu en jeu) Le premier `Activate` d'un jeu compte comme une
« deuxième visite ».** L'état copié apporte `visitCount ≥ 1` et `uidBoss` ; la carte copiée contient le boss vivant ;
`Zone.Simulate` croit que le joueur revient sur un étage où il a laissé le boss, donc : boss retiré, sommet conquis,
sans coffre. Trois façons d'y arriver, toutes ordinaires :
 1. Un invité arrive seul à l'étage du boss ; l'host (ou un autre invité) le rejoint. L'host rappelle l'étage,
    reçoit `visitCount ≥ 1`, entre : le boss s'enfuit chez l'**host**, `isConquered` écrit dans son monde (c'est
    celui qui reste dans la sauvegarde, d'où « donjon conquis » sur la carte du monde).
 2. L'host (ou un invité) a déjà visité l'étage du boss, puis un invité y descend : le bail lui envoie
    `visitCount ≥ 1`, son `Activate` fait fuir le boss chez **lui** (l'host ne voit pas de changement).
 3. Deux invités à des étages différents : chaque passage de bail d'un étage vu par un autre refait 1 ou 2.
 Cela colle à « on ne sait pas qui était à l'étage » : il suffit que deux jeux voient l'étage du boss l'un après
 l'autre. Cela explique « conquis » **sans** boss mort et sans message de victoire.

**B. (lu, moins probable) Le boss d'un jeu n'existe pas dans l'autre.** Non : le numéro du boss est dans la zone
et la carte l'a, les numéros de cartes sont réservés par l'host (plages, `ElinNetHostTravel.cs` `ReserveLease`).
Seul cas : l'invité dont la zone est inconnue de lui et qui garde `uidBoss` 0 (point 2, dernier tiret) : le boss
est là mais le jeu ne le voit pas comme boss ; ne produit pas « conquis ».

**C. (supposé, faible) Étage généré deux fois, dont un sans boss** : `AdoptHostUid` reconnaît « la même zone »
par id, x, y sans le niveau (`ElinNetClientTravel.cs:254`) et peut retirer le mauvais étage (déjà noté
`PLAN_donjon_regenere.md` §E). Un étage refait a un boss neuf, donc pas « conquis », sauf si le boss a changé
d'étage : à surveiller, pas la cause.

**D. (non retenu) Personnage retiré par le mod pris pour un boss mort** : rien dans le mod ne retire un boss
(voir §2). **E. (non retenu) Contrôle chez un joueur sans carte** : `Boss` vient de la carte chargée, pas de
contrôle séparé. **F. Deux étages différents** : ne crée pas « conquis » par lui-même, mais multiplie A.

## 4. Correction la plus petite pour A (non faite)

Règle : **un état qui vient d'un autre jeu ne compte pas comme une visite de ce jeu pour la fuite du boss.**
1. `M/Models/ZoneLease/ZoneLeaseState.cs` : dans `ApplyState`, noter le numéro de la zone dans un
   `HashSet<int> Imported` (une ligne).
2. Nouveau petit patch Harmony (un fichier, ~25 lignes, ex. `M/Patches/BossFleePatch.cs`) sur `Zone.Simulate` :
   préfixe : si `Imported.Remove(zone.uid)` et `zone.uidBoss != 0`, mémoriser `uidBoss`, le mettre à 0 ;
   finaliseur : le remettre. Résultat : `Boss` est nul pendant ce seul `Simulate`, la règle ne joue pas, et le
   boss reste sur la carte avec son numéro.
3. Même effet pour un invité dont la zone vient d'un instantané (`ElinNetClientZone.cs:94` chemin « zone inconnue ») :
   y poser la même marque. Hors bail, un jeu qui ne simule pas la carte n'a pas à faire fuir de boss.
Effet de bord assumé : dans le mod, quitter l'étage du boss puis y revenir ne le fait plus fuir si l'étage a changé
de mains entre-temps (plus indulgent que le jeu seul). Garder la règle exacte demanderait de décider à la sortie
du joueur, plus gros : à proposer seulement si le joueur la veut. Pas de case à cocher (réparation).
Alternative plus simple mais plus large : remettre `visitCount` local dans `ApplyState` (ajouter 8 à
`_hostOwnedInts`) ; refusé d'emblée : `visitCount == 0` déclenche aussi `dateRevive` (`J/Zone.cs:992`) et des
tutoriels (`Zone_DungeonPuppy.cs:24`) chez l'autre jeu.

## 5. Test au banc (rouge puis vert)

Base : `dev/_tools/travel_suite.py`, `cave_run` (l.513-580), `s18` (l.583). Aides : `ev`, `wait`, `check`, `marker`,
`enter_at`, `client_settled`, `both_joined`, `zone_uid`. Le monde de test n'a peut-être pas de Nefia (le journal
dit « pas de Nefia » ; non vérifié) : l'host en crée une depuis la carte du monde, avant que l'invité s'y rende :
`EClass.world.region.CreateRandomSite(EClass._zone, 5)` (`J/Region.cs:141-190`) ; la classe du lieu dépend de la
source tirée au hasard : relancer jusqu'à `is Zone_RandomDungeon`. Pas besoin de marcher jusqu'à `LvBoss` :
la règle ne demande que `IsNefia` et `Boss != null`, donc on pose un boss sur l'étage -2 :
`if (EClass._zone.Boss == null) EClass._zone.Boss = EClass._zone.SpawnMob(null, SpawnSetting.Boss(EClass._zone.DangerLv, EClass._zone.DangerLv));`
(même appel que `Zone_RandomDungeon.cs:64`), en notant `Boss.uid`.
- **s19a (invité d'abord, rappel par l'host)** : comme `cave_run` sans le vieillissement : l'invité descend à -2,
  on y pose le boss, on attend un point de passage ou on laisse le rappel faire monter la carte, l'host descend
  par l'escalier. Vérifier chez l'**host** : `EClass._zone.Boss != null && EClass._map.FindChara(uid) != null`
  et `!EClass._zone.GetTopZone().isConquered`. Rouge aujourd'hui (boss retiré, sommet conquis), vert après §4.
- **s19b (host d'abord, invité ensuite)** : l'host descend seul à -2 (bail en retour d'un invité resté dehors),
  pose le boss, l'invité descend à son tour ; mêmes assertions chez l'**invité**, après `client_settled`.
- Témoin vert dans les deux cas : l'étage -2 d'un donjon qui n'est pas une Nefia (`Zone_DungeonYeek`) : pas de
  boss attendu, `isConquered` faux ; et la mort réelle du boss (`Boss.Die(null)` chez celui qui tient la carte)
  doit encore mettre `isConquered` à vrai (garde-fou : la correction ne coupe pas la vraie victoire).
- Piège : dialogue de tutoriel (`dismiss_dialogs`), pas de saut d'étage à étage, une seule fenêtre invitée
  (règle des deux fenêtres du `CLAUDE.md`). Durée attendue ~10 minutes (comme s18), `--reuse --only s19`.

## 6. Trouvailles voisines (supposées, hors du retour, à garder)

- **Victoire d'un invité non transmise à l'host** : `isConquered` s'écrit sur le sommet (`Chara.cs:6021`), mais
  seul l'état de l'étage tenu voyage (`ZoneLeaseState`, `_ints` de l'étage). Un invité qui tue vraiment le boss
  marque conquis dans SON monde seulement. Même cause inversée : à tester après A.
- **Invité sur la carte de l'host** : `uidBoss` reste 0 chez lui (zone créée par `SpatialGenDelta`), donc
  `TryDropBossLoot` rejoué par `CharaDieDelta` ne reconnaît pas le boss (`Chara.cs:6006`) : ni fanfare ni
  renommée côté invité (supposé ; le coffre est créé par l'host, non vérifié). Inégalité host/invité à ajouter à
  la chasse aux différences.

## 7. À demander au joueur (trois questions)

1. Quand tu as vu « conquis » : y avait-il le message « le boss ... s'enfuit » (ou un nom de boss avec « quitte »),
   ou le message de victoire avec un coffre ? Et est-ce écrit sur la carte du monde pour tous, ou seulement chez toi ?
2. Qui est arrivé à l'étage du boss en premier (host ou invité) et l'autre l'a-t-il rejoint par l'escalier
   (boss encore en vie à ce moment-là) ?
3. Un joueur était-il déjà descendu dans ce donjon avant, puis revenu en haut, ou deux joueurs étaient-ils à des
   étages différents ? (Si oui, A est quasi sûre.)
