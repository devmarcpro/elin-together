# Sommeil et déplacements brusques (lecture du code, 2026-10-06, version 0.26.506)

Rapport de l'utilisateur : « beaucoup de bugs avec le sommeil (des téléportations impromptues) », à trois joueurs ou
plus, lui est invité. Étude par lecture seule : rien n'a été lancé. « non vérifié » = déduit du code, jamais joué.
Chemins : `J:` = `dev/_decomp/Elin/`, `M:` = `ElinTogether/` (le mod).

## Ce qu'il faut savoir d'abord
- Les joueurs distants **sont dans le groupe de l'host** : `chara.MakeAlly()` (M:Net/Host/ElinNetHostPlayerManager.cs:221,
  J:Chara.cs:2524-2551) en fait des membres du groupe (`IsPCParty`, J:Chara.cs:634) et des habitants de la base
  (`IsPCFaction`). `NetPeerState.FindChara` les cherche dans `pc.party.members` (M:Net/NetPeerState.cs:42-45).
- Les compagnons de **tous** les joueurs sont dans ce même groupe (M:Helper/CompanionHelper.cs:1-30).
- `MoveImmediate` passe par `Map.MoveCard` (J:Card.cs:6168-6186, J:Map.cs:946), pas par `Chara._Move` : le mod
  n'envoie **aucun** `CharaMoveDelta` pour lui (M:Patches/DeltaEvents/Chara/CharaMoveEvent.cs:11-60). Les autres
  joueurs le voient au prochain instantané du monde, qui force la case si l'écart dépasse 2
  (M:Models/WorldState/CharaStateSnapshot.cs:153-166). D'où un saut « de nulle part » quelques secondes après.
- Le monde n'est **pas en pause** pendant l'écran de nuit : `UI.IsPauseGame` est forcé à faux en session
  (M:Patches/PauseGame.cs:40-46). Que `LayerSleep` demande la pause en solo : non vérifié.

## 1. Le jeu en solo (ce que le mod hérite)
- Lit : `TraitBed.TrySetAct` (J:TraitBed.cs:23-33) prend comme « amoureux » le premier personnage de la case du lit s'il
  est assez ami. `AI_Sleep` (J:AI_Sleep.cs:7-24) : si l'amoureux est à 1 case, le joueur saute sur sa case
  (`MoveImmediate`, l.14-18) ; sinon `_Move` sur le lit (l.19-22) ; puis `Chara.Sleep` (J:Chara.cs:10359-10371 : `ConSleep`
  avec `pcSleep = 15`). La barre « Dormir » pose lit et oreiller par terre (J:HotItemActionSleep.cs:9-34).
- `ConSleep.Tick` (J:ConSleep.cs:62-143), un tour par appel : 1er tour, `SuccubusVisit` (l.64-68, 172-210) ; descend de
  monture (l.71-82) ; décompte 15 tours ; à 0 :
  - **boucle « dormir à côté »** (l.106-130) : tout personnage de la carte (sauf le joueur, sans monture, sans
    entrave) est **placé sur la case du joueur** (`MoveImmediate`, l.121) s'il a le drapeau 123 (réglé par dialogue
    « dors à côté »), ou s'il est de la faction du joueur, de race à étiquette `sleepBeside` et tire 1 sur 5 (l.115) ;
    il s'endort 20 à 45 (l.124-126). Races à cette étiquette (lues dans `sharedassets0.assets`, non vérifié pour le
    détail) : chat, chien, shiba, lapin, slime ;
  - tous les membres du groupe reçoivent `ConSleep` 5 à 14 (l.131-137) ; ouvre `LayerSleep.Sleep` (l.141).
- `LayerSleep.Advance` (J:LayerSleep.cs:52-107) : +10 min par pas (l.105). À la fin : `SimulateFaction` si carte de
  base, champ ou carte du monde (l.57-60) ; `OnSleep` de tout le groupe (l.76-79) ; sauvegarde (l.85-88).
- `Player.SimulateFaction` (J:Player.cs:1910-1939) : le joueur est promené dans **chaque base en retard** (`MoveZone`
  + `scene.Init`, jusqu'à `maxSimBases`) puis ramené à sa case. Le groupe suit (J:Zone.cs:1747-1752).
- Réveil : `ConSleep.OnRemoved` (J:ConSleep.cs:228-352) remonte en selle (l.240-255), reprend le lit (l.262-266).
- `Zone.Simulate` (J:Zone.cs:1304-1480) ne tourne pas pour la carte où l'on dort ; ailleurs, les habitants hors
  groupe sont posés sur leur lit ou leur travail (J:GoalSleep.cs:49-66, J:GoalWork.cs:136-141). Les membres du groupe
  sont ignorés (J:Zone.cs:1383, 1439).

## 2. Ce que fait le mod, pas à pas
Fichier central : M:Patches/Synchronization/SleepSynchronizationContext.cs (« SSC »).
- **Partout** : « peut dormir » est toujours vrai pour le joueur local (SSC:100-120). Chaque image, l'host compte les
  joueurs vivants et ceux qui ont un `ConSleep` (SSC:28-83) ; annonce « X veut dormir » (SSC:85-98).
- **L'invité clique « dormir »** : son jeu ne dort pas, il envoie `SleepRequestDelta` (SSC:122-147). L'host pose un
  `ConSleep` 50 sur l'avatar (M:Models/Delta/Misc/SleepRequestDelta.cs:22-27), renvoyé à tous. Ce `ConSleep` ne tourne
  jamais (SSC:236-253) ; il attend. Un geste de l'invité = `SleepCancelDelta` (SSC:209-234) et le sommeil est tué.
- **L'host clique « dormir »** : `ConSleep` normal ; il tourne 14 tours, puis **s'arrête à 1 tant que tout le monde
  n'est pas prêt** (SSC:187-207, 252). Pendant l'attente il peut agir ; son premier ordre est avalé et annule
  (SSC:209-234).
- **Tous prêts** : l'host passe à 0, fait la boucle du §1 (« dormir à côté », membres du groupe), ouvre l'écran de
  nuit ; `SleepStartDelta` l'ouvre chez les invités (SSC:255-270 ; M:Models/Delta/Misc/SleepStartDelta.cs:15-25). Chez
  eux `Advance` est coupé (SSC:313-329) ; l'heure arrive par `WorldDateAdvanceDelta`, qui fait aussi
  `TickConditions` 4/6 par minute (M:Models/Delta/World/WorldDateAdvanceDelta.cs:60-70).
- **Fin de nuit** : `SimulateFaction` n'est **pas** fait si l'host est connecté à 2 joueurs ou plus (SSC:306-311).
  `OnSleep` de l'host -> `CharaSleepDelta` + sommeil des avatars distants tué (SSC:272-296) ; chaque invité fait
  `OnSleep`, tue son sommeil, ferme l'écran (M:Models/Delta/Chara/CharaSleepDelta.cs:22-33).
- **Un seul des trois dort** : rien ne bouge ; s'il est l'host, il attend en pouvant agir ; si c'est un invité, il
  attend (sommeil annulable). **Deux dorment** : pareil, l'attente dure jusqu'au troisième.
- **Invité seul sur une carte qu'il tient** (voyage indépendant) : `Connection` est nulle (M:Net/NetSession.cs:40),
  donc **le sommeil complet du jeu** : tout le §1, y compris `SimulateFaction` (SSC:306-311 le laisse passer :
  `Connection is not ElinNetHost` est vrai). Test : seulement Vernis (sleep_suite.py:265-290), où ce chemin ne
  s'exécute pas (ni base, ni champ, ni carte du monde).

## 3. Déplacements brusques, du plus au moins probable (trois joueurs)

### A. Familiers et « dormir à côté » tirés sur le lit de l'host — probable, chaque nuit de l'host
- Qui : chats, chiens, shibas, lapins, slimes de **tous** les joueurs (compagnons des invités compris) et habitants
  de la base, 1 sur 5 chacun ; les PNJ au drapeau 123, toujours. Même s'ils sont loin de l'host.
- Où : sur la case du lit de l'host, avec un sommeil de 20 à 45 (J:ConSleep.cs:106-130).
- Quand : à la fin du décompte de l'host, juste avant l'écran de nuit. Vu des invités avec retard (pas de delta, voir
  plus haut) : « mon chat a sauté tout seul ».
- Pourquoi : la boucle exclut seulement `IsPC` (le joueur local) ; les compagnons des invités sont du groupe et de la
  faction de l'host. Suite : à leur réveil ils repartent vers leur propriétaire (J:AI_Idle.cs:448-471 ; propriétaire
  choisi par M:Patches/CompanionFollowPatch.cs:40-43) et, bloqués 10 fois (100 en base), se **téléportent** vers lui
  (J:AI_Idle.cs:469) : un second saut.
- En solo : oui, mais c'est le familier du joueur qui dort. Ici c'est celui d'un autre : défaut. Et l'invité qui dort
  ne tire rien vers lui (la boucle ne tourne que pour le joueur local de l'host, J:ConSleep.cs:69) : inégalité.
- Ni la suite ni la doc ne l'ont testé (aucun familier dans sleep_suite.py).

### B. Invité éloigné qui dort : `SimulateFaction` chez lui — probable si quelqu'un voyage seul
- Qui : l'invité endormi, seul sur sa copie (voyage indépendant, actif par défaut : M:Emp/EmpConfig.cs:120-125).
- Où : le jeu l'envoie dans chaque base en retard ; chez lui `MoveZone` passe par `TryTravel`
  (M:Patches/DeltaEvents/Chara/CharaMoveZoneEvent.cs:25-28), qui **demande un bail à l'host** et refuse le
  déplacement (M:Net/Client/ElinNetClientTravel.cs:103-125) ; mais `Player.SimulateFaction` fait quand même
  `scene.Init` (J:Player.cs:1928-1931). Résultat attendu : carte vue de travers comme le bug du 2026-10-02 (MODLOG
  l.1023-1033), ou, une fois le bail accordé, l'invité **emmené dans une base**. Non vérifié, jamais exécuté.
- Quand : au réveil, si la carte est une base, un champ ou la carte du monde (J:LayerSleep.cs:57) et qu'une autre
  base a plus d'une heure de retard. Dormir sur la carte du monde est courant.
- En solo : oui, voulu (le jeu simule ses bases). Défaut ici : l'host est protégé (SSC:306-311), pas l'invité seul.
  Autre trou voisin : l'host ne passe jamais ce chemin ; l'invité éloigné, si.

### C. Succube et ver des rêves : un personnage téléporté sur le lit — rare
- Qui : tout personnage « oisif » de la carte ayant le trait 1216 ou un ver des rêves dans le sac, **les avatars des
  invités compris** (`!chara.IsPC`), puis il est mis en `AI_Fuck` (J:ConSleep.cs:178-205, `Teleport` à la l.189).
- Chance : 1 sur 3 avec un ver ; 1 sur 200 pour l'host sans ver face à un succube (l.185). Au premier tour du sommeil.
- En solo : oui ; défaut seulement si l'avatar d'un invité est pris pour un monstre. `IsIdle` d'un avatar : non vérifié.

### D. Le dormeur lui-même : sauts d'une case — très faible
- Se coucher sur la case d'un animal ou d'un autre joueur couché sur le lit : `MoveImmediate` (J:AI_Sleep.cs:14-18) ;
  sans delta, rattrapé par instantané. Remontée en selle ou descente de selle de l'host
  (J:ConSleep.cs:71-82, 240-255 ; J:ActRide.cs:140-144). Même chose qu'en solo.

### E. Pas des déplacements, mais « bugs de sommeil » vus en lisant
- L'host attend sans fin si un joueur est parti seul : la copie de ce joueur n'a jamais de `ConSleep` côté host
  (SSC:44-57 compte tous les `CurrentPlayers`). Non vérifié en jeu.
- Pendant l'écran de nuit le monde tourne (voir plus haut) : monstres libres pendant que tous dorment. Non vérifié.
- Bases en retard : sautées à la nuit (SSC:306-311), rattrapées à l'entrée (habitants posés sur leur lit : normal).

## 4. Petite correction et test pour les trois premiers
Modèle de test : `dev/_tools/sleep_suite.py` (étapes z0, z1, z2 et `awake`) ; fenêtres H (host) et A (invité).

**A. Familiers.** Correction : sur `ConSleep.Tick` (préfixe + finaliseur) noter « nuit commune en cours » et, sur
`Card.MoveImmediate`, refuser quand le personnage est un compagnon d'un autre propriétaire que le joueur qui dort
(`CompanionOwnerUid` différent de celui du joueur local, M:Helper/CompanionHelper.cs). ~15 lignes, dans
SleepSynchronizationContext. L'égalité parfaite demanderait que l'invité aussi tire les siens : non fait ici.
Test (nouvelle étape `p1`, après z0) : par `eval` chez l'host, créer un chat de l'invité (`CharaGen.Create("cat")`,
`MakeAlly`, `SetCompanionOwner(invité)`, `SetBool(123, true)` pour forcer le tirage) à 12 cases de l'host et dix autres
chats ; noter les cases ; jouer z1 puis z2 ; mesurer `Dist` au lit de l'host des deux côtés. Rouge : le chat de
l'invité est sur la case de l'host (distance 0 à 1) ; vert : il n'a pas bougé de plus de 3 cases.

**B. Invité éloigné.** Correction : dans `OnSimulateFaction` (SSC:308-311) renvoyer vrai seulement hors session ou
host seul : `Transport is null || (Connection is ElinNetHost && CurrentPlayers.Count < 2 && !IsAway)`. Une ligne.
Test (étape `y2`, modèle de y1 + w0) : host sur la carte du monde, invité seul sur un champ (`move`, `enter_at`) ;
`pendingSimHours = 5` sur la base de départ par `eval` (donne un retard sans seconde base) ; l'invité dort ;
mesurer `zone_uid(A)` avant/après, `state(A)["sceneMode"]`, `EInput.haltInput`, et compter « Requesting zone lease »
dans le journal de l'invité. Rouge : bail demandé ou zone changée ou entrées bloquées ; vert : la même carte, libre.

**C. Succube/ver.** Correction : préfixe sur `Card.Teleport` qui refuse quand `__instance` est un `IsRemotePlayer` et
que l'appelant est `SuccubusVisit` (ou, plus court, préfixe sur `ConSleep.SuccubusVisit` qui sort s'il y a une
session et que l'hôte dort : l'invité n'a jamais ce tirage chez lui). Test : `eval` chez l'host, ajouter un
`TraitDreamBug` (id « dreambug », non vérifié) dans le sac de l'avatar de l'invité, rendre l'avatar oisif, jouer z1-z2,
répéter 6 nuits : rouge si l'avatar arrive sur la case de l'host une fois ; (tirage 1 sur 3 : peu pratique, d'où
le rang bas ; ne pas l'écrire avant A et B).

## 5. Questions à poser à l'utilisateur
1. Qui a été déplacé : toi, un autre ami, ou un animal / compagnon ?
2. Il atterrissait où : près du lit de celui qui venait de se réveiller, ou ailleurs ?
3. Vous aviez des familiers (chat, chien, lapin…) avec vous à ce moment ?
4. Quelqu'un était-il parti seul (carte du monde, autre ville) pendant que d'autres dormaient ?
5. Après la nuit, l'écran est-il resté noir ou figé, ou bien la carte a-t-elle changé ?
