# Journal de la partie à 4 du 6 octobre (0.26.524) : ce que le détecteur a dit

Journal lu : `Session_20261006.log` du joueur (hors dépôt). Lui : invité de 19:32Z à 19:52Z (host : LemiWinks), puis
HOST à partir de 20:12Z avec les pairs 1 (LemiWinks, personnage 582), 2 (Arma Minima, 541), 3 (Nardole, 658).
Carte : `Zone_startSite@0` (numéro 7). Le personnage 1 est celui de l'host.

**Limite de cette lecture** : le détecteur n'écrivait que des nombres (« 8/10 », « bags of 1 »), jamais QUELS
personnages ou objets. Le journal ne permet donc pas de nommer ce qui manquait. Ce qui est écrit « prouvé » l'est par
les lignes citées et par le code ; le reste est marqué « hypothèse ». Le détecteur corrigé nomme désormais les cartes
(voir « Ce qui a changé ») : le prochain journal de l'host tranchera.

## 1. `bags of 1` en continu : le détecteur comparait ce que le mod ne tient pas à l'identique

Verdict : **bruit du détecteur à faire taire** (fait), avec dessous un **vrai écart de copie, sans effet en jeu**.

Lignes : invité, 5 fois en 90 s (19:46:23, 19:47:13, 19:47:31, 19:47:37, 19:47:51). Host, 20:19:03 à 20:22:10 :
18 lignes `bags of 1` des pairs 1 et 2 ; puis `bags of 1,541`, `bags of 1,658`, `bags of 582`, `bags of 1,658,582`.

Ce que le journal prouve :
- Ce n'est **pas** un défaut de construction du calcul (cartes d'aptitude, objet tenu, ceinture…) : les deux côtés
  sautent les mêmes cartes (`Skipped`), et de 20:16:09 à 20:18:58 les pairs 1 et 2 étaient sur la carte avec l'host
  **sans aucune ligne** : les sacs étaient égaux. Après une copie neuve du monde (pair 1, 20:25:10) le sac de 1
  n'est plus signalé par ce pair (`charas 8/10, bags of 582` à 20:25:47, sans le 1), puis il l'est de nouveau à
  20:28:16. Donc : égal après une copie du monde, puis ça dérive.
- La dérive commence quand l'host travaille : de 20:18:36 à 20:18:54 il récolte (expérience des éléments 225/250
  toutes les 1 à 4 s), première ligne à 20:19:03. Côté invité, chaque ligne suit un ramassage de l'host
  (`Chara 1 picked …` à 19:47:31, 19:47:40-44).
- Chaque nouvelle ligne = le sac a changé puis est resté différent 3 comparaisons : d'où la répétition sans fin.

Cause dans le code (lue, **pas prouvée par ce journal**) : la copie qu'un jeu garde du personnage d'un AUTRE joueur
rejoue ses gestes avec les règles d'un personnage non joueur, qui ne sont pas celles du joueur :
- `Models/Delta/Chara/CharaPickThingDelta.cs:65` rejoue `chara.Pick(thing)` : toujours avec empilement, alors que le
  jeu d'origine a pu ramasser sans empiler (`Chara.HoldCard` → `Pick(t, false, tryStack: false)`), et avec la
  recherche de place d'un non-joueur (`ThingContainer.GetDest`, branche `!owner.IsPC` : le sac principal seulement).
  Si la copie empile là où le vrai personnage n'a pas empilé : la carte est détruite chez l'invité, la quantité de la
  pile n'y monte pas (`CardModNumEvent` bloque), puis le `CardAddThingDelta` de l'host est jeté
  (`CardAddThingDelta.cs:34`, « cannot be resolved here » : `CardCache.Find` rend la carte détruite, les données
  jointes ne sont pas lues). L'invité a alors une carte de moins dans le sac de ce joueur, pour de bon.
- `Models/Delta/Chara/CharaSwitchHeldDelta.cs:45` : `chara.PickHeld()` sur une copie passe par `things.TryStack`
  (le vrai joueur en est dispensé pour un objet de la barre, `Chara.PickHeld`, `invY == 1`) : même effet.
- À 19:36 l'invité a écrit 5 fois `Dropping CardAddThingDelta from peer 0, uid … cannot be resolved here` pendant
  que l'host minait : c'est ce chemin. Dans ces 5 cas l'host avait empilé lui aussi (la quantité suit :
  `Applying card num 12264425: 16 -> 17`), donc sans écart ; il suffit d'un cas où l'host n'empile pas.

Portée : c'est la copie d'un sac que **personne n'enregistre** (la vérité est chez le jeu qui tient la carte). Pas
d'objet perdu ni doublé pour le joueur concerné. Visible seulement si on regarde ou échange avec ce joueur.

Sacs 541, 582, 658 (le sac d'un invité vu par LUI-MÊME, `bags of 1,541` vient du pair 2 qui joue 541) : apparus à
20:25:33, juste après les retours de 20:25:10-19 (`Replaced remote chara`, copie du monde renvoyée). Là c'est le sac
**du joueur lui-même** qui diffère de la copie de l'host, et cette copie est celle qui est enregistrée. **Hypothèse** :
objets à numéro provisoire renumérotés par l'host (`ElinNetHostTravel.cs`, `ReplaceRemoteChara`, `AssignUID`) ou
équipement remis chez l'invité (`ElinNetClientPlayer.cs:220`). Pas prouvé : le prochain journal nommera les cartes.

## 2. `charas 8/10`, `9/9 (not the same ones)`, `10/13`, `11/13`, `12/14` : vrai écart, non réparé par le rechargement

Verdict : **vrai écart** (un invité a moins de personnages que l'host), **cause non établie**. Pas un faux positif
connu : les deux jeux comptent pareil (ni morts, ni hors carte, ni numéros provisoires).

Séquence A (pair 1) :
- 20:24:52 `Host leaves Zone_startSite@0, LemiWinks keeps it` ; 20:25:09 `Recalling zone … from LemiWinks` ;
  20:25:10.21 `Replaced remote chara 582`, `658` ; 20:25:10.33 `World and map Zone_ntyris@0 sent together to player 1`
  (l'host est encore sur la carte du monde) ; 20:25:11.27 `Replaced remote chara 541` (APRÈS la copie du pair 1) ;
  20:25:18.77 `…but the zone state is stale, switching to … Zone_startSite@0` : le pair 1 reçoit la carte seule, sans
  nouvelle copie du monde ; 20:25:19.08 placé.
- 20:25:47 `Player 1 reports … charas 8/10, bags of 582, reload true` ; 20:25:47.36 `Received zone state request` ;
  20:26:01 de nouveau `charas 8/10` : **le rechargement n'a rien changé**. 20:26:05 le pair 1 quitte la partie.
- Les sacs comparés par ce pair ne contiennent ni 541 ni 658 (seulement `582`), alors que ces deux joueurs sont sur
  la carte de l'host : indice que **les 2 personnages manquants sont ceux des deux autres joueurs**. Indice, pas preuve.

Séquence B (pair 2) : 20:26:05 le pair 1 part (`remote chara 582 removed from map`) ; 20:26:09 `charas 9/9 (not the
same ones) … reload true` ; 20:26:23 encore `9/9 (not the same ones)` : rechargement sans effet. Même nombre, pas les
mêmes : un personnage en trop (probablement 582, qu'un invité ne retire jamais de lui-même :
`WorldStateSnapshot.cs:116` épargne les personnages des joueurs) et un en moins.

Séquence C : 20:27:39 l'host reprend la carte au pair 3 ; pairs 3 et 1 placés à 20:27:47 et 20:27:49 ;
20:28:00 pair 3 `charas 10/13` ; 20:28:02 pair 1 `11/13, reload true` ; 20:28:07 pair 3 `10/13, reload true`, puis plus
rien du pair 3 pendant 41 s (réparé, ou nombres qui bougent) ; 20:28:32 pair 1 `charas 12/14, things 17/18`.
Les nombres du passage de main donnent les personnages NON globaux de l'host sur cette carte : 4 (20:24:52), 2
(20:26:25), 7 (20:28:48). Il y en a donc 5 de plus après que le pair 3 a tenu la carte (animaux ou visiteurs
apparus chez lui, ou chez l'host à son retour).

Ce que le code prouve :
- Un rechargement de carte (`RequestZoneState`) n'apporte que le fichier de carte : les personnages **non globaux**
  (`Map.Save` saute `IsGlobal`). Les personnages des joueurs, leurs compagnons, les habitants globaux vivent dans le
  monde : un rechargement ne peut pas les rendre. C'est ce que montrent A et B.
- Les positions envoyées 5 fois par seconde remettent sur la carte tout personnage que l'invité **connaît**
  (`CharaStateSnapshot.cs:137-150`). Un écart qui dure est donc un personnage que l'invité ne connaît plus du tout
  (ni dans son monde ni dans sa mémoire des cartes), ou qu'il compte autrement.
- Piste (lue, pas prouvée) : quand un joueur quitte la carte de l'host, chaque autre invité l'efface de son monde
  (`CharaRemoveFromGameDelta.cs:28`). Quand il revient, il est rendu par `CardGenDelta`, qui le met dans la mémoire
  des cartes mais **pas dans le monde** (`CardGenDelta.cs:63`, pas de `globalCharas.Add`). Au prochain chargement de
  carte de cet invité (y compris le rechargement automatique) il n'est plus posé, et ne revient que si l'objet est
  encore en mémoire.

## 3. `things 16/17`, `17/17 (not the same ones or amounts)` : un objet au sol, réparé par le rechargement (probable)

Pair 3 : `16/17` à 20:25:31 (12 s après son arrivée), `17/17 (not the same…)` à 20:25:43, `16/17` à 20:26:01, puis
`reload true` à 20:26:03. Ensuite plus aucune ligne de ce pair jusqu'au départ de l'host (20:26:25, 22 s) : l'écart
n'est pas resté. Le sol est dans le fichier de carte : un rechargement le répare. **Vrai écart, court, réparé**
(probable : 22 s seulement d'observation). Lequel : inconnu. Le nombre qui passe de 16 à 17 puis revient à 16 fait
penser à un objet que ce joueur manipulait (posé ou porté). `things 17/18` du pair 1 à 20:28:32 : rechargé, l'host
quitte la carte 16 s après, pas de suite.

## 4. Rechargements automatiques

6 en tout (`Received zone state request`) : pair 1 à 20:25:47, 20:28:02, 20:28:32 ; pair 3 à 20:26:03, 20:28:07 ;
pair 2 à 20:26:09. Écart minimum pour un même pair : 30 s (la borne).

| Pair, heure | Pour | Après |
|---|---|---|
| 1, 20:25:47 | charas 8/10 | 20:26:01 : toujours 8/10. Sans effet |
| 3, 20:26:03 | things 16/17 | silence 22 s. Réparé (probable) |
| 2, 20:26:09 | charas 9/9 autres | 20:26:23 : pareil. Sans effet |
| 1, 20:28:02 | charas 11/13 | 20:28:16 : plus de ligne « charas » ; 20:28:32 : 12/14. Pas réparé |
| 3, 20:28:07 | charas 10/13 | silence 41 s. Réparé ou instable |
| 1, 20:28:32 | charas 12/14, things 17/18 | l'host part 16 s après |

Le garde-fou « 3 sans effet » n'a jamais joué : au plus 2 par pair et par séjour, et les compteurs repartent de zéro
à chaque changement de carte (le pair 1 est passé par `Zone_field` entre ses rechargements). Bilan : 3 rechargements
sur 6 demandés pour des personnages qu'un rechargement ne peut pas rendre. Corrigé (voir plus bas).
Trouvé en passant : le silence de 12 s après un rechargement était ramené à 6 s par l'arrivée de la carte. Corrigé.

## 5. `Replaying {Held} held deltas` : juste, rien n'est doublé

- La copie du monde est prise après que l'host a vidé ses messages (`SendSaveProbe` : `RefreshBuffer` puis
  `WorldStateDeltaUpdate` avant l'envoi) : ce qui est retenu est arrivé APRÈS la copie, donc n'y est pas.
- `CharaTickDelta` et `CharaTickConditionDelta` ne touchent jamais le personnage du joueur local (`IsPC` : ignoré).
  Sa faim et ses états ne vivent pas 735 tours d'un coup.
- Les 735 tours sont ceux des AUTRES joueurs pendant les 12,6 s du premier chargement (~58 par seconde pour 2 ou 3
  joueurs). Ils sont rejoués d'un bloc sur leurs copies, qui ont bien vécu ces tours chez eux. Les états ne sont pas
  comptés deux fois : sur une copie (`GoalRemote`), `Chara.Tick` saute `TickConditions`
  (`CharaTickConditionEvent.cs`), seul le message les fait avancer. La vie est de toute façon recalée 5 fois par
  seconde. `0 lost over the limit` partout.
- Effet visible possible : une saccade à l'arrivée et des copies qui « rattrapent » (`Move delta jump chara 1` à
  19:32:39). Pas un défaut de données.

## 6. Passage de main

`Taking over … our copy is the same, kept` (19:46:06, 19:50:30, 19:51:30) et `Host leaves … host copy sent along
true` : cohérent. À noter : le sol de `Zone_startSite` est identique à 20:24:52 et 20:26:25 (`things 17:5BE0AE33`).
`host copy sent along false: none` à 20:29:06 : carte du monde, normal.

## Ce qui a changé (`ElinTogether/Net/NetDesync.cs`, compilé `ReleaseNightly` 0 erreur, **jamais lancé**)

1. **Les sacs n'avertissent plus et ne déclenchent rien.** Plus de `bags of …` dans les avertissements. À la place,
   au plus une fois par sac et par 5 minutes : l'invité envoie le contenu qu'il a (numéro, quantité, porté), et
   l'host écrit, en Information, `Player {PeerIndex} holds another bag of {Uid} on {ZoneFullName}, left as it is
   (- it lacks, + only it has, amount there/here) [{Diff}]` avec le nom de chaque carte. Chez l'invité :
   `Bags of {Uids} differ from their keeper's … left as they are` (Information).
2. **Un rechargement n'est demandé que s'il peut réparer** : objets au sol différents, ou personnages NON globaux
   différents (deux nombres ajoutés au message : `Locals`, `LocalMix`). Un écart de personnages globaux avertit
   toujours, mais ne recharge plus.
3. **L'avertissement nomme ce qui diffère.** Avec lui partent les numéros des personnages (s'ils diffèrent) et des
   objets au sol (s'ils diffèrent). L'host écrit : `Player {PeerIndex} on {ZoneFullName}: characters it lacks
   [{Missing}], characters only it has [{Extra}], sent again {Resent}` et `… floor items differ … [{Diff}]`.
   Le détail dit aussi `of which not global a/b`.
4. **Réparation des personnages manquants** (règle `AutoResync`) : l'host renvoie à tous le personnage que l'invité
   n'a pas (`CardGenDelta`, sans effet chez qui le connaît, 8 au plus par signalement) ; les positions le remettent
   alors sur la carte en moins d'une seconde. Ne répare pas un personnage que l'invité connaît mais ne compte pas :
   la ligne de l'host le dira.
5. Le silence de 12 s après un rechargement n'est plus raccourci.
6. Host et invités doivent avoir la même version (le calcul et le message ont changé) ; la connexion le vérifie déjà.

`dev/_tools/resync_suite.py` R5 : attend la ligne de l'host qui nomme l'écart, et aucun avertissement.

## Corrections à faire ailleurs (pas dans mes fichiers)

1. `Models/Delta/Card/CardAddThingDelta.cs:34` : relire les données jointes quand la carte locale est détruite.
   Avant : `if (Thing.Find() is not Thing { isDestroyed: false } thing) { warning; return; }`.
   Après : si `Thing.Find()` rend une carte détruite et que `Thing.Data` n'est pas nul, `CardCache.Remove(Thing.Uid)`
   puis `Thing.Find()` de nouveau (il la refait depuis les données, que l'host joint toujours, `OnRefresh`). C'est la
   plus petite correction qui guérit les sacs des autres joueurs quelle que soit la cause de la destruction locale.
2. `Models/Delta/Chara/CharaPickThingDelta.cs:27` et `:65` (+ `Patches/DeltaEvents/Chara/CharaPickThingEvent.cs:66`,
   fichier de l'autre agent) : ajouter `[Key(4)] public bool TryStack { get; init; } = true;`, le remplir avec
   l'argument `tryStack` du ramassage d'origine, rejouer `chara.Pick(thing, tryStack: TryStack)`.
3. `Models/Delta/Chara/CharaSwitchHeldDelta.cs:45` : sur une copie, `chara.held = null` quand l'objet tenu est dans
   son sac, au lieu de `chara.PickHeld()` (qui empile).
4. `Models/Delta/Card/CardGenDelta.cs:63` : un personnage global reçu (`card is Chara { IsGlobal: true }`) est aussi
   ajouté à `game.cards.globalCharas`, sinon il disparaît de cet invité à son prochain chargement de carte.
   À vérifier avec le prochain journal avant de le faire (piste du point 2).
5. `Models/Delta/Chara/CharaActPerformDelta.cs:111` (fichier de l'autre agent) : 107 exceptions dans ce journal,
   toutes `ToolKind: Zap`, `ActId: 0`, `Tool: null` → `ACT.Create(0)` lève `InvalidCastException`. Quand l'outil
   n'est pas trouvé chez l'invité, sortir avant `ACT.Create`. (La baguette de l'host introuvable chez l'invité est
   peut-être le même écart de sac qu'au point 1.)
6. Hors sujet mais dans ce journal : de 20:28:49 à 20:29:07 le pair 2 est refusé 4 fois de suite par la carte tenue
   par le pair 3 (`Zone 7 refused player … it returns to the host`), avec une copie du monde renvoyée à chaque fois.

## Pas sûr

- La cause exacte de `bags of 1` et des personnages manquants : pistes lues dans le code, pas prouvées.
- Rien de ce qui a changé n'a été lancé. Le plus fragile : le renvoi d'un personnage par `CardGenDelta` (point 4).
- `IsGlobal` supposé identique chez l'host et l'invité pour un même personnage ; sinon un rechargement de trop ou de
  moins, sans autre effet.
- Session de zone (invité chez un invité) : la ligne qui nomme les cartes s'écrit dans le journal du joueur qui tient
  la carte, pas dans celui de l'host.
