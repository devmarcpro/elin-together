# Journal réel du 2026-10-06 (partie à 4, 0.26.524) : placement, rappels, carte remplacée

Journal lu : `Session_20261006.log` du joueur (host de 20:12Z à 20:32Z, puis invité de LemiWinks dès 20:40Z).
Tout ce qui suit est **lu dans le code et le journal, compilé, jamais joué**.

## 0. Reste à faire par celui qui reprend (une ligne, hors de mes fichiers)

**La cause du défaut 1 n'est pas corrigée dans le code**, seulement son effet. La correction est ici :

`ElinTogether/Patches/Synchronization/SleepSynchronizationContext.cs:884` (`OnSimulateFaction`)

```csharp
// avant
return session.Connection is not ElinNetHost || session.CurrentPlayers.Count < 2;
// après : dès qu'un joueur est connecté, même parti ailleurs (il n'est plus dans CurrentPlayers)
return session.Connection is not ElinNetHost host || !host.IsConnected;
```

Le commentaire au-dessus (« Not done while others are connected ») dit déjà cela ; le test, lui, compte les
joueurs **sur la carte de l'host**. `place_suite.py` P6 est rouge tant que ce n'est pas fait.

## 1. Un joueur qui arrive n'est jamais posé (grave)

Séquence chez l'host :

- 20:28:48 l'host quitte la Prairie (zone 7), Nardole la garde. 20:29:06 et 20:30:36 : Lemi garde sa copie de la
  carte du monde (zone 2), Arma garde la forêt (69). **Plus personne n'est sur la carte de l'host.**
- 20:30:40 à 20:31:00 : l'host, sur la carte du monde, essaie dix fois d'entrer dans la Prairie
  (`Recalling zone Zone_startSite@0 from Nardole`). Nardole ne la rend jamais (pas lu pourquoi : son journal manque).
- 20:31:02 `Sleep vote from 0` : l'host dort sur la carte du monde.
- 20:31:07.716 `Recalling zone Zone_startSite@0` puis 20:31:07.891 `Switching zone` **Prairie**, sans
  `handed back, host enters` : ce n'est pas un déplacement de l'host. C'est le réveil du jeu
  (`LayerSleep.Advance` → `Player.SimulateFaction`, J:Player.cs:1910) : il fait `pc.MoveZone(base)` puis
  `scene.Init` pour chaque base. Le mod refuse le `MoveZone` (carte tenue, rappel), le jeu charge quand même la
  carte. `OnSimulateFaction` devait empêcher ce tour, mais il compte `CurrentPlayers` (joueurs sur la carte de
  l'host) : ils étaient tous ailleurs, donc 1, donc le tour a eu lieu.
- État de l'host ensuite : il regarde la Prairie, son personnage est resté sur la carte du monde
  (`pc.currentZone` = carte du monde, `pc.pos` = sa case de la carte du monde, vers 33,104). Pas de retour à la
  carte du monde dans le journal (le second `scene.Init` n'a pas abouti ; pourquoi : pas dans ce journal).
- 20:31:28 Lemi se déconnecte, 20:31:47 il revient. `OnZoneDataReceivedResponse` le pose « à côté de l'host » :
  `pc.pos.GetNearestPoint(...)`, qui rend `pc.pos` lui-même quand rien n'est libre autour (J:Point.cs:624). Cette
  case est celle de la carte du monde : hors de la Prairie. `Zone.AddCard` ne vérifie rien :
  `Map.OnCardAddedToZone` met le personnage dans la liste de la carte, puis lève sur `new Point(x, z).cell`.
- Le gestionnaire s'arrête : pas de `ZoneActivateResponse`. Lemi attend sur son écran de chargement. Chez l'host
  son personnage est dans la liste de la carte, sur aucune case.
- 20:32:10 Arma arrive à son tour, `has finished zone replication`, puis **plus rien** : le journal de l'host
  s'arrête là (jeu figé ou fermé ; relancé à 20:38).

Les cases gardées (`_returnSpots`) ne sont **pas** en cause : elles portent déjà le numéro de leur carte
(`spot.ZoneUid == _zone.uid`), et Lemi n'en avait pas (parti ailleurs au moment de la coupure).

Changé (`ElinTogether/Net/Host/ElinNetHostZone.cs`, `OnZoneDataReceivedResponse`) :

- « à côté de l'host » seulement si l'host est sur cette carte (`pc.currentZone == _zone`) ;
- garde-fou avant de poser : une case qui n'est pas `IsValid` et `IsInBounds` est remplacée par l'entrée
  ordinaire de la carte (`EntrancePoint` : `Zone.GetSpawnPos` sans chemin d'arrivée, sinon le milieu), avec un
  avertissement `No tile of … for player …` ;
- la case que le personnage rapporte d'une autre carte est remplacée aussi quand elle est hors limites ;
- poser, puis les suites (compagnons, ventes, balayage) sont enveloppés : une exception est écrite en erreur, un
  second essai est fait à l'entrée, et **la réponse part toujours**.

Non couvert : l'host reste « devant une carte où il n'est pas » tant que la ligne du §0 n'est pas faite. Un joueur
qui arrive est maintenant posé à l'entrée de la Prairie et joue ; l'host, lui, ne peut toujours rien faire.

Taille de la Prairie non lue (le fichier de la carte n'est pas là) : que 104 dépasse son tableau est déduit de
l'exception, pas mesuré.

## 2. L'invité renvoyé auprès de l'host en boucle

Séquence chez le joueur (invité de Lemi) :

- 20:43:41 il sort de la Prairie : `Leased zone Zone_ntyris@0`, il marche seul sur sa copie de la carte du monde.
- L'host (Lemi) voyage : champ 139 → carte du monde → champ 140 → carte du monde → champ 141 → carte du monde.
- À chaque pas de l'host sur la carte du monde (20:44:03, 20:44:36, 20:45:24) :
  `Host entered away zone Zone_ntyris@0 without recall, rejoining` → monde entier rechargé
  (`Received save data from host`, `Falling behind with 150-220 dropped ticks`, 1 à 8 s d'écran figé), posé sur
  la carte du monde de l'host. Deux secondes plus tard l'host entre dans un champ : `Took over zone Zone_ntyris@0`.
- La troisième fois, l'host est déjà dans le champ 141 quand le joueur finit de charger : pas encore « installé »,
  il **suit l'host dans le champ 141** (téléporté là sans l'avoir voulu).

Lu dans le code : l'host ne rappelle jamais la carte du monde (`CanEnterNow` : `zone.IsRegion` → vrai, « chacun
a sa copie », `LeavePlayersBehind` donne un bail par joueur). Côté invité, `OnHostZoneChangedWhileAway` traitait
« l'host est entré sur la carte que je tiens sans la rappeler » comme une urgence, carte du monde comprise. Les
deux moitiés se contredisent : défaut, pas une conception. `PLAN_invites_tp_sur_host.md` ne demande nulle part
de regrouper les joueurs quand l'host pose le pied sur la carte du monde.

Changé (`ElinTogether/Net/Client/ElinNetClientTravel.cs`, `OnHostZoneChangedWhileAway`) : sur la carte du monde,
l'invité reste sur sa copie (une ligne de journal en Debug). Rien n'est rechargé, sa tuile ne change pas.

Ce que cela change pour les joueurs (**choix de conception, à passer au conseil si on veut autre chose**) :

- un invité déjà sur la carte du monde ne voit pas l'host y passer (comme quand l'host est en ville) ;
- un invité qui **sort d'une ville** pendant que l'host est sur la carte du monde le rejoint toujours (inchangé,
  `TryTravel` → `SendRejoin`) : pour voyager ensemble on sort après l'host ;
- pas de case à cocher : elle irait dans `Models/SessionState/**`, qu'un autre agent modifie en ce moment.

### `Handed zone 141 while not in it` (20:45:40)

L'host quitte le champ 141 où le joueur vient d'être traîné, et lui laisse la carte (`LeavePlayersBehind` : il est
« installé » dès que l'host lui a répondu, avant que son jeu ait chargé la carte). L'invité ne se reconnaît pas sur
cette carte (ni `visiting` ni `withHost` ; lequel des deux tests a manqué n'est pas dans le journal : la ligne
écrit maintenant sa carte et son état), écrit l'avertissement et **ne fait rien**. Or l'host a déjà retiré son
personnage de sa carte et le croit parti : l'invité suit encore l'host (`Received zone state` de la carte du monde
puis de la Prairie) mais n'est plus jamais posé ni écouté. C'est le joueur fantôme de la fin du journal
(`Map checksum differs … charas 11/10`).

Changé (même fichier, `TakeOverZone`) : dans ce cas (ni ailleurs ni en retour), l'invité revient chez l'host
comme un joueur parti (`SendRejoin`) : l'host lâche le bail (`rejoins while still holding zones`), renvoie le
monde et le pose. Un rechargement de plus, mais plus de fantôme.

Non couvert : `MarkSettled` côté host arrive avant la fin du chargement de l'invité (8 à 21 s sur cette machine).

## 3. La carte remplacée à tort au départ de l'host

- 20:42:19 : `our copy is the same, kept` avec `held 38:FBF1753B`.
- 20:42:19 à 20:42:47 le joueur tient la Prairie, la rend ; l'host (Lemi) y revient et fabrique
  (`AI_UseCrafter of chara 582`) pendant les 21 s où le joueur charge (20:42:58 → 20:43:19).
- 20:43:19 : `our copy differs` : sol et personnages identiques, `held` 38 des deux côtés, mélange différent.
  Chez le joueur le mélange est **le même qu'une minute avant** : c'est la copie de l'host qui a changé (une
  quantité, ou un contenant, d'un objet rangé), sans que cela arrive chez le joueur. Quel objet : le journal ne
  donne que des totaux.
- Les trois passages de 19:46, 19:50 et 19:51 (Nymelle) ont tous `held 0:00000000` : aucun contenant au sol,
  rien à comparer. La Prairie (26 à 38 objets rangés) est le seul cas où « held » compte.

Lu dans le code : rien ne tient le contenu des contenants au sol à l'identique pendant le jeu. Le contrôle
continu (`NetDesync`, sommes de la carte) ne compte que le sol et les personnages ; une quantité n'est envoyée que
par `Card.ModNum` (`CardModNumEvent`), pas par les autres chemins du jeu (pile fusionnée, `SetNum`) ; un objet
rangé s'empile selon les règles de chaque jeu (`PLAN_journal_desync_6_octobre.md` §1).

Changé : `ZoneLeaseState.SameFloor` (`ElinTogether/Models/ZoneLease/ZoneLeaseState.cs`) : la décision porte sur
le sol et les personnages. Dans `AdoptHostCopy` (`ElinNetClientTravel.cs`), un écart sur « held » seul écrit
`the content of a container differs, our copy is kept` (Information, avec les deux sommes) et ne recharge plus.

**Ce qui n'est plus couvert** : quand le contenu d'un coffre diffère vraiment, la copie de l'invité devient la
référence (c'est elle qu'il rend à l'host). Ce que l'host avait pris dans un coffre sans que l'invité le sache y
revient (objet en double) ; ce qu'il y avait mis disparaît. Avant ce changement la copie de l'host gagnait, au prix
d'un rechargement sous les pieds. La vraie correction serait de réparer le coffre seul (comme `CharaBagDelta` pour
un sac) : non écrite.

## 4. Au passage (lu, non corrigé)

- `Lobby enter refused with k_EChatRoomEnterResponseDoesntExist` (20:38:53, avertissement + information du même
  essai) : `SteamNetLobbyManager.OnLobbyEntered` ; le salon Steam demandé n'existe plus (celui de sa propre partie,
  fermée à 20:32).
- `Map checksum differs … charas 11/10, things 20/17` (20:46:03) : l'invité est le fantôme du §2, il regarde une
  copie que l'host ne tient plus à jour pour lui (son personnage et ce qui a suivi n'y sont plus chez l'host).
- `Player … disconnected while away in zones …, keeping its last checkpoint` : `ReleaseLeaseOnDisconnect` ; le
  joueur a coupé pendant qu'il tenait une carte, l'host garde sa dernière copie (60 s au plus) et sauvegarde.
- `Removing quest from player chara` : `QuestSynchronizationContext.Update` ; un personnage de joueur porte une
  quête de donneur (`chara.quest`), que seul un non-joueur doit porter : retirée.
- Vu en passant : l'host envoie la carte entière à **tous** les joueurs à chaque changement de carte, y compris à
  ceux qui sont ailleurs et n'en lisent que le numéro (`PropagateZoneChangeState` → `Broadcast`).
- Vu en passant : Nardole n'a jamais répondu à dix rappels de la Prairie en 27 s (20:30:40 à 20:31:07).

## 5. Tests écrits, jamais lancés (`dev/_tools/place_suite.py`, deux fenêtres)

- **P5** : A part seul à Vernis, l'host va sur la carte du monde, A sort de Vernis : il est sur une case de la
  carte de l'host, la même des deux côtés ; le balayage final refuse toute exception.
- **P6** : A tient la Prairie, l'host sur la carte du monde lance `Player.SimulateFaction()` (ce que fait le
  réveil ; raccourci : pas de nuit, retard posé à la main) : l'host reste sur la carte du monde, A n'est pas
  rappelé, puis A le rejoint sur une case valide. **Rouge tant que le §0 n'est pas fait.**
- **P7** : A seul sur la carte du monde, l'host sort de la Prairie et y rentre trois fois : A garde sa case et son
  monde n'est pas rechargé (`core.game` reste le même objet).

Pas de test pour le §3 (il faut un coffre dont le contenu diffère entre deux jeux) ni pour `Handed zone … while
not in it` (il faut un host qui quitte une carte pendant que l'invité la charge).
