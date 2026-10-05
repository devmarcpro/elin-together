# Passation — ElinTogether « indépendance », état au 2026-10-05, 19h30 (haut du fichier ; le reste date de 14h15 à 17h)

À lire en premier par la session suivante. Détail daté : fin de `MODLOG.md` (« Étape D suite, Elin 23.352 »).
Mode d'emploi : `DOCUMENTATION.md`. Règles : `../CLAUDE.md`. Message de départ : `PROMPT_reprise.md`.

## État à 21h30 (le plus récent : lire ceci d'abord ; il remplace « État à l'arrêt de 20h »)

- **Publiée : 0.26.463.** Arbre propre, tout commité et poussé. Le jeu de cette machine a le build de test (Debug).
- **Base gérée par un invité : commitée (`23041ef`).** Le rouge (servante retirée par l'invité) venait de la fenêtre des
  habitants de l'invité, mal redessinée à la réponse de l'host (tous les onglets listés dans la même liste : la ligne
  cachée, le clic suivant redevenait celui du jeu). `base_suite` : B1 à B11 verts ; B12 vert au passage d'avant (le
  dernier passage s'est arrêté en B12 sur un manque de mémoire du PC). **Piège trouvé** : `send_raw` de `base_suite`
  n'envoyait rien (`Delta` est un champ, pas une propriété) : les trois « l'host refuse quand même » étaient de faux
  verts ; réparé, avec un témoin (case décochée, le même envoi passe).
- **Duels, étapes 2 à 4 : commités (`e77ea83`).** Menu « Challenge to a duel », boîte oui/non, compte à rebours, duel
  sur place, personne ne meurt, les deux soignés ; case host `Duels` (règle 15, cochée) ; deltas 837, 838 (prochain :
  839). `duel_suite` 90/91 puis D3 seul 13/13 (le rouge était le test). Pas faits : arène, pari, bouton Abandonner.
  Pas joués : deux PC, sorts et flèches, trois joueurs.
- **Piège** : `build.ps1` lancé tout de suite après la fermeture du jeu peut ne rien installer (DLL encore tenue) sans
  le dire dans un `grep` : attendre quelques secondes et lire « 0 Erreur(s) ».
- **Le PC était plein (300 Mo libres, un autre jeu ouvert)** : pas de passe large ce soir.
- **À faire ensuite, dans l'ordre** : 1) dépôt : l'invité qui reprend le monde doit jouer SON personnage (`depot_suite`
  P1 rouge) ; 2) dépôt GitHub : fermer le jeu pendant un envoi (G4) ; 3) conseil 6 : copie du monde par Steam ;
  4) passe large (`run_short.sh` + `travel_suite`), PC libre, puis proposer une 0.26.49x ; 5) reste de la chasse 2.

## État à l'arrêt de 20h (dépassé par 21h30)

- **Publiée : 0.26.463** (Elin EA 23.352). Depuis : tout est commité et poussé jusqu'à `b7b8cc5` (mode construction de l'invité
  complet, terrain, zones, coffres, autel, résurrection, Kettle, outils, pas de mort entre joueurs, dépôt GitHub, docs).
- **NON COMMITÉ dans l'arbre de travail (ne pas l'écraser : `git status`, `git diff`)** : la base gérée par un invité
  (conseil 7 : servante, type / réserve / rappel / renvoi d'un résident, abandon et acte refusés à l'invité, case
  `HostManagesBase` clé 14, textes), avec les corrections de la relecture ; `dev/_tools/depot_suite.py` (étape P1). Ça
  compile et c'est INSTALLÉ dans le jeu (build Debug). Preuve rouge faite sur l'ancien build ; **vert pas encore lu**.
- **Lus à 20h20** : `travel_suite` **54/54** (le S15 rouge d'avant était un tirage) ; `base_suite` **176/177** sur la base
  gérée par un invité, un seul rouge : « l'invité retire la servante du même clic (réel) : host 508, invité 0 » (le
  retrait de la servante par l'invité n'arrive pas chez l'host : à corriger, puis commiter la base) ; `depot_suite`
  P1 (`_shots/depot-p1.log`) : **l'invité qui reprend le monde du dépôt joue le personnage de l'HOST** (Josdear, uid 1,
  son or, son sac), pas le sien (uid 469, resté sur la carte comme un personnage ordinaire) : l'angle mort du conseil 6
  est confirmé ; c'est la première chose à régler avant la copie du monde par Steam, et cela vaut aussi pour le dépôt
  GitHub et le dépôt dossier d'aujourd'hui.
- **Duels, étapes 2 à 4 : écrits, pas joués.** Patch `_shots/duels_2_4.patch` (compile ; fait sur le commit `b7b8cc5`, à
  appliquer avec `git apply --3way` APRÈS avoir commité la base), ses 12 textes dans `_shots/duels_2_4.textes.md`. Puis
  relecture, rouge, vert (`duel_suite.py` D1 à D6).
- **À faire ensuite, dans l'ordre** : 1) lire les trois journaux, corriger, commiter la base (un commit), pousser ;
  2) S15 du voyage ; 3) duels 2-4 (appliquer le patch, relecture, rouge puis vert) ; 4) dépôt GitHub : fermer le jeu
  pendant un envoi (G4 rouge) ; 5) conseil 6 : copie du monde chez chaque joueur par Steam (selon P1) ; 6) passe large
  (`run_short.sh` + `travel_suite`) puis proposer une 0.26.49x à l'utilisateur ; 7) reste de la deuxième chasse.
- **Consigne de l'utilisateur (20h)** : effort faible, moins de jetons : réponses courtes, peu d'agents.
- Ses dépôts GitHub sont tous privés sauf `elin-together` (fait à sa demande) ; dépôt d'essai `elin-together-monde-essai`.

## État à 19h30 (le plus récent : lire ceci d'abord ; tout le reste du fichier date de 14h15 à 17h et est marqué)

Fait d'après `git log 895d5b0..HEAD` et `git status` à 19h30. Ce qui n'est pas joué est écrit « pas joué ».

- **Version publiée : 0.26.463** (2026-10-05, 15h35, commit `895d5b0`, Elin EA 23.352,
  https://github.com/devmarcpro/elin-together/releases/tag/independance-0.26.463). **Rien de ce qui suit n'est dedans.**
  Le jeu de cette machine a un build de TEST plus récent : avant de jouer avec quelqu'un, `Installer.bat` du zip publié.
- **Branches** : `fix/points-restants` (courante) et `feat/independent-travel` sont toutes deux à `1d698a5`, qui est
  aussi `origin/feat/independent-travel` : **tout ce qui est commité est poussé**. 20 commits depuis `895d5b0`.
- **Pas commité (copie de travail à 19h30, 20 fichiers en index + 2 non indexés)** : la **base gérée par un invité**
  (conseil 7) : servante, type de résident, réserve, rappel, renvoi (`BaseRequestKind` `Maid`, `MemberType`, `Reserve`,
  `Recruit`, `Banish`, `RemoteResidentPatch.cs` nouveau), case `HostManagesBase` (règle de session 14, « seul l'host gère
  la base », décochée), `base_suite.py` agrandie, textes (`emp_localization.xlsx`, `SourceLocalization.json`). Écrit,
  **en test, pas joué à ma connaissance** : ne pas le commiter avant un test rouge puis vert. Je n'ai pas vérifié si R6
  (acte de propriété) et « abandon refusé à l'invité » y sont.
- **Fait, testé, poussé depuis la 0.26.463** (un test rouge vu d'abord quand le message du commit le dit) :

| Point | Commit | Test |
|---|---|---|
| Prière sans dieu non soignée ; jours et heures de l'invité sur la carte de l'host (aucun crochet d'heure ou de jour ne tournait en jeu normal) | `194c6d7` | `hunt2_suite` E4, E5, 29/29 |
| Prix d'expédition lu avec le dieu du joueur | `445fa5e` | **pas joué** |
| Carte à gratter du casino qui arrive à l'invité | `3459019` | **pas joué** |
| Mode construction de l'invité refusé avec un message avant de payer | `99c7353` | `build2_suite` G1 |
| `together_suite` T12 attend les récoltes chez l'invité (le rouge était le test) | `6b62659` | T12, 20/20 |
| Terrain qui suit : l'état de chaque case changée est envoyé par celui qui simule (`TileStateDelta`) | `1a25661` | `build2_suite` C3, C4 |
| Réglages de coffre de la base (priorité, pas de pourri, catégories, filtre, drapeaux, distribution), deux sens | `57d5d3e` | `setting_suite` S7, 35/35 |
| Duel d'autel : même résultat dans tous les jeux, artefact reforgé à côté de celui qui offre | `915e6dd` | `hunt2_suite` E6, 58/58 |
| **Mode construction de l'invité** (menu, miner, creuser, couper ; case `GuestBuild`, cochée) : `AgentTaskDelta` | `b2a6f16` | `build2_suite` 28/28 ; `build_suite` 19/19 |
| Outils et fouets (clé à molette, marque écolo, brosse, marteau, fouets) agissent sur le monde de l'host | `1a89eed` | `unplayed_suite` U8, U9, 26/26 |
| Résurrection d'un compagnon chez le barman (`CharaReviveRequestDelta`) | `cd7d652` | `hunt2_suite` E7, 26/26 (parchemin et sort : pas joués) |
| Copie chez Kettle et grimoire chez Demitas (`CopyShopDelta`) | `fccee72` | `hunt2_suite` E8, 140/140 pour la suite |
| Zones de base, outil de terrain (hauteurs), cases changées hors `Map.Set*` (toit miné, mur tourné, pousse, labour, arrosage) | `d04114c` | `build2_suite` C7 à C9, 58/58 |
| Un joueur ne peut plus tuer un autre joueur (case `PlayerKill`, décochée) | `ca8d009` | `duel_suite` P1, 10/10, deux sens |
| **Dépôt GitHub privé** pour garder le monde (`github:proprietaire/depot`, une clé) | `1d698a5` | `depot_github_test` 66/66 (faux GitHub, hors jeu) ; `depot_github_real` 13/13 (vrai GitHub, hors jeu) ; `DEPOT_GITHUB=1 depot_suite` 31/33 (faux GitHub, en jeu) ; dossier 13/13 |

  Le reste des 20 commits est de la documentation (`8fe1a8a`, `e88a0e0`, `7013bc8`, `2e23dd5`, `fe34335`).
  **Rouge connu (G4)** : fermer le jeu pendant un envoi vers GitHub n'attend pas la fin de l'envoi ; le verrou expire
  alors de lui-même après 3 minutes. Pas corrigé.
- **Les quatre patchs d'agents de 17h sont tous commités** : `ligne8.patch` = `cd7d652`, `ligne11.patch` = `1a89eed`,
  `etape7.patch` = `d04114c`, `depot_github.patch` = `1d698a5` ; la copie chez Kettle (ligne 9) = `fccee72`.
- **Suites larges sur le build de test (`run_short.sh pub2`, lancé à 17h)** : leur résultat n'est pas écrit dans mes
  sources (journaux `_shots/*-pub2.log`) : **à relire avant de proposer une version**. `travel_suite` seule reste à lancer.
- **Conseils rendus** (verdicts complets dans `MODLOG.md`) :
  - **5, mode construction de l'invité** : fait jusqu'à l'étape 7 (zones, terrain). Restent refusés avec un message
    (d'après `b2a6f16`, pas revérifié) : plans de construction, mode toit (Alt).
  - **6, où vit le monde partagé** : une copie chez chaque joueur par Steam par défaut, GitHub en option, Workshop
    écarté. **Pas commencé.** Première chose à faire, sans code : avec le dépôt « dossier » et deux fenêtres, vérifier que
    l'invité qui prend le monde joue SON personnage et pas celui de l'host (`SaveDepot.Take` puis `Game.Load`). Puis les six
    étapes (`world.version`, envoi du zip, héberger la copie, retour de l'ami, divergence, avertissement).
  - **7, duels et base gérée par un invité** : duels, étape 1 faite (`ca8d009`), **étapes 2 à 7 à faire** (menu
    « Défier », duel sur place, départ et déconnexion, invité contre aventurier, arène, pari) ; base : écrite, en test,
    pas commitée (voir plus haut). Le verdict parle d'un « plancher à 1 PV » : le code laisse le joueur à **0** point de vie.
- **Numéros pris** : deltas jusqu'à **835** (832 `CharaReviveRequestDelta`, 833 `TerrainHeightDelta`, 834 `AreaStateDelta`,
  835 `CopyShopDelta`) ; arguments de tâche jusqu'à **227** ; règles de session jusqu'à la **clé 14** (12 `AllowGuestBuild`,
  13 `AllowPlayerKill`, 14 `HostManagesBase` pas commité). Prochain delta : 836.
- **Dépôt privé d'essai** pour le dépôt GitHub : `devmarcpro/elin-together-monde-essai` (créé avec l'accord de
  l'utilisateur ; `depot_github_real.py` y écrit `lock.json` et `world.zip`).
- **Deuxième chasse aux différences** (`PLAN_chasse_differences_2.md`) : lignes 1 à 11, 25, 26, 30, 33, 34 corrigées ;
  restent 12 à 24, 27 à 29, 31, 32, 35, 37 ; la 36 est « à juger » (chaque jeu lit le dieu de son joueur, comme un
  joueur solo).
- **À faire ensuite (19h30)** : (1) lire les résultats `pub2`, lancer `travel_suite` seule ; (2) finir la base gérée par
  un invité (test rouge puis vert, relecture par `relecteur-elintogether`, commit, pousser) ; (3) conseil 6 : la
  vérification sans code du personnage de l'invité, puis l'étape 1 ; (4) duels, étape 2 ; (5) lignes restantes de la
  chasse 2 ; (6) **proposer à l'utilisateur une version 0.26.47x** quand `pub2` et `travel_suite` sont verts (ne pas
  publier sans son accord) ; (7) pousser `feat/independent-travel` après chaque lot validé.

- **Suites larges `run_short.sh pub2`** (17h → 18h05, build du commit `b2a6f16`, jeu relancé entre chaque suite) : recruit 45/45,
  quest 59/59, instance 32/32, trade 122/122, base 63/63, version 8/8, leave 13/13, equal2 35/35, hunt 135/135, together
  131/131, sleep 32/32 ; unplayed 67/75 (les 8 rouges = U8, U9, alors pas encore corrigés : verts depuis) ; guest 314/317
  (G36, la laisse : rejouée seule 21/21, c'était un tirage). **`travel_suite` : pas rejouée depuis la 0.26.442.**
  Rien de large n'a été rejoué sur les commits d'après `b2a6f16` (résurrection, Kettle, outils, zones, terrain, pas de
  mort entre joueurs, dépôt GitHub) : seulement leurs propres suites.
- Conseil 6, « l'invité qui prend le monde joue-t-il SON personnage » : **pas vérifié**.
- Pas de mort entre joueurs : le coup laisse la victime à **0** point de vie (c'est ce que fait le jeu pour « ne peut pas
  mourir », `EvadeDeath`) ; le « 1 PV » du verdict était une image.
- `DEPOT_GITHUB=1 depot_suite` 31/33 : les deux rouges sont G4 et sa suite (la reprise du monde, bloquée 3 minutes par le
  verrou resté pris).

## Où on en est (texte de 14h15 : dépassé par « État à 19h30 » ; gardé pour mémoire)

- **Le dossier de travail est `G:\ElinMods`** (C: était plein). `C:\Users\steamdeckwin\Documents\ElinMods` n'est plus
  qu'une suite de raccourcis vers G:. Seul `_lab` (les copies de test du jeu, des liens vers le jeu Steam) est resté
  sur C:. **Ouvrir la session depuis `G:\ElinMods`** : ouverte depuis C:, l'application demande une autorisation à
  chaque écriture.
- **Dernière version publiée : 0.26.442** (2026-10-05 vers 9h25, préversion `independance-0.26.442`, commit `f096255`,
  https://github.com/devmarcpro/elin-together/releases/tag/independance-0.26.442). Depuis : une douzaine de commits non
  publiés en version (`git log --oneline 2935741..HEAD`), tous poussés sur GitHub.
- **ELIN S'EST MIS À JOUR : EA 23.351 → EA 23.352** (Steam, 2026-10-05, `version.json` dit canal « Stable »).
  Conséquences : (1) les copies de test `_lab` pointent vers les anciens fichiers, la connexion est refusée (« Version
  mismatch … game 0.23.351.2 -> 0.23.352.0 ») : **refaire `python _tools/make_lab.py Elin2 2` après chaque mise à jour
  d'Elin** (fait pour Elin2) ; (2) le mod compilé contre 23.352 se charge sans erreur ; rejoué sur 23.352 : hunt D1
  8/8, together 128/133 puis T1–T2 19/19 (les rouges étaient des tirages), unplayed 51/53 ; (3) le code décompilé
  `_decomp` est celui de 23.351 : **à refaire avant de s'y fier** pour ce qui a changé ; (4) **la version publiée
  0.26.442 a été compilée pour 23.351** : à republier, compilée sur 23.352, quand l'utilisateur le voudra.
- **Le jeu de cette machine** a le build de test (Debug ou Release selon le dernier `build.ps1`) : `dev/build.ps1` avant
  tout test ; `Installer.bat` du zip avant de jouer avec quelqu'un.
- **Fait à 14h15, commit `ee374b7` : la barrière de version.** L'utilisateur (14h) : « rendre les futures versions du
  mod compatibles avec les futures versions d'Elin sans forcément le mettre à jour, ne pas avoir de barrière ». Le mod
  s'accroche au jeu par les noms de ses fonctions, il n'y a pas de verrou de version ; la seule vraie barrière était le
  refus de connexion quand deux joueurs n'ont pas la même version d'Elin (quatre contrôles : clé de connexion Steam,
  filtre des salons, poignée de main côté client, côté host). Maintenant : seule la version du MOD doit être la même ;
  une version d'Elin différente = les joueurs sont prévenus ; une case côté host (onglet de configuration) redemande
  la même version d'Elin. Testé : `version_suite.py` 8/8 en connexion locale ; **le chemin par le salon Steam utilise
  le même contrôle, pas joué**. Fichiers : `Common/BuildVersionIntegrity.cs`, `Net/Client/ElinNetClientValidator.cs`,
  `Net/Host/ElinNetHostIntegrity.cs`, `Emp/EmpConfig.cs`, `Components/Tabs/TabServerConfiguration.cs`, les textes.
  La 0.26.442 publiée n'a pas ce changement : elle refusera toujours deux versions d'Elin différentes.
- **Branches** : `fix/points-restants` (branche courante, **la branche de travail**) et `feat/independent-travel` sont
  au **même commit** (`ee374b7`) ; `feat/independent-travel` est **poussée sur GitHub**.
  `wip/lots-non-compiles` est très en retard, gardée, pas supprimée.
- **Habitude demandée par l'utilisateur** : **pousser `feat/independent-travel` après chaque lot validé** (l'avancer sur
  `fix/points-restants` sans changer de branche courante, puis `git push origin feat/independent-travel`). **Publier
  une nouvelle version demande toujours son accord.** Ne jamais pousser sur `upstream`.
- Consignes de l'utilisateur (4 octobre au soir) : **aucune différence entre un joueur host et un joueur invité,
  tout doit être fluide, tous doivent pouvoir tout faire** ; travailler en continu sans s'arrêter ni demander
  d'autorisation (« j'autorise tout ») ; autant d'agents que nécessaire ; les décisions de conception sont tranchées
  par le skill `llm-council` (critères dans l'ordre : l'invité obtient ce qu'un solo obtiendrait ; pas de
  duplication ni de perte ; le plus petit changement ; aucun risque pour les sauvegardes).

## Fait et testé depuis la 0.26.442 (état de 14h15 ; la suite est dans « État à 19h30 »)

| Point | Commit | Test |
|---|---|---|
| Monture déjà prise refusée à un second cavalier | `31faaac` | `unplayed_suite` U6 vert |
| Notes, étiquettes de vente, lits (qui le tient, son type) : réglés par un joueur, vus par l'autre, deux sens | `eccc52a` | `setting_suite` S1–S3 |
| Recherche et compétences du foyer d'un invité : vraies demandes à l'host (il vérifie, paie une fois ; l'état de la base revient chez les joueurs) ; la recherche faite par l'host arrive chez l'invité | `b559952` | `base_suite` B1 20/20, B4 |
| « Ne pas vagabonder » propre à chaque joueur (en plus de « garder ses distances ») | `0b48902` | `hunt_suite` D14, 17/17 |
| Politiques de la base, deux sens | `e3b4de3` | `setting_suite` S4 (vraie fenêtre, clic), 20/20 |
| Nom de la base, de la faction, d'un téléporteur, deux sens | `ed99a6b` | `setting_suite` S5, S6, 25/25 (nom de faction non joué) |
| **Vrai défaut** : le don d'un objet pris dans une pile par un invité n'arrivait jamais chez l'host (objet non consommé, don sans effet) ; l'host annulait aussi le massage lancé par le jeu de l'invité | `7cd9db2` | `unplayed_suite` U1, U3, U5 (deux acheteurs : un exemplaire, un payeur), U6 |
| Quêtes à donjon à deux, sens invité : RÉCOLTE et MUSIQUE ouvertes (ce que livre l'un ou l'autre compte pour le preneur, même poids affiché, fouille des deux sacs, une récompense ; « tout livrer » passe par le même chemin qu'un dépôt) | `af18078` | `together_suite` T12, T13 |
| Deuxième chasse aux différences (37 lignes lues dans le code, rien de joué) | `e8dbc47` | |
| Barrière de version : seul le mod doit avoir la même version ; Elin différent = avertissement ; case de l'host pour le contrôle strict | `ee374b7` | `version_suite` 8/8 (connexion locale ; salon Steam non joué) |

Avant 9h30, déjà dans la 0.26.442 : mort après le jour 90, prime de guilde, cadeaux du dieu, pièges, grimoires,
bénédiction, autels, abattage, appel à l'aide, dieu quitté, source chaude, gestes tenus en main (G33–G39), quêtes à
donjon à deux dans les deux sens (subjuguer), chasse aux différences D1 à D14, échange plus strict, consigne « ne pas
s'éloigner » (détail : `MODLOG.md`).

Non-régression de la 0.26.442 (jeu relancé entre chaque suite) : equal2 35/35, together 107/107, death 11/11, parity
15/15, sleep 32/32, recruit 45/45, quest 59/59, instance 32/32, trade 122/122, hunt D1–D14, base 53/53, guest 317/317,
leave 13/13, travel 54/54, council vert. Sur 23.352, depuis : seulement hunt D1, together T1–T2 et unplayed.

Constats : les étapes de dialogue « acheter des plans » et « améliorer le foyer » n'existent dans aucun dialogue du jeu
installé ; un joueur peut « monter » un autre joueur sur la même case (comportement du mod d'origine, pas jugé).

**Pas joués par le banc** (`unplayed_suite`, seulement avec `--only`) : U2 bouton partagé d'un coffre (bouton
introuvable), U4 parchemin d'alias (aucun dans les données du jeu), U7 eau profonde (l'eau du banc n'étouffe personne).

## PAS JOUÉ (à dire tel quel ; liste de 14h15, complétée à 19h30 par les derniers points)

**Ajouté à 19h30 (depuis la 0.26.463) :**

- **Rien de ce qui est nouveau n'a été joué à deux PC** (mode construction, terrain, zones, coffres, résurrection, Kettle,
  outils, `PlayerKill`, dépôt GitHub).
- **Mode construction de l'invité** : pas joués : objet du stock ou du sac posé par le menu, pont, glisser sur plusieurs
  cases, creuser, mode rampe, la case `GuestBuild` décochée, une carte tenue par un invité. Plans de construction et mode
  toit : refusés avec un message (pas revérifié). Le banc choisit le mode et la recette par l'appel du bouton, pas à la souris.
- **Terrain** : pas couverts : récolte (seule la marque est jouée), sol tourné ; l'outil de terrain est joué par un coup,
  pas par un glisser bouton enfoncé.
- **Réglages de coffre** : la boîte du filtre, le collage et les boutons d'autodump ne sont pas joués.
- **Duel d'autel** : le glisser à la souris est remplacé par le dépôt ; un pair d'une ancienne version (graine absente)
  n'est pas essayé. **Résurrection** : parchemin et sort pas joués. **Outils et fouets** : tentes et nouvelle fiche des
  fouets « passe-temps » et « métier » chez l'invité pas couverts. **Prix d'expédition** (`445fa5e`) et **carte à gratter**
  (`3459019`) : jamais joués.
- **Un joueur ne tue pas un joueur** : saignement, poison, feu, condamnation à mort pas couverts ; sorts et projectiles
  pas joués ; le test utilise le coup de mêlée du jeu (Maj + clic).
- **Dépôt GitHub** : prouvé hors jeu (faux et vrai GitHub) et en jeu contre le faux GitHub ; **pas joué** : le vrai
  GitHub depuis le jeu (TLS de Mono, première demande d'environ 7 s, limite de débit), deux PC, la fermeture brutale du
  jeu pendant un envoi, un dépôt tout à fait vide sur le vrai GitHub, la clé expirée, le texte d'aide suivi avec une vraie
  clé, la croissance du dépôt (72 Mo par soirée : un calcul). **Rouge connu (G4)** : fermer le jeu pendant un envoi
  n'attend pas la fin ; le verrou expire après 3 minutes.
- **Base gérée par un invité** : écrite, en test, pas commitée ; rien de joué.
- Suites larges sur le build de test (`pub2`) : résultat non consigné ici. `shared_suite`, `trio_suite`,
  `companion_suite`, suites du serveur : non relancées.

**Liste de 14h15 (toujours vraie sauf ce qui est dit plus haut) :**

- **Corrigé dans le code, aucun test ne le prouve** : karma d'un visiteur chez un teneur de carte (`927f342`) ; noyade
  en eau profonde (`cf62040`, U7 saute) ; fenêtres d'alias, de retour du vide et de caisse de ferme (`2239dde`, U4
  saute) ; carte au trésor d'un invité sur la carte du monde (`4b45541`, `council_suite --only c6` à refaire) ; la
  retenue de « ne pas vagabonder » elle-même (un ennemi hors de vue du joueur) ; le nom de faction ; le score d'un
  concert de la quête de musique joué par l'host.
- **Deuxième chasse** : les 37 lignes de `PLAN_chasse_differences_2.md` sont lues dans le code, aucune n'est jouée.
- **Rien de ce qui est nouveau depuis la 0.26.442 n'a été joué à deux PC**, ni la 0.26.442 elle-même. Pour
  l'utilisateur : tout le point 1 de sa liste d'essais (deuxième joueur par Steam, hébergeur qui part, mode avec Elin
  entre deux PC, Internet avec mot de passe).
- Suites non relancées sur 23.352 : presque toutes (sauf hunt D1, together T1–T2, unplayed) ; `shared_suite`,
  `trio_suite` (trois fenêtres), `companion_suite` et les suites du serveur : non relancées depuis avant la 0.26.442.
  `run_short.sh` ne lance pas `travel_suite` ni `shared_suite`.
- Gestes tenus en main : pas comparés entre les deux jeux, les effets du puits sur le potentiel et les mutations ;
  pas de test d'un refus ; la portée de 2 cases ne regarde pas les murs.
- Quêtes à donjon à deux : les tests prennent la quête, tuent et sortent par les appels du jeu, pas par le dialogue ni
  en marchant ; pas de test pour « pas de boîte si l'autre a déjà une quête à donjon ou un échange » ; pas de test de
  déconnexion dans la zone ; trois joueurs pas essayé ; la boîte reste ouverte si la connexion tombe ; `instance_suite`
  et le bot attendent 15 s à chaque entrée. **La défense reste en solo pour l'invité** (cor, vagues et prime tenus par
  celui qui simule).
- Chasse 1, pas joués : le pinceau, le vol à la tire (l'host peut encore avancer vers la victime), investir dans une
  ville, les runes d'arme à distance, un refus de rune, le vrai glisser dans la fenêtre de rune, le parchemin de retour.
- Limites connues : sur une lecture ratée par un invité, ni confusion ni monstres ; un piège d'acide ou de malédiction
  n'abîme l'équipement que dans le jeu de l'invité ; un invité qui prie seul en voyage puis chez l'host pourrait
  recevoir un cadeau deux fois ; l'or perdu à la mort est ramassable par n'importe quel joueur ; les jours passés avec
  son dieu ne sont comptés que dans le jeu de l'invité ; la colère du dieu quitté est au tarif de base chez l'host.
  Réglages de la base encore locaux à l'écran de l'invité : servante, type et réserve d'un résident, réglages de coffre.

## À faire ensuite, dans l'ordre (liste de 14h15 : la version de 19h30 est dans le premier bloc ; ici les points 2 et 3 sont en partie faits)

1. **Barrière de version : la jouer.** Elle est faite et testée en local (`ee374b7`). Reste : la regarder en vrai
   (deux PC, deux versions d'Elin, par le salon Steam), vérifier le texte de l'avertissement et la case de l'host, et
   que la version du MOD, elle, refuse toujours clairement. Rien d'autre à écrire tant que ce n'est pas essayé.
2. **Republier une version compilée sur 23.352** (elle contiendra la barrière de version), **avec l'accord de
   l'utilisateur** : `dev\make_release.ps1`, note de version, README. Avant : relancer les suites larges sur 23.352
   (`run_short.sh`, puis `travel_suite` et `shared_suite` seules), refaire `_decomp` pour 23.352.
3. **Étape E = `PLAN_chasse_differences_2.md`**, en commençant par les lignes **hautes** : 1 (mode construction d'un
   invité : il paie, rien ne se construit chez l'host) et 2 (tailler un rondin à la hache : `TaskChopWoodArgs`). Puis
   les « sûr » : 6 (nourriture du sac de l'invité qui ne pourrit jamais), 25 (prière sans dieu), 26 (prix d'expédition),
   30 (carte à gratter du casino), 33 (jours, relance des quêtes), 36 (Mifu, Nefu, Aquli) ; puis 5 (prière qui ne
   soigne que l'invité), 8 (résurrection d'un compagnon), 11, 28, 29… Un test rouge puis vert par ligne, dans
   `hunt_suite.py` (prochain numéro : D15) ou `unplayed_suite.py`. Cocher l'état dans le plan.
4. **Ce qui reste du conseil 4** : servante, type et réserve d'un résident, réglages de coffre (ligne 7 de la deuxième
   chasse), **mesurer le rechargement de l'invité au retour de l'host** pendant la soirée d'essai (n'alléger qu'au-delà
   de 5 s).
5. **Défense à deux** (quêtes à donjon, sens invité) : le cor, les vagues et la prime sont tenus par celui qui simule ;
   gros, à décider par le conseil.
6. **Première chasse, ce qui reste** (`PLAN_chasse_differences.md`) : 8 (machine à gènes), 17 (habitants qui ne
   remarquent que l'host : conseil), 25 à 28, tombe d'épée (21). **Étape D, ce qui reste** : mutation en double avec un
   équipement d'éther ; serveur (relais sans coupure, personnage planté à la base, rôle du gardien du monde, mot de
   passe en clair).
7. Après chaque lot validé : pousser `feat/independent-travel`. Quand un ensemble est vert : passe large, puis proposer
   une nouvelle version à l'utilisateur (ne pas publier sans son accord).

## Liste d'essais de l'utilisateur (à deux vrais joueurs) — mise à jour 19h30 : points 10 à 18 ajoutés en fin de liste

Un seul point par ligne, dans cet ordre :

1. Un deuxième joueur qui rejoint par Steam ; l'hébergeur qui part ; le mode avec Elin entre deux PC ; Internet avec
   mot de passe.
2. Quêtes à donjon à deux, **dans les deux sens** : l'host prend une quête à donjon, l'invité répond Oui à la boîte,
   puis une fois Non ; l'invité prend une quête « subjuguer », « récolte » ou « musique », l'host répond Oui, puis une
   fois Non.
3. **Le temps de rechargement de l'invité quand l'host revient sur sa carte** (à chronométrer).
4. **La carte au trésor**, lue puis creusée par l'invité sur la carte du monde, avec l'host.
5. Tout ce qui est PAS JOUÉ : karma d'un visiteur chez un invité (les gardes le voient-ils ?), tri du sac (celui de
   l'autre ne change pas), « déjà vendu » à l'achat au même instant, message qui nomme l'host avant le rechargement,
   ticket d'hôtesse, fenêtres d'alias / retour du vide / caisse de ferme, eau profonde, vol à la tire, investir dans une
   ville, pinceau, runes d'arme à distance, concert d'une quête de musique.
6. L'invité règle la base : recherche et compétences du foyer (payé une fois, résultat visible chez l'host), politiques,
   lit, étiquette de vente, note, nom de la base et d'un téléporteur : l'autre joueur doit le voir.
7. Un échange : un objet équipé, un sac plein, un objet qu'on ne peut pas lâcher.
8. Un invité qui offre un objet pris dans une pile (le don arrive chez l'host) ; une monture déjà prise.
9. Deux joueurs sur une version d'Elin différente (barrière de version, `ee374b7`) : l'avertissement, la case de
   l'host, et un mod de version différente qui reste refusé.
10. **Construire dans la base de l'host** (invité) : un sol, un mur, un meuble neuf du menu, miner, couper ; l'or est
    pris une fois, ce qui est construit se voit chez l'host tout de suite. Puis l'inverse : l'host construit, l'invité
    le voit sans changer de carte. Ensuite, avec la case « Other players can use build mode » décochée : un message, rien
    n'est payé.
11. **Zones et outil de terrain** : l'invité dessine une zone de stockage, la renomme, l'efface ; il monte et baisse le
    terrain ; l'host voit la même chose, et dans l'autre sens.
12. **Réglages de coffre** : l'invité règle la priorité et « pas de pourri » d'un coffre de la base ; l'host les voit ; ses
    habitants rangent en en tenant compte.
13. **Résurrection d'un compagnon chez le barman** (invité) : l'or part une fois, le compagnon se relève à côté de
    l'invité, toujours à lui. Essayer aussi un parchemin (pas joué).
14. **Copie chez Kettle** (invité) : laisser un objet, voir la copie en vente, reprendre l'objet.
15. **Clé à molette** sur un coffre par l'invité (le coffre grandit chez l'host aussi), fouet-œuf sur un animal.
16. **Se frapper sans se tuer** : un joueur frappe l'autre jusqu'à 0 point de vie (Maj + clic) : personne ne meurt ; puis
    avec la case « les joueurs peuvent se tuer » cochée : la mort a lieu comme avant. Essayer aussi un sort et une flèche
    (pas joués).
17. **Dépôt GitHub avec une vraie clé** : créer un dépôt privé et la clé en suivant seulement l'aide du mod (onglet
    « Client Settings », quatre étapes), la donner à l'ami, prendre le monde, jouer, quitter, que l'ami reprenne. Vérifier
    que le jeu ne se fige pas pendant un envoi et que la clé n'est visible nulle part dans le jeu.
18. **Fermer le jeu pendant un envoi vers GitHub** (rouge connu G4) : voir si l'ami peut reprendre le monde tout de suite
    ou seulement après 3 minutes, et si la dernière sauvegarde est là.

## Questions qui restent pour l'utilisateur (de 14h15 ; voir aussi 19h30)

- Sa soirée d'essai (liste ci-dessus), et l'essai de la carte au trésor à deux.
- **Republier maintenant une version compilée sur 23.352 ?** (la 0.26.442 est compilée pour 23.351 ; elle marche
  sans doute, mais deux joueurs sur deux versions d'Elin se verraient refuser la connexion.)
- La barrière de version (`ee374b7`) : est-ce bien ce qu'il voulait (Elin différent = avertissement, case côté host
  pour le contrôle strict) ? Faut-il aussi laisser passer un mod d'une autre version ?
- Quel mod fournit les quêtes `dmp_quest_*`.

## Aide-mémoire

```
powershell -ExecutionPolicy Bypass -File dev\build.ps1
cd dev && set PYTHONPATH=_tools/pylib
python _tools/make_lab.py Elin2 2              # APRÈS CHAQUE MISE À JOUR D'ELIN (sinon connexion refusée)
python _tools/mp_test.py                       # host + 1 client ; peut rester à « connexion demandée » : relancer
python _tools/council_suite.py                 # les décisions du conseil (C6 : --only c6, fenêtres neuves)
python _tools/guest_suite.py --only g31,g32    # ou g33 à g39 (gestes tenus en main)
python _tools/equal2_suite.py                  # abattage, appel à l'aide, dieu quitté, source chaude
python _tools/together_suite.py                # quêtes à donjon à deux, les deux sens (T1 à T13, ~20 min)
python _tools/hunt_suite.py                    # chasse aux différences host / invité (D1 à D14 ; --only d1,d3)
python _tools/base_suite.py                    # base réglée par un invité (recherche, foyer : B1, B4…)
python _tools/setting_suite.py                 # notes, étiquettes, lits, politiques, noms (S1 à S6, 25 vérifs)
python _tools/unplayed_suite.py                # corrections jamais jouées (U1, U3, U5, U6 ; U2, U4, U7 : --only)
python _tools/trade_suite.py                   # échange, dont les refus R6 à R11
python _tools/version_suite.py                 # barrière de version (8 vérifications, connexion locale)
python _tools/hunt2_suite.py                   # deuxième chasse (E1 à E8 ; --only e7,e8)
python _tools/build2_suite.py                  # mode construction à deux, terrain, zones (G1, C1 à C9)
python _tools/duel_suite.py                    # un joueur ne tue pas l'autre (P1)
python _tools/depot_github_test.py             # dépôt GitHub contre le faux GitHub, sans le jeu (66 vérifications)
python _tools/depot_github_real.py proprietaire/depot   # contre le VRAI GitHub, dépôt privé d'essai seulement
DEPOT_GITHUB=1 python _tools/depot_suite.py    # en jeu contre le faux GitHub (~10 min ; 31/33, G4 rouge)
bash _tools/run_short.sh <nom> death_suite guest_suite parity_suite sleep_suite recruit_suite
git push origin feat/independent-travel        # après chaque lot validé, une fois la branche avancée
```

`run_short.sh <nom> suite1 suite2…` relance le jeu entre deux suites (journaux `_shots/<suite>-<nom>.log`) : c'est la
façon de faire la non-régression ; il ne sait pas lancer `travel_suite` ni `shared_suite` (elles lancent elles-mêmes le
jeu : les lancer seules, jeu fermé).

Pièges du 5 octobre (après-midi) : la panne de mémoire du banc (« OutOfMemoryException » du pont) revient après ~30
minutes de tests sur les mêmes fenêtres : relancer le jeu entre les grandes suites ; `mp_test.py` peut rester bloqué à
« connexion demandée » (relancer) ; le menu contextuel « buy » du jeu se referme sans souris dessus (le test le
reconstruit à l'identique) ; ne pas lancer `Stop-Process` par bash avec `\$_` (ça ne tue rien) : `taskkill /PID <n> /F`
depuis PowerShell ; un test qui dépend d'un tirage peut échouer une fois (monstre non tué en 40 coups, vérification
faite trop tôt : relancer avant de croire à un défaut) ; après une mise à jour d'Elin, `make_lab.py` d'abord.

Pièges du matin du 5 octobre : le « Yes. » des boîtes du jeu a un point (chercher par `StartsWith`) ; une fenêtre Elin
peut rester après `Stop-Process` : vérifier, puis `taskkill /PID <n> /F` ; D3 : la matière d'un seau est tirée au hasard
et le coffre ne prend que ce qui s'empile (le test copie les mêmes seaux).

Pièges de la nuit : ne pas compiler pendant qu'un agent écrit dans le même dossier (son travail à moitié
fini part dans la DLL : compiler depuis un worktree propre, `git worktree add`) ; une zone créée par l'host « sans
annonce » n'est jamais connue du client (« Remote zone does not exist… », puis « invalid zone ») ; `ModCurrency` chez
un client est une demande (sa bourse ne baisse qu'à la réponse de l'host : pas pour savoir « a-t-il payé ») ; ce que
fait l'host en appliquant le tick d'un autre joueur n'est pas envoyé (il faut `ElinDelta.Simulate()`) ; le banc sait
dérouler un vrai dialogue (`talk`, `pick`, `hang_up` dans `hunt_suite.py`, choix cliqués par leur texte anglais) ;
le gel occasionnel de la fenêtre host au chargement existe déjà (noté dans `mp_test.py`), ce n'est pas le code testé.
`new ActPray()` n'a pas d'identifiant (prendre `ACT.Create(6050)`) ; sur la carte du monde on
creuse sous ses pieds, `Teleport` n'y bouge pas un invité (`MoveImmediate` oui), y marcher peut déclencher une
rencontre ; quand l'host quitte une ville en premier, l'invité hérite de la carte ; un préfixe sur
`Chara.GetPietyValue` qui lit `IsPC` fige le chargement d'une sauvegarde (tester `core.IsGameStarted`) ; l'outil Bash
n'aime pas un texte long avec des apostrophes dans un « heredoc » : écrire le fichier avec l'outil d'écriture ;
`_lab` doit rester sur le même disque que le jeu (liens physiques). Un geste du banc qui prend un objet en main et
l'utilise dans la même commande allait plus vite qu'un joueur : c'était un vrai défaut du mod (l'objet tenu arrivait
chez l'host une image après la tâche, `CharaTaskRemoteEvent`). Dans un test, `check(cond=eventually(...),
label=f"...")` : Python évalue les arguments nommés dans l'ordre écrit, la condition (qui attend) avant le libellé ;
l'inverse affiche la valeur d'AVANT l'attente (« 0 -> 0 » marqué OK = faux vert). Le jeu n'appelle jamais à l'aide
dans une base du joueur (`Chara.DoHostileAction`, `!EClass._zone.IsPCFaction`) : tester ça à Vernis, pas à la
Prairie. Les anciens pièges sont dans `MODLOG.md`.


## Ajout de 14h35 (daté : étape E commencée ; lignes 1 à 11 faites depuis, voir 19h30)

- Trois lignes de la deuxième chasse corrigées et vertes (`python _tools/hunt2_suite.py`, 21/21) : rondin à la hache,
  prière qui soigne aussi les compagnons de l'invité, nourriture du sac de l'invité qui vieillit.
- Reprendre par la ligne 1 de `PLAN_chasse_differences_2.md` (mode construction d'un invité), test rouge d'abord ;
  détail et ordre dans la dernière entrée de `MODLOG.md`.
- À proposer à l'utilisateur : publier une version compilée sur Elin 23.352 (la 0.26.442 date de 23.351).

## Arrêt de 14h45 (daté ; demandé par l'utilisateur pour compacter la session ; la 0.26.463 est publiée depuis)

- Rien en cours : arbre propre, tout poussé, aucun Elin ouvert, aucun agent en route. Le jeu de cette machine contient
  un build de test (Debug) du dernier commit : avant de jouer avec quelqu'un, `Installer.bat` du zip publié.
- **L'utilisateur a dit oui (14h40) à une nouvelle version compilée sur Elin 23.352** : c'est la première chose à
  faire à la reprise ; la marche à suivre exacte est le point 2 de `PROMPT_reprise.md` (suites larges d'abord).
- Ensuite : ligne 1 de `PLAN_chasse_differences_2.md` (mode construction d'un invité). L'agent qui devait écrire les
  faits dans `dev/PLAN_construction_invite.md` a été arrêté avant la fin : le relancer.
- Pour reprendre : coller le contenu de `dev/PROMPT_reprise.md` (à jour à 14h45) dans une nouvelle session.

## Demandes de l'utilisateur du 5 octobre, 15h (daté ; conseils rendus et dépôt GitHub fait, voir 19h30)

- **Un invité doit pouvoir gérer la base de l'host** ; idée : un système de membres par base. Le mode construction de
  l'invité (conseil 5, `PLAN_construction_invite.md`) en est la première moitié ; reste : qui a le droit (membres), les
  réglages encore locaux (servante, résidents, coffres).
- **Duels entre joueurs**, comme contre les aventuriers : les deux joueurs envoyés sur une autre carte, combat à mort, la
  mort finit seulement le combat, aucune perte des deux côtés, pari possible. Lire d'abord l'arène du jeu (`bout_win`,
  `Zone_Arena`, section « Pas parcouru » de `PLAN_chasse_differences_2.md`).
- **Dépôt GitHub pour garder le monde** (demandé le 5 octobre, 16h45, accord donné : « ça serait top ») : troisième sorte de
  dépôt du mode « sans Elin », en plus du dossier partagé et du logiciel serveur. Un dépôt **à part, privé** (jamais le
  dépôt public du mod), et **le fonctionnement expliqué dans le mod lui-même** (textes d'aide dans l'onglet, 4 langues :
  créer le dépôt, inviter les joueurs, créer la clé d'accès, où la coller). Faits : `PLAN_depot_github.md` (agent lancé).
