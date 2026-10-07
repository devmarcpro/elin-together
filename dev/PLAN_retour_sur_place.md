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
