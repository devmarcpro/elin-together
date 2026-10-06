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
- Seconde carte pendant une retenue : ce qui a été retenu sur la première carte est rejoué sur la seconde (cartes
  inconnues = sans effet, lu pour les types courants ; pas pour tous).
- D5 : les autres invités gardent leur fantôme jusqu'à ce qu'ils le touchent (alors ils sont corrigés à leur tour).
  Un objet « en attente » (numéro provisoire) que l'host ne sait pas relier est toujours retiré chez son auteur.
- D5, recherche réelle : pas dans les coffres posés au sol si l'invité ne nomme pas le contenant.
- Le temps du jeu retenu pendant D4 : rattrapé d'un coup au relâchement (plafonné par `MaxGameDeltaBuffer`, lu).
