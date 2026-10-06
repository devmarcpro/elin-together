# Invités ramenés sur l'host (lecture du code, 2026-10-06, version 0.26.506)

Rapport d'une vraie partie à trois joueurs ou plus (l'utilisateur est invité) : « Les personnages invités ne font
que se faire tp sur l'host. » Même soirée : téléportations au sommeil, un ami « tp dans l'eau sur la carte du
monde », un ancien personnage « vu en jeu qui se battait ». Étude par lecture seule, rien n'a été lancé.
« non vérifié » = déduit du code, jamais joué. Chemins : `J:` = `dev/_decomp/Elin/`, `M:` = `ElinTogether/`.
Suite de `dev/PLAN_sommeil_teleportations.md` (familiers tirés sur le lit de l'host : sa cause A).

## Résumé
- **Le jeu lui-même ne peut presque pas déplacer le personnage d'un invité chez l'host** : son IA est `GoalRemote`,
  `Chara.Tick` et `Chara._Move` sont coupés pour lui. Suivi du chef, téléportation « trop loin », laisse : sans effet.
- **Le mod, lui, pose l'invité à côté de l'host à chaque fois que l'invité charge une carte** : une seule ligne,
  `pc.pos.GetNearestPoint(...)` (M:Net/Host/ElinNetHostZone.cs:100). Deux exceptions seulement existent
  (`_returnSpots`), et elles ne couvrent que **le premier** invité. À trois, le deuxième invité et les suivants
  rechargent la carte et atterrissent sur l'host (ou sur le joueur qui « tient » la carte) à chaque changement de
  carte de l'host. C'est la cause la plus probable, et deux fenêtres ne la montrent pas.
- Rien trouvé du côté « le déplacement de l'invité A appliqué à l'invité B » : écarté (voir la fin).

## 1. Ce que le jeu fait à un membre du groupe, et pourquoi l'invité y échappe
- Chez l'host, l'invité est dans `pc.party` (`MakeAlly`, M:Net/Host/ElinNetHostPlayerManager.cs:221). Son IA est
  `GoalRemote` (M:Elements/GoalRemote.cs) : tout `SetAI` sur lui est remplacé par `GoalRemote`
  (M:Patches/DeltaEvents/Chara/CharaTaskRemoteEvent.cs:31-38, message « Reset remote on <uid>, was X, requested Y » :
  ce message dit seulement que le jeu a voulu lui donner une IA, pas qu'il a été déplacé).
- `Chara.Tick` ne tourne pas pour lui (M:Patches/DeltaEvents/Chara/CharaTickEvent.cs:23-25) : pas d'`AI_Idle`, donc
  pas de « suivre le chef » ni de téléportation après 10 échecs (J:AI_Idle.cs:448-471).
- `Chara._Move` est refusé pour lui (M:Patches/DeltaEvents/Chara/CharaMoveEvent.cs:14-17). Or `Card.Teleport` passe
  par `_Move` (J:Card.cs:6220) : succube, garde du corps (J:Chara.cs:9001), sorts de téléportation ne le bougent pas
  chez l'host. La laisse (J:Chara.cs:3267-3275) appelle `TryMoveTowards`, donc `_Move` : sans effet aussi.
- Ce qui passe quand même : `Card.MoveImmediate` (J:Card.cs:6168, écrit la case sans `_Move`) et `Zone.AddCard`.
  Appels qui visent « à côté du joueur local » : « dormir à côté » (J:ConSleep.cs:121), le bouton « appeler » de la
  liste du groupe (J:ListPeopleParty.cs:178), `Chara.GetRevived` (J:Chara.cs:5480), l'entrée du groupe sur une carte
  (J:Zone.cs:1747-1775) et `Chara.MoveZone` du chef qui emmène les membres (J:Chara.cs:3685-3693).
- Les **compagnons** (pas les joueurs) gardent l'IA du jeu chez l'host : ils suivent leur maître
  (M:Patches/CompanionFollowPatch.cs:38-41) mais **retombent sur le chef du groupe, l'host,** si le maître n'est pas
  « vivant sur cette carte » (M:Helper/CompanionHelper.cs:40-48), puis se téléportent sur lui (J:AI_Idle.cs:469).
- Chez l'invité, son propre personnage n'est jamais corrigé par l'instantané de l'host
  (M:Models/WorldState/CharaStateSnapshot.cs:96-98). Seuls le déplacent : l'arrivée sur une carte
  (M:Net/Client/ElinNetClientZone.cs:223), la résurrection (M:Models/Delta/Chara/CharaReviveDelta.cs:93-100).

## 2. Les causes, de la plus à la moins probable (« trois joueurs ou plus, tout le temps »)

### C1. Le deuxième invité et les suivants rechargent la carte et atterrissent sur l'host (ou sur le teneur)
Avec le voyage indépendant (coché par défaut), quand l'host quitte une carte où se tiennent deux invités :
- le premier la « tient » (M:Net/Host/ElinNetHostTravel.cs:181-200), il ne bouge pas ;
- les autres deviennent ses visiteurs (l.203-213 ; `StayAsGuest`, M:Net/Client/ElinNetClientTravel.cs:498-513) : leur
  jeu **recharge tout** (monde du teneur, puis la carte) et le teneur les pose **à côté de lui**
  (M:Net/Host/ElinNetHostZone.cs:100-118 ; `ReplaceRemoteChara` a vidé leur carte, ElinNetHostTravel.cs:1276 ; aucune
  case gardée : `_returnSpots` n'est jamais rempli dans une session de carte).
- Le teneur part à son tour : la carte passe au visiteur suivant (`HandOverZone`, ElinNetHostTravel.cs:944-964), les
  autres rechargent encore et atterrissent sur le nouveau teneur.
- **L'host revient sur cette carte** : il la rappelle (l.712-718). Le teneur garde sa case
  (`_returnSpots`, l.1101-1102, condition `handedBack`). Les visiteurs sont rappelés (l.934-941), rendent leur
  personnage sans carte (`handedBack` faux), donc `_returnSpots.Remove` (l.1104) : **posés à côté de l'host**, là où
  il vient d'entrer.
- Fréquence : à chaque changement de carte de l'host ou du teneur, pour tous les invités sauf un. Dans un donjon ou
  entre ville et carte du monde : sans arrêt. L'invité qui s'est connecté le premier ne le voit presque pas.
- À deux joueurs : non (le seul invité est toujours le teneur). `trio_suite` (4 fenêtres) regarde qui tient la carte
  et les objets, **jamais la case des joueurs** (dev/_tools/trio_suite.py, t3) ; non relancée depuis la 0.26.442.
- Jamais joué : non vérifié en jeu. Les lignes de code, elles, sont lues.

### C2. L'invité est « emmené » : voyage indépendant décoché, ou invité pas encore installé
- Décoché chez l'host : rien ne retient les invités (ElinNetHostTravel.cs:154), le jeu emmène le groupe du chef
  (J:Chara.cs:3685-3693), tous rechargent et sont posés à côté de l'host (ElinNetHostZone.cs:100). L'invité qui veut
  sortir seul est refusé avec « emp_party_gather » (ElinNetClientTravel.cs:98-101). Voulu, mais c'est exactement
  « ils ne font que se faire tp sur l'host » si la case a été décochée sans le savoir.
- Coché : seuls restent les invités **installés** (`_settled`, l.168) ; celui qui charge encore la carte (il vient
  d'arriver, de revenir, d'être rappelé) suit l'host à la carte suivante (l.165-167). Un host qui enchaîne les
  escaliers plus vite que les invités ne chargent les traîne à chaque étage. Plus il y a de joueurs, plus les
  chargements durent (non vérifié). `_settled.Clear()` (l.170) vide aussi la liste à chaque départ.
- À deux joueurs : oui, pareil.

### C3. Entrer par soi-même sur la carte où est l'host = atterrir sur l'host, pas à l'entrée
- Un invité qui prend un escalier, une porte ou sort d'une ville vers la carte où se tient l'host « revient chez
  l'host » (ElinNetClientTravel.cs:116-123, `SendRejoin`) et est posé à côté de lui (ElinNetHostZone.cs:100). La
  case gardée ne vaut que pour la carte qu'il rend (l.103-104 : `spot.ZoneUid == _zone.uid`), pas pour celle où il
  entre.
- **Carte du monde** : sortir d'une ville pendant que l'host marche sur la carte du monde pose l'invité à côté de
  l'host, parfois à l'autre bout du pays. La case choisie est la plus proche « libre » (J:Point.cs:624-674), sans
  regarder si c'est la mer : c'est très probablement « un ami tp dans l'eau sur la carte du monde » (que
  `GetNearestPoint` accepte une case de mer : non vérifié). En solo le groupe partage la case du joueur sur la
  carte du monde (J:Zone.cs:1752-1770).
- Fréquence : à chaque entrée d'un invité sur la carte de l'host. À deux joueurs : oui.

### C4. Compagnons des invités tirés vers l'host
- Sommeil de l'host : familiers posés sur son lit (cause A du plan sommeil, J:ConSleep.cs:106-130).
- Maître mort ou pas « vivant sur la carte » : le compagnon suit puis se téléporte sur l'host (voir §1).
- Résurrection d'un compagnon par l'host (liste du barman) : il se relève à côté de l'host (J:Chara.cs:5480 ;
  M:Patches/Remote/RemoteRevivePatch.cs ne couvre que la demande d'un invité).
- Si « personnages invités » veut dire « nos compagnons », c'est ici. À deux joueurs : oui.

### C5. Résurrection d'un joueur à côté de l'host
- Un invité mort dont la case n'est plus connue de l'host est relevé à côté de l'host
  (M:Models/Delta/Chara/CharaReviveDelta.cs:46-53). Le plus souvent il se relève où il est tombé. Rare.

### C6. Nouveautés de la 0.26.506 : aucune ne rappelle un invité sur l'host (lu)
- Mode construction d'un invité : seul l'« agent » invisible est déplacé (M:Models/Delta/Zone/AgentTaskDelta.cs:100-102).
- Échange de personnages : `arriving.pos.Set(former.pos)` ne tourne qu'au chargement d'un monde repris
  (M:Net/Host/ElinNetHostHandOver.cs:211-343) ; `GiveOrphanTo`, appelé à chaque connexion
  (ElinNetHostPlayerManager.cs:75-77), ne change qu'une table.
- Duels, « un joueur ne tue pas un joueur », base gérée par un invité, hauteurs de terrain : aucun `MoveImmediate`,
  `Teleport` ni `pos.Set` sur un joueur (recherche dans tout `ElinTogether/`).
- `PlayerStandIn.For` et `RemoteCraft.AsCrafter` font de l'invité « le joueur » le temps d'un geste
  (M:Helper/PersonalQuests.cs:403-425). Risque lu, non vérifié : si ce geste déclenche un `pc.MoveZone` (rappel,
  évasion rejoués chez l'host), `TryEnterZone` croit que **l'host** part
  (M:Patches/DeltaEvents/Chara/CharaMoveZoneEvent.cs:14-16) et laisse tout le monde derrière. Rare.
- La reconnexion automatique (`c34732d`) est **après** la 0.26.506 : pas dans la partie jouée.

### Écarté : le déplacement de l'invité A appliqué à l'invité B
- Un pas porte l'uid du personnage (`Owner`, M:Models/Delta/Chara/CharaMoveDelta.cs:14-15), pas un numéro de joueur ;
  chaque jeu ignore le sien (l.47) ; l'host le relaie tel quel (l.72-74).
- La position qu'un invité déclare (5 fois par seconde) est appliquée à `ActiveRemoteCharas[peer.Id]`
  (M:Net/Host/ElinNetHostUpdate.cs:154-155), la sienne. Pas de repli sur l'host : s'il manque, exception, rien bougé.
- Numéros de joueur : 0 = diffusion et host, puis 1, 2, 3… par compte Steam, gardés à la reconnexion
  (M:Net/Steam/SteamNetPeer/SteamNetPeer.cs:21-53). Deux comptes Steam ne peuvent pas partager un numéro. Deux
  joueurs sur le **même** compte Steam auraient le même numéro : non vérifié, improbable.
- Aucun `First()`, `Single()`, `Peers[0]` sur les joueurs en jeu (recherche faite) ; `PcOwners.First()`
  (ElinNetHostHandOver.cs:66) est une table à une entrée.
- Consignes « ne pas s'éloigner » / « ne pas vagabonder » (D14) : seulement pour les compagnons
  (M:Patches/DeltaEvents/Card/CardActReplayEvent.cs:130-144).

## 3. Les autres retours de la soirée
- **Téléportations au sommeil** : plan sommeil, causes A et B. S'y ajoute C1 : à la fin de nuit rien ne recharge,
  mais un host qui change de carte juste après fait sauter les visiteurs.
- **« Dans l'eau sur la carte du monde »** : C3.
- **« Mon ancien personnage se battait »** (non vérifié) : un personnage de joueur reste membre de la base de l'host
  (`_MakeAlly`, J:Chara.cs:2545-2549). Quand son joueur en change, il sort du groupe mais reste habitant. L'host
  l'enlève de sa carte une fois par seconde (M:Net/Host/ElinNetHost.cs:142-146) ; **un invité qui tient une carte
  seul n'a pas ce ménage** (`Connection` nulle), ni un teneur avant d'avoir des visiteurs : l'ancien personnage y
  vit avec l'IA du jeu, comme un habitant, et se bat. À confirmer par la question 3.

## 4. Plus petite correction et test, pour les trois premières

**C1.** Garder la case de tout invité qui était déjà sur la carte.
- Retour de l'host : dans `OnZoneLeaseRelease`, lire `_guests[peer.Id].ZoneUid` **avant** `_guests.Remove` (l.1094)
  et remplir `_returnSpots` aussi pour un visiteur (condition `release.Rejoin && chara?.pos` valide, carte = celle
  qu'il visitait). 4 lignes.
- Départ de l'host et passation : un champ `Stays` dans `ZoneGuestRequest`, mis par `LeavePlayersBehind` et
  `HandOverZone` ; le teneur garde alors la case du personnage reçu (`RegisterGuest`, une table par compte Steam lue
  dans `OnZoneDataReceivedResponse`). ~12 lignes.
- Test : **trois fenêtres obligatoires** (`mp_test.py --clients 2`, modèle `trio_suite.py` t3). A et B à 10 cases
  l'un de l'autre et de l'host ; l'host sort ; noter la case de B dans le jeu de A et de B ; l'host rentre ; même
  mesure. Rouge aujourd'hui : B à 1 case du teneur, puis à 1 case de l'host. Vert : B n'a pas bougé de plus d'1 case.
  Accord de l'utilisateur nécessaire pour trois fenêtres sur le Steam Deck.

**C2.** Pas un défaut à corriger à l'aveugle : d'abord la question 1. Si la case était décochée : rien à corriger,
mais le dire à l'invité (un message « l'host vous emmène » à l'arrivée, 3 lignes). Si elle était cochée : compter
comme installé un invité dont le personnage se tient déjà sur la carte quand l'host part (au lieu d'attendre la
fin de son chargement). Test à deux fenêtres (modèle `travel_suite.py`) : l'invité revient chez l'host, l'host change
de carte dans la seconde ; rouge : l'invité est emmené ; vert : il reste et tient la carte.

**C3.** Carte du monde d'abord : l'invité qui sort d'une ville envoie la case de cette ville dans sa demande de
retour (`ZoneLeaseRelease`, un champ `ArrivePos`), l'host la met dans `_returnSpots` pour la carte où il se tient.
~10 lignes. Test à deux fenêtres (modèle `travel_suite.py`) : host sur la carte du monde à 15 cases de Vernis,
l'invité sort de Vernis à pied ; rouge : l'invité est à 1 case de l'host ; vert : sur la case de Vernis. Escaliers
et portes (arriver à l'entrée, pas sur l'host) : plus gros, à voir avec l'utilisateur.

## 5. Trois questions courtes au joueur
1. Ça arrivait quand l'host changeait de carte (escalier, sortie de ville), avec un écran de chargement chez toi,
   ou en pleine marche sans chargement ? Et l'host avait-il touché à la case « voyage indépendant » ?
2. Tout le monde était touché, ou surtout ceux arrivés après le premier invité ? C'était toi, ou tes compagnons ?
3. Ton ancien personnage : tu l'as vu où (la base, une ville) et l'host était-il sur cette carte ?

## 6. Quoi chercher dans le journal de l'host
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs\Session_<date>.log` (niveau Debug écrit,
M:Emp/Logger/EmpLogger.cs:111-114). Compter et dater :
- « Assigned zone sync position to player … at … » : **chaque** pose à côté de l'host. Une rafale = C1, C2 ou C3.
- C1 : « Host leaves …, … keeps it », « Player … joins the zone session of … », « Zone … handed over to … »,
  « Recalling zone … from … before entering », « Player … returns to the host zone ».
- C2 : « Dispatching zone to all players » sans « Host leaves … keeps it » juste avant (personne n'est resté).
- C3 : « Player … returns to the host zone » sans « Recalling zone » avant (l'invité est venu de lui-même).
- Déplacements forcés hors chargement : « Reconcile force move chara », « Move delta jump chara », « Removing stale
  chara », « Removing duplicate map chara ». S'il y en a beaucoup sans changement de carte, ce plan a manqué
  quelque chose.
- Compagnons : « Companion … back with player … at … ». Morts : « Revive chara … at … ».
- Journal d'un invité, si on l'a : « Joining the zone session of », « Took over zone », « Host recalls zone »,
  « Host entered away zone … without recall, rejoining », « Zone session ended », « Received zone activation ».
