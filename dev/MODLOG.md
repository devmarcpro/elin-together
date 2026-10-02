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

### À faire ensuite (ordre demandé par l'utilisateur)
1. Série de bots de 30 minutes : faite (voir plus haut). Zip : fait.
   **En cours, mis de côté à la demande de l'utilisateur (`git stash`, « en cours : retours des joueurs »)** :
   `PLAN_retours_joueurs.md`. Écrit, pas testé : état « posé » joint aux effets d'une pose
   (`CardSetPlacedStateEvent`), mur cassé par un monstre (`CharaDestroyPathDelta`, union 227), matériel du bot
   donné seulement à un joueur installé (`IsSettled`). Tests prêts : `build_suite.py` (B1–B5, B3 ; rouges
   attendus sur `d2ae52e` : B5 « roaming » et B3), `player_suite.py` F1 (à refaire : l'host arrête une tâche
   injectée quand le client se dit inactif, il faut partir du jeu du client).
2. Nouveau zip (`make_release.ps1`), puis remettre le build Debug.
3. Suite de `DOCUMENTATION.md` section 7. **Pas le « temps du monde commun » sans l'utilisateur.**
4. Demande de l'utilisateur (2026-10-02) : lire la page Workshop d'Elin Together et surtout ses commentaires
   (https://steamcommunity.com/sharedfiles/filedetails/?id=3773298709) pour des pistes d'amélioration, **après**
   le reste ; lui proposer la liste avant de coder.
