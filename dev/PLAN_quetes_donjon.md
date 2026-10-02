# Plan : quêtes à donjon propre pour tous les joueurs

Plan établi par un agent (lecture du code seule, rien n'a été exécuté) dans la nuit du 2026-10-01. Chemins du mod
sous `ElinTogether\ElinTogether\`, du jeu sous `_decomp\Elin\`. À cocher au fur et à mesure.

**Principe.** Le joueur qui prend la quête crée lui-même la zone d'instance et la loue comme un étage de donjon.
L'host sait seulement « cette zone louée est une instance » et la supprime quand le bail finit. Le jeu du preneur
applique le résultat une fois arrivé dans la zone de retour, par les chemins existants des quêtes personnelles
(terminer / échouer). Quand le détenteur part, les invités sont renvoyés dans la zone de retour (pas de passation).

Tout est conditionné à `PersonalQuests.Enabled && Rules.AllowIndependentTravel` ; sinon les blocages actuels restent.

## Changements, dans l'ordre

1. **Débloquer.** `BlockClientQuestPatch.cs:15,46`, `QuestStartEvent.cs:28`, `QuestAcceptDelta.cs:32`. Les garde-fous
   testent `IsClient`, faux en voyage seul : un client en voyage peut déjà prendre ces quêtes. Option décochée :
   tester `Transport is ElinNetClient`.
2. **Délai.** `ElinNetHostPersonalQuests.cs` (`AcceptPersonal`) : `deadline = 0` pour `UseInstanceZone` avant de
   sérialiser. Sinon le `QuestStartDelta` de l'host écrase le 0 posé par `CreateInstanceZone` et
   `PersonalQuests.Tick` fait expirer la quête en pleine instance.
3. **Plan de zone.** Ajouter `LZ4Bytes? Instance` à `LeaseZoneBlueprint` (`ZoneLeaseRequest.cs:39`). Dans
   `CreateClientZone` (`ElinNetHostTravel.cs`), quand il est présent :
   - pas de réutilisation « existe déjà » (sinon deux joueurs dans la même ville partagent une zone) ;
   - poser `zone.instance` ;
   - pas de `elomap.SetZone` (écrase la case de la ville sur la carte du monde) ;
   - pas de `SpatialGenDelta` (`SpatialGenEvent.cs:53` ; `SpatialGenDelta.cs:72` a le même défaut côté clients).
   Même garde `elomap` dans `AdoptHostUid` (`ElinNetClientTravel.cs`).
4. **Durée de vie côté host.**
   - Postfix `Zone.CanDestroy` → faux tant que la zone est louée (avec `instance`, la prochaine sauvegarde de l'host
     la supprimerait en plein bail : `Zone.cs:1956`, `2023`).
   - `ApplyLeasedZone` : sortir tout de suite pour une instance. Client `CreateLeaseRelease` : `Map = null`.
   - `OnZoneLeaseRelease` et `ReleaseLeaseOnDisconnect` : `zone.Destroy()` avant `HandOverZone` (qui prend alors
     sa branche « zone introuvable, rappeler les invités »).
5. **Résultat.** `PersonalQuests.LeaveInstance()`, appelé dans `TryTravel` quand le joueur local tient la quête de
   l'instance : `zone.events.OnLeaveZone()` une fois ; retirer le `ZoneEventQuest` ; noter
   `(uidQuest, uidClient, fail = status != Success, lastWave, bonus)` ; `instance.uidQuest = 0` (l'événement
   « avant d'entrer » du jeu devient sans effet, `ZonePreEnterOnCompleteQuestInstance.cs:14`).
   `PersonalQuests.Tick` l'applique une fois installé dans une zone normale : `quest.Complete()` ou `Fail()`, plus
   le dialogue du donneur s'il est là. Ajouter `LastWave`/`Bonus` à `QuestCompleteDelta`
   (`QuestDefenseGame.cs:24,47` lit des statiques fausses chez l'host). Bail refusé avec un résultat en attente :
   `SendRejoin`.
6. **Sécurité des invités.**
   - Généraliser `ZoneEventHarvestPatch` à tous les `ZoneEventQuest.OnVisit`.
   - Prefix `ZoneEventQuest.OnTickRound` avec `IsHost` (`GameUpdater.cs:533` fait tourner les événements chez les clients).
   - Postfix du getter `ZoneEventQuest.quest` : copie « visiteur », rangée dans `PersonalQuests.Restore` avant le `RemoveAll`.
   - Prefix `ZoneInstanceRandomQuest.OnLeaveZone` : rien si la quête n'est pas la nôtre.
7. **Les invités partent avec le détenteur.** `OnZoneLeaseRecall` (`ElinNetClientTravel.cs`) : si
   `_zone.IsInstance`, effacer `_handoffDeadline` et `TryTravel(zoneDeRetour)` au lieu de `SendRejoin`.
8. **Phase 2 : entrée des invités.** Une instance n'a pas de porte, personne ne peut y entrer aujourd'hui. L'host
   diffuse « instance ouverte » (zone uid/id/x/y + la quête), aussi aux joueurs en voyage. Le donneur garde l'offre
   pour les autres ; l'accepter fait renvoyer par `CreateInstanceZone` un bouchon avec ce numéro, et `RequestLease`
   prend le chemin existant `GrantGuestLease`.

## Comment ça marche en solo (repères)

- Accepter : `DramaCustomSequence.cs:568–571` démarre la quête ; 599–605 `CreateInstanceZone(c)` puis
  `pc.MoveZone(z, Center)`.
- Créer : `QuestInstance.cs:25–37` (événement avec `uidQuest`, `ZoneInstanceRandomQuest` avec `uidClient` et
  `uidQuest`, `deadline = 0`). `SpatialGen.cs:39–48` : enfant de la Région aux x/y de la zone du haut, nouveau
  numéro, `uidZone`/`x`/`z` de la zone et de la position du joueur, `dateExpire` +1 jour. Ne touche pas `elomap`.
- Objectif et chrono : `ZoneEventQuest.cs:64–74`. Récolte et Musique : 180 minutes ; Subjuguer réussit quand
  `enemies` est vide (`ZoneEventSubdue.cs:36`).
- Sortir : `Chara.cs:3627–3640` : `events.OnLeaveZone()`, destination forcée à `instance.uidZone` en `x`/`z`, puis
  `instance.OnLeaveZone()` met en file l'événement « avant d'entrer » (`ZoneInstanceRandomQuest.cs:23`), exécuté
  dans `Zone.Activate` (`Zone.cs:1021`) → Complete ou Fail.
- Détruire : `Deactivate` décharge la carte (`Zone.cs:1843`) ; zone détruite à la sauvegarde suivante.
- Mort : statut Fail (`Chara.cs:5767`) ; pas de résurrection en ville (`Scene.cs:606`).

## Ce qui marche et ce qui casse si on débloque seulement

- Marche : entrer. Les invités reçoivent `instance` et `events` du monde du détenteur. Les livraisons de récolte
  tournent déjà chez le détenteur.
- Casse : le plan de zone et les envois ne portent que `_ints`, bits et sous-ensemble (pas d'`instance`, pas
  d'événements) → l'host a une zone ordinaire jamais détruite et réutilisée ; défauts `elomap` et réutilisation ;
  résultat perdu quand l'host ou un autre joueur occupe la zone de retour ; la passation donnerait la zone à un
  invité sans la quête ; les sauvegardes en route envoient une carte qui sera supprimée.

## Risques

- Résultat en attente perdu si le preneur plante entre la sortie et l'installation.
- Le vrai host ne peut pas rejoindre l'instance d'un client (à remettre à plus tard).
- De retour sur la carte de l'host, le joueur arrive à côté de l'host, pas en `instance.x/z`.

## Test (host 27551, client A 27552, tous deux à la base)

`QuestSubdue` est le plus simple (pas de chrono). L'identifiant se lit au lancement.

1. Host crée l'offre : `var c = EClass._map.charas.Find(x => !x.IsPCFaction && !x.IsPC && x.quest == null);
   var q = Quest.Create(EClass.sources.quests.rows.Find(r => r.type == "QuestSubdue").id, null, c);`
2. A accepte quand il voit l'offre : `EClass.game.quests.Start(c.quest); var z = c.quest.CreateInstanceZone(c);
   EClass.pc.MoveZone(z, ZoneTransition.EnterState.Center);`
3. Chez A : `_zone.IsInstance` ; `GetEvent<ZoneEventSubdue>().quest != null` et `max > 0` ; quête au journal avec `deadline == 0`.
4. Chez l'host : pas dans son journal ; gardée pour A ; offre disparue ; `spatials.Find(zuid).IsInstance` ;
   `world.region.elomap.GetZone(x, y)` est toujours la base ; la zone survit à `game.Save()`.
5. A nettoie et sort : tuer chaque `enemies` par `Die()`, `CheckClear()`, statut `Success`, puis
   `EClass.pc.MoveZone(EClass._zone.ParentZone)`.
6. Après le retour : les deux à la base ; quête sortie du journal de A et de ce que garde l'host ; récompense aux
   pieds de A chez l'host ; renommée de A en hausse, celle de l'host inchangée ; `spatials.Find(zuid) == null` chez
   l'host ; pas d'exception.
7. Variantes : sortir sans tuer (renommée en baisse, pas de récompense) ; option décochée (prise refusée).
