# Corrections D1, D4, D5 de `PLAN_desync.md` (2026-10-06)

Écrites et compilées à part (`ReleaseNightly`, 0 erreur). **Rien n'a tourné en jeu.** Test : `dev/_tools/desync_suite.py`
(jamais lancé), comparaison réutilisable : `dev/_tools/world_diff.py`. Chemins relatifs à `ElinTogether/`.

## D1. Trou entre la copie du monde et la copie de la carte

- **Fait vérifié dans le code actuel**, avec une nuance : depuis la 0.26.510 la retenue existait déjà, mais seulement
  à partir de la réception de la carte. Entre « monde reçu » et « carte reçue » rien n'était retenu : jeté.
- **Choix : la carte part dans la même image que le monde** (`Net/Host/ElinNetHostPlayerManager.cs`, `SendSaveProbe`),
  et l'invité retient dès le monde reçu (`Net/Client/ElinNetClientPlayer.cs`, `OnSaveDataProbe` :
  `Delta.HoldForIncomingMap(true)`), ne redemande plus la carte.
- **Pourquoi pas « retenir et rejouer » seul** : la carte était photographiée plus tard que le monde. Rejouer ce qui
  est arrivé entre les deux aurait appliqué deux fois tout ce qui touche la carte (déjà dans sa copie). Avec une seule
  photo pour les deux, tout ce qui suit est appliqué une fois, dans l'ordre (les envois fiables gardent leur ordre par
  joueur, y compris les gros messages en morceaux : `SteamNetPeer.Send`, lu).
- Avant les deux copies, l'host envoie à tous ce qu'il avait en attente (`Delta.RefreshBuffer(); WorldStateDeltaUpdate()`,
  comme `ElinNetHostTravel.cs:857-859`) : sinon ces messages, déjà dans les copies, seraient rejoués par l'arrivant.
- Une seconde carte reçue pendant la retenue (l'host a changé de carte entre-temps) **ne vide plus** ce qui est retenu :
  les personnages des joueurs ne sont dans aucune carte.
- `_awaitingActivation = 0` à la réception d'un monde : une carte reçue pour le jeu d'avant ne fait plus refuser
  celle du nouveau monde comme « reçue deux fois » (l'invité ne la redemandant plus, il serait resté bloqué).
- Journal : host, Information `World and map {ZoneFullName} sent together to player {@Peer}` ; invité, Information
  `Replaying {Held} held deltas ({Acts} besides game time) after {Seconds:F1}s of loading, hold started by {HoldStart}, {Lost} lost over the limit: {Types}`
  avec `HoldStart` = `world copy`. `Acts` > 0 = des gestes des autres joueurs sont arrivés pendant le chargement
  (ceux que la 0.26.510 jetait jusqu'à la carte reçue).

## D4. Carte reçue pendant que le jeu tourne

- **Fait vérifié** (`HoldForIncomingMap` sortait tout de suite si le jeu tournait).
- `Net/Base/ElinDeltaManager.cs` : la retenue vaut aussi quand le jeu tourne, jusqu'à `MapPlaced()` appelé à la fin du
  chargement dans `OnZoneActivateResponse` (`Net/Client/ElinNetClientZone.cs`). Ce qui était arrivé avant la carte est
  appliqué comme avant (pas vidé). Tout ce qui demande un jeu lancé est retenu, temps du jeu compris : le jeu de
  l'invité est figé le temps d'un aller-retour.
- Garde-fou : 10 s sans placement (rafraîchies à chaque carte reçue) : la retenue est lâchée et rejouée sur la carte en
  place, Warning `No placement on the incoming map after {Seconds:F1}s, giving up the hold`. Plafond inchangé :
  20 000 messages, le surplus est compté (`{Lost}`), plus jeté sans bruit.
- `HasPendingIn` compte ce qui est retenu : rejoué même si plus rien n'arrive (host en pause).
- Journal : la même ligne `Replaying …`, `HoldStart` = `map copy, game running`.

## D5. Objet inconnu de l'host : « quantité 0 » à tous

- **Fait vérifié** (`Models/Pending/TaskCache.cs`, `CancelClientAct`).
- Deux changements, dans ce seul fichier :
  1. « Pas dans le registre des cartes » n'est pas « disparu » : l'host cherche la carte pour de vrai (dans le
     contenant que l'invité nomme, sinon au sol de la carte, sinon parmi les personnages de la carte). Trouvée : elle
     est inscrite au registre et le message de l'invité est rejoué à l'image suivante : il obtient ce qu'un joueur
     seul obtiendrait. Aucun doublon possible : c'est l'objet de l'host.
  2. Vraiment absente : « quantité 0 » n'est envoyé **qu'à l'invité qui s'est trompé** (`SendDeltaTo`), plus à tous.
- Pas d'adoption de l'objet de l'invité : un objet que l'host n'a pas est presque toujours un fantôme (retrait
  manqué, l'objet est déjà dans le sac de quelqu'un) : l'adopter ferait un doublon. Et il faudrait un nouveau message.
- Journal (Warning, host) :
  `Uid {Uid} of {DeltaType} from peer {PeerIndex} is here but was not in the card cache, adopted and replayed ({Adopted} adopted, {Refused} refused so far)`
  et `Refusing stale {DeltaType} from peer {PeerIndex}, uid {Uid} is gone here: only that player is told to drop it ({Refused} refused, {Adopted} adopted so far)`.
  **La seconde remplace** `Refusing stale {DeltaType} from peer {PeerIndex}, uid {Uid} is gone here` (tableau du §6
  de `PLAN_desync.md` : chercher le début de la ligne).

## D2. Passage de main : la copie de l'host fait foi

Écrit et compilé (`ReleaseNightly`, 0 erreur), **rien n'a tourné en jeu**. Test : `desync_suite.py --only d2` (trois fenêtres).

- **Fait vérifié.** L'host qui part n'envoyait au repreneur qu'un bail `Handoff` sans carte (`Map` nul) : l'état de la
  zone (drapeaux, dates) et les plages de numéros. Le repreneur gardait sa copie (`TakeOverZone`, qui n'applique même
  pas l'état reçu). Les autres restés (`Guest` + `Handoff`) rechargent la copie **du repreneur** par sa session de zone
  (monde + carte, `SendSaveProbe` du repreneur). L'host, en revenant, charge la copie du repreneur
  (`ZoneLeaseRelease.Map` -> `ApplyLeasedZone`). Raison du choix d'origine : pas de rechargement ni de déplacement pour
  celui qui garde la carte, et rien de ce qu'il vient de faire n'est perdu.
- **Choix : (b), en un seul message.** L'host joint au bail sa carte (`Map`, le champ existait) **et** ses nombres
  (`MapSums`, clé 9). Le repreneur compare avec les siens, après avoir appliqué les derniers messages de l'host :
  égaux, il ne fait rien (comme avant) ; différents, il recharge la carte de l'host sous ses pieds, par le même chemin
  que tout rechargement de la carte active, et reste sur sa case.
- **Pourquoi pas (a)** : rechargement visible à chaque départ de l'host. **Pourquoi pas (b) avec aller-retour** (l'host
  n'envoie la carte que si on la lui redemande) : entre-temps l'host est parti et les autres restés chargent déjà la
  copie du repreneur ; il faudrait un message de plus, une attente, et bloquer les autres. Prix du choix : la carte
  voyage à chaque départ de l'host où quelqu'un reste (comme pour tout bail), et l'host l'enregistre une fois de plus.
- **Les nombres ne sont pas `NetDesync.Collect()`** : au passage de main les joueurs présents ne sont pas les mêmes
  des deux côtés (l'host a déjà retiré ceux qui restent). `ZoneLeaseState.Sums` compte ce qu'une copie de carte
  contient vraiment : objets au sol (numéro, case, quantité), **contenu des coffres et autres contenants au sol**
  (numéro, contenant, quantité), personnages enregistrés avec la carte (numéro). Si l'on préfère un seul calcul :
  ajouter à `NetDesync` une variante `Collect(Func<Chara, bool> skip)` et y compter le contenu des contenants.
- **Journal.** Host, Information :
  `Host leaves {ZoneFullName}, {@Peer} keeps it, uid range from {UidRangeStart}, host copy sent along {HasMap}: {Sums}`
  (même début qu'avant). Repreneur, Information :
  `Taking over {ZoneFullName} from the host: our copy is the same, kept ({Sums})` ; ou Warning :
  `Taking over {ZoneFullName} from the host: our copy differs, replaced by the host's (here {Local} | host {Host})`.
  Les nombres : `things N:mélange, held N:mélange, charas N:mélange`. L'host ne sait pas lequel des deux a eu lieu
  (pas de message retour) : lire le journal du repreneur.
- **Non couvert par les nombres** : le terrain (murs, sols, cultures), ce que portent les personnages de la carte
  (marchands compris), leur case et leur vie, les personnages « du monde » (joueurs, compagnons, habitants uniques,
  aventuriers : ils ne sont pas dans une copie de carte), l'état de la zone. Un écart qui ne touche que cela passe
  toujours tel quel.
- **Non corrigé, même défaut** : carte du monde (chacun la sienne, voulu) ; carte de quête laissée à celui qui a pris
  la quête (pas de carte jointe : rechargement non lu sur une carte de quête) ; **un invité qui tient une carte et la
  passe à un autre invité** (`HandOverZone`) : l'héritier garde sa copie alors que l'host vient de recevoir celle du
  partant. Correction possible, même outil : nombres du partant dans `ZoneLeaseRelease`, carte et nombres dans le bail
  de `HandOverZone`, sauf si le partant est tombé (alors la copie de l'invité est la plus récente).
- **Déjà bon dans l'autre sens** : un invité qui rend sa carte à l'host (rappel ou retour) envoie sa carte entière,
  l'host la charge ; ses invités sont rappelés et rechargent la copie de l'host, qui est celle-là.
- **Pas sûr.**
  - Un geste du repreneur dans le dernier aller-retour, que l'host n'a pas vu : si les copies diffèrent, la carte de
    l'host le défait sur la carte mais pas dans le sac (objet posé perdu, objet ramassé en double). Fenêtre : un
    aller-retour, et seulement quand il y a rechargement. Vraie correction : attendre l'accusé du repreneur comme pour
    un départ normal.
  - Si un contenu de coffre diffère « normalement » entre host et invité (non lu pour tous les coffres, ex. coffres de
    marchand), le repreneur rechargera à chaque départ de l'host : le journal le dira (`held` différent à chaque fois).
  - Rechargement avec une fenêtre ouverte ou en plein combat chez le repreneur : même chemin que quand l'host change
    de carte, pas vu tourner ici.
  - Une très grosse carte (base) alourdit le bail : envoi en morceaux de `9a25491` requis.
  - `Zone.Deactivate` met dans le sac les artefacts divins au sol : retirés du sac après coup dans `AdoptHostCopy`
    (ils reviennent avec la carte de l'host). Le rechargement existant (`ElinNetClientZone.cs:187`, outil de
    resynchronisation) a le même piège et ne le traite pas : à voir à part.

## D2 bis. D'un invité à un autre invité (2026-10-06, nuit, seconde passe)

Écrit et compilé (`ReleaseNightly`, 0 erreur), **rien n'a tourné en jeu**. Test : `desync_suite.py --only d2g` (trois
fenêtres). Ferme le point « non corrigé » de D2.

- **Fait vérifié.** Un invité qui tient une carte et s'en va la rend à l'host avec sa carte entière
  (`CreateLeaseRelease`, `ApplyLeasedZone`), puis l'host donne le bail à un de ses visiteurs (`HandOverZone`) **sans
  carte** : l'héritier gardait sa copie, que les autres visiteurs rechargeaient ensuite, et qui remplaçait celle de
  l'host à son prochain point de passage.
- **Fait.** `ZoneLeaseRelease.MapSums` (clé 13) : les nombres de la carte du partant, calculés avec la carte, pas pour
  un point de passage. `HandOverZone` joint au bail de l'héritier la carte du partant et ces nombres (les octets reçus,
  pas recompressés), sous la case `AutoResync` comme pour le départ de l'host. L'héritier compare
  (`TakeOverZone` -> `AdoptHostCopy`) : égaux, rien ne change ; différents, il charge la carte du partant sous ses
  pieds et reste sur sa case.
- **Pas quand le partant est tombé** (déconnexion) : l'host n'a alors qu'un vieux point de passage, la copie de
  l'héritier est la plus récente : pas de carte jointe, comme avant. Ni quand l'host est déjà sur cette carte.
- **Ordre des numéros** : la plage de numéros du bail est prise **avant** le chargement (l'héritier charge cette carte
  en jouant seul, plus en client : ce que le chargement créerait doit prendre ses numéros dans sa plage).
- **Objet ramassé dans le dernier aller-retour** (valait aussi pour D2) : après le chargement, ce que l'héritier
  porte et qui se trouve aussi au sol de la carte reçue est retiré du sol : il le garde dans son sac, comme un joueur
  seul, au lieu de l'avoir deux fois. L'inverse reste : un objet posé dans ce dernier aller-retour est perdu.
- **Journal.** Host, Information :
  `Zone {ZoneFullName} handed over to {@Peer}, uid range from {UidRangeStart}, owner copy sent along {HasMap}: {Sums}`
  (même début qu'avant). Héritier : les lignes de D2 **ont changé de texte** pour servir aux deux cas :
  `Taking over {ZoneFullName} from {From}: our copy is the same, kept ({Sums})` et
  `Taking over {ZoneFullName} from {From}: our copy differs, replaced by theirs (here {Local} | there {Host})`,
  `From` = `the host` ou `its owner`. Nouveau, Warning :
  `Taking over {ZoneFullName}: {Count} thing(s) of that copy are in our bag already, taken off the floor: {Uids}`.
- **Pas sûr.**
  - L'héritier charge la carte hors de toute connexion (jeu « seul »), par le chemin d'une carte louée
    (`Zone.Deactivate`, `UnloadMap`, `player.MoveZone`) mais sur la carte où il se tient : pas vu tourner.
  - Entre un invité et celui qui tient la carte, la case d'un objet lancé ou éparpillé peut différer (dés de chaque
    jeu) : les nombres du passage de main comptent la case, donc rechargement à chaque passage dans ce cas. Voulu
    (la copie du partant est celle de tout le monde), mais visible : le journal le dira.
  - Les autres visiteurs rechargent la copie de l'héritier pendant qu'il recharge peut-être la sienne : même ordre
    que pour D2 (bail de l'héritier envoyé avant les autres), pas vu tourner à quatre.
  - Carte de quête : toujours sans carte jointe (`Map` nul pour une carte de quête).

## Après relecture (2026-10-06, nuit)

Compilé (`ReleaseNightly`, 0 erreur), **rien n'a tourné en jeu**. Ce qui suit remplace ce que D1 et D4 disent plus haut
quand les deux se contredisent.

- **D4, messages d'avant la carte appliqués deux fois** (`Net/Base/ElinDeltaManager.cs`). Ce qui attendait déjà quand
  la carte arrive (même image) était retenu puis rejoué sur la nouvelle carte, qui le contient. Maintenant : mis de
  côté (`_beforeHold`) et appliqué d'abord, sans retenue, sur la carte qu'on quitte, comme avant D4. Seul ce qui
  arrive après la carte est retenu.
- **Seconde carte juste après le placement** (`HoldForIncomingMap`). Le cas « retenue ouverte, jeu lancé, pas encore
  rejoué » vidait ce qui était retenu depuis la copie du monde. Maintenant : une carte reçue pendant une retenue ne
  vide jamais rien ; si le jeu tourne, la retenue dure jusqu'au placement sur cette carte (ou 10 s).
- **Carte qui n'arrive jamais après le monde** (`Net/Client/ElinNetClientPlayer.cs`, `ElinNetClientZone.cs`,
  `AskMissingMap`). 15 s après la copie du monde sans aucune carte reçue : l'invité la redemande **une fois** par le
  chemin d'avant (`RequestZoneState`). Journal invité, Warning : `No map {Seconds:F0}s after the world copy, asking the
  host for it once`. Si la première carte arrive juste après la demande : la seconde est refusée comme « reçue deux
  fois » (même carte, moins de 10 s, pas encore placé), ou chargée par-dessus (cas du point précédent).
- **D5, `SendDeltaTo` hors file** : laissé. Il n'existe pas d'envoi « à un seul joueur » qui passe par la file ordonnée
  (la file de sortie part à tous, `Broadcast`). Le « quantité 0 » peut donc doubler un `CardGen` encore en file pour ce
  joueur (au plus une image d'envoi, 20 ms).

Pas sûr, pas corrigé :
- **L'host ne vide pas sa file avant de copier la carte demandée** (`Net/Host/ElinNetHostZone.cs`, `OnMapDataRequest`,
  fichier non touché) : ce qu'il a déjà fait mais pas encore envoyé (au plus 20 ms) part après la carte, est retenu
  par l'invité et rejoué sur une carte qui le contient. Correction : `Delta.RefreshBuffer(); WorldStateDeltaUpdate();`
  avant `PropagateZoneChangeState`, comme dans `SendSaveProbe`.
- Carte redemandée après 15 s : ce qui a été retenu entre la copie du monde et cette carte est rejoué sur une carte
  qui le contient déjà (pour ce qui touche la carte). Prix du filet ; sans lui l'invité attendait sans fin.
- Si l'host n'a aucune carte active au moment de la demande tardive, il coupe l'invité (`InvalidZone`, code existant).
- Placement qui arrive plus de 10 s après la carte, jeu lancé : la retenue est lâchée avant, ce qui a été rejoué
  l'est sur l'ancienne carte et manque sur la nouvelle (l'outil de somme de contrôle le rattrape).
- Un message d'avant la carte qui se remet lui-même en attente (carte pas encore connue : `ZoneAddCardDelta`,
  `CharaMoveDelta`, `CharaMakeAllyDelta`) est retenu à son tour et rejoué après le placement, comme avant D4.
- Carte reçue, réponse envoyée, mais l'host ne dit jamais où se placer, jeu pas encore lancé : toujours pas de filet
  (comme avant). Le prochain changement de carte de l'host débloque.

## Hors plan, demandé en cours de route

`Net/Host/ElinNetHostZone.cs` (`OnZoneDataReceivedResponse`) : un joueur déjà debout sur la case où on le remet y
reste (sa propre case était refusée comme occupée, il sautait d'une case à chaque rechargement sur place).

## Pas sûr

- Rien n'a été joué. Le plus fragile : l'invité traite maintenant la carte dans la même image que le monde (avant :
  un aller-retour plus tard). Lu : rien dans `OnZoneDataResponse` n'attend une image ; pas vu tourner.
- Si la carte envoyée avec le monde n'arrive jamais, l'invité reste sur l'écran d'attente (avant : pareil si sa
  demande ou la réponse se perdait). Host sans carte active à cet instant : Warning
  `No active map to send with the world to player {@Peer}`, la carte suivante de l'host le débloque.
- Les messages « différés » de l'host (`DeferRemote`) partent encore après les copies : rejoués une fois de trop
  chez l'arrivant. Peu nombreux (non recensés).

## Après relecture (seconde passe, 2026-10-06, nuit) : passage d'une carte

Compilé (`ReleaseNightly`, 0 erreur), **jamais lancé**. Remplace ce que D2 et D2 bis disent plus haut quand ils se
contredisent.

- **La case des objets au sol n'est plus dans `ZoneLeaseState.Sums`** (numéro + quantité ; le contenu des coffres
  reste compté : numéro, contenant, quantité). Les lignes plus haut qui disent « objets au sol (numéro, case,
  quantité) » et « les nombres du passage de main comptent la case, donc rechargement à chaque passage » sont
  fausses depuis cette passe. Un objet lancé ou éparpillé qui est à une autre case chez le repreneur n'est plus vu :
  il est remis à sa case au prochain rechargement, quel qu'en soit le motif.
- **`AdoptHostCopy` (`ElinNetClientTravel.cs`) ne laisse plus le repreneur sans carte** : `Deactivate`, retrait des
  artefacts, `UnloadMap` et `WriteMap` sont dans un `try`. Échec : Warning
  `Taking over {ZoneFullName} from {From}: their copy could not be loaded, returning to the host` (avec l'exception),
  puis `SendRejoin()` ; l'appelant (`TakeOverZone`) s'arrête là (`_rejoining`). Un visiteur (`Session.IsAway`) repasse
  invité avant de partir : sinon son bail rendrait la carte à moitié détruite comme celle de la zone.
- **Fenêtres du joueur** : `ui.RemoveLayers()` juste avant le rechargement. Le chargement ordinaire
  (`OnZoneActivateResponse`) n'a aucun code propre pour cela : c'est `Scene.Init`, appelé par `player.MoveZone`, qui
  retire les fenêtres, et après le déchargement. Ici c'est fait avant. Non fait : attendre la fin d'un combat ou d'un
  menu (le rechargement coupe ce que le joueur faisait ; limite connue).
- **Limites connues, non corrigées**, de « un objet porté et aussi au sol de la carte reçue est retiré du sol »
  (comparaison par numéro) : (1) un ramassage fusionné dans une pile du sac (l'objet du sol n'existe plus chez nous,
  l'autre exemplaire reste au sol : en double) ; (2) un ramassage partiel d'une pile (idem) ; (3) un objet pris dans un
  coffre de la carte reçue (il est de retour dans le coffre). L'inverse (objet posé dans le dernier aller-retour,
  perdu) reste comme avant.
- Pas sûr : le chemin d'échec n'a jamais tourné ; l'état exact de la session après `SendRejoin()` en plein
  `TakeOverZone` (côté host : bail abandonné « gone meanwhile ») est lu, pas vu.
- Seconde carte pendant une retenue : ce qui a été retenu sur la première carte est rejoué sur la seconde (cartes
  inconnues = sans effet, lu pour les types courants ; pas pour tous).
- D5 : les autres invités gardent leur fantôme jusqu'à ce qu'ils le touchent (alors ils sont corrigés à leur tour).
  Un objet « en attente » (numéro provisoire) que l'host ne sait pas relier est toujours retiré chez son auteur.
- D5, recherche réelle : pas dans les coffres posés au sol si l'invité ne nomme pas le contenant.
- Le temps du jeu retenu pendant D4 : rattrapé d'un coup au relâchement (plafonné par `MaxGameDeltaBuffer`, lu).
