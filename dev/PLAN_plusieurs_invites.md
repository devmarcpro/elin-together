# Plus on est d'invités, plus ça rame et plus il y a de bugs (audit par lecture, 2026-10-06)

Retour de la vraie partie du 6 octobre (l'utilisateur est invité, un ami host, d'autres amis invités) : « J'ai
l'impression que plus on est de joueurs invités plus le jeu galère et plus il y a de bugs. » Le banc n'a presque
jamais joué qu'à deux. Étude par lecture du code seulement : rien n'a été lancé, rien n'a été mesuré.
« non vérifié » = déduit du code, jamais joué ni chronométré. Chemins : `M:` = `ElinTogether/`, `J:` = `dev/_decomp/Elin/`.
Suite de `PLAN_retours_soiree_6_octobre.md` et de `PLAN_invites_tp_sur_host.md` (causes C1 à C6, non répétées ici).

## Résumé
- **Lenteur.** Ce que l'host fait *à chaque image* ne dépend presque pas du nombre de joueurs (l'instantané du monde
  est fabriqué une fois et la même copie part à tous). Ce qui coûte, ce sont des **gels** de l'host, et il y en a un
  par invité et par événement : chaque retour d'un invité sur la carte de l'host = une copie du monde entier + une
  sauvegarde complète ; chaque carte tenue = un envoi de carte entière par minute. À quatre, ces gels s'enchaînent.
- Deux défauts de fond qui grossissent avec le nombre : chaque jeu **recopie la table de toutes les cartes à chaque
  image** (`CardCache.Update`), et chaque jeu ne **lit que 8 messages réseau par image** : un host qui rame prend un
  retard qui ne se rattrape plus.
- **Défauts à trois.** Le voyage indépendant traite le premier invité connecté autrement que les suivants (il tient la
  carte, les autres rechargent), et plusieurs règles sont « tous les joueurs » (sommeil) ou « l'host et un invité »
  (quête à deux). Les échanges, les duels, les numéros de joueur et les numéros d'objets sont, eux, faits pour N (lu).
- Le message « Falling behind » **ne mesure pas la lenteur** (voir A11). Aujourd'hui rien dans le mod ne la mesure.

## A. Lenteur : classement pour une soirée à trois ou quatre

| # | Quoi | Où | Coût selon le nombre d'invités N | Gravité |
|---|---|---|---|---|
| A1 | Retour d'un invité sur la carte de l'host : le monde entier compressé pour lui, puis une sauvegarde complète de l'host, puis la carte entière | `M:Net/Host/ElinNetHostTravel.cs:1144` (`SendSaveProbe`), `:1148-1150` (`game.Save`), `M:Models/SessionState/SaveDataProbe.cs:25`, `M:Models/ZoneState/ZoneDataResponse.cs:41-49` | linéaire : un gel par invité et par retour. **L'host qui revient sur une carte tenue rappelle tout le monde : N copies du monde + N sauvegardes + N cartes à la suite** | 1 |
| A2 | Toutes les cartes connues recopiées à chaque image, dans chaque jeu (`_cards.ToArray()`) | `M:Models/CardCache.cs:207-218`, appelé par `M:Patches/Synchronization/CoreSynchronizationContext.cs:44` | linéaire en objets de la carte + sacs de tous les joueurs et compagnons ; mémoire jetée à chaque image, donc à-coups du ramasse-miettes (non mesuré) | 2 |
| A3 | Lecture du réseau plafonnée à 8 messages par image | `M:Common/EmpConstants.cs:13`, `M:Net/Steam/SteamNetManager/SteamNetManager.cs:76` | linéaire : chaque invité envoie jusqu'à 50 listes + 5 états par seconde ; à 3 invités actifs et un host à 20 images/s (160 lus/s) le retard grandit sans fin. Débit réel des invités non mesuré | 3 |
| A4 | Point de passage toutes les 60 s de chaque invité qui tient une carte : **carte entière** sauvegardée et compressée fort, son personnage, ses compagnons, et le personnage + compagnons de chaque visiteur | invité : `M:Net/Client/ElinNetClientTravel.cs:895-910, 950-970`, `M:Models/ZoneLease/ZoneLeaseState.cs:19-30`, `M:Models/LZ4Bytes.cs:48-52`, `M:Net/Host/ElinNetHostZoneSession.cs:100-124` ; host : `ElinNetHostTravel.cs:1159-1180, 1227-1254` | linéaire : un gel par minute chez le teneur et ses visiteurs, et un par minute et par carte tenue chez l'host (fichiers écrits, personnages relus) | 4 |
| A5 | Le monde de l'host ne s'arrête que si **tous** les joueurs de la carte sont immobiles ; l'avance rapide d'**un** joueur (repos, long travail) accélère le monde pour tous, et les autres jeux suivent | `M:Patches/PauseGame.cs:33-36`, `M:Patches/Synchronization/GameSynchronizationContext.cs:56-61, 73-79, 103-131` | croît puis sature : à 4 il y a presque toujours quelqu'un qui bouge ou se repose. Pas du calcul : c'est « le temps saute » (retour 8) | 5 |
| A6 | Changement de carte de l'host : carte entière envoyée à **tous**, absents compris ; avec le voyage indépendant, N-1 invités rechargent le monde du teneur | `M:Net/Host/ElinNetHostZone.cs:23-33`, `ElinNetHostTravel.cs:181-214, 944-965` | linéaire en envoi, N-1 rechargements par départ de l'host ou du teneur (C1 de l'autre plan) | 6 |
| A7 | Instantané du monde 5 fois par seconde : tous les personnages de la carte, fabriqué une fois, sérialisé une fois, copié à chaque joueur, **absents et joueurs en chargement compris** (ils le décodent puis le jettent) | `M:Models/WorldState/WorldStateSnapshot.cs:39-73`, `M:Net/Host/ElinNetHostUpdate.cs:30-51, 262-272`, `M:Net/Steam/SteamNetPeer/SteamNetPeer.cs:95-99`, `SteamNetPeerBroadcast.cs:34-69`, cibles : `SteamNetManager.cs:207`, tri chez l'invité : `M:Net/Client/ElinNetClientIntegrity.cs:33-40` | calcul constant en N, linéaire en personnages (donc en compagnons) ; réseau linéaire. Chez chaque invité : `map.charas.Contains` par personnage (`M:Models/WorldState/CharaStateSnapshot.cs:137-138`) = personnages² 5 fois par seconde | 7 |
| A8 | Relais : ce qu'un invité fait est appliqué chez l'host puis renvoyé à tous, lui compris et absents compris | ex. `M:Models/Delta/Chara/CharaMoveDelta.cs:72-74`, `ElinNetHostUpdate.cs:56-73, 107-123` | octets en N² (N invités × ce que font les N), une seule sérialisation par envoi. Pas un envoi par destinataire, sauf `SendDeltaTo`/`SendDeltaToAllExcept` (`M:Net/Base/ElinNetBase.cs:137-159` : une sérialisation par joueur, messages rares : discussion, quêtes) | 8 |
| A9 | Temps de combat par joueur : pour chaque personnage en combat, à chaque pas de simulation, recherche de son joueur dans la liste du groupe | `M:Patches/ActionModeCombat.cs:413-426`, `M:Patches/PlayerCombatTime.cs:36-68, 73-98`, `M:Helper/CompanionHelper.cs:54-65` | combattants × taille du groupe (N joueurs + tous leurs compagnons) | 9 |
| A10 | Compagnons de N joueurs dans le seul groupe de l'host : limite d'alliés **par joueur**, donc jusqu'à N × (5 + bonus) ; chaque appel de `Party.Count` reparcourt le groupe ; chaque entrée ou sortie recalcule la vitesse de tous | `M:Patches/CompanionAllyLimitPatch.cs:24-33, 59-67, 86-95`, `CompanionHelper.cs:70-104` | groupe² dans le pire cas ; fréquence des appels du jeu et coût de l'IA du jeu pour N×compagnons : non vérifié | 10 |
| A11 | « Falling behind with {DroppedTicks} dropped ticks » | `M:Net/Client/ElinNetClientUpdate.cs:51-57` | voir sous le tableau | - |
| A12 | Sauvegarde automatique de l'host toutes les 2 min (5 min si elle dure plus de 0,5 s) : gèle l'host et tous ceux de sa carte | `M:Emp/EmpAutoHost.cs:16-19, 105-178` | durée selon la taille du monde (croît avec les joueurs et les cartes visitées), déjà adaptative | 11 |
| A13 | Chaque connexion gèle le jeu qui l'accepte jusqu'à 0,5 s (attente du nom Steam), y compris chez un invité qui reçoit un visiteur | `M:Net/Host/ElinNetHost.cs:153-156` | un gel par arrivée | 12 |
| A14 | Ménages périodiques : grille entière toutes les 2 s, liste des personnages chaque seconde | `ElinNetHostUpdate.cs:160-207`, `ElinNetHost.cs:142-146` | constant, négligeable | - |
| A15 | Combat au tour par tour, vitesse moyenne partagée : **décochés par défaut** (`PlayerCombatTime`, `PlayerClock`, `PlayerStepPace` cochés, `SharedAverageSpeed` décoché, `M:Emp/EmpConfig.cs:106-160`) | `ActionModeCombat.cs:242-294`, `M:Net/Host/ElinNetHostPlayerManager.cs:18-23` | si l'host les coche : la phase « décider » attend chaque joueur **sans limite de temps** (`:268-275`), et un seul joueur qui voit un ennemi met tout le monde au tour par tour (`:247`). `SharedActState` n'est lu nulle part | - |

**A11, « Falling behind ».** L'invité compare le numéro de deux instantanés reçus de suite. S'il en manque, il écrit
la ligne, **et ne fait rien d'autre** (pas de rattrapage, pas de demande d'état complet). Les envois sont fiables : il
n'en manque que quand l'invité les a refusés lui-même (il charge une carte, il est ailleurs). Journal de cette machine
du 6 octobre (banc de test, pas la vraie soirée) : 104 lignes, 40 instantanés manqués en moyenne (8 s), 97 % au-dessus
de 5. Ces lignes comptent donc les **rechargements**, pas la lenteur. Le vrai retard (messages en attente, A3) n'est
écrit nulle part. Après un gel, l'host rattrape ses envois un par image (`M:Net/Base/TickScheduler.cs:21-22`) : petite
rafale, bornée par le moteur (non vérifié).

**Numéros d'objets.** Chaque carte prêtée réserve 50 000 numéros au-dessus du compteur
(`ElinNetHostTravel.cs:889-902`), et le compteur de l'host saute à cette plage dès que l'invité y a créé un objet
(`:1090-1092`). Le plancher ne redescend que si **plus personne** ne tient de carte (`:1095-1097`), rare à trois. Les
numéros « en attente » utilisent le bit 30 (`M:Models/Pending/PendingUid.cs:8`) : vers 21 000 prêts, un vrai numéro
serait pris pour un numéro en attente. Des centaines d'heures de jeu : pas pour cette soirée, à surveiller (non vérifié).

### Les cinq premiers : plus petite amélioration et test
- **A1.** Ne plus sauvegarder à chaque retour : noter « sauvegarde due » et laisser `EmpAutoHost` la faire une fois, au
  calme (il a déjà `_owed` et `CanSave`). ~6 lignes. Risque à dire : si l'host plante entre les deux, la carte rendue
  est plus récente que `game.txt` (c'est la raison écrite à la ligne 1147). La copie du monde, elle, reste due à chaque
  retour (le jeu de l'invité repart d'elle) : ne pas y toucher sans mesure. Test : **deux fenêtres** pour un retour
  (durée du gel de l'host avant et après) ; **trois fenêtres** pour le cas « l'host revient, deux invités rappelés ».
- **A2.** Faire ce ménage une fois par seconde au lieu de chaque image, sans copie (liste des numéros morts réutilisée).
  3 lignes. Test : **deux fenêtres**, mesure du temps par image et du nombre de passages du ramasse-miettes, avant et après.
- **A3.** Lire le réseau en boucle tant que le lot revient plein, avec une limite de temps par image (4 ms). 5 lignes
  dans `Poll`. Test : **deux fenêtres** en bridant l'host (`Application.targetFrameRate = 10` par `eval`) pendant que
  l'invité marche : délai entre le pas chez l'invité et le pas vu chez l'host, qui ne doit plus grandir ; **trois
  fenêtres** pour le cas réel sans bride.
- **A4.** Point de passage sans la carte deux fois sur trois (le personnage et les compagnons, eux, à chaque fois : c'est
  ce qu'un plantage ferait perdre), ou compression rapide pour les points de passage. ~8 lignes. Test : **deux
  fenêtres** (l'invité tient Vernis : pic du temps par image chez lui et chez l'host à chaque point) ; **trois** pour
  le coût des visiteurs.
- **A5.** Choix de conception, donc une case à cocher côté host et l'avis de l'utilisateur d'abord : l'avance rapide
  d'un joueur n'accélère le monde que si aucun autre joueur de la carte n'agit. ~6 lignes dans `ShouldRemoteTurbo`.
  Test : **deux fenêtres** (l'invité se repose, l'host marche : la date de l'host ne doit pas accélérer) ; **trois**
  pour vérifier que le troisième n'est pas entraîné.
- Ensuite, sans risque : retirer les absents des cibles de diffusion (A7, A8, ~6 lignes : `RemoveTarget` au départ,
  `AddTarget` au retour ; attention, ils doivent encore recevoir discussion, quêtes et date, envoyées dans les mêmes
  listes : à séparer d'abord).

## B. Défauts qui n'existent qu'à trois joueurs ou plus : classement

| # | Défaut | Où | État |
|---|---|---|---|
| B1 | Le deuxième invité et les suivants rechargent la carte et atterrissent sur l'host ou sur le teneur à chaque changement de carte de l'host ou du teneur | C1 de `PLAN_invites_tp_sur_host.md` | écrit (retour 7), `trio_place_suite.py` à lancer |
| B2 | L'invité « pas encore installé » est emmené par l'host. À trois, l'host sert les copies du monde l'une après l'autre (A1) : les suivants attendent plus longtemps, donc sont emmenés plus souvent ; `_settled.Clear()` vide la liste à chaque départ | `ElinNetHostTravel.cs:165-170`, C2 de l'autre plan | pas écrit ; aggravation à trois non vérifiée |
| B3 | Sommeil : il faut que **tous** les joueurs vivants de la carte soient couchés, et la nuit ne passe que par le sommeil de celui qui simule la carte (l'host, ou l'invité teneur). À quatre, un seul joueur qui ne veut pas dormir bloque les trois autres, sans limite de temps ni majorité | `M:Patches/Synchronization/SleepSynchronizationContext.cs:45-60, 192-199, 257` | pas écrit, choix de conception |
| B4 | Quête à deux (« Go along? ») : un seul état chez l'host (`_questAsk`, `_accompanied`, `_lastQuestAsked`). La question n'est posée qu'à l'host ; un invité B à côté de l'invité A n'est jamais invité et **n'a aucun moyen de suivre A** (la carte de quête d'A n'est pas annoncée aux autres). Quand c'est l'host qui part en quête, seul le **teneur** de la ville est invité, pas ses visiteurs | `ElinNetHostTravel.cs:239-253, 264-278, 322-353, 1425-1455` | pas écrit |
| B5 | Carte du monde : chaque invité y a sa propre copie. Deux invités ne s'y voient jamais ; avec l'host, si | `ElinNetHostTravel.cs:183-199, 1494-1497` | voulu à l'origine, inégalité host/invité |
| B6 | L'ordre de connexion décide qui tient la carte : le premier connecté ne recharge jamais et simule pour les autres, même si son PC ou sa ligne est le plus faible | `ElinNetHostTravel.cs:168-184, 945` | pas écrit |
| B7 | Visiteur d'un autre invité : ce qui lui manque (liste sous le tableau) | `M:Net/Host/ElinNetHostZoneSession.cs` et les `IsZoneSession` | pas écrit |
| B8 | Temps de combat : un monstre agit sur les tours du joueur qu'il vise. À trois, B frappe sans risque le monstre qui vise A pendant qu'A réfléchit | `PlayerCombatTime.cs:45-53` | choix de conception, existe à deux, grandit avec N |
| B9 | Message « pour ce joueur » perdu si le personnage n'est plus dans la table des joueurs présents : le numéro 0 est pris pour l'host | `M:Patches/Synchronization/MsgRelayContext.cs:16-26`, `ElinNetHostTravel.cs:616` | rare, pas propre à trois |

**B7, visiteur d'un invité : ce qu'il n'a pas, comparé à un invité chez l'host** (lu dans le code, non joué) :
- la gestion de la base : sa demande est ignorée par un teneur (`M:Models/Delta/Zone/BaseRequestDelta.cs:130`), les
  habitants et les achats de la base aussi (`M:Patches/Remote/RemoteResidentPatch.cs:29`, `RemoteBasePaidPatch.cs:157, 238`) ;
- les quêtes à deux : aucune invitation ni question dans une session de carte (`M:Models/Delta/Quest/QuestFollowDelta.cs:83-99`) ;
- le journal des quêtes personnelles n'est pas tenu par le teneur (`M:Net/Host/ElinNetHostPersonalQuests.cs:74, 126, 150,
  163, 189, 234, 295, 323`) : prendre ou rendre une quête d'habitant en visite, non vérifié ;
- la liste des joueurs de l'host (`ElinNetClientTravel.cs:988`) : il ne voit que ceux de sa carte ;
- la sécurité : son personnage ne vit que dans le jeu du teneur, qui n'a pas de sauvegarde. Si le **teneur** plante, il
  perd jusqu'à 60 s et reprend sur une case ancienne (`ElinNetHostTravel.cs:1007`, `ElinNetHostZoneSession.cs:164-179`
  ne couvre que le plantage du visiteur) ; la reconnexion automatique ne vaut que pour le lien avec l'host
  (`M:Net/NetReconnect.cs:30`) ;
- le ménage de l'ancien personnage (retour 6) n'existe pas chez un teneur seul.

**Lu et trouvé correct pour N** : échanges et duels (une liste de séances par paire, refus si l'un des deux est pris,
`M:Helper/PlayerTrade.cs:35, 358`, `M:Helper/PlayerDuel.cs:39, 287`) ; numéros de joueur (un par compte Steam, gardé,
`SteamNetPeer.cs:21-53`) ; numéros d'objets en attente (6 bits de joueur, `PendingUid.cs:25-34`) et plages par carte
prêtée ; « tout pour chaque invité » au sommeil (`SleepSynchronizationContext.cs:308-355, 404-408`) ; aucun `First()`,
`Single()` ou `Peers[0]` sur les joueurs (`Socket.FirstPeer` est le lien de l'invité vers son host, un seul par lien).

### Les cinq premiers : plus petite correction et test
- **B1.** Déjà écrit. Test : `trio_place_suite.py` Q1 à Q3, **trois fenêtres** obligatoires.
- **B2.** Compter comme installé un invité dont le personnage se tient déjà sur la carte quand l'host part (C2 de
  l'autre plan) ; avec A1 l'attente raccourcit d'elle-même. Test de base à **deux fenêtres** (`travel_suite`) ; **trois**
  pour le cas « deux invités reviennent ensemble, l'host repart dans les 5 s ».
- **B3.** À décider avec l'utilisateur (case à cocher) : la nuit passe quand la majorité est couchée depuis 30 s, les
  autres restent éveillés. Sans décision : au moins dire à l'écran **qui** on attend. Test : **trois fenêtres** (deux
  couchés, un debout) ; à deux fenêtres on ne peut jouer que « l'host ne dort pas ».
- **B4.** Inviter aussi les visiteurs de la ville : dans `InviteToQuestZone`, ajouter les joueurs de `_guests` dont la
  carte est celle de la quête. 3 lignes. Laisser B suivre A sans l'host : plus gros, à voir. Test : **trois fenêtres**
  (host + A teneur + B visiteur à Vernis, l'host prend une chasse : B doit recevoir la question).
- **B5/B7.** D'abord la base : faire suivre la demande du visiteur au teneur comme elle l'est à l'host. À étudier
  avant d'écrire (non vérifié). Test : **trois fenêtres** (A tient la base, B la visite, B lance une recherche).

## Ce que `trio_suite.py` couvre, et ce qu'une suite à trois doit vérifier d'abord
- `trio_suite.py` : **quatre fenêtres** (host + 3 clients, `mp_test.py --clients 3`), donc au-delà de l'accord donné
  (trois). T1 à T5 : qui tient Vernis et qui est visiteur après chaque départ, retour, plantage ; un objet posé vu par
  les autres ; un pas vu par les autres. Jamais : la case des joueurs, les compagnons, le temps, le sommeil, les quêtes,
  le combat, la durée des chargements. Pas relancée depuis la 0.26.442. T1 à T4 se portent à deux clients ; T5 non.
- `trio_place_suite.py` (cases, C1 et C3) et `trio_time_suite.py` (date et nourriture) : trois fenêtres, écrites, à lancer.
- Une suite à trois (`mp_test.py --clients 2`) doit vérifier en premier, dans cet ordre :
  1. après chaque passation, les deux invités voient le même monde : mêmes personnages, mêmes cases, même date ;
  2. les compagnons de B (le visiteur) restent à B et à côté de B après un départ et un retour de l'host ;
  3. l'host revient : durée du gel de l'host et durée de l'écran de chargement de chaque invité (A1) ;
  4. sommeil à trois : deux couchés, un debout ; puis trois couchés ;
  5. deux invités créent des objets en même temps (artisanat, ramassage) pendant que l'host en crée : aucun doublon,
     aucun « Card uid conflict » dans les journaux ;
  6. l'host prend une quête depuis une ville tenue par A et visitée par B (B4) ;
  7. A tient une carte, B le visite, A plante : B garde son personnage et son sac.

## Mesurer la lenteur au banc
Aujourd'hui le mod ne mesure rien : ni temps par image, ni messages en attente. Le pont de test répond à `state`
(`M:Emp/EmpDebugListener.cs:246`) : c'est là qu'il faut lire la mesure.
- **À ajouter dans le mod (build Debug seulement, ~40 lignes)** : un objet `perf` dans `state`, remis à zéro à chaque
  lecture : temps par image moyen et maximum (`Time.unscaledDeltaTime`), nombre de passages du ramasse-miettes
  (`GC.CollectionCount(0)`), messages reçus et nombre d'images où le lot de 8 est revenu plein (`SteamNetManager.Poll`),
  listes en attente (`ElinDeltaManager.GetCounts`, `:241`), octets par seconde par joueur (déjà calculés :
  `SteamNetPeer.Stat.AvgBpsOut/In`, `:169-175`), et la durée + la taille du dernier `SaveDataProbe`, de la dernière
  `ZoneDataResponse`, du dernier point de passage et de la dernière sauvegarde (un chronomètre autour de chaque).
- **Sans recompiler, pour un premier chiffre** : le pont sait charger un script (`load`, `EmpDebugListener.cs:205`) ;
  un petit script qui note `Time.unscaledDeltaTime` à chaque image suffit pour le temps par image (non vérifié qu'un
  script chargé ainsi peut tourner à chaque image).
- **Commande à ajouter** : `python _tools/perf_suite.py`. Pour 0, 1 puis 2 clients (`mp_test.py --clients n`, même
  sauvegarde, même carte) : 30 s tout le monde immobile, 30 s tout le monde en marche (les déplacements de
  `travel_suite.move`), puis un aller-retour d'un invité à Vernis ; lecture de `state.perf` chaque seconde sur chaque
  port ; un tableau à la fin : temps par image moyen et maximum de l'host, lots pleins, octets par seconde, durée de
  chaque gel. Trois lignes à comparer (1, 2, 3 joueurs) : si le temps par image moyen ne bouge pas mais que le maximum
  grimpe, ce sont les gels (A1, A4, A12) ; si la moyenne grimpe, c'est A2, A7 ou A9 ; si les lots pleins apparaissent, A3.
- Trois fenêtres sur ce PC faussent un peu la mesure (elles se partagent le processeur) : comparer les lignes entre
  elles, pas avec une vraie partie.

## Questions pour l'utilisateur
1. « Le jeu galère » : des **arrêts** d'une ou plusieurs secondes de temps en temps (quand quelqu'un change de carte, ou
   toutes les minutes), ou tout est **mou en continu** (les pas des autres en retard, les actions qui tardent) ?
2. C'était pire chez l'host ou chez les invités ? Et pire quand tout le monde était sur la même carte, ou dispersé ?
3. Sommeil à plusieurs : attendre tout le monde, ou la majorité suffit ?
