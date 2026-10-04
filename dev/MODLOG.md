# MODLOG — Elin : voyage indépendant en multijoueur

Objectif : fork d'ElinTogether pour que chaque joueur puisse aller sur la carte de son choix sans suivre l'host.
Fini = un client explore une carte où l'host n'est pas, revient, et l'état de la carte est conservé chez l'host
(vérifié en jeu, log + capture).

## Dossiers

| Chemin | Contenu | Git |
|---|---|---|
| `ElinTogether/` | fork, branche `feat/independent-travel`, remote `upstream` = ElinTogether/ElinTogether | oui |
| `_decomp/Elin/` | Elin.dll décompilé (ILSpy 9.1) — **référence seulement, ne jamais commit ni publier** | non |
| `_tools/` | `ilspycmd.exe` 9.1.0.7988 (la 11.x exige .NET 10+) | non |

Re-décompiler après une mise à jour d'Elin :
`_tools/ilspycmd.exe -p -o _decomp/Elin -r "<Elin>/Elin_Data/Managed" "<Elin>/Elin_Data/Managed/Elin.dll"`

## Jeu

- Elin, Steam 2135150, `C:\Program Files (x86)\Steam\steamapps\common\Elin`
- Unity 2021.3.45f2, Mono, pas d'anti-cheat, BepInEx intégré (`BepInEx/`, `doorstop_config.ini`, `winhttp.dll`)
- Version : **EA 23.350 Patch 1, canal Nightly** (`version.json`) → compiler en `DebugNightly` / `ReleaseNightly`
- Sauvegardes : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`
- `Package/_ModdingKit` présent (requis par le scripting du debug listener)
- `loadorder.txt` : YK Framework (workshop 3400020753), Specific Portraits Settings, **Elin Together workshop
  (3773298709, id `dk.elinplugins.elintogether`)** → à désactiver quand on teste le build de dev (même id)

## Build ElinTogether

- SDK exigé : `11.0.100-preview.5.26302.115` exactement (`global.json`, rollForward disable). Machine : SDK 8 seulement.
- Variables : `ElinGamePath` = racine du jeu ; `SteamContentPath` = `...\steamapps\workshop\content`
- `dotnet restore ./ElinTogether --locked-mode` puis `dotnet build ./ElinTogether -c DebugNightly`
- **Sortie du build = `$(ElinGamePath)\Package\Mod_ElinTogether\`** (écrit directement dans le dossier du jeu)

## Outils de test fournis par upstream (build DEBUG)

- `Emp/EmpDebugListener.cs` : pont TCP JSON sur 127.0.0.1:27551-27560, requêtes `hello`, `state`, `command`,
  `eval` (C# via _ModdingKit), `screenshot`, `load`, `unload` → notre oracle de test
- Console : `emp.add_local` (host UDP 55556), `emp.connect_udp` (client local) → host + client sur la même machine
- `scripts/Start-Multicast.ps1` : upstream lance des instances Steam supplémentaires via Sandboxie (un compte Steam par box)

## Faits moteur (code décompilé)

- **Une seule carte active** : `EClass._zone => core.game.activeZone`, `_map => activeZone.map`.
  `Zone.Activate()` (Zone.cs:639) désactive toujours `activeZone` avant de le remplacer.
  ~2 500 références à `_map/_zone` dans 466 fichiers, ~2 470 à `pc`. → multi-carte sur l'host = infaisable.
- **Rattrapage** : `Zone.Simulate()` (Zone.cs:1297) avance une carte selon `MinsSinceLastActive` / `pendingSimHours`
  quand on y revient → une carte non simulée pendant l'absence est un comportement natif.
- La génération d'une carte se fait dans `Activate()` → l'host ne peut pas générer une carte sans quitter la sienne.

## Architecture ElinTogether (upstream 4a487d1, 2026-09-27)

- Host autoritaire ; les clients sont des répliques de `_zone` de l'host.
- Les joueurs distants sont des `Chara` dans la carte de l'host avec l'IA `GoalRemote`.
- Changement de carte : `ElinNetHostZone.PropagateZoneChangeState` → `ZoneDataResponse` (carte sérialisée) →
  client `OnZoneDataResponse` / `OnZoneActivateResponse` (`ElinNetClientZone.cs`).
- Client : génération désactivée sur les cartes répliquées (`isGenerated = true`, `dateExpire = int.MaxValue`,
  `Region.dateCheckSites = int.MaxValue`).
- `RemoteTravelRegionPatch` : seul l'host se déplace réellement sur la carte du monde.
- FAQ upstream : « Client players can't change map. It's intended. » Rien dans la roadmap (issue #2).

## Conception retenue : autorité de carte déléguée (prêt de carte)

1. Un client quitte la carte de l'host → l'host lui **prête** la carte de destination (une seule autorité par carte).
2. Le client génère / fait tourner la carte en local (instance Elin complète).
3. Au retour (et périodiquement, en cas de déco), le client renvoie la carte sérialisée à l'host
   (= `ZoneDataResponse` en sens inverse) ; l'host l'écrit dans la sauvegarde, `Simulate()` gère le rattrapage.
4. Date, quêtes, factions, personnages restent gérés par l'host via les deltas existants.

Points durs : carte du monde partagée (copie locale non synchronisée ?), deux joueurs sur une carte prêtée
(relais ou interdiction en v1), quêtes host-only, déconnexion avec carte prêtée, génération aléatoire côté client,
personnage distant « hors carte » côté host.

Règle de fork : fonctionnalité derrière une option de config, code dans ses propres fichiers → rebase facile.

## Conception détaillée v1 (voyage indépendant)

Constats code (upstream 4a487d1) :
- Le blocage = un seul patch : `CharaMoveZoneEvent` (préfixe `Chara.MoveZone`, client, zone ≠ `Session.CurrentZone`).
- Upstream avait prévu l'idée : `NetSession.Mode.PartialSync` (« player in the map alone, simulates ») et
  `ShouldSimulate` — **jamais utilisés**.
- Quasi tous les patches commencent par `if (NetSession.Instance.Connection is not { } c) return true;` → sans
  connexion, le jeu se comporte en solo. 122 lectures de `Connection` dans Patches/.
- Host : `OnPeerDisconnected` fait déjà le « départ » (retire perso de la carte, des `States`/`CurrentPlayers`,
  garde la sauvegarde `SavedRemoteCharas`). `PreparePlayerJoin`/`SendSaveProbe` = retour (remet le perso dans la
  zone de l'host + renvoie la sauvegarde → le client reconstruit tout son monde).
- Host : `DisconnectInactive` ne coupe que si le transport est coupé → un client silencieux reste connecté.
- Elin : une carte quittée reste en mémoire (`zone.map`) ; écrite sur disque (`<save>/<uid>/`) seulement à la
  sauvegarde. `Map.Save` exclut les persos globaux (joueurs, compagnons).
- Elin : `CardManager.uidNext` = compteur global d'uid de cartes (objets + persos) → collision si le client crée
  des cartes de son côté.

Protocole (tout derrière `NetSessionRules.AllowIndependentTravel`, config host `Server.IndependentTravel`) :
1. Client `MoveZone(z)` avec z ≠ zone de l'host → `ZoneLeaseRequest(z)`, déplacement bloqué en attendant.
2. Host : zone libre ? → retire le perso du client de sa carte (comme une déco, sans couper), réserve une plage
   d'uid (`uidNext + 1 000 000`), `ZoneLeaseGrant(z, plage, carte si déjà générée chez l'host)`.
3. Client : mode « absent » : `NetSession.Connection` renvoie null (les patches voient du solo, `Transport` garde
   la vraie connexion), sauvegarde bloquée, paquets de l'host ignorés sauf bail/règles/sauvegarde (on note juste
   la zone de l'host), `uidNext` = début de plage, puis `MoveZone` vanilla (génération locale si besoin).
4. Départ de z : `ZoneLeaseRelease(z, carte sérialisée, perso sérialisé, uidNext, rejoin?)`.
   Host : écrit les fichiers de la carte dans `<save>/<uid>/` (décharge sa copie mémoire), `isGenerated = true`,
   remplace son perso distant par celui reçu, `uidNext = max`. Si `rejoin` → `SendSaveProbe` (retour normal).
   Sinon le client enchaîne un `ZoneLeaseRequest` pour la zone suivante.
5. Carte du monde (Region) : bail sans transfert de carte ni upload (copie locale), plusieurs clients possibles.

Limites v1 assumées : sous-zones créées côté client (étages de nefia) non gérées (uid de spatials),
déco pendant l'absence = changements perdus, chat non reçu pendant l'absence, l'host qui entre dans une zone
prêtée garde la priorité (upload du client ignoré), quêtes toujours côté host.

## Premier jalon

Un client entre dans une carte où l'host n'est pas, y dépose un objet, revient ; l'host voit l'objet dans la carte.

## Journal

- 2026-09-30 : recon, clone, décompilation, lecture de l'architecture, choix de conception. Branche créée.
- 2026-09-30 : SDK .NET 11.0.100-preview.5.26302.115 installé en système (installeur officiel, SHA-512 vérifié).
  Upstream compile tel quel en DebugNightly → `Elin\Package\Mod_ElinTogether` (package.xml id `dk.elinplugins.elintogether`).
  `loadorder.txt` : build de dev activé, Workshop 3773298709 désactivé. Elin associe les lignes par chemin d'abord
  (`ModManager.LoadLoadOrder`), donc les deux copies coexistent sans conflit.
  Scripts : `build.ps1` (compile + déploie, refuse si Elin tourne), `use-workshop.ps1` / `use-workshop.ps1 -Dev`.
  Prochaine étape : lancer Elin avec le build de dev, vérifier qu'il charge (BepInEx/LogOutput.log), puis tester
  si deux instances d'Elin peuvent tourner sur ce PC avec un seul compte Steam (host `emp.add_local` + client `emp.connect_udp`).

- 2026-09-30 : **banc de test multijoueur local opérationnel** (host + client sur ce PC, un seul compte Steam).
  Commit `8f73f01` fix(dev) : 3 bugs d'upstream empêchaient le test local sous Windows (client vers `[::]` au
  lieu de 127.0.0.1 ; host qui rejette `emp_not_allowed` hors lobby Steam ; client qui rejoint le lobby Steam
  pendant le handshake et coupe la connexion locale). Scénario complet vérifié 2 fois (log + captures).
  Prochaine étape : le vrai sujet, voyage indépendant (premier jalon ci-dessus).
- 2026-09-30 : **premier jalon atteint**, commit `2d68eae` feat: independent travel through zone leases.
  `python _tools/travel_test.py --zone vernis` (après `mp_test.py`) : 8/8. Le client va seul à Vernis (jamais
  générée chez l'host), dépose sa hache + une pomme créée sur place (uid 1000545, plage réservée), revient ;
  l'host va à Vernis et retrouve la même carte avec les deux objets au même endroit, même uid ; l'inventaire du
  client côté host n'a plus la hache. Captures `_shots/mp-travel-*.png`.
  Piège trouvé : les drapeaux d'une zone (isGenerated…) vivent dans `Spatial.bits` à l'exécution, `_ints[0]`
  n'est rafraîchi qu'à la sérialisation → sans correction, l'host régénérait la zone et perdait les objets.
  Traductions EN/JP (xlsx, réécrit par openpyxl, chargé OK en jeu) + CN (json).

## Vérification approfondie (en cours, 2026-09-30 soir)

`python _tools/travel_suite.py` : 13 scénarios enchaînés + scan des logs (voir la docstring du script).
Relecture indépendante du code (sous-agent) : 10 problèmes signalés, tous vérifiés contre le code/Elin.
Corrigés (non commités, build DEBUG déployé sauf le dernier point) :
- mort d'un client près de l'host → ne déclenche plus de bail (`deathZoneMove`), l'host gère la résurrection
- retour demandé deux fois → garde `_rejoining` côté client, release ignorée côté host si le joueur n'est pas absent
- consommation d'uid : réserve 50 000 au-dessus du compteur (au lieu d'1 M), compteur de l'host avancé seulement
  si le client a réellement créé des cartes (mesure à confirmer par S13)
- jetons de compétence et uid « en attente » du client purgés du perso reçu par l'host
- membres fantômes dans la base de l'host (`FactionBranch.members` garde l'ancien objet) → `RemoveMemeber(old)`
- cache de cartes de l'host : il renumérotait les objets rapportés par le client (cause de l'échec S4) →
  l'host oublie les cartes de sa copie mémoire de la zone avant de la décharger
- actions faites juste avant le départ : l'host ne retire le joueur de sa carte qu'à réception de
  `ZoneLeaseAck`, envoyé après les derniers deltas du client
- retour propre : `Scene.Init(Mode.None)` avant de reconstruire le jeu (103 exceptions → 0) + caches vidés
- sauvegarde auto de l'host au retour d'un client (cartes écrites dans le dossier de save → game.txt cohérent)
- UI session : boutons kick/reconnect basés sur `Transport`, masqués pendant l'absence ; ping désactivé en absence ;
  sortie d'instance → même zone de destination qu'Elin ; libellé de log « Away »
- histoire principale (Player.Flags.OnLeaveZone) non jouée chez les clients ; les autres dialogues du jeu
  (tutoriels…) restent et se ferment d'un clic (la suite les ferme via `RemoveLayer<LayerDrama>`)
- entrée vide dans `_leases` retirée au retour

Run 2 : S1–S4 OK (S4 corrigé), 0 exception des deux côtés. Perturbé ensuite par des actions manuelles dans les
fenêtres (l'host a bougé) : le client absent a correctement rejoint l'host sur la carte du monde.
Découvert : entrer sur une case libre de la carte du monde crée une zone « field » côté client → refusée
(`emp_travel_invalid`) ; l'host crée ses propres zones avec les mêmes uid (collision de spatials, uid 136 vu des
deux côtés). **À traiter en priorité** : c'est un geste de jeu courant.

Suite des corrections (runs 3 à 7) :
- S5 (objet ramassé dans la même frame que le départ, qui s'empile) : la fusion de pile est faite par l'host et
  renvoyée au client, réponse perdue car le client était déjà absent → **barrière de départ** : le client envoie
  `ZoneLeaseAck` après ses derniers deltas, l'host applique tout, renvoie les résultats puis `ZoneLeaseDepart` ;
  le client applique ces résultats avant de partir.
- S10 : un client qui plante pendant son absence n'était jamais expulsé (upstream ne surveille que les joueurs
  présents dans `States`) → le bail restait bloqué → `DisconnectInactive` expulse aussi les absents déconnectés.
- Zones créées à la volée (case libre de la carte du monde, étages de donjon) : la requête porte un
  `LeaseZoneBlueprint` (id, parent, x, y, état) ; l'host crée la zone avec **son** uid (SpatialGen.Create +
  elomap), le client renumérote sa zone toute neuve (`AdoptHostUid`). Suivi des zones créées localement via le
  postfix `SpatialGenEvent` (hors application de deltas). S14 (client absent) et S15 (client avec l'host) OK.
  Nom `ZoneBlueprint` déjà pris par Elin (classe globale) → `LeaseZoneBlueprint`.
- Tests : dialogues du jeu (fée, tutoriel Nerun…) fermés des deux côtés comme un clic ; marqueurs = seau posé à
  4 cases (les compagnons de l'host ramassent et mangent les pommes au point d'arrivée — gameplay, pas un bug).
- Run 6 : 40/42, les 2 échecs = erreur du test (position de la hache), corrigée.
- **Run 7 (propre, depuis zéro) : 42/42, 0 exception** host et client (`_shots/suite-run7.log`).
- Observé (upstream, pas lié) : un client tout juste lancé peut rater le 1er handshake (réponse de version
  trop tardive, timeout host) ; le 2e essai passe.

Limites restantes connues : déco pendant l'absence = changements perdus ; chat non reçu pendant l'absence ;
deux clients dans la même zone prêtée refusés ; persos globaux modifiés pendant l'absence (compagnons, PNJ
recrutés) non remontés ; quêtes côté host.

## Parité — étape 2 : zones partagées entre clients (conception)

But : B entre dans la zone Z que simule le client A → ils jouent ensemble comme avec l'host.
Principe (« zone host ») : A ouvre une **2e session ElinTogether limitée à Z** (un ElinNetHost de plus dans son jeu)
et B s'y connecte avec un 2e ElinNetClient, en plus de leur lien avec l'host H. Toute la synchro existante
(combat, objets, mouvements…) est réutilisée entre A et B. Upstream l'avait esquissé
(`NetSession.Mode.FullSync` : « players share the same map, first player simulates ») sans l'implémenter.

État par jeu :
- `NetSession.Transport` = lien avec H (toujours) ; `NetSession.ZoneSession` = session de zone (host chez A,
  client chez B) ; `Connection => ZoneSession ?? (IsAway ? null : Transport)` → les patches voient la session de zone.
- A : `AwayZone = Z`, autorité (bail, checkpoints, release) ; B : invité de Z (`AwayZone = Z`, pas d'autorité).
- La zone de H suivie par le lien principal dans un champ à part (`HostZone`), plus `Session.CurrentZone`
  (qui redevient « la zone que je réplique / simule » pour la session de zone).
- Les ~15 `ResetSession()` des composants réseau (retour au titre !) → pour une session de zone : on ne ferme
  que la session de zone. `ElinNetClient.Stop()` ne doit pas renvoyer au titre pour une session de zone.
- Pas de lobby Steam pour la session de zone ; port : local debug = 55600 + identité, Steam = P2P port virtuel 1.

Protocole (B demande Z tenue par A) :
1. H → B `ZoneLeaseGrant(Guest)` ; B quitte proprement sa position actuelle (barrière ack si avec H, release
   de sa zone si absent) → H a le perso à jour de B.
2. H → A `ZoneGuestRequest(B, perso de B)` ; A ouvre sa session de zone si besoin, enregistre B.
3. A → H `ZoneGuestReady` ; H → B `ZoneLeaseDepart(invité de A, adresse)` ; B se connecte à A : handshake,
   sauvegarde de A (SaveDataProbe) avec le perso de B, données de Z → B dans Z en réplique de A.
- Checkpoints/release de A : incluent les persos de ses invités (A en est l'autorité).
- Chat : toujours par le lien principal (H relaie à tout le monde), pas par la session de zone.
Sorties : B part (A rend le perso de B à H, puis B voyage) ; A part (passation : Z confiée à B, B recharge Z en
autorité) ; H entre dans Z (rappel de A et de ses invités) ; plantage de A (B rejoint H) ; plantage de B.

Banc de test : identités de test (commit 1781eea) → `mp_test.py --clients 2` = host + 2 joueurs distincts.

### État au 2026-10-01 01:25 (pause, reprise prévue 3 h en /loop) — historique, voir plus bas
- `python -u _tools/shared_suite.py > _shots/shared-run3.log` : 10/18. Marche : bail invité, session de zone de A
  (port 55620), connexion de B, sync A→B. Échoue : B vu sur la carte de A, sync B→A (objet, déplacement),
  G3/G4 (perso de B dans le checkpoint de A), G5, G6 (B ne retombe pas chez H quand A est tué).
- `_shots/elin3-player.log` (B) : 800 NRE, dès `Requesting zone lease Zone_vernis@0` (01:13:20) :
  `PauseGame.OnGetShouldPauseGame` (l.26), `NetPeerState.FindChara` (l.41), `NotificationExceedParty.Visible`
  (`EClass.pc.party.Count()`), `ElementContainerCard.ValueBonus`, `HomeResourceSafety`, `WidgetStatsBar`
  → piste : chez B, `pc.party` est **null** (ou `pc`/faction incohérents) après le SaveDataProbe de la session de
  zone de A (le perso de B vient du monde de A). Vérifier `pc.party`, `pc.faction`, `pc.homeBranch` chez B via eval.
- Ensuite : rendre robustes PauseGame/FindChara, relancer shared_suite (run4), puis passation quand A part avec
  des invités (aujourd'hui popup `emp_travel_guests_present`), rappel par H avec invités, travel_suite (régressions),
  commit + Co-Authored-By.

### 2026-10-01 3 h — causes trouvées (run3 → run4 : G1–G4 au vert)
- NRE de B : H retire B de sa carte (`DepartFromHostMap` → `CharaRemoveFromGameDelta` diffusé à tous) ; B, encore
  en attente du départ (invité), l'appliquait **à son propre pc** → `pc.party = null`, pc hors de `globalCharas`.
  → `CharaRemoveFromGameDelta` ignore `chara.IsPC`.
- A ne voyait pas B / sync B→A cassée : `CardCache.Add` côté « host » **renumérote** une carte si l'uid est déjà
  pris dans le cache. Chez A, d'anciennes entrées (copies reçues de H) occupaient les uids du perso de B → le perso
  de B devenait 478 au lieu de 477 (SaveDataProbe envoyé avec 478, état joueur avec 477, checkpoint refusé par H
  « uploaded chara 478, expected 477 »). → `ReplaceRemoteChara` oublie d'abord le cache aux uids de la copie reçue.
- G2 : un client ne crée pas d'objet à partir de rien (`ZoneAddCardEvent` → `DelayDestroy`) : le test fait poser à B
  un vrai objet de son sac (`DropThing`).
- G6 : un client de session de zone ne voyait jamais la perte de A (`ProblemDetectedLocally` n'est pas géré,
  seul `ClosedByPeer` l'est, et le timeout client est `#if !DEBUG`) → `ElinNetClient.Update` : session de zone
  et `!IsConnected` → `EndSession`.

### Passation de zone (A part, ses invités restent)
- A n'est plus bloqué : en partant (`HandBackAwayZone`), il rend Z à H (carte + persos des invités) et ferme sa
  session de zone.
- H (`HandOverZone`, à la release de Z ou à la déconnexion de A) : le 1er invité reçoit `ZoneLeaseGrant{Handoff}`
  (nouveau bail, nouvelle plage d'uid, pas de carte) ; les autres invités → `ZoneGuestRequest` vers lui puis
  `ZoneLeaseDepart(Guest)` ; si H est en route vers Z (rappel) → `ZoneLeaseRecall` aux invités ; invités en
  attente chez A → refusés.
- B (`TakeOverZone`) : garde sa copie vivante de Z, ferme la session de zone, `IsGuest = false`, uids en attente
  → plage reçue, persos des autres joueurs retirés. Session de zone fermée sans nouvelle de H : B joue seul
  (Connection null) et attend 30 s (`UpdateHandoffWait`) avant de rentrer chez H.
- `ReplaceGuestCharas` n'écrase plus le perso d'un invité parti entre-temps (il a apporté une copie plus récente).
- Tests : G7 (A rentre → B reprend Vernis, A revient en invité de B, H arrive → rappel de B et de A) et G6 revu
  (A tué → B garde Vernis, y pose un objet, rentre ; H le retrouve à Vernis).

### Résultat étape 2 (2026-10-01 03:50) — commitée
- `shared_suite.py` (run6) : **26/26**, 0 exception sur les 3 jeux. `travel_suite.py` (run9) : **49/49**, 0 exception.
- 3 joueurs (2026-10-01 08:12) : `_lab/Elin4` (identité 4, `make_lab.py Elin4 4`), `mp_test.py --clients 3`,
  `trio_suite.py` T1–T5 : **24/24**, 0 exception sur les 4 jeux (≈2,3 Go par instance, 3,4 Go restants sur 20).
  Couvert : 2 invités chez A (relais entre invités), passation à 2 invités (B hérite, C rejoint B), rappel par H
  avec hôte de zone + invité, plantage de l'hôte de zone avec 2 invités (C hérite, A rejoint C).
- Reste (non bloquant) : test réel à 2 PC via Steam (sessions de zone par `ConnectSteamUser`/SDR, jamais testé
  hors UDP local).

## Décision quêtes (2026-10-01, à faire après les compagnons)
Quêtes **communes** à tous (comme Elin : un seul `game.quests` par monde) : n'importe quel joueur prend, avance,
rend ; c'est fait pour tout le monde. À faire : changements de quête faits en voyage seul → envoyés à l'host et
rediffusés ; ouvrir histoire principale / quêtes à drama / donjons de quête aux clients (bloqués aujourd'hui,
`BlockClientQuestPatch`). Proposé, non confirmé : récompense (objets, argent) à celui qui rend, renommée/karma/
histoire communs ; limite 5 quêtes aléatoires → 5 + 2 par joueur connecté.

## Parité — étape 3 : compagnons (conception)
Elin : **un seul groupe** (`pc.party`), chef = pc de l'host ; `AI_Idle` fait suivre `party.leader`, seul le chef
entraîne le groupe dans `Chara.MoveZone`. ElinTogether met les joueurs distants et tous les alliés dans ce groupe
(alliance/hostilité, pause, minicarte, sommeil en dépendent) → on garde le groupe unique et on ajoute un
**propriétaire** par compagnon.
- `emp_owner` (int, `Card.SetInt`) = uid du perso du joueur propriétaire ; absent = le chef (host).
  Recrutement par un client : posé par l'host avant `MakeAlly` (la delta `CharaMakeAllyDelta` le transporte) ;
  en voyage seul / hôte de zone : posé sur le pc local.
- Suivi : transpiler sur `AI_Idle.Run` (MoveNext) : `party.leader` → propriétaire s'il est vivant dans la zone.
- Voyage seul : `Chara.MoveZone` du pc (non chef, sans connexion) entraîne ses compagnons dans sa copie ;
  l'host retire ces compagnons de sa carte au départ (`DepartFromHostMap`), les garde dans le groupe hors carte
  (`currentZone = null`) ; checkpoints / release (`ZoneLeaseRelease.Companions`) remplacent ses copies ;
  au retour (ou à la reconnexion), placés près du joueur (`CardGenDelta` + `CharaMakeAllyDelta`).
- `CharaRemoveFromGameDelta` n'efface jamais un compagnon du joueur local (même piège que le pc de B).
- Zones partagées : `ZoneGuestRequest.Companions` (copies de l'host), `RegisterGuest` → `ReplaceCompanions`,
  `BringCompanions` à l'arrivée ; checkpoints/release de l'hôte de zone : `GuestCompanions` ; un invité qui part
  emmène les siens (`TakeCompanionsAlong`) ; `TakeOverZone` retire aussi les compagnons des autres joueurs.
- Renvoyé en voyage (absent de l'envoi) → l'host le retire du groupe, efface le propriétaire, l'envoie chez lui.
- Reste : limite d'alliés par joueur (`Player.MaxAlly` = pc de l'host, compte tout le groupe), mort d'un
  compagnon en voyage (non testé), compagnons des joueurs qui ne reviennent jamais (restent hors carte).

### Résultat étape 3 (2026-10-01 ~11:50) — commitée
`run_all.sh` : companion 23/23, party 27/27, travel 49/49, shared 26/26, trio 24/24 ; 0 exception.
Reste noté : 2 destructions locales de copie de chara chez un client (recrutement, retour) — sans effet (plus
envoyées à l'host), à comprendre un jour.

## Première version pour test réel à deux PC — 2026-10-01 16:50
- `make_release.ps1` → `_release/ElinTogether-independance.zip` (build ReleaseNightly, commits `c16ddad` + `fd04af5`,
  Elin EA 23.350 Patch 1). Contient `Mod_ElinTogether/`, `Installer.bat` (`install.ps1`), `Desinstaller.bat`,
  `LISEZMOI.txt`. Modèle des scripts : `_release/template/`. L'installateur trouve Elin (registre Steam +
  `libraryfolders.vdf`), exige YK Framework (Workshop 3400020753), met l'ancienne copie dans
  `Elin\_ElinTogether_sauvegarde`, active la copie locale et désactive la Workshop dans `loadorder.txt`.
  Essayé sur ce PC (2 fois) : OK.
- Le jeu de l'utilisateur a maintenant le **build Release** dans `Package/Mod_ElinTogether` : relancer `.uild.ps1`
  (Debug) avant de reprendre les tests automatiques. `Save/config.txt` remis en plein écran 1920×1080
  (`_backup/config.test-fenetre.txt` = version fenêtrée). Sauvegardes copiées :
  `_backup/sauvegardes-avant-test-ami-20261001.zip`.
- Décision utilisateur : arrêter les longues séries de tests (trop lentes, trop d'échecs dus aux tests eux-mêmes),
  aller au test réel avec un ami, corriger ensuite ce qu'ils trouvent avec des tests courts (`--reuse`, une seule
  série de fenêtres, seulement ce qui a changé). Fenêtres de test muettes (`-empmute`).
- Non vérifié : chemin Steam (lobby, SDR, sessions de zone en P2P) ; erreur host vue une fois à 3 joueurs
  (`IndexOutOfRangeException` dans `OnZoneDataReceivedResponse`, pile perdue) ; pas de passe complète après les
  derniers changements. En cas de souci chez eux : demander `Player.log` et `ElinMP/Logs/Session_*.log` des deux joueurs.

## Pause du 2026-10-01 ~17:30 (l'utilisateur relancera plus tard) — reprendre ici
- Test manuel de l'utilisateur (host + joueur 2 sur ce PC) : **« quand le host change de carte il tp les joueurs
  sur lui »** = comportement upstream (le groupe du host entraîne tout le monde). Correction écrite, compile,
  **non testée en jeu, non commitée** : `ElinNetHost.LeavePlayersBehind` (appelé par `TryEnterZone`) : avec
  « Voyage indépendant », les joueurs présents quittent la carte du host (`DepartFromHostMap`), le 1er reçoit
  `ZoneLeaseGrant{Handoff}` et garde la carte telle qu'elle est chez lui (`TakeOverZone` accepte maintenant le cas
  « sur la carte du host »), les autres `ZoneLeaseGrant{Handoff, Guest}` → `StayAsGuest` → invités du 1er ; sur la
  carte du monde chacun garde sa copie. Pour suivre le host : prendre la même sortie (rejoin).
- **État du dossier du jeu : build DEBUG avec cette correction** (`Package/Mod_ElinTogether`). Le zip pour l'ami
  (`_release/ElinTogether-independance.zip`) est le build Release d'avant, SANS cette correction. Avant de jouer avec
  l'ami : relancer `make_release.ps1` (refait le zip et remet le Release dans le jeu), les deux joueurs doivent avoir
  le même zip.
- Attention au lancement manuel : si l'utilisateur clique « Continuer » dans la fenêtre du host pendant le
  chargement, c'est sa vraie partie (`Cloud Save/world_3`) qui est hébergée au lieu de `world_lab` (arrivé une fois,
  rien n'a été écrit ; copie : `_backup/cloud-world_3-20261001-1712.zip`).
- Méthode demandée : tests courts, une seule série de fenêtres, pas de longues passes ; fenêtres muettes.

## Quêtes communes (étape 4) — 2026-10-01 soir, commits `1e1be22` + `cde3425`

- **L'host ne traîne plus les joueurs** (`LeavePlayersBehind`, `leave_suite.py` 11/11) : quand l'host change de carte,
  les joueurs restés sur l'ancienne en héritent (le premier la simule, les autres sont ses invités).
- **Quêtes aléatoires en voyage** : un joueur parti seul accepte / avance / termine dans sa copie du monde, et le
  dit à l'host par le lien principal (`QuestAwaySync.Send`, listes blanches dans `ElinNetHostUpdate` et
  `ApplyChatWhileAway`). L'host tient le seul journal de quêtes et relaie aux autres. Numéros de quêtes : chaque
  bail réserve 10 000 numéros (`ZoneLeaseGrant.QuestUidRangeStart`). Vernis (uid 16) n'est pas une `Zone_Town` :
  pas de quêtes aléatoires, le test utilise Lumiest (42).
- **Récompenses** : à celui qui rend la quête (`QuestRewardPatch.GiveTo` sur `Player.DropReward`) ; rien chez l'host
  quand la quête a été rendue en voyage (`GiveNothing`). Renommée et karma : communs.
- **Quêtes d'histoire par un client sur la carte de l'host** : `QuestManager.Start` côté client garde une copie
  sans numéro (uid < 0, `SharedQuests.AwaitHost`, épargnée 10 s par `QuestSynchronizationContext`) et envoie
  `QuestStartDelta` ; l'host lui donne son numéro, la démarre (`OnStart` chez l'host) et la diffuse. `ChangePhase`
  d'un client part à l'host avec l'étape d'origine (`From`) : ignoré si quelqu'un a déjà avancé la quête.
  Tant que la copie n'a pas de numéro, les deltas la désignent par son id (`SharedQuests.Find`).
  Toujours bloquées pour un client : les quêtes à zone propre (`UseInstanceZone`).
- **Souvenirs de dialogue** (`player.dialogFlags`) : comparés deux fois par seconde à ce qui a été partagé
  (`DialogFlagSync`, `DialogFlagDelta` union 807), dans les deux sens, y compris en voyage.
- **Erreur à 3 joueurs** (`IndexOutOfRange` dans `OnZoneDataReceivedResponse`) : `RemoveLeftOverCharas` retirait de la
  carte de l'host un joueur qui n'y était pas, avec une position d'une autre carte (hors limites sur une petite
  carte). `RemoveRemoteChara` et `CharaRemoveFromGameDelta` ne touchent plus la carte dans ce cas. Diagnostic fait
  par lecture du code et des journaux, **pas retesté à 3 joueurs**.
- Tests : `quest_suite.py` Q1–Q7 30/30 (host + 1 client, ~2 min, sur instances déjà lancées).
- **Bot** `_tools/bot.py` : joue au hasard sur le client (ou l'host avec `--who host`), vérifie toutes les 4 actions
  (jeux vivants, pas d'exception, même journal de quêtes, mêmes joueurs/sacs/or/objets sur la même carte), traverse
  l'écran de mort comme un joueur. `--seed N` rejoue la même suite. Trois passages (79, 44, 104 actions) : aucun
  problème ; une mort en voyage → retour à la base correct. Actions à ajouter : creuser, récolter, construire,
  coffres, lancer, compagnons, dormir, se déconnecter/reconnecter.
- **Reste à faire pour l'histoire** (inventaire par lecture du code, non testé) : ce que les dialogues font en dehors
  des quêtes reste local au client — `invoke` de `DramaOutcome` (combat du tutoriel `QuestDefense_0/1`,
  `OnClaimLand`, emménagements `MeetFarris`/`AfterCrystal`, récompenses), `drop`, `addKeyItem`, `modAffinity`,
  drapeaux `player.flags` (dette de Loytel). Piste : envoyer le nom de l'`invoke` à l'host, qui l'exécute sous
  `GiveTo` + `Simulate`. `QuestDeliver.OnStart` donne l'objet à `EClass.pc` (l'host).
- Deux sessions Claude lancent Elin sur ce PC (celle-ci et `VisibleEquipment`) : ne lancer que si aucun `Elin.exe`
  ne tourne, ne tuer que ses propres PID.

## Soirée du 2026-10-01, 21:50–22:40 — code écrit SANS test en jeu (l'utilisateur se sert du PC)

Commits `70ff98d` et `254974c`. **Tout ce qui suit compile (Debug et Release) mais n'a jamais tourné.** Premier
geste à la reprise : `mp_test.py` puis `quest_suite.py` (choisit seul P1–P4/P11 ou Q1–Q4/Q11 selon l'option).

- **Cause de la quête disparue (essai à 4)** : elle a expiré chez l'host. Sur la carte du monde l'horloge de l'host
  avance vite ; un joueur en voyage a la sienne. `Quest.Fail` n'était pas synchronisé. Fait : `QuestFailDelta` 810,
  et `QuestStartDelta.Now` pour que le délai garde le même temps restant sur l'horloge de chacun.
- **Relecture par un agent** des commits `cde3425` et `23f4eee`, 8 points, 7 traités :
  étapes de quête rejouées par les joueurs qui ne font que les recevoir (maintenant : phase + journal seulement) ;
  quête d'histoire lancée/terminée en voyage → l'host exécute `Start()`/`Complete()` sans récompense (suites de
  quêtes) ; état d'une quête partagé hors phase (`SharedQuests.TellChanges` : hash du JSON toutes les 0,5 s →
  `QuestUpdateDelta`, appliqué par copie des champs `[JsonProperty]` dans l'objet existant ; sert à la dette de
  Loytel et à `setQuestClient`) ; une quête lancée par dialogue chez un client garde son objet et prend le numéro de
  l'host ; cible du dialogue cherchée par uid ; `daysAfterQuestExploration` et `magicChestSent` restent à l'host ;
  gacha non offert deux fois. Non traité : un client peut faire créer n'importe quel objet à l'host (triche).
- **Décision de l'utilisateur (22:00)** : quêtes aléatoires, renommée et karma **par joueur**, histoire commune.
  Option host `PersonalQuests` (cochée par défaut). `PersonalQuests` (côté joueur : remise en place après chaque
  chargement du monde, expiration sur sa propre horloge, envoi de la renommée), `ElinNetHostPersonalQuests`
  (`personal_quests` et `player_standing` dans la sauvegarde ; nouveau joueur : renommée 0, karma 30),
  `PlayerStandIn` (l'host remplace `player.chara` par le joueur le temps de `quest.Start()` / `Complete()` ;
  `ModFame`/`ModKarma` redirigés vers lui), deltas 811–814. Les quêtes à donjon propre restent bloquées pour un client.
- Une deuxième relecture par agent porte sur ces deux commits.
- Autre conversation proposée à l'utilisateur : idées de nouveaux mods pensés pour le multijoueur.

### Suite de la soirée (22:40–23:10), toujours sans test en jeu

- `0a77c9d` bot du menu : actions outil / construit / coffre (avec la case « Bots do everything ») ; l'host donne
  un kit au joueur qui arrive dans les 4 minutes après le lancement d'un bot (`EmpBotLauncher.Tick`).
- Choix du personnage à la connexion (option host `ChooseCharacter`, cochée par défaut) : `PlayerRosters`
  (`remote_chara_roster` dans la sauvegarde) garde tous les personnages d'un joueur ; `PreparePlayerJoin` envoie
  `SessionCharaSelectRequest` s'il en a au moins un ; le client affiche `Dialog.List` (ses personnages +
  « A new character ») et répond `SessionCharaSelectResponse` (0 = nouveau → création habituelle). Le bot du menu
  et `mp_test.py` cliquent le premier choix. Les quêtes, la renommée et l'argent d'expédition sont rangés par
  personnage, ils suivent donc le personnage choisi.
- Demandes notées : fenêtre d'échange entre joueurs ; idées de nouveaux mods (autre conversation, lancée).

## Nuit du 2026-10-01 au 02 (PC libre de ~23h05 à 8h00) — tenir cette section à jour

État à 23h00 : 7 commits jamais lancés en jeu : `70ff98d`, `254974c`, `0a77c9d`, `53bd50d`, `85a08db`, `933330b`,
et le dernier (numéros en double). Build Debug installé = avant `254974c`.

Chasse aux conflits par trois agents (lecture seule), demandée par l'utilisateur :
- **Deux joueurs sur la même chose** (rapport reçu, `933330b`) : `ThingRequest` prenait dans une pile le nombre
  demandé sans le borner (copie d'objets) et pouvait sortir un objet du sac d'un autre joueur ;
  `CardTryStackToDelta` idem ; sanctuaire utilisable deux fois ; impôt payé par le client ET par l'host.
  Non traité : deux achats quasi simultanés payés une seule fois (`CardModCurrencyDelta`), construction de deux
  joueurs sur la même case (deux objets consommés), pile « fantôme » après 10 s au curseur, dernier emplacement
  d'un coffre rempli par deux joueurs, et les actions prédites chez le client sans retour arrière (équiper, donner,
  banque, impôt).
- **Numéros en double** (rapport reçu, dernier commit) : plages de numéros (cartes et quêtes) oubliées quand l'host
  redémarre → `lease_range_floor` dans la sauvegarde ; étage de donjon créé deux fois quand un joueur parti avant
  descend à son tour → `CreateClientZone` réutilise l'existant ; escalier/tente qui gardait l'ancien numéro de zone
  → `AdoptHostUid` ; compteur de cartes réglé sur le dernier numéro reçu au lieu du suivant ; `ForgetCachedCard`
  qui évinçait une carte plus récente ; expédition qui ignorait les autres personnages d'un joueur.
  Non traité : invité resté seul à la passation sans plage réservée ; plages sans borne haute ; `CardCache.Add`
  qui renumérote sans prévenir personne.
- **Pendant les transferts** (rapport reçu 23h00, 10 points). Traités dans `4ca15eb` : joueur refusé comme invité
  juste après avoir quitté la carte de l'host qui restait muet (`returning` tient compte de `_rejoining`) ; dépôt à
  la caisse ou paiement reçu en voyage → sauvegarde immédiate (`_nextCheckpoint = 0`) ; pas d'écran de choix du
  personnage pour les invités d'une session de zone. **À traiter cette nuit, avec tests** :
  (2) rappel par l'host avec invités : l'invité continue de jouer seul jusqu'au rappel puis envoie son personnage,
  ce qu'il a ramassé entre-temps existe en double, ce qu'il a posé est perdu ;
  (3c) banque et boîte de livraison vidées au départ et jamais renvoyées ;
  (4) invité qui passe directement dans la zone d'un autre joueur : rien n'est envoyé, retour en arrière jusqu'à 60 s ;
  (5) monture / parasite : l'animal monté existe deux fois au retour ;
  (6) plantage du détenteur avec invités : ce qu'il a posé depuis sa dernière sauvegarde revient dans son sac ;
  (7) messages de l'host reçus pendant le chargement d'un client jetés au lieu d'être gardés ;
  (8) actions locales pendant les fenêtres fermées (après l'accord de départ, pendant le retour) ;
  (9) bail fantôme quand une reprise de carte annule une demande en cours ; `_pendingHostMove` jamais effacé ;
  (10) bail accordé pour la zone où l'host est en train d'entrer ; PNJ globaux d'une carte louée jamais renvoyés.

Suivi de la nuit :
- 23h07 : la session « idées de mods » (dossier `Sortileges`) avait deux fenêtres Elin ouvertes → prévenue par
  message, fenêtres fermées ; elle a répondu qu'elle ne lance plus Elin avant 7h45 (**lui écrire quand le jeu est libre**).
- 23h19 : **premier passage en jeu de tout le code de la soirée : `quest_suite.py` 53/55**, les 2 échecs sont de
  vieux journaux des bots de l'après-midi (supprimés). Quêtes par joueur P1–P4 et P11, histoire Q5–Q10 : tout passe.
  Démarrage lent ce soir (6 min pour host + client).
- 23h20 : écrit pendant ce test, puis compilé pour le passage suivant : invité qui change de carte envoie son
  personnage ; `IsInTransfer` / `UpdateTransferLock` (entrées du joueur bloquées pendant un transfert, 30 s max ;
  le bot attend aussi) ; `ElinDeltaManager.HoldForIncomingMap` (messages de l'host gardés pendant le chargement
  d'une carte, seulement quand le jeu n'est pas démarré). Nouveau test `chara_suite.py` (C1–C3, choix du personnage).
- 23h30 : build avec ces trois changements → **`quest_suite.py` 53/53**. `chara_suite.py` **10/10** (reprendre son
  personnage, en créer un nouveau, retrouver le premier avec sa renommée). Piège de test : après
  `ResetSession()` le client est déjà à l'écran titre, un second `scene.Init(Title)` lève une exception.
- 23h34 : **passe complète lancée** (`_shots/night-runall.log`). Premier résultat : `travel_suite` 12/13, arrêtée à
  S3. **Pas une régression de ce soir** : S3 attendait que le client suive l'host quand l'host change de carte, ce
  qui n'est plus vrai depuis « l'host ne traîne plus les joueurs » (`1e1be22`) ; cette suite n'avait pas été
  relancée depuis. `host_goto` corrigé (le client rejoint l'host de lui-même). Les autres suites déplacent aussi
  l'host (`companion` 205, `party` 100, `shared` 153/205/248, `trio` 148) : **revoir ces scénarios un par un** à la
  fin de la passe avant de conclure à une régression.
- 23h50 : quêtes à donjon propre pour un client, phase 1 écrite d'après `PLAN_quetes_donjon.md` (sources
  seulement, compile, **non commitée, non installée**) : déblocage si `PersonalQuests.InstancesEnabled` ;
  `LeaseZoneBlueprint.Instance` ; côté host `CreateQuestZone` (jamais réutilisée, hors carte du monde, pas
  d'annonce aux autres) et `DestroyQuestZone` au retour du bail ; `LeasedZonePatch` (l'host ne supprime pas une zone
  louée en sauvegardant) ; côté client `PersonalQuests.LeaveInstance` note le résultat en sortant et
  `SettleOutcome` l'applique une fois arrivé quelque part. Phase 2 (les autres joueurs entrent dans la zone) : pas
  faite, une zone de quête n'a pas de porte. Test prêt : `instance_suite.py` (I1–I3).
- 01h16 : **fin de la passe complète (build de 23h34)**. combat 15/15. travel 12/13 et companion 19/20 : scénario
  périmé (corrigé). economy 22/24, shared 12/17, trio 17/22 : **vraie régression** — sur la carte d'un joueur,
  l'invité recevait un nouveau numéro de personnage (« uploaded chara …, expected …, keeping host copy ») et
  devenait invisible pour son hôte. Cause : ma modification de `ForgetCachedCard` (ne retirer du cache que si
  l'objet est le même) ; or `ReplaceRemoteChara` compte justement sur le retrait par numéro pour que la copie
  envoyée prenne la place de l'ancienne. **Annulée.** party, leave, quest, chara : lancement raté (jeu très lent
  cette nuit, host > 3 min à charger) → attente du chargement portée à 10 min dans `mp_test.py`.
  Bruit sans gravité : à chaque connexion, 8 avertissements « Card uid conflict … refusing incoming » — les
  messages gardés pendant le chargement (`HoldForIncomingMap`) rejouent l'équipement du nouveau personnage, déjà
  présent dans le monde reçu.
- 01h20 : build (avec les quêtes à donjon, non commitées) et **deuxième passe** en arrière-plan (tâche b2egb7erl) :
  shared, trio, economy, party, travel, companion → `_shots/night-runall2.log`, puis `mp_test` + leave, quest,
  chara, transfer, instance → `_shots/<suite>-night2.log`. Deux agents en parallèle : plan de la fenêtre d'échange ;
  état des lieux karma / affinité / guildes.
- 01h40 : la deuxième passe avance lentement : chaque client met ~2 min à s'ouvrir (le mod `VisibleEquipment` de
  l'autre session est maintenant dans `Package` et se charge dans toutes les fenêtres). `shared_suite` : lancement
  raté (commande de connexion sans réponse en 30 s) → `mp_test.py` et `emp.py` rendus plus patients (appels 90 s,
  connexion 180 s, attente du client 300 s). **À relancer : shared_suite.**
- 01h40 : **fenêtre d'échange entre joueurs écrite** d'après `PLAN_echange.md` (sources seulement, compile, non
  commitée, non installée) : `Helper/PlayerTrade.cs` (public, pilotable par le pont : `Invite`, `Accept`, `Offer`,
  `SetGold`, `Confirm`, `Cancel`, `Describe`), `Models/Delta/Inv/PlayerTradeDeltas.cs` (unions 704, 705),
  `Components/LayerPlayerTrade.cs` (fenêtre), `Patches/PlayerTradePatch.cs` (remplace « actTrade » du jeu sur un
  autre joueur), option host `PlayerTrade` (`AllowPlayerTrade`, clé 7). Test prêt : `trade_suite.py` (R1–R3).
  Plans des agents enregistrés : `PLAN_echange.md`, `PLAN_parite.md` (karma, affinité, guildes).
- 01h45 : écrit aussi d'après `PLAN_parite.md` (sources seulement, compile, non commité) : **guildes communes**
  (`DialogFlagSync` partage type / grade / contribution des quatre guildes, clés `g:<guilde>:t|r|e`) et **affinité
  commune** (`CharaAffinityDelta` union 226, `CharaAffinityPatch` sur `Chara.ModAffinity` : le jeu de l'acteur tire
  les dés, l'host additionne et diffuse la valeur ; un jeu qui rejoue l'action d'un autre ne tire pas). Test prêt :
  `parity_suite.py` (Y1 affinité, Y2 guilde). Karma et crime d'un client (partie A du plan) : pas commencé.
  **Pile non commitée à tester après la passe, dans cet ordre** : annulation ForgetCachedCard (déjà dans le build de
  la passe), quêtes à donjon (idem), puis échange, guildes, affinité (pas dans ce build).
- 02h51 : **fin de la deuxième passe** (build de 01h20) : economy **25/25**, party **28/28**, leave **13/13**,
  quest **55/55**, chara **12/12**, transfer **11/11** (banque et caisse en voyage). trio 21/22, travel 35/36,
  companion 26/27, instance : chaque fois un **scénario de test** en cause, pas le mod — S14 et T4 supposaient que
  les joueurs suivent l'host ; K8 ne répondait pas à l'écran de choix du personnage après relance ; le test des
  quêtes à donjon laissait ouvert le dialogue « quête réussie », qui retient le déplacement suivant. Scénarios
  corrigés (`with_host` patient, `join_client` dans K8, `dismiss_dialogs` dans instance_suite).
- 02h56 : **`instance_suite.py` 20/20** : un client prend une quête à donjon chez l'host, entre dans sa zone, tue,
  ressort, est payé ; échec quand il ressort sans rien tuer ; la zone disparaît chez l'host.
  Commit : quêtes à donjon phase 1 + annulation de `ForgetCachedCard`.
- 03h00 : build avec l'échange, les guildes et l'affinité (non commités) ; `trade_suite`, `parity_suite`,
  `quest_suite` en cours (tâche birghxwpq, `_shots/<suite>-night3.log`). **Reste à relancer : shared_suite,
  trio_suite, travel_suite, companion_suite** (scénarios corrigés).
- 03h05 : lancement raté une fois de plus (l'host ne répond plus pendant plusieurs minutes quand host et client
  démarrent ensemble ; seul, il répond). Contournement : `mp_test.py --clients 0` puis `launch_client.py` (nouveau).
- 03h30 : **`trade_suite.py` 19/19** et **`parity_suite.py` 9/9**. Commits `23fd93b` (affinité et guildes communes),
  `b730280` + `a50f081` (fenêtre d'échange). Captures : `_shots/mp-trade-window-A.png`,
  `_shots/mp-trade-invite-host.png`. Pièges de test : un objet donné peut s'empiler sur un autre (utiliser le
  numéro rendu par `AddThing`, compter par type) ; chez un client, le personnage de l'host n'est ni `IsPC` ni
  `remote_chara` (filtrer par `IsPCParty`).
- 03h35 : **troisième passe** (tâche byj5x5kcp) : `run_all.sh night3 shared_suite trio_suite travel_suite
  companion_suite` → `_shots/night-runall3.log`. Un agent relit l'échange, la parité et les quêtes à donjon.
- 03h45, pendant la passe : **karma par joueur, écrit, compile, NON installé, NON testé, NON commité**
  (`PLAN_parite.md` partie A) : `Helper/PlayerKarma.cs`, `Patches/PlayerKarmaPatch.cs`, `GiveKarma` /
  `IsCriminal` / `HasCriminalHere` dans `ElinNetHostPersonalQuests.cs`. Règle : chez un client, le karma pris
  pendant le rejeu d'un message de l'host est ignoré ; chez l'host, le coupable est le joueur derrière le tueur
  (`Chara.Die`) ou derrière la tâche qui se termine, et il reçoit un `PlayerStandingDelta` relatif ; les gardes de
  l'host regardent le karma du joueur visé (`Chara.IsHostile`, `GoalCombat`, `Zone.RefreshCriminal`). Test écrit :
  `parity_suite.py` Y3–Y4. Compiler sans toucher au jeu : `dotnet build ./ElinTogether -c DebugNightly
  -p:OutputPath=<dossier temporaire>\`. `DOCUMENTATION.md` mis à jour. Un agent prépare le plan de la phase 2
  des quêtes à donjon (les autres joueurs rejoignent le preneur).
- 04h05 : `shared_suite` de la troisième passe **pas lancée** : le client 1 n'a jamais fini de se connecter
  (lancement à trois fenêtres très lent, 6 min pour charger le monde, pendant que je compilais et que deux agents
  lisaient le code). **Ne pas compiler pendant un lancement.** À relancer seule. `trio_suite` a démarré normalement.
- 04h20 : **relecture de l'échange, de la parité et des quêtes à donjon reçue** (10 points). Écrit, compile,
  **NON installé, NON testé, NON commité** (avec le karma par joueur) :
  1. objets échangés invisibles chez celui qui les reçoit s'il a déjà une pile dans un sac → `AddThing(…, false)`
     (test `trade_suite` R4) ;
  2. zone de quête chez l'host sans `instance` → `Zone.Destroy` effaçait l'icône de la ville sur la carte du monde
     de l'host ; zone jamais détruite après un bail décliné → `instance` posé, `DestroyQuestZone` sur refus et sur
     retour (test `instance_suite` : icône inchangée) ;
  3. état de l'échange jamais vidé (boutons morts après un changement de carte) → `PlayerTrade.WatchSession`
     chaque image ; la réponse à une invitation vaut pour cette invitation (test `instance_suite` I4) ;
  4. quête de défense payée d'après les vagues de l'host → `LastWave`/`Bonus` dans `QuestCompleteDelta` (test I5) ;
  5. s'équiper d'un objet au moment où on le donne le reprenait → refus si l'objet est dans le sac d'un autre
     (test `trade_suite` R5) ;
  6. étage de donjon loué détruit avec son sommet expiré → `HasLeasedFloor` dans `LeasedZonePatch` (pas de test) ;
  7. déconnexion dans la zone d'une quête : la quête restait au journal sans zone → abandonnée sans pénalité à
     la reconnexion (`PersonalQuests._dropInstances`, test I4).
  **Laissés** : expérience de guilde écrasée quand deux joueurs en gagnent au même moment ; affinité de la tonte
  et de l'abattage perdue pour un client ; sac plein non vérifié à l'échange ; invitation sans délai.
- Plan de la phase 2 des quêtes à donjon rendu : `PLAN_quetes_donjon_phase2.md` (gros : 8 étapes, pas cette nuit).
- 04h40 : **troisième passe finie : `trio_suite` 24/24, `companion_suite` 30/30, `travel_suite` 36/37** (S15 :
  scénario périmé, attendait que le client suive l'host sur la carte du monde → corrigé, à relancer avec
  `shared_suite`).
- 04h52 : **host figé pour de bon** juste après le chargement (0 % de processeur, fil principal en attente, rien
  dans `Player.log` ; copie dans `_shots/host-hang-0452-player.log`). Cause non trouvée, mais **toujours quand
  host et client démarrent en même temps** (8 min de chargement au lieu de 50 s). `mp_test.py` lance maintenant
  **une fenêtre à la fois** (host, chargement du monde, puis chaque client) : host chargé en 48 s, client en jeu
  2 min 20 plus tard, plus de gel.
- 05h02 : **`parity_suite` 17/17** (karma par joueur Y3–Y4 du premier coup), **`trade_suite` 32/32** (R4 pile dans
  un sac, R5 s'équiper en donnant : l'host écrit bien « Refusing CharaEquipDelta … is held by »),
  `instance_suite` 32/34 : icône de la base intacte, I5 prime de défense OK ; I4 (quête abandonnée après une
  déconnexion dans sa zone) raté car `PersonalQuests.Tick` ne tourne pas hors connexion → une nouvelle connexion se
  reconnaît à son objet `Transport`. Recompilé, relancé.
- **05h10 → 08h30 : le PC s'est mis en veille.** Le lancement de 05h08 est resté en plan (host et client lancés,
  serveur pas démarré), aucun test n'a tourné pendant ces trois heures, le réveil de la boucle prévu à 05h30 n'a
  pas eu lieu. **Pour une prochaine nuit : désactiver la mise en veille du PC avant de partir.**
- 08h31 : fin de la nuit. Fenêtres fermées (PID 14328, 19832), session « idées de mods » prévenue que le jeu est
  libre. Commits `f247883` (karma et crime par joueur, prime de défense) et `4edfd63` (corrections de la
  relecture). **Zip refait** : `_release/ElinTogether-independance.zip`, commit `4edfd63`, puis build Debug remis.
- **Reste à faire à la reprise, dans l'ordre** :
  1. `mp_test.py` puis `instance_suite.py` : I4 (quête abandonnée après une déconnexion dans sa zone) n'a **pas
     été retesté** depuis la réécriture de la détection (`PersonalQuests._transport`) ; puis `quest_suite.py` et
     `chara_suite.py` sur ce build.
  2. `bash _tools/run_all.sh night4 shared_suite travel_suite` : `shared_suite` n'a jamais pu se lancer cette
     nuit (lenteur), `travel_suite` S15 (scénario corrigé) et la suite S16, S17, S9–S11 n'ont pas tourné.
  3. Bots (menu, case « tout faire », 30 min + `bot.py --watch`) : **pas faits cette nuit**.
  4. Refaire le zip si quelque chose change.
  5. Ensuite : phase 2 des quêtes à donjon (`PLAN_quetes_donjon_phase2.md`), restes de la relecture (expérience de
     guilde, affinité de la tonte), conflits rares (double achat, construction sur la même case, monture).
- **Matin du 2026-10-02 (reprise à 09h00)** : fenêtres de la session « idées de mods » fermées (prévenue).
  Captures de toutes les nouveautés dans `_shots/nouveautes/` (outil `_tools/showcase.py`). En repassant
  `instance_suite` après les captures : **29/32**, deux vrais défauts : (1) au retour de sa zone, la quête rendue
  revenait dans le journal (l'état envoyé par l'host, gardé pendant le chargement, arrivait après le règlement) →
  le règlement attend cet état (`_stateFresh`, 10 s max), cherche la quête par numéro, et `_gone` empêche de la
  reprendre ; (2) quête abandonnée après une déconnexion : l'host la gardait → prévenu explicitement.
  **`instance_suite` 32/32, `quest_suite` 53/53.** Commits : règlement des quêtes à donjon, puis écran
  « Server Setting » en sections avec une ligne d'explication par case (demande de l'utilisateur).
  Piège : `LangMod/EN/SourceLocalization.json` dans le mod installé est fabriqué par le jeu à partir du classeur
  et **garde les anciens textes** : le supprimer quand on change un texte existant (`make_release.ps1` l'enlève
  du zip). En cours : `run_all.sh jour shared_suite travel_suite` → `_shots/jour-runall.log`.
  Idée validée, en file d'attente : profil de mods pour le multijoueur (`PLAN_profil_mods.md`).
- 09h51 : `run_all.sh jour` : **`shared_suite` 16/17** (G5 arrêté : « A et B rejoignent l'host à Vernis », délai
  dépassé) et **`travel_suite` 37/38** (S15 arrêté plus loin qu'avant : « client rejoint en zone 137 »). **À
  regarder** : scénario périmé (l'host ne traîne plus les joueurs) ou vrai défaut ? Les étapes suivantes de ces
  deux suites n'ont pas tourné. Détail : `_shots/shared_suite-jour.log`, `_shots/travel_suite-jour.log`.
- **10h00 : déménagement dans le dépôt** (demande de l'utilisateur, pour continuer sur une autre machine).
  Tout ce qui vivait dans `Documents\ElinMods\` (outils, notes, scripts, modèle d'installateur) est maintenant
  dans `dev/` du dépôt, poussé sur https://github.com/devmarcpro/elin-together (public). Sur cette machine, les
  anciens chemins `_tools` et `_release` sont des jonctions vers `dev/`, et `dev/_lab`, `dev/_shots`,
  `dev/_decomp`, `dev/_backup` des jonctions vers les anciens dossiers. Le dossier du jeu se lit dans
  `ELIN_GAME_PATH` (`dev/game-path.ps1`, `dev/_tools/gamepath.py`), les copies pour le bot du menu dans
  `ELINTOGETHER_LAB`. Nouveau : `CLAUDE.md` (consignes), `dev/SETUP.md` (installation d'une machine).
  Hors dépôt, à copier à la main : `_lab/saves/world_lab.pristine` (le monde de test).
- Commit `36eccb3` : contient AUSSI quatre changements écrits après ce build, donc **pas encore testés** :
  dépôts à la banque / boîte de livraison en voyage envoyés à l'host (`ShippingDeposit.Box`), rappel abandonné
  (`_pendingHostMove` effacé), bail refusé (`ZoneLeaseDecline`), entrées bloquées pendant l'attente de passation
  (`_handoffDeadline` dans `IsInTransfer`). Le message du commit dit à tort « 53/53 avec tout ça ».

### 22:40 — rapports des deux agents traités (commit `85a08db`, toujours sans test en jeu)

- **Avertissement A** (« Client copy of chara 1 destroyed ») : sans gravité. Chez un invité, `Game.OnLoad` renvoyait
  « à la maison » le personnage de l'host, qui n'a plus de zone dans le monde du joueur qui a hérité de la carte →
  fantôme immobile visible de ce seul invité. `CompanionLimboPatch` : chez un client, qui n'est nulle part reste
  nulle part.
- **Avertissement B** (« Card uid conflict ») : **vraie duplication d'objet**. Un joueur en train de charger le monde
  qu'on lui envoie pouvait encore envoyer des actions (ici « poser l'objet 372 ») : appliquées après la copie qui lui
  était destinée, l'objet existait deux fois (au sol et dans son sac). `OnWorldStateDeltaResponse` : un joueur pas
  encore installé (`_settled`) est traité comme un joueur en voyage, seuls le chat et les quêtes passent.
- **Relecture des quêtes par joueur**, 10 points, 9 traités : quête finie pendant l'application d'un message (le
  coup qui termine une chasse) → rendue quand même ; quête prise et rendue d'un seul clic (livraison déjà dans le
  sac) → plus de quête fantôme ; quête prise comme invité → transmise à l'host du monde ; comparaison d'état sans
  1 Mo de déchets par quête (hash du JSON, `LZ4Bytes.ToJson`) ; délais recalés d'une horloge à l'autre
  (`PersonalQuestDelta.Now`, `PersonalStateDelta.Now`, `PersonalQuests.Rebase`) ; renommée jamais envoyée avant
  d'avoir reçu la sienne ; offres déjà prises effacées sur toutes les cartes (`_taken`) ; l'host du monde ne
  récompense qu'une quête qu'il sait détenue ; remise en place dès le chargement du monde
  (`PersonalQuests.OnWorldLoaded` dans `OnSaveDataProbe`) ; `task.owner` après `CopyState`. Non traité : l'escorte
  d'une quête d'escorte n'est peut-être pas libérée côté host.
- L'utilisateur autorise à fermer les fenêtres Elin des autres sessions : ce travail passe en premier.

## Essai à 4 fait par l'utilisateur (host + bot Python + 2 bots du menu) — 2026-10-01 21:39–21:44

L'utilisateur a pris la main sur l'host de test et ajouté deux bots par le menu, avec quêtes et vente activées,
pendant que `bot.py` tournait sur le client. Tout a tenu 5 minutes (voyages, session de zone, passation quand
l'host quitte la Prairie, rappel quand il revient). À traiter, relevé dans le journal de session :

1. **Quête acceptée en voyage absente chez l'host.** Le bot n° 3, qui tenait la Prairie (héritée de l'host),
   accepte `music 60002` (19:42:33) puis `supply 60003` (19:42:41). 60002 arrive partout. 60003 est chez le client
   en voyage à Lumiest mais pas chez l'host (vérifié trois fois de suite par `bot.py`). Le client ne peut l'avoir
   reçue que par le relais de l'host : l'host l'a donc eue puis perdue, ou a relayé sans l'insérer. Pas de ligne de
   journal dans cette branche (`QuestStartDelta`, origine en voyage) → **ajouter un log et reproduire** : A hérite de
   la Prairie, y accepte la quête d'un habitant.
2. `Client copy of chara 1 destroyed, not synced` (19:42:06) juste après qu'un invité rejoint une session de zone
   sur la Prairie.
3. `Card uid conflict: uid 52030 held by local 372, refusing incoming 372` (19:43:31) après le rappel de la
   Prairie par l'host.
4. Deux bots qui se connectent en même temps : premiers essais perdus (`Handshake timed out … AwaitingVersion`,
   `host shut down`), réussite au 3e essai automatique (~45 s). Gênant, pas bloquant.
5. `bot.py` : l'action « reconnecte » a échoué parce que l'utilisateur fermait l'host au même moment ; à réessayer.

Nouvelles actions de `bot.py` essayées avant (graine 5, 48 actions, 0 problème) : outil (pioche, pelle, hache),
construit (poser une planche, un coffre, une torche), coffre (ranger / prendre), compagnon (recruter), reconnecte.
Pas encore portées dans le bot du menu (`EmpBot.cs`).

## Dialogues d'histoire joués par un client — 2026-10-01 21:35

- **Objets offerts** (`StoryGifts`, `StoryGiftDelta` 808) : un client ne peut pas créer d'objet (uid provisoire,
  détruit en fin de frame). `Player.DropReward` côté client, et `Zone.AddCard` d'un objet pendant un dialogue
  (action `drop`), notent l'objet ; en fin de frame (`CoreSynchronizationContext`, avant `CardCache.Update`) il est
  envoyé sérialisé à l'host, qui lui donne un vrai numéro et le pose au même endroit. Envoi en fin de frame pour
  garder ce que le code du jeu modifie après la pose (charges, identification).
- **Effets sur le monde** (`StoryOutcomePatch`, `StoryOutcomeDelta` 809) : liste de méthodes de `DramaOutcome`
  (`OnClaimLand`, `QuestDefense_0/1`, `Tutorial1`, `PutOutFire`, `QuestExploration_*`, `QuestDebt_reward`,
  `revive_pet`, `event_*`, `reward_stone_dream`). Client connecté : non exécutées chez lui, envoyées à l'host qui
  appelle la vraie méthode du jeu sur un `DramaOutcome` monté à la main (objet inactif + `DramaManager.tg`), sous
  `GiveTo` + `Simulate`. Joueur en voyage : il exécute chez lui, et l'host répète seulement celles qui ne touchent
  pas la carte (`_worldOnly`), sans récompense. `chara_hired*` : le joueur paie chez lui, l'host fait `Recruit`.
- **Mémoire de l'histoire** (`DialogFlagSync`, clés préfixées `d:` `f:` `k:` `p:debt`) : en plus des drapeaux de
  dialogue, les propriétés bool/int de `Player.Flags` (sauf réglages personnels : chaussures, aides, etc.), les
  objets clés et la dette.
- `QuestChangePhaseDelta` : ignoré partout si l'étape est déjà la bonne (pas d'effet en double).
- Test : `quest_suite.py` Q8–Q10, total 41/41. Par appels directs ; pas de vrai dialogue cliqué.
- Non traité : affinité (`modAffinity`, cadeaux — jamais synchronisée par le mod), guildes, `fiama_pet*`,
  `poppy_found`, mariage, `get_scratch`.
- **Demande notée** : écran de choix du personnage quand on rejoint une partie.

## Bot dans le menu du jeu — 2026-10-01 21:25

- Onglet Lobby (Debug) : « Add a bot player » → `EmpBotLauncher.Launch()` démarre un serveur local si besoin, puis
  lance la première copie libre de `Documents/ElinMods/_lab/Elin*/Elin.exe` (ou `[Dev] BotLaunchers`) avec
  `-empmute -empbot` (+ `-empbotall` si la case « Bots also take quests and sell » est cochée).
- `EmpBot` (dans l'instance lancée) : à l'écran titre il se connecte au port local, valide la création de
  personnage, puis joue une action au hasard toutes les 1 à 2,5 s (marche, pas, voyage, ramasser, poser, manger,
  parler, attaquer, s'équiper ; quêtes et vente avec `-empbotall`), traverse l'écran de mort. Lignes « Bot: » dans
  le journal de session.
- Piège : un jeu lancé depuis le jeu hérite des variables `DOORSTOP_*` du chargeur de mods et démarre **sans aucun
  mod** (pas de pont, pas de bot). Le lanceur les retire de l'environnement de l'enfant.
- « Stop the bots (n) » ne ferme que les fenêtres lancées par ce bouton.
- Test : bouton cliqué par le pont → bot en jeu en ~30 s, 82 actions dont 3 voyages, `bot.py --watch` 17
  vérifications sans problème ; bouton stop → l'host revoit 1 joueur.

## Équipement ajouté et équipé dans le même tick — 2026-10-01 18:00, corrigé, testé, NON commité
- Bug (hérité d'upstream, trouvé par la session `VisibleEquipment`) : l'host ajoute un objet à un perso et l'équipe
  dans le même tick (équiper depuis un coffre ou le sol) → `CardAddThingDelta.OnRefresh` sérialise l'objet à
  l'envoi, déjà marqué `c_equippedSlot`. Chez le receveur (objet inconnu, donc désérialisé), `CharaEquipDelta`
  se fiait au drapeau et sortait : `body.slots[i].thing` restait vide, le retrait était perdu, drapeau posé à vie
  (et `Card.RemoveThing` / `CharaBody.Equip` d'Elin se fient à ce drapeau → mauvais objet déséquipé plus tard).
  Touche aussi client A → client B (relayé et resérialisé par l'host), pas client → host.
- Correction (`CharaEquipDelta.OnApply`) : « déjà appliqué » se lit dans l'emplacement (`slots.Find(s => s.thing ==
  thing)`), plus dans le drapeau. Équiper : rien si l'emplacement visé tient déjà l'objet (sinon Elin bascule et
  déséquipe) ; drapeau sans emplacement → remis à 0 puis `body.Equip` normal. Retirer : on vide l'emplacement
  qui tient l'objet (plus « l'emplacement n° SlotIndex » quel que soit son contenu) ; aucun → drapeau remis à 0.
- Test : `travel_suite.py` S17 (`--reuse --only s17`, ≈20 s sur des instances connectées). Build d'avant : 3 échecs
  côté client (`_shots/travel_suite-equip-red.log`, état client « slot=-1, flag=1, tête vide »). Avec la
  correction : 10/10, 0 exception (`_shots/travel_suite-equip-green.log`). Contrôles en plus sur les mêmes
  instances, 8/8 (`_shots/equip-extra.log`) : équiper depuis le sac, ajouter + équiper + retirer d'un coup,
  client → host, lâcher l'objet équipé.
- État du dossier du jeu : build DEBUG avec cette correction + `LeavePlayersBehind` (toujours non testée, non
  commitée). Le zip de l'ami n'a ni l'une ni l'autre. Le contournement `RelinkEquipment` de VisibleEquipment n'est
  plus nécessaire avec ce build (laissé en place, sans effet si l'emplacement est déjà lié).

## Idées de l'utilisateur pour plus tard
- **Choisir la partie à lancer et le personnage à jouer** (2026-10-01) : aujourd'hui l'host charge sa sauvegarde puis
  ouvre la session ; un client a un seul perso par monde d'host (`SavedRemoteCharas[SteamID]`, créé au 1er join).
  À préciser avec lui : plusieurs persos par joueur et choix au moment de rejoindre ? amener un perso d'une de
  ses propres parties ? choix de la sauvegarde depuis l'écran du mod ?
- Mod séparé : équipement visible sur les personnages.
- Serveur dédié (monde sans joueur host), après le temps du monde.
- **Serveur « dépôt de sauvegarde »** (idée de l'utilisateur, 2026-10-03 au soir, **retenue** : il veut qu'on s'y
  mette dès que les points 1 à 4 de sa liste sont bons, plan à lui présenter avant de coder). Le serveur est un
  petit programme, sans Elin : il garde la sauvegarde et dit qui tient quelle carte. Toute la simulation est faite
  par les joueurs, un joueur par carte (le prêt de carte poussé au bout : plus d'host, tout le monde est invité).
  Difficile : ce qui n'appartient à aucune carte (heure du monde, quêtes, base, compagnons qui changent de carte,
  numéros des objets), aujourd'hui tenu par le jeu de l'host ; le mod suppose partout que l'host est le monde ;
  un joueur qui plante en tenant une carte. Première marche : le temps du monde commun.

## Options de l'host (onglet Configuration du serveur) — 2026-10-01 après-midi
Demande de l'utilisateur : chaque nouveauté est une **case à cocher** réglée par l'host (config `Server.*`, règle
envoyée aux clients dans `NetSessionRules`, rechargée à chaud par le watcher du .cfg).
| Case | Config | Règle | Décochée |
|---|---|---|---|
| Voyage indépendant | `IndependentTravel` | `AllowIndependentTravel` | tout le monde sur la carte de l'host (upstream) |
| Expédition par joueur | `PlayerShipping` | `UsePlayerShipping` | tout va à l'host (upstream) |
| Combat au rythme de chaque joueur | `PlayerCombatTime` | `UsePlayerCombatTime` | temps réel, ou tours globaux si « tour par tour » coché |

### Expédition par joueur (`ElinNetHostShipping`, `ShippingHelper`, `economy_suite.py` 25/25)
- Un seul coffre ; chaque objet déposé est marqué `emp_shipper` (uid du perso déposant, porté par
  `CardAddThingDelta.Shipper`, corrigé par l'host) ; `Thing.CanStackTo` refuse de fusionner deux déposants dans le coffre.
- 5 h : avant `GameDate.ShipGoods`, l'host vend les lots de chaque joueur (`ShipPlayersGoods`) : **seul l'argent est
  personnel** (décision utilisateur) ; total d'expédition et paliers de bonus = une progression commune
  (`player.stats` de l'host), le lingot d'un palier va à celui dont la vente le franchit ; exp et stats de la base communes.
- Paiement : paquet `ShippingPayout` → le client fait `pc.ModCurrency` lui-même (la monnaie d'un joueur est à lui :
  un `AddThing` de l'host posait l'argent hors de la bourse, non compté par `GetCurrency`). Invité d'une zone ou
  hors ligne : dû gardé (`shipping_owed`), payé à l'arrivée sur la carte de l'host.
- En voyage : coffres du monde (expédition, livraisons, banque) **vidés dans la copie** (`EmptyWorldContainers`,
  sinon objets ressortis en double) ; un dépôt dans le coffre part chez l'host (`ShippingDeposit`, aussi pour les
  invités via l'hôte de zone) ; la copie ne fait ni `ShipGoods` ni `ShipPackages` (argent en double avant).
- Piège de test : `ThingGen.Create("bucket")` a une matière aléatoire → prix variable ; un id d'`[Union]` en double
  (609) casse **toute** la sérialisation des deltas.

### Combat au rythme de chaque joueur (`PlayerCombatTime`, `combat_suite.py` 16/16)
Idée utilisateur : un monstre vit sur l'horloge du joueur qu'il combat.
- Elin : `CharaUpdater.FixedUpdate` accumule `roundTimer` en temps réel, un perso agit quand il dépasse `actTime`
  (= temps d'un tour du joueur × vitesse de référence / sa vitesse).
- Chaque joueur signale ses vrais tours (`stats.turns` changé dans `Chara.Tick` : l'host directement, les clients par
  `PlayerTurnDelta`, Union 620). L'host ajoute alors `baseActTime × RefSpeed / vitesse du joueur` au `roundTimer` de
  tout ce qui est sur l'horloge de ce joueur ; ces persos n'accumulent plus le temps réel (`AccumulateRoundTimer`).
- Horloge d'un perso (`TimeOwner`) : le joueur qu'il combat (ou propriétaire du compagnon / maître du familier qu'il
  combat), sinon son propre propriétaire s'il combat ; hors combat ou joueur mort/absent : temps normal.
- `PauseGame` : le monde tourne 0,3 s après un octroi pour jouer les tours donnés. Prend le pas sur le tour par tour.
- Actif seulement chez celui qui simule la carte (host ou hôte de zone) avec ≥ 2 joueurs.
- Piège de test : les habitants de la base tuent le monstre en quelques secondes → retirés de la carte de test.

### Pause du 2026-10-01 ~13:00 — NON commité (reprendre ici)
- Restes de l'étape 3 faits et testés (companion 30/30, party 28/28, travel 50/50, shared 27/27 ; trio
  interrompu par la pause, à relancer) : limite d'alliés par joueur (`CompanionAllyLimitPatch` : `Party.Count`
  du pc local, malus de vitesse par propriétaire, ancien patch `MaxAlly` d'upstream retiré), compagnon mort en
  voyage (`TravellingWith` envoie les morts, l'host les garde morts hors du groupe), `CompanionLimboPatch` étendu
  aux persos des joueurs absents (cause des 2 destructions locales). Tests K9/K10 ajoutés.
- **Bug trouvé, corrigé, pas encore testé** : une copie de voyage faisait la vente du coffre d'expédition de 5 h
  (`GameDate.ShipGoods`) et l'envoi des colis (`ShipPackages`) → argent en double. `WorldShipGoodsEvent` :
  seulement dans le monde de l'host (pas `IsAway`).
- À faire, dans l'ordre proposé (non confirmé) : relancer trio puis commit ; expédition par joueur (objets du
  coffre marqués par déposant, paiement et bonus par joueur, exp de base commune, joueur absent payé par message
  ou à son retour) + test du bug ci-dessus ; combat au rythme de chaque joueur (idée de l'utilisateur : un monstre
  vit au rythme du joueur qui le combat, `ActionModeCombat.ApplyTurnBudget` par monstre au lieu de global) ;
  quêtes communes.

### Pièges trouvés (étape 3)
- **Le monde de l'host est en pause quand l'host ne fait rien** : les pas d'un client (`CharaMoveDelta`) ne font
  pas avancer le temps → PNJ et compagnons figés. `PauseGame` : pas de pause si un joueur a bougé < 1 s
  (`CharaMoveDelta.HasRecentMove`).
- **`Game.OnLoad` renvoie chez eux les membres de branche sans zone** (« Moving invalid chara ») : c'est l'état
  voulu d'un compagnon parti avec son propriétaire → côté client, `Zone.AddCard` hors delta → `DelayDestroy` →
  destruction envoyée à l'host (`CardModNumDelta` num 0) qui **détruisait le vrai compagnon**. Corrigé :
  `CompanionLimboPatch` (pas de déplacement au chargement pour un compagnon avec propriétaire), l'host refuse
  `CardModNumDelta` sur un chara venant d'un client, un client n'envoie jamais la destruction d'un chara,
  `CharaRemoveFromGameDelta` oublie aussi le cache (copie périmée réutilisée sinon), `CardCache.Reset()` avant
  de démonter un monde (retour chez l'host, arrivée chez un hôte de zone).
- Relance d'un client tué trop tôt : Unity affiche « Fatal error / Another instance is already running » →
  `companion_suite.relaunch_client` attend 15 s et réessaie.
- Tests : `companion_suite.py` (K1–K8, 1 client), `party_suite.py` (P1–P8, 2 clients) ; `_tools/run_all.sh`
  enchaîne les suites en fermant les instances entre chaque.

## Suite (par priorité)

1. Chemin réaliste sans téléport : sortir à pied → carte du monde (bail Region) → entrer dans une ville.
2. 2e visite d'une zone déjà générée chez l'host (le bail envoie la carte de l'host au client).
3. Nefias : étages créés côté client → plage d'uid de spatials + remontée des nouvelles zones.
4. Déco pendant l'absence : checkpoints réguliers de la zone et du perso.
5. Chat reçu pendant l'absence (laisser passer `MsgSayDelta`).
6. L'host qui entre dans une zone prêtée : lui faire rapatrier la zone d'abord au lieu d'ignorer l'upload.
7. Deux clients dans la même zone (aujourd'hui refusé « occupied ») : relais via l'host.
8. Test réel à deux PC via Steam (pas en UDP local).

## Banc de test multijoueur local

`python _tools/mp_test.py` (≈4 min) : restaure `world_lab`, lance le host (jeu normal) et le client (`_lab/Elin2`),
charge la sauvegarde, `emp.add_local`, `emp.connect_udp`, valide la création de personnage, affiche l'état des deux
côtés et enregistre `_shots/mp-host.png` / `mp-client.png`. `--reuse` pour repartir d'instances déjà lancées.

- **Pourquoi `_lab/Elin2`** : Elin a `forceSingleInstance = True` (PlayerSettings dans `globalgamemanagers`) → une
  2e instance quitte avec le code 0 avant même d'écrire un log. `_tools/make_lab.py` crée un dossier de jonctions
  et liens physiques vers le jeu + une copie de `globalgamemanagers` où **un seul octet** change (0x1178 : 1 → 0),
  + sa propre copie de `BepInEx/config` (sinon « Sharing violation » sur le .cfg) + un `loadorder.txt` aux chemins
  du lab. À relancer après chaque mise à jour d'Elin. Le dossier du jeu n'est pas modifié par ce script.
- **`steam_appid.txt`** (2135150) ajouté dans le dossier du jeu : Heathen.Steamworks appelle
  `SteamAPI.RestartAppIfNecessary` → sans ce fichier, lancer l'exe directement renvoie vers Steam, qui ignore la
  demande si le jeu tourne déjà. Mécanisme développeur officiel Valve ; Steam doit tourner et posséder le jeu.
- Même compte Steam des deux côtés : OK (l'host ne se compte pas comme pair). Nom affiché du joueur = 玉皇大帝.
- Les instances partagent `LocalLow/Lafrontier/Elin` (saves, `ElinMP/Logs/Session_*.log`). Conflit constaté à
  2 clients : tous deux écrivaient la carte reçue dans `Save/world_emp/<uid>/` en même temps (« Sharing violation »)
  → en DEBUG, le monde répliqué d'un client est `world_emp_<identité>` (`ResourceFetch.EmpSaveId`).
  Le client écrit son Player.log dans `_shots/elin2-player.log` (`-logFile`), le 2e dans `elin3-player.log`.
- 3 instances : `mp_test.py --clients 2` (host + `_lab/Elin2` identité 2 + `_lab/Elin3` identité 3), ponts
  27551/27552/27553. Suites : `travel_suite.py` (1 client, S1–S16) et `shared_suite.py` (2 clients, G1–G7).
  `_tools/idle.ps1` = secondes depuis la dernière action de l'utilisateur (vérifier avant de lancer le jeu).
- Sauvegarde de test : `world_lab` = copie de `world_3` avec la Prairie revendiquée (`_zone.ClaimZone()`, l'host
  exige une terre revendiquée). Copie vierge : `_lab/saves/world_lab.pristine`. Les vraies saves ne sont pas utilisées.
- Pont de debug : `python _tools/emp.py ports|hello|state|cmd|eval|shot` (host 27551, client 27552 en général).
  `eval` = C# dans le jeu ; 1er appel lent (compilation), timeout 180 s.
- Création de personnage automatisée : `LayerEditBio` → `ButtonEmbark.onClick.Invoke()` (même listener que le clic).

## Sauvegardes (restauration)

- Snapshots `um backup` dans `%USERPROFILE%\.universal-modder\backups\` :
  `elin-save`, `elin-cloudsave`, `elin-elinmp`, `elin-user` (20260930-1811xx).
  Restaurer : `um backup restore elin-save` (etc.). `Cloud Backup` (650 Mo d'anciennes sauvegardes) non copié.
- `_backup/loadorder.original.txt` = loadorder.txt d'origine.
- `_backup/config.original.txt` = `Save/config.txt` d'origine (plein écran 1920×1080). Actuellement : fenêtré 1280×720.
- `_backup/elintogether.cfg.original` = config BepInEx du mod d'origine. Actuellement : `[Dev] Listener = true`
  (sans effet sur la version Workshop, le pont n'existe qu'en build DEBUG).
- Ajouté au dossier du jeu : `steam_appid.txt`, `Package/Mod_ElinTogether/` (build de dev).

Retour complet à l'état d'origine : `use-workshop.ps1`, recopier `config.original.txt` vers `Save/config.txt`,
supprimer `steam_appid.txt` et `Package/Mod_ElinTogether/`, supprimer `Save/world_lab`.

## Nouvelle machine (Steam Deck sous Windows) — 2026-10-02, à partir de 10h30 — reprendre ici

Entrée la plus récente du journal (la précédente est « Nuit du 2026-10-01 au 02 », plus haut). Les prochaines
entrées s'ajoutent **ici, à la fin du fichier**.

### Installation (10h30 → 11h10)
- Machine : Steam Deck (Valve Jupiter, 15 Go de mémoire) sous Windows 11, écran 1920×1080, utilisateur
  `steamdeckwin`. Le dossier de travail est venu par `ElinMods-transfert.zip` dans `Documents\ElinMods` : pas de
  fausses copies du jeu, `_decomp`, `_shots`, `_backup`, `_lab\saves\world_lab.pristine`, `dev\_tools\pylib`
  (Python 3.12) et `ilspycmd` étaient dedans.
- Déjà fait par l'utilisateur : Steam connecté, Elin installé (canal Nightly, EA 23.350 Patch 1, emplacement
  habituel), abonnements Workshop YK Framework et Elin Together. Elin n'avait **jamais été lancé**.
- Installé avec winget : git 2.55, Python 3.12.10, SDK .NET 11.0.100-preview.5.26302.115. Le SDK et git demandent
  chacun un clic « Oui » à l'écran (sans personne devant, l'installation s'annule : deux essais perdus pour git).
- `apres-deplacement.ps1` : raccourcis `dev\_lab`, `_shots`, `_decomp`, `_backup` vers `Documents\ElinMods\…`,
  et `ElinMods\_tools`, `_release` vers `dev\…`. `ELIN_GAME_PATH` pas nécessaire (emplacement habituel).
  `ELINTOGETHER_LAB` = `dev\_lab`. Copies du jeu `Elin2`, `Elin3`, `Elin4` (identités 2, 3, 4).
- Dans le jeu : `steam_appid.txt`, build Debug, `loadorder.txt` (build de dev actif, version Workshop inactive),
  `Save\config.txt` = `_backup\config.test-fenetre.txt` (fenêtre 1280×720) + `Save\version.txt`,
  `[Dev] Listener = true` dans le jeu et les trois copies.
- Git : identité du dépôt = celle des commits précédents ; l'adresse d'envoi de `upstream` est neutralisée
  (`git remote set-url --push upstream …`) ; connexion GitHub faite par l'utilisateur, `git push` marche.
- Universal Modder (extension Claude Code, 0.2.0) réinstallé par l'utilisateur à 11h38 : `um` n'est pas dans le
  PATH, le lancer avec `PYTHONPATH=<dossier de l'extension> python -m um …`. Les anciens instantanés
  `um backup` de l'ancienne machine ne sont pas ici.

### Ce qui diffère de l'ancienne machine
- Démarrage bien plus rapide : host chargé en 45 s, client en jeu 1 min 30 plus tard (`mp_test.py` < 2 min).
- Pas de `Save` de l'utilisateur : ses parties sont dans `Cloud Save` (Steam Cloud), `Save` ne contient que
  `world_lab` et les mondes des clients de test. Pas de mod « Specific Portraits Settings », pas de
  `VisibleEquipment` dans `Package` (les fenêtres s'ouvrent plus vite).
- Réglages du mod remis à neuf (premier lancement) : `[Server] TurnBasedCombatMode = true` (valeur par défaut ;
  l'ancienne sauvegarde `_backup\elintogether.cfg.original` avait `false`). Les suites passent ainsi.
- Les suites comptent une vérification de plus par journal `elin3`/`elin4-player.log` de moins de deux heures :
  d'où 16 et 31 au lieu de 17 et 32 pour `parity_suite` et `trade_suite` (rien ne manque).
- Mise en veille : 15 min sur secteur. Aucun réglage changé ; `dev\_tools\keep-awake.ps1` (nouveau) empêche la
  veille tant qu'il tourne.

### Pièges rencontrés
- **Elin jamais lancé + build Debug = mod qui plante au démarrage.** Pas de `config` tant que la langue n'est pas
  choisie ; `NoApplicationPausePatch` lisait `core.config` pendant la pose des patches → exception, plus aucun
  patch, pas de pont de test (7 minutes d'attente pour rien). Corrigé (`388fae3`). Le build Release n'est pas
  touché : il pose ses patches à l'ouverture d'une session.
- Le jeu ignore `Save\config.txt` s'il n'y a pas `Save\version.txt` à côté, et affiche le choix de la langue.
- Au tout premier lancement, le mod remet son `.cfg` à neuf : `Listener = true` écrit avant est perdu (d'où
  l'ordre « lancer, fermer, puis régler »). Les copies du jeu faites avant ce réglage ont `Listener = false`.
- PowerShell 5.1 abîme les guillemets passés à `python` ou `git` : envoyer le C# au pont par un fichier ou
  l'entrée standard, et les messages de commit par `git commit -F fichier`.
- `SETUP.md` avait un chemin cassé (`dev` + caractère « cloche » + `pres-deplacement.ps1`).
- Les fenêtres de test **avec la souris de l'utilisateur dessus** : voir ci-dessous.

### Vérification (11h07 → 12h08)
- `mp_test.py` OK, `parity_suite` **16/16**, `trade_suite` **31/31** (étape 7 de SETUP.md).
- **G5 et S15 : scénarios périmés, pas des défauts** (analyse d'un agent sur les journaux d'hier, puis en jeu).
  G5 ne demandait qu'une fois à A et B de rejoindre l'host ; la demande de B, faite pendant que la Prairie
  changeait de mains, était perdue. S15 attendait que le client suive l'host dans sa zone. S10 (jamais repassé
  depuis le choix du personnage) ne répondait pas à « avec quel personnage jouer ? ». Corrigés (`e27bbbd`) :
  **`shared_suite` 26/26, `travel_suite` 55/55**, premier passage vert de leurs fins depuis `1e1be22`.
  Les quatre changements de `36eccb3` étaient bien dans le build d'hier ; aucun de leurs avertissements dans ces
  deux passes, mais ils n'ont toujours pas de test à eux.
- Limite notée, pas corrigée : un invité qui demande à voyager juste quand la carte change de mains perd sa
  demande (`TakeOverZone` efface `_pendingTravel`), il doit recliquer.
- **Vrai défaut trouvé par hasard** : pendant que l'utilisateur se servait du PC, un client de test est resté
  bloqué sur « World Law » à la création du personnage (72 clics du test pour rien). L'écran de création du jeu
  relit les objets sous le pointeur et plante sur un objet détruit (une fenêtre sans le focus garde ses anciens
  objets survolés) ; l'exception coupait `OnSessionNewPlayerRequest` avant la pose du bouton du mod. Corrigé
  par `CharaMakerHoverPatch` (`a6819f1`), test dans `chara_suite.py` C2 : rouge avant
  (`_shots/chara_suite-hover-red.log`), **12/12** après. Le blocage complet n'a pas été rejoué de bout en bout
  (il dépend du focus des fenêtres), le test appelle la même fonction du jeu.
- `SETUP.md` et `apres-deplacement.ps1` corrigés (`95ce7f6`).

### Série de bots (12h08 → …)
- Lancement sans cliquer dans le menu : `mp_test.py --clients 0`, puis par le pont (les types du mod sont
  `internal`, il faut passer par `HarmonyLib.AccessTools`) : `EmpConfig+Dev.BotAllActions.Value = true`,
  `EmpBotLauncher.Launch()` ; attendre un `Client` en jeu ; `bot.py --watch --minutes 30` ; à la fin
  `EmpBotLauncher.StopAll()` et `BotAllActions = false` (la valeur est écrite dans le `.cfg` du jeu).
- **Premier passage, 23 minutes, 165 vérifications, 710 actions du bot, puis un vrai défaut** : le bot a pris une
  quête auprès d'un habitant de Mysilia (carte visitée seul), puis est rentré chez l'host avec cette quête en
  cours → `PersonalQuests.Restore` cherchait l'habitant alors que le monde tout juste reçu n'a pas encore de carte
  active → exception du jeu (`EClass._map`), `OnSaveDataProbe` coupé en deux, **le joueur reste connecté sans jeu
  (écran vide)**. Tout joueur qui prend une quête en ville et rentre avec y avait droit. Corrigé (`449c5fa`) :
  hors carte active, seuls les personnages connus partout sont cherchés ; l'habitant est relié au passage
  suivant. Test `quest_suite.py` P5 : rouge avant (`_shots/quest_suite-p5-red.log`), **`quest_suite` 60/60** après.
- Au début du même passage, pendant 80 s : le sac du bot comptait 7 objets de plus chez l'host que chez lui.
  Cause dans l'outil, pas dans le jeu : `EmpBotLauncher.Tick` donnait le matériel 2 s après l'envoi du monde au
  bot, avant que son jeu ait fini de charger (`_settled`) ; le personnage qu'il avait reçu n'avait pas le matériel.
  Corrigé dans l'outil (`IsSettled`). Même fenêtre pour tout ce que l'host ferait au personnage d'un joueur en
  train de charger ; rien d'autre que ce matériel n'y touche aujourd'hui.

- **Deuxième passage, sur `449c5fa` : 35 minutes, 1 066 actions du bot, 148 + ~80 vérifications, 0 problème,
  0 exception** dans les journaux des deux jeux (le bot est rentré plusieurs fois chez l'host avec des quêtes).
  Le surveillant s'était arrêté seul à la 13ᵉ minute : il interrogeait un jeu pile pendant un changement de carte
  (`EClass._map` vide). `bot.py` : un jeu entre deux cartes fait sauter la comparaison, six fois de suite au plus
  (`BUSY_CHECKS`), après quoi c'est signalé comme un vrai problème. Relancé 20 minutes sur les mêmes fenêtres.

### Zip pour l'ami (13h55)
- `make_release.ps1` sur le commit `d2ae52e` (les corrections en cours, pas testées, étaient mises de côté par
  `git stash`) : `_release/ElinTogether-independance.zip`, 1 Mo, Elin EA 23.350 Patch 1, mod 0.26.292.
  Contenu vérifié : pas de `.pdb`, pas de fichier du jeu.
- Installateur essayé ici comme chez l'ami (zip décompressé ailleurs, `install.ps1`) : jeu trouvé, ancienne
  copie mise de côté, `loadorder.txt` corrigé. Le build Release se charge sans exception (écran titre, entrée
  de menu « Elin Together »). **Pas testé en partie** : le build Release n'a pas de pont de test ; c'est le même
  code que le Debug qui a passé les suites. Message de l'installateur précisé quand la version d'Elin diffère
  (canal Nightly).
- Le jeu de cette machine a maintenant **le build Release du zip** (pour jouer avec l'ami). Avant de reprendre
  les tests : `build.ps1`. Avant de rejouer avec l'ami après des tests : relancer `Installer.bat` du zip, sinon
  les numéros de version ne correspondent plus et la connexion est refusée.

### Page Workshop d'Elin Together, lue le 2026-10-02 (67 commentaires) — pistes, à proposer à l'utilisateur
Rien de neuf côté code d'origine : `upstream/main` n'a aucun commit depuis la base du fork (`4a487d1`).
Ce que les joueurs demandent ou signalent, du plus fréquent au plus rare :
1. **Ne pas être forcé de suivre l'host** (4 commentaires, dont « l'host cultive, moi je veux les donjons ») ; les
   auteurs répondent que c'est impossible avec leur conception. C'est exactement ce que fait ce fork.
2. Le temps quand on voyage seul (un joueur propose une option) → « temps du monde commun », à voir avec l'utilisateur.
3. Listes de mods différentes (« Act Mapping Mismatch », déconnexion immédiate, « personne ne peut manger ») →
   `PLAN_profil_mods.md` (déjà en file d'attente) ; au minimum, un message clair qui dit quels mods diffèrent.
4. Combat tour par tour : les monstres jouent 20 fois de suite, l'esquive d'un client ne marche pas → à vérifier
   avec « combat au rythme de chaque joueur » (case du fork).
5. Recommencer son personnage / supprimer celui d'un ami → « nouveau personnage » existe ici ; manque : supprimer.
6. Garder sa progression hors de la partie de l'host (jouer seul puis revenir) → importer / emporter un personnage
   (point 7 de la liste « Reste à faire »).
7. Défauts signalés, à vérifier un par un dans le fork : apparence changée au miroir par un client pas gardée ;
   objet posé par l'host (panneau) vu comme un objet au sol par le client, qui peut le ramasser ; dons (feats)
   d'un client sans effet (rêve lucide, potions de sorcière) ; race slime qui perd gènes et dons en mourant ;
   objets fabriqués par un client tous « en granit » (matières pas synchronisées) ; apparence personnalisée (PCC).

### Page GitHub du projet d'origine (ElinTogether/ElinTogether), lue le 2026-10-02
10 étoiles, 13 tickets en tout, 3 ouverts, pas de discussions, dernier envoi le 2026-09-27 (= la base du fork).
- Ouverts : #9 un client qui pose un objet tenu (mur pris d'une pile) le voit tomber au sol au lieu d'être
  installé ; #10 le message « vous avez fabriqué… » d'un client s'affiche chez l'host (idem feu de camp) ;
  #2 la liste TODO des auteurs.
- TODO des auteurs, pas fait : la mort (« une façon adaptée au multijoueur », aujourd'hui on choisit où
  revenir) ; proposition de reconnexion automatique ; quêtes avancées par un client (« pas pour tous les
  types ») ; changements d'apparence en cours de jeu (priorité basse) ; connexion par adresse IP.
- Fermés sans suite : #8 un client fée esquive et joue comme l'host en tour par tour (même plainte que sur le
  Workshop) ; #4 demande d'un tour par tour qui ne bloque pas ceux qui construisent pendant qu'un autre se bat ;
  #7 (liste) : boss de donjon qui casse un mur pas vu par le client, objets en plus d'un squelette nommé pas vus,
  tenue changée à la coiffeuse pas gardée. Réponse des auteurs à « un client ne gagne pas de karma » : « le
  monde est celui de l'host, le client n'est qu'un coéquipier » — l'inverse du but de ce fork.
- Leur règle pour contribuer : expliquer le changement, le relier à un ticket, « pas de code d'IA non relu ni testé ».
- **Notre page (devmarcpro/elin-together)** : pas de description, pas reliée au projet d'origine comme « fork »,
  et le README est encore celui d'origine (il dit « un client ne peut pas changer de carte, c'est voulu »).
  À proposer : un README du fork (ce qu'il ajoute, les cases de l'host, comment l'installer, limites).

### Retours des joueurs corrigés (14h → 17h), plan dans `PLAN_retours_joueurs.md`
Un commit par correction, chacune avec son test rouge puis vert :

| Commit | Défaut | Test |
|---|---|---|
| `b4bd4f4` | pièce posée par un autre joueur vue « au sol », ramassable | `build_suite.py` B5 |
| `5ea85b9` | mur cassé par un monstre resté debout chez les autres (`CharaDestroyPathDelta`, union 227) | `build_suite.py` B3 |
| `af546f2` | fabrication d'un joueur non-host faite avec les dons et talents de l'host (`RemoteCraft.AsCrafter`) | `player_suite.py` F1, F2 |
| `6d8223e` | apparence changée au miroir perdue à la reconnexion (`CharaAppearanceDelta`, union 228) | `player_suite.py` F3, F4 |
| `9ebcd5a` | slime joué par un non-host : pas de gènes absorbés (`RemoteSlimePatch`) | `player_suite.py` F5 |
| `ac4546e` | après une mort sur la carte de l'host, plus de voyage seul (`deathZoneMove` jamais remis à zéro) | `death_suite.py` D1–D3 |
| `1ee6948` | texte de la case « combat tour par tour » : sans effet avec « combat au rythme de chacun » | — (texte) |

Passe complète des 16 suites sur `6d8223e` : tout vert sauf deux tests alors neufs (combat F6, player F5).
**Aucune passe complète depuis** (slime, mort, texte, sommeil, vitesse) : à refaire.

Pièges de test notés ce jour-là :
- Le monde de l'host est en pause sans entrée du joueur : un `SetAI` injecté chez l'host n'avance pas, il faut
  appeler `task.OnProgressComplete()`.
- L'host arrête une action injectée quand le client se dit inactif : une fabrication se pilote depuis le
  `LayerCraft` du client.
- Les dialogues du jeu (`LayerDrama`, `LayerShippingResult`) retiennent le temps : les fermer dans le test.
- Une recette trop dure tue un personnage neuf par épuisement.
- PowerShell 5.1 abîme les guillemets passés à un exécutable : C# par fichier (`ev.py <port> -`), messages de
  commit par `git commit -F`.

### Première vraie partie à deux PC, et le bug du sommeil (2026-10-02 après-midi)
- L'utilisateur a joué avec son ami (l'ami hébergeait, zip `1ee6948`, mod 0.26.301). Les deux dorment **sur une
  carte sauvage** : l'host se réveille dans une « vue cinéma », ne peut plus rien faire, l'autre reste endormi.
- Cause : loin d'une base, le jeu finit la nuit par `Player.SimulateFaction`, qui promène le joueur dans chacune
  de ses bases et le ramène, changement de carte sur changement de carte dans la même image. Pour le fork ce sont
  de vrais déplacements de l'host : `LeavePlayersBehind` donne la carte au joueur endormi à côté, le retour doit
  attendre le rappel de cette carte, le jeu n'attend pas et initialise la scène sur une carte où l'host n'est
  pas (`AM_ViewZone`).
- Correction `9ec9cc8` : `SimulateFaction` n'est pas fait chez un host tant que d'autres sont connectés (une base
  se rattrape quand quelqu'un y entre). Test : `sleep_suite.py`, neuf (le sommeil du mod n'avait aucun test).
  Carte sauvage (`--only w0,z0,z1,z2`) : rouge avant (`_shots/sleep_suite-wild-red.log`), 16/16 après ; à la
  base 15/15 avant et après.
- **Leçon** : les suites ne jouaient jamais une nuit entière. Chaque geste courant d'une soirée (dormir, manger,
  mourir, vendre) doit avoir son test joué « comme un joueur », sur une carte sauvage aussi.
- Piège : lancer Elin ici pendant que l'utilisateur joue ailleurs avec le même compte Steam ferme le jeu d'ici
  (hors ligne) et peut gêner sa partie. Demander avant.

### Zips et page des versions
- 15h : zip du commit `1ee6948` (mod 0.26.301), publié sur GitHub (`independance-0.26.301`). Avait le bug du sommeil.
- 17h44 : zip du commit `9ec9cc8` (**mod 0.26.304**, 1 075 446 octets), publié à 18h comme
  `independance-0.26.304` (préversion) ; fichier public vérifié identique au zip local ; l'ancienne version et son
  étiquette retirées. Publication par l'API GitHub avec le jeton que git utilise déjà (`git credential fill`
  appelé par `cmd /c … < fichier`, le tube PowerShell ne marche pas) ; jeton jamais affiché.
- README et README_fr : pointent vers la page des versions ; disent « joué une seule fois entre deux PC ».
- Règle retenue (demande de l'utilisateur) : quand il demande le zip, le faire **tout de suite** à partir des
  commits testés, mettre de côté ce qui n'est pas prouvé, tester après.

### Elin s'est mis à jour pendant la passe complète (2026-10-02, 19h02) — EA 23.351
- Passe « soir » sur `f4b3e30`, lancée à 18h10 : travel 55/55, shared 26/26, trio 24/24, companion 30/30,
  party 28/28, economy 25/25, **combat 16/20**, quest 61/61, chara 13/13, parity 17/17, trade 32/32,
  build 21/21, player 31/31. Puis `instance_suite` : le client ne se connecte plus, « invalid version ».
- Cause : Steam a mis Elin à jour (canal Nightly, `buildid 25680002`, EA 23.351) à 19h02. Les lanceurs de
  `_lab` gardaient une partie de l'ancienne version : le journal du mod dit
  `game 0.23.350.1 -> 0.23.351.0`. Remède : refaire `make_lab.py Elin2 2` (3, 4), comme le dit SETUP.md.
  **Piège** : `mp_test.py` attend alors 5 minutes par essai sans dire pourquoi ; lire
  `ElinMP/Logs/Session_<date>.log` (« Version mismatch with host »).
- Le mod (`26ad8d9`) se compile contre 23.351 sans erreur et sans avertissement ; host + 1 client se connectent,
  aucune exception au chargement. Le zip publié (0.26.304) a été compilé contre 23.350 Patch 1 : pas essayé
  tel quel sur 23.351. `dev/_decomp` est toujours le code de 23.350.
- `instance`, `leave`, `transfer`, `death`, `sleep` : **pas passées** ce soir. Toute la passe est à refaire sur 23.351.
- Combat 16/20 : F4 et F5 échouaient déjà à 15h08, avant la correction de vitesse (le monstre de A agit pendant
  les tours de l'host). Les trois joueurs du banc sont côte à côte : un monstre change de cible pour le joueur
  d'à côté et passe sur son horloge. `combat_suite.py` écarte maintenant les joueurs au début (F1).
  Mesuré à deux joueurs sur 23.351 : l'invité a la même vitesse chez lui et chez l'host (105), pas d'inégalité.

### Zip et version publiée pour EA 23.351 (20h32)
- L'utilisateur : « Oui dès que tu peux publie la release ». Passe sur 23.351 arrêtée après les 7 suites longues
  (travel 56/56, shared 27/27, trio 24/24, companion 30/30, party 28/28, economy 25/25, combat 22/22), zip fait
  tout de suite : commit `f17ad6c`, **mod 0.26.309**, 1 076 004 octets, `version-elin.txt` = EA 23.351.
  Le build Release se charge sur 23.351 (écran titre, 0 exception). Publié : `independance-0.26.309`
  (préversion), fichier public identique au zip local, `independance-0.26.304` et son étiquette retirés.
- Les 11 suites courtes relancées ensuite sur le build Debug du même commit (journaux `_shots/*-351.log`),
  finies à 21h06 : quest 61/61, chara 13/13, parity 17/17, trade 32/32, build 21/21, player 31/31,
  instance 34/34, leave 13/13, transfer 11/11, death 13/13, sleep 30/30. **Les 18 suites passent sur 23.351**
  pour le code du zip 0.26.309. La note de la page de publication le dit.
- Les corrections des inégalités H1–H6 sont dans `git stash` (« inegalites invites H1-H6 »), avec
  `guest_suite.py` : écrites, relues par un agent (3 défauts trouvés et repris), **jamais compilées ni jouées**.
- `dev/_decomp` est encore le code de 23.350 : à refaire avant de relire du code du jeu.

### Inégalités invité/host H1–H5 corrigées (21h10 → 21h40), `guest_suite.py` 41/41
- Rouge sur `3eb0741` (`_shots/guest_suite-red.log`), les cinq défauts vus en jeu : bouteille vide sans effet ;
  baguette sans effet + exception chez l'autre joueur à chaque coup, dans les deux sens ; pêche 0,6 % de prises
  bonus contre 7,1 % ; repos +0 point de vie pour l'invité et, pour tous, un repos qui finit en sommeil ;
  coffres de pari jamais usés, l'invité mort d'épuisement en 15 secondes.
- H6 (torche) : sans objet, aucun objet du jeu ne porte `TraitToolTorch` en 23.351.
- Commits : `88f1241` (H5), `7aa1cc6` (H3), `94b7b56` (H2), `a9fe6ee` (H1 + H4, mêmes fichiers).
- Une relecture par un agent avant tout essai a trouvé trois défauts dans les corrections écrites (pêche : une
  exception à chaque vraie prise ; baguette : le coup revenait sur le lanceur ; bouteille : l'eau n'arrivait pas
  chez l'invité). **Faire relire avant de jouer a évité trois cycles.**
- Pièges de test : `ThingGen.Create("potion")` tire une potion au hasard (compter « ce qui se boit ») ;
  l'élément 7004 est un modèle sans élément (prendre 50500, flèche de feu) ; un monstre de test laissé en vie tue
  un personnage neuf pendant le test suivant (`try/finally`, cible neutre) ; une action finie reste dans
  `pc.ai` jusqu'au prochain geste du joueur (tester `ai.IsRunning`, pas le type) ; `TraitToolTorch` n'existe sur
  aucun objet : chercher l'objet dans `sources.things` **avant** d'écrire la correction.
- Passe complète « invites » sur ces cinq commits (21h40 → 22h57) : 17 suites vertes sur 19. `transfer` : le
  serveur du banc n'a pas démarré (raté de lancement, 11/11 en la rejouant). `guest_suite` : 39/41, irrégulier.
- Deux causes trouvées à l'irrégularité de `guest_suite` (23h → 23h45, sept essais sur fenêtres neuves) :
  1. **Un dialogue du jeu (tutoriel) ouvert chez l'invité met son jeu en pause** : sa pêche ne mord jamais
     (compteur de tours figé à 2). Le test ferme maintenant les dialogues pendant ses attentes (`awake()`).
     Astuce de l'utilisateur : en jeu, la touche Entrée passe ces tutoriels.
  2. **Le temps d'un client vient de l'host** (`GameDelta`, envoyé seulement quand l'host n'est pas en pause, et
     l'host se met en pause dès que plus personne n'est occupé de son point de vue). L'host use le dernier coffre
     de pari un pas avant que le jeu de l'invité le voie parti : avec un host inactif, le monde s'arrête là et
     l'invité reste « occupé » à ouvrir du vide, sans pouvoir annuler (`roundTimer` figé, pas de fenêtre, pas de
     pause affichée). Vrai défaut de `a9fe6ee`. Correction : chez l'host, l'ouverture d'un invité reste active
     quelques pas après le dernier coffre, jusqu'à ce que l'invité se dise libre.
     **À retenir pour toute tâche ajoutée à la table : qui finit le premier, l'host ou le client ?**
- Pas dans le zip 0.26.309.

### Deuxième lot d'inégalités (23h45 → 0h05), `guest_suite.py` G6 à G9 : 58/58
- Rouge sur le build de `5ab0109` (`_shots/guest_suite-lot2-red.log`, 45/59) : contenu des colis, maquettes et
  paquets cadeau dans le sac de l'host ; lot de la boule de gacha aux pieds de l'host ; recette trouvée en
  creusant inconnue de l'host ; fenêtre de la banque, du coffre des impôts et du panneau des politiques ouverte
  aussi chez l'host ; **corde de l'invité : la question « se pendre ? » chez l'host ; pierre de retour de
  l'invité : l'host emmené sur la carte du monde**.
- Commits : `eadeca4` (suite des coffres de pari + mise au point du test), `11ca53d` (boîtes), `3f45072`
  (fenêtres, corde, pierre), `e3772ef` (recettes). Vert : lot 1 40/40, lot 2 58/58, aucune exception.
- Pas de passe complète depuis `a9fe6ee` hors `guest_suite`. Pas dans le zip 0.26.309.
- Reste de la liste : M3 cadeaux du dieu, M4 livres anciens (et livres « dojin » : un invité qui en lit un est
  converti, vu dans le code), M5 pièges, M6 graines, M8 arrosoir, M9 carte au trésor, M10 vœu, M11 bénédiction,
  M13 grimoires, M14 réglages de la base, et les points mineurs.

### Nuit du 2 au 3 octobre
- Passe « nuit » (0h05 → 1h22) sur les deux lots : 18 suites sur 19 vertes, `guest_suite` 96/96. `combat` 20/22 :
  F4/F5 encore (le monstre de A agit pendant les tours de l'host, +11), alors que les joueurs sont écartés. Échoue
  par intermittence depuis le 2 à 15h08, avant toutes les corrections du soir. Cause pas trouvée : à creuser,
  sans conclure que c'est le mod ni le test.
- Troisième lot : rouge 42/59, vert 53/53. Commits `8e1c7ee` (identification), `8925eea` (arrosoir), `ed51490`
  (livres), `453a5f0` (graines), `c0ab2e2` (vœu). Détail dans `PLAN_egalite_invites.md`.
- Passe « nuit2 » (1h35 → 2h49) avec le troisième lot : **18 suites sur 19 vertes, combat 22/22 cette fois**.
  `guest_suite` 147/151 : seul G11 (premier clic de pêche) échoue, ce qui donne la preuve qui manquait →
  correction `316160e`, G2 + G11 15/15. Rien de tout cela dans le zip 0.26.309.
- Quatrième lot (3h45 → 3h55) : rouge 46/64, vert 63/63. Commits `9114ca3`, `8a1443b`, `4b1455c`, `5c5d125`,
  `0fc19ee`. Le plus visible : le mannequin utilisé par un invité déshabillait l'host. Conception des lots 3 et 4
  par des agents (lecture seule), chaque correction rejouée rouge puis verte.
- Passe « nuit3 » (3h58 → 5h13) avec les quatre lots : 18 suites sur 19 vertes (combat 22/22), `guest_suite`
  210/211 → piège de test (sac plein en fin de suite : un paquet pose à terre ce qu'il donne) ; corrigé dans le
  test, `guest_suite` complet **211/211** sur fenêtres neuves.
- Munitions (`1f774e7`, G30) : rouge 8/11 (l'arme de l'host rechargée), vert 11/11.
- **État à 5h40 : 26 inégalités corrigées et prouvées depuis le 2 au soir, toutes les suites vertes. Rien dans le
  zip publié (0.26.309).** Attendent l'utilisateur : M3, M5, M9, L1, L7, M13 (prix à accepter), et la publication
  d'un nouveau zip. Pas encore faits sans décision : M11 (drapeau « est le joueur »), L4/L5 (mécanisme nouveau),
  M14 (réglages de la base).

### À faire ensuite
1. Fait à 18h : vitesse en combat d'un joueur surchargé. `PlayerCombatTime` prenait la vitesse de la copie chez
   l'host (105) au lieu de celle du jeu du joueur (52) : ses monstres recevaient la moitié du temps dû, être
   ralenti lui coûtait moitié moins qu'à l'host. Test `combat_suite.py` F6 (mesure directe : on appelle le
   calcul chez l'host et on relit la vitesse utilisée), rouge 8/9 puis vert 9/9. Seuls F1 et F6 ont tourné sur
   ce build. Ce changement n'est **pas** dans le zip 0.26.304.
2. Fait à 18h10. **Signalé par l'utilisateur le 2026-10-02 au soir** : un joueur non-host qui dort avec un lit
   dans son sac retrouve le lit posé par terre au réveil, pas revenu dans le sac (l'oreiller aussi).
   Cause : l'action « Dormir » de la barre pose lit et oreiller puis appelle `Chara.Sleep(lit, oreiller,
   pickup: true, …)` ; chez un client le mod remplace cet appel par une demande à l'host et jetait ces
   arguments ; la condition de sommeil venue de l'host n'avait rien à reprendre. Correction, côté client
   seulement : ce qui a été posé est gardé à la demande et remis sur la condition juste avant qu'elle finisse
   (`ConSleep.OnRemoved`), le jeu fait le reste. Test `sleep_suite.py` B1 (nuit), B2 (il renonce), B3 (un lit
   déjà installé reste en place) : rouge 14/18 (`_shots/sleep_suite-bed-red.log`), vert 18/18 ; nuit normale
   15/15 ensuite. Pas dans le zip 0.26.304.
   Reste vrai : le lit et l'oreiller d'un invité n'ont **aucun effet** sur sa nuit (c'est la nuit de l'host qui
   compte), et un second « Dormir » pendant l'attente pose un second lit qui reste par terre.
   **Demande de l'utilisateur ensuite** : chercher les autres inégalités de ce genre entre invités et host
   (ce que le jeu ne fait que pour le joueur local). Audit en lecture seule lancé, rapport attendu dans le
   dossier temporaire de la session (`audit-inegalites.md`) ; lui donner la liste avant de corriger.
3. Connu, pas corrigé : un joueur seul sur une carte qu'il tient ne peut pas y dormir (sa demande part chez
   l'host, rien ne se passe) ; demande de voyage perdue pendant une passation ; bonus de première fabrication
   compté sur la fiche de l'host ; esquive d'une fée pas vérifiée.
4. Passe complète (`run_all.sh` + `run_short.sh`, avec `death_suite` et `sleep_suite`).
5. Deux choix de conception attendent l'utilisateur (ne pas coder avant) : que faire quand un joueur meurt sur
   la carte de l'host ; que faire quand la connexion tombe.
6. Suite de `DOCUMENTATION.md` section 7. **Pas le « temps du monde commun » sans l'utilisateur.**
7. Le jeu de cette machine a le build Debug : avant de jouer d'ici avec l'ami, relancer `Installer.bat` du zip.

### Version 0.26.337 publiée depuis le PC d'origine (2026-10-03, 13h05)
- Demande de l'utilisateur : « prends tout sur le dépôt et fais une nouvelle release ». `git pull` (28 commits de
  l'autre machine, jusqu'à `a377e4a`), Elin de ce PC déjà en EA 23.351 Patch 1.
- `make_release.ps1` sur `a377e4a` : **mod 0.26.337**, 1 082 628 octets, pas de `.pdb`. Publié en préversion :
  `independance-0.26.337`, fichier public identique au zip local. Note de publication : les 26 inégalités
  invité/host corrigées, l'état des tests de la nuit (18 suites sur 19, `guest_suite` 211/211, munitions testées
  seules après). `independance-0.26.309` laissée en place (à retirer si l'utilisateur le demande).
- Publication faite avec l'identifiant GitHub que git avait déjà enregistré sur ce PC (`gh` n'y est pas connecté).
- **Pas vérifié ici** : le chargement du build Release en jeu (l'utilisateur était devant le PC, pas de fenêtre
  ouverte sans lui). Le jeu de ce PC a maintenant ce build 0.26.337 dans `Package/Mod_ElinTogether`, prêt à jouer.

### Après-midi du 2026-10-03 (PC d'origine)
- 15h58 : la version publiée 0.26.337 se charge en jeu sur ce PC (écran titre en 40 s, 0 exception, « Loading
  [Elin Together 0.26.337] »). Son du jeu coupé dans `Save/config.txt` le temps de l'essai, puis remis à
  l'identique (copie du fichier).
- Banc refait pour 23.351 (`build.ps1`, `make_lab.py` ×3). Passe complète lancée, **arrêtée à 16h19** à la
  demande de l'utilisateur (« je veux jouer avec un ami ») : seul `travel_suite` a fini, **54/54**.
- Écrit, compile, **pas testé, pas commité** (dans l'arbre de travail) : bonus de première fabrication d'un invité
  (`CraftFirstTimeDelta`, union 816, `AIUseCrafterArgs.FirstTime`, test `player_suite.py` F6). Nouveau test
  `sleep_suite.py` Y1 (invité seul sur une carte qu'il tient : peut-il dormir ?), pas encore joué.
- 16h25 : réinstallé sur ce PC la version 0.26.337 (copie locale du zip publié, identique) pour jouer. Pas de
  nouvelle version : rien de testé n'a changé depuis 0.26.337. **github.com répondait 503 depuis ce PC**
  (page d'accueil comprise, alors que le statut GitHub disait « tout va bien ») : téléchargement impossible d'ici.
- Plan détaillé du profil de mods reçu d'un agent : `PLAN_profil_mods.md`.

### Soir du 2026-10-03 (PC d'origine) : retours de la première vraie partie de l'utilisateur comme invité
- Journaux de sa partie (18h11–18h27, 0.26.337, lui client) : aucune exception d'ElinTogether. L'host est sorti et
  rentré de la carte au moins quatre fois : à chaque retour, « Host recalls zone, rejoining » → rechargement (deux
  `Scene.Init:Zone` de suite) et invité replacé à côté de l'host. 11 342 `NullReferenceException` après la
  déconnexion, toutes du mod Workshop **Somewhat Enhanced Display** (sa barre de vie lit le dernier personnage
  survolé à chaque image, même sans jeu). Deux mods en plus chez l'utilisateur : celui-là (absent de
  `loadorder.txt`, donc activé d'office) et `Mod_VisibleEquipment`.
- Corrigé, chacun rouge puis vert, détail dans `PLAN_retours_partie_reelle.md` : `b164dd7` (première
  fabrication), `1189ac0` (rejoindre le groupe par le dialogue : `PartyJoinEvent`, `JoinOnly`), `23554f2` (place
  gardée au retour de l'host + second état de zone ignoré), `7238c7a` (`OtherModsCompat`), `09410f4` (test Y1 :
  un invité seul sur sa carte peut dormir, la limite notée n'existait pas).
- Pièges : `Party.AddMemeber` appelé directement par le jeu (dialogue d'un habitant, liste des résidents) ne
  passe pas par `MakeAlly` ; le client reçoit deux `ZoneDataResponse` pour la même carte quand l'host y entre
  (réponse à sa demande + diffusion de l'entrée) ; `ilspycmd` 9.1 demande `DOTNET_ROLL_FORWARD=LatestMajor`.
- 19h30 : passe complète lancée sur ce build (`_shots/soir-long.log`, `_shots/soir-short.log`, 21 suites dont
  `recruit_suite` et `compat_suite`). **Le jeu de ce PC a le build Debug : remettre la version publiée (ou une
  nouvelle) avant que l'utilisateur rejoue avec son ami.**
- Demandes en attente : fluidité des déplacements de l'invité (agent en cours), import d'un personnage solo
  (plan prêt), serveur indépendant (question de l'utilisateur, réponse donnée dans la conversation).

### Arrêt à 19h55 le 2026-10-03 (l'utilisateur met le PC en veille)
- Passe complète du soir **arrêtée** : seul `travel_suite` a fini (54/54) sur le build des cinq corrections.
  Les suites propres à chaque correction sont vertes (`recruit` 21/21, `leave` 13/13, `player` 38/38, `compat` 5/5,
  `sleep` Y1 6/6). **La passe complète reste à faire avant de publier ces corrections.**
- Le jeu de ce PC a de nouveau la **version publiée 0.26.337** (pour jouer avec l'ami). Les corrections du soir
  n'y sont pas. Avant de reprendre les tests : `dev/build.ps1`.
- Fluidité des déplacements d'un invité (demande de l'utilisateur) : cause lue dans le code par un agent — chez
  un client, `Core.gameDelta` est remplacé par le temps de jeu de l'host reçu par le réseau
  (`GameSynchronizationContext`), donc chaque pas attend ce temps, qui arrive par paquets, alors que l'animation
  suit l'horloge locale. **Écrit, compile, jamais lancé** : branche `wip/player-clock` (option host `PlayerClock`,
  règle `UsePlayerClock` clé 8, active seulement avec `PlayerCombatTime` ; le client garde son horloge locale ;
  l'host ne passe plus en turbo pour la marche d'un invité ; test `move_suite.py` V1–V3 : pas réguliers même quand
  l'host tourne à 5 images par seconde). À faire : jouer `move_suite` sur l'ancien build (rouge attendu sur V2),
  puis sur la branche, puis `combat_suite`, `guest_suite`, `sleep_suite`. Second point de l'agent, pas fait :
  le rythme des pas dépend de l'écart de vitesse entre joueurs (`SetActTime`, `RefSpeed`).
- Reste de la liste de l'utilisateur, dans l'ordre : fluidité (ci-dessus), import d'un personnage solo (plan dans
  `PLAN_retours_partie_reelle.md`, pas commencé), autres chemins de recrutement (causes 2 et 3), retour de l'host
  sans rechargement (plan B), profil de mods, puis temps du monde commun et serveur indépendant (réponse donnée :
  niveau 1 « serveur gardien » recommandé, il attend sa décision).

### Reprise sur le Steam Deck (2026-10-03, 21h05)
- `git pull` (10 commits, jusqu'à `5b54595`), `build.ps1` : 0 erreur, mod 0.26.347 en Debug dans le jeu.
- **Piège, encore** : Steam avait mis Elin à jour (EA 23.351 **Patch 2**, `game 0.23.351.0 -> 0.23.351.2`). Le
  client du banc était refusé (« invalid version »), `mp_test.py` a attendu trois fois 5 minutes sans dire
  pourquoi. Remède habituel : fermer les fenêtres, `make_lab.py Elin2 2` (3, 4). Ensuite host + client connectés
  en 1 min 30.
- 21h56 : passe complète lancée sur `5b54595` (journaux `_shots/*-p2.log`, résumé `_shots/p2-long.log`).
- **Passe complète verte sur `5b54595` (code inchangé depuis), Elin EA 23.351 Patch 2, 21 suites sur 21** :
  travel 54/54, shared 26/26, trio 24/24, companion 30/30, party 28/28, economy 25/25, combat 21/21,
  quest 61/61, chara 13/13, parity 17/17, trade 32/32, build 21/21, player 40/40, instance 34/34, leave 15/15,
  transfer 11/11, death 13/13, sleep 34/34, guest 218/218, recruit 23/23, compat 7/7.
  Interrompue deux fois à la demande de l'utilisateur (reprise à 0h04 puis 0h20 le 4), sans échec.
- **Piège** : `economy_suite` et `combat_suite` ouvrent elles-mêmes leurs fenêtres (3 joueurs) : elles vont dans
  `run_all.sh`, pas dans `run_short.sh` (« Elin tourne deja », arrêt immédiat). Série courte = quest, chara,
  parity, trade, build, player, instance, leave, transfer, death, sleep, guest, recruit, compat.
- **Piège** : arrêter la tâche de fond ne ferme ni `bash run_all.sh`, ni le python de la suite, ni `mp_test.py`,
  ni les jeux : les fermer tous par numéro (`Get-CimInstance Win32_Process`), sinon de nouvelles fenêtres s'ouvrent.
- Décisions de l'utilisateur ce soir : rythme des pas = **option A** (chaque joueur marche comme en solo), avec
  sa propre case host ; serveur « dépôt de sauvegarde » retenu pour la suite (voir « Idées »).

### Version 0.26.349 publiée depuis le Steam Deck (2026-10-04, 1h35)
- `make_release.ps1` sur `17614f7` : **mod 0.26.349**, 1 084 377 octets, pas de `.pdb`. Publié en préversion
  `independance-0.26.349`, fichier public identique au zip local (SHA-256 `03831336…8a1c78`). Copie gardée :
  `_release/ElinTogether-independance-0.26.349.zip`. Contenu nouveau : les cinq corrections du 3 au soir.
- Le build Release se charge en jeu ici : « Loading [Elin Together 0.26.349] », écran titre, 0 exception dans
  `Player.log`. Son coupé par `volumeMaster` dans `Save/config.txt`, fichier remis à l'identique ensuite.
  Vu dans la console au lancement (pas dans `Player.log`, le jeu continue) : un bloc « Native Crash Reporting »
  de mono dans `ReflexCLI.CommandRegistry.LoadAssembly` (Elin Scripting Kit). Pas de notre mod, sans effet visible.
- `gh` n'est pas installé ici : publication par l'API GitHub avec l'identifiant que git a déjà (`git credential
  fill`). `target_commitish` veut le numéro de commit **entier** (422 sinon).
- `independance-0.26.337` et `independance-0.26.309` sont toujours sur la page : à retirer si l'utilisateur le
  veut (elles ne se connectent pas à la 0.26.349).

### Fluidité des déplacements d'un invité : fusionnée (2026-10-04, 1h30 → 2h15)
- `move_suite.py` sur le code publié (0.26.349) : **rouge 6/9**. Host à 5 images par seconde : le pas de
  l'invité passe de 120 à 240 ms. Host trois fois plus rapide : l'invité à 209 ms par pas, l'host à 34 ms.
- Branche `wip/player-clock` fusionnée (`48930ce`) avec trois ajouts :
  - **case host `PlayerStepPace`** (« chaque joueur marche comme en solo », option A choisie par l'utilisateur,
    règle `UsePlayerStepPace` clé 9, active avec `PlayerCombatTime`) : le tour d'un joueur dure toujours le
    temps de base, il n'est plus étiré par la vitesse des autres. En combat rien ne change (le temps donné aux
    monstres par tour garde le rapport des vitesses). `5584c51`.
  - **accéléré partagé** (`6af7ffa`), trouvé par la relecture : sur sa propre horloge, l'accéléré d'un invité
    n'accélérait que lui, et celui de l'host le laissait en arrière. L'invité dit quand il accélère
    (`PlayerCharaStateSnapshot.Turbo`), le monde de l'host suit ; l'host envoie l'allure de son monde
    (`GameDelta.Turbo`, lue au début de l'image : `WorldTurbo`) et le jeu de l'invité est relevé à cette allure,
    jamais multiplié par-dessus la sienne (`FollowsHost`).
  - `move_suite` V4 à V6, échauffement, cases réglées par le test lui-même. **Vert 17/17.**
- **Pièges du test** :
  - une marche lancée par `AI_Goto` met le jeu de celui qui marche en accéléré (x2,2) : les 118 ms par pas
    sont déjà une allure d'accéléré (pas de base : 260 ms) ;
  - l'option du jeu « courir tout seul » allume l'accéléré selon la distance entre la souris et le personnage :
    la mesure dépendait de l'endroit où traînait le pointeur. Le test la coupe le temps des mesures ;
  - la première marche après un lancement part en rafale : le pont de test compile ses commandes, le jeu se
    fige un instant puis rattrape (temps d'image lissé). D'où la marche d'échauffement ;
  - un `eval` qui passe par `Traverse`/`TypeByName` prend plus d'une seconde : pas dans une boucle de mesure ;
  - un joueur immobile perd l'accéléré à chaque image (`AM_Adv`, `HasNoGoal` → `EndTurbo`) ;
  - dans un script lancé par l'outil Bash, `\\n` devient un vrai retour à la ligne : écrire les fichiers C#
    avec l'outil d'écriture, pas par un script en ligne.
- Pas testé : la marche touche enfoncée ou souris tenue (`GoalManualMove`), le pont ne tient pas de touche.
- Passe complète relancée sur `6af7ffa` à 2h11 (`_shots/*-p3.log`).
- Écrit pendant la passe, **pas compilé, pas lancé** : personnage d'une sauvegarde solo (`Helper/CharaImport.cs`,
  case `ImportCharacter`, test `import_suite.py`) et autres recrutements (`CharaMakeAllyEvent.Recruiter`,
  `CharaMakeAllyRequestDelta.Data`, `recruit_suite` R7 boule à monstre, R8 animal acheté, R9 monture).

### Import d'un personnage solo et autres recrutements (2026-10-04, 2h20 → 3h25)
- Passe complète sur `6af7ffa` (fluidité), suites longues : combat 21/21, economy 24/24, travel 55/55,
  shared 26/26, trio 24/24, companion 30/30, party 28/28.
- Écrits pendant cette passe, relus par un agent avant la première compilation (deux `using` oubliés ; l'animal
  acheté n'aurait jamais été vu des clients : un personnage désérialisé chez l'host n'émet pas de
  `CardGenDelta`, il faut l'envoyer comme un compagnon qui revient ; le propriétaire posé pendant l'application
  d'un delta n'était dit à personne ; un invité qui ranime un compagnon de l'host le prenait).
- **Personnage d'une sauvegarde solo** `6d43567` : `Helper/CharaImport.cs`, case host `ImportCharacter`
  (décochée par défaut), message `SessionCharaImportResponse`, `SessionCharaSelectRequest.AllowImport/Notice`.
  Liste : les 8 dernières sauvegardes **écrites** (date du fichier `game.txt`, pas la date que porte la
  sauvegarde : une copie la garde). Source = `dossier/numéro/nom`, gardée sur la copie (`emp_import`).
  `import_suite.py` : rouge (case absente) → **21/21**, marché du premier coup ; seul écart, la hache que le mod
  offre à tout invité, que le test écarte de la comparaison.
- **Autres recrutements** `7b0c70e` : `CharaMakeAllyEvent.Recruiter` (cadeau, delta du joueur en cours
  d'application `ElinDelta.Apply` → `Actor`, tâche terminée par l'host pour lui, tour de sa copie
  `ActingRemotePlayer`), monture dans `PartyJoinEvent.OnAddMember` (seulement si c'est bien sa monture),
  `CharaMakeAllyRequestDelta.Data` + `AdoptLocal` pour le personnage qui n'existe que chez l'acheteur.
  `recruit_suite` R7–R9 : rouge 8/21 → **41/41** avec R1–R6.
- **Pièges** :
  - « monter » (`ActRide.Perform`) prend le **dernier personnage de la case visée** : les compagnons de l'invité
    le suivent jusque sur cette case et c'est l'un d'eux qui est monté. R9 passe donc avant R7 et R8 ;
  - `ActRide.Perform` renvoie toujours faux ; `new ActRide()` n'a pas de numéro et n'est pas transmis :
    `EClass.pc.UseAbility(ACT.Create(ABILITY.ActRide), cible, case)` ; `ActRide.Ride` direct n'est pas transmis ;
  - un personnage reçu entier de l'host et déjà « global » n'est pas ajouté à la liste des personnages du monde
    du client (`SetGlobal` ne fait rien) : ajouté dans `CharaMakeAllyDelta` ;
  - l'outil Bash casse aussi un script Python donné en ligne quand il contient certaines suites de guillemets :
    écrire le script dans un fichier.
- 3h27 : passe complète relancée sur `7b0c70e` (`_shots/*-p4.log`), courtes d'abord.
- **Passe complète verte sur `7b0c70e`, 23 suites sur 23** (5h06) : quest 61/61, chara 13/13, parity 17/17,
  trade 32/32, build 21/21, player 40/40, instance 34/34, leave 15/15, transfer 11/11, death 13/13, sleep 34/34,
  guest 218/218, recruit 41/41, compat 7/7, move 18/18, import 21/21, companion 30/30, party 28/28,
  combat 21/21, economy 24/24, travel 55/55, shared 26/26, trio 24/24.
  `move_suite` avait fait 16/18 dans la série : sa mesure de référence partait en rafale parce que la commande
  de départ changeait de texte à chaque position (recompilée par le pont, jeu figé un instant). Commande rendue
  constante (`e1b9a44`), 18/18 deux fois de suite sur des mondes neufs.
  **Piège** : `bash run_short.sh … | head -1` coupe le script avant qu'il ferme ses fenêtres.

### Version 0.26.362 publiée depuis le Steam Deck (2026-10-04, 5h15)
- `make_release.ps1` sur `f9b2ecd` : **mod 0.26.362**, 1 091 645 octets, pas de `.pdb`. Préversion
  `independance-0.26.362`, fichier public identique au zip local (SHA-256 `660e5e1f…5d716b`). Copie gardée :
  `_release/ElinTogether-independance-0.26.362.zip`. Nouveau par rapport à 0.26.349 : fluidité des déplacements
  d'un invité, case « chacun marche comme en solo », personnage d'une sauvegarde solo, compagnons d'un invité
  par boule à monstre, monture, achat.
- Le build Release se charge en jeu ici (« Loading [Elin Together 0.26.362] », écran titre, 0 exception). Son
  coupé par `Save/config.txt` le temps de l'essai, fichier remis à l'identique.
- **Le jeu de cette machine a la version publiée 0.26.362** (le build Release laissé par `make_release.ps1`),
  prête pour jouer avec l'ami une fois qu'il a le même zip. Avant de reprendre les tests : `dev/build.ps1`.
- Publication : `dev/_tools/publish_release.py <version> <commit entier> <note.md> <zip>` (API GitHub avec
  l'identifiant que git a déjà ; vérifie que le fichier public est identique).
- Sur la page des versions : `independance-0.26.349`, `-0.26.337` et `-0.26.309` sont toujours là. Aucune ne se
  connecte à la 0.26.362. À retirer si l'utilisateur le veut (pas fait sans lui).

### À faire ensuite (état au 2026-10-04, 5h15)
1. L'utilisateur joue la 0.26.362 avec son ami : fluidité entre deux PC, import d'un vrai personnage, recrutements.
2. Ce qu'il a demandé de ne commencer **qu'après lui avoir demandé**, un par un : retour de l'host sans
   rechargement (plan B de `PLAN_retours_partie_reelle.md`), profil de mods (`PLAN_profil_mods.md`), touche
   « signaler un problème », bot qui rejoue une vraie soirée, faux réseau lent.
3. Temps du monde commun puis serveur « dépôt de sauvegarde » : il veut s'y mettre maintenant que 1 à 4 sont
   faits ; **lui présenter le plan avant de coder**.
4. Petits restes : brosse à tester en jeu, animal de Fiama, laisse qui regarde l'host, écran de choix à chaque
   connexion quand seule la case d'import est cochée.

### Sauvegardes du nuage Steam, captures, plan du serveur (2026-10-04, 5h10 → 5h45)
- Captures des nouveautés (`showcase.py options imported`, `_shots/nouveautes/01`, `14` à `16`). En les
  regardant : la liste ne montrait que `world_import` et `world_lab`. **Les vraies sauvegardes de l'utilisateur
  sur cette machine sont dans le nuage Steam** (`Cloud Save/world_1`, `world_3` : `index.txt` à côté de
  `cloud.zip`, qui contient `game.txt`) ; `Save/world_N` ne contient que des dossiers `Temp` vides. La 0.26.362
  ne lui aurait donc rien proposé.
- Corrigé `1ed724d` (voir `git log`, « Steam Cloud saves were missing ») : les deux dossiers sont listés ; une
  sauvegarde du nuage est lue **dans son archive, en mémoire** (`ZipArchive`, référence
  `System.IO.Compression.dll` du jeu ajoutée au projet), jamais déballée ni déplacée (le chargement du jeu, lui,
  déplace `cloud.zip` et vide le dossier). `import_suite` I6 : rouge 21/22 → **25/25**.
- Essai réel : le personnage Onold de l'utilisateur (`Steam Cloud world_1`, niveau 4, 292 pièces d'or, 32
  objets) importé dans le monde de test : en jeu en 8 s, même fiche chez l'host, aucun numéro en double,
  dossier de la sauvegarde inchangé à l'octet près. Capture `_shots/mp-import-reel-onold.png`.
- Contrôle sur ce build : chara 13/13, import 25/25, leave 15/15, quest 61/61, compat 7/7.
- Plan du serveur « dépôt de sauvegarde » écrit d'après un recensement en lecture seule de tout ce qui dépend
  du jeu de l'host : `PLAN_serveur_depot.md`. **Rien de codé, à valider par l'utilisateur.**

### Version 0.26.366 publiée (2026-10-04, 5h50) — reprendre ici
- `make_release.ps1` sur `dc879ba` : **mod 0.26.366**, 1 092 122 octets, pas de `.pdb`. Préversion
  `independance-0.26.366`, fichier public identique au zip local (SHA-256 `6db1f695…2c7187`). Copie gardée :
  `_release/ElinTogether-independance-0.26.366.zip`. Elle remplace la 0.26.362 (publiée à 5h15), qui ne listait
  pas les sauvegardes du nuage Steam. Chargée une fois en jeu (écran titre, 0 exception), son remis à l'identique.
- **Le jeu de cette machine a la version publiée 0.26.366.** Avant de reprendre les tests : `dev/build.ps1`.
- Page des versions : `independance-0.26.362`, `-0.26.349`, `-0.26.337`, `-0.26.309` y sont encore. Aucune ne se
  connecte à la 0.26.366 ; la 0.26.362 n'a plus d'intérêt. **À retirer si l'utilisateur le veut** (pas fait
  sans lui).
- La liste « À faire ensuite » de la section précédente reste vraie, avec en plus : valider avec lui
  `PLAN_serveur_depot.md` (cinq décisions) avant de commencer le temps du monde commun.

### Temps du monde commun, première marche du serveur (2026-10-04, 9h → …) — reprendre ici
- L'utilisateur au réveil : « tu avais d'autres choses à faire ». Il avait dit la veille de continuer sans
  s'arrêter et que le serveur commençait dès que le reste était bon. **Ne pas s'arrêter pour demander** quand il
  a dit de continuer : prendre les choix proposés dans le plan et avancer. Il a confirmé que le serveur est bien
  son idée (un programme qui est juste la sauvegarde).
- **Étape 1 du plan faite** `a76d6a9` : case host `SharedWorldTime` (règle `UseSharedWorldTime`, clé 10).
  Un joueur qui tient une carte dit la date que son jeu a atteinte (`WorldTimeReportDelta`, union 504, envoyée
  hors de la carte de l'host comme le chat) ; l'host rattrape par `GameDate.AdvanceMin` (donc avec tout ce que
  fait une heure ou un jour qui passe), son personnage vit ce temps, et il le redit à tous ; un joueur qui tient
  une carte rattrape de même quand le monde a avancé sans lui (`WorldDateAdvanceEvent.CatchUp`, à l'image
  suivante, hors de la boucle des deltas). Garde-fou : pas plus d'un mois de jeu d'un coup.
- `time_suite.py` W1–W5 : **rouge 7/12** case décochée (l'host n'avance pas avec l'invité, l'invité ne suit pas
  l'host, la date de l'invité recule de 300 minutes à son retour) → **vert 12/12**.
- **Piège** : `Chara.TryMoveTowards` appelé par le pont déplace le joueur sans lui faire jouer de tour, donc sans
  faire passer le temps. Une vraie marche (`AI_Goto`) fait passer ~7 minutes de jeu pour 11 pas. Le monde de
  l'host ne fait passer aucune minute tant que son joueur ne joue pas.
- En cours : `travel`, `shared`, `trio`, `economy`, puis `sleep`, `quest`, `instance`, `transfer`, `leave`,
  `guest`, `time`, `move` sur ce build (`_shots/*-p6.log`).
- Écrits pendant ce temps, **pas compilés** : la marque de l'animal de Fiama (le compagnon fabriqué chez
  l'acheteur part à l'image suivante, avec ce que le dialogue lui pose après le recrutement) ; l'écran de choix
  n'est plus affiché à chaque connexion quand seule la case d'import est cochée (une fois, tant que le joueur n'a
  personne ici) ; `recruit_suite` R10 (brosse) et la marque dans R8.
- **Le jeu de cette machine a le build de test.** Remettre une version publiée avant que l'utilisateur joue.
- Contrôle sur `a76d6a9` (temps commun) : travel 54/54, shared 26/26, trio 24/24, economy 25/25, sleep 34/34,
  quest 61/61, instance 34/34, transfer 11/11, leave 15/15, guest 218/218, time 14/14. `move_suite` 17/18.

### Gardien du monde et petits restes (2026-10-04, 10h → 10h50) — reprendre ici
- Étude en lecture seule de ce que `GameDate.AdvanceMin/Hour/Day/Month` fait, classé « carte », « joueur »,
  « monde ». Elle a montré que le temps commun rendait systématiques deux doublons déjà présents : une quête qui
  expire et l'impôt du mois coûtaient renommée et karma deux fois (dans le jeu de l'host et dans la copie du
  joueur parti seul, dont la perte remontait à l'host par `PlayerStanding`).
- **Gardien du monde, premier commit** `1b0f5c3` : case host `WorldKeeper` (règle `UseWorldKeeper`, clé 11),
  `Patches/WorldKeeper.cs`. Un jeu qui a rejoint une session ne fait plus ce que le temps fait au monde : météo,
  quêtes expirées, sites aléatoires, données du jour, jour et mois de la faction, lettres et colis aléatoires.
  La météo du gardien est envoyée à tous (`WeatherDelta`, union 505), y compris aux joueurs de la carte de
  l'host, qui ne la voyaient jamais changer. Un rattrapage fait vivre au personnage un jour de temps au plus.
  `world_suite.py` K1–K4 : **rouge 6/9** case décochée (deux météos, la copie de l'invité comptait sa fin de
  mois et fabriquait 7 colis) → **vert 10/10**.
- **Petits restes** `d3d5622` : le personnage fabriqué chez l'acheteur part à l'image suivante, avec la marque
  que le dialogue lui pose après le recrutement (animal de Fiama) ; avec la case d'import seule, plus d'écran de
  choix à chaque connexion ; `recruit_suite` R10, domptage par la vraie action de la brosse (`AI_TendAnimal`,
  brosse en main). **recruit 47/47, import 27/27.**
- **Piège Harmony** : plusieurs `[HarmonyPatch(type, méthode)]` sur une seule méthode se combinent en UNE cible.
  Pour plusieurs cibles : une classe avec `TargetMethods()`.
- **`move_suite` irrégulière depuis ~10h** (13/18, 15/18, 16/18 ; 18/18 deux fois à 4h20 sur `7b0c70e`) :
  `idle.ps1` donnait 0 s, **l'utilisateur se servait du PC**. L'accéléré d'une marche dépend des entrées
  (souris, Maj) que reçoivent les fenêtres du jeu. À rejouer PC libre avant de conclure à une régression du
  temps commun (rien dans ce code ne touche un joueur présent sur la carte de l'host).
- **Arrêt des fenêtres de jeu à 10h50** : règle de `CLAUDE.md`, pas de fenêtre quand l'utilisateur se sert du PC.
  **Pas faite : la passe complète sur le gardien du monde**, donc pas de nouvelle version publiée. À faire PC
  libre : `build.ps1`, passe complète (avec `time_suite`, `world_suite`), `move_suite` deux fois, puis version.
- **Le jeu de cette machine a de nouveau la version publiée 0.26.366** (dossier du zip recopié dans `Package`,
  même fichier). Le temps commun et le gardien n'y sont pas.


### Machine partagée avec une autre session (2026-10-04, 13h)
- L'utilisateur : « c'est trop, 4 clients Elin » (une autre session travaille sur un serveur privé Dofus sur ce PC).
  **Sur cette machine, ne plus lancer `trio_suite` (host + 3 clients)** tant qu'il ne dit pas le contraire ; deux
  fenêtres au plus par défaut. `trio_suite` était verte sur `a76d6a9` (temps commun), pas rejouée sur le gardien
  du monde : un essai a échoué sur une connexion locale entre deux fenêtres (10 s sans réponse), sans exception.
- Passe sur `2c6a89e` (gardien du monde + petits restes) : travel 54/54, shared 26/26, companion 30/30,
  party 28/28, combat 22/22, economy 25/25. Courtes en cours (`_shots/*-p8.log`).
- Courtes sur `2c6a89e` : quest 61/61, chara 13/13, parity 17/17, trade 32/32, build 21/21, player 40/40,
  instance 34/34, leave 15/15, transfer 11/11, death 13/13, sleep 34/34, guest 218/218, recruit 47/47, compat 7/7,
  import 27/27, time 14/14, world 10/10, move 18/18 (la mesure de référence de `move_suite` est reprise jusqu'à
  trois fois si elle est irrégulière : la première marche mesurée part parfois encore en rafale).

### Version 0.26.375 publiée (2026-10-04, 14h45)
- `make_release.ps1` sur `807d13d` : **mod 0.26.375**, 1 095 659 octets. Préversion `independance-0.26.375`, fichier
  public identique (SHA-256 `0242d6cc…de1988`), copie `_release/ElinTogether-independance-0.26.375.zip`. Chargée
  une fois en jeu (écran titre, 0 exception). Nouveau : une seule date pour le monde, gardien du monde (météo,
  impôts, quêtes expirées une seule fois), brosse, marque de l'animal de Fiama, écran de choix une seule fois.
- 24 suites sur 25 vertes sur ce code ; `trio_suite` (4 fenêtres) pas rejouée, voir plus haut.
- Page des versions : 0.26.366, 0.26.362, 0.26.349, 0.26.337, 0.26.309 y sont encore, à retirer si l'utilisateur le veut.
- Ensuite : branche `wip/keeper2` (dossier `ElinMods\_wt-keeper2`, pas compilé) : colis et chance du jour chez le
  gardien seulement, charisme du dompteur (`TameCharismaPatch`).

### Suite du gardien, charisme du dompteur, dépôt de sauvegarde (2026-10-04, 14h45 → 15h30) — reprendre ici
- L'utilisateur a demandé d'utiliser les skills **ponytail** (la plus petite solution qui marche) à partir de 13h.
- `d7a83ab` : un invité dompte avec son propre charisme (le jeu lisait celui du joueur local, donc de l'host) :
  `TameCharismaPatch`, `recruit_suite` R10 avec seul le charisme de l'invité monté, rouge puis vert.
- `856d878` : seul le gardien envoie et livre les colis (`World.SendPackage`, `FactionBranch.ReceivePackages`),
  et sa « chance du jour » est celle de tous (`DayDataDelta`, union 506). `world_suite` K1 rouge (deux chances
  différentes) puis 11/11. Les boucles internes de `GameDate` sont laissées tant qu'un test ne montre pas un
  doublon (ponytail).
- Contrôle : world 11/11, time 14/14, sleep 34/34, quest 61/61, guest 218/218. `recruit_suite` 41/43 : la
  capture à la boule à monstre a raté une fois (réussie les trois fois précédentes), à rejouer.
- **Dépôt de sauvegarde** (commit « a save depot ») : en appliquant ponytail à l'idée de l'utilisateur, le
  serveur « qui est juste la sauvegarde » devient un dossier partagé. `Helper/SaveDepot.cs`, réglage client
  `DepotPath`, deux boutons dans l'onglet Lobby, le dossier se règle dans l'onglet Client Settings.
  `depot_suite.py` D1–D6 : **11/11** (premier essai 2/4 : `EClass.pc` lève une exception à l'écran titre, il n'y
  a pas de jeu). Détail et limites dans `PLAN_serveur_depot.md` et `DOCUMENTATION.md` section 6.
- **Piège** : `EClass.pc` n'est pas nul sans jeu, il lève une exception. Tester `EClass.core.IsGameStarted`.
- En cours : recruit, chara, leave, depot, travel sur ce build (`_shots/*-p10.log`), puis une version.
- Le jeu de cette machine a le build de test ; la dernière version publiée est la 0.26.375.

- Contrôle sur le build du dépôt : recruit 45/45, chara 11/11, depot 11/11, travel 54/54, leave 13/13 (un premier
  passage à 12/13 : l'host est arrivé par hasard à deux cases de l'invité, qui était bien resté à sa place).

### Version 0.26.382 publiée (2026-10-04, 16h05) — reprendre ici
- `make_release.ps1` sur `88d435b` : **mod 0.26.382**, 1 098 852 octets, préversion `independance-0.26.382`, fichier
  public identique (SHA-256 `300707c9…baab8e`), copie `_release/ElinTogether-independance-0.26.382.zip`. Chargée une
  fois en jeu (0 exception). Nouveau depuis 0.26.375 : dépôt de sauvegarde, colis et chance du jour chez le
  gardien seulement, charisme du dompteur.
- **Le jeu de cette machine a la version publiée 0.26.382** (build Release laissé par `make_release.ps1`).
- Page des versions : 0.26.375, 0.26.366, 0.26.362, 0.26.349, 0.26.337, 0.26.309 y sont encore.
- À faire avec l'utilisateur : essayer le dépôt entre deux PC (dossier synchronisé), décider s'il faut le
  relais sans coupure et un programme à la place du dossier. Sinon, liste du point 5 (plan B du retour de
  l'host, profil de mods, touche « signaler un problème », bot de soirée, faux réseau lent).

### Serveur « comme un serveur Minecraft » (2026-10-04, 16h → 16h40) — reprendre ici
- L'utilisateur, après l'explication du dépôt : « ça me dérange pas d'avoir quelque chose qui tourne sur ce pc,
  c'est mon pc de dev, ça serait pas possible d'héberger un serveur comme un serveur minecraft ».
- Fait (commit « a server like a Minecraft server ») : `Emp/EmpServer.cs`. `Elin.exe -empserver <sauvegarde>`
  charge la sauvegarde et ouvre la partie tout seul (port 55556), coupe le son, ferme la question « mods
  manquants », sauvegarde toutes les 5 minutes tant qu'un joueur est là. `cloud:<id>` pour une sauvegarde du
  nuage Steam, `world_depot` pour prendre le monde du dépôt. Côté joueur : onglet Lobby, « Join by address »
  (`ElinNetClient.ConnectAddress`, `IsDirectConnection` : pas de lobby Steam ; les cartes des autres joueurs se
  rejoignent toujours par Steam). `Serveur.bat` + `serveur.ps1` dans le zip : trouve le jeu, liste les
  sauvegardes (les deux dossiers), lance, affiche les adresses.
- Presque tout existait : connexion directe par adresse (le banc), cartes simulées par les joueurs, date commune
  (c'est elle qui fait qu'un serveur que personne ne joue suit le temps des joueurs : +15 min quand le joueur
  passe 15 min sur sa carte, sans rien ajouter).
- `server_suite.py` V1–V5 : **7/7**. Deux faux départs : le serveur attendait une interface « inactive » à
  l'écran titre (elle ne l'est jamais) ; le test appelait `ElinNetClient` directement (classe interne : par
  réflexion).
- **À vérifier par l'utilisateur** : le même compte Steam sur le PC serveur et sur le PC où il joue (Steam
  peut bloquer) ; la connexion depuis chez son ami (port 55556 UDP ou réseau privé).


### Version 0.26.385 publiée (2026-10-04, 16h50)
- `make_release.ps1` sur `fd2b1a2` : **mod 0.26.385**, 1 102 000 octets, préversion `independance-0.26.385`, fichier public
  identique (SHA-256 `b7715504…9461bb`), copie dans `_release`. Le zip contient `Serveur.bat` et `serveur.ps1`.
  Chargée une fois en jeu (0 exception). **C'est la version dans le jeu de cette machine.**
- Demande suivante de l'utilisateur : « je voudrais que le serveur soit un vrai logiciel avec une interface, le
  plus light possible ». Prévu : un petit exécutable (choix de la sauvegarde, démarrer/arrêter, état, joueurs,
  adresses), le jeu derrière sans affichage si Elin le supporte (`-batchmode -nographics`, à tester), arrêt
  propre avec sauvegarde.

### Elin Together Server, le logiciel (2026-10-04, 16h50 → 17h15) — reprendre ici
- L'utilisateur : « je voudrais que le serveur soit un vrai logiciel avec une interface, le plus light possible »,
  puis « le serveur n'est pas Elin n'est-ce pas, pas besoin d'avoir une copie d'Elin pour que ça tourne ».
  Réponse donnée : jusque-là si, c'était Elin derrière. Fait ensuite : le mode sans Elin.
- `dev/server/ElinTogetherServer.cs` (un fichier, WinForms, compilé par le `csc` de Windows :
  `dev/server/build.ps1` → `_release/template/ElinTogetherServer.exe`, 23 Ko, aucune dépendance) :
  - **Sans Elin** : classe `Depot`, un `TcpListener` (port 55557, pas de droits administrateur). Une demande par
    connexion : mot de passe, commande (`WHO`, `TAKE`, `PUT`, `BEAT`, `RELEASE`), identité, nom, longueur, octets.
    Le monde est une archive `world.zip` (écrite à côté puis échangée), les trois précédentes sont gardées.
    Verrou réel, périmé après trois minutes sans signe de vie. Côté jeu : `SaveDepot` a deux formes, dossier ou
    `adresse:port` ; ce qui vient du réseau n'est déballé que dans le dossier de la sauvegarde.
  - **Avec Elin** : lance `Elin.exe -batchmode -nographics -empserver <id>`, lit `ElinMP/server.txt`, arrête par
    `ElinMP/server.stop` (le serveur sauvegarde puis `Application.Quit`), force l'arrêt après 45 s.
- **Elin tourne en `-batchmode -nographics`** : `server_suite` 7/7 sans fenêtre ni affichage.
- Tests sur le build final : `depot_suite` 11/11 (dossier), 11/11 avec `DEPOT_SERVER=1` (le logiciel),
  `server_suite` 9/9 sans fenêtre (avec V6 : état écrit, arrêt après sauvegarde).
- **Piège** : enchaîner `mp_test.py` juste après `run_short.sh` échoue (« Elin tourne déjà », les fenêtres ne sont
  pas encore fermées) : attendre quelques secondes.
- Captures : `ElinMods\_shots\nuit-2026-10-04\serveur-sans-elin.png`.


### Version 0.26.388 publiée (2026-10-04, 17h25) — reprendre ici
- `make_release.ps1` sur `951776f` : **mod 0.26.388**, 1 117 074 octets, préversion `independance-0.26.388`, fichier public
  identique (SHA-256 `524da968…47fc7e`), copie dans `_release`. Le zip contient `ElinTogetherServer.exe`
  (23 040 octets), `Serveur.bat`, `serveur.ps1`. Chargée une fois en jeu (0 exception).
- **Le jeu de cette machine a la version publiée 0.26.388.** Avant de reprendre les tests : `dev/build.ps1`.
- Page des versions : sept anciennes versions y sont encore (0.26.385, .382, .375, .366, .362, .349, .337, .309),
  à retirer si l'utilisateur le veut.
- À faire avec lui : essayer le serveur entre deux PC (les deux modes) ; décider si le mode sans Elin doit
  apprendre le relais sans coupure quand l'hébergeur part (plan long, étapes 3 et 4 de `PLAN_serveur_depot.md`).
- L'utilisateur : « en mode sans Elin est-ce qu'on peut sélectionner la sauvegarde ? c'est un peu tout
  l'intérêt ». Ajouté : liste des sauvegardes du PC et « Parcourir… » (dossier d'une sauvegarde copiée d'ailleurs),
  bouton « Mettre cette sauvegarde sur le serveur » (`Depot.Import` : dossier avec `game.txt`, sauvegarde du nuage
  par son `cloud.zip`, ou archive ; refusé tant qu'un joueur héberge ; le monde précédent est gardé). Ligne de
  commande `--import <sauvegarde>` pour le test. `depot_suite` avec `DEPOT_SERVER=1` : 11/11, la sauvegarde
  vient du logiciel, plus d'un joueur.
- **Piège** : `ZipFile.CreateFromDirectory` de .NET Framework écrit les dossiers avec des barres inversées et une
  entrée `Temp\` pour le dossier vide : le jeu le prenait pour un fichier (accès refusé). `SaveDepot.Unzip`
  remet les barres dans le bon sens avant de décider.

### Version 0.26.390 publiée, passation (2026-10-04, 17h40) — reprendre ici
- `make_release.ps1` sur `452f89e` : **mod 0.26.390**, 1 118 345 octets, préversion `independance-0.26.390`, fichier public
  identique (SHA-256 `7a4a21cc…801ee1`), copie dans `_release`. `ElinTogetherServer.exe` : 26 112 octets, avec le
  choix de la sauvegarde. Chargée une fois en jeu (0 exception). **C'est la version dans le jeu de cette machine.**
- L'utilisateur ouvre une nouvelle session : passation dans `dev/HANDOFF.md`, message de départ dans
  `dev/PROMPT_reprise.md`.


### Premier essai entre deux PC, bouton d'adresse unique, logiciel en anglais (2026-10-04, soir) — reprendre ici
- **Premier essai réel de l'utilisateur entre deux PC** (même réseau local, serveur sur le Steam Deck, 192.168.1.28).
  Il lance Elin Together Server en mode « Without Elin » (TCP 55557) et, sur l'autre PC, utilise « Join by
  address ». Ce bouton ne parlait qu'à un serveur de jeu (mode « With Elin », UDP 55556) : rien ne répondait, et le
  jeu montrait la clé brute `emp_ui_timeout` (le texte manquait dans toutes les langues). Ce n'était pas le réseau :
  le serveur écoutait et le pare-feu laissait passer.
- Contournement qui a marché : « Client Settings », champ « Depot » = `192.168.1.28:55557`, puis onglet « Lobby »,
  bouton qui prend le monde. Il s'est connecté. **Le mode sans Elin a donc été joué une fois entre deux PC sur un
  réseau local** (connexion et prise du monde). **Pas encore essayé** : par Internet, le mode avec Elin entre deux
  PC, un deuxième joueur qui rejoint, l'hébergeur qui part.
- **Correction, commit `018091d`** : « Join by address » marche avec les deux serveurs. Il demande d'abord à
  l'adresse si c'est Elin Together Server. Si oui : cette adresse devient le dépôt (le réglage `DepotPath` se
  remplit tout seul), et le joueur prend le monde et l'héberge, ou apprend qui l'héberge déjà. Sinon il rejoint un
  serveur de jeu comme avant. Code : `TabLobbyBrowser.JoinAddress`, `SaveDepot.TakeFrom`. `emp_ui_timeout` a
  maintenant un texte (EN/JP/CN) : « The server does not answer. Check the address, the port and the mode of the
  server. » La saisie d'adresse cite les deux ports (55556 avec Elin, 55557 sans).
  **Plafond connu** : le jeu peut se figer jusqu'à 5 secondes si la machine à cette adresse laisse tomber la
  connexion sans rien répondre.
- Test : `depot_suite` avec `DEPOT_SERVER=1`, le deuxième joueur ne règle aucun dépôt et passe par `JoinAddress`.
  Le test utilise maintenant le port 55558, pour ne jamais heurter un vrai serveur de l'utilisateur sur 55557.
  **Rouge 3/4 avant la correction** (le joueur n'arrive jamais dans le monde), **vert 11/11 après**. Pas testé :
  le texte du délai lui-même (seuls les builds Release l'affichent).
- Pour les joueurs, il n'y a plus qu'**une chose à savoir** dans les deux modes : panneau Elin Together, onglet
  « Lobby », « Join by address », taper l'adresse affichée par le logiciel serveur. Le champ « Depot » de « Client
  Settings » existe encore (dossier partagé, mot de passe) mais n'est plus nécessaire pour le logiciel sans mot
  de passe.
- Partir d'un monde neuf : un joueur crée une partie normalement, puis onglet « Lobby », bouton « Put this save
  in the depot » (`emp_ui_depot_put`) ; le serveur garde le monde précédent à côté (`world.1.zip`). Ou choisir une
  sauvegarde dans le logiciel.
- **Quêtes « Dummy » / « Mokyu »** vues par l'utilisateur : **pas causées par le mod ni par le serveur**. Le monde de
  son serveur était sa sauvegarde du nuage Steam `world_3` (écrite le 2026-10-01 à 22h15, même taille à l'octet,
  1 628 098). Dans cette sauvegarde, 6 quêtes étaient déjà écrites `QuestDummy` avant tout travail sur le serveur ;
  leurs identifiants commencent par `dmp_quest_` (travel, massacre_religion, weightlifting) : des quêtes d'un autre
  mod, non installé sur le Steam Deck. C'est Elin lui-même (`GameSerializationBinder` : un type de quête introuvable
  à la lecture devient `QuestDummy`, et la sauvegarde suivante l'écrit). Les quêtes du jeu (histoire, dette,
  guildes, maison…) sont intactes dans le fichier. L'utilisateur prend une partie neuve pour le serveur.
  **Question ouverte** pour lui : quel mod fournit `dmp_quest_*` (une réparation serait possible, le vrai
  identifiant est encore dans la sauvegarde).
- **Elin Together Server est maintenant en anglais** (`dev/server/ElinTogetherServer.cs`, `dev/server/build.ps1`).
  Libellés : modes « Without Elin: keeps the world, a player hosts it » et « With Elin on this PC: the world
  runs all the time » ; boutons « Browse… », « Put this save on the server », « Start »/« Stop » ; case « No
  game window (lighter) » ; « Password (empty: none): » ; état « Running »/« Stopped » ; liste « Addresses to
  give to the players (double-click to copy): » et, dessous : « In the game: Elin Together panel, Lobby tab,
  "Join by address", and type one of these addresses. » `LISEZMOI.txt` et `DOCUMENTATION.md` les citent.
- **En cours, pas fait** : un message clair quand le mot de passe du serveur est faux (aujourd'hui le jeu peut dire
  « password is hosting the world ») ; rejouer les suites du serveur ; essayer à la main les boutons du logiciel ;
  une nouvelle version publiée. **Le jeu de cette machine a le build de TEST** ; la dernière version publiée est
  toujours la 0.26.390 : remettre une version publiée avant que l'utilisateur joue.
- **Pièges** : l'outil Bash casse les barres inverses dans un Python en ligne (un script avec `'\\'` dans un
  heredoc a échoué) : écrire les scripts avec l'outil d'écriture. Et `Player.log` du jeu installé est écrasé par
  les passes de test : il ne dit rien de la session de l'utilisateur sur un autre PC.
- Méthode : agent `haiku` pour chercher dans le code décompilé (il a trouvé `QuestDummy` ; son hypothèse sur la
  cause, la sérialisation réseau, était fausse : c'est le fichier de sauvegarde qui a donné la réponse), agent
  `sonnet` pour ces documents.

### Trous du parcours serveur corrigés, passation (2026-10-04, 18h45 → 19h20) — reprendre ici

- **Méthode** : cinq agents en lecture seule pour décider quoi faire. Trois `haiku` sur les trois dépôts GitHub que
  l'utilisateur veut utiliser, un `sonnet` qui classe le travail restant, un `sonnet` qui suit pas à pas le chemin
  d'un joueur qui arrive pour la première fois sur le serveur. Ce dernier a trouvé de vrais trous ; chacun a été
  vérifié dans le code avant d'être corrigé. L'utilisateur a donné carte blanche (« j'autorise tout »).
- **Commits** : `018091d` « Join by address » marche avec les deux modes, texte `emp_ui_timeout` ; `6ad16ab`
  logiciel serveur en anglais et documents ; `899b221` mot de passe faux dit clairement (« The server refused the
  password… ») ; `ab57854` corrections du serveur et test `dev/_tools/depot_proto_test.py` (parle le protocole du
  serveur sans le jeu, 10 secondes : rouge 5/11, vert 11/11). Les changements du jeu (`SaveDepot.cs`,
  `EmpServer.cs`, `ElinNetHostCompanions.cs`, textes, `depot_suite.py`, le logiciel serveur) sont dans le commit
  « the server path ».
- **Corrigé** :
  - Une partie neuve ne pouvait jamais remplacer le monde du serveur (refus dès qu'un monde existait). Maintenant :
    acceptée quand personne n'héberge, le joueur devient l'hébergeur ; refusée avec le nom de l'hébergeur sinon.
  - Après « Put this save on the server », le jeu continuait sa propre sauvegarde, donc les suivantes
    n'arrivaient jamais au serveur. Maintenant le « OK » du dialogue renvoie au titre et recharge le monde depuis
    le serveur (`world_depot`) : chaque sauvegarde y va.
  - Les trois sauvegardes de secours étaient effacées par quatre sauvegardes automatiques (20 minutes). Maintenant
    un monde remplacé est gardé pour de bon (`replaced-<date>.zip`, dossier du serveur) ; sauvegarde de secours
    glissante : au plus une par 30 minutes.
  - Fermer ou arrêter le logiciel pendant qu'un joueur héberge : il demande d'abord. Remplacer un monde depuis le
    logiciel : il demande d'abord.
  - 300 Mo de mémoire pouvaient être réservés sans mot de passe : le mot de passe est vérifié d'abord.
  - L'hébergeur n'était jamais prévenu quand ses sauvegardes n'arrivaient plus. Maintenant : fenêtre quand une
    sauvegarde n'est pas reçue ; la sauvegarde est marquée (`Save\world_depot.unsent`) ; à la prochaine prise du
    monde, le jeu propose de l'envoyer (le monde actuel du serveur est gardé à côté) ; si un autre joueur a repris
    le monde entre-temps, un dialogue le dit une fois.
  - Deuxième joueur : le message « X is hosting » dit de rejoindre par Steam (invitation, ou « Join Game » dans la
    liste d'amis Steam) et d'attendre jusqu'à 3 minutes si l'hébergeur vient de partir. Le message du serveur vide
    dit quoi faire.
  - Mode avec Elin : une sauvegarde sans base, ou une session qui ne peut pas s'ouvrir, fait écrire au jeu sans
    fenêtre `state=error:<raison>` puis quitter ; le logiciel affiche « The server could not start: … ».
  - Bogue trouvé par le test : exception quand l'hébergeur retourne au titre avec un invité encore connecté
    (`TakeCompanionsAlong`) : garde ajoutée.
  - Une relecture `sonnet` de ces changements a trouvé quatre défauts de plus, tous corrigés : un monde entier mis
    de côté à chaque sauvegarde après que le verrou a expiré pendant une mise en veille ; en mode dossier, une
    sauvegarde tardive pouvait détruire le monde plus récent d'un autre joueur (maintenant gardé à côté :
    `world.replaced-<date>`) ; un vieux repère « non envoyé » pouvait revenir sur une partie neuve qu'on venait de
    déposer ; un serveur sans fenêtre bloqué sur une question à laquelle personne ne peut répondre.
- **Pas testé** : le mode avec Elin sur une sauvegarde sans base (aucune sous la main) ; un port UDP déjà pris ne
  fait pas échouer la prise réseau de Steam (essayé : le serveur arrive quand même à « running »), donc ce cas n'est
  pas détecté. Les boutons du logiciel n'ont pas été essayés à la main.
- **Tests** : `depot_proto_test.py` 11/11 ; `depot_suite` en mode dossier 13/13 ; `depot_suite` avec `DEPOT_SERVER=1`
  19/20, le seul échec étant le compte du test lui-même (objets empilés comptés comme un seul), corrigé et relancé :
  résultat à lire dans `dev/_shots/depot_suite-srv4.log` ; `server_suite` sans fenêtre 9/9 (V1 à V6, rejoint par le
  même bouton que le joueur). La passe large sur le code final a été commencée puis arrêtée exprès après 3 suites
  (server 9/9, travel 54/54, depot 11/11), parce que le code changeait encore.
- **Trois dépôts GitHub à utiliser** : `DeusData/codebase-memory-mcp` (index local du code, serveur MCP, utile pour
  chercher dans le code décompilé ; l'utilisateur l'installe lui-même avec `install.ps1`, puis relance Claude Code :
  la session suivante cherche ses outils (ToolSearch « codebase-memory ») et les utilise à la place des agents
  haiku, en indexant le mod et `_decomp`) ; `trailhq/Graft` (même idée, plus lourd : clé d'API, mesures envoyées par
  défaut : jugé en double, pas installé) ; `msitarzewski/agency-agents` (230 fiches de rôles ; la fiche « multijoueur
  Unity » ne convient pas ; un relecteur propre au projet a été écrit :
  `Documents\ElinMods\.claude\agents\relecteur-elintogether.md`, modèle sonnet). Claude n'installe pas de
  programme tiers lui-même. Le serveur `fal` du plugin `universal-modder` a échoué (jeton refusé, HTTP 401).
- **Nouvelles consignes de l'utilisateur** : carte blanche (ne pas s'arrêter, noter le choix recommandé) ; plusieurs
  agents en parallèle pour décider et relire ; Remote Control activé à chaque début de session ; tout ce qu'il voit
  dans le logiciel serveur en anglais ; toujours écrire tout ce qui reste à faire.
- **Pièges du jour** : dans les dialogues à deux boutons du jeu, « Yes » n'est pas à l'indice 0 de la hiérarchie :
  le cliquer par son libellé ; `Dialog.Ok(texte, action)` lance l'action à **toute** fermeture du dialogue ; des
  objets du même genre s'empilent : compter avec `Sum(t => t.Num)` ; un Python en ligne dans l'outil Bash
  transforme `\\n` en vrai retour à la ligne : écrire un fichier script ; `run_short.sh` et `run_all.sh` laissent
  leurs processus bash, python et Elin vivants quand la tâche de fond est arrêtée : les fermer par numéro de
  processus ; `Player.log` et `_shots/elin2-player.log` sont écrasés par le test suivant.
- **Corrections de lignes périmées** : le message de mot de passe faux est **fait** (pas « en cours ») ; la page
  GitHub compte **neuf** anciennes préversions (0.26.388, .385, .382, .375, .366, .362, .349, .337, .309), pas sept
  ni huit comme dit plus haut (section de 17h25).
- **État de la machine à la passation** : le jeu a la version **publiée 0.26.390** (dossier `Mod_ElinTogether` venu de
  `dev/_release/ElinTogether-independance-0.26.390.zip`), pour que l'utilisateur joue avec son ami : lancer
  `dev/build.ps1` avant tout test. Avec elle, « Join by address » ne marche que pour le mode avec Elin ; contournement
  pour le mode sans Elin : « Client Settings », champ « Depot » = `192.168.1.28:55557`, puis « Lobby », prendre le
  monde. Son logiciel serveur est dans `Documents\ElinTogether-independance\` (0.26.390, en français), son dossier de
  monde dans `Documents\ElinTogetherServer` (vieux monde `world.zip`, sauvegarde du nuage `world_3`).
- **Idées notées, pas commencées** : le deuxième joueur rejoint l'hébergeur tout seul depuis « Join by address » (le
  serveur donnerait l'identifiant Steam de l'hébergeur ; il faut deux comptes Steam pour tester) ; chiffrement
  (TLS) du mot de passe du dépôt ; journal visible dans le logiciel.
- **À faire, dans cet ordre** : (1) lire `dev/_shots/depot_suite-srv4.log` ; (2) passe large sur le code final :
  `bash _tools/run_all.sh <nom> travel_suite companion_suite server_suite` puis
  `bash _tools/run_short.sh <nom> depot_suite quest_suite chara_suite parity_suite trade_suite build_suite player_suite instance_suite leave_suite transfer_suite death_suite sleep_suite guest_suite recruit_suite compat_suite import_suite time_suite world_suite move_suite`
  (deux fenêtres, PC libre, 1 à 2 heures ; pas de `trio_suite`, ni shared/economy/combat/party) ; (3) essayer à la
  main les boutons du logiciel (Browse…, Put this save on the server, les trois confirmations, Start/Stop en mode
  avec Elin, le message d'erreur) ; (4) publier une nouvelle version (`make_release.ps1`, `publish_release.py`) et
  la mettre dans le jeu ; (5) sa soirée : deuxième joueur par Steam, hébergeur qui part, mode avec Elin entre deux
  PC, Internet. Décisions à lui, à demander : relais sans coupure, joueur qui meurt sur la carte de l'host et
  connexion qui tombe, six inégalités (`PLAN_egalite_invites.md` : M3, M5, M9, L1, L7, M13), plan B retour de
  l'host, profil de mods, touche « signaler un problème », bot de soirée, faux réseau lent, retrait des neuf anciennes
  versions de GitHub. Question ouverte : quel mod fournit `dmp_quest_*`.
- **19h20** : `depot_suite` avec `DEPOT_SERVER=1` relancé avec le compte corrigé (objets empilés) : **20/20**. Le point (1) ci-dessus est fait. Version publiée 0.26.390 remise dans le jeu de cette machine avant la passation.


### Passe large sur le code final, boutons du logiciel, version 0.26.399 (2026-10-04, 19h30 → 22h) — reprendre ici

- **Début** : `git pull` (à jour), `dev/build.ps1`, `depot_proto_test.py` 11/11. `dev/_shots/depot_suite-srv4.log`
  lu : 20/20.
- **Outil `codebase-memory` (MCP)** : présent. Le mod était déjà indexé (projet
  `C-Users-steamdeckwin-Documents-ElinMods-ElinTogether-ElinTogether`). Le code décompilé
  `Documents\ElinMods\_decomp` a été indexé (projet `C-Users-steamdeckwin-Documents-ElinMods-_decomp`, 54 391
  nœuds ; 4 fichiers lus en partie : PartialMap.cs, PartialMapMenu.cs, SerializedCards.cs, UIScreenshot.cs). Il a
  servi à trouver `Application_quitting` dans Heathen en une seule requête. `gh` (GitHub CLI) n'est pas installé
  sur cette machine ; aucune issue ni PR ouverte sur le fork (vu par l'API publique).
- **Deux consignes qui se croisaient** : l'utilisateur a collé un second message « traiter le backlog en
  autonomie » (une issue = une branche `fix/` = une PR, pas de release). On lui a demandé lequel suivre : il a
  répondu « Liste HANDOFF, comme avant » (donc branche `feat/independent-travel`, publication comprise). Il a aussi
  dit oui pour ouvrir deux fenêtres alors que `idle.ps1` donnait 0 s (il se servait du PC).
- **Passe large sur le code final** (commit `2dba2fd`), journaux `dev/_shots/<suite>-final.log` : 22 suites, 19
  vertes au premier passage. travel 54/54, companion 28/28, server 8/9, depot (mode dossier) 13/13, quest 59/59,
  chara 11/11, parity 15/15, trade 30/30, build 19/19, player 38/38, instance 32/32, leave 12/13, transfer 9/9,
  death 11/11, sleep 32/32, guest 216/216, recruit 45/45, compat 5/5, import 25/25, time 11/12, world 9/9, move
  16/16. **Non rejouées** : `trio_suite` et shared/economy/combat/party (trois ou quatre fenêtres).
- **Les trois échecs** :
  - `server_suite` : `InvalidOperationException: Steamworks is not initialized.` dans le `Player.log` du serveur, à
    la fermeture, après la sauvegarde. Pile : `Steamworks.SteamInput.Shutdown` ←
    `HeathenEngineering...API.Input.Client.Shutdown` ← `API.App.Application_quitting` ←
    `Application.Internal_ApplicationQuit`. C'est le jeu lui-même (sa bibliothèque Heathen ferme Steam Input après
    Steam), **pas le mod** ; déjà vu le 2026-10-01 (`night-quest1.log`, clients 2 et 3). Revenu au 2e passage (8/9).
    Le compteur d'exceptions des suites (`scan_logs` dans `dev/_tools/travel_suite.py`) ignore maintenant cette
    ligne : 9/9 (`server_suite-final3.log`). Commit `7a4c2d1`.
  - `leave_suite` : « l'host, lui, est ailleurs sur la carte (a 1 cases) » : l'host est revenu à 1 case de l'invité
    au lieu d'être loin ; l'invité, lui, était bien resté à sa place. Rejouée : 13/13 (20 cases). **Cause non
    établie**, test noté fragile.
  - `time_suite` W3 : « les heures sont passées chez l'host (son personnage a plus faim) » : faim 31 → 31 après le
    saut de 5 heures (la date, elle, avait bien sauté de +300 min). Rejouée : 12/12 (31 → 32). La marge du test est
    d'un seul point et la faim est lue tout de suite après le saut : test noté fragile, **cause non établie** (pas
    exclu : les heures appliquées chez l'host avec un petit retard).
- **Boutons du logiciel serveur, essayés par un test** : nouveau `dev/_tools/server_ui_test.ps1` (UI Automation de
  Windows + clics postés aux vrais contrôles, lit le texte des boîtes).
  - `-Part depot` (dossier de test `%TEMP%\ets-ui-depot`, port 55558, jamais le dossier
    `Documents\ElinTogetherServer` de l'utilisateur) : **15/15**. Lancement « Running » sans monde ; « Put this save
    on the server » sur un serveur vide (boîte « This save is now the world of the server. », `world.zip` créé) ;
    remplacement : boîte « The server already holds a world. Replace it… », No ne change rien, Yes garde l'ancien
    en `replaced-*.zip` ; pendant qu'un joueur héberge (TAKE envoyé par le protocole) : la liste le montre, Stop et
    la croix de la fenêtre demandent (« Tester is hosting the world right now… »), No laisse tout en place, Yes
    arrête ; port déjà pris : boîte « Port 55558 is already in use on this PC. » et le logiciel reste Stopped ;
    Start avec port libre : Running, le monde est toujours là ; « Browse… » ouvre le choix de dossier (annulé) ;
    arrêté puis fermé : se ferme sans question.
  - `-Part elin` : **6/6**. Mode With Elin, `world_lab`, case « No game window » cochée, Start → « Starting… » →
    « Running » (date du monde affichée, un Elin sans fenêtre) ; fermer la fenêtre demande « The server is
    running. Stop it (it saves first)? » (No : toujours Running) ; Stop → « Stopping: saving… » → Stopped, plus
    d'Elin.
  - **Défaut trouvé et corrigé** : la boîte « port déjà pris » ajoutait le texte de Windows en français. Maintenant
    tout est en anglais : « Port N is already in use on this PC. / Close the other program that uses it, or the
    other Elin Together Server. » (sur deux lignes). Commit `3c6ca9c` (avec le test et le nouvel exe, 27 136
    octets).
  - Reste dans la langue de Windows (pas modifiable simplement) : les boutons Oui/Non des boîtes et la fenêtre de
    choix de dossier. Si `Depot.Import` échoue sur une erreur système, son texte vient aussi de Windows.
  - **Pas joué** : choisir vraiment un dossier dans « Browse… » ; le message « The server could not start: … »
    (toujours aucune sauvegarde sans base sous la main).
  - **Pièges du script** : en PowerShell `$T` et `$t` sont la même variable ; `return` dans `ForEach-Object` ne
    sort pas de la fonction ; les contrôles WinForms sont vus comme `ControlType.Pane` (filtrer par ClassName
    `*BUTTON*`, `*COMBOBOX*`, `*LISTBOX*`), ceux des boîtes par ClassName `Button` ; `InvokePattern.Invoke`
    bloquerait sur une boîte modale, d'où `PostMessage BM_CLICK`.
- **Version 0.26.399 publiée** (~21h50) : `make_release.ps1` sur `3c6ca9c`, zip 1 122 367 octets, préversion
  `independance-0.26.399` (https://github.com/devmarcpro/elin-together/releases/tag/independance-0.26.399),
  fichier public identique (SHA-256 `7b6bb319…284645`), copie
  `dev/_release/ElinTogether-independance-0.26.399.zip`. Build Release lancé une fois : « Loading [Elin Together
  0.26.399] », 0 exception, fermé par numéro de processus. **Le jeu de cette machine a la version publiée
  0.26.399** (avant de reprendre des tests : `dev/build.ps1`). Elle ne se connecte pas à la 0.26.390 : l'ami doit
  installer le même zip. Le logiciel serveur de l'utilisateur dans `Documents\ElinTogether-independance\` est
  encore celui de la 0.26.390 (en français) : il doit le remplacer par celui du nouveau zip (pas fait à sa place).
  Dix anciennes préversions sont maintenant sur la page (0.26.390 s'ajoute aux neuf) : ne rien retirer sans son
  accord.
- **Question de l'utilisateur : serveur sur un NAS Synology ?** Réponse donnée : oui pour le mode sans Elin, de deux
  façons. (a) Tout de suite, sans rien écrire : un dossier partagé du NAS comme dépôt (le réglage « Depot » du jeu
  accepte un chemin de dossier, mode dossier testé par `depot_suite` 13/13) ; marche sur le réseau local ou par un
  réseau privé (Tailscale…), pas d'adresse à taper dans « Join by address ». (b) À écrire : le logiciel est un
  programme Windows (.NET Framework, fenêtre) ; il faudrait une petite version sans fenêtre du même protocole
  pour le NAS (un script Python d'environ 150 lignes, ou Docker), testable par `depot_proto_test.py`. **Idée
  notée, pas commencée, à lui demander.** Le mode avec Elin ne peut pas tourner sur un NAS (il faut Elin, Steam et
  Windows).
- **Pas testé** (à dire tel quel) : les deux tests fragiles ci-dessus (causes non établies) ; « Browse… » avec un
  vrai choix de dossier ; « The server could not start: … » ; `trio_suite` et shared/economy/combat/party sur le
  code final ; tout ce que l'utilisateur doit jouer lui-même (deuxième joueur par Steam, hébergeur qui part, mode
  avec Elin entre deux PC, Internet avec mot de passe).
- **À faire ensuite** : voir `dev/HANDOFF.md` (état au 22h). En tête : sa soirée d'essai réelle avec la 0.26.399.

### Points restants traités en autonomie, décisions du conseil (2026-10-04, nuit) — reprendre ici

- **Consigne** : l'utilisateur a donné la liste des points restants à traiter du début à la fin sans s'arrêter ; chaque
  décision de conception est tranchée par le skill `llm-council` (5 avis, 5 relectures, un président ; avis et
  relectures en `sonnet`). Critères, dans l'ordre : l'invité obtient ce qu'un solo obtiendrait ; pas de duplication ni
  de perte ; le plus petit changement ; aucun risque pour les sauvegardes. Branche `fix/points-restants`, un commit
  par point.
- **Conseil 1, « qui reçoit quoi »** (faits lus dans le code par trois agents avant le conseil) :
  - *Cadeaux du dieu (M3)* — question : deux joueurs du même dieu, qui reçoit le familier et l'artefact ? Verdict :
    **rang de cadeau par joueur**, sans case ; l'host exécute le cadeau pour l'invité en prêtant au rang du monde,
    le temps de l'appel, un entier rangé sur le personnage (`try/finally`), la tentative chez l'invité est coupée.
    Écarté : « premier arrivé » (3 avis sur 5, mais il prive l'invité si l'host a déjà prié ce dieu), ne rien faire.
  - *Prime de la guilde des guerriers (L7)* — verdict unanime : **au joueur derrière le tueur** (l'invité, ou le
    maître du compagnon), repli sur l'host si introuvable. Écarté : partage, ne rien faire.
  - *Mort (L1)* — verdict : **même pénalité que le solo pour un invité sur la carte de l'host**, sans case, lettre
    de testament comprise, appliquée une fois, chez l'host. Écarté : ne rien changer, une case d'option. Limite
    acceptée : l'or tombé au sol peut être ramassé par un autre joueur.
  - *Carte au trésor (M9)* — verdict unanime : **l'host cherche la carte dans le sac de celui qui creuse**. Écarté :
    exécuter toute la fin du creusage « à la place du joueur » (recette tirée deux fois), ne rien faire.
- **Conseil 2, « tirages faits deux fois »** :
  - *Pièges (M5)* — verdict : **seul le jeu de l'invité tire** ; l'host saute le piège pour les personnages des
    invités (pas pour leurs compagnons), et une demande invité→host « condition de piège sur moi » (liste fermée :
    sommeil, cécité, paralysie) garde ces effets. L'expérience de désamorçage est gardée. Écarté : l'host seul tire
    (expérience et téléportation perdues), les deux jets gardés avec le déclenchement de l'invité coupé (messages
    contradictoires), une graine commune (non vérifiable).
  - *Grimoires (M13)* — verdict : **seul le jeu de l'invité tire** ; son annulation de lecture porte un motif
    « échec », l'host décompte alors une charge. Limite acceptée et écrite : sur un échec, la confusion et les
    monstres (28 % des échecs) n'arrivent pas. Écarté : l'host seul tire (l'invité échapperait au mana et à la
    téléportation, 72 % des échecs), le saut seul (lectures ratées qui n'usent pas le livre).
- **Vérification des autres points de la liste (agent, lecture seule, rien joué)** : réels : M11 bénédiction, L4
  puits, L5 tickets de meuble, L6 punition en quittant son dieu, seringues, stéthoscope (charges), laisse et
  consigne, appel à l'aide, karma sur la carte d'un invité, autel de l'invention (une recette différente par jeu),
  mutation en double (seulement avec un équipement d'éther). Déjà corrigés : source chaude (`a9fe6ee`, reste : le
  groupe), teinture (`88f1241`). Faux : « clé » (aucun objet de ce genre), affinité de la tonte et de l'abattage
  (elle arrive par le jeu de l'invité ; à confirmer par un test). Trouvé en passant : quand un invité abat un
  animal, c'est l'host qui perd de l'endurance.
