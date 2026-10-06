# Salon de la session ouverte toute seule : les joueurs connus du monde entrent sans être amis

Date : 2026-10-06. Demande : « le jeu devrait savoir quel personnage est à qui… le joueur n'a pas à réfléchir,
il se connecte au serveur et voilà tout est bon ». Un joueur dont le compte est dans la sauvegarde doit pouvoir
rejoindre la partie ouverte toute seule sans être ami Steam de l'hébergeur. Un inconnu ne doit pas entrer.

## 1. Faits (chemin complet, numéros de ligne avant ma correction, fichiers au 2026-10-06)

Création du salon
- `Emp/EmpAutoHost.cs:86` : `StartServer(local, true)` (quiet = ouverte toute seule). Seulement si
  `IsSharedWorld || SaveDepot.Holding` (`:81`).
- `Net/Host/ElinNetHost.cs:36` : `CreateLobby(quiet ? Friend : Public, quiet: quiet)`. Le bouton Start Server
  (`Components/Tabs/TabLobbyBrowser.cs:144`) et la console (`Emp/EmpConsole.cs:85`) donnent `Public`. Il n'existe
  aucun choix de type de salon dans l'interface : la seule différence manuel / automatique est ce `quiet`.
- `SteamNetLobbyManager.cs:88-95` : `Public -> k_ELobbyTypePublic`, `Friend -> k_ELobbyTypeFriendsOnly`,
  `Invite -> k_ELobbyTypePrivateUnique`. `:97-99` : en DEBUG tout devient `PrivateUnique` (banc).
- `OnLobbyCreated` (`:242`) : données du salon (version du mod, version du jeu, zone), `SetGameServer(SteamUser)`,
  `SessionId = salon`, présence riche `connect = "+connect_lobby <salon>"` (`UpdateRichPresence`, `:184`).

Liste / recherche
- `GetOnlineLobbies` (`:168`) : `RequestLobbyList` mondial, filtres sur la version du mod et du jeu (hors DEBUG).
  `OnLobbyMatchListComplete` (`:417`) garde tout salon valide et non vide. Un salon `FriendsOnly` n'est pas
  renvoyé par une recherche ; un salon `Invisible` l'est (voir plus bas).

Demande d'entrée
- Côté joueur : `ConnectLobby` (`:117`) -> `SteamMatchmaking.JoinLobby(id)` (`:143`). Appelé par le bouton du dépôt
  (`Helper/SaveDepot.cs:323`, `Join`, identifiant lu dans le champ `join` du verrou « <steam64> <salon> »,
  `:130-146` et `:309-335`), par la présence riche (`:287`), l'invitation Steam (`:278`) et les reconnexions
  (`Net/Client/ElinNetClientPlayer.cs:269,283,299`, `Net/Client/ElinNetClient.cs:96`).
- Réponse de Steam : `OnLobbyEntered` (`:300`) ; refus -> `ResetSession` et fenêtre « emp_lobby_enter_failed »
  (`:303-315`). Puis contrôle des versions (`:330-349`), `HasServer` (`:351`), `TryJoinCurrentLobbyGame` (`:364`).

Le contrôle (ligne 383 avant ma correction)
- `OnLobbyChatUpdate` (`:368`), chez le propriétaire du salon, au moment « Entered » : ami Steam
  (`GetFriendRelationship == Friend`) ou invité à la main (`_invited`, `InviteSteamUser`) -> il reçoit une clé de
  connexion (`Current["connection_key_<id>"]` et `SteamNetManager.ConnectionKeys[id]`, `PlayerUidMaker.
  MakeConnectionKey`). Sinon `Current.KickMember(id)`.
- `KickMember` (Heathen, `dev/_decomp/Heathen/...:3126`) n'expulse personne : il écrit `[id]` dans la donnée de
  salon `z_heathenKick`, et c'est le mod du joueur concerné qui se retire (`OnLobbyDataUpdate`, `:404`). Un client
  qui ne coopère pas reste dans le salon (voir risque 1).

La connexion P2P qui suit
- Le joueur attend `connection_key_<lui>` dans les données du salon (`Net/Client/ElinNetClient.cs:50-55`), puis
  `ConnectSteamUser(GameServer)` (`:123`, `Socket.Connect(steamId)`).
- Chez l'hôte : `SteamNetManager.AcceptIfHost` (`Net/Steam/SteamNetManager/SteamNetManagerServer.cs:84`) refuse
  (« emp_not_allowed », `:114-118`) tout compte absent de `ConnectionKeys` (hors connexion locale de banc). Donc
  même qui connaîtrait l'adresse de l'hôte ne peut pas ouvrir la connexion sans être passé par le contrôle
  ci-dessus. Aucune vérification d'amitié dans la couche P2P : `grep Friend` ne trouve que le type du salon
  (`SteamNetLobbyManager.cs:90`) et le contrôle (`:382-383`).
- (Une session de zone d'un invité met `ConnectionKeys[user] = "zone_guest"`, `ElinNetHostZoneSession.cs:91` :
  autre chemin, non touché.)

Qui est « connu du monde »
- Tables de la sauvegarde, par compte Steam : `SavedRemoteCharas` (`remote_chara`, `ElinNetHostPlayerManager.cs:25`),
  `PlayerRosters` (`remote_chara_roster`, `:35`), `PcOwners` (`pc_owner`, `ElinNetHostHandOver.cs:27`, le propriétaire
  du personnage local, y compris celui qui a sauvé le monde avant l'hôte actuel). `PcOrphans` ne donne que des uid
  de personnage, pas de compte. Tout est `private static` dans `ElinNetHost` : inaccessible depuis le dossier
  `Net/Steam/` (d'où une ligne à ajouter ailleurs, voir 3).

## 2. Ce que Steam permet (docs Steamworks, ELobbyType ; de mémoire, non rejoué ici)

| Type | Qui peut `JoinLobby(id)` | Renvoyé par une recherche | Vu des amis |
|---|---|---|---|
| Private / PrivateUnique | seulement sur invitation | non | non |
| FriendsOnly | amis de celui qui l'a créé, et invités | non | oui |
| Public | tout le monde | oui | oui |
| Invisible | tout le monde qui a l'identifiant | OUI (malgré le nom) | non |

- Donc l'hypothèse de l'utilisateur est la bonne : le blocage n'est pas seulement la ligne 383. Le serveur de
  Steam refuse l'entrée d'un non-ami dans un salon « amis seulement » même avec l'identifiant
  (`EChatRoomEnterResponse` NotAllowed, qui arrive à `OnLobbyEntered:303`). La ligne 383 n'était que la seconde
  barrière.
- `Private` / `PrivateUnique` : il faudrait que l'hôte invite chaque compte connu à l'avance
  (`InviteUserToLobby`), alors que l'hôte ne sait pas qui va arriver ni quand, et que la redirection du dépôt
  se fait par identifiant, sans invitation. Écarté.

## 3. Correction (la plus petite qui tient avec Steam)

Une session ouverte toute seule dont l'hôte sait dire « ce compte est connu du monde » devient un salon
**Invisible** (au lieu de « amis seulement »). L'entrée est ensuite filtrée par l'hôte : ami Steam OU invité OU
compte connu du monde. Tout autre est « refusé » (expulsé par la donnée de salon, aucune clé de connexion donc
aucune connexion P2P).

Changé, dans `Net/Steam/SteamNetLobby/SteamNetLobbyManager.cs` (seul fichier de code touché) :
- `:35` `internal Func<ulong, bool>? KnownAccount` : posé par l'hôte (voir la ligne ailleurs). Nul = comportement
  d'avant (amis seulement).
- `:111-113` (dans `CreateLobby`) : `quiet && type == Friend && KnownAccount != null` -> `k_ELobbyTypeInvisible`.
  `:119` mémorise que le salon est Invisible. Le bloc DEBUG (`PrivateUnique`) reste après : le banc ne change pas.
- `:292-294` (dans `OnLobbyCreated`) : donnée de salon `emp_hidden = 1` sur un salon Invisible.
- `:469` (dans `OnLobbyMatchListComplete`) : la liste en jeu saute les salons marqués `emp_hidden` (un salon
  Invisible est renvoyé par la recherche ; sans cela un inconnu verrait la partie dans l'onglet des salons).
- `:405-418` (dans `OnLobbyChatUpdate`) : `known = IsKnownAccount(user)` ajouté à « ami ou invité » ; le journal dit
  pourquoi un compte est accepté (« account known to this world » / « friend or invited ») et dit un refus
  (« Refused … not a friend, not invited, not known to this world »), qui n'était pas journalisé.
- `:433-446` `IsKnownAccount` : vrai seulement si le salon a été ouvert tout seul (`_quiet`) et que le crochet existe.
  **Une session ouverte à la main (Start Server) passe par les mêmes lignes qu'avant** : `quiet` faux -> type
  `Public`, `_quiet` faux -> jamais « connu », seul ami / invité entre comme avant.

### LIGNE À AJOUTER AILLEURS (je ne l'ai pas faite : `ElinNetHost.cs`)

Fichier `ElinTogether/Net/Host/ElinNetHost.cs`, dans `StartServer`, juste AVANT la ligne
`Session.Lobby.CreateLobby(quiet ? SteamNetLobbyType.Friend : SteamNetLobbyType.Public, quiet: quiet);`
(ligne 36 au moment où j'ai lu, juste après le commentaire « nobody asked for this session ») :

Avant :
```csharp
        // nobody asked for this session: never one a stranger can find
        Session.Lobby.CreateLobby(quiet ? SteamNetLobbyType.Friend : SteamNetLobbyType.Public, quiet: quiet);
```
Après :
```csharp
        // nobody asked for this session: never one a stranger can find, and the players of this world come in
        Session.Lobby.KnownAccount = quiet
            ? user => SavedRemoteCharas.ContainsKey(user) || PlayerRosters.ContainsKey(user) || PcOwners.ContainsKey(user)
            : null;
        Session.Lobby.CreateLobby(quiet ? SteamNetLobbyType.Friend : SteamNetLobbyType.Public, quiet: quiet);
```
Vérifié : cette ligne compile avec ma modification (essai sur une copie du dépôt dans le dossier temporaire, la
copie a été effacée ; les seules erreurs de la copie venaient de GitVersion qui manque hors du dépôt git).
Tant que cette ligne n'est pas ajoutée, rien ne change pour personne (le crochet est nul : salon « amis seulement »
comme en 0.26.510).

Texte du commentaire de `EmpAutoHost.cs` / `SaveDepot.cs` : rien à changer.

## 4. Ce qui est écarté, et pourquoi

- **Public non listé** : n'existe pas (Public est toujours renvoyé par la recherche et vu des amis).
- **Private / PrivateUnique + invitations** : voir 2.
- **Laisser `FriendsOnly` et ne changer que la ligne 383** : inutile, Steam refuse déjà le non-ami avant.
- **Ouvrir en Public** : aurait montré la partie de chacun à tout le monde ; le but de « amis seulement » était
  justement de ne jamais être trouvable.
- **Filtre serveur `NotEqual emp_hidden` dans la recherche** : je ne sais pas ce que Steam fait d'un salon sans la
  clé ; le filtre côté client (`:469`) est sûr, et la barrière réelle est le contrôle de l'hôte.
- **Lire les tables par réflexion depuis `Net/Steam/`** : fragile ; un crochet explicite est plus honnête.

## 5. Preuve du dépôt (pas faite : plus que quelques lignes)

Cas non couvert : un joueur qui a la clé du dépôt mais qui n'a jamais joué ce monde (aucune entrée dans les
tables) et n'est pas ami de l'hébergeur : il entre dans le salon Invisible, est refusé. Pour le couvrir sans jamais
écrire la clé :
- Le joueur calcule `HMAC-SHA256(clé du dépôt, "join|<salon>|<son steam64>")` et le pose en donnée de MEMBRE du
  salon (`SetLobbyMemberData`, après `OnLobbyEntered`) ; la clé ne sort jamais, le lien est lié au salon et au
  compte (un autre compte ou un autre salon ne peut pas le rejouer).
- L'hôte, qui tient le dépôt (`SaveDepot.Holding`), recalcule avec la même clé et accepte si égal. Il doit attendre
  la donnée de membre (elle arrive après « Entered » : traiter aussi `LobbyDataUpdate_t` d'un membre, ou
  réévaluer pendant quelques secondes avant d'expulser).
- Il faut une fonction de calcul dans `SaveDepot.cs` (accès à `DepotPassword`) et un appel à l'arrivée du joueur
  dans `Join` : fichiers que d'autres touchent ; à faire quand ils sont libres. À noter : un HMAC permet de tester
  des mots de passe faibles hors ligne ; avec un mot de passe long (clé GitHub) c'est sans danger.
En attendant : ce joueur doit être ami de l'hôte, ou avoir joué le monde une fois (alors il est « connu »).

## 6. Risques connus

1. **Salles prises par des inconnus.** Un salon Invisible peut être rejoint par quiconque a l'identifiant, et
   `KickMember` ne retire personne : un inconnu au mod modifié pourrait rester dans le salon (16 places) et gêner
   l'entrée des autres. Il n'obtient ni clé ni connexion, ne voit que les noms des membres. L'identifiant n'est
   publié que dans le verrou du dépôt (donc connu de ceux qui ont la clé) et renvoyé par une recherche Steam
   (c'est pourquoi la liste en jeu le cache ; un programme qui ne passe pas par le mod le verrait). Si cela
   arrive en vrai : `Current.SetJoinable(false)` après N refus, ou revenir à « amis seulement ».
2. **Un ancien joueur renvoyé sans le savoir** : un inconnu refusé ne voit aucun message (le mod du joueur se
   retire de lui-même) ; comme avant.
3. **Joueur invisible aux amis dans la liste Steam** : l'entrée par « Rejoindre la partie » du profil de l'ami
   passe par la présence riche (`connect`), inchangée ; l'entrée par la liste des salons du mod ne le montre plus
   (c'est voulu).

## 7. Ce qui reste à essayer à deux PC (deux comptes Steam, pas amis)

Rien de ceci n'est prouvé : non lancé, non testé, seulement compilé (0 erreur, 0 avertissement).
1. PC A (hôte) charge un monde partagé où le compte B a un personnage (ou un `pc_owner`). A n'est pas ami de B.
   Vérifier dans le journal de A : « Lobby created », puis à l'arrivée de B « Connection ready for … (account known
   to this world) ». B rejoint par le verrou du dépôt (bouton « Join ») sans rien régler, joue son personnage.
2. Compte C inconnu du monde, pas ami : rejoint par l'identifiant du salon (à lire dans le journal de A) : le
   journal de A dit « Refused … », C n'obtient pas de clé, ne se connecte pas, A ne voit pas C parmi les joueurs.
   (Premier doute à lever : Steam laisse-t-il bien C et B entrer dans un salon Invisible avec l'identifiant ?)
3. Le salon d'A n'apparaît pas dans l'onglet « Lobby » de C.
4. Régression : A clique Start Server à la main : salon Public comme avant, un non-ami non invité est toujours
   refusé, un compte connu non ami AUSSI (puisque c'est une session manuelle).
5. A et B amis : rien ne change (accepté « friend or invited »).

Au banc : presque rien. D7 (`dev/_tools/depot_suite.py`) joue la redirection par le PORT LOCAL (les deux fenêtres ont
le même compte Steam, le salon est `PrivateUnique` en DEBUG, `Lobby.ConnectLobby` et `OnLobbyChatUpdate` ne sont
jamais atteints : le fichier le dit lui-même, « Ce que D5b et D7 ne jouent PAS »). Ce qu'on peut vérifier au banc :
la compilation et la non-régression de D5b/D6/D7 (le chemin local n'est pas touché). Le contrôle lui-même ne peut
être joué qu'avec deux comptes.
