# Plan — donjon régénéré quand l'host rejoint un invité

Retour de partie réelle (0.26.506, 6 octobre 2026, trois joueurs ou plus) : un invité entre seul dans une cave et
descend ; l'host arrive au niveau -1, la carte « se recharge » et l'host a une AUTRE carte que celle de l'invité.

Tout ce qui suit vient de la lecture du code. Rien n'a été lancé. Ce qui est supposé est marqué « non vérifié ».
Les numéros de ligne de `ElinNetHostTravel.cs` peuvent avoir bougé (un autre agent y écrit).

## 1. Comment le jeu fait un niveau de donjon

- Le premier niveau d'un donjon porte déjà le numéro **-1** (`Zone_Dungeon.cs:35`, `StartLV => -1`). « Niveau -1 »
  est donc la carte d'entrée de la cave, pas le niveau du dessous (-2).
- Escalier : `TraitNewZone.MoveZone` (`TraitNewZone.cs:191-218`) cherche le niveau voisin parmi les enfants du
  sommet (`Spatial.FindZone(lv)`, `Spatial.cs:728`). S'il n'existe pas : `CreateZone` (`TraitNewZone.cs:240`) le
  crée (`SpatialGen.Create`, puis `lv`, `x`, `y`, et `c_uidZone` sur l'escalier).
- `Zone.Activate` (`Zone.cs:639`) : carte générée si `isGenerated` est faux ou si le fichier `<uid>/map` manque
  (`Zone.cs:665-704`), sinon chargée depuis le dossier de sauvegarde. La génération est aléatoire (pas de graine
  commune) : deux jeux qui génèrent le même niveau ont deux cartes différentes.
- **Régénération à l'entrée** (`Zone.cs:648-656`) : si la zone a `RegenerateOnEnter`, qu'on vient d'un AUTRE
  donjon ou de la carte du monde, et que `dateExpire` est passée (0 compte comme passée, `Date.cs:338`), le jeu
  écrit « regenerateZone », appelle `ClearZones` (`Zone.cs:2083`) : la carte est jetée et **tous les autres niveaux
  du donjon sont détruits**.
- `RegenerateOnEnter` n'est vrai que pour `Zone_DungeonUnfixed` (`Zone_DungeonUnfixed.cs:9-11`, durée **1 jour**) :
  la Caverne du chiot (`Zone_DungeonPuppy`), `cave_yeek`, `cave_dragon`. Pas Nymelle, pas les Nefia.
- Nefia : pas de régénération à l'entrée, mais une Nefia expirée est **détruite à la sauvegarde** de l'host
  (`Zone.CanDestroy`, `Zone.cs:1957-2026`, appelé par `_OnBeforeSave`), sauf si le joueur du jeu est dedans.
- Ces règles supposent un seul joueur : dedans ou dehors. À plusieurs, un joueur peut être dedans quand un autre
  arrive de dehors.

## 2. Ce que fait le mod (chemin normal, lu, il paraît juste)

1. L'invité prend l'escalier. Son jeu crée le niveau (`SpatialGenEvent.cs:44-47` le note comme « créé ici »), et
   demande le bail avec un plan (`ZoneLeaseRequest.cs:25-31`, `LeaseZoneBlueprint`).
2. L'host crée la MÊME zone chez lui, sous le même donjon, avec **son** numéro (`CreateClientZone`,
   `ElinNetHostTravel.cs:1355-1392`), ou réutilise celle qui existe déjà (même id, x, y, niveau). L'invité prend
   ce numéro (`AdoptHostUid`, `ElinNetClientTravel.cs:240-282`, escaliers corrigés). Pas de plage de numéros de
   zone par joueur : c'est toujours l'host qui choisit.
3. La carte de l'invité monte chez l'host : à chaque point de passage (60 s par défaut, `ApplyCheckpoint`,
   l.1156), quand il quitte le niveau (`OnZoneLeaseRelease`, l.1064) et quand l'host le rappelle.
4. L'host qui veut entrer dans une zone tenue : `CharaMoveZoneEvent.cs:14-16` → `TryEnterZone` → `CanEnterNow`
   (l.688-721) bloque le déplacement et envoie `ZoneLeaseRecall`. L'invité rend la zone avec sa carte
   (`ElinNetClientTravel.cs:618-636`, `CreateLeaseRelease` l.872). L'host écrit les fichiers (`ApplyLeasedZone`,
   l.1222-1249), sauvegarde (l.1145), puis entre (`ResumePendingHostMove`, l.1208) et charge la carte reçue.
5. Par l'escalier, l'host retrouve bien le niveau de l'invité (`FindZone(lv)` : même parent, même niveau).

Donc, sans expiration, l'host ne génère pas : il reçoit. **Ce chemin n'a jamais été testé** (voir 3).
Le passage du journal « une zone créée par l'host sans annonce n'est jamais connue du client » (`MODLOG.md:1983`,
`ElinNetClientZone.cs:90-91`) est le sens inverse (host → client) et ne joue pas ici.

## 3. Ce que les tests couvrent

- Aucune suite n'utilise un escalier ni un donjon à niveaux (recherche de `TraitStairs`, `TraitNewZone`, `lv`,
  `Nefia`, `nymelle` dans `dev/_tools/*.py` : rien, sauf un filtre d'objets dans `guest_suite.py:862`).
- `travel_suite.py` S14/S15 : zone créée par l'invité = une case libre de la carte du monde (`Zone_Field`), un seul
  niveau. S7 : rappel par l'host, dans une ville.
- `instance_suite.py`, `together_suite.py` : zones de quête (instances), traitées à part (`CreateQuestZone`,
  jamais de carte rendue). `leave_suite.py` : rien sur les donjons.
- `MODLOG.md:551` : « étage de donjon loué détruit avec son sommet expiré → `HasLeasedFloor` (pas de test) ».

## 4. Causes possibles, de la plus probable à la moins probable

### A. La cave « se régénère à l'entrée » alors qu'un joueur est dedans (la plus probable, non vérifié en jeu)

Colle au récit mot pour mot (« cave », « niveau -1 », « régénérée ») si la cave est la Caverne du chiot,
`cave_yeek` ou `cave_dragon`, et si plus d'un jour de jeu a passé depuis que l'invité a généré l'entrée. Avec
l'heure commune (cochée par défaut, `EmpConfig.cs:162-165`), la date du monde est celle du joueur le plus avancé :
à trois joueurs ou plus, un sommeil ou un voyage sur la carte du monde suffit à faire passer un jour.

- **A1, l'invité est encore à l'entrée (-1).** Rappel, la carte de l'invité est écrite chez l'host, puis
  `Zone.Activate` de l'host voit la date dépassée (`Zone.cs:648`) et jette cette carte pour en générer une autre.
  L'invité, ramené près de l'host, reçoit la nouvelle carte.
- **A2, l'invité est déjà en dessous (-2).** L'entrée n'est plus tenue (rendue à la descente). L'host entre,
  `ClearZones` détruit chez lui le niveau -2 où se tient l'invité (`Zone.cs:2096-2102`, rien ne le protège :
  `LeasedZonePatch` ne garde que `CanDestroy`). L'invité continue de jouer dans un niveau qui n'existe plus chez
  l'host : ses points de passage sont ignorés sans un mot (`ApplyCheckpoint`, l.1164 : zone introuvable). Si
  l'host descend, le jeu crée un **second** niveau -2 avec un autre numéro, non tenu, donc sans rappel : deux
  joueurs au même étage sur deux cartes.

Suite : la carte de l'host est celle gardée dans la sauvegarde ; le dossier de l'ancien niveau est effacé à la
sauvegarde (`GameIO.cs:98-106`). Ce que l'invité porte sur lui est gardé (son personnage remonte à part,
`ReplaceRemoteChara`). Ce qu'il a posé au sol, tué ou ouvert est perdu ; la nouvelle carte a de nouveaux coffres
et monstres (pas de vrai doublon d'objet, mais du butin en plus, comme une régénération normale du jeu).

### B. Nefia expirée, détruite par la sauvegarde entre le rappel et l'entrée (non vérifié)

Au retour d'un rappel, le bail est retiré (l.1079, l.1133), puis l'host sauvegarde (l.1145) **avant** d'entrer
(l.1150). Si l'host vient de la carte du monde et que la Nefia est expirée, `CanDestroy` la détruit à cet instant
(plus de bail, donc `LeasedZonePatch` ne la garde plus) ; l'host entre alors dans une zone détruite,
`isGenerated` faux (`Zone.cs:2080`) : il génère. Durée d'expiration des Nefia non lue (réglage du jeu).

### C. L'invité tombe ou se déconnecte moins de 60 s après être descendu (non vérifié)

Aucun point de passage n'est encore monté : chez l'host le niveau existe sans carte. `ReleaseLeaseOnDisconnect`
(l.1497) ou `CanEnterNow` (l.705-709, joueur introuvable) retire le bail, l'host entre et génère. L'invité qui
revient trouve la carte de l'host. Pas le récit (personne n'a parlé de coupure), mais même effet.

### D. Retour sans carte (peu probable, non vérifié)

Si l'invité répond au rappel sans se croire maître de la zone (`CreateLeaseRelease`, l.877 : numéro -1, pas de
carte), l'host écrit « rejoins while still holding zones, dropping them » (l.1125), retire le bail et génère.
Aucun chemin trouvé qui mène là pour un invité entré seul.

### E. Côté invité (à corriger plus tard, hors du récit)

- Un invité qui entre de dehors dans une cave expirée dont un autre joueur tient un étage la régénère chez lui
  (même ligne `Zone.cs:648`), puis rend cette nouvelle entrée à l'host : entrée et étages ne vont plus ensemble.
- `AdoptHostUid` (l.254) reconnaît « la même zone » par id, x, y **sans le niveau** : deux étages d'un même
  donjon ont les mêmes trois valeurs.

## 5. La plus petite correction

Règle : **un donjon où un joueur se tient, ou qu'un joueur vient de rendre, n'est pas expiré.** Deux endroits, côté
host seulement, pas de nouvelle case à cocher (c'est une réparation du voyage indépendant).

1. `ElinNetHostTravel.cs`, une fonction d'une dizaine de lignes :
   ```csharp
   // the game expires a dungeon nobody is in; a player is, or just was
   internal void KeepAlive(Zone zone)
   {
       foreach (var z in new[] { zone, zone.GetTopZone() }) {
           if (z.isGenerated && world.date.IsExpired(z.dateExpire)) {
               z.dateExpire = world.date.GetRaw() + 1440 * z.ExpireDays;
           }
       }
   }
   ```
2. L'appeler à la fin de `ApplyLeasedZone` (après `ApplyState`, l.1242) : couvre A1 et B (la date est remise
   avant la sauvegarde et avant l'entrée de l'host), et les points de passage.
3. L'appeler dans le préfixe de `ZoneActivateEvent.cs:13-20`, quand le jeu est l'host et que
   `host.IsLeased(top.uid) || host.HasLeasedFloor(top)` (`top = __instance.GetTopZone()`) : couvre A2 (un étage
   est tenu, l'host entre par le haut).

Non couvert par cette correction : C (demander un point de passage dès que l'invité a fini de générer, une ligne
dans `TravelTo` côté invité, à voir ensuite), E.

## 6. Le test à deux fenêtres (rouge aujourd'hui)

Nouveau scénario `s18` dans `travel_suite.py` (mêmes aides : `ev`, `wait`, `marker`, `on_map`, `enter_at`,
`client_settled`, `both_joined`, `zone_uid`). Donjon : la Caverne du chiot, trouvée par son type (présence dans le
monde de test non vérifiée ; sinon `cave_yeek`, même classe mère) :
`EClass.game.spatials.map.Values.OfType<Zone_DungeonUnfixed>().First(z => z.GetTopZone() == z)` → uid, x, y.

1. L'invité sort sur la carte du monde (`EClass.player.ExitBorder()`), entre dans la cave par sa case
   (`enter_at`, le vrai chemin). Attendre `client_settled(client, cave, True)`.
2. Seau `m1` posé à l'entrée. Noter la case de l'escalier :
   `EClass._map.FindThing<TraitStairsDown>().owner.pos`.
3. L'invité descend par l'escalier, comme un clic dessus :
   `EClass._map.FindThing<TraitStairsDown>().MoveZone(); "ok"`. Attendre un `awayZone` dont `lv == -2` ;
   `etage = zone_uid(client)`. Seau `m2` posé.
   Vérifier chez l'host : `spatials.Find(etage)` existe, `lv == -2`, bail compté (`leases(host) == 1`).
4. Un jour passe, comme une nuit de sommeil de l'host : `EClass.world.date.AdvanceMin(1500); "ok"` sur l'host.
5. L'host sort sur la carte du monde et entre dans la cave par sa case (`enter_at`).
   - **rouge aujourd'hui** : « l'entrée est celle de l'invité » (`on_map(host, [m1])` à la même case, escalier à
     la même case) ;
   - **rouge aujourd'hui** : « l'étage de l'invité existe encore chez l'host » (`spatials.Find(etage) != null`).
6. L'host prend l'escalier (même appel qu'en 3). Attendre `zone_uid(host) == etage` (**rouge** : autre numéro),
   `both_joined(host, client, etage)`, `on_map(host, [m2])` à la même case, et un seul enfant de niveau -2 :
   `cave.children.Count(c => c.lv == -2) == 1`.

Deux témoins à ajouter, verts dès aujourd'hui si la lecture du chapitre 2 est juste (sinon ils montrent une autre
cause) : le même scénario **sans** l'étape 4, et le même dans une Nefia
(`OfType<Zone_RandomDungeon>().First(z => z.GetTopZone() == z)`, présence non vérifiée, monstres plus forts).
Pièges : dialogue de tutoriel à la première visite de la caverne (`dismiss_dialogs`) ; `LockExit` au niveau -2 de
la Caverne du chiot ; ne pas se téléporter d'étage en étage, c'est l'escalier qui est en cause.

## 7. Deux questions pour le joueur

1. C'était quelle cave : la Caverne du chiot près de la Prairie, une Nefia (donjon au nom tiré au hasard), ou
   Nymelle ? Et quand l'host est entré, le jeu a-t-il écrit une phrase disant que l'endroit avait changé ?
2. Quand l'host est arrivé, l'invité était-il encore sur la première carte de la cave ou déjà un étage plus bas,
   et quelqu'un avait-il dormi ou longuement voyagé entre-temps ? Ensuite, l'invité a-t-il été ramené près de
   l'host ou est-il resté seul sur sa carte ?
