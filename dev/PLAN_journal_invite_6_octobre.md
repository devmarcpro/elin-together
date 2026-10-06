# Journal d'un invité, partie à 4 du 2026-10-06 (0.26.524) : causes et corrections

Journaux lus (hors dépôt) : l'invité « Arma Minima » (20:14Z-20:51Z) et « 玉皇大帝 » (host 20:12Z-20:32Z, puis
**client** de 20:40Z à 20:46:03Z). L'horloge de 玉皇大帝 retarde de 34,5 s sur celle de l'invité (heures « h » ci-dessous
= son journal, « g » = l'invité). **À partir de 20:38Z l'host est LemiWinks, dont on n'a pas le journal** : entre
20:45Z et 20:49Z le croisement se fait avec un autre client, jusqu'à h20:46:03 seulement.

Compilé (`ReleaseNightly`, 0 erreur, 0 avertissement). **Rien n'a tourné en jeu.**

## 0. La cause commune (à corriger en premier, hors de mes fichiers)

`ElinTogether/Net/Base/ElinNetBase.cs:74-86`, `OnDestroy`, **build Release seulement** (`#if !DEBUG`) : quand
**n'importe quel** composant réseau est détruit, tous les patchs Harmony du mod sont retirés (`UnpatchSelf`). Le mod
d'origine n'avait qu'un composant ; le fork en a deux chez un invité (le lien avec l'host + la session de zone). Dès
qu'une session de zone se ferme (l'invité cesse de tenir une carte avec des visiteurs, ou quitte la carte d'un
autre), le lien avec l'host continue **sans aucun patch** : plus rien n'est envoyé, les messages reçus ne sont plus
appliqués à chaque image (seulement quand le code les force : départ, passage de main), changer de carte n'est plus
intercepté (le joueur entre et sort des cartes chez lui seul, sans bail). Ça dure jusqu'à la création d'un nouveau
composant (nouvelle session de zone, reconnexion). Le banc de test est en Debug : jamais vu.

Preuves dans le journal : après chaque `Removed zone session of …` (g20:25:35, 20:43:23, 20:44:16, 20:45:52,
20:49:57, 20:50:25), plus une seule ligne de message appliqué jusqu'au prochain `Initialized zone session` /
`Initialized new connection component`, sauf une rafale au moment exact d'un départ forcé (g20:27:00.29,
20:46:15.15, 20:50:09.72 : `Zone add card`, `Applying element` de plusieurs secondes d'un coup). Même chose chez
玉皇大帝 (h20:45:26 -> 20:45:40 : zéro ligne, puis il se retrouve sur `Zone_startSite` sans avoir rien demandé).

Correction exacte (une condition) :

```
// avant (ElinNetBase.cs:83-85)
#if !DEBUG
        EmpMod.SharedHarmony.UnpatchSelf();
#endif

// après
#if !DEBUG
        // only when the last component goes: a zone session closing next to the host link must leave the
        // patches that link runs on (a link made again in the same frame keeps them too)
        if (Session.Transport == null && Session.ZoneSession == null) {
            EmpMod.SharedHarmony.UnpatchSelf();
        }
#endif
```

(`NetSession.RemoveZoneSession` met `ZoneSession` à null avant `Destroy` ; `RemoveComponent` met `Transport` à null :
lu.) Test : build **Release**, un invité tient une carte, un second y entre puis en sort ; le premier doit continuer
à recevoir et envoyer (`HarmonyLib.Harmony.HasAnyPatches(ModInfo.Guid)` vrai).

En attendant, filet dans mes fichiers : `Net/Client/ElinNetClientPlayer.cs` (`OnSaveDataProbe`), une image après
chaque monde reçu, les patchs sont remis s'ils manquent (Warning `The patches of the mod were gone when the world
arrived, put back`). Ne couvre pas le temps entre la fermeture de la session de zone et le monde suivant. À retirer
une fois `ElinNetBase` corrigé.

## 1. Expulsé pour « invalid zone » (g20:48:52)

Séquence (invité) : 20:45:52.324 `Removed zone session of ElinNetHost` (patchs retirés) ; 20:46:19 il garde la carte
du monde ; 20:47:48 l'host y entre -> `without recall, rejoining` -> monde + carte reçus, placé sur la carte du
monde ; sans patch, il entre de lui-même dans une carte (rien au journal, rien demandé) ; 20:48:05.177 l'host quitte
la carte du monde et la lui laisse : `Handed zone 2 while not in it` (il n'y est plus). L'host le tient désormais
pour parti, lui se croit client : il reçoit chaque carte où l'host entre (137, 2, 137, 2), répond « prêt », n'est
jamais placé. 20:48:52.016 l'host crée un champ **neuf** (uid 142) : l'annonce de la zone (`SpatialGenDelta`) est
dans la file que plus rien ne traite -> `Remote zone does not exist` -> la reconstruction depuis l'état reçu échoue
(exception avalée en Release) -> `Zone state mismatch` ; trois essais en 0,5 s, tous pareils -> expulsion.

Ce n'est donc ni une « reçue deux fois » gardée à tort (ce filtre a bien travaillé : même zone, même seconde), ni
`AdoptHostUid`, ni l'envoi « monde + carte ensemble » : c'est une zone créée après la copie du monde, annoncée par un
message jamais appliqué. 141/142 sont deux champs différents créés par l'host à une minute d'écart.

Fait :
- `Net/Client/ElinNetClientZone.cs`, `RetryZoneSync` : plus d'expulsion. Au 3e échec le lien est fermé comme un lien
  perdu (`RemoteClosed`, pas `InvalidZone` qui coupe le retour automatique) : `NetReconnect` ramène le joueur tout
  seul (monde puis carte, comme une arrivée). Warning `Zone sync failed after {RetryCount} attempts, joining the game
  again for its world and map`. Si l'host a décoché le retour automatique : écran titre comme avant.
- Même fichier, `OnZoneDataResponse` : l'exception de la reconstruction est écrite (Warning `Zone {ZoneFullName} is
  unknown here and could not be built from its state`, avec l'exception). On ne sait pas encore laquelle c'est.
- `Net/Base/ElinDeltaManager.cs`, `ProcessLocalBatch` : pendant une retenue (monde ou carte en cours de chargement),
  un `SpatialGenDelta` est appliqué tout de suite au lieu d'être retenu : la carte qui suit a besoin de sa zone.
  Sans cela, depuis D4, un host qui enchaîne deux cartes dont la seconde est neuve (carte du monde puis champ)
  pouvait donner le même « mismatch » à un invité pas encore placé sur la première.

À faire ailleurs (`Net/Client/ElinNetClientTravel.cs`, pas à moi) :
- `TakeOverZone`, lignes 431-435 : après le Warning `Handed zone … while not in it`, avant `return` :
  `if (!Session.IsAway && _pendingTravel is null && _pendingGrant is null) { SendRejoin(); }`. L'host l'a retiré de
  sa carte pour lui laisser celle-ci : rien d'autre ne le ramène. (`SendRejoin` ne fait rien s'il revient déjà ; côté
  host, `OnZoneLeaseRelease` le trouve dans `_departed`, lâche le bail fantôme et renvoie monde + carte.)
- `OnZoneLeaseRecall`, lignes 741-744 (« already handed back ») : répondre
  `if (_pendingTravel is null && _pendingGrant is null) { Host.Send(new ZoneLeaseDecline { ZoneUid = recall.ZoneUid }); }`
  avant `return`. Aujourd'hui l'host attend sans fin un joueur qui ne tient pas la carte (h20:30:09 -> h20:31:07 :
  14 `Recalling zone Zone_startSite@0 from Nardole`, l'host bloqué 58 s à la porte de sa base). À relire : le cas
  « deux baux pendant un déplacement ».
- Option propre à la place de `RemoteClosed` : ajouter `InvalidZone` à `EmpDisconnectInfo.IsLinkLost`
  (`Common/EmpDisconnectInfo.cs:29`), ce qui couvre aussi l'host qui coupe pour « invalid zone »
  (`ElinNetHostZone.cs:77`).

## 2. « invalid source » sur la carte d'un autre invité (g20:25:35)

Ce n'est pas un refus automatique : la session de zone de LemiWinks a refait **son** contrôle des sources avec
**ses** réglages (`flags=All`, 15 sources) alors que l'host (玉皇大帝) n'en demandait aucun (`flags=None, 0 sources`).
Trois écarts -> la question « continuer ? » s'est affichée chez l'invité en pleine marche (20:25:30.958), il a
répondu non 5 s plus tard (`Client chose to disconnect due to validation mismatches`) -> session de zone fermée,
30 s d'attente d'un repreneur, puis rappel par l'host.

Fait, `Net/Host/ElinNetHostIntegrity.cs`, `OnNetHandshakeResponse` : une session de zone ne contrôle plus rien
elle-même (ni sources, ni mods, ni « même version du jeu » : ces cases sont celles du joueur qui tient la carte, pas
celles de la partie). Version du mod vérifiée, puis entrée directe. Information `Guest {@Peer} was let in by the host
of the game, no source validation here`. Les actes (seul contrôle bloquant) ont été comparés à ceux de l'host pour
les deux joueurs. Plus aucune question à l'invité en entrant sur une carte.

Ce que `[DIFF] SourceThing` peut casser : les objets voyagent en texte (`RemoteCard.Data` = JSON du jeu, identifiant
texte), pas par index de table : **pas de décalage**. Un objet d'un mod que l'autre n'a pas : sa création échoue chez
lui (objet absent, puis `parent uid cannot be resolved`). Mêmes identifiants, lignes différentes : mêmes objets, mais
poids, prix ou valeurs calculés différemment chez chacun (l'host fait foi). Les deux `[MISSING]` sont des mods
d'affichage.

## 3. Cinq rechargements en 17 s (g20:29:25 -> 20:29:42)

Ce n'est pas une descente de donjon. Croisé avec l'host (h = g - 34,5 s) :
- h20:28:48 l'host quitte la base (`Zone_startSite`) : `Nardole keeps it`. Nardole ne la tient pas vraiment (très
  probablement le même `Handed zone … while not in it`, voir §0 ; son journal manque) : il refuse tout visiteur et ne
  répond pas aux rappels.
- h20:28:50 l'invité revient de son champ vers l'host : copie n° 1 (normale).
- h20:28:53, 20:28:57, 20:29:02, 20:29:06 : l'invité essaie quatre fois d'entrer dans la base ; chaque fois
  `joins zone Zone_startSite@0 held by Nardole` -> `left the host map` -> `Zone 7 refused player` ->
  `returns to the host zone` -> `Sending save probe`. **Chaque refus = une copie entière du monde**, parce que l'host
  retire le joueur de sa carte (`OnZoneLeaseAck` -> `DepartFromHostMap`) **avant** de demander au teneur s'il
  l'accepte ; refusé, il ne peut revenir que comme une arrivée (`OnZoneLeaseDenied` -> `SendRejoin`).
- La 5e fois l'host est entré entre-temps dans la forêt : l'invité est rechargé **dans le donjon** (`Zone_dungeon_forest@-1`).
  C'est le « téléporté ».

Corrections, par ordre : (a) §0 (plus de teneur fantôme) ; (b) les deux lignes de §1 dans `ElinNetClientTravel.cs` ;
(c) plan pour ne plus payer un monde par refus, non fait (trop gros sans test) :
`ElinNetHostTravel.cs`, `RefuseGuest` (1080-1091) quand le joueur vient de quitter la carte de l'host
(`_departed` le contient, aucun bail) : au lieu de `ZoneLeaseDenied` seul, le remettre sur la carte (l'inverse de
`DepartFromHostMap` : `_departed.Remove`, `States`/`ActiveRemoteCharas`/`CurrentPlayers` comme
`SendSaveProbe` lignes 244-260, sans la copie) puis `PropagateZoneChangeState(_zone, peer)` ; côté invité
(`OnZoneLeaseDenied`, 708-715) : `_pendingGrant = null; StartWorldStateUpdate();` sans `SendRejoin`. Il n'a rien
manqué : pendant l'attente il reçoit et applique encore les messages (seuls les instantanés sont filtrés). Demande
un champ « remis sur la carte » dans `ZoneLeaseDenied` (anciens clients : comportement actuel).

## 4. Personnages en moins

- g20:26:43 (9/9 pas les mêmes), g20:46:11 (5/8), g20:51:04 (6/7) : périodes sans patch (§0). Les personnages
  manquants sont ceux des autres joueurs, annoncés par des messages reçus mais pas appliqués (`Zone add card 1`,
  `Zone add card 504` arrivent d'un bloc à g20:46:15.15). Vrai écart, corrigé par §0.
- g20:41:22 (10/11, base) : un joueur en cours d'arrivée. L'host met son personnage sur sa carte dès l'envoi du
  monde (`SendSaveProbe`, `chara.MoveZone`, `ElinNetHostPlayerManager.cs:247`) et ne l'annonce aux autres qu'une
  fois le joueur chargé (`OnZoneDataReceivedResponse`, `CardGenDelta`), ici 8 s plus tard (玉皇大帝, chargé à
  h20:40:48 = g20:41:22,6). Écart vrai mais passager. Correction proposée dans le détecteur (`Net/NetDesync.cs`, pas
  à moi) : côté host ne pas compter le personnage d'un joueur pas encore placé (`host.IsSettled(peerId)` faux).
- `Card uid conflict` (18, uid 583-591 puis 659-669) : pas un écart. Les objets de départ d'un personnage neuf
  arrivent deux fois : dans les données du personnage, puis un par un. Le second est refusé, c'est le même objet.
- `Dropping CardAddThingDelta … parent uid 529` (8, g20:27:00) : dans la rafale d'une période sans patch ; 529 est un
  contenant porté par un autre joueur. Vrai petit écart (contenu d'un sac d'autrui), cause §0.
- `Dropping WorldStateDeltaList at handshake stage AwaitingIntegrity` (170) / `AwaitingVersion` (8) : messages reçus
  avant la copie du monde, qui les contient : pas une perte. 5 s de ces messages pendant la question du §2.

## Au passage

- `Dropping delta CharaMoveDelta after 7201 failed defer` (41) : pendant que le joueur **créait son personnage**
  (g20:14:25 `Received new player creation request` -> 20:16:37 monde reçu : 2 min 12 s d'écran de création, pas de
  lenteur). Ces messages se remettent en attente à chaque image tant qu'il n'y a pas de carte : 7200 images. Sans
  effet (la copie du monde a les positions).
- `Relay Pick … failed to store, forcing local` (8) : l'objet ramassé n'a pas pu être rangé dans le sac du
  personnage distant chez l'invité, il est posé de force ; lié aux « bags of 1 » du détecteur. Non étudié plus loin.
- `Message of 42 bytes not sent: k_EResultNoConnection` : envoi à un visiteur qui venait de partir (g20:50:25, même
  10 ms que sa déconnexion). Sans effet.

## Pas sûr

- §0 est déduit du code et de la forme du journal (silences, rafales) ; pas reproduit. Le journal de LemiWinks
  (host après 20:38Z) et celui de Nardole le confirmeraient (`Handed zone … while not in it`, puis plus rien).
- Pourquoi l'invité n'était « pas dessus » à g20:48:05 : supposé (sorti de la carte chez lui seul, sans patch) ;
  le journal ne peut pas le montrer.
- L'exception de la reconstruction d'une zone inconnue reste inconnue (maintenant écrite au journal).
- `RemoteClosed` pour fermer le lien : le journal de l'host dira « remote closed », pas « invalid zone ».
- Session de zone sans contrôle des sources : la version du mod reste vérifiée ; pas vu tourner.
