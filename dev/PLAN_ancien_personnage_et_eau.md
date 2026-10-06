# Ancien personnage qui se bat, invité dans l'eau (lecture du code, 2026-10-06, version 0.26.506)

Deux retours d'une vraie partie (l'utilisateur est invité). Étude par lecture seule : rien n'a été lancé ni compilé.
« vérifié » = lu dans le code. « non vérifié » = déduit, jamais joué. `J:` = `dev/_decomp/Elin/`, `M:` = `ElinTogether/`.
Je n'ai trouvé AUCUN chemin prouvé pour A : voir §A.3. Le plan donne donc les pistes classées, une garde qui règle toute
la famille, et un test qui dit si la garde manque.

## A. L'ancien personnage revient sur la carte et se bat

### A.1 Ce que devient un personnage que personne ne joue (vérifié)
- Il reste dans `game.cards.globalCharas` (jamais détruit) avec le drapeau `remote_chara` (M:Net/Host/ElinNetHostPlayerManager.cs:223,
  jamais retiré). Il est aussi **membre de la base** : `MakeAlly` -> `_MakeAlly` -> `homeBranch.AddMemeber` (J:Chara.cs:2544-2554).
  `RemoveRemoteChara` le sort du groupe (`pc.party.RemoveMember`, l.50) mais **pas de la base**.
- À la déconnexion ou au départ seul : `RemoveRemoteChara` (ElinNetHostPlayerManager.cs:42-65, appelé par ElinNetHost.cs:193-194 et
  ElinNetHostTravel.cs:860-861) fait `_zone.RemoveCard` (l.53) donc `currentZone = null` (J:Zone.cs:2205-2208). Sur une autre
  carte : `parent = null; currentZone = null` (l.56-57). Un `currentZone` nul veut dire « nulle part » : le jeu ne le pose nulle part.
- **Qui est « joueur » n'existe qu'en mémoire** : `ActiveRemoteCharas` (ElinNetHostPlayerManager.cs:13). Tout ce qui protège un joueur
  distant (dégâts, décomposition, tueur, repos, tour d'IA `GoalRemote`) passe par `IsRemotePlayer` / `IsActiveRemoteChara`
  (M:Helper/RemoteCardHelper.cs:31-47, M:Patches/Remote/*, M:Patches/Synchronization/GameSynchronizationContext.cs:116-122).
  Un chara qui porte le drapeau mais n'est pas dans cette liste est, pour le jeu, **un allié ordinaire de la base** : il
  suit les ordres de l'IA, attaque, mange, ramasse, équipe, meurt. Cela colle à « il se battait ».
- Les seuls endroits où le jeu remet un personnage global sur une carte (vérifié) :
  1. `Zone.AddGlobalCharasOnActivate` (J:Zone.cs:1710-1789, appelé à l'activation l.719 et l.727) : **tout** global dont
     `currentZone == cette zone` (l.1726-1728), sans regarder le drapeau. Il ne le replace que si `global.transition != null`
     (l.1747) ; sinon il garde son ancienne case (`Map.AddCardOnActivate`, J:Map.cs:899-902, ne corrige que hors limites).
  2. `Map.OnDeactivate` (J:Map.cs:210-220) : tout global encore sur la carte qu'on quitte reçoit `currentZone = cette zone`
     (l.215-218). C'est ce qui « réarme » un personnage resté sur la carte quand l'host change de carte, puis il revient
     à la prochaine activation (point 1).
  3. `Game.OnLoad` (J:Game.cs:417-425) : tout membre de base sans zone est envoyé chez lui (`MoveZone(..., RandomVisit)`). Retenu
     par `CompanionLimboPatch` (M:Patches/CompanionLimboPatch.cs:35-48) pour le drapeau `remote_chara` : OK pour l'ancien
     personnage ; **le patch ne vaut que pendant `Game.OnLoad`** (`_loading`). Et Game.cs:370-379 (zone du joueur nulle) met
     tous les membres du groupe en zone `homeZone` : sans effet ici car l'ancien n'est plus dans le groupe.
  4. Côté mod, qui donne une zone à un personnage : `SendSaveProbe` (l.222, `MoveZone`), `ReplaceRemoteChara` (ElinNetHostTravel.cs:1276,
     met nul), `TakeOverPc` (ElinNetHostHandOver.cs:290,302,315), `CharaMoveZoneEvent.cs:54` (compagnons).
     `Chara.MoveZone` ne fait rien si la zone est déjà la sienne (J:Chara.cs:3594-3597).

### A.2 Filets existants et leurs trous
- Trois filets retirent un chara drapeauté absent de `ActiveRemoteCharas` : au chargement (ElinNetHostPlayerManager.cs:346-382), chaque
  seconde sur `_map.charas` seulement (ElinNetHost.cs:140-146, abonné l.49 et ElinNetHostZoneSession.cs:45), et après chaque arrivée
  (ElinNetHostZone.cs:146). Ils sont **tous dans la session de l'host (ou de l'hôte de zone)**.
- **Trou 1 (vérifié dans le code)** : `RemoveRemoteChara` ne retire de la carte que si `currentZone == _zone` ET `_map.charas` le contient
  (l.52). Sinon branche `else` (l.54-58) : met `parent` et `currentZone` à nul **sans l'ôter de `_map.charas` ni de sa case**. Un
  chara dans `_map.charas` avec une `currentZone` fausse reste donc sur la carte, et le filet à la seconde ne change plus rien.
  Qu'un cas réel y arrive : non vérifié.
- **Trou 2 (vérifié)** : un invité **seul dans une zone** n'a pas de `Connection` (M:Net/NetSession.cs:40) : aucun filet ne tourne dans
  son monde. Son monde est la copie reçue à sa connexion : un ancien personnage d'un autre joueur y garde la zone qu'il avait
  alors. L'invité n'est pas servi par `CharaRemoveFromGameDelta` tant qu'il est loin (M:Models/Delta/Chara/CharaRemoveFromGameDelta.cs,
  seulement pour ceux qui reçoivent les envois). Quand il hérite de la carte ou y entre, le point A.1-1 pose l'ancien
  personnage et le jeu l'anime. Non vérifié en jeu.
- **Trou 3 (vérifié)** : `OnSessionNewPlayerResponse` (l.244-257) n'a pas la garde `ActiveRemoteCharas.ContainsKey(peer.Id)` que
  `OnSessionCharaSelectResponse` (l.144) et l'import (l.169) ont. Si le lien de l'ancienne connexion n'est pas encore tombé,
  `SendSaveProbe` écrase l'entrée (l.219) et l'ancien reste sur la carte, drapeauté mais « plus joueur » : le filet à la seconde
  le retire ensuite, **sauf trou 1**.

### A.3 À quel moment il peut réapparaître (classé, rien de joué)
1. Carte de l'host quittée puis revue pendant qu'il est encore sur la carte (trous 1 ou 3) : `Map.OnDeactivate` le marque, la
   réactivation le replace. Vraisemblable si le filet n'a pas encore tourné. Non vérifié.
2. Un autre invité qui tient la zone (hérite de la carte quand l'host part : ElinNetHostTravel.cs:152-215, 908-965) : son monde
   garde l'ancien personnage (trou 2). Le joueur qui rejoint cette zone voit alors son ancien personnage se battre. Non vérifié.
3. Chargement d'une partie de l'host sauvegardée pendant que l'ancien était sur la carte : le filet de chargement le retire, ou
   `CompanionLimboPatch` le retient. Peu probable, mais le patch ne couvre que `Game.OnLoad`.
4. Voyage indépendant (ElinNetHostTravel.cs:814-870) : l'ancien est mis à nul comme n'importe quel départ ; la copie
   envoyée par l'invité (`ReplaceRemoteChara` l.1243-1291) est ignorée si son numéro n'est plus celui de `SavedRemoteCharas`
   (l.1258-1262) : bon. Rien de réarmé ici.

### A.4 Peut-il mourir, perdre ou gagner des objets ? (non vérifié, vraisemblable)
Oui : sans passer par `IsRemotePlayer`, aucune des protections des joueurs ne s'applique (voir A.1). Il est allié de la base :
l'IA peut le faire attaquer, utiliser des potions, manger sa nourriture, ramasser par terre, et un ennemi peut le tuer
(personnage mort : renaissance par le jeu seulement si `CanRevive`). Ses compagnons (propriétaire = lui) sont aussi hors carte
tant que `TakeCompanionsAlong` les y a laissés (ElinNetHostCompanions.cs:19-44) : même risque s'ils reviennent.
Perte pour le joueur : réelle si le personnage meurt ou si l'IA consomme/dépose ses objets.

### A.5 Plus petite correction
Règle : **un personnage qui porte `remote_chara`, n'est pas `pc` et n'est pas un joueur présent n'est JAMAIS sur une carte.**
1. Garde unique, dans tous les modes qui font tourner le jeu (host, hôte de zone, invité seul) : postfix sur
   `Zone.AddGlobalCharasOnActivate` (J:Zone.cs:1710) qui retire de `_map.charas` tout `remote_chara` hors `pc` et hors
   `ActiveRemoteCharas` (liste vide si pas de `ElinNetHost`). Pas pour un invité relié à un host (`Connection is ElinNetClient`) :
   il garde `WorldStateSnapshot.RemoveLeftOverCharas` (M:Models/WorldState/WorldStateSnapshot.cs:105-139).
2. Corriger le trou 1 : dans `RemoveRemoteChara`, retirer par `_zone.RemoveCard` dès que `_map.charas` contient le chara, quelle que soit
   sa `currentZone` (l.52). Environ 5 lignes.
3. Ajouter à `OnSessionNewPlayerResponse` la même garde que l.144 (trou 3).
Ne rien changer à `Map.OnDeactivate` : sans personnage sur la carte, il ne marque rien.

### A.6 Test à deux fenêtres (nouvelle étape C5 de `dev/_tools/chara_suite.py`, après C4)
Départ : host H et invité A, deux personnages (`first` joué, `second` laissé), comme à la fin de C4 (réglage `ChooseCharacter`).
1. Vérifier l'état normal : `second` a `currentZone == null`, n'est pas dans `_map.charas`, pas dans `pc.party.members`.
2. Réarmer comme le jeu : par `eval` chez l'host, `Find(second).currentZone = EClass._zone` (ce que `Map.OnDeactivate` laisse
   après un changement de carte), puis un vrai aller-retour de l'host (`move(host, VERNIS)` puis `move(host, HOME)` du modèle
   `host_goto` de travel_suite.py) ; l'invité rejoint comme dans `both_joined`.
3. Attendre 10 s. Mesurer chez l'host puis chez l'invité : `second` absent de `_map.charas`, points de vie et nombre d'objets
   inchangés, `ai` non actif. **Rouge attendu aujourd'hui** si le trou 1 ou 2 existe : `second` est sur la carte. Si le test est
   vert sans correction, noter que le chemin n'est pas celui-là (on garde la garde, qui ne coûte rien) et poser la question 1.
4. Variante « zone tenue par un invité » (étape C6, plus longue) : A est seul sur un champ (`travel_suite.enter_at`), l'host fait
   changer le joueur de personnage, puis l'host entre dans la zone de A : mesurer l'ancien personnage dans le monde de A.
Ce que le banc ne joue pas comme un joueur : le réarmement est posé par `eval`, pas par une vraie sauvegarde ; une seule
adresse Steam pour les deux fenêtres.

### A.7 Questions au joueur
1. Pour changer de personnage, as-tu quitté puis rejoint avec l'écran de choix, ou créé un nouveau ? Le vieux est apparu tout de suite ou
   après un changement de carte de l'host ?
2. L'as-tu vu seul, ou l'host et les autres aussi le voyaient ? Avait-il encore ses objets après, ou est-il mort ?

## B. Un invité téléporté dans l'eau sur la carte du monde

### B.1 Ce que fait le jeu (vérifié)
- Sur la carte du monde, une case n'est « praticable » que par son drapeau `impassable`, posé à la génération de la carte
  depuis les tuiles et les nuages non découverts (J:MapGenRegion.cs:35,44), avec une rustine des plages à part (J:Region.cs:50-72).
  L'eau est donc bloquée comme un mur. Cela se calcule **par copie du jeu** : la carte du monde n'est jamais envoyée (M:ElinNetHostTravel.cs:767,
  `zone.IsRegion ... ? null`) et chacun joue sa copie (ElinNetHostTravel.cs:183, 1477).
- `Point.GetNearestPoint` (J:Point.cs:624-694) évite les cases bloquées par défaut, mais **rend la case de départ telle quelle** si rien
  n'est libre à 30 anneaux (l.675-676).
- `Zone.GetSpawnPos` (J:Zone.cs:1499-1710) sur la région : case de la zone quittée **sans contrôle** (`new Point(topZone.mapX, mapY)`,
  l.1510-1513), point de départ de la carte (`embarkX/Y`, l.1626-1632), `Exact/PortalReturn/Dead/Fall` = la case demandée sans contrôle
  (l.1641-1649). Les sites d'eau existent (J:Region.cs:127,145-147, `dungeon_water`), leur case est de l'eau.
- `Card.MoveType.Force` ignore les murs.

### B.2 Ce que le mod appelle pour un invité (vérifié)
- Arrivée ou retour sur la carte de l'host : case choisie sur la copie de l'HOST, `pc.pos.GetNearestPoint(allowChara:false, allowInstalled:false)`
  (M:Net/Host/ElinNetHostZone.cs:100,106) ; l'host le place en `Force` (l.109) ; l'invité s'y déplace en `Force` sur SA copie
  (M:Net/Client/ElinNetClientZone.cs:223). Valable aussi pour la reconnexion : `SendSaveProbe` (l.222) puis cette même arrivée.
- Rattrapage 5 fois par seconde d'un avatar qui s'écarte de plus de 2 cases : `Stub_Move(Pos, Force)` (M:Models/WorldState/CharaStateSnapshot.cs:156-165).
- Case de retour d'un invité qui rend une carte : sa propre case, jamais vérifiée contre la carte de l'host
  (ElinNetHostTravel.cs:1101-1105, ElinNetHostZone.cs:103-107).
- Départ puis retour d'une zone d'instance de quête : `TryTravel` remplace la zone mais **garde le `transition` d'origine**
  (M:Net/Client/ElinNetClientTravel.cs:78-79) ; `TravelTo` le rejoue (l.306). La carte de remplacement de l'host pour une quête
  tenue par un invité ne règle ni `instance.x` ni `instance.z` (ElinNetHostTravel.cs:1431-1433, alors que l.460-463 les règle
  pour la quête accompagnée) : une sortie `PortalReturn` irait en (0,0) (J:Zone.cs:1641-1649). Non vérifié que ce chemin se produit.
- Réanimation d'un invité : si le chara n'est pas sur la carte active, la case est `pc.pos` de l'HOST, qui est dans une autre zone
  (M:Models/Delta/Chara/CharaReviveDelta.cs:46-59) ; la case demandée par l'invité n'est contrôlée que pour les limites (l.47).
- Rien dans le mod n'appelle `Region.GetRandomPoint`, `Teleport`, `lastZonePos` ni `MoveImmediate` pour placer un invité sur la région
  (recherche faite). Le « rappel près de l'host » est le rattrapage de la 2e ligne. `NetReconnect` ne place rien, il rejoint.
- Sommeil sur la carte du monde : voir PLAN_sommeil_teleportations.md §3B (le jeu promène le joueur de base en base).

### B.3 Trois causes les plus probables (aucune jouée)
1. **Case de l'host jouée de force sur la copie de l'invité** (B.2 lignes 1 et 2). Si les deux copies de la carte du monde ne
   bloquent pas les mêmes cases (nuages, plages), l'invité se retrouve sur une case d'eau de SA copie. Plus probable car c'est le
   chemin de toute arrivée, reconnexion comprise.
   Correction : dans `OnZoneActivateResponse` (ElinNetClientZone.cs:223), si `_zone.IsRegion` et la case est bloquée sur la copie
   de l'invité, prendre `GetNearestPoint(allowBlock:false, allowChara:false)` de SA copie avant `Stub_Move`. 4 lignes.
2. **Case rendue sans contrôle par le jeu avec un `transition` que le mod a refait ou gardé** (B.2 lignes 4 et 5 : sortie de
   quête, sortie d'un site d'eau, `Exact/PortalReturn`). Correction : sur la région, après chaque `MoveZone` d'un invité, si
   `pc.pos.cell.blocked`, aller à la case libre la plus proche (postfix sur `Chara.MoveZone` quand `IsPC` et région, côté invité) ;
   règle aussi `instance.x/z` de la carte de remplacement (ElinNetHostTravel.cs:1431).
3. **Réanimation à la case de l'host dans une autre zone** (B.2 ligne 6). Correction : dans `CharaReviveDelta` (l.52), n'employer
   `pc.pos` que si le chara est dans la zone de l'host ; sinon laisser le jeu choisir (`Revive` sans case) ; contrôler aussi la
   case demandée (`IsInActiveMapBounds` ne regarde pas les murs).

### B.4 Tests (modèle `dev/_tools/travel_suite.py`, fenêtres H et A, nouvelles étapes w1 à w3)
Pas d'eau « vraie » : le banc peint des cases dans le jeu de l'invité seul, comme U7 de unplayed_suite.py (« deux cases repeintes dans son
jeu seul, remises à la fin »).
- **w1** : H et A sur la carte du monde (`ExitBorder`, `client_settled(...)`). Chez A seul, `cell.impassable = true` + rafraîchir sur la
  case où H se tient (et ses 8 voisines). A fait `leave()`/`connect_unasked()` de chara_suite.py n'efface pas la peinture si
  on la repose juste avant l'arrivée : utiliser plutôt l'appel direct du gestionnaire (`OnZoneActivateResponse` par
  `Traverse`) avec `Pos` sur une case peinte. Mesurer chez A : `pc.pos.cell.blocked`. Rouge : vrai ; vert : faux.
- **w2** : A dans une zone de quête tenue par lui (ou un champ), sortie par `EClass.player.ExitBorder()`, comme s6 : mesurer
  que `pc.pos` sur la région n'est pas bloquée, avec un site d'eau peint à l'emplacement de la zone quittée.
- **w3** : A tué hors de la carte active de H (A sur un champ, H à la Prairie) ; mesurer la case de réanimation dans la zone de A :
  elle ne doit pas égaler `pc.pos` de H quand les deux cartes diffèrent. Raccourci : la mort est posée par `Die()` chez A.
Ce que le banc ne joue pas : l'eau est peinte, pas celle du vrai monde ; un seul compte Steam.

### B.5 Questions au joueur
1. Juste avant, où était ton ami : dans une ville, un donjon, une quête, sur la carte du monde, ou venait-il de se reconnecter ou de mourir ?
2. Était-il tout seul sur la carte du monde, ou près de l'host ? Est-il resté bloqué dans l'eau, ou a-t-il pu marcher ?

## Ordre conseillé
1. A.5 point 2 et 3 (petits, sûrs), puis la garde du point 1 avec C5 rouge puis vert. 2. B.3 cause 1 avec w1. 3. Les questions
au joueur avant de toucher aux causes 2 et 3 de B. Un test = une correction = un commit ; ce qui n'est pas rejouable
(vraie reconnexion Steam) est écrit « non joué » dans le commit et le journal.
