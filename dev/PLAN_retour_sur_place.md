# Retour sur place (conseil 11, tranche 1) — premier jet, 2026-10-07

Quand l'host entre sur une carte qu'un invité tient seul, l'invité ne recharge plus le monde : il garde son jeu et
son écran, et redevient client de l'host sur place. Derrière la case **décochée** `SoftRecall` (« No world reload when
the host joins a player (new) », onglet Server Setting, section joueurs). Case décochée : rien ne change.

**État : écrit, compilé (0 erreur en Release et en Debug), JAMAIS joué.** Le jeu de l'utilisateur tournait : aucun
test en jeu, aucun commit. Tout ce qui suit est à prouver au banc avant de cocher la case.

## Ce qui a été écrit, fichier par fichier

| Fichier | Contenu |
|---|---|
| `Net/NetSessionRules.cs` | règle `SoftRecall`, clé 23, faux par défaut |
| `Emp/EmpConfig.cs` | `Server.SoftRecall` (EN + CN) |
| `Components/Tabs/TabServerConfiguration.cs` | la case `soft_recall`, sous « réparer la carte » |
| `package/LangMod` | `emp_ui_sv_cfg_soft_recall`, `emp_ui_sv_desc_soft_recall` (JP, EN, CN), ajoutés par `add_texts.py` |
| `Models/ZoneLease/ZoneLeaseRecall.cs` | champ `Soft` (clé 1) |
| `Models/ZoneLease/ZoneLeaseRelease.cs` | champ `Soft` (clé 14) |
| `Models/ZoneLease/ZoneSoftRejoin.cs` | **nouveau** : `ZoneSoftRejoin` (host -> invité) et `ZoneSoftRejoinFailed` (invité -> host) |
| `Net/Host/ElinNetHostPlayerManager.cs` | `RegisterPlayer` sorti de `SendSaveProbe` (même code, partagé par les deux chemins) |
| `Net/Host/ElinNetHostSoftRejoin.cs` | **nouveau** : `CanRecallSoftly`, `CanRejoinSoftly`, `RegisterSoftRejoin`, `TakeSoftRejoins`, `CompleteSoftRejoin`, `OnZoneSoftRejoinFailed`, `FallBackToWorldCopy`, `UpdateSoftRejoins` |
| `Net/Host/ElinNetHostTravel.cs` | le rappel porte `Soft` ; `OnZoneLeaseRelease` choisit entre `RegisterSoftRejoin` et `SendSaveProbe` ; `ReplaceRemoteChara` note les renumérotations ; ménage à la déconnexion |
| `Net/Host/ElinNetHostCompanions.cs` | `ReplaceCompanions` note les renumérotations |
| `Net/Host/ElinNetHostZone.cs` | `PropagateZoneChangeState` : l'invité qui reste sur place ne reçoit pas la carte, il reçoit `ZoneSoftRejoin` |
| `Net/Host/ElinNetHost.cs`, `Net/Client/ElinNetClient.cs` | enregistrement des deux messages, `UpdateSoftRejoinWait` |
| `Net/Client/ElinNetClientSoftRejoin.cs` | **nouveau** : `CanRejoinSoftly`, `OnZoneSoftRejoin`, `ApplySoftRejoin`, `AskWorldCopy`, `FillWorldBoxes`, `AdoptHostCharas`, `ConfirmSoftPlacement`, l'attente |
| `Net/Client/ElinNetClientTravel.cs` | `OnZoneLeaseRecall` décide, `CreateLeaseRelease` marque `Soft`, `ZoneSoftRejoin` accepté par un invité absent |
| `Net/Client/ElinNetClientPlayer.cs` | une copie du monde qui arrive quand même annule l'attente |
| `Net/Client/ElinNetClientZone.cs` | le « tu es placé là » de l'host ne recharge pas la carte qu'on n'a jamais quittée |
| `Net/NetDesync.cs` | `HoldOff()` : pas de comparaison pendant la bascule (6 s, comme après un chargement de carte) |
| `Patches/PauseGame.cs` | le jeu de l'invité est en pause entre son envoi et la réponse de l'host |

## La suite des messages

1. **Host**, `CanEnterNow` : la carte est tenue par un invité -> `ZoneLeaseRecall { Soft }`. `Soft` si la règle est
   cochée, que ce n'est ni la carte du monde ni une zone de quête, et qu'aucun visiteur n'y est ni n'y va
   (`_guests`, `_pendingGuests`).
2. **Invité**, `OnZoneLeaseRecall` : si `Soft` et qu'il est debout, vivant, sur cette carte, qu'il la tient seul
   (pas de session de zone), sans voyage ni passage de main en cours -> il arme l'attente (20 s) et envoie
   `ZoneLeaseRelease { Rejoin, Soft }` : carte, personnage, compagnons, compteur, **comme aujourd'hui**. Entrées
   bloquées (`IsInTransfer`, inchangé) **et jeu en pause** (`IsAwaitingSoftRejoin`). Sinon : chemin d'aujourd'hui.
3. **Host**, `OnZoneLeaseRelease` : applique carte, personnage, compagnons, compteur comme aujourd'hui. Puis, si le
   retour peut se faire sur place (`CanRejoinSoftly` : l'host est toujours en route vers CETTE carte, l'invité s'y
   tenait, personnage vivant, rien d'autre de tenu) : `RegisterSoftRejoin` = `RegisterPlayer` (groupe, liste des
   joueurs, cache, drapeau `remote_chara`) **sans** `SendSaveProbe`. Sinon `SendSaveProbe` comme aujourd'hui (l'invité
   accepte les deux réponses). Puis `ResumePendingHostMove` : l'host entre.
4. **Host**, deux images après `Zone.Activate`, là où il diffuse sa carte (`PropagateZoneChangeState`) : les autres
   joueurs reçoivent la carte ; cet invité reçoit à la place, dans cet ordre, `CompleteSoftRejoin` :
   a. vidage du tampon (`Delta.RefreshBuffer` + `WorldStateDeltaUpdate`, comme `SendSaveProbe`) ;
   b. `ZoneSoftRejoin` : compteur d'uid, renumérotations (ancien -> nouveau), somme du sac, sommes de la carte que
      l'host vient de charger, contenu des trois boîtes du monde, date, personnages du monde présents sur la carte ;
   c. `SessionPlayersSnapshot` ;
   d. `OnZoneDataReceivedResponse` appelé directement : placement sur sa case (le `_returnSpots` posé à l'étape 3),
      `GoalRemote`, compagnons (`BringCompanions`, chacun sur sa case), expédition due, `ZoneActivateResponse`.
5. **Invité**, `OnZoneSoftRejoin` -> `ApplySoftRejoin` : vérifie (renumérotations toutes trouvées, somme du sac égale),
   applique, **bascule** (`AwayZone = null`, `IsGuest = false`, `_rejoining = false`, `CardCache` refait depuis la
   carte, `StartWorldStateUpdate`), une ligne « Soft rejoin of … ». Puis `ZoneActivateResponse` ne fait que confirmer
   sa case.
6. **Filet**, à n'importe quel moment : `ZoneSoftRejoinFailed` (invité, sur écart, exception ou 20 s sans réponse) ou
   délai (host, 30 s sans être entré) -> `FallBackToWorldCopy` -> `SendSaveProbe`, c'est-à-dire exactement le chemin
   d'aujourd'hui. Dernier cran : si le monde demandé n'arrive pas en 20 s, l'invité ferme le lien comme un lien
   perdu et revient tout seul (schéma de `RetryZoneSync`).

### Pourquoi l'ordre tient (canal fiable, ordonné)

- Tant que l'invité n'a pas traité `ZoneSoftRejoin`, il est « absent » : il ne prend que la liste blanche de
  `ApplyChatWhileAway`. Tout ce que l'host dit de son **ancienne** carte (pendant qu'il la quitte) et des deux images
  entre son `Zone.Activate` et l'étape 4 est donc jeté chez l'invité.
- Ce qui est jeté ne manque pas : l'étape 4a envoie tout ce qui attendait AVANT de prendre les sommes (4b). Les
  sommes de la carte et du sac décrivent donc l'état de l'host après tout ce qui a été jeté.
- Tout ce que l'host envoie après 4b arrive après `ZoneSoftRejoin`, donc après la bascule, et s'applique à une carte
  qui a les mêmes sommes.
- Aucune minuterie côté invité n'est nécessaire pour « ignorer la carte de l'host » : l'host ne la lui envoie pas.

## Ce qui a changé par rapport au protocole demandé, et pourquoi

1. **`ZoneSoftRejoin` part APRÈS l'entrée de l'host sur la carte, pas avant.** Avant, deux trous : (a) entre le
   message et l'arrivée de l'host, l'invité déjà basculé aurait appliqué à SA carte les deltas de l'ANCIENNE carte de
   l'host (un mur creusé par un troisième joueur : même x, z, mauvaise carte ; rien ne le détecte, le terrain n'est
   pas dans les sommes) ; (b) ce que `Zone.Activate` fait chez l'host (apparitions, `Zone.Simulate`) n'aurait été
   dans aucune comparaison. Après : les sommes sont celles de la carte chargée (ce que le conseil avait retenu :
   « avec les sommes de la carte chargée par l'host »). Coût : l'invité attend le chargement de la carte par l'host,
   entrées bloquées (il l'attendait déjà aujourd'hui, plus la copie).
2. **Le personnage n'est pas posé directement sur sa case à l'enregistrement.** Il suit le chemin d'aujourd'hui (dans
   le groupe, il entre avec l'host, puis `OnZoneDataReceivedResponse` le remet sur sa case grâce à `_returnSpots`,
   2 images plus tard). Zéro code de placement nouveau.
3. **Trois niveaux de repli au lieu d'un** : sommes de carte égales -> rien n'est rechargé ; sommes de carte
   différentes -> l'invité bascule quand même et redemande **la carte seule** (comme `NetDesync` répare, case gardée
   par `KeepSpotForResync`) ; tout le reste -> copie du monde.
4. **Ajouts au message** : la somme du sac (garde-fou sur le point « doublons ») et les **personnages du monde
   présents chez l'host** (l'host, ses compagnons, d'autres joueurs) : l'invité n'en a que des copies vieilles de sa
   dernière copie du monde, et `CardGenDelta` ne remplace pas un personnage déjà connu.
5. **Nouveau petit message `ZoneSoftRejoinFailed`** plutôt que de détourner `ZoneLeaseDecline` ou un second
   `ZoneLeaseRelease` (l'host les ignore pour un joueur qui n'est plus « parti »).
6. **Pause du jeu de l'invité pendant l'attente** (non demandé) : voir « dangers ».
7. **La tâche en cours est arrêtée « à la main »**, pas gardée : voir point 8 de la liste à vérifier.

## Les dangers listés par le conseil

| Danger | Réponse |
|---|---|
| Objets ramassés / posés entre l'envoi et la bascule | entrées bloquées (existant) + **jeu de l'invité en pause** : ni PNJ ni joueur ne bougent chez lui. Si quelque chose change quand même : somme du sac différente -> copie du monde ; sommes de carte différentes -> carte seule |
| Deltas reçus entre l'enregistrement et la bascule | jetés (invité encore absent), couverts par le vidage 4a puis les sommes 4b |
| Personnage mort | chemin d'aujourd'hui (refus des deux côtés) |
| Compagnons | rendus et remplacés comme aujourd'hui ; replacés par `BringCompanions(keepSpot)` ; leurs cartes « en attente » renumérotées sont dans le même dictionnaire |
| `_returnSpots` | inchangé : posé par `OnZoneLeaseRelease` (case où il se tenait), consommé par `OnZoneDataReceivedResponse`, même case si elle est libre ; reposé avant un repli sur la copie |
| `Zone.Activate` de l'host | `ZoneLeaseState.Imported`, `BossFleePatch`, `lastActive`, `KeepAlive` : inchangés côté host. Ce qu'Activate change d'autre est dans les sommes |
| Troisième joueur | debout avec l'host : il garde l'ancienne carte (`LeavePlayersBehind`, inchangé). En train de charger : il suit l'host et reçoit la carte normalement. Visiteur de l'invité : pas de retour sur place (rappel non marqué) |
| `NetDesync` | pas affaibli ; `HoldOff()` à la bascule ; il ne compare de toute façon pas tant que `_rejoining` |

## À vérifier au banc (rien de tout cela n'a tourné)

1. **Le cas nominal passe-t-il ?** La somme du sac (`NetDesync.Bag`) est-elle vraiment égale des deux côtés juste après
   un aller-retour de sérialisation ? Si elle diffère toujours, tout retombe sur la copie (sûr, mais gain nul).
2. **Les sommes de carte sont-elles égales** après `Zone.Activate` + 2 images chez l'host (donjon, ville avec variante
   saisonnière, base) ? Sinon le retour coûte un chargement de carte à chaque fois.
3. **Le monde de l'invité n'est plus jamais rafraîchi** tant qu'il enchaîne des retours sur place : résidents, faction,
   maison, quêtes des autres, zones créées depuis. Quand il suit ensuite l'host vers une ville par la carte seule, les
   personnages globaux viennent de SA vieille copie. C'est le « monde périmé » du conseil (drapeaux « sali ») : **pas
   fait dans cette tranche**. À mesurer : 5 étages puis retour en ville, comparer habitants et `emp.desync`.
4. Personnages globaux qui ne sont ni joueurs ni compagnons (aventuriers de passage) : chez l'host ils sont ou non
   sur la carte selon SON monde. Ceux de l'host sont envoyés ; ceux que seul l'invité a sont retirés par
   `RemoveLeftOverCharas` après deux instantanés. À regarder en ville.
5. La pause (`AM_Adv.ShouldPauseGame`) arrête-t-elle bien tout, y compris dans un autre mode que l'aventure
   (construction) ? Et ne laisse-t-elle rien de figé après la bascule ou après un repli ?
6. PNJ après la bascule : ils ne tournent plus chez l'invité (`CharaTickEvent`), mais gardent l'objet « but » qu'ils
   avaient (combat en cours). Un client normal les reçoit neufs avec la carte. Effets visibles ?
7. Jetons de compétences de la barre : retirés du cache et redéclarés à l'host (`AbilityLayoutDirty`). La barre
   marche-t-elle encore, les jetons ne sont-ils pas doublés au prochain vrai chargement ?
8. Tâche en cours (lecture, minage) : arrêtée comme à la main à la bascule, rien de consommé. Pas pire qu'aujourd'hui
   (perdue avec la scène), mais pas « gardée ». Pour la garder : la relancer par le chemin client après la bascule.
9. Boîtes du monde : remplies avec les objets de l'host sous ses numéros. Fenêtre de boîte ouverte au moment du
   rappel ? Expédition par joueur (`emp_shipper`) intacte ?
10. Groupe chez l'invité après `AdoptHostCharas` : l'host est-il bien chef et membre, ses compagnons alliés, la liste
    à l'écran juste ?
11. `SessionPlayersSnapshot` envoyé juste après le message : `Self` et l'indice de pair corrects pour les numéros
    « en attente » créés dans la première seconde ?
12. Repli forcé à chaque étape : avant la réponse (délai 20 s), pendant l'application (exception), après la bascule.
    Le joueur n'est jamais bloqué, jamais interrogé, aucun objet en double.
13. Une sauvegarde de l'host puis rechargement après un retour sur place : le personnage de l'invité, ses compagnons
    et la carte sont ceux d'après le retour.
14. `GiveAxeToRemotePlayer`, `PayShipping` : changent le sac côté host autour de l'enregistrement. Une hache donnée à
    ce moment ferait différer la somme du sac (repli) ; l'argent d'expédition arrive après la somme.
15. Zones créées par l'invité (`_localZones`) : gardées telles quelles (son monde reste). Pas de doublon d'étage
    quand l'host crée le même ensuite ?

16. Les délais (invité 20 s, host 30 s) : l'host fait jusqu'à deux sauvegardes plus un chargement de carte avant de
    répondre. Sur le Steam Deck avec un gros monde, combien de retours dépassent 20 s (donc retombent sur la copie) ?
17. Contenu des coffres : `SameFloor` ne le compare pas (comme au départ de l'host). Un écart est seulement écrit au
    journal (« the content of a container differs »). Les événements de zone et la branche ne voyagent pas non plus.
18. Dates de la zone chez l'invité : laissées telles quelles à la bascule (un client normal a `dateExpire` et
    `dateRegenerate` au maximum, posés à chaque carte reçue). Voulu : ces dates repartent chez l'host au prochain
    passage de main. À regarder : aucune régénération chez l'invité avant la prochaine carte reçue.

## Relecture

Relu par l'agent `relecteur-elintogether` (lecture seule) : rien trouvé qui duplique ou perde un objet, règle décochée
sans effet. Corrigé après sa relecture : dernier cran contre un joueur bloqué, vidage du tampon avant la carte envoyée
aux AUTRES joueurs dans la branche nouvelle, délais allongés, ligne de journal pour les coffres. Non retenu : forcer
les dates de la zone (point 18).

## Ce qui retombe encore sur la copie du monde, et pourquoi

- L'invité **marche** vers la carte de l'host (`TryTravel` -> `SendRejoin(arrival)`, cas b) : tranche 2.
- L'host entré « sans rappel » (`OnHostZoneChangedWhileAway`), refus `emp_travel_host_zone`, session de zone fermée,
  zone de quête, carte du monde : pas de rappel marqué.
- L'invité a des visiteurs, est mort, voyage déjà, ou n'est pas debout sur la carte rappelée.
- L'host a renoncé à entrer ou est allé ailleurs avant la réponse ; l'host n'entre pas dans les 30 s.
- Somme du sac différente, renumérotation introuvable, exception, pas de réponse en 20 s.
- Première connexion, reconnexion, départ d'une carte : inchangés.

## Banc : étapes à ajouter

`dev/_tools/floors_suite.py` compte déjà les copies par étage. Avec la case cochée (`EmpConfig.Server.SoftRecall`),
l'étape **« etage n, invite d'abord : aucune copie du monde pour l'invite »** doit passer au vert (l'invité tient
l'étage du dessous, l'host le rejoint = rappel). L'étape « host d'abord » reste rouge : c'est la tranche 2. La ligne
« Back after … world copy of 0 bytes » sort aussi pour un retour sur place.

À ajouter, dans cet ordre :
1. Lancer la suite deux fois, case décochée puis cochée : décochée, les chiffres d'aujourd'hui, à l'identique.
2. Compter aussi les lignes « Soft rejoin of » (deux côtés), « given up » (replis) et « asking for the map alone ».
3. Totaux d'objets, d'or et d'expérience des deux sacs avant / après (déjà fait pour les objets), avec un objet posé
   au sol et un ramassé juste avant le rappel.
4. Doublons d'uid : des deux côtés, sur la carte + les sacs, après chaque retour (`GroupBy(uid).Any(Count > 1)`), et
   aucun uid « en attente » resté dans le sac de l'invité.
5. Tâche : lancer une lecture chez l'invité, rappeler, noter « arrêtée » (attendu) et que le livre est entier.
6. Sommes de carte égales 10 s après (`emp.desync` des deux côtés), aucune ligne « Map checksum differs ».
7. Repli forcé : (a) couper la réponse (délai) ; (b) fausser `BagMix` ; (c) fausser `MapSums` -> carte seule ;
   vérifier une copie du monde (a, b) ou une carte (c), et un joueur jouable dans les 45 s.
8. Compagnon de l'invité + compagnon de l'host : chacun à sa place, dans le bon groupe, des deux côtés.
9. Trois fenêtres (PC libre seulement) : un troisième joueur debout avec l'host, puis en train de charger.
10. Sauvegarde de l'host + rechargement après un retour, puis 20 passages de main d'affilée (taux de repli).

---

# Tranche 2 : retour par la carte seule (l'invité marche vers la carte de l'host) — 2026-10-07

Quand un invité seul sur une carte qu'il tient prend l'escalier (ou la porte) vers la carte où se tient l'host, il ne
recharge plus le monde : il garde son jeu, reçoit ce qu'il ne peut pas savoir sans copie du monde, puis **la seule
carte de l'host**, et la charge comme un client qui suit l'host. Même règle, même case que la tranche 1 (`SoftRecall`,
décochée par défaut ; textes de la case mis à jour : « No world reload when the host and a player meet again (new) »).
Case décochée : rien ne change.

**État : écrit, compilé (0 erreur en Release et en Debug), JAMAIS joué.** Aucun test en jeu, aucun commit. La tranche 1,
elle, a été jouée le 7 octobre (9 retours sur 9 sans copie) ; son chemin n'a été touché que par deux retouches
(extraction de `CreateSoftRejoin`, une condition de plus dans `FallBackToWorldCopy`) : à rejouer avec la suite.

## Ce qui a été écrit, fichier par fichier

| Fichier | Contenu |
|---|---|
| `Models/ZoneLease/ZoneSoftRejoin.cs` | champ `Travel` (clé 8) : même message que la tranche 1, la carte suit |
| `Models/ZoneLease/ZoneLeaseDenied.cs` | champ `HostZoneUid` (clé 2) : le numéro de la zone **chez l'host** quand le refus est `emp_travel_host_zone` |
| `Models/ZoneState/ZoneDataResponse.cs` | champs `ZoneState` (clé 4) et `IdCurrentSubset` (clé 5) : les nombres de la zone chez l'host, envoyés avec chaque carte |
| `Net/Host/ElinNetHostSoftRejoin.cs` | `CanReturnSoftly`, `SendSoftReturn` ; `CreateSoftRejoin` sorti de `CompleteSoftRejoin` (même contenu, partagé) ; `FallBackToWorldCopy` garde le point d'arrivée encore noté |
| `Net/Host/ElinNetHostTravel.cs` | `OnZoneLeaseRelease` : troisième branche (`SendSoftReturn`) entre le retour sur place et la copie ; le refus `emp_travel_host_zone` porte `HostZoneUid` |
| `Net/Client/ElinNetClientSoftRejoin.cs` | `_softReturnZone`, `CanReturnSoftly`, branches « Travel » de `OnZoneSoftRejoin` / `ApplySoftRejoin`, `EnterBySoftReturn`, `ForgetAbsentCharas`, délai de 8 s pour la carte |
| `Net/Client/ElinNetClientTravel.cs` | `SendRejoin(arrival)` arme le retour par la carte ; refus `emp_travel_host_zone` : `AdoptHostUid` + bon numéro dans `Arrival` (règle cochée seulement) ; `IsInTransfer` tient jusqu'à la carte chargée |
| `Net/Client/ElinNetClientZone.cs` | la branche « carte seule » de `OnZoneActivateResponse` sortie telle quelle dans `EnterHostMap` ; branche nouvelle `EnterBySoftReturn` ; `RetryZoneSync` demande le monde tout de suite pendant un retour par la carte ; `OnZoneDataResponse` prend les nombres de la zone (règle cochée) |
| `Net/Client/ElinNetClientPlayer.cs` | une copie du monde qui arrive annule aussi `_softReturnZone` |
| `Net/NetSessionRules.cs`, `Emp/EmpConfig.cs`, `package/LangMod` | description de la règle (EN + CN + JP) étendue aux deux cas |
| `dev/_tools/floors_suite.py` | compte les lignes « Soft return », les replis (« given up »), et les numéros en double des deux côtés (non lancé) |

## La suite des messages

1. **Invité**, `TryTravel` (la zone visée est celle de l'host) ou `OnZoneLeaseDenied` (`emp_travel_host_zone` : la
   zone qu'il a créée lui-même prend d'abord le numéro de l'host, `AdoptHostUid`) -> `SendRejoin(arrival)`. Si
   `CanReturnSoftly` : `_softReturnZone` = la zone de l'host, attente 20 s, et le rendu part marqué
   `ZoneLeaseRelease { Rejoin, Soft, Arrival }` avec carte, personnage, compagnons, compteur **comme aujourd'hui**.
   Entrées bloquées et jeu en pause dès cet instant.
2. **Host**, `OnZoneLeaseRelease` : applique carte, personnage, compagnons, compteur comme aujourd'hui ; note le point
   d'arrivée (`_returnSpots`, inchangé). Si `CanReturnSoftly` -> `SendSoftReturn`, **dans la même image** :
   a. `RegisterPlayer` (groupe, carte de l'host, liste des joueurs, cache) sans sérialiser le monde ;
   b. vidage du tampon (`Delta.RefreshBuffer` + `WorldStateDeltaUpdate`) ;
   c. `ZoneSoftRejoin { Travel }` : compteur d'uid, renumérotations, somme du sac, trois boîtes du monde, date,
      personnages du monde debout sur la carte de l'host (pas de sommes de carte : l'invité n'en a pas de copie) ;
   d. `SessionPlayersSnapshot` ;
   e. `ZoneDataResponse` (la carte, avec les nombres de la zone).
   Sinon `SendSaveProbe`, comme aujourd'hui.
3. **Invité**, `OnZoneSoftRejoin` -> `ApplySoftRejoin` (branche Travel) : mêmes vérifications que la tranche 1
   (renumérotations, somme du sac), boîtes, date, personnages de l'host ; `ForgetAbsentCharas` ; **bascule**
   (`AwayZone = null`, `_rejoining = false`) ; `CardCache.Reset()` ; `Delta.HoldForIncomingMap()` ; délai de 8 s pour
   la carte. Pause et blocage des entrées **gardés** (`_softReturnZone`).
4. **Invité**, `OnZoneDataResponse` (chemin existant) : fichiers de la carte écrits, zone trouvée (ou construite
   depuis le message si elle est inconnue et que son parent est connu), nombres de la zone pris, `Ready`.
5. **Host**, `OnZoneDataReceivedResponse` (chemin existant) : place le personnage au point d'arrivée, `GoalRemote`,
   compagnons autour de lui, expédition due, `ZoneActivateResponse`, `MarkSettled`.
6. **Invité**, `OnZoneActivateResponse` -> `EnterBySoftReturn` : ses compagnons changent de zone avec lui, ses
   invocations restent sur la carte rendue, `EnterHostMap` (la branche existante : `pc.MoveZone`, `player.MoveZone`),
   ménage (ce que le jeu a mis dans le sac en quittant la carte, tampon sortant, jetons de compétences), fin de la
   pause, puis `Delta.MapPlaced()` et la case donnée par l'host.
7. **Filet**, à chaque étape : `AskWorldCopy` -> `ZoneSoftRejoinFailed` -> `FallBackToWorldCopy` -> `SendSaveProbe`
   (20 s sans réponse, 8 s sans carte, écart, exception, zone impossible à charger). Dernier cran inchangé : pas de
   monde 20 s après l'avoir demandé = lien fermé comme un lien perdu, retour automatique.

### Pourquoi l'ordre tient

- **Avant la bascule** l'invité est « absent » : tout ce que l'host dit de sa carte est jeté (`ApplyChatWhileAway`).
  Rien n'en manque : l'host vide son tampon (2b) **avant** de prendre la somme du sac et la copie de la carte, dans la
  même image. Ce qui est jeté est donc dans la copie ; ce qui vient après la copie part après `ZoneSoftRejoin`.
- **Entre la bascule et la carte chargée** l'invité n'est plus absent, mais son écran montre encore la carte qu'il
  quitte. `HoldForIncomingMap` (jeu en marche) garde tout jusqu'à `MapPlaced` : rien n'est appliqué à la mauvaise
  carte. Deux sortes passent quand même : `SpatialGenDelta` (voulu : une zone nouvelle) et `CharaMoveDelta`, qui ne
  bouge qu'un personnage dont la zone est celle de l'host ; aucun n'est dans ce cas chez l'invité à ce moment (les
  siens sont encore dans l'ancienne zone, ceux de l'host arrivent sans zone, les autres ont été retirés par
  `ForgetAbsentCharas`).
- La garde lâche au bout de 10 s (`MaxHoldSeconds`) ; l'invité demande le monde au bout de **8 s** et vide tout. La
  garde ne lâche donc jamais sur l'ancienne carte.
- **Dans l'autre sens** : l'host jette ce que dit un joueur pas encore placé (`_settled`) ; le jeu de l'invité est en
  pause et ses entrées bloquées jusqu'à la carte chargée ; ce que la sortie de l'ancienne carte a produit est effacé
  (`Delta.ClearOut`) avant tout envoi. Sa position envoyée avant le chargement porte le numéro de l'ancienne zone :
  l'host ne la prend pas.

## Ce qui a changé par rapport à la demande, et pourquoi

1. **Même message `ZoneSoftRejoin` + un champ `Travel`**, pas de message frère : le contenu est le même, la
   vérification côté invité aussi (`ApplySoftRejoin` partagé). `MapSums` est vide dans ce cas.
2. **Tout part dans la même image que le rendu** (pas après un `Zone.Activate` comme en tranche 1) : l'host est déjà
   debout sur sa carte, c'est le schéma de `SendSaveProbe` (monde + carte ensemble), sans le monde.
3. **Le refus `emp_travel_host_zone` renvoyait le numéro de la zone chez l'INVITÉ** (celui de la demande), pas celui
   de l'host : `AdoptHostUid` n'avait rien à adopter. Champ `HostZoneUid` ajouté ; utilisé seulement règle cochée.
4. **Les nombres de la zone voyagent avec chaque carte** (`ZoneDataResponse.ZoneState`), pris par le client règle
   cochée. Non demandé, petit, et c'est le seul point périmé trouvé qui peut coûter quelque chose (voir plus bas).
5. **Les autres joueurs absents de la carte sont oubliés** (`ForgetAbsentCharas`), comme un client les oublie quand
   ils partent : sinon leur vieille copie est reprise à leur retour.
6. **Pas de retour par la carte avec un objet « à porter seulement » dans les mains ou le sac** : le jeu le pose en
   quittant la carte (`Chara.TryDropCarryOnly`), sur une carte qui n'est plus à l'invité.
7. **Les invocations restent sur la carte rendue** (comme avec la copie du monde aujourd'hui) : le jeu les aurait
   emmenées (`listCarryoverMap`) comme des personnages inconnus de l'host.
8. **Pas de « drapeaux sali »** : voir « ce qui peut être périmé ».

## À vérifier au banc (rien de tout cela n'a tourné)

1. `floors_suite.py --soft` : les étapes « host d'abord » passent-elles à 0 copie, avec une ligne « Soft return: map
   … loaded » chez l'invité et aucune « given up » ? Les étapes « invité d'abord » restent-elles à 0 (tranche 1) ?
2. Même suite **case décochée** : chiffres d'avant, à l'identique.
3. La somme du sac est-elle égale des deux côtés juste après `RegisterPlayer` (qui appelle `MakeAlly`, `MoveZone`,
   `GiveAxeToRemotePlayer`) ? Sinon tout retombe sur la copie.
4. L'invité arrive-t-il **sur l'escalier** (point d'arrivée), y compris quand il a créé l'étage lui-même sous un
   autre numéro (refus + `HostZoneUid`) ? Regarder la ligne « Zone … created locally as …, host uid … ».
5. Pause et blocage : rien ne reste figé après la carte chargée, ni après un repli. Durée du gel ressentie.
6. Compagnons de l'invité : présents, près de lui, dans le bon groupe des deux côtés ; pas en double, pas restés sur
   l'ancienne carte. Compagnon mort en route. Monture.
7. Invocations : restées sur l'ancienne carte chez l'host, absentes chez l'invité ; pas de fantôme.
8. Personnages du monde sur la carte de l'host (l'host, ses compagnons, un aventurier, un résident de la base) :
   visibles chez l'invité au bon endroit dès les premières secondes ; aucun en double ; aucun fantôme d'un personnage
   qui était là dans le vieux monde de l'invité et n'y est plus.
9. Trois fenêtres : un troisième joueur absent de la carte (oublié par `ForgetAbsentCharas`) qui revient ensuite :
   son sac est-il juste chez l'invité ? La liste des joueurs à l'écran ?
10. Objet posé sur la carte de l'host par l'host **pendant** le retour de l'invité (entre le rendu et la carte
    chargée) : visible chez l'invité, une seule fois.
11. Artefact divin au sol de la carte quittée : pas dans le sac de l'invité après le retour, toujours sur la carte
    chez l'host.
12. Jetons de compétences : la barre marche, pas de jeton en double après ce retour puis après un vrai chargement.
13. Boîtes du monde (expédition, livraison, banque) : contenu juste après le retour, dépôt et retrait possibles.
14. Repli forcé à chaque étape : avant la réponse (couper `ZoneSoftRejoin`), après la bascule (couper la carte :
    8 s), `BagMix` faussé, exception dans le chargement. Joueur jouable, aucun objet en double, une copie du monde.
15. Zone inconnue de l'invité (étage créé par l'host après le départ de l'invité) : construite depuis la carte, ou
    repli. Pas d'étage en double dans le donjon ensuite (reprendre l'escalier dans les deux sens).
16. L'host change de carte pendant le retour de l'invité : l'invité finit avec l'host, ou seul, jamais bloqué.
17. Sauvegarde de l'host puis rechargement après un retour par la carte : personnage, sac, compagnons de l'invité.
18. Puis l'host part et l'invité hérite de la carte (`TakeOverZone`), puis l'host revient (tranche 1) : enchaîner
    dix fois, sommes de carte égales, `emp.desync` propre des deux côtés.
19. Nombres de la zone : investir dans une ville pendant que l'invité est ailleurs, le faire revenir par la carte,
    lui laisser la ville, le faire repartir : l'investissement est-il toujours là chez l'host ?
20. Tâche en cours et message « tu arrêtes… » : ne sort-il pas à chaque escalier (voir point 8 de la tranche 1) ?
21. La ligne « Back after … 0 bytes, N host deltas not taken (…) » : relever les sortes non prises sur une vraie
    partie, c'est la liste de ce qui est périmé.

## Ce qui retombe encore sur la copie du monde, et pourquoi

- **Refusé par l'invité avant d'envoyer** (`CanReturnSoftly`) : règle décochée ; il a des visiteurs ou visite
  quelqu'un (session de zone) ; il quitte la carte du monde ou une zone de quête (pas de carte à rendre), ou va vers
  l'une d'elles ; mort ; un voyage, un passage de main ou une attente en cours ; un dialogue, un échange ou un coffre
  ouvert ; un objet « à porter seulement » sur lui.
- **Les retours sans point d'arrivée** (`SendRejoin()` nu) : suivre l'host dans la zone de sa quête (`FollowHost`),
  l'host entré « sans rappel », zone fermée sans repreneur, invité refusé chez un autre joueur.
- **Refusé par l'host** (`CanReturnSoftly`) : l'host est en route vers une autre carte (`_pendingHostMove`) ; il est
  sur la carte du monde, dans une zone de quête ou une instance ; le numéro d'arrivée n'est pas celui de sa carte
  (il a bougé depuis) ; l'invité rend aussi des personnages de visiteurs, ou tient encore une autre zone ; personnage
  mort.
- **En cours de route** : renumérotation introuvable ou numéro déjà pris, carte « en attente » sans numéro, somme du
  sac différente, exception, pas de réponse en 20 s, pas de carte en 8 s, chargement de la carte en échec.
- **Zone inconnue de l'invité dont le parent est inconnu aussi**, ou nom de zone différent : `RetryZoneSync` demande
  le monde tout de suite. En pratique seulement si l'host a changé de carte entre-temps vers une zone née après la
  dernière copie de l'invité : par `TryTravel` l'invité vise toujours une zone que son monde connaît ou qu'il vient
  de créer (parent connu).
- Première connexion, reconnexion : inchangés.

## Ce qui peut être périmé après un retour par la carte

Aucune vérification automatique du « monde périmé » n'a été ajoutée (pas de drapeaux « sali ») : seulement la somme
du sac, la zone introuvable, et ce qui est renvoyé ci-dessous. Un invité qui ne revient plus que par la carte garde
donc le reste périmé jusqu'à une copie du monde venue pour une autre raison.

| Quoi | État | Peut coûter (objets, or, expérience) ? |
|---|---|---|
| Son personnage, son sac, ses compagnons | les siens font foi, envoyés à l'host ; numéros en attente renumérotés ; somme du sac comparée | non (écart = copie du monde) |
| Compteur de numéros de cartes | envoyé | non |
| Boîtes du monde, date, météo, quêtes, drapeaux, factures, codex | envoyés, ou pris pendant l'absence | non |
| Personnages du monde debout sur la carte de l'host | envoyés neufs | non |
| Personnages que son monde croit sur cette carte | retirés avant le chargement | non, apparence |
| Autres joueurs absents de la carte, leurs compagnons | oubliés ; reviennent entiers à leur arrivée | non |
| Nombres de la zone chargée (visites, développement, dates, drapeaux) | pris avec la carte | **oui sans cela** : l'invité qui hérite ensuite de la carte renvoie SES nombres à l'host avec son rendu (`TakeOverZone` n'applique pas ceux de l'host) ; un investissement fait pendant son absence aurait été écrasé |
| Personnages du monde ailleurs (résidents, aventuriers) | périmés | apparence. Un échange avec un personnage du monde fait seul sur une carte n'est déjà pas renvoyé à l'host aujourd'hui (limite existante) ; périmé, ce personnage peut en plus ne plus être là chez l'host |
| Base et faction (ressources, politiques, membres, noms) | périmés | non : toute action passe par l'host, qui décide avec ses valeurs ; l'écran de la base montre de vieux chiffres |
| Zones créées ou détruites par l'host ailleurs, sites de la carte du monde | inconnus / fantômes | non : entrer dans une zone disparue est refusé (`emp_travel_invalid`) ; un site nouveau n'est pas visible avant la prochaine copie |
| Compteur de numéros de zones | pas envoyé | non : une zone créée ici est renumérotée au bail ou au refus (`AdoptHostUid`) |
| Recettes apprises par les autres (`AddRecipeDelta`), affinités, religions, niveaux et attributs des autres | périmés | non, apparence ou manque passager |

Suite proposée (conseil) : les drapeaux « sali » côté host pour base / zones / personnages du monde, ou plus simple,
une copie du monde forcée après N retours par la carte ou quand la ligne « host deltas not taken » contient une sorte
hors d'une liste connue.

## Relecture (tranche 2)

Relu par l'agent `relecteur-elintogether` (lecture seule) : aucun chemin trouvé qui duplique ou perde un objet, ni
qui laisse l'invité bloqué ; règle décochée sans effet (seule différence : `ZoneState` voyage toujours avec la carte).
Corrigé après : une réponse de placement qui croise une demande de monde est ignorée (`OnZoneActivateResponse`).
Noté, non corrigé : (a) host qui sauvegarde tout de suite (serveur dédié, sauvegarde automatique décochée) : la
sauvegarde passe avant la réponse de placement ; au-delà de 8 s l'invité retombe sur la copie du monde ; (b) si une
autre zone de l'invité porte déjà le numéro de l'host sous un autre nom, la carte reçue la remplace dans la table des
zones (comportement existant de `OnZoneDataResponse`) ; (c) règle cochée, le numéro d'arrivée corrigé (`HostZoneUid`)
sert aussi quand le retour finit par la copie du monde ; (d) `ZoneState` est aussi pris pour la carte du monde et pour
une carte rechargée sur place ; (e) lien perdu pendant le passage : `EInput.haltInput` peut rester vrai (déjà possible
avant, à vérifier).

## Trouvé au passage dans le chemin d'aujourd'hui (non corrigé, règle décochée inchangée)

1. Le refus `emp_travel_host_zone` renvoie le numéro de zone **de la demande** : pour un étage créé par l'invité,
   `_hostZoneUid` et `Arrival.ZoneUid` sont faux ; si les numéros diffèrent, le point d'arrivée noté ne correspond pas
   à la carte et l'invité apparaît à côté de l'host au lieu de l'escalier.
2. `TryTravel` compare `zone.uid == _hostZoneUid` même pour une zone créée ici (numéro local) : un hasard de numéros
   envoie l'invité « chez l'host » à tort.
3. `AdoptHostUid` prend pour « la copie de l'host » toute zone de même id et mêmes x, y qui porte ce numéro : un autre
   étage du même donjon est alors détaché de son parent.
4. En quittant une carte tenue seul pour une autre (bail accordé), la carte est rendue **avant** le déplacement :
   l'artefact divin que `Zone.Deactivate` met dans le sac existe alors deux fois, et l'objet « à porter seulement »
   posé par `TryDropCarryOnly` est perdu.
5. `TakeOverZone` n'applique pas `grant.ZoneState` : les nombres de la zone de l'héritier repartent chez l'host.
6. `CardGenDelta` reprend la copie du monde d'un joueur déjà absent quand ce client a reçu son monde : son sac est
   vieux à son retour (réparé par la demande de sac de `NetDesync`). À confirmer.
7. Tranche 1 : `ForgetAbsentCharas` n'y est pas appelé (même besoin à trois joueurs).
8. Un rendu marqué `Soft` auquel l'host répond par le monde : l'invité attend 20 s puis 20 s ; sur un lien lent avec
   un gros monde il ferme le lien avant la fin du transfert.
