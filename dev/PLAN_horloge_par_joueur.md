# Plan : une horloge par joueur (faits pour le conseil)

2026-10-06. Lecture seule du code, rien compilé, rien joué. Ce qui n'a pas été lu ou joué est marqué
**non vérifié**. Chemins du jeu : `dev/_decomp/Elin/`. Chemins du mod : `ElinTogether/` (le dossier du code).

Retour de la partie réelle (0.26.506, trois joueurs ou plus, l'utilisateur est invité) : « l'hôte revient à la
base et le temps des invités saute, un invité meurt de faim d'un coup et sa nourriture pourrit ; il faudrait que
les joueurs gardent leurs propres horloges ».

## 0. En trois phrases
- Aujourd'hui le monde a **une seule date : la plus avancée** (`SharedWorldTime`, cochée par défaut). Chaque pas
  d'un joueur sur la carte du monde coûte **3 heures** ; ces 3 heures sont ensuite **vécues par tous les autres**,
  où qu'ils soient : 120 tours de faim et de conditions d'un coup, et 3 heures de pourriture dans le sac.
- C'est voulu par le code et même vérifié par un test (`time_suite.py` W3 : « son personnage a plus faim »).
  Ce n'est donc pas un bug isolé : c'est la règle « tout le monde vit le temps des autres » qu'il faut changer.
- La branche `wip/player-clock` ne traite pas ce sujet : elle règle la **cadence des pas** (temps réel), elle est
  déjà fusionnée (`48930ce`). Rien n'existe encore pour « la date ne me fait pas vieillir si je ne l'ai pas jouée ».

## 1. Le jeu en solo
### Comment le temps avance
- Minute par minute : `GameUpdater.cs:527-538`, une minute chaque `secsPerHour / 60` secondes de `Core.gameDelta`
  (valeur de `secsPerHour` : **non vérifié**, réglage du jeu). Le temps ne passe que quand le joueur agit :
  constaté en jeu dans `MODLOG.md:1408-1410` (11 pas ≈ 7 minutes ; aucun temps si le joueur ne joue pas).
- `GameDate.AdvanceMin` (`GameDate.cs:24-90`) : compteurs du joueur, traces de pas, effets de zone, événements de
  zone ; à chaque heure pleine appelle `AdvanceHour`.
- `GameDate.AdvanceHour` (`GameDate.cs:92-168`) : une heure « en temps réel » pour la carte active
  (`VirtualDate.SimulateHour`, `IsRealTime = true`), puis météo (`:113`), `Player.OnAdvanceHour` (`:114`), quêtes
  expirées (`:115`), aventuriers du monde (`:125-140`), et à 5 h : expédition, colis, lettres (`:142-150`).
- `AdvanceDay` (`GameDate.cs:170-273`) : compteur de jours, coût de relance des quêtes, prière du jour, relations,
  faction (`:198`), aventuriers, quêtes d'histoire à date fixe, colis d'anniversaire. `AdvanceMonth` (`:275-298`) :
  impôts et salaires par `Faction.OnAdvanceMonth`, saison des tuiles. `AdvanceYear` (`:300-307`).
- `Player.OnAdvanceHour` (`Player.cs:2467-2485`) : foi, identification, 1 point d'expérience au groupe une heure
  sur deux. `Player.OnAdvanceDay` (`Player.cs:2487-2506`) : jours avec le dieu, prière et pêche remises à zéro, karma.
### Ce que coûte un pas
- **Carte du monde** (`Chara.cs:2984-3034`) : base 30, plus pluie/neige (+5 à +15), plus sol 48 (+20), divisé par
  le talent de voyage ; la date avance de `30 × 6 = 180` minutes (`:3013`) et **chaque membre du groupe joue
  `30 × 4 = 120` tours de conditions** (`:3017-3025`). Le jeu arrête la marche si la vie tombe sous 1/5 (`:3026-3032`).
- **En ville** : un tour = un `TickConditions` ; la date avance en temps réel (ci-dessus), pas par pas.
- **Sommeil** : `LayerSleep.cs:52-106`, la date avance par bonds de 10 minutes ; au réveil `Chara.OnSleep`
  donne +20 de faim (`Chara.cs:10431-10434`). Voyage express : `LayerTravel.cs:161` appelle `AdvanceHour` directement.
### Ce que le temps fait au joueur et à ses affaires
- **Faim et sommeil** : dans `Chara.TickConditions` (`Chara.cs:3942-4100`), tous les 50 tours : +1 sommeil une
  fois sur deux, **+1 faim une fois sur trois** (`:3965-3986`), soit environ 0,8 de faim par pas de carte du monde.
  Phase « affamé » (5) : une fois sur cinq par tour, dégâts `1 + 0..1 + vie max / 50` (`:4089-4094`), et plus de
  régénération dès la phase 4 (`:4060-4062`). Donc **120 tours d'un coup à « affamé » ≈ 24 coups ≈ la moitié de
  la vie ; 240 tours tuent**. Seuils des phases : dixièmes du maximum (`Stats.cs:117-120`), table **non vérifiée**.
- **Conditions** (poison, saignement, brûlure, mouillé, durées, recharges) : comptées en tours, dans le même
  `TickConditions`. Elles ne dépendent pas de la date.
- **Pourriture** : `Card.DecayNatural` (`Card.cs:7086-7107`) puis `Card.Decay` (`:7118-7199`), `MaxDecay` 1000
  (`Card.cs:2355`). À chaque heure réelle : `Zone.OnSimulateHour` (`Zone.cs:3629-3682`) fait vieillir **le sac du
  joueur local seulement** (`:3645`) et tout ce qui est posé sur la carte, coffres compris, contenu compris
  (`:3647-3650`, `Card.cs:7077-7084`). Les sacs des autres personnages ne vieillissent jamais en solo.
  Le bonus « tout juste cuit » compare à la **date du monde** (`Card.cs:7109-7116`).
- **Réassort des marchands** : `c_dateStockExpire` comparé à la date du monde (`Trait.cs:1698-1723`).
### Le rattrapage au retour sur une carte
- `Zone.OnVisit` (`Zone.cs:1146-1200`) appelle `Zone.Simulate` (`Zone.cs:1304-1445…`) puis pose
  `lastActive = date` (`:1195`). Pas de rattrapage sur la carte du monde ni si moins de 2 heures (`:1348`, `:1363`).
- Qui le subit : **les personnages de la carte hors groupe du joueur** (repos, sommeil, et **sac vidé au-delà de
  20 objets** après un jour, `:1379-1399`) ; **tous les objets posés et le contenu des coffres** vieillissent de
  toutes les heures passées en une fois (`:1417-1420`) ; chaque heure simulée : la base (`branch.OnSimulateHour`),
  réapparition des monstres, pluie, **pousse des cultures à 6 h** (`Zone.cs:3629-3682`) ; par jour et par mois :
  la base (`:3684-3702`). **Le sac du joueur et son groupe ne subissent rien** au rattrapage (`:1321`, `:1383`).

## 2. Le mod aujourd'hui
### Qui fait avancer la date
- `GameDate.AdvanceMin` ne tourne que dans un jeu « qui simule » : l'host, et un joueur seul sur une carte qu'il
  tient (`Patches/DeltaEvents/World/WorldDateAdvanceEvent.cs:15-19` ; `Net/NetSession.cs:40`, `:61`, `:84`).
  Un invité sur la carte de l'host ne fait jamais avancer la date.
- L'host envoie chaque avance à tous (`WorldDateAdvanceEvent.cs:33-41`, `WorldDateAdvanceDelta`), y compris aux
  joueurs partis ailleurs (`Net/Client/ElinNetClientTravel.cs:937`).
- **Une seule date** (`UseSharedWorldTime`, `Net/NetSessionRules.cs:70-75`, case `SharedWorldTime` cochée par
  défaut, commit `a76d6a9`) : un joueur qui tient une carte dit sa date à l'host (`WorldDateAdvanceEvent.cs:26-31`,
  `Models/Delta/World/WorldTimeReportDelta.cs:18-25`) ; l'host **rattrape** (`CatchUp`, `:64-84`) et le redit à
  tous. Garde-fou : pas plus d'un mois d'un coup (`:13`, `:67`).
- **Gardien du monde** (`UseWorldKeeper`, `Patches/WorldKeeper.cs:17-91`, cochée par défaut) : météo, quêtes
  expirées, sites, jour, faction (jour et mois), lettres, colis ne sont faits que par l'host.
- `UseSharedSpeed` (`Patches/Synchronization/GameSynchronizationContext.cs:90-100`), `UsePlayerCombatTime`,
  `UsePlayerClock`, `UsePlayerStepPace` (`NetSessionRules.cs:29-68`) : vitesse et durée d'un tour, pas la date.
### Ce qu'un saut de date fait à chaque joueur (trois chemins)
1. **Invité sur la carte de l'host** (`Models/Delta/World/WorldDateAdvanceDelta.cs:18-93`) : la date est posée,
   puis `pc.TickConditions()` est joué `Minutes × 4 / 6` fois, **sans plafond** (`:50-57`), puis les crochets
   d'heure (au plus 24) et de jour (au plus 3) du joueur (`:60-78`, commit `194c6d7`). Ce calcul tourne **chez
   l'invité**. Son sac vieillit **chez l'host**, une fois par heure réelle, puis l'état lui est envoyé
   (`Patches/Remote/RemoteDecayPatch.cs:11-30`, `Models/Delta/Card/CardDecayDelta.cs`, `MODLOG.md:2241`).
2. **Invité qui tient une carte** (resté seul, ou premier resté quand l'host est parti :
   `Net/Host/ElinNetHostTravel.cs:152-215`) : il reçoit la date de l'host, et son jeu fait
   `AdvanceMin(retard)` (`WorldDateAdvanceEvent.cs:73`) : toutes les heures passent « en temps réel » sur sa carte,
   donc **son sac vieillit** (`Zone.cs:3645`), les objets posés aussi, la base tourne ; puis son personnage joue
   `min(retard, un jour) × 4 / 6` tours (`:76-81`). Tout tourne **chez l'invité**. Le plafond d'un jour vaut par
   appel : l'host qui fait 10 pas envoie 10 sauts de 3 heures, donc 1 200 tours, sans que le plafond serve.
3. **Invité en visite chez un autre invité** (troisième joueur) : `WorldDateAdvanceDelta.cs:26-32` ne fait rien
   pour lui (il est « ailleurs » et ne tient pas la carte) ; sa date lui vient de l'instantané du monde
   (`Models/WorldState/WorldStateSnapshot.cs:84`). Pas de tours de faim. Mais son sac vieillit dans le jeu de celui
   qui tient la carte, heure par heure pendant le rattrapage (`RemoteDecayPatch.cs:17-30`). **Jamais joué**
   (`DOCUMENTATION.md:458-460` : trois joueurs, carte tenue avec visiteurs : pas testé).
### Le cas rapporté, pas à pas
1. L'host quitte la carte ; les invités y restent : le premier la tient, les autres sont ses visiteurs
   (`ElinNetHostTravel.cs:181-214`).
2. L'host marche sur la carte du monde : **chaque pas** fait `AdvanceMin(180)` dans son jeu (`Chara.cs:3013`,
   `Patches/Remote/RemoteTravelRegionPatch.cs:24-30`) et part vers tous.
3. L'invité qui tient la carte : chemin 2. Par pas de l'host : 3 heures de pourriture dans son sac, 120 tours de
   faim et de conditions. Dix pas : 30 heures, 1 200 tours (environ +8 de faim ; s'il était déjà « affamé » ou
   empoisonné, il meurt). Les visiteurs : chemin 3 (sac seulement).
4. L'host entre sur leur carte : la carte lui revient ; `lastActive` est remis à la date du moment
   (`ElinNetHostTravel.cs:1244-1245`), donc **pas de rattrapage de carte** à ce moment-là.
- Ce qui n'est **pas vérifié** : lequel des chemins a tué le joueur dans la vraie partie (pas de journal lu),
  ni si le saut a été vu « au retour » parce que les messages arrivaient en rafale. Par le code, les sauts
  arrivent pendant tout le voyage de l'host, pas seulement à son arrivée.
- Même chose dans l'autre sens : un invité qui voyage seul sur la carte du monde fait vivre 3 heures par pas à
  l'host (chemin `CatchUp`) et à tous les joueurs de la carte de l'host (chemin 1, sans plafond).
- Inégalité vue en passant : sur la carte du monde **avec** l'host, le pas d'un invité ne coûte ni temps ni
  faim (`RemoteTravelRegionPatch.cs:29` : le bloc ne tourne que chez celui qui simule) ; il paie les pas de l'host.
### Ce qui existe déjà
- `wip/player-clock` : deux commits, `5d69faf` (« WIP, never run », le client garde son horloge **temps réel**
  pour ses pas : `GameSynchronizationContext.cs`, `NetSessionRules.cs`, `move_suite.py`) et `5584c51`
  (`PlayerStepPace`). **Déjà fusionnée** dans la branche de travail (`48930ce`, `MODLOG.md:1277-1282`), puis
  l'accéléré partagé (`6af7ffa`). Elle ne contient rien sur la date, la faim ou la pourriture.
- `a76d6a9` une seule date ; `1b0f5c3`, `856d878` gardien du monde ; `194c6d7` jours et heures de l'invité ;
  ligne 6 de `PLAN_chasse_differences_2.md:34` : sac de l'invité qui vieillit (`hunt2_suite` E3).
- Délais de quêtes : déjà recalés d'une horloge à l'autre (`QuestStartDelta.cs:171`,
  `Helper/PersonalQuests.cs:326-334`) ; les quêtes personnelles expirent sur la date du jeu du joueur (`:170-174`),
  donc **elles expirent aussi par les sauts des autres**.
- Attention : changements non commités d'une autre session (sommeil, `SleepSynchronizationContext.cs`).

## 3. Ce qui est au monde, ce qui est au joueur

| Lié à la date du monde (une décision est nécessaire pour le rendre personnel) | Où |
|---|---|
| Saison, jour et nuit affichés, neige sur les tuiles | `Date.cs:111-191`, `GameDate.cs:289` |
| Météo | `GameDate.cs:113`, gardien |
| Pousse des cultures, pluie, réapparition des monstres | `Zone.cs:3656-3681` |
| Base : travail des habitants, recherches, ressources, impôts, salaires | `FactionBranch.cs:318`, `:598`, `:680`, `GameDate.cs:198`, `:297` |
| Expédition, colis, lettres | `GameDate.cs:142-150`, `309` |
| Réassort des marchands | `Trait.cs:1698-1723` |
| Cartes qui expirent, se régénèrent, renaissent | `Zone.cs:648`, `:703`, `:732`, `:1001`, `:1148` |
| Rattrapage d'une carte (`lastActive`) | `Zone.cs:1304`, `Spatial.cs:117` |
| Quêtes d'histoire à date fixe, aventuriers, anniversaires de mariage | `GameDate.cs:199-272` |
| Objets posés et contenu des coffres | `Zone.cs:3647`, `:1417` |

| Personnel (peut suivre le temps joué par le joueur) | Où |
|---|---|
| Faim, sommeil, conditions, recharges, vampirisme, soleil | `Chara.cs:3942-4100` (en tours) |
| Pourriture de **son** sac | `Zone.cs:3645`, `RemoteDecayPatch.cs` |
| Compteurs de jours, relance des quêtes, prière du jour, pêche, jours avec le dieu | `GameDate.cs:173-193`, `Player.cs:2487` |
| Délais de ses quêtes aléatoires | `Quest.cs:339`, `PersonalQuests.cs:170` |
| Bonus « tout juste cuit » (aujourd'hui lié à la date) | `Card.cs:7109` |

Âge des habitants et événements saisonniers : **non vérifié** (pas lus).
## 4. Conceptions possibles

Cas de référence : R = le cas rapporté (host voyage, invités restés) ; S = un joueur dort ; V = un joueur voyage
seul ; T = tous ensemble en ville.
### (a) Date commune, vie personnelle au temps joué
- Idée : la date reste unique. Un joueur ne joue des tours de faim et de conditions que pour ses propres tours.
  Son sac ne vieillit que des heures que **son** jeu a vécues (minute par minute sur sa carte, son sommeil, ses
  propres pas de carte du monde), comptées dans un compteur « minutes vécues » porté par le personnage.
- R : la date des invités suit, il fait nuit plus tôt, rien d'autre ne leur arrive. S : le dormeur vit sa nuit,
  les autres voient l'heure changer. V : le voyageur paie ses pas, comme en solo. T : rien ne change.
- À écrire : `WorldDateAdvanceEvent.cs`, `WorldDateAdvanceDelta.cs`, `RemoteDecayPatch.cs`, un petit compteur
  (un entier sur le personnage), `Zone.OnSimulateHour` pour le sac local. Ordre : 150 à 250 lignes, une case host.
- Pertes et abus : la nourriture d'un joueur immobile ne pourrit pas (comme en solo : sans action, pas de temps) ;
  on peut « mettre au frais » de la nourriture dans le sac d'un joueur qui joue peu pendant que la date file ;
  un coffre de la base suit la date, un sac non. « Tout juste cuit » s'éteint à la date du monde. Les quêtes
  personnelles expirent encore par les sauts des autres (à traiter à part, voir questions).
- Sauvegardes : un entier de plus par personnage, rien à convertir. Test : celui de la section 5, étendu.
### (b) (a) plus le rattrapage borné pour ce qui appartient à un joueur présent
- Idée : sur une carte où un joueur est présent, un saut causé par un autre ne fait pas tourner les heures
  « en temps réel » : objets posés, coffres, base, cultures ne prennent que le temps vécu sur place ; le reste
  du saut est dû plus tard, par le rattrapage normal du jeu quand la carte est quittée puis revisitée.
- R : la viande posée sur la table de la base ne pourrit pas parce que l'host marche ; les cultures ne sautent
  pas trois jours sous les yeux du joueur. S, V, T : comme (a).
- À écrire : (a), plus séparer « poser la date » de « simuler la carte » dans `CatchUp`, plus une dette d'heures
  par carte (le jeu a déjà `pendingSimHours`, `Zone.cs:1352-1371`). Ordre : 400 à 600 lignes.
- Pertes et abus : une base toujours habitée par un joueur immobile produit moins (elle ne vit que le temps de ce
  joueur) ; à l'inverse la dette rendue d'un coup refait un saut pour celui qui revient. Qui « possède » un objet
  posé n'est pas écrit dans le jeu.
- Sauvegardes : la dette par carte doit être sauvée (**non vérifié** que le champ du jeu l'est).
- Test : viande posée au sol chez l'invité, saut chez l'host, âge inchangé ; il sort et rentre : heures dues prises.
### (c) Une date par joueur, le monde montré à chacun selon la sienne
- Idée : chaque jeu garde sa date ; les choses communes suivent la date du gardien ; tout ce qui porte une date
  (délais, réassort, expiration des cartes, `lastActive`, cuisson) est converti à chaque passage d'un jeu à l'autre.
- R, S, V : personne ne voit jamais la date sauter. T : deux joueurs côte à côte peuvent être l'un de jour,
  l'autre de nuit, l'un en hiver, l'autre en été : la neige et les cultures sont dans la carte, il faut quand
  même une règle commune dès qu'ils sont ensemble.
- À écrire : presque tout ce qui lit la date (46 lignes rien que dans le mod), les transferts de
  carte, les quêtes, les marchands, le gardien. Ordre : 1 500 lignes et plus, plusieurs semaines.
- Pertes et abus : acheter chez un marchand « réassorti » pour l'un et pas pour l'autre, quêtes à durée
  différente, doublons à chaque conversion ratée.
- Sauvegardes : risque fort (dates de la sauvegarde de l'host à réinterpréter, décalage par personnage au dépôt).
  Test : une suite entière à écrire ; `time_suite` W1 à W4 deviennent faux par définition.
### (d) La date n'avance qu'au rythme du plus lent (ou à la moyenne)
- Idée : un saut (pas de carte du monde, nuit) n'est accordé que si tous l'ont « payé » ; sinon le joueur paie
  ses tours mais la date attend.
- R : pas de saut pour les invités. S : la nuit ne passe que si tous dorment. V : le voyageur a faim comme en
  solo mais arrive « à la même heure ». T : comme aujourd'hui.
- À écrire : `WorldDateAdvanceEvent.cs`, un compteur par joueur chez l'host, le sommeil. Ordre : 300 lignes.
- Pertes et abus : dans Elin un joueur qui ne fait rien ne fait pas passer le temps ; **un joueur absent du
  clavier gèle la date du monde** (cultures, marchands, délais). Avec la moyenne : le saut existe encore, divisé.
- Sauvegardes : aucun risque. Test : `time_suite` W3 inversé (l'host ne saute pas tant que l'invité n'a pas joué).
### (e) Le voyage sur la carte du monde ne fait plus avancer la date quand d'autres sont ailleurs
- Idée : le pas coûte toujours ses 120 tours au voyageur et à son groupe, mais la date n'avance pas de 3 heures
  (ou seulement de quelques minutes) s'il y a des joueurs sur d'autres cartes.
- R : plus de saut pendant le voyage de l'host. S : inchangé (une nuit saute encore pour tous). V : pareil pour
  un invité qui voyage. T : inchangé.
- À écrire : `RemoteTravelRegionPatch.cs` et une garde. Ordre : 30 à 60 lignes, une case host.
- Pertes et abus : voyager ne consomme plus les délais de quêtes, ne fait plus pousser, ne réassortit plus ;
  la nourriture du voyageur ne vieillit plus en route (sauf avec le compteur de (a)). Le sommeil reste une source
  de sauts : (e) seule ne suffit pas, elle réduit surtout l'écart de date.
- Sauvegardes : aucun risque. Test : 5 pas de l'host, la date de l'invité bouge de moins de 15 minutes.

Combinaisons qui tiennent : urgence seule ; urgence puis (a) ; (a) + (e) ; (a) puis (b). (c) et (d) remplacent
le reste.

## 5. Correction d'urgence (tient quelle que soit la suite)

Règle : **le temps qu'un autre joueur a fait passer change la date, pas mon personnage ni mon sac.**

- Un drapeau « rattrapage en cours » posé autour de `AdvanceMin(behind)` dans `WorldDateAdvanceEvent.CatchUp`
  (`:64-84`), et un champ de plus dans `WorldDateAdvanceDelta` (« ces minutes sont un rattrapage ») rempli par
  l'host quand il rattrape la date d'un autre.
- Pendant un rattrapage : pas de boucle `pc.TickConditions` (`WorldDateAdvanceEvent.cs:78-81`,
  `WorldDateAdvanceDelta.cs:50-57`) ; pas de vieillissement des sacs des joueurs : sac local (`Zone.cs:3645`, par
  un préfixe sur `Card.DecayNatural` quand la carte est un joueur) et sacs des autres (`RemoteDecayPatch.cs`).
- En plus, par sécurité : plafonner la boucle de `WorldDateAdvanceDelta.cs:50` (elle n'a aucun plafond).
- On garde : la date commune, les crochets d'heure et de jour, la carte qui vit ses heures, le gardien.
  Ordre : 40 à 80 lignes, quatre fichiers, une case host cochée par défaut (règle de `CLAUDE.md`).
- Ce que l'urgence ne règle pas : le saut de l'host subi par un invité **sur la même carte que lui** (carte du
  monde à deux, nuit de l'host), les objets posés, les délais de quêtes : c'est le choix de conception.

Test rouge puis vert, à deux fenêtres (`time_suite.py`, nouvelle étape W6, sur le modèle de W2 et de `hunt2` E3) :
1. L'invité part seul à Vernis (il tient la carte), reçoit une viande fraîche (`decay = 0`), on note `pc.turn`,
   `pc.hunger.value`, `pc.hp`.
2. L'host, chez lui, fait huit fois `EClass.world.date.AdvanceMin(180)` (ce que font huit pas sur la carte du
   monde ; variante lente : huit vrais pas).
3. Attendu : les deux dates sont égales (`gap() == 0`) ; chez l'invité `pc.turn` n'a pas bougé de plus de
   quelques tours, la viande a `decay == 0`, la faim n'a pas monté. **Rouge aujourd'hui** : `turn` +960, viande
   vieillie de 24 heures.
4. Variante mortelle : `pc.hunger.value` posé à la phase 5 avant le saut ; attendu : `pc.hp` inchangé, vivant.
   Rouge aujourd'hui : mort ou presque.
5. Témoin : l'invité marche jusqu'à passer une heure de sa propre date (`spend`) : sa viande vieillit, comme en solo.
- À changer en même temps : `time_suite` W3 affirme aujourd'hui que l'host « a plus faim » après le saut de
  l'invité ; avec l'urgence c'est l'inverse qui est vrai. `hunt2` E3 et E5 (saut fait par l'host lui-même, invité
  sur sa carte) restent verts.
- Pas prouvable à deux fenêtres : le visiteur d'un invité (chemin 3) et l'invité sur la carte de l'host pendant
  qu'un troisième voyage : il faut trois fenêtres (`trio_suite`, interdit sur cette machine sans accord).

## 6. Questions pour le conseil

1. La date du monde reste-t-elle unique (a, b, d, e) ou devient-elle personnelle (c) ?
2. L'urgence part-elle seule dans une version tout de suite, avant le choix du reste ?
3. Le sac : « temps vécu par le joueur » (a) suffit-il, ou faut-il aussi protéger les objets posés et les coffres
   d'une carte où un joueur est présent (b) ?
4. Le voyage sur la carte du monde doit-il encore faire avancer la date de tous (e ou non) ? Et la nuit d'un
   seul joueur ?
5. Sur la même carte que l'host (carte du monde à deux, nuit de l'host) : l'invité vit-il le saut de l'host ?
   Et son propre pas sur la carte du monde doit-il lui coûter comme en solo (aujourd'hui : rien) ?
6. Délais des quêtes personnelles : date du monde, ou temps vécu par le joueur ?
7. Une case host de plus, ou la nouvelle règle remplace-t-elle l'ancienne sans case ?
8. Trois fenêtres pour jouer les chemins à trois joueurs : accord de l'utilisateur ?
