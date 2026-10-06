# Plan : un host seul dans sa session vit le jeu solo

Enquête en lecture seule (2026-10-06). Rien compilé, rien joué. **lu** = code lu (mod, ou jeu décompilé
`dev/_decomp/Elin_23351`). **supposé** = déduit, à prouver au banc. Règle visée : `CurrentPlayers.Count <= 1`
= jeu solo, bascule propre quand un invité arrive ou part.

## État (2026-10-06, appliqué non testé en jeu : compilé seulement, build ReleaseNightly 0 erreur)

**Porte commune** : `ElinTogether/Net/NetCompany.cs`, `NetCompany.HasCompany` (fichier neuf, lecture seule de l'état existant).
Elle dit « un autre joueur existe dans ce monde » et PAS `CurrentPlayers.Count > 1` ni `HasActiveConnection` :
`Connection` nulle (pas de session, ou seul dans une zone éloignée) = faux ; client = vrai (l'host est un autre joueur) ;
host = `CurrentPlayers.Count > 1` **ou** au moins un pair connecté (`Connection.IsConnected` : poignée de main, choix du
personnage, invité parti voyager seul). Le test des pairs est relu au plus toutes les 50 ms (il interroge Steam ; les
lectures de compétence sont le chemin le plus chaud du jeu). Un invité qui arrive est donc vu au plus 50 ms en retard.
Conséquence voulue : un invité qui voyage seul garde l'host en mode « plusieurs » (le plan voulait, pour la pause des menus
seulement, `Count > 1` : décision à prendre, voir S16).

| # | État | Où (après changement) | Condition |
|---|---|---|---|
| S1 | fait | `AIFuckPatch.cs:16` | `!HasCompany` -> `return true` (le jeu fait l'acte) |
| S2 | fait | `CharaTaskRemoteEvent.cs:46` (idle) et `:57` (case prise) | `HasCompany` ajouté aux deux tests |
| S3 | fait | `RemotePlayerKillPatch.cs:29` | `Connection is ElinNetHost && HasCompany` |
| S4 | fait | `RemoteResidentPatch.cs:131` | `&& HasCompany` sur le refus de la réserve |
| S5 | fait | `InvSplitThingEvent.cs:17` | `!HasCompany` -> `return true` |
| S6 | fait | `ElinNetHostZone.cs:25` | `peer is null && Socket.Peers.Count == 0` (pairs, pas la porte : même sens, sans cache) ; ligne du salon gardée ; `InviteToQuestZone` sauté aussi (sans pair il n'envoie rien : relu) |
| S7 | fait | `ElementChangedEvent.cs:43` (préfixe), `:55` (postfixe) | `!HasCompany` -> sortie |
| S8 | **pas fait** | `CardAddThingEvent.cs:99` (fichier interdit) et `ShippingStackPatch.cs:15` | le plan les lie : sans la moitié `CardAddThingEvent`, la moitié `ShippingStackPatch` seule fusionnerait des piles d'expéditeurs différents (un reste d'un invité absorbe l'objet de l'host) : à faire ensemble, avec `HasCompany` |
| S9 | fait | `QuestGiveClientPatch.cs:23` | `&& HasCompany` |
| S10 | **pas fait** | `AreaWatch.cs:40` (`Patches/Synchronization/**`, interdit) | à faire : `if (!NetCompany.HasCompany) { _map = null; return; }` en tête de `Update` |
| S11 | n'existe pas dans le plan | | |
| S12 | fait | `CharaVisibilityChangeEvent.cs:16, 39, 63` | `!HasCompany` -> sortie. Pas de minuteur à forcer ici : `ActionModeCombat` (S15) le remet « dû » |
| S13 | **retiré volontairement** (voir « Après relecture ») | `CardGenEvent.cs` (aucune porte `HasCompany`, vérifié) | la ligne « fait » de cette table était fausse : la porte a été ôtée (risque de désynchronisation), M9 reste ouvert |
| S14 | fait | `TileStateDelta.cs:44` (`Mark`) et `:67` (`Flush`) | `&& HasCompany` ; `_dirty` est vidé à la fin de `Flush` comme avant |
| S15 | fait | `ActionModeCombat.cs:64` | `!HasCompany` -> `_visibilityTimer = VisibilityRefreshInterval; ChangePhaseLocal(Inactive); return` (la porte vaut vrai pour un client : rien ne change pour lui) |
| S16 | fait | `PauseGame.cs:44`, `RemoteSharedSpeedPatch.cs:13` | `HasCompany` à la place de `HasActiveConnection`. Pas fait : `RemoteMinimapPatch.cs:16, 29`, `RemotePartyPatch.cs:22` (cités en M16, absents de S16) |

À décider avant de passer plus loin : (a) S16, invité parti voyager seul : la pause des menus de l'host revient-elle (plan, `Count > 1`)
ou reste-t-elle coupée (appliqué, plus prudent) ? (b) un client seul dans une zone éloignée (`Connection` nulle) passe maintenant
au jeu pur pour la pause des menus et la vitesse partagée (avant : `HasActiveConnection` vrai) ; cohérent avec « le jeu tourne en solo
là-bas », non testé. (c) S2 : seul, le test « idle identique ignoré » est levé : `CharaTaskDelta` d'une tâche vide est alors fabriqué et
envoyé à personne à chaque `SetAI` idle du joueur (coût faible, `NetProfileSynchronizationContext.Update` seulement un delta si la main
change) ; une sortie anticipée `host seul -> return true` en tête de `OnSetAI` couvrirait S2 en entier et supprimerait ce coût.

**Reste à faire** : S8 (deux fichiers, dont `CardAddThingEvent.cs:99` : `ShippingHelper.Enabled ?` -> `ShippingHelper.Enabled && NetCompany.HasCompany ?`, puis
`ShippingStackPatch.cs:15` : première condition `&& NetCompany.HasCompany`), S10 (`AreaWatch.cs:40`), C1 à C8 (non touchés). Test : `dev/_tools/solo_suite.py`
(écrit, jamais lancé ; couvre Z0 à Z10 = S1 à S7, S12, S15, S16 ; pas S13, S14, S6 seulement par les lignes du journal).
Le plan §6 dit pour S2 « refusé seulement si l'invité vise la case » : le code refuse pour tout perso de la carte (`TaskCache.IsPosTaken`
lit `map.charas`), la suite attend ce que fait le code. Décompilation de référence : `Elin_23351`, jeu actuel 23.352 (non relue).

## 0. Faits qui changent le tableau

- **Release : les patchs n'existent que pendant une session** (`Net/Base/ElinNetBase.cs:41-47` PatchAll au démarrage du
  composant, `UnpatchSelf` à sa destruction ; lu). Avec l'ouverture automatique, un host seul porte donc **tous** les
  patchs, y compris ceux sans aucune garde réseau. En Debug (banc) tout est patché dès le lancement : une fenêtre de banc
  n'est jamais « du vanilla pur ».
- **`HasActiveConnection` ne veut PAS dire « un autre joueur est là »** : pour un host c'est « au moins un pair connecté
  (même en poignée de main) » (`Net/Steam/SteamNetManager/SteamNetManager.cs:56`, `SteamNetPeer.cs:87` ; lu). Seul : faux.
  Un invité en train de se connecter, au choix du personnage ou **parti voyager seul** (retiré de `CurrentPlayers`,
  `ElinNetHostTravel.cs:865`) le rend vrai alors que `Count <= 1`.
- `NetSession.IsHost` est vrai **sans session** (`NetSession.cs:84`) : les `return IsHost` sont inoffensifs.
- Coûts constants d'un host seul (lu) : `WorldStateSnapshotUpdate` à 5 Hz crée un instantané de tous les charas de la carte
  (`ElinNetHostUpdate.cs:30-52`, abonnement `:267`), les deltas sont sérialisés à 50 Hz puis envoyés à zéro cible
  (`SteamNetPeerBroadcast.cs:40-42`). `States[0]` = l'host, donc `PauseWorldStateUpdate` ne tourne jamais.

## 1. Déjà bon pour un host seul (lu, rien à faire)

| Sujet | Où | Pourquoi c'est bon |
|---|---|---|
| Pause dans les menus | `PauseGame.cs:43` | `HasActiveConnection` faux sans pair ; `ShouldPauseGame` (`:15-37`) ne filtre que les joueurs distants (liste vide) |
| Tours de combat | `ActionModeCombat.cs:245-252` | `players.Count >= 2` exigé ; sortie vers `Inactive` dès que l'invité part (`:250`) |
| Temps de combat par joueur | `PlayerCombatTime.cs:31-32` | `HostActive` exige `Count >= 2` |
| Sauvegarde / chargement rapides | `GameSaveLoad.cs:15, 39-40` | host non « away » sauve ; `TryLoad` passe si `Count <= 1` |
| Sommeil | `SleepSynchronizationContext.cs:64, 110, 444` | `alive < 2`, `AllowPartySleep` et `SimulateFaction` portent déjà `Count` |
| Limite d'alliés | `CompanionAllyLimitPatch.cs:32` | `1 + places utilisées` = `Party.Count` du jeu (`Party.cs:61`) si seuls pc + ses compagnons sont dans le groupe |
| Vitesse partagée | `RemoteSharedSpeedPatch.cs:13` | `HasActiveConnection` faux ; case décochée par défaut (`EmpConfig.cs:104`) |
| Cadence des tours | `CharaSynchronizationContext.cs:52-62`, `GameSynchronizationContext.cs:85-99` | seul, `RefSpeed` = vitesse du pc (retard max ~0,2 s, instantané à 5 Hz ; supposé sans effet) |
| Sauvegarde auto | `EmpAutoHost.cs:115-123` | ne sauve que s'il y a des invités |
| `NoActiveGCPatch` | `NoActiveGCPatch.cs:1` | `#if DEBUG` seulement |
| Lumière, vue, minimap, pièges, dieux, deuil, tactiques | `Fov/*`, `Remote*` | copie équivalente au jeu ou réservée aux joueurs distants (lu) |

## 2. Table des écarts, classés par gêne pour le joueur

### Grave (le joueur le sent)

**G1. Dressage et actes d'amour : la copie du mod remplace tout `AI_Fuck.Run`, sans garde** (lu).
`Patches/DeltaEvents/Task/AIFuckPatch.cs:12-16` (corps `:18-159`). Jeu solo (`AI_Fuck.cs:87-245`) : variation lait,
feat « fast fucker », slime, brosse de zone du dressage (outil 770, message `tame_end`, son, hygiène +15, `stats.brush++`,
seuil d'affinité Respected). Mod seul : copie ancienne, seuil Intimate, pas de brosse de zone ni de compteur. Visible :
animaux moins bien dressés, dialogues. Valable aussi pour les PNJ (`AI_Idle`). Correction : voir S1 (une ligne) ; la vraie
parité demande de porter les écarts (C1). Bascule : aucun risque pour l'acte en cours (l'énumérateur existe déjà).

**G2. Chaque changement de zone sérialise et sauve la carte pour personne** (lu).
`DeltaEvents/Zone/ZoneActivateEvent.cs:47` → `ElinNetHostZone.cs:17-25` → `ZoneDataResponse.cs:41` (`zone.map.Save(...)`,
compression de tout le dossier) puis `Broadcast` à zéro pair. Visible : hoquet à chaque entrée de zone, pire sur grande
carte ou domicile (durée : supposé). Correction : S6. Bascule : un invité qui arrive reçoit la zone par
`PreparePlayerJoin` → `PropagateZoneChangeState(zone, peer)` (`ElinNetHostZone.cs:60, 93`) : rien de perdu.

**G3. Chemin chaud du jeu : `ElementChangedEvent` alloue à chaque lecture d'une compétence** (lu).
`DeltaEvents/Element/ElementChangedEvent.cs:38-44` (préfixe : `new int[4]` à chaque appel de `GetElement`/`GetOrCreateElement`),
`:58` (le postfixe ne sort tôt que pour les persos distants, puis lambda + `CoroutineHelper.Deferred`). `GetElement` est
appelé des milliers de fois par image (`Evalue`). Visible : images par seconde en combat / zone dense (coût exact : supposé).
Correction : S7. Bascule : ce qui a changé avant l'arrivée de l'invité n'est pas envoyé, il reçoit l'état complet
(supposé, à prouver : T-Elem).

**G4. Pas de swap ni de poussée avec les alliés** (lu côté IL, comportement supposé).
`Patches/Remote/RemoteNoPushPatch.cs:11-24` : le transpiler remplace le `if (type != MoveType.Force)` de `Chara._Move`
(`Chara.cs:3234-3250`) par un saut toujours pris, pour tous les persos. Jeu solo : on échange sa place avec un allié
(`CanReplace` + `MoveByForce` + message `replace_pc`), `TryPush`. Mod : jamais ; le pc entre sur la case occupée.
Visible : couloirs bloqués par les compagnons. Correction : C2 (IL, pas une ligne). Bascule : évaluée à chaque pas, aucun état.

**G5. Un clic « couper / récolter » ne fait rien si un autre perso de la carte vise déjà la case** (lu).
`DeltaEvents/Chara/CharaTaskRemoteEvent.cs:55-60` + `Models/Pending/TaskCache.cs:20-24` (`IsPosTaken` regarde tous les
`map.charas`, compagnons et ouvriers compris). Le jeu solo n'a pas cette règle. Seule trace : log Debug. Correction : S2.
Bascule : testé au démarrage de la tâche seulement.

**G6. Les alliés ne peuvent pas tuer l'host (tir ami, sort de zone)** (lu).
`Patches/Remote/RemotePlayerKillPatch.cs:28` (`Connection is ElinNetHost`) puis `:51` : si l'attaquant est le pc, un joueur
ou un allié du pc (`IsPCFactionOrMinion`) et la cible un « joueur » (le pc), la cible reçoit « invulnérable » le temps du coup
(règle `AllowPlayerKill` décochée par défaut). Seul : un sort de zone d'allié ou un allié confus laisse le pc à 0 pv au lieu
de le tuer. Visible : mort impossible dans ce cas, état 0 pv étrange. Correction : S3. Bascule : le bouclier dure un coup.

**G7. « Mettre un allié en réserve » refusé à l'host, avec le message « seul l'host peut »** (lu).
`Patches/Remote/RemoteResidentPatch.cs:130` : `kind == Reserve && c.IsPCParty` → `Refuse(true)` quelle que soit la session
(le jeu solo l'autorise : `BaseListPeople.cs:454`, `Faction.AddReserve` retire du groupe `:340-343`). Correction : S4.
Bascule : décidé à chaque clic.

### Moyen / faible

| # | Écart (fichier:ligne) | Jeu solo | Host seul avec le mod | Correction |
|---|---|---|---|---|
| M1 | `DeltaEvents/Inventory/InvSplitThingEvent.cs:14` (lu) | `Thing.ShowSplitMenu` : le reste va au conteneur, la pile d'origine est glissée (`Thing.cs:1940-1949`) | le nouveau morceau est glissé, le reste garde l'objet d'origine : identité (uid) de la pile changée, place du reste non copiée (supposé peu visible) | S5 |
| M2 | `Helper`→`CardAddThingEvent.cs:97-106` + `ShippingStackPatch.cs:15` (lu) | une seule pile dans la boîte d'expédition | objets mis avant/après la session portent des clés d'expéditeur différentes : deux piles (argent inchangé : `ElinNetHostShipping.cs:161`) | S8 |
| M3 | `QuestGiveClientPatch.cs:18-23` (lu ; effet supposé) | le pc pouvait être tiré pour donner une quête (`TraitChara.cs:122-131`) | jamais, dès qu'une connexion existe | S9 |
| M4 | `CharaTaskRemoteEvent.cs:46-48` (lu) | `SetAI` retire `ConWait` et rend `g` | « idle » identique ignoré, rend null | S2 (même fichier) |
| M5 | `NoApplicationPausePatch.cs:11-19` (lu) | `runInBackground` = réglage du joueur (défaut faux) | forcé à vrai, et **écrit dans le réglage** du joueur (`other.runBackground`) ; en Release seulement au prochain `CoreConfig.Apply` | C3 |
| M6 | `Fov/FovCellLightOffsetPatch.cs:10-34`, vidé seulement dans `ZoneActivateEvent.cs:19` (lu ; effet supposé) | — | après le départ d'un invité, son `Fov` reste dans `PlayerFovs` : ses dernières cases restent « vues » (`pcSync`) pour l'host jusqu'au prochain changement de zone | C4 |
| M7 | `CoreSynchronizationContext.cs:29-58`, `AreaWatch.cs:41-60`, `NameWatch.cs`, `PlayerTrade/Duel`, `QuestSynchronizationContext.cs:7-17`, `CharaSynchronizationContext.cs:68`, `NetProfileSynchronizationContext.cs` (lu) | rien | une dizaine de vérifications à chaque image ; `AreaWatch` fait `string.Join` sur tous les points de toutes les zones tous les 0,25 s (lourd sur grande base) | S10 |
| M8 | `CharaVisibilityChangeEvent.cs:15, 38, 61` (lu, agent) | — | une ligne de vue par perso de la carte à chaque `KillActor` et `Die`, pour une visibilité inutile seul | S12 |
| M9 | `DeltaEvents/Card/CardGenEvent.cs:24-56` (lu, agent) | — | copie complète `LZ4Bytes.Create(card)` pour chaque carte créée, sans destinataire | S13 |
| M10 | `Zone/TileStateEvent.cs`, `TileStateDirectEvent.cs`, `Models/Delta/Zone/TileStateDelta.cs:39-95` (lu, agent) | — | chaque cellule changée est marquée, puis 24 entiers par cellule construits à chaque image | S14 |
| M11 | `ActionModeCombat.cs:55-81` (lu) | — | à chaque image : `CurrentPlayers.ToList()`, LINQ, mesure de visibilité toutes les 0,5 s, delta envoyé | S15 |
| M13 | `CompanionAllyLimitPatch.cs:32` + `CompanionHelper.cs:100-104` (lu) | `Party.Count` simple | `CompanionsOf` avec `ToList` et `Contains` (carré), appelé 2 fois par image (`Scene.cs:241, 547`) | C5 |
| M14 | `EmpConfig.cs:72`, `ElinNetBase.cs:65-72` (lu) | la touche P ne fait rien de mod | P envoie un ping et affiche un message, même seul (peut-être en conflit avec le jeu : supposé) | C6 |
| M15 | `Trait/TraitRecipePatch.cs:16` (lu) | tout lecteur apprend la recette | seul : faux (aucun pair). Avec un invité : un compagnon qui lit consomme sans apprendre. Bug avec invité, pas seul | `c.IsPC` → `c is not { IsRemotePlayer: true }` |
| M16 | `PauseGame.cs:43`, `RemoteSharedSpeedPatch.cs:13`, `RemoteMinimapPatch.cs:16, 29`, `RemotePartyPatch.cs:22` (lu) | — | utilisent « un pair connecté » : un invité en poignée de main, au choix du perso ou **parti seul** coupe la pause des menus de l'host. Aligner sur `Count > 1` | S16 |

À ignorer (vérifié sans effet seul) : `AIFishPatch.cs:200-213` (appât, très bas), `PlayerKarmaPatch` (tout derrière
`ActiveRemoteCharas.Count > 0`), `WorldKeeper*` (l'host est le gardien), `LeasedZonePatch`, `BossFleePatch`, les patchs
`Trait/*` et `Remote*` réservés aux persos distants, les `DeltaEvents` qui ne font qu'envoyer.
`Card.Tool` (`RemoteGetToolPatch.cs:7-18`, toujours actif) rend `held` au lieu de `currentHotItem.Thing` du jeu
(`Card.cs:2479`) : à comparer en jeu (outil de la barre rapide non tenu).

## 3. Corrections « sûres en une ligne » (prêtes à coder)

`using ElinTogether.Net;` si absent. `Alone` = `NetSession.Instance.CurrentPlayers.Count <= 1`.

- **S1** `AIFuckPatch.cs:13` : insérer en tête de `OnRun` `if (NetSession.Instance.CurrentPlayers.Count <= 1) return true;`
  (avant : `__result = Run_Modified(...)` toujours).
- **S2** `CharaTaskRemoteEvent.cs:55` : `connection.IsHost && __instance.IsPC && ...` → `connection.IsHost && NetSession.Instance.CurrentPlayers.Count > 1 && __instance.IsPC && ...`.
  Et `:46` : `if (NetSession.Instance.CurrentPlayers.Count > 1 && __instance.ai.GetType() == ...` (garde le test existant).
- **S3** `RemotePlayerKillPatch.cs:28` : `Connection is ElinNetHost ? Shield(...)` → `Connection is ElinNetHost && NetSession.Instance.CurrentPlayers.Count > 1 ? Shield(...)`.
- **S4** `RemoteResidentPatch.cs:130` : `(kind == BaseRequestKind.Reserve && c.IsPCParty)` → `(kind == BaseRequestKind.Reserve && c.IsPCParty && NetSession.Instance.CurrentPlayers.Count > 1)`.
- **S5** `InvSplitThingEvent.cs:14` (début de `OnShowSplitMenu`) : `if (NetSession.Instance.CurrentPlayers.Count <= 1) return true;`.
- **S6** `ElinNetHostZone.cs:17` (début de `PropagateZoneChangeState`, appel sans pair) : si `peer is null && Socket.Peers.Count == 0`,
  garder la ligne du salon (`:40`) et sortir avant `ZoneDataResponse.Create`. Test sur les **pairs** (pas sur `Count`) : un invité
  parti voyager reste un pair.
- **S7** `ElementChangedEvent.cs:38` (préfixe) : `if (NetSession.Instance.CurrentPlayers.Count <= 1) { __state = null; return; }` ;
  `:58` (postfixe) même test, `return`.
- **S8** `CardAddThingEvent.cs:99` : `ShippingHelper.Enabled ?` → `ShippingHelper.Enabled && NetSession.Instance.CurrentPlayers.Count > 1 ?` ;
  `ShippingStackPatch.cs:15` : ajouter `&& NetSession.Instance.CurrentPlayers.Count > 1` à la condition de la première `if`.
- **S9** `QuestGiveClientPatch.cs:23` : `if (__instance.owner.IsPlayer)` → `if (__instance.owner.IsPlayer && NetSession.Instance.CurrentPlayers.Count > 1)`.
- **S10** `AreaWatch.Update` (`AreaWatch.cs:40`, début) : `if (NetSession.Instance.CurrentPlayers.Count <= 1) { _map = null; return; }`
  (la reprise « autre carte » à `:51-56` enregistre l'état sans l'envoyer : pas de faux delta à l'arrivée).
- **S12** `CharaVisibilityChangeEvent.cs:15, 38, 61` : `if (NetSession.Instance.CurrentPlayers.Count <= 1) return;` (voir risque en T-Vis : forcer `_visibilityTimer` à l'arrivée).
- **S13** `CardGenEvent.cs:24` (avant le `AddRemote` final) : `if (NetSession.Instance.CurrentPlayers.Count <= 1) return;`.
- **S14** `TileStateDelta.Mark` / `Flush` (`TileStateDelta.cs:39, 60`) : sortir (en vidant `_dirty`) si `Count <= 1`.
- **S15** `ActionModeCombat.cs:57` : après le test `Connection`, ajouter `if (NetSession.Instance.CurrentPlayers.Count <= 1) { ChangePhaseLocal(CombatPhase.Inactive); return; }`.
- **S16** `PauseGame.cs:43`, `RemoteSharedSpeedPatch.cs:13` : `HasActiveConnection` → `NetSession.Instance.CurrentPlayers.Count > 1`.

À ne PAS faire : mettre `Count > 1` dans `CompanionAllyLimitPatch.cs:19`. Un invité parti voyager (hors `CurrentPlayers`) laisse ses
compagnons dans le groupe de l'host : le jeu seul les compterait dans la limite de l'host ; le calcul du mod est le bon (supposé,
voir `CompanionLimboPatch`). Pas de correction de règle, seulement le coût (C5).

## 4. Corrections qui demandent un choix de conception

- **C1. Parité réelle de `AI_Fuck`** : porter dans `Run_Modified` les écarts du jeu (liste en G1), ou n'envelopper que ce que le mod
  change (progression distante). Sinon, avec un invité, l'host garde une copie ancienne : inégalité host/invité contraire à la règle du
  projet. Conseil à tenir (décision de conception).
- **C2. `RemoteNoPushPatch`** : remplacer le saut toujours pris par `type == Force || NetSession.Instance.CurrentPlayers.Count > 1`
  (IL : `ldarg_2; call Skip; brtrue`). Question : avec un invité, faut-il garder « pas de poussée pour tous » ou seulement pour les joueurs ?
  Bascule : à chaque pas, sans état.
- **C3. `NoApplicationPausePatch`** : ne plus écrire le réglage du joueur ; fixer `Application.runInBackground = réglage || Count > 1`
  à chaque image (ou à l'arrivée/départ). Choix : le mod doit-il forcer l'arrière-plan avec un invité (oui, sinon le jeu de l'invité fige).
- **C4. `PlayerFovs`** : retirer le `Fov` d'un invité qui part (là où `RemoveRemoteChara` le retire de la carte, `ElinNetHost.cs` non lu en
  détail) et remettre `pcSync` ; ou ignorer dans `OnClearVisible` les `Fov` dont le chara n'est plus dans la carte.
- **C5. Coût de `Party.Count`** : sortie rapide dans `OnCount` quand le groupe ne contient que le pc et ses compagnons sans propriétaire
  étranger (pas `Count`, voir §3).
- **C6. Touche P** : ping seulement si `Count > 1` (vérifier d'abord si le jeu l'utilise).
- **C7. Coupe générale des envois à vide** : `WorldStateSnapshotUpdate` (5 Hz, `ElinNetHostUpdate.cs:30-52`) et `WorldStateDeltaUpdate`
  (`:60-72`) quand `Socket.Peers.Count == 0` : sauter l'instantané (garder `selfState.Speed`) et **vider** `Delta` au lieu de la sérialiser.
  C'est le gain le plus gros et le plus diffus (couvre `CharaTick`, `CardSetDir`, `CardDamageHp`, `CharaMove`…, 8 à 10 patchs
  d'événements), mais il touche au cœur : (a) cas « session de zone » (un client seul qui héberge une zone a un autre `CurrentPlayers`,
  supposé) ; (b) un delta dont `Refresh()` a un effet local (non vérifié) ; (c) l'invité qui arrive doit recevoir l'état complet, pas des
  deltas anciens. Tester avec l'arrivée en plein combat. Critère sur les pairs, pas sur `Count`.
- **C8. Une seule porte** : ajouter `NetSession.Instance.HasCompany => CurrentPlayers.Count > 1` (et un événement quand elle change) pour
  éviter 20 copies de la condition, et y remettre à zéro combat, pause, sommeil à la bascule.

## 5. Bascule : invité qui arrive ou repart pendant l'état « solo »

- **Menu ouvert, jeu en pause** : `Core.cs:371` met le temps à 0 tant que le menu est ouvert ; à l'arrivée l'invité, `IsPauseGame` devient
  faux à l'image suivante et le monde repart pendant que l'host est dans son menu (voulu). Au départ : le menu repause. Aucun état gardé.
- **Combat** : arrivée → `Inactive` → `Deciding` une fois la visibilité de l'invité reçue ; `EClass.pc.ai.Cancel()` coupe l'action de l'host
  (`ActionModeCombat.cs:221-224`). Départ en `Deciding` ou `Executing` → `Inactive` aussitôt, la décision en attente est perdue (`:206-210`) :
  l'host doit recliquer. Avec S12/S15 : forcer le minuteur de visibilité à l'arrivée sinon 0,5 s de retard.
- **Sommeil** : l'host qui dort seul (`AllPlayersReady` vrai) attend l'invité qui arrive jusqu'à son vote (`SleepSynchronizationContext.cs:212`,
  `InSleepWaitWindow`) ; un clic de l'host annule alors son sommeil (`:236-243`). Voulu, mais à tester. Un invité qui arrive pendant `LayerSleep`
  ne reçoit pas `SleepStartDelta` (supposé).
- **Chargement / sauvegarde** : décidés à chaque appel (`GameSaveLoad.cs:39-40`) ; un invité qui arrive pendant le chargement bloque `TryLoad`.

## 6. Tests de banc (une fenêtre host avec session ; `python _tools/mp_test.py --clients 0`, `emp.py eval`)

La fenêtre de banc ouvre sa session par `emp.add_local` ; les tests « avec invité » passent à `--clients 1` (l'invité part avec
`emp.kick` ou `emp.disconnect`). Pour chaque correction : rouge d'abord, puis vert.

| Corr. | Test seul (une fenêtre) | Test de bascule (host + 1 invité) |
|---|---|---|
| S1/C1 | `Harmony.GetPatchInfo(AccessTools.Method(typeof(AI_Fuck),"Run"))` ; brosser un animal par `AI_TendAnimal` : `player.stats.brush` monte, message `tame_end` | invité arrive pendant l'acte : l'acte finit ; le suivant prend l'autre chemin |
| S2 | cultiver un arbre, donner `TaskCut` en cours à un compagnon sur la case, `pc.SetAI(new TaskCut{pos=…})` : `pc.ai` change | idem avec un invité : refusé seulement si l'invité vise la case |
| S3 | `pc` au coup d'un allié (`DamageHP(1e6, origin: allié)`) : `pc.isDead` vrai ; pas de tag `Invulnerable` | invité présent : un coup de l'invité sur l'host laisse à 0 pv |
| S4 | interface : ouvrir la liste de la base, clic droit sur un compagnon, « réserve » : `EClass.Home.listReserve` +1, pas de message « host » | invité présent : refusé |
| S6/G2 | `Stopwatch` autour d'un `MoveZone` ; journal : plus de ligne « Dispatching zone to all players » | invité arrive 1 image après l'activation : reçoit la zone |
| S7/G3 | `perf_probe.py` (images/s) ; nombre de deltas en attente après 2 s sans bouger | une compétence modifiée avant l'arrivée : même valeur chez l'invité |
| S10 | mesurer l'appel `AreaWatch.Update` sur une grande base (log de temps) | invité arrive après un changement de zone : pas de faux delta |
| S12/S15 | combat seul : `ActionModeCombat.Phase` reste `Inactive`, aucun delta de visibilité | invité arrive en plein combat : `Deciding` en moins d'une seconde |
| S16 | `EClass.ui.IsPauseGame` avec un `LayerInventory` ouvert : vrai | invité en poignée de main (pair sans personnage) : reste vrai ; invité au jeu : faux ; `emp.kick` : revient vrai |
| C2/G4 | allié adjacent, `pc.Move` vers lui : `allié.pos` = ancienne case du pc, message `replace_pc` | invité présent : comportement choisi |
| C7 | compter les octets sérialisés par seconde (`SteamNetPeer.cs:97`) seul : ~0 ; images/s | invité arrive pendant un combat : état complet identique |

Invité « parti voyager » (sans test aujourd'hui) : `travel_suite`, vérifier menus, vitesse, dressage solo.

Ordre : S1 à S4 et C2, puis S6, S7, C7 (mesurer), puis le reste, C1 et C8 en dernier (conseil).

Limites : aucun test joué ; `Helper/PersonalQuests.cs`, `ElinNetHostTravel.cs` et `Models/Delta/*` lus en partie ; coûts en ms supposés.
