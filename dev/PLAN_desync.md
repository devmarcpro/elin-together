# « Énormément de desync entre les joueurs » : enquête par lecture (2026-10-06, soir)

Retour de la vraie partie (Steam, 3 joueurs ou plus, version publiée 0.26.510). **Pas de journaux de cette partie.**
Lecture du code exact de la 0.26.510 (`git show b1f83c3:<fichier>`), rien lancé. « lu » = vu dans ce code, ligne
donnée ; « supposé » = déduit, à prouver. Chemins relatifs à `ElinTogether/`. Test de D6 : `combat_suite`, 200 coups.
Les journaux sont en JSON : le texte à chercher est celui du champ `"@mt"`, tel quel, accolades comprises.

## 1. Les faits d'abord

- **Il n'y a pas de resynchronisation des objets.** L'instantané (5 fois par seconde) ne porte que les
  **personnages présents** : vie, camp, maître, case si l'écart dépasse 2 cases, et il retire les personnages en trop
  après 2 instantanés (lu, `Models/WorldState/WorldStateSnapshot.cs:39-73, 75-139`, `CharaStateSnapshot.cs:84-167`).
  Il ne porte ni les objets au sol, ni les sacs, ni l'équipement, ni les compétences, ni le terrain, ni les coffres.
- **Un personnage qui manque chez un invité ne revient jamais** par l'instantané : il est cherché par son numéro, pas
  trouvé, ligne suivante (lu, `CharaStateSnapshot.cs:86-89`, `Models/RemoteCard.cs:106-118` : sans données jointes,
  rien à fabriquer). C'est la forme générale du « boss que les invités ne voient pas ».
- **Un message qui parle d'une carte (objet ou personnage) inconnue est jeté sans une ligne au journal** chez
  l'invité, dans presque tous les types (lu : `CardPlacedDelta.cs:24-26`, `CardRemoveThingDelta.cs:18-20`,
  `CharaDieDelta.cs:32-34`, `CardDamageHpDelta.cs:45-47`, `CharaMoveDelta.cs:47-49`, `ZoneAddCardDelta.cs:27-34`).
  Trois types seulement attendent (`DeferLocal`), et seulement tant qu'aucune carte n'est chargée. Rien n'est redemandé.
- **Un écart dure donc jusqu'au prochain chargement de carte** de ce joueur (objets, monstres) ou jusqu'à sa
  prochaine copie du monde (sacs et équipement des autres joueurs et des compagnons, qui ne sont pas dans la carte).
- **Il n'existe aucune somme de contrôle, aucune détection.** « Falling behind with {DroppedTicks} dropped ticks »
  (lu, `Net/Client/ElinNetClientUpdate.cs:49-57`) compare les numéros de deux instantanés reçus de suite, écrit la
  ligne, et **ne fait rien** : rien n'est jeté par elle, rien n'est rattrapé.
- Ce qui existe pour réparer à la main : `emp.reconnect_self` (invité) et `emp.reconnect <numéro>` (host) dans la
  console du mod (lu, `Emp/EmpConsole.cs:47-73`) : monde + carte renvoyés. **À dire au joueur dès ce soir.**
- L'ordre entre trois jeux est sûr pour ce qui passe par l'host : il applique, puis renvoie à tous dans son ordre
  (lu, ex. `CardModNumDelta.cs:26-35`, valeur absolue). Les écarts viennent de messages **manquants**, pas de l'ordre.

## 2. Les causes, classées pour une soirée à 3 ou 4 par Steam

| # | Cause | Probabilité | Corrigée dans le dossier de travail ? |
|---|---|---|---|
| D1 | Trou entre la copie du monde et la copie de la carte, à chaque arrivée ou retour d'un joueur | forte | non |
| D2 | Passation : la carte « telle qu'elle est à l'écran » de l'invité devient la vérité | forte (multiplie les autres) | non |
| D3 | Message fiable refusé par Steam (file pleine, 512 Ko ou plus) et perdu sans bruit | moyenne (dépend des tailles) | oui, `9a25491` (pas joué, pas publié) |
| D4 | Carte reçue pendant que le jeu tourne : rien n'est retenu jusqu'au rechargement | moyenne | non |
| D5 | Carte inconnue = message jeté, jamais réparé ; l'host détruit l'objet « fantôme » chez tous | moyenne (suite de D1 à D4) | non |
| D6 | Aléatoire rejoué dans chaque jeu (effets annexes d'une action) | faible à moyenne (supposé) | non |
| D7 | Lecture du réseau, 8 messages par image : retard, pas écart | faible pour l'écart, forte pour l'impression | oui, `dfa476d` (pas joué) |
| D8 | Une exception en lisant un message fait perdre le reste du lot (jusqu'à 7 messages) | faible | oui, `9a25491` |
| D9 | Numéros d'objets : plages de 50 000 sans plafond | faible ce soir | non |
| D10 | Filtres de réception (absent, départ, poignée de main, pair inconnu) | faible : voulu, trouvé correct | - |

### D1. Trou entre la copie du monde et la copie de la carte (forte)
- **Lu.** Un joueur qui arrive ou revient reçoit d'abord le monde entier (`Net/Host/ElinNetHostPlayerManager.cs:238-264`),
  le charge, **puis** demande la carte (`Net/Client/ElinNetClientPlayer.cs:163-246`). Entre les deux, son jeu n'est
  « pas commencé » et la retenue des messages ne démarre qu'à la réception de la carte
  (`Net/Client/ElinNetClientZone.cs:75`). Tout message reçu dans l'intervalle et marqué « jeu commencé requis » (le
  défaut, `Models/Delta/ElinDelta.cs:134`) est **jeté sans ligne au journal** (`Net/Base/ElinDeltaManager.cs:124-129`).
- Ce qui concerne la carte est rattrapé (la carte est copiée après). **Ce qui concerne les personnages des joueurs et
  leurs compagnons ne l'est pas** : ils sont dans la copie du monde, pas dans la carte. Durée du trou : transfert du
  monde + son chargement + un aller-retour, soit quelques secondes (supposé, non mesuré).
- **À deux**, pendant ce temps seul l'host agit (et il est souvent gelé par sa sauvegarde). **À trois ou quatre**, les
  autres jouent : ils ramassent, mangent, s'équipent, gagnent des compétences. Et chaque retour sur la carte de l'host
  est une copie du monde, donc un trou.
- **Vu par le joueur.** C revient sur la carte ; pendant son écran de chargement B ramasse une épée et l'équipe. Chez
  C, B a toujours l'ancienne arme ; l'épée n'existe pas. B la pose : chez C rien n'apparaît (objet invisible). C ne
  peut pas l'échanger ni la ramasser.
- **Preuve au journal.** Le rejet lui-même n'écrit rien. Indirecte, chez l'host, plus tard :
  `Dropping {DeltaType} from peer {PeerIndex}, owner {OwnerUid} or thing {Uid} unresolved`, ou
  `Refusing stale {DeltaType} from peer {PeerIndex}, uid {Uid} is gone here`, peu après une ligne
  `Sending save probe to player {@Peer} for replication` pour un autre joueur.
- **Plus petite correction** (~15 lignes, 3 fichiers, après D3) : l'host envoie la carte **dans la même image** que
  le monde (`SendSaveProbe` appelle `PropagateZoneChangeState(_zone, peer)`), l'invité commence à retenir dès le monde
  reçu (`OnSaveDataProbe` -> `Delta.HoldForIncomingMap()`) et ne redemande pas la carte. Le doublon éventuel est déjà
  écarté (`ElinNetClientZone.cs:68-71`).
- **Test (3 fenêtres, `mp_test.py --clients 2`).** B fait `emp.reconnect_self` ; pendant son chargement, par `emp.py
  eval` chez A : ramasser un objet posé et manger une ration. Puis comparer chez l'host et chez B la liste
  `uid:Num` du sac de A. Pour élargir le trou : `Application.targetFrameRate=5` chez B. Rouge : listes différentes.
  Vert : identiques.

### D2. Passation « telle qu'à l'écran » (forte à 3 et plus : elle rend définitif tout écart)
- **Lu.** Voyage indépendant coché par défaut (`Emp/EmpConfig.cs:120-123`). Quand l'host quitte sa carte, le premier
  invité resté la garde **sans qu'aucune carte lui soit envoyée** : il continue avec sa copie
  (`Net/Host/ElinNetHostTravel.cs:151-214`, bail `Handoff` lignes 191-199 ; côté invité
  `Net/Client/ElinNetClientTravel.cs:425-493`). Les autres rechargent **sa** version. Au retour, sa version remplace
  celle de l'host.
- Ce n'est pas une source d'écart, c'est ce qui le **grave** : tout objet ou monstre que la copie de cet invité avait
  raté disparaît pour tout le monde, tout « fantôme » devient réel.
- **Vu par le joueur.** L'host tue un monstre et part ; chez A (resté) le monstre n'était pas mort ou le butin
  n'existait pas : pour A, B et l'host à son retour, c'est la version de A.
- **Preuve.** Host : `Host leaves {ZoneFullName}, {@Peer} keeps it, uid range from {UidRangeStart}`. Invité :
  `Took over zone {ZoneFullName}, uid range from {UidRangeStart}, from the host {WithHost}`. Un désaccord signalé
  juste après ces lignes = D2.
- **Plus petite correction** (~20 lignes, 2 fichiers, avec l'outil du §4) : l'host joint au bail sa somme de contrôle
  de la carte ; si celle de l'invité diffère, l'host envoie la carte (le champ `Map` du bail existe déjà) et l'invité
  la charge. Sans écart, aucun rechargement de plus.
- **Test (3 fenêtres).** Chez A, retirer un objet du sol par `eval` (`EClass._zone.RemoveCard`), puis l'host sort.
  Rouge : l'objet a disparu chez B et chez l'host revenu. Vert : il est là chez les trois.

### D3. Message fiable perdu à l'envoi (moyenne, dépend de la taille du monde et des cartes)
- **Lu.** `Net/Steam/SteamNetPeer/SteamNetPeer.cs:95-129` : si Steam refuse, `Send` rend `false`, **sans ligne au
  journal**. Diffusion : `SteamNetPeerBroadcast.cs:34-80`, même chose par joueur. Tous les appelants ignorent le
  retour sauf un (`Models/Delta/Card/ThingRequest.cs:97`) : listes de changements et instantanés
  (`Net/Host/ElinNetHostUpdate.cs:50, 70`), monde (`ElinNetHostPlayerManager.cs:263`), carte
  (`Net/Host/ElinNetHostZone.cs:29, 33`), baux, points de passage (`ElinNetClientTravel.cs:968`).
- **Débit (lu).** Host vers chaque invité : 5 instantanés par seconde (`ElinNetHostUpdate.cs:267`) + une liste par
  image jusqu'à 50 par seconde, car l'host y met le pas de temps à chaque image
  (`Patches/Synchronization/CoreSynchronizationContext.cs:56-66`). Invité vers host : 5 états + jusqu'à 50 listes
  quand il agit. Tailles : **non mesurées** ; un instantané pèse quelques dizaines d'octets par personnage (supposé).
- **Supposé.** Limites de Steam par défaut : 512 Ko par message, 512 Ko en attente par lien. Un message de 512 Ko ou
  plus est toujours refusé : le joueur reste bloqué au chargement (pas un écart). L'écart naît quand une carte ou un
  monde proche de 512 Ko occupe la file : les listes qui suivent pendant une ou deux secondes sont refusées **pour
  ce joueur seul**, donc trou définitif chez lui. Mesure sur ce PC : monde d'essai 839 Ko sur disque, plus grosse
  carte d'essai 214 Ko ; taille après compression par le mod inconnue. Un vieux monde avec une grosse base : inconnu.
- **Vu par le joueur.** Juste après une arrivée, celui qui charge ne voit pas ce que les autres ont fait entre-temps.
- **Preuve en 0.26.510.** Aucune ligne directe. Indirectes : `Falling behind with {DroppedTicks} dropped ticks` chez
  un invité **installé**, loin de tout changement de carte (les envois étant fiables et l'host rattrapant ses
  instantanés un par image, `Net/Base/TickScheduler.cs:21-22`, un trou hors chargement = un envoi refusé) ; host :
  `Dispatching zone to player {@Peer}` sans `Player {@Peer} has finished zone replication` ensuite ; invité :
  `Requesting zone state {@Zone} from host` sans `Received zone state`.
- **Déjà corrigé** dans `9a25491` : file d'attente par joueur, gros messages en morceaux de 128 Ko
  (`Net/NetFragments.cs`, `SteamNetPeer.Flush`). Nouvelles lignes : `Send queue of {@Peer} is full: …`,
  `Message of {Size} bytes sent in {Pieces} pieces`, `Message of {Size} bytes not sent: {Result}`. Pas joué.
- **Test.** `dev/_tools/chunk_check` (hors jeu) existe. En jeu, 2 fenêtres : une carte de plus de 512 Ko (poser des
  milliers d'objets par `eval`), l'invité y entre. Rouge (0.26.510) : bloqué. Vert : entre, et les lignes ci-dessus.

### D4. Carte reçue pendant que le jeu tourne (moyenne)
- **Lu.** `Net/Base/ElinDeltaManager.cs:222-227` : si le jeu de l'invité tourne, `HoldForIncomingMap` ne retient
  rien. Or la carte est photographiée chez l'host 2 images après son arrivée
  (`Patches/DeltaEvents/Zone/ZoneActivateEvent.cs:47`), et l'invité ne la charge qu'à la réponse de placement
  (`Net/Client/ElinNetClientZone.cs:157-226`). Entre les deux, les messages sur la nouvelle carte sont appliqués à
  l'ancienne : un objet créé reçoit pour parent une carte non chargée et n'y figure pas après chargement
  (`ZoneAddCardDelta.cs:54-56`, jeu : `Zone.AddCard`, `dev/_decomp/Elin/Zone.cs:2168-2196`).
- **Quand.** L'invité suit l'host sans recharger le monde : carte de quête, invité « pas encore installé », voyage
  indépendant décoché, second envoi d'une carte (`Net/Host/ElinNetHostZone.cs:86-93`), carte active rechargée.
- **Vu.** L'host arrive, ouvre un coffre ou tue un monstre tout de suite : l'invité arrivé 3 secondes après ne voit
  pas le butin.
- **Preuve.** Invité : entre `Received zone state` et `Received zone activation`, des lignes
  `Dropping stale move on chara {Uid} (expected {ExpectedZoneUid}, got {GotZoneUid})` (niveau Debug), et pas de
  `Starting initial scene init` (qui signe un jeu reparti de zéro).
- **Plus petite correction** (~15 lignes, 2 fichiers) : retenir aussi quand le jeu tourne, avec un drapeau « jusqu'au
  placement », relâché à la fin de `OnZoneActivateResponse`. Les messages sans carte (discussion, quêtes) passent.
- **Test (2 fenêtres).** Voyage indépendant décoché ; l'host change de carte et, par `eval` dans la même seconde, pose
  un objet. Rouge : absent chez l'invité. Vert : présent.

### D5. Carte inconnue : jamais réparée, puis détruite chez tous (moyenne, c'est la suite visible de D1 à D4)
- **Lu.** Voir §1. Et dans l'autre sens : quand un invité agit sur un objet que l'host n'a pas, l'host écrit
  `Refusing stale {DeltaType} from peer {PeerIndex}, uid {Uid} is gone here` et **diffuse « quantité 0 »** pour ce
  numéro (`Models/Pending/TaskCache.cs:26-45`) : l'objet disparaît chez tous les invités qui l'avaient.
- **Vu.** « Je marche sur un objet et il disparaît » (retour 17) : cela ressemble exactement à ceci (supposé : le
  retour 17 a aussi une cause propre au sac plein, `PLAN_ramassage_sac_plein.md`).
- **Preuve.** Host : la ligne ci-dessus (140 fois au banc le 5 octobre : à rapporter au nombre de changements de carte).
- **Plus petite correction** (~40 lignes, 3 fichiers) : petite demande « envoie-moi la carte numéro N » de l'invité
  vers l'host quand un instantané ou un message cite un numéro inconnu (une fois par numéro et par seconde) ; l'host
  répond `CardGenDelta` avec données + `ZoneAddCardDelta` à ce joueur (`SendDeltaTo`). Et ne plus diffuser
  « quantité 0 » à tous : seulement à l'expéditeur.
- **Test (2 fenêtres).** Par `eval` chez l'invité, retirer un monstre de la carte et du cache. Rouge : il ne revient
  jamais, l'host se bat seul contre lui. Vert : revenu en moins de 2 secondes.

### D6. L'aléatoire (faible à moyenne, en grande partie supposé)
- **Lu.** Une action d'un personnage est **rejouée** dans chaque jeu avec ses propres dés
  (`Models/Delta/Chara/CharaActPerformDelta.cs:95-120`). Sont ramenés à la valeur de l'host : la vie
  (`CardDamageHpDelta.cs:62-64` et l'instantané), la mort (seul l'host la décide, `CharaDieDelta.cs:27-30`), le
  butin (seul l'host crée, `CardGenDelta.cs:20-24`), le tirage de l'autel (`InvOwnerOnProcessDelta.cs:73, 165`), le
  jour (`DayDataDelta.cs`). Une carte n'est jamais générée chez un invité, toujours envoyée
  (`ElinNetClientZone.cs:126-128`).
- **Supposé, non lu jusqu'au bout.** Les effets annexes du rejeu chez l'invité (état posé par un coup, recul de moins
  de 3 cases, charges d'un objet) ne sont pas tous annulés. À vérifier type par type avant d'écrire.

### D7 à D10, en bref
- **D7 (lu).** `Common/EmpConstants.cs:13`, `Net/Steam/SteamNetManager/SteamNetManager.cs:70-105` : 8 messages lus
  par image. Du retard (positions vieilles de plusieurs secondes après un gel), pas un écart durable. Corrigé `dfa476d`.
- **D8 (lu).** Même fonction, ligne 97 : la lecture d'un message n'est dans aucun `catch` ; une exception laisse le
  reste du lot ni lu ni rendu à Steam. Preuve : une exception dans `Player.log` du jeu (pas dans le journal du mod).
  Corrigé `9a25491` (ligne `Message dropped`). Dans le même fichier : pair inconnu = message ignoré sans ligne
  (81-84) ; type inconnu = `Failed to parse type hash {TypeHash}` (90-94).
- **D9 (lu).** `Net/Host/ElinNetHostTravel.cs:894-900` : chaque bail commence 50 000 au-dessus du précédent, sans
  plafond. Si l'host crée plus de 50 000 cartes pendant qu'un bail reste ouvert (longue soirée, l'un reste des heures
  en ville, l'host enchaîne les étages), ses numéros entrent dans la plage prêtée. Preuve : comparer
  `Leased zone {ZoneFullName} to {@Peer}, uid range from {UidRangeStart}, map {HasMap}` au numéro des objets récents ;
  `Uid {Uid} taken by client local card, evicting for host {CardType}` ; `Card uid conflict: uid {Uid} held by
  local …` **ailleurs** que juste après `Starting initial scene init` (là, le banc en écrit déjà 51 par jour).
- **D10 (lu, trouvé correct).** Invité absent : seuls discussion, quêtes, date, météo passent, dans les deux sens
  (`Net/Host/ElinNetHostUpdate.cs:112-118`, `ElinNetClientTravel.cs:936-945, 975-989`) ; les changements d'une
  carte ne polluent pas un joueur d'une autre carte. Deux invités sur une carte tenue par l'un : même code que
  l'host (`Net/Host/ElinNetHostZoneSession.cs`), donc mêmes défauts D1, D4, D5 entre eux. `_pauseUpdate` côté invité
  n'est mis à vrai nulle part. Un invité « pas installé » voit ses actions sur les cartes ignorées par l'host
  (`ElinNetHostUpdate.cs:112`) : sans suite durable, son jeu repart d'une copie (supposé).

## 3. Ordre proposé
1. Jouer et publier ce qui est déjà écrit : `9a25491` (D3, D8) et `dfa476d` (D7). Sans D3, D1 ne peut pas se corriger.
2. L'outil du §4, **en mode « avertir seulement »** : il dira dès la prochaine soirée laquelle des causes est la vraie.
3. D1 (15 lignes), puis D4 (15 lignes) : les deux trous au chargement.
4. D5 (40 lignes) : la réparation à la demande. Puis D2 (20 lignes), qui s'appuie sur l'outil.
5. D6 et D9 : seulement si les journaux les montrent. Un lot = un test = un commit ; D1 et D2 : trois fenêtres.

## 4. Outil de diagnostic à livrer vite : somme de contrôle par carte
- **Existe déjà.** Un message de l'host à tous, 1 fois toutes les 2 secondes (`SessionPlayersSnapshot`,
  `Net/Host/ElinNetHostUpdate.cs:253, 265`) ; le rechargement de la carte sans se déconnecter
  (`RequestZoneState(MapDataRequest.CurrentRemoteZone)`, `Net/Client/ElinNetClientZone.cs:21-28`, puis
  « Reloading active zone from received snapshot », ligne 182) ; la reconnexion complète (`ReconnectSelf`) ; `state`
  du pont de test (`Emp/EmpDebugListener.cs`) ; le compteur `Desyncs` de la fenêtre de débogage, qui ne compte que
  les exceptions (`Net/Runtime/ElinNetRuntime.cs:45-51`).
- **À ajouter (~60 lignes, sans l'écrire ici).** (1) Un calcul commun : nombre de personnages vivants de la carte,
  nombre d'objets au sol, un mélange (ou exclusif) de `uid`, case et quantité de chaque objet au sol, et pour chaque
  joueur le nombre d'objets et la quantité totale de son sac. (2) Ces 4 ou 5 nombres dans `SessionPlayersSnapshot`,
  avec le numéro de la carte. (3) Chez l'invité : comparer ; si la différence tient **3 fois de suite** (6 secondes,
  pour laisser arriver les messages en route) et qu'aucun chargement n'est en cours, écrire un avertissement, par
  exemple `Map checksum differs on {ZoneFullName}: charas {Local}/{Host}, things {Local}/{Host}, bags {Local}/{Host}`.
  (4) Une case à cocher côté host « resynchroniser tout seul » : au plus une fois par minute, redemander la carte
  (écart de carte) ou se reconnecter (écart de sac). D'abord livrer (1) à (3) seulement.
- **Attention.** Le rechargement automatique passe par D4 : tant que D4 n'est pas corrigé, il peut créer un nouveau
  trou. Et les numéros « en attente » d'un invité (objets pas encore confirmés par l'host) doivent être sautés.
- **Test (2 fenêtres).** Par `eval` chez l'invité, retirer un objet du sol : la ligne paraît en moins de 8 secondes ;
  case cochée : l'objet est revenu en moins de 70 secondes. Sans rien toucher, 5 minutes de jeu du bot : zéro ligne.

## 5. Cinq questions pour le joueur
1. Qu'est-ce qui était différent, au juste : des monstres ou des objets que l'un voit et pas l'autre, des joueurs
   pas au même endroit, des sacs ou des armes différents, ou l'heure ?
2. Ça commençait quand : juste après que quelqu'un arrive ou change de carte (ou que l'host quitte une carte où
   d'autres restent), ou en plein milieu, sans que personne ne change de carte ?
3. Était-ce toujours le même joueur qui voyait « faux » (le dernier arrivé, le PC le plus lent), ou tout le monde ?
4. Est-ce que ça se réparait quand ce joueur changeait de carte ou se reconnectait ? (Essayer `emp.reconnect_self`.)
5. Peux-tu envoyer les journaux du même soir **de l'host et d'au moins un invité**, le fichier `Player.log` du jeu,
   et la taille du dossier de sauvegarde de l'host (surtout `game.txt` et la carte de la base) ?

## 6. Lignes à chercher dans les journaux
Fichier : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs\Session_AAAAMMJJ.log`. Chercher le texte exact.
À vérifier d'abord : que la version publiée écrit bien le niveau Debug (non vérifié ; le banc, compilé en Debug, l'écrit).

| Ligne (`@mt`) | Chez qui | Ce qu'elle dit |
|---|---|---|
| `Refusing stale {DeltaType} from peer {PeerIndex}, uid {Uid} is gone here` | host | un invité a touché un objet que l'host n'a pas : écart prouvé (D5) |
| `Dropping {DeltaType} from peer {PeerIndex}, owner {OwnerUid} or thing {Uid} unresolved` | host | idem, équipement (D1) |
| `Dropping {DeltaType} from peer {PeerIndex}, uid {Uid} cannot be resolved here` (et `parent uid`) | host | idem, sac |
| `Refusing {DeltaType} from peer {PeerIndex}, uid {Uid} is held by player {HolderUid}` | host | deux joueurs croient tenir le même objet |
| `ThingRequest dangling of {Uid} was never dango dongo'd, returning to {ParentUid}` | invité | une demande d'objet restée sans réponse |
| `Falling behind with {DroppedTicks} dropped ticks` | invité | **loin** d'un changement de carte : envoi perdu (D3). Près : normal |
| `Sending save probe to player {@Peer} for replication` | host | début d'un trou D1 pour ce joueur ; compter par heure |
| `Received save data from host` puis `Received zone state` | invité | l'écart de temps entre les deux = largeur du trou D1 |
| `Dispatching zone to player {@Peer}` sans `Player {@Peer} has finished zone replication` | host | carte jamais arrivée (D3) |
| `Requesting zone state {@Zone} from host` sans `Received zone state` | invité | idem |
| `Host leaves {ZoneFullName}, {@Peer} keeps it, uid range from {UidRangeStart}` | host | passation (D2) : noter l'heure |
| `Took over zone {ZoneFullName}, uid range from {UidRangeStart}, from the host {WithHost}` | invité | idem |
| `Dropping stale move on chara {Uid} (expected {ExpectedZoneUid}, got {GotZoneUid})` | invité | messages pour une carte pas encore chargée (D4) |
| `Dropping delta {DeltaType} after {DeferCount} failed defer` | les deux | un message a attendu 7200 fois puis a été jeté |
| `Exception at processing delta {DeltaType}` | les deux | un changement non appliqué (niveau Debug) |
| `Exception at handling T1 message {CallbackName}, T1 = {MessageType}` (et `T2`) | les deux | un message entier non traité |
| `Card uid conflict: uid {Uid} held by local {LocalCardId} ({LocalCardNum}), refusing incoming {CardId}` | invité | deux objets, un numéro (hors arrivée) (D9) |
| `Uid {Uid} taken by client local card, evicting for host {CardType}` | invité | idem |
| `Reconcile force move chara {Uid} from {@FromPos} to {@Pos}` | invité | position corrigée de force : beaucoup = retard (D7) |
| `Removing stale chara {Uid} at {@FromPos}, actual pos {@Pos}` / `Removing duplicate map chara {Uid} at {@Pos}` | host | personnage de joueur en double sur la carte |
| `Dropping {MessageType} from host at handshake stage {HandshakeStage}` | invité | normal à l'arrivée (1132 fois au banc) : ne prouve rien |

Dans `Player.log` (journal du jeu, pas du mod) : toute exception citant `SteamNetManager.Poll` ou `Deserialize` (D8).
Compter par heure : arrivées (D1), passations (D2), `Refusing stale` (D5). Si les troisièmes suivent les deux premières, c'est D1 et D2.
