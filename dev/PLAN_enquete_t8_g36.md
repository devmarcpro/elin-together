# Enquête : T8 (NullReference chez l'invité) et G36 (laisse), 2026-10-06

Lecture seule. Rien n'a été compilé ni joué. « vérifié » = lu dans le code ou un journal. « non vérifié » = supposition.

## A. `together_suite` T8 : `CharaDieDelta` lève NullReferenceException chez l'invité

### Faits vérifiés
1. Ce ne sont pas les coups de l'invité. Ce sont les `c.Die()` du banc, appelés sur l'host au début de T8
   (`dev/_tools/together_suite.py:404`, `foreach (var c in alive.Skip(1)) c.Die()`). Preuves :
   - nuit2 : 10 monstres (`together_suite-nuit2.log:82`), 18 lignes d'exception = 2 x 9 ; pub : 13 monstres, 24 = 2 x 12 ;
     nuit et nuit4 : 0. Le nombre de lignes = (monstres - 1) x 2.
   - Journal de session (voir 3) : les exceptions portent les uid 101080 à 101092, sans 101087 : le dernier monstre,
     tué à l'épée par l'invité (Origin = invité, Melee), ne lève rien.
   - Elles tombent 7 s après l'activation de la zone chez l'invité et 0,7 s après le « died » de l'host (`Session_20261005.log`,
     13:05:54.7 UTC), donc pas pendant un chargement ni une sortie de zone.
2. Le delta est `Origin = None, ElementId = None, AttackSource = None` (champ `Delta` du journal). Même boucle en T2
   (`together_suite.py:158`) : aucune exception, jamais. La différence T2/T8 : en T8 la quête est celle de l'invité, sa zone
   est celle qu'il a demandée (uid 72) puis reprise par l'host (« Zone lease 72 denied: quest_follow_coming », « Received zone
   state »), et ses événements de zone sont remplacés par ceux de l'host (`ElinNetClientTravel.cs:594-609`).
3. La pile est gardée, le banc ne l'affiche pas. `LocalLow/Lafrontier/Elin/ElinMP/Logs/Session_AAAAMMJJ.log` (JSON, champ `@x`) ;
   le banc ne montre que les lignes contenant « Exception » (`travel_suite.py:581-584`). Pile, identique dans les 21 cas lus :
   `DMD<Stub_Die>` puis `CharaDieDelta.cs:41`, `ElinDelta.cs:157`, `ElinDeltaManager.cs:125`. Aucun cadre en dessous.
   Conséquence : le déréférencement est dans le corps de `Chara.Die` lui-même (ou un accesseur trivial inliné), pas dans
   `ZoneEventSubdue.CheckClear` (`dev/_decomp/Elin/ZoneEventSubdue.cs:36`), `Effect`, `Msg` ni `SpawnLoot` (déjà coupé
   chez le client, `CardSpawnLootEvent.cs:10`), qui auraient leur propre cadre.
4. Ce n'est pas `OnApply` avant `Stub_Die` : `Owner.Find()` a trouvé le monstre (sinon retour ligne 28), `Origin` null est géré.
5. Tout ou rien par passage : les 9 (ou 12) monstres échouent tous, ou aucun. La cause est un état du jeu de l'invité,
   pas une propriété d'un monstre.
6. Corrélation (vérifiée, 5 passages lus, trop peu pour conclure) : les deux passages rouges (13:05Z, 22:07Z) ont dans le
   journal de l'host « Reset remote on 636, was NoGoal » (`CharaTaskRemoteEvent.cs:33`) entre « Assigned zone sync position » et
   « Received zone activation » ; les trois verts (15:50Z, 21:38Z, 23:30Z) non. Le personnage de l'invité a été recréé chez
   l'host dans les rouges seulement. Lien avec le NullReference : non vérifié.

### Objets qui peuvent être nuls dans `Chara.Die` (`dev/_decomp/Elin/Chara.cs`), du plus probable au moins probable (non vérifié)
- `currentZone` : lignes 5863 (`currentZone.IsActiveZone`) et 5872 (`currentZone.RemoveCard(this)`). C'est
  `RefZone.Get(_cints[1])` (Chara.cs:260, `RefZone.cs`) = `game.spatials.map[uid]` ; nul si le jeu de l'invité ne connaît pas
  la zone que porte le monstre (zone 72 créée par l'invité puis remplacée). Après `isDead = true` (5827).
- `EClass._map.props.sales` (5833) ou `EClass._map.deadCharas` (5870) : carte pas encore rattachée à la zone active.
- `renderer` (5732) : seulement si le monstre est dans la zone active.
- `EClass._zone.events` (5993) : peu probable, la liste existe (T7 lit `GetEvent<ZoneEventSubdue>` chez l'invité).

### Ce que ça casse
- Selon la ligne : avant 5827, le monstre reste vivant chez l'invité et mort chez l'host ; après, `isDead = true` mais le monstre
  reste dans la liste de la carte, et `events.OnCharaDie` (5993) n'est pas appelé : le compteur « monstres restants »
  de l'invité (`enemies`) ne baisse pas. Non vérifié lequel.
- T8 ne le voit pas : il compte les morts chez l'host (`together_suite.py:407-413`), et chez l'invité seulement le dernier monstre.
- Un vrai joueur : oui, probablement. Même chemin : il prend la quête, l'host vient avec lui et tue les monstres. Le test
  tue sans auteur ; avec un auteur (coup d'épée) le même état nul donnerait la même erreur si la cause est la zone
  (non vérifié : le dernier coup avec auteur n'a rien levé, mais il tombe plus tard dans le passage).

### Plus petite correction proposée (non écrite)
1. Sans toucher au mod : faire afficher la pile par le banc. Dans `scan_logs` (`travel_suite.py:583`, importé par
   `together_suite`), afficher aussi les 3 lignes qui suivent un « NullReferenceException », ou lire le champ `@x` du journal de
   session. Un rouge sur trois suffit pour nommer la ligne de `Chara.Die` (la pile donne le décalage IL, comparer avec 5863/5833/5732).
2. Si c'est `currentZone` (le plus probable) : une ligne au début de `CharaDieDelta.OnApply`, avant `Stub_Die` :
   `chara.currentZone ??= EClass._zone;` (même geste que `ElinNetClientZone.cs:178`). À ne mettre qu'après la pile.
   Si c'est `_map` nul : copier la garde de `CharaMoveDelta.cs:41-45` (`core.game?.activeZone?.map is null` → `DeferLocal`).

## B. `guest_suite` G36 : la laisse du compagnon de l'invité

### Faits vérifiés
1. Quatre rouges identiques (regr1 02:50, nuit3, nuit4, pub2), un vert en suite complète (regr4 08:50), vert seul. Dans les
   quatre rouges le chat reste sur la case où il est né, (42,39) ou (41,39) (`guest_suite-nuit3.log`, `-nuit4`, `-pub2`,
   `-regr1`) ; dans regr4 il finit en (46,40), à côté de l'invité qui a marché de 5 cases : il a suivi.
2. « détacher : action absente, proposées : » vide est une conséquence du premier rouge, c'est le banc. L'invité est à 5 ou 6
   cases du chat (`gap` lu juste avant). `TraitLeash.TrySetHeldAct` (`dev/_decomp/Elin/TraitLeash.cs:5`) n'offre rien sans
   `p.IsSelfOrNeighbor` ; le banc le fixe à `dist <= 1` (`guest_suite.py:73`). L'attente `gap <= 1` (ligne 1059) n'a aucune
   suite si elle échoue : le test détache quand même à distance 5 (ligne 1063). Un chat qui ne suit pas donne
   toujours cette ligne.
3. Le côté host est vert dans les 4 rouges (le chat suit, distance 1) : la règle du jeu (`Chara.cs:3267`) fonctionne
   dans cette zone et ce banc.
4. La règle du mod (`GuestLeash.Follow`, `CardActReplayEvent.cs:130-144`) = celle du jeu, avec deux différences :
   la clé `emp_leash` à la place du bit `isLeashed`, et « garder ses distances » lu chez l'invité
   (`PlayerTacticsDelta.KeepDistanceOf` sinon réglage de l'host), ajouté par le commit 9155835 (05/10 08:11). Le premier
   rouge (regr1, 02:50) est antérieur à ce commit : ce n'est pas la cause d'origine.
5. `Follow` est appelé seulement si l'host a appliqué le pas de l'invité (`CharaMoveDelta.cs:77-88`). L'host voit l'invité 5
   cases plus loin (`gap` côté host), donc les pas passent.
6. `EClass._zone.KeepAllyDistance` est vrai dans cette zone (`hunt_suite.py:455` le contrôle). Donc le réglage « garder ses
   distances » compte ici.
7. g31 à g35 ne laissent ni monstre hostile ni compagnon : g31 remet la piété de l'invité mais pas `c_daysWithGod = 100` posé
   chez l'host (`guest_suite.py:774`) ; g32 détruit l'autel ; g33 détruit meuble et tickets ; g34 et g35 appellent
   `clear_conditions` ; g35 détruit le puits. Seul `hunt_suite` touche à `allyKeepDistance` (`hunt_suite.py:459-492`), et le
   remet à faux dans un `finally`. Aucun test de la suite ne règle les tactiques de l'invité.
8. Le chat est créé paralysé par le banc (`guest_suite.py:951`), puis `clear_conditions(m)` (ligne 1033, définie 848-852) tue les conditions chez
   l'host et chez l'invité.

### Ce qui empêche la laisse de tirer (non vérifié : le banc ne mesure rien à cet instant)
Conditions de `Follow` (lignes 139-140) et du jeu : `!IsDisabled`, `!IsInCombat` (`ai is GoalCombat`, `Chara.cs:913`),
pas `ConEntangle`, pas `host`, pas de « garder ses distances ».
1. Le chat est en combat (`GoalCombat`) ou désactivé : un chat immobile 30 s à (42,39) et un chat qui ne suit pas non plus
   par son IA ordinaire (écart 5-6 pendant 30 s, `ConfigTactics.AllyDistance` = 5 si la case est cochée) vont avec
   « case cochée » ou « en combat ». Le HANDOFF penchait pour le combat. Piste la plus simple.
2. `emp_tactics` de l'invité dit « garder ses distances » : envoyé par `RemoteTacticsPatch.Update` toutes les 10 s depuis le
   jeu de l'invité (`RemoteTacticsPatch.cs:36-57`) ; défaut du jeu = faux (`ConfigTactics.cs`), donc il faudrait un réglage laissé
   par un autre test ou une autre suite chez l'invité.
3. `Follow` jamais appelé ou `CompanionsOf` ne renvoie pas le chat : peu probable (vert seul, vert côté host).

### Banc ou mod ?
Pour « détacher vide » : le banc. Pour « le chat ne suit pas » dans la suite : inconnu. Rien ne montre une erreur du mod
(règle identique à celle du jeu, vert seul et côté host). Un joueur le vit déjà dans le jeu seul : laisse + compagnon en
combat ou case « garder ses distances » cochée = pas de traction. Si c'est la cause 3 (clé ou propriétaire), un vrai
joueur aussi : non vérifié.

### Plus petite correction proposée (non écrite)
1. `guest_suite.py` g36, juste après `walk` (avant la ligne 1059) : une seule mesure, dans le libellé du test :
   `ev(H, ...)` qui rend pour le chat `IsInCombat`, `IsDisabled`, `ai.GetType().Name`, `Dist` à l'invité, `emp_leash`,
   `IsCompanionOf`, `EClass._zone.KeepAllyDistance`, `emp_tactics` de l'invité (`GetInt("emp_tactics")`) et
   `EClass.game.config.tactics.allyKeepDistance`. Un rouge sur trois la donne.
2. Avant de détacher (ligne 1059) : si `gap > 1`, `stand(port, uid, cx, cz)` (ligne 95) ou `free_next_to`, pour que
   « détacher » ne dépende plus du premier rouge. Cela ne répare pas la laisse, cela sépare les deux rouges.
3. Mod : rien à changer avant la mesure 1. Si elle montre `IsInCombat = True` : le mod suit le jeu, ajouter au test
   `m.enemy = null; m.SetAI(new NoGoal())` pour le chat (et chercher quel ennemi le rend hostile) ; si elle montre
   la case cochée : poser `emp_tactics`/`allyKeepDistance` à faux au début de g36, comme `hunt_suite` à la fin.
