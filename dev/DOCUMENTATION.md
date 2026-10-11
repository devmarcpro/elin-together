# ElinTogether « indépendance » — documentation

Fork du mod multijoueur ElinTogether pour Elin. But : **en jeu, aucune différence entre l'host et les autres
joueurs**. Chacun va où il veut, avec ses compagnons, et le monde (quêtes, base, argent de la base) reste commun.

- Dépôt : https://github.com/devmarcpro/elin-together (public), branche `feat/independent-travel` (poussée après chaque
  lot validé ; on travaille sur `fix/points-restants`, au même commit). Le code du mod est dans `ElinTogether/`, tout
  ce qui sert à développer et tester dans `dev/` (ce dossier).
- Installer une nouvelle machine : `SETUP.md`. Consignes pour une session Claude : `CLAUDE.md` à la racine.
- Journal détaillé (pièges, essais, dates) : `MODLOG.md`. Ce document-ci dit ce qui existe et comment s'en servir.
- Les chemins `_tools/`, `_lab/`, `_shots/`, `_release/` de ce document sont relatifs à `dev/`. Le journal parle
  encore de `Documents\ElinMods\` : c'était leur place avant le 2026-10-02.
- État : 2026-10-06, 22h30. Dernière version publiée : **0.26.524** (commit `2c98607`, compilée pour Elin EA 23.352 Patch 1 ; elle remplace la
  0.26.510, qui reste en ligne). **La 0.26.524 est écrite, relue et compilée, mais JAMAIS JOUÉE, pas même par les suites** : voir `HANDOFF.md`
  (« État au 6 octobre, 22h30 »). Dossier de travail : `G:\ElinMods`.
- Complété le 6 octobre à 22h30 pour la 0.26.510 et la 0.26.524 : lignes « Depuis la 0.26.506 » du tableau de la section 1, cases de la
  section 2, bloc « Mise à jour du 2026-10-06, 22h30 » au début de la section 7. Ce qui est marqué « pas joué » n'a jamais tourné en jeu.
- Ce document a été complété à 19h30 pour tout ce qui est nouveau depuis la 0.26.463 : les lignes ajoutées sont dans
  les tableaux de la section 1, les options (section 2), le dépôt GitHub (sections 3 et 4), les suites (section 5), les
  limites (section 6) et le reste à faire (section 7). Les paragraphes plus anciens gardent leur date.

## 1. Ce que le fork apporte, vu du joueur

| Fonction | Ce que ça change | Vérifié par |
|---|---|---|
| Voyage indépendant | Un joueur part sur une autre carte sans l'host ; la carte et ce qu'il y fait sont conservés. | `travel_suite.py` |
| Points de sauvegarde et chat | En voyage, la progression est sauvée régulièrement ; le chat marche entre toutes les cartes. | `travel_suite.py` |
| Cartes partagées | Un joueur peut rejoindre un autre joueur sur sa carte, sans l'host. Si celui qui « tient » la carte part, un autre la reprend. | `shared_suite.py`, `trio_suite.py` |
| L'host ne traîne personne | Quand l'host change de carte, les joueurs restés sur l'ancienne y restent. | `leave_suite.py` |
| Compagnons | Les compagnons suivent le joueur qui les a recrutés, y compris en voyage. Limite d'alliés par joueur. | `companion_suite.py`, `party_suite.py` |
| Expédition par joueur (option) | Une seule caisse d'expédition ; l'argent de la vente va à celui qui a déposé l'objet. Le reste (rang de la base, total vendu) est commun. | `economy_suite.py` |
| Combat au rythme du joueur (option) | Un monstre agit au rythme du joueur qu'il combat, au lieu du rythme de l'host. | `combat_suite.py` |
| Quêtes aléatoires par joueur (option) | Les quêtes des habitants et des tableaux appartiennent à celui qui les prend : lui seul les voit, les rend, touche la récompense, la renommée et le karma. 5 quêtes par joueur. Elles le suivent en voyage et à la reconnexion. | `quest_suite.py` P1–P4, P11 |
| Quêtes communes | Les quêtes d'histoire sont dans un seul journal : n'importe qui les lance, les avance, les termine. Sans l'option ci-dessus, les quêtes aléatoires aussi, et la récompense va à celui qui rend la quête. | `quest_suite.py` |
| Quêtes d'histoire | Un joueur qui n'est pas l'host peut lancer et avancer une quête d'histoire. Ce que le dialogue offre lui revient, ce qu'il déclenche dans le monde se produit chez l'host. La mémoire de l'histoire (dialogues déjà vus, drapeaux, objets clés, dette) est commune. | `quest_suite.py` (voir limites) |
| Quêtes à donjon pour tous (avec les options « voyage » et « quêtes par joueur ») | Un joueur qui n'est pas l'host peut prendre une quête qui a sa propre zone (subjuguer, récolte, escorte…) : la zone est à lui, il y entre seul, et la quête se règle quand il en ressort. | `instance_suite.py` |
| Quêtes à donjon à deux, l'host a la quête (avec les options « voyage » et « quêtes par joueur », sans case à elle) | Quand l'host part en quête, une boîte Oui/Non s'ouvre chez l'invité (« X part en quête : l'accompagner ? La récompense revient à X », 15 s, sans réponse = non ; l'host voit le refus ; pas de boîte si l'invité a déjà une quête à donjon ou un échange). Oui : l'invité arrive dans la zone simulée par l'host. La récompense est à celui qui a pris la quête ; quand il sort, tout le monde sort ; l'accompagnant peut aussi rentrer seul en ville (pour une récolte, il est fouillé comme chez l'host : moitié des récoltes non livrées reprises, 1 de karma). L'host qui sort reprend bien la ville tenue par l'invité. | `together_suite.py` T1–T6 |
| Quêtes à donjon à deux, l'invité a la quête (mêmes options, sans case à elle ; `26756bf`) | Quand l'invité accepte une quête « subjuguer » et part, la demande de zone est retenue chez l'host, qui voit la boîte Oui/Non (15 s ; l'invité lit « on demande à X… »). Oui : l'host crée la zone et la simule, l'invité y est un client ordinaire, la quête reste à son journal (l'host la lit sans l'avoir au sien). Quand l'invité sort, tout le monde sort ; la récompense est donnée une fois, à l'invité. L'host peut rentrer seul : la zone passe à l'invité, qui finit seul. Non ou pas de réponse : comme avant, l'invité simule sa zone seul. La sauvegarde de l'host ne contient rien de la quête de l'invité. Subjuguer, puis (`af18078`) récolte et musique : ce que livre l'un ou l'autre compte pour le preneur (même poids affiché, fouille des deux sacs, une seule récompense ; le bouton « tout livrer » suit le même chemin qu'un dépôt). La défense reste en solo pour l'invité (cor, vagues et prime tenus par celui qui simule). | `together_suite.py` T7–T11 (107/107 avec T1–T6), T12 (récolte), T13 (musique) ; le score d'un concert joué par l'host n'est pas testé |
| Chasse aux différences host / invité (5 octobre, `PLAN_chasse_differences.md`) | Un invité sous 20 % de vie ne prend plus peur et peut frapper (`392266d`) ; le guérisseur payant le soigne vraiment, lui et ses compagnons (`3d27d3f`) ; le rangement automatique est propre à chaque joueur : celui de l'invité n'emporte plus les objets de l'host, celui de l'host ne ferme plus les fenêtres de l'invité (`f4c5b44`) ; radio, juke-box, liste de lecture, livres des résidents et de l'équipe, détecteur, roue, vue de carte, pinceau : la fenêtre ne s'ouvre que chez celui qui s'en sert (`ea93c88`) ; l'ecopo de la faucille va à l'invité qui fauche, et son vol à la tire ne coûte plus d'endurance à l'host (`f00f5a6`) ; investir dans une boutique ou une ville arrive chez l'host au lieu d'être payé pour rien (`f63a879`) ; la bénédiction des prêtresses atteint l'invité et ses compagnons (`9046034`) ; une recette lue par un joueur n'est apprise qu'une fois par l'autre (`15d6e05`) ; runes et prises : fenêtre chez l'utilisateur seul, rune posée et usée dans les deux jeux (`3ccad87`). Déjà bons : parchemin d'évacuation, carte au trésor lue. Ensuite (0.26.442) : le pied-de-biche d'un invité force aussi le coffre chez l'host (`fb7a507`, D13) ; sous l'eau profonde l'invité perd son souffle (`cf62040`), son ticket d'hôtesse masse l'invité (`ab73333`), ses fenêtres d'alias, de retour du vide et de caisse de ferme ne s'ouvrent plus chez l'host (`2239dde`) : **pas joués**. | `hunt_suite.py` D1–D14 (D12 saute : pas d'eau profonde sur la carte de test) |
| Gestes tenus en main d'un invité | Ticket de meuble, seringues (gène, sang, paradis, licorne), puits, stéthoscope, laisse : le geste est rejoué chez l'host, l'objet est dépensé des deux côtés. Au puits, le vœu est tiré dans le jeu de l'invité (1 chance sur 21 par gorgée), pas chez l'host. Autres corrections de la nuit du 5 octobre : un invité qui abat un animal ne fait plus perdre l'endurance de l'host ; un habitant ami frappé par un invité appelle ses voisins (dans une ville ; le jeu n'appelle jamais dans une base) ; quitter son dieu punit l'invité ; la source chaude profite à l'invité et à son compagnon, pas à l'host. | `guest_suite.py` G33–G39, `equal2_suite.py` |
| Base réglée par un invité (sans case) | Recherche et compétences du foyer : d'abord refusées avec un message (`06a0f94`), puis de vraies demandes à l'host (`b559952`) : il vérifie, paie une seule fois, l'état de la base revient chez tous les joueurs ; la recherche faite par l'host arrive chez l'invité. Notes, étiquettes de vente, lits (qui le tient, son type) et nom d'un téléporteur (`eccc52a`, `ed99a6b`), politiques de la base (`e3b4de3`), nom de la base et de la faction (`ed99a6b`) : réglés par un joueur, vus par l'autre, dans les deux sens. Les étapes « acheter des plans » et « améliorer le foyer » n'existent dans aucun dialogue du jeu installé (le foyer monte tout seul). Réglages de coffre : faits depuis (ligne « Réglages de coffre » plus bas). Servante, type et réserve d'un résident, rappel, renvoi : écrits, en test, **pas commités** (section 7). | `base_suite.py` B1 20/20, B4 ; `setting_suite.py` S1–S6, 25/25 (nom de faction non joué) |
| Consignes « ne pas s'éloigner » (`9155835`) et « ne pas vagabonder » (`0b48902`) | Ce sont les réglages du joueur du compagnon, pas ceux de l'host : le compagnon suit la case et les yeux de son maître. La retenue elle-même (un ennemi hors de vue du joueur) n'est pas jouée. | `hunt_suite.py` D14, 17/17 |
| Karma d'un visiteur (`927f342`) | Sur une carte tenue par un autre joueur que l'host, les gardes voient le karma d'un visiteur : il l'annonce au teneur de la carte, gardé en mémoire seulement, effacé à son départ. | pas joué |
| Messages d'achat et de retour (`211658e`) | Le second acheteur d'un même objet apprend qu'il est parti ; l'invité est prévenu de qui revient sur sa carte avant le rechargement de son écran. Tri du sac propre à chaque joueur (`5ffa169`) : seul le réglage partagé / personnel d'un conteneur de la carte voyage. | pas joués |
| Don d'un objet pris dans une pile, massage (`7cd9db2`) | Le don d'un objet pris dans une pile par un invité n'arrivait jamais chez l'host (l'objet n'était pas consommé, le don sans effet) : corrigé. L'host n'annule plus le massage lancé par le jeu de l'invité. Tests des corrections jamais jouées : tri du sac, deux acheteurs d'un même objet, monture déjà prise (refusée, `31faaac`), ticket d'hôtesse. | `unplayed_suite.py` U1, U3, U5, U6 (U2, U4, U7 : seulement avec `--only`, le banc ne les joue pas) |
| Échange entre joueurs (option) | Clic sur un autre joueur → « Échanger » : une fenêtre où chacun met des objets et de l'or, puis confirme. Rien ne change de mains tant que les deux n'ont pas confirmé ; s'éloigner annule. Depuis `9cd8062` : refus de ce que le jeu solo refuse de donner (objet qu'on ne peut pas lâcher, propriété d'un habitant, cadeau, objet lié), refus avant tout transfert si le sac de l'autre est plein, message qui explique pourquoi pour un objet équipé (pas de déséquipement automatique). | `trade_suite.py` (R6–R11, 122/122) |
| Choix du personnage (option) | À la connexion, le joueur choisit parmi ses personnages de cette partie ou en crée un nouveau. | `chara_suite.py` |
| Karma et crime par joueur (avec l'option « quêtes par joueur ») | Tuer un habitant, voler, creuser la rue : c'est le joueur qui l'a fait qui perd du karma, plus l'host ni les autres. Les gardes de l'host ne poursuivent que le joueur criminel. | `parity_suite.py` Y3–Y4 |
| Affinité et guildes communes | L'affinité d'un habitant est la même pour tous ; rejoindre une guilde ou y monter en grade vaut pour le groupe. | `parity_suite.py` |
| Mort en voyage | Le joueur choisit où revenir, et retrouve l'host s'il revient à la base. | vu une fois avec le bot |
| Déplacements fluides d'un invité (option) | Un invité marche et agit sur l'horloge de son propre jeu, comme l'host : ses pas ne dépendent plus du réseau ni d'un host qui rame. L'accéléré est partagé : quand un joueur accélère, tous ceux de la carte accélèrent. | `move_suite.py` V1–V3, V6 |
| Chacun marche comme en solo (option) | La durée d'un pas ne dépend plus de la vitesse des autres joueurs. En combat la vitesse compte toujours. | `move_suite.py` V4–V5 |
| Personnage d'une sauvegarde solo (option, décochée par défaut) | À la connexion : « un personnage d'une de mes sauvegardes », puis la liste des dernières sauvegardes. Il arrive avec ses caractéristiques, son apparence, son équipement, son sac, son or, sa renommée et son karma. Pas ses compagnons, sa base, ses quêtes ni sa banque. La sauvegarde est seulement lue. Un seul exemplaire par sauvegarde et par joueur. | `import_suite.py` |
| **Elin Together Server** (`ElinTogetherServer.exe`, 26 Ko, rien à installer) | Le logiciel serveur. Interface en anglais depuis le 2026-10-04. « Sans Elin » : il garde le monde et un vrai verrou, aucun jeu ne tourne ; le premier joueur prend le monde et l'héberge, chaque sauvegarde lui revient (le joueur tape l'adresse `adresse:55557` dans « Join by address » ; le réglage « Depot » se remplit tout seul, et sert encore pour un dossier partagé et pour le mot de passe). « Avec Elin sur ce PC » : il lance le jeu en serveur sans fenêtre ni affichage, montre l'état, les joueurs, la date du monde, la dernière sauvegarde, et l'arrête après une sauvegarde. Source : `dev/server/`. | `depot_suite.py` avec `DEPOT_SERVER=1`, `server_suite.py` |
| Serveur (comme un serveur Minecraft) | Un Elin que personne ne joue, lancé par `Serveur.bat` (ou `Elin.exe -empserver <sauvegarde>`, `cloud:<id>` pour une sauvegarde du nuage) : il charge le monde et ouvre la partie tout seul, sauvegarde toutes les cinq minutes tant que quelqu'un joue. Les joueurs le rejoignent par adresse : onglet Lobby, « Join by address », `adresse:55556`. | `server_suite.py` |
| Un seul bouton pour rejoindre : « Join by address » (depuis `018091d`) | Il marche avec les deux serveurs. Il demande d'abord à l'adresse si c'est Elin Together Server ; si oui, cette adresse devient le dépôt (le réglage « Depot » se remplit tout seul) et le joueur prend le monde et l'héberge, ou apprend qui l'héberge déjà ; sinon il rejoint un serveur de jeu comme avant. La saisie d'adresse cite les deux ports (55556 avec Elin, 55557 sans). Le jeu peut se figer jusqu'à 5 secondes si la machine à cette adresse laisse tomber la connexion sans rien répondre. Le texte `emp_ui_timeout` manquait dans toutes les langues (le jeu montrait la clé brute) : « The server does not answer. Check the address, the port and the mode of the server. » (EN/JP/CN). | `depot_suite.py` avec `DEPOT_SERVER=1` : 11/11 (3/4 rouge avant). Le texte du délai n'est pas testé : seul un build Release l'affiche. |
| Dépôt de sauvegarde (réglage « Depot folder », onglet Client Settings) | Un dossier que tout le groupe peut atteindre (partagé ou synchronisé) garde le monde. Écran titre, onglet Lobby : « Take the world from the depot and host it ». Le premier arrivé héberge, les autres le rejoignent, chaque sauvegarde retourne au dépôt, et quand il part un autre peut reprendre. « Put this save in the depot » y dépose une sauvegarde. | `depot_suite.py` |
| Une seule date, un seul monde (options) | Le temps passé par un joueur seul sur sa carte compte pour tous ; météo, impôts, salaires, colis et quêtes expirées n'arrivent qu'une fois. | `time_suite.py`, `world_suite.py` |
| Compagnons d'un invité, toutes façons de recruter | Dialogue d'un habitant, boule à monstre, monture, animal ou esclave acheté : le compagnon est à l'invité et le suit. | `recruit_suite.py` |
| **Depuis la 0.26.463 (5 octobre, 15h40 → 19h30)** : | | |
| Mode construction d'un invité (case `GuestBuild`, cochée par défaut) | Un invité construit dans la base comme l'host : sols, murs, meubles neufs du menu, objets du stock, miner, creuser, couper. Son jeu ne finit pas la tâche : il l'envoie (`AgentTaskDelta`, tâche `TaskBuildArgs`) à celui qui tient la carte, qui la fait avec l'invité à la place du joueur. L'or (10 par case) est pris une fois, les matériaux une fois (d'abord le sac de l'invité, puis le stock de la carte), la pierre minée va dans le sac de l'invité. Avant ce lot, l'invité payait 10 d'or par case pour rien et ses murs minés ne tombaient que chez lui : d'abord un message avant de payer (`99c7353`), puis la vraie fonction (`b2a6f16`). Mode toit (touche Alt) et plans de construction : encore refusés avec un message, avant de payer. Si la case est décochée (ou `HostManagesBase`, plus bas) : refus avec un message. **Pas joués** : objet du stock ou du sac posé par le menu, pont, glisser sur plusieurs cases, creuser, mode rampe, la case décochée, une carte tenue par un invité (l'host y est le « client »). | `build2_suite.py` G1, C1, C2, C5, C6 ; `build_suite.py` 19/19 |
| Le terrain suit entre les jeux (`TileStateDelta`, `TileStateDirectEvent`) | Celui qui simule la carte envoie, en fin d'image, l'état complet de chaque case dont le sol, le bloc (mur), l'objet de case, le pont, le toit ou la déco a changé (par morceaux de 2048 cases, avec l'identifiant de la zone). Ce que l'host construit en mode construction arrive chez l'invité tout de suite (avant : à sa prochaine entrée dans la zone). **Couvert aussi, hors des fonctions habituelles de la carte** (`d04114c`) : toit miné, mur tourné (touche R), pousse, récolte (la marque seulement), labour, arrosage. **Pas couvert** : voir section 6. | `build2_suite.py` C3, C4, C9 |
| Zones de base et outil de terrain (`AreaStateDelta`, `TerrainHeightDelta`) | Un invité dessine, renomme, règle l'accès et efface une zone de la base (stockage…) comme l'host, et utilise l'outil de terrain (monter, baisser) : les zones, leurs points et leurs réglages, et les hauteurs, sont les mêmes chez les deux. Piège trouvé par le test : comparer les zones par le JSON du jeu annonçait un « nouvel état » quatre fois par seconde (le jeu numérote ses objets à neuf à chaque appel) et défaisait le changement de l'autre joueur ; les zones sont comparées champ par champ (`AreaWatch.cs`). | `build2_suite.py` C7, C8 ; 58/58 pour la suite |
| Réglages de coffre (`57d5d3e`, `InvSaveDataDelta` étendu) | Priorité, « pas de nourriture pourrie », catégories, filtre, drapeaux, distribution : réglés par un joueur, vus par l'autre, dans les deux sens ; l'host relaie. Les habitants de l'host rangent donc avec ces réglages. Depuis le 2026-10-09 aussi ce qu'un joueur règle sur le coffre lui-même : nom, icône, taille, colonnes et couleur de la grille, tri (avant, un invité les perdait dès que le monde lui était renvoyé). Seule la place de la fenêtre à l'écran reste à chacun. Les réglages sont lus à chaque image tant que la fenêtre du coffre est ouverte (`InvSettingsWatch`), plus par le menu. Les sacs restent propres à chaque joueur. | `setting_suite.py` S7, 16/16 pour S7 seul |
| Duel d'autel (`915e6dd`, `RemoteAltarPatch.cs`) | Offrande sur l'autel d'un autre dieu : le duel de conversion donne le même résultat dans tous les jeux (avant, l'autel pouvait changer de dieu chez un joueur seulement) ; ce qu'il fait est dit aux invités ; un artefact « reforgé » tombe à côté de celui qui a offert, pas de l'host. (Ne pas confondre avec les duels entre joueurs, section 7.) | `hunt2_suite.py` E6, 58/58 |
| Prière sans dieu, heures et jours de l'invité (`194c6d7`) | Un invité sans dieu qui prie n'est plus soigné (comme l'host). Chez un invité sur la carte de l'host, les heures et les jours passent vraiment : compteur de jours, coût de relance des quêtes, prière du jour remise à zéro, crochets d'heure et de mois. **Trouvé en relisant, pas par un test** : aucun de ces crochets ne tournait en jeu normal (l'heure de l'host arrive minute par minute, `WorldDateAdvanceDelta` sortait quand le saut faisait moins de 2 minutes et comptait les jours en minutes). | `hunt2_suite.py` E4, E5 (29/29) |
| Résurrection d'un compagnon (`cd7d652`, `CharaReviveRequestDelta`) | Chez le barman, l'invité demande ; l'host vérifie, prend le prix une fois dans la bourse de l'invité, et le compagnon se relève à côté de l'invité, toujours à lui, dans son groupe (avant : l'invité payait, le compagnon restait mort). Parchemin et sort de résurrection rejoués chez l'host : le compagnon se relève par l'invité aussi, **pas joué**. | `hunt2_suite.py` E7, 26/26 |
| Copie chez Kettle, et grimoire chez Demitas (`fccee72`, `CopyShopDelta`) | Un invité peut laisser un objet à copier : le coffre de copie est fait par l'host et partagé, l'objet y est une fois chez les deux, la boutique vend sa copie, l'objet peut être repris (avant, le coffre ne vivait qu'une image chez l'invité). Un seul coffre par marchand pour tous les joueurs, comme le jeu. | `hunt2_suite.py` E8 (140/140 pour la suite) |
| Outils et fouets (`1a89eed`, `CardActReplayDelta`, `CardSettingDelta`) | Clé à molette (le coffre grandit pour tous), marque écolo, brosse et marteau « à effacer », fouets (œuf pondu, clé et charge dépensées une fois) utilisés par un invité agissent sur le monde de l'host ; ce qu'un tel outil change sur un objet chez l'host arrive chez les invités. Pas couvert : tentes, nouvelle fiche des fouets « passe-temps » et « métier » chez l'invité. | `unplayed_suite.py` U8, U9, 26/26 |
| Petits correctifs de la chasse 2, **pas joués** | Prix d'expédition lu avec le dieu du joueur et non celui de l'host (`445fa5e`) ; carte à gratter gratuite du casino qui arrive à l'invité (`3459019`). Joués avant (E1 à E3) : rondin taillé à la hache, prière qui soigne aussi les compagnons de l'invité, nourriture du sac de l'invité qui vieillit. | — / `hunt2_suite.py` E1 à E3 |
| Un joueur ne peut plus tuer un autre joueur (case `PlayerKill`, décochée, `ca8d009`, `RemotePlayerKillPatch.cs`) | Un coup d'un joueur, ou de ce qui se bat pour lui, qui tuerait le personnage d'un autre joueur le laisse à 0 point de vie, dans tous les jeux. Avant : un Maj + clic tuait pour de vrai (tombe, or au sol, écran de mort). Le coup arrivait par deux chemins : celui de l'host, et les dégâts que le jeu de la victime annonce après avoir rejoué l'attaque. Case cochée : le jeu d'origine. Première étape du conseil 7 (duels). Pas couvert : saignement, poison, feu, condamnation à mort ; sorts et projectiles : pas joués. | `duel_suite.py` P1, 10/10, deux sens |
| Dépôt GitHub (troisième sorte de dépôt, `1d698a5`) | Un dépôt GitHub **privé** garde le monde : aucun PC à laisser allumé, aucun port à ouvrir, chaque sauvegarde est gardée dans l'historique. Comment le régler : section 3 ; comment ça marche : section 4 ; preuves et limites : section 6. | `depot_github_test.py` 66/66 ; `depot_github_real.py` 13/13 ; `DEPOT_GITHUB=1 depot_suite.py` 31/33 |
| **Depuis la 0.26.506 (6 octobre, 14h → 22h30)** : | | |
| Le jeu sait quel personnage est à qui, sans question (0.26.506, `45acadd`, `29c4fa5`) | Celui qui reprend un monde joue SON personnage ; celui de l'ancien host l'attend. Un nouveau venu sans personnage passe par l'écran de création du jeu. Copie de secours avant tout échange. Plus d'écran « Who do you want to play? » à chaque connexion (clé `AskCharacter`, fausse par défaut). | `depot_suite.py` 33/33 |
| Retour automatique après une coupure (0.26.510, `c34732d`, règle 16 `AutoReconnect`) | L'invité dont le lien tombe revient seul dans la même partie (toutes les 5 s pendant 3 minutes). | `reconnect_suite.py` 46/46 |
| Sauvegarde toutes les 2 minutes, partie ouverte toute seule, redirection du dépôt (0.26.510) | Quand un autre joueur est là, le monde se sauve seul ; un monde déjà partagé ouvre sa partie au chargement ; si quelqu'un héberge déjà le monde du dépôt, le deuxième joueur est envoyé chez lui (bouton « Join X »). | `autosave_suite.py` 18/18 ; `depot_suite.py` D5b, D7 (pas relus après la dernière correction du test) |
| Corrections de la soirée à trois joueurs (0.26.510, `PLAN_retours_soiree_6_octobre.md`) | Les invités gardent leur case et arrivent par l'entrée, jamais dans l'eau ; le temps d'un autre ne coûte ni faim, ni nourriture pourrie, ni délais de quête ; sommeil : seuls les familiers du dormeur le rejoignent ; musique : un autre joueur ne jette plus de pièces ; ancien personnage jamais remis sur une carte ; cave gardée tant qu'un joueur y est ; chargement rapide arrêté à plusieurs. | `trio_place_suite.py` 17/17, `trio_time_suite.py` 25/25, `witness_suite.py`, `place_suite.py`, `travel_suite.py` 83/83 |
| **Depuis la 0.26.510, dans la 0.26.524 : TOUT CE QUI SUIT EST ÉCRIT, RELU, COMPILÉ, PAS JOUÉ** : | | |
| Désynchronisation entre les joueurs (`PLAN_desync.md`, `PLAN_desync_corrections.md`, `PLAN_desync_outil.md`, `PLAN_gros_messages.md`) | Plus aucun message jeté quand Steam est saturé (file locale par joueur, gros messages en morceaux de 128 Ko) ; le monde et la carte partent ensemble et ce que les autres font pendant le chargement est rejoué ; l'objet inconnu de l'host ne disparaît plus chez tous ; au départ de l'host, sa copie de la carte fait foi ; toutes les 2 s les jeux comparent quelques nombres par carte, un écart immobile est écrit dans les journaux (delta 842) et la carte est rechargée sur place (case `AutoResync`, règle 20). Les sacs en écart sont signalés, pas réparés. Réparer à la main : `emp.reconnect_self`. | `desync_suite.py`, `resync_suite.py` (jamais lancées) ; `chunk_check` ALL OK hors jeu |
| Boss de donjon (`PLAN_donjon_conquis.md`, `BossFleePatch.cs`) | Rejoindre un joueur à l'étage du boss ne le fait plus fuir et ne marque plus le donjon conquis. | `travel_suite.py` s19a, s19b (jamais lancées) |
| Ramassage sac plein (`PLAN_ramassage_sac_plein.md`) | Sac plein, l'objet reste par terre, comme en solo, au lieu d'entrer dans le sac sans case. | `pickup_suite.py` (jamais lancée) |
| Banque et caisse d'expédition d'un invité (`PLAN_banque_invite.md`) | Un invité seul sur une autre carte voit le vrai contenu, dépose et reprend (l'host sert la reprise) ; la banque et la boîte de livraison de la zone d'un autre invité vont à l'host. Banque commune. | `bank_suite.py` (jamais lancée) |
| Chacun dort pour soi (`PLAN_nuit_chacun_pour_soi.md`, `PLAN_reveil_invite.md`, case `OwnSleep`, règle 17) | On dort tout de suite sans attendre ; la nuit ne passe pour le monde que si tous dorment en même temps ; l'invité lit son grimoire, profite de son lit et de son oreiller, tire sa propre recette ; delta 840. | `sleep_suite.py` n1 à n6, k1 ; `trio_sleep_suite.py` (jamais lancées) |
| Le temps ne saute que quand tous sautent (`PLAN_date_ensemble.md`, case `TimeJumpsTogether`, règle 18) | Un pas sur la carte du monde ne fait avancer la date que si tous voyagent ensemble ; sinon le voyageur paie ses propres tours (l'invité aussi) ; le chronomètre des quêtes de récolte, concert, mariage n'avance plus par le temps d'un autre ; un message au lieu de 120 par pas. | `time_suite.py` W7 à W9 (jamais lancée) |
| Rangement et factures (`PLAN_rangement_factures.md`, case `DumpSparesBelt`, règle 19) | Le rangement automatique épargne la main et la ceinture à outils ; un invité paie une facture (impôt ou livraison) avec son or, une seule fois, tout le monde lit qui a payé (delta 839). | `hunt_suite.py` d3b ; `bills_suite.py` (jamais lancées) |
| Host seul = jeu solo (`PLAN_joueur_seul.md`, `NetCompany.HasCompany`) | Seul dans sa session, l'host retrouve les règles du jeu (dressage, pause des menus, tours de combat, réserve des alliés, perf). | `solo_suite.py` (jamais lancée) |
| Le dépôt ouvre la partie ; les joueurs connus entrent sans être amis Steam (`PLAN_salon_joueurs_connus.md`) | Prendre le monde du dépôt ouvre la session tout seul ; le salon ouvert tout seul est « Invisible » et filtré par l'host : ami, invité ou compte connu du monde. | `depot_suite.py` D8 ; deux comptes Steam pour le reste (jamais lancés) |
| Moins de lenteurs à plusieurs (`PLAN_lenteurs_corrections.md`) | Réseau lu jusqu'au bout (4 ms au plus par image), ménage des cartes une fois par seconde, une seule sauvegarde pour tous les retours, la quête de l'host est proposée aussi aux visiteurs. Rien n'a été mesuré. | `perf_probe.py` (jamais lancé) |
| **10-11 octobre, pas publié** : Boutiques à stock limité, une fois par joueur (`Patches/LimitedStockPatch.cs`) | Ce qu'un marchand ne vend qu'une fois par monde (livres de compétence, recettes, quelques armes) se vend une fois à chaque joueur ; un monde déjà joué retrouve ces objets au réassort suivant. | `oct10_suite.py l1` 21/21 |
| **Pas publié** : Combat, un monstre attaqué par un autre joueur que sa cible n'est plus figé (conseil 13, `Patches/PlayerCombatTime.cs`) | L'horloge d'un monstre est celle du joueur engagé le plus rapide (sa cible, ou qui l'a attaqué dans ses 5 derniers tours, touché ou raté), jamais la somme ; vaut sur la carte de l'host et sur une carte tenue par un invité. | `oct10_suite.py f1,f2` 19/19 (trois fenêtres) |
| **Pas publié** : Reprise quand l'host part ou plante (case `Takeover`, décochée ; `PLAN_reprise_automatique.md` R3 à R5) | L'host qui quitte donne sa dernière sauvegarde, l'invité désigné rouvre le monde, les autres le rejoignent seuls ; après un plantage, une minute d'attente puis la même chose. La case entraîne la copie du monde chez les invités. | `takeover_suite.py`, `takeover_trio.py` et `--crash` 13/13 |
| **Pas publié** : Ce que le jeu compte « pour le joueur » est à chacun (`DialogFlagSync._own`) | Prix du titre de terrain et du marteau de Garokk (qui doublent), prix de musicien, recette de cuisine inventée, malédiction de Melilith, maladie de l'éther. | `oct10_suite.py h1` |
| **Pas publié** : Petites égalités du 10 octobre | Une seule bourse pour un invité neuf ; sorts des barres gardés d'une session à l'autre ; offres de quêtes d'une ville identiques après un tirage, bouton « Reroll Quests » d'un invité ; factures payées de suite depuis une autre carte ; recette de bloc comptée une fois ; monture d'un invité reliée à son cavalier au retour. | `oct10_suite.py` (b1, h1, q1, c1, m1), `bills_suite.py p4` |

Limite de quêtes aléatoires : **5 par joueur** avec l'option « par joueur » (décisions du 2026-10-01 : quêtes
aléatoires, renommée et karma personnels ; histoire commune), 5 pour tout le groupe sans elle.

## 2. Options (host, onglet « Configuration du serveur »)

| Case | Cochée | Décochée |
|---|---|---|
| Voyage indépendant (`IndependentTravel`) | chacun va où il veut | tout le monde suit l'host, comme le mod d'origine |
| Expédition par joueur (`PlayerShipping`) | l'argent va au déposant | tout va à l'host |
| Combat au rythme du joueur (`PlayerCombatTime`) | chaque monstre suit son adversaire | rythme de l'host |
| Choix du personnage à la connexion (`ChooseCharacter`) | le joueur choisit parmi ses personnages de cette partie, ou en crée un nouveau | toujours le dernier personnage joué |
| Quêtes aléatoires et renommée par joueur (`PersonalQuests`) | chacun ses quêtes aléatoires, sa renommée, son karma | un journal et une renommée pour le groupe |
| Échange entre joueurs (`PlayerTrade`) | « Échanger » apparaît en cliquant sur un autre joueur | pas d'échange |
| Chaque joueur sur sa propre horloge (`PlayerClock`, avec le combat au rythme du joueur) | un invité marche aussi régulièrement que l'host | ses pas suivent le temps de l'host reçu par le réseau |
| Chacun marche comme en solo (`PlayerStepPace`, avec le combat au rythme du joueur) | un pas dure toujours le temps de base | la durée d'un pas dépend de l'écart de vitesse entre le joueur le plus rapide et le plus lent |
| Une seule date pour le monde (`SharedWorldTime`) | le temps passé par un joueur seul sur sa carte compte pour tous : la date la plus avancée est celle du monde | seule la date de l'host compte ; un joueur qui rentre reprend la sienne |
| Ce que le temps fait au monde n'arrive qu'une fois (`WorldKeeper`) | météo, quêtes expirées, impôts, salaires et lettres sont faits par un seul jeu (l'host pour l'instant), pareil pour tous | chaque joueur qui tient une carte les refait dans sa copie du monde |
| Personnage d'une sauvegarde solo (`ImportCharacter`, décochée par défaut) | le joueur peut amener le personnage d'une de ses sauvegardes | choix absent |
| Mode construction pour les autres joueurs (`GuestBuild`, règle de session n° 12, cochée par défaut) | un invité construit dans la base, c'est le jeu qui tient la carte qui construit pour lui | refus avec un message, seul le jeu qui tient la carte construit |
| Les joueurs peuvent se tuer (`PlayerKill`, règle n° 13, **décochée**) | un coup d'un joueur peut tuer le personnage d'un autre | le coup mortel laisse l'autre à 0 point de vie |
| Seul l'host gère la base (`HostManagesBase`, règle n° 14, décochée, `23041ef`) | ce que les autres joueurs demandent à la base (recherche, compétences du foyer, politiques, noms, réglages d'objets, résidents, mode construction) est refusé avec un message ; l'host leur renvoie l'état qu'il tient ; quitter la base pour de bon reste à l'host dans tous les cas | chaque joueur gère la base comme l'host |
| Duels entre joueurs (`AllowDuels`, règle n° 15, cochée) | « Challenge to a duel » dans le menu sur le personnage d'un autre joueur, boîte oui/non, compte à rebours, duel sur place ; personne ne meurt, les deux sont soignés, rien n'est perdu | pas de menu de duel |
| Retour automatique (`AutoReconnect`, règle n° 16, cochée) | un joueur dont le lien tombe revient seul | laissé à l'écran titre |
| **0.26.524, pas joué** : Chacun dort pour soi (`OwnSleep`, règle n° 17, cochée) | on dort tout de suite, la nuit ne passe que si tous dorment | tout le monde attend tout le monde |
| **0.26.524, pas joué** : Le temps ne saute que quand tous sautent (`TimeJumpsTogether`, règle n° 18, cochée) | un pas sur la carte du monde ne fait avancer la date que si tous voyagent ensemble ; le voyageur paie ses tours | chaque pas de n'importe qui ajoute 3 heures pour tous |
| **0.26.524, pas joué** : Le rangement épargne la main et la ceinture (`DumpSparesBelt`, règle n° 19, cochée) | le rangement automatique ne prend ni l'objet tenu ni la ceinture à outils | comme le jeu |
| **0.26.524, pas joué** : Réparer la carte tout seul (`AutoResync`, règle n° 20, cochée) | une carte en écart durable est rechargée (au plus une fois par 30 s, jamais en combat ni menu ouvert) | l'écart n'est qu'écrit dans le journal |

Les options sont envoyées aux clients à la connexion (`NetSessionRules`). Toute nouvelle fonction doit avoir sa case.
**État au 2026-10-11 : prochaine règle de session libre 24, prochain delta libre 847 (845 `QuestOffersDelta`, 846 `QuestRerollDelta`) ; les nombres ci-dessous datent du 6 octobre.**
Règles de session prises jusqu'à la clé 20 (12 `AllowGuestBuild`, 13 `AllowPlayerKill`, 14 `HostManagesBase`, 15
`AllowDuels`, 16 `AllowReconnect`, 17 `UseOwnSleep`, 18 `TimeJumpsTogether`, 19 `DumpSparesBelt`, 20 `AutoResync`) : la prochaine est la clé 21.
Deltas pris jusqu'à 842 (839 `BillPayDelta`, 840 `SleepStateDelta`, 842 `DesyncReportDelta` ; 841 libre). Le dépôt GitHub n'a pas de case de l'host : c'est un réglage de chaque joueur (onglet « Client
Settings », comme les autres dépôts), voir section 3.

## 3. Installer

**Pour jouer (toi et ton ami, même zip des deux côtés)** : `_release/ElinTogether-independance.zip`, puis
`Installer.bat`. `Desinstaller.bat` remet le mod du Workshop. Refaire le zip : `make_release.ps1`. Le zip n'est
pas dans le dépôt : il se fabrique sur chaque machine.
**Mise à jour du 6 octobre, 22h30 : la dernière version publiée est la 0.26.524** (voir l'état en tête de ce document ; la note est `NOTE_version.md`).
Le texte qui suit date de la 0.26.506 et reste valable pour l'installation.
La version publiée avant elle était la **0.26.506** (2026-10-05, au soir, compilée pour Elin EA 23.352,
https://github.com/devmarcpro/elin-together/releases/tag/independance-0.26.506). Elle remplace la 0.26.463 (15h35, commit
`895d5b0`) et la 0.26.442 (commit `f096255`, compilée pour 23.351). **Tout ce qui est décrit dans ce document comme « depuis
la 0.26.463 » est dans la 0.26.506** (mode construction d'un invité complet, terrain, zones, base gérée par un invité,
duels, dépôt GitHub, etc.) ; ce qui est écrit « depuis la 0.26.506 » n'y est pas : une nouvelle version se publie
seulement avec l'accord de l'utilisateur. Le zip de `_release` est celui de la dernière
publication ; il est aussi sur la page des versions du dépôt (https://github.com/devmarcpro/elin-together/releases) :
c'est le lien à donner à un ami. La note de version est `NOTE_version.md`, les README des quatre langues ont
8 captures dans `assets/screens/` (prises par `_tools/showcase.py`).
**Le jeu de cette machine peut avoir un build de TEST plus récent que la 0.26.506** (`build.ps1`) : avant de jouer avec
quelqu'un, relancer `Installer.bat` du zip publié, sinon la connexion est refusée (versions différentes).

**Garder le monde sur GitHub (dépôt « GitHub », depuis `1d698a5`, dans la 0.26.506).** C'est la troisième sorte de
dépôt du mode « sans Elin », avec un dossier partagé et Elin Together Server. Les quatre étapes sont aussi écrites dans
le mod (onglet « Client Settings »). Celui qui est propriétaire du dépôt :
1. crée sur github.com un dépôt **vide et privé**, uniquement pour ce monde (jamais le dépôt public du mod) ;
2. crée une **clé d'accès** (Settings, Developer settings, Fine-grained tokens) limitée à **ce seul dépôt**, droit
   « Contents : Read and write » (une clé a une date de fin : expirée, le jeu dit « clé refusée ») ;
3. colle la clé dans le réglage « mot de passe du dépôt / clé GitHub » (Client Settings) et écrit dans « Depot »
   `github:proprietaire/depot` (exemple : `github:marc/elin-monde`) ;
4. donne ces deux lignes à ses amis, qui les mettent aux mêmes endroits.
**Une seule clé, créée par le propriétaire du dépôt et partagée** : un ami n'a pas besoin de compte GitHub, la clé
n'ouvre que ce dépôt et se révoque d'un clic. (On pense qu'une clé de ce genre ne peut viser que les dépôts du compte
qui l'a créée, donc les amis ne peuvent pas faire la leur sur le dépôt de l'autre : non vérifié.) Ensuite, le joueur
prend le monde comme avec les autres dépôts (écran titre, Lobby, « Take the world… »). La clé reste en clair dans le
fichier de réglages du mod, comme le mot de passe d'un autre dépôt ; la boîte de saisie ne la réaffiche jamais
(laissée vide, la clé est gardée). Le mod refuse, avec un message : clé absente ou refusée, dépôt introuvable, **dépôt
public**, monde de plus de 20 Mo en zip. La clé n'est écrite dans aucun journal. Un dépôt grossit à chaque envoi :
on le supprime et on en recrée un quand il approche 1 Go (calcul, pas mesuré : environ 72 Mo par soirée de 4 h).

**Pour développer** : `build.ps1` compile en Debug et copie dans `Elin\Package\Mod_ElinTogether`. Le Debug ajoute
le pont de test (ports 27551+) et permet deux fenêtres sur le même PC. `build.ps1 Release` pour la version joueur.
Elin doit être fermé pendant la compilation.

## 4. Comment ça marche

**Base (mod d'origine).** L'host simule le monde. Chaque changement part en « delta » vers les clients, qui
l'appliquent. Les clients envoient leurs actions à l'host.

**Voyage seul.** Quand un client quitte la carte de l'host, il demande un **bail** sur la carte où il va. S'il
l'obtient, il charge sa propre copie du monde et la simule lui-même. À son retour (ou à chaque point de
sauvegarde), il renvoie la carte à l'host, qui reste la référence. Le lien avec l'host reste ouvert pour le chat,
les quêtes et les souvenirs de dialogue.

**Carte partagée.** Celui qui tient le bail ouvre une **session de zone** : il devient host pour cette carte, et
les autres s'y connectent comme invités, en plus de leur lien avec le vrai host. S'il part, le bail passe à un
invité (**passation**) et les autres se reconnectent à lui. Quand c'est l'host qui quitte sa carte, le même
mécanisme sert : le premier joueur resté reçoit le bail.

**Compagnons.** Chaque compagnon porte le numéro de son joueur. Il suit ce joueur, voyage avec lui, et ne compte
que dans sa limite d'alliés.

**Expédition.** Chaque objet déposé est marqué du numéro du déposant. À 5 h, l'host vend tout, garde les comptes
par joueur, et envoie à chacun son argent (ou le lui garde s'il est absent).

**Combat.** Avec l'option, un monstre lié à un joueur n'avance que quand ce joueur joue un tour.

**Quêtes aléatoires par joueur.** Chaque jeu ne garde dans son journal que les quêtes aléatoires de son joueur.
L'host conserve celles de tout le monde dans la sauvegarde, avec la renommée et le karma de chacun, et les
redonne au joueur quand il arrive sur sa carte. Quand un joueur prend ou rend une quête sur la carte de l'host,
l'host exécute l'étape « à sa place » : l'objet à livrer, la récompense, la renommée vont à ce joueur.

**Quêtes d'histoire.** L'host tient le seul journal. Sur sa carte, il exécute lui-même ce qu'une étape déclenche, et dépose
les récompenses aux pieds du joueur concerné. En voyage, le joueur exécute l'étape dans sa copie et prévient
l'host, qui met le journal à jour sans redonner la récompense. Chaque bail réserve 10 000 numéros de quêtes pour
éviter les doublons.

**Quêtes à donjon.** Le joueur qui prend la quête demande à l'host un bail sur une zone neuve, créée pour
l'occasion et jamais réutilisée. Il la simule comme n'importe quelle carte où il voyage seul. En sortant, le
résultat est noté, puis réglé une fois qu'il est arrivé quelque part ; l'host détruit alors la zone.

**Échange.** Celui qui simule la carte (l'host, ou le joueur qui tient la carte) tient la « table » : il reçoit
les intentions (inviter, accepter, offrir, confirmer), renvoie l'état aux deux joueurs, et fait le transfert d'un
seul coup après avoir revérifié que chaque objet et chaque pièce existe encore.

**Karma.** Le jeu retire du karma « au joueur » là où l'action se règle : une mort chez l'host, une fin de tâche
chez l'host puis rejouée chez chaque client. Chez un client, ce qui est retiré pendant le rejeu d'un message de
l'host est ignoré ; chez l'host, le coupable est le joueur derrière le tueur ou derrière la tâche, et l'host lui
envoie la sanction. Quand un garde regarde quelqu'un, la question « le joueur est-il criminel ? » est posée pour
le joueur regardé.

**Affinité, guildes.** Le jeu du joueur qui agit calcule, l'host garde la valeur et la renvoie à tous.

*Les paragraphes suivants décrivent ce qui est nouveau depuis la 0.26.463.*

**Mode construction d'un invité.** Chez l'invité, le jeu fabrique déjà la tâche (poser, miner, couper…) et la fait finir
par « l'agent ». Le mod envoie cette tâche à celui qui tient la carte (`AgentTaskDelta`, union 831, avec `TaskBuildArgs`,
tâche 227) au lieu de la finir ; ce jeu-là la termine avec l'invité à la place du joueur (`RemoteCraft.AsCrafter`). L'or
(déjà une demande, `CardModCurrencyDelta`), la pierre ramassée et les matières vont donc du bon sac, sans code de plus.
L'host revérifie la case `GuestBuild` (double clic), les ingrédients (nombre et quantité) ; le remboursement est plafonné
à 10. Idée écartée : rejouer le geste chez chacun (faux dès que les cartes diffèrent).

**Terrain, zones, hauteurs.** Celui qui simule la carte envoie en fin d'image l'état de chaque case changée
(`TileStateDelta`, union 830 ; ce qui change une case sans passer par les fonctions habituelles de la carte est vu par
`TileStateDirectEvent.cs`). Les zones de base : `AreaStateDelta` (834), lu par `AreaWatch.cs`, comparé champ par champ.
Les hauteurs de l'outil de terrain : `TerrainHeightDelta` (833). L'invité demande, celui qui simule fait et diffuse.

**Dépôt GitHub (`Helper/GitHubDepot.cs`, branché dans `Helper/SaveDepot.cs`).** Il répond aux mêmes cinq demandes que
le logiciel serveur (qui héberge ? prendre, déposer, battre, rendre) avec deux fichiers de la branche par défaut :
`lock.json` (qui héberge) et `world.zip`. Chaque écriture nomme la version qu'elle remplace (`sha`) : de deux joueurs qui
écrivent en même temps, GitHub n'en accepte qu'un, et ce refus **est** le verrou (rien n'est jamais forcé ; l'historique
garde tous les mondes, c'est la sauvegarde de secours). Verrou périmé après 3 minutes, comptées à l'heure de GitHub.
Les sauvegardes partent en arrière-plan (le jeu ne se fige pas), au plus une toutes les 5 minutes, la dernière à la
sortie ; un marqueur `world_depot.unsent` est posé avant l'envoi. Une sauvegarde gardée de côté ne remplace jamais un
monde plus récent. Le nom du dépôt est refusé s'il n'est pas de la forme attendue, un dépôt renommé est suivi. La clé
ne voyage que dans l'en-tête `Authorization`. Le fichier compile seul (`dev/_tools/github_depot_cli/`) pour les tests ;
un faux GitHub local sert aux tests (`dev/_tools/fake_github.py`, le jeu l'atteint par la variable
`ELINTOGETHER_GITHUB_API`, acceptée seulement pour 127.0.0.1).

**Un joueur ne tue pas un autre joueur (`Patches/Remote/RemotePlayerKillPatch.cs`).** Si un coup d'un joueur, ou de ce
qui se bat pour lui, tuerait le personnage d'un autre joueur, il le laisse à 0 point de vie. Deux chemins : le coup
propre de l'host, et les dégâts annoncés par le jeu de la victime après qu'elle a rejoué l'attaque
(`CardDamageHpDelta.cs`). La case `PlayerKill` rend le comportement du jeu d'origine.

### Où c'est dans le code (`ElinTogether/ElinTogether/`)

Chemins relatifs au dossier `ElinTogether/` du dépôt (le code du mod).

| Sujet | Fichiers |
|---|---|
| Baux, départ, retour, passation | `Net/Host/ElinNetHostTravel.cs`, `Net/Client/ElinNetClientTravel.cs` |
| Arrivée d'un joueur sur une carte | `Net/Host/ElinNetHostZone.cs`, `Net/Client/ElinNetClientZone.cs` |
| État de la session (voyage, session de zone) | `Net/NetSession.cs`, `Net/NetSessionRules.cs` |
| Compagnons | `Helper/CompanionHelper.cs`, `Net/Host/ElinNetHostCompanions.cs`, `Patches/Companion*.cs` |
| Expédition | `Helper/ShippingHelper.cs`, `Net/Host/ElinNetHostShipping.cs`, `Net/Client/ElinNetClientShipping.cs` |
| Combat | `Patches/PlayerCombatTime.cs`, `Patches/PauseGame.cs` |
| Quêtes aléatoires par joueur | `Helper/PersonalQuests.cs`, `Net/Host/ElinNetHostPersonalQuests.cs`, `Models/Delta/Quest/PersonalQuestDeltas.cs` |
| Quêtes et histoire | `Models/Delta/Quest/`, `Patches/DeltaEvents/Quest/`, `Helper/SharedQuests.cs`, `Helper/DialogFlagSync.cs` (mémoire commune), `Helper/StoryGifts.cs` (objets offerts), `StoryOutcomePatch.cs` (effets sur le monde) |
| Quêtes à donjon | `Helper/PersonalQuests.cs` (`LeaveInstance`, `SettleOutcome`), `Net/Host/ElinNetHostTravel.cs` (`CreateQuestZone`), `Patches/LeasedZonePatch.cs` |
| Échange | `Helper/PlayerTrade.cs`, `Components/LayerPlayerTrade.cs`, `Models/Delta/Inv/PlayerTradeDeltas.cs`, `Patches/PlayerTradePatch.cs` |
| Choix du personnage | `Models/SessionState/SessionCharaSelect.cs`, `Net/Host/ElinNetHostPlayerManager.cs`, `Net/Client/ElinNetClientPlayer.cs` |
| Karma et crime | `Helper/PlayerKarma.cs`, `Patches/PlayerKarmaPatch.cs`, `Net/Host/ElinNetHostPersonalQuests.cs` (`GiveKarma`, `IsCriminal`) |
| Affinité, guildes | `Models/Delta/Chara/CharaAffinityDelta.cs`, `Patches/DeltaEvents/Chara/CharaAffinityPatch.cs`, `Helper/DialogFlagSync.cs` |
| Mode construction d'un invité | `Models/Delta/Zone/AgentTaskDelta.cs`, `Models/Delta/Task/TaskBuildArgs.cs`, `Patches/Remote/RemoteBuildModePatch.cs`, `Patches/Remote/RemoteAgentTaskPatch.cs` |
| Terrain, zones, hauteurs | `Models/Delta/Zone/TileStateDelta.cs`, `Patches/DeltaEvents/Zone/TileStateEvent.cs`, `TileStateDirectEvent.cs`, `Models/Delta/Zone/AreaStateDelta.cs`, `Patches/Synchronization/AreaWatch.cs`, `Models/Delta/Zone/TerrainHeightDelta.cs`, `Patches/Remote/RemoteTerrainPatch.cs` |
| Réglages de coffre | `Models/Delta/Inv/InvSaveDataDelta.cs`, `Patches/DeltaEvents/Inventory/InvRefreshMenuEvent.cs` |
| Autel, résurrection, copie, outils | `Patches/Remote/RemoteAltarPatch.cs`, `Models/Delta/Chara/CharaReviveRequestDelta.cs` + `Patches/Remote/RemoteRevivePatch.cs`, `Models/Delta/Zone/CopyShopDelta.cs` + `Patches/DramaCopyShopPatch.cs`, `Models/Delta/Card/CardActReplayDelta.cs` + `CardSettingDelta.cs` |
| Un joueur ne tue pas un joueur | `Patches/Remote/RemotePlayerKillPatch.cs`, `Models/Delta/Card/CardDamageHpDelta.cs` |
| Base gérée par un invité (pas commité) | `Models/Delta/Zone/BaseRequestDelta.cs`, `BaseStateDelta.cs`, `Patches/Remote/RemoteBasePaidPatch.cs`, `RemoteResidentPatch.cs` |
| Dépôt GitHub | `Helper/GitHubDepot.cs`, `Helper/SaveDepot.cs`, `Components/Tabs/TabClientConfiguration.cs` (texte d'aide `emp_ui_depot_gh_help`) |
| Bot du menu | `Emp/EmpBot.cs`, `Emp/EmpBotLauncher.cs` |
| Options | `Emp/EmpConfig.cs`, `Components/Tabs/TabServerConfiguration.cs` |
| Pont de test (Debug) | `Emp/EmpDebugListener.cs` |

Règle à ne pas oublier : chaque type de delta a un numéro (`[Union(n, …)]` dans `Models/Delta/ElinDelta.cs`).
Deux deltas avec le même numéro cassent toute la communication. **Numéros pris au 2026-10-05, 19h30 : deltas jusqu'à
835** (830 `TileStateDelta`, 831 `AgentTaskDelta`, 832 `CharaReviveRequestDelta`, 833 `TerrainHeightDelta`, 834
`AreaStateDelta`, 835 `CopyShopDelta`), **arguments de tâche jusqu'à 227** (`TaskBuildArgs`), **règles de session
jusqu'à la clé 14**. Le prochain delta prend 836.

## 5. Tester

Tout se fait sur ce PC, avec plusieurs fenêtres Elin muettes, pilotées par le pont de test. Les commandes se
lancent depuis `dev/`, avec `PYTHONPATH=_tools/pylib`.

```
python _tools/mp_test.py                 # lance host + 1 client dans la Prairie (--clients 2 ou 3 pour plus)
python _tools/launch_client.py           # ajoute un client à un host déjà lancé
python _tools/quest_suite.py             # un test court, sur les fenêtres déjà ouvertes
python _tools/bot.py --minutes 5 --seed 1
```

| Outil | Sert à | Joueurs | Durée |
|---|---|---|---|
| `leave_suite.py` | l'host change de carte | 2 | ~1 min |
| `quest_suite.py` | quêtes (par joueur, histoire), souvenirs de dialogue | 2 | ~4 min |
| `instance_suite.py` | quêtes à donjon prises par un client | 2 | ~3 min |
| `trade_suite.py` | échange entre joueurs, dont les refus (objet non lâchable, sac plein, objet équipé : R6–R11) | 2 | ~3 min |
| `chara_suite.py` | choix du personnage à la connexion | 2 | ~3 min |
| `parity_suite.py` | affinité, guildes, karma et gardes | 2 | ~1 min |
| `transfer_suite.py` | ce qui se passe pendant un changement de carte | 2 | ~3 min |
| `economy_suite.py` | expédition par joueur | 2 | ~5 min |
| `combat_suite.py` | combat au rythme du joueur | 2 | ~5 min |
| `build_suite.py` | poser, construire, mur cassé par un monstre | 2 | ~3 min |
| `player_suite.py` | dons à la fabrication, apparence au miroir, slime | 2 | ~4 min |
| `death_suite.py` | mourir sur la carte de l'host puis repartir seul | 2 | ~3 min |
| `sleep_suite.py` | dormir à plusieurs, à la base ou sur une carte sauvage (`--only w0,z0,z1,z2`) | 2 | ~3 min |
| `guest_suite.py` | le même geste par l'invité puis par l'host : repos, pêche, baguette, coffres de pari, bouteille vide, gestes tenus en main (G33–G39 : ticket, seringues, puits, laisse, stéthoscope ; `--only g33,g34,g35,g36,g37,g38,g39`) | 2 | ~3 min |
| `equal2_suite.py` | invité et host à égalité : abattage (E2), appel à l'aide à Vernis (E1), dieu quitté (E3), source chaude (E4) | 2 | ~5 min |
| `together_suite.py` | quêtes à donjon à deux, dans les deux sens : boîte Oui/Non, entrer, sortir, fouille de l'accompagnant (T1–T6, l'host a la quête) ; l'invité a la quête, boîte chez l'host, récompense, l'host rentre seul, sauvegarde de l'host (T7–T11) ; récolte et musique de l'invité (T12, T13) ; `--only t7,t8` | 2 | ~20 min |
| `hunt_suite.py` | chasse aux différences host / invité, un test par ligne de `PLAN_chasse_differences.md` : peur, guérisseur, rangement, objets à fenêtre, faucille, investir, prêtresses, évacuation, recette, rune, carte au trésor, pied-de-biche, consignes « ne pas s'éloigner » et « ne pas vagabonder » (D1–D14 ; `--only d1,d3`). Sait dérouler un vrai dialogue (`talk`, `pick`, `hang_up` : choix cliqué par son texte anglais) | 2 | ~10 min |
| `hunt2_suite.py` | deuxième chasse aux différences, un test par ligne de `PLAN_chasse_differences_2.md` : E1 rondin à la hache, E2 prière et compagnons, E3 nourriture du sac, E4 prière sans dieu, E5 jours qui passent, E6 offrande sur l'autel d'un autre dieu, E7 résurrection d'un compagnon chez le barman, E8 copie chez Kettle (E1 à E8, 140/140 pour la suite ; `--only e7,e8`) | 2 | non mesuré |
| `build2_suite.py` | mode construction à deux (conseil 5) : G1 refus avant de payer ; l'invité pose un sol (C1), mine (C2), coupe (C5), pose un meuble neuf (C6) ; l'host pose un sol (C3) et mine un mur (C4) vus par l'invité ; outil de terrain trois coups (C7) ; zone de base créée, renommée, effacée (C8) ; mur tourné et plante qui pousse (C9) (58/58) | 2 | non mesuré |
| `duel_suite.py` | duels entre joueurs (conseil 7) : P1 hors duel un joueur ne peut pas tuer l'autre, dans les deux sens (10/10). Les autres étapes ne sont pas écrites | 2 | non mesuré |
| `base_suite.py` | base réglée par un invité : recherche et compétences du foyer = demandes à l'host, payées une fois, état de la base chez les deux, recherche de l'host chez l'invité (B1 20/20, B4) | 2 | ~4 min |
| `setting_suite.py` | réglages d'un joueur vus par l'autre, deux sens : notes, étiquettes de vente, lits, politiques (vraie fenêtre), nom de la base, de la faction et d'un téléporteur (S1–S6, 25/25), **réglages d'un coffre de la base (S7, le banc pose les valeurs que posent les curseurs, il ne clique pas le filtre, le collage ni les boutons d'autodump)** | 2 | ~5 min |
| `unplayed_suite.py` | tests de corrections jamais jouées : tri du sac, deux acheteurs, monture, ticket d'hôtesse (U1, U3, U5, U6) ; **clé à molette sur un coffre (U8) et fouet-œuf sur un animal compagnon (U9), 26/26** ; U2 bouton partagé d'un coffre, U4 parchemin d'alias, U7 eau profonde : seulement avec `--only`, le banc ne les joue pas | 2 | ~6 min |
| `version_suite.py` | barrière de version (`ee374b7`) : même mod et Elin différent = connexion et avertissement ; mod différent = refus ; case de l'host cochée = refus strict (8 vérifications, connexion locale ; salon Steam non joué) | 2 | ~3 min |
| `recruit_suite.py` | compagnons recrutés par un invité : dialogue, monture, boule à monstre, achat | 2 | ~5 min |
| `council_suite.py` | les décisions du conseil du 2026-10-04 : grimoires, prime de guilde, cadeaux du dieu, mort après le jour 90, pièges (à Vernis) ; `--only c6` carte au trésor (ne passe pas au banc) | 2 | ~5 min |
| `move_suite.py` | pas de l'invité : réguliers, host qui rame, écart de vitesse, accéléré partagé | 2 | ~2 min |
| `import_suite.py` | rejoindre avec le personnage d'une sauvegarde (copie du monde de test) | 2 | ~3 min |
| `time_suite.py` | une seule date pour le monde : invité seul ailleurs, host, saut de cinq heures, retour | 2 | ~2 min |
| `world_suite.py` | le gardien du monde : même météo partout, fin de mois comptée une fois | 2 | ~2 min |
| `depot_github_test.py` | le dépôt GitHub sans le jeu et sans GitHub : le vrai code C# du mod (`github_depot_cli`) contre `fake_github.py`, un processus par joueur : refus clairs (clé, dépôt introuvable ou public), course au verrou, verrou périmé, monde changé pendant une coupure, pannes (500, limite de débit, coupure), 19 Mo oui / 21 Mo non, réponse perdue puis renvoi, clé nulle part ailleurs que dans l'en-tête (G0–G13, 66/66) | 0 | ~1 min |
| `depot_github_real.py` | le même C# contre le **vrai** GitHub, sur un dépôt privé d'essai (`python _tools/depot_github_real.py proprietaire/depot` ; la clé est celle que git a déjà sur ce PC, gardée en mémoire, écrite nulle part) : prise, envoi de 1,6 et 2,1 Mo, octets identiques au-delà de 1 Mo, refus de celui qui n'a plus le monde, deux preneurs en même temps (un seul gagne) (13/13). N'écrire que sur un dépôt d'essai | 0 | non mesuré |
| `depot_proto_test.py` | le protocole du serveur sans le jeu : monde remplacé, refus, mot de passe, sauvegardes de secours (11 vérifications) | 0 | ~10 s |
| `depot_suite.py` | dépôt de sauvegarde : déposer, prendre, refus quand c'est pris, relais entre deux joueurs, monde neuf (`DEPOT_SERVER=1` : à travers le logiciel serveur ; **`DEPOT_GITHUB=1` : à travers le dépôt GitHub contre le faux GitHub local, 31/33, le rouge est la fermeture du jeu pendant un envoi (G4) ; ~10 min, `DEPOT_GITHUB_FULL_WAIT=1` attend vraiment les 5 minutes d'envoi**) | 2 | ~2 min (~10 min avec GitHub) |
| `server_suite.py` | serveur : démarrage tout seul, joueur qui rejoint par adresse, temps qui avance, retour | lance ses 2 fenêtres | ~4 min |
| `server_ui_test.ps1` | les boutons du logiciel serveur, clics sur les vrais contrôles (PowerShell : `-Part depot` 15 vérifications, sans Elin, port 55558, dossier `%TEMP%\ets-ui-depot` ; `-Part elin` 6 vérifications, lance un Elin sans fenêtre) | — | — |
| `compat_suite.py` | cohabitation avec d'autres mods (Somewhat Enhanced Display) | 2 | ~2 min |
| `run_short.sh` | les suites courtes à la suite, chacune sur un monde neuf (pas `economy`, `combat`, `travel` ni `shared`, qui ouvrent leurs fenêtres : les lancer seules, jeu fermé) | 2 | ~50 min |
| `companion_suite.py`, `party_suite.py` | compagnons, limite d'alliés | 2 | ~10 min chacun |
| `travel_suite.py` | voyage seul, sauvegarde, chat, équipement | 2 | ~15 min |
| `shared_suite.py`, `trio_suite.py` | cartes partagées, passation | 3 et 4 | ~15 min chacun |
| `run_all.sh` | tout, à la suite | — | > 1 h, PC libre seulement |
| `bot.py` | jouer au hasard et surveiller | 2 | au choix |

**Le bot** joue au hasard (marcher, voyager, ramasser, poser, manger, parler, attaquer, quêtes, vendre,
s'équiper, mourir et revenir). Toutes les 4 actions il vérifie : les deux jeux répondent, pas d'erreur dans les
journaux, même journal de quêtes, et sur la même carte mêmes joueurs, sacs, or et objets au sol. Il ne sait pas
si le jeu est « juste », seulement s'il casse ou si les deux jeux ne sont plus d'accord. `--seed N` rejoue la même
suite, `--who host` fait jouer l'host, `--only a,b` limite les actions. Compte rendu dans `_shots/bot-*.log`.

**Le bot depuis le jeu.** Dans le menu ElinTogether, onglet « Lobby » : **Add a bot player** ouvre une deuxième
fenêtre Elin (muette), qui rejoint ta partie toute seule en ~30 s et joue au hasard. **Stop the bots** la ferme.
La case « Bots also take quests and sell » l'autorise à prendre des quêtes et à vendre par la caisse (à laisser
décochée sur un monde auquel tu tiens ; même sans elle, le bot ramasse et pose ce qui traîne au sol).
Conditions : version Debug du mod, serveur local (le bouton le démarre si aucun serveur ne tourne ; avec un
serveur Steam déjà ouvert il faut d'abord se déconnecter), et les copies du jeu `_lab/Elin2…4` (`make_lab.py`).
Pendant qu'il joue, `python _tools/bot.py --watch --minutes 5` fait les vérifications. Ce que fait le bot est
écrit dans le journal du mod (lignes « Bot: »). Code : `Emp/EmpBot.cs`, `Emp/EmpBotLauncher.cs`.

Monde de test : `world_lab`, remis à neuf à chaque lancement depuis `_lab/saves/world_lab.pristine`. Les vraies
sauvegardes ne sont pas touchées (copies dans `_backup/`).

### Règles de travail

- Tests **courts**, sur des fenêtres déjà ouvertes, seulement ce qui a changé. La passe complète : quand le PC est libre.
- Fenêtres Elin toujours **muettes** (`-empmute`).
- Ne pas cliquer dans la fenêtre de l'host pendant le chargement (sinon il charge une vraie sauvegarde).
- Fermer Elin **par numéro de processus exact**. D'autres sessions lancent aussi le jeu sur ce PC : ce travail-ci
  passe avant (leurs fenêtres peuvent être fermées), mais jamais un jeu lancé par l'utilisateur.
  `run_all.sh` ferme **tous** les Elin entre deux suites : PC libre seulement.
- Ne jamais laisser une correction sans test, même venue d'une relecture.
- Les fenêtres se lancent **une à la fois** (`mp_test.py` le fait) : deux jeux qui démarrent ensemble mettent
  8 minutes et l'host peut rester figé. Ne pas compiler pendant un lancement.
- Un changement = un test = un commit, puis une ligne dans `MODLOG.md`.

## 6. Limites connues

- **Dialogues d'histoire joués par un client** : quêtes, objets offerts, effets sur le monde et mémoire de
  l'histoire sont gérés, mais testés par appels directs, **pas encore en cliquant dans les vrais dialogues** (depuis le 5 octobre le banc sait le faire : `hunt_suite.py`,
  aides `talk`, `pick`, `hang_up` ; guérisseur, boutique et prêtresses sont joués ainsi, pas encore les quêtes).
  Restent locaux au joueur : les alliés offerts par un dialogue (animal de Fiama), le mariage. En voyage seul, seuls les effets « sur le monde entier » sont répétés chez l'host.
- Quêtes à donjon : à deux, dans les deux sens (boîte Oui/Non chez l'autre joueur ; `PLAN_quetes_donjon_a_deux.md`,
  E1 à E6 faites). Dans le sens « l'invité a la quête » : subjuguer, récolte et musique (`af18078`) ; la défense reste
  en solo
  pour l'invité (cor, vagues et prime tenus par celui qui simule) ; le score d'un concert joué par l'host n'est pas
  testé. Les tests prennent la
  quête, tuent et sortent par les appels du jeu, pas par le dialogue ni au combat ; pas de test de déconnexion dans la
  zone ; à trois joueurs : pas essayé ; `instance_suite` et le bot attendent 15 s à chaque entrée (boîte sans réponse
  chez l'host). L'escorte prise par un client n'a été testée que par le code, pas en marchant.
- Échange : les objets équipés ne s'échangent pas (le message le dit, pas de déséquipement automatique) ; un sac plein
  est refusé avant tout transfert (`9cd8062`) ; fenêtre simple (liste + boutons).
- Karma : sur une carte tenue par un joueur (pas l'host), les gardes voient le karma d'un visiteur depuis `927f342`
  (il l'annonce au teneur, en mémoire seulement ; **pas joué**).
  (Un habitant attaqué par un invité appelle maintenant à l'aide comme pour l'host, `cf4797d` ; l'affinité de la
  tonte est bonne, confirmé par `equal2_suite` E2.) Expérience de guilde :
  si deux joueurs en gagnent au même instant, un des deux gains est perdu.
- Conflits connus, rares, non corrigés : deux achats au même instant chez le même marchand (un seul payé), deux
  joueurs qui construisent sur la même case (deux objets consommés), monture qui existe en double au retour
  d'un voyage, plantage du joueur qui tient une carte avec des invités (retour à sa dernière sauvegarde).
  Un invité qui demande à voyager à l'instant où la carte qu'il visite change de mains perd sa demande : il
  doit recliquer.
- **État des tests au 2026-10-04 à 5h, Elin EA 23.351 Patch 2** : passe complète sur `7b0c70e` (le code de la
  version publiée ensuite), les 23 suites vertes : travel 55/55, shared 26/26, trio 24/24, companion 30/30,
  party 28/28, economy 24/24, combat 21/21, quest 61/61, chara 13/13, parity 17/17, trade 32/32, build 21/21,
  player 40/40, instance 34/34, leave 15/15, transfer 11/11, death 13/13, sleep 34/34, guest 218/218,
  recruit 41/41, compat 7/7, move 18/18, import 21/21. Puis, sur `1ed724d` (sauvegardes du nuage Steam, seul
  `CharaImport.cs` change) : import 25/25, chara 13/13, leave 15/15, quest 61/61, compat 7/7.
  Après une mise à jour d'Elin par Steam : refaire `make_lab.py` pour les trois copies, sinon le client de test
  est refusé (« invalid version », ou « Version mismatch … game 0.23.351.2 -> 0.23.352.0 ») sans que `mp_test.py` dise
  pourquoi. **Elin est passé de EA 23.351 à EA 23.352 le 2026-10-05** (canal « Stable » dans `version.json`) : rejoué
  dessus, hunt D1 8/8, together T1–T2 19/19, unplayed 51/53 ; le code décompilé `_decomp` est encore celui de 23.351, à
  refaire. **Barrière de version : faite, `ee374b7`, `version_suite` 8/8 en local, salon Steam non joué** (ne plus
  refuser une connexion que si la version du MOD diffère ; Elin différent = un avertissement ; une case côté host pour
  le contrôle strict ; quatre contrôles à changer : clé de connexion Steam, filtre des salons, poignée de main côté
  client et côté host).
  Les quatre changements de `36eccb3` (banque en voyage, rappel abandonné, bail refusé, entrées bloquées pendant
  une passation) n'ont toujours pas de test à eux.
- Sommeil : pas testé à trois joueurs. (Un invité seul sur une carte qu'il tient peut y dormir : `sleep_suite` Y1.)
- Vu dans la vraie partie du 2026-10-03 et pas encore corrigé : le rechargement de l'invité quand l'host revient
  sur sa carte (une fois au lieu de deux depuis `23554f2`).
- Déplacements : corrigés et mesurés au banc local, **pas encore joués entre deux PC**. La marche touche
  enfoncée ou souris tenue n'est pas testée (le pont de test ne tient pas de touche).
- Personnage d'une sauvegarde solo : testé avec un personnage de niveau 1, et une fois avec un vrai personnage
  de l'utilisateur (niveau 4, sauvegarde du nuage Steam de 1 Mo : en jeu en 8 s). Pas essayé : une grosse sauvegarde
  de fin de partie (gel de quelques secondes attendu à la lecture), une sauvegarde faite avec d'autres mods (objet
  inconnu chez l'host), un personnage qui porte une boule à monstre pleine (le monstre garde son ancien numéro),
  les artefacts uniques en double, les cadeaux du dieu reçus de nouveau. Avec la case cochée et « choix du
  personnage » décochée, l'écran de choix s'affiche à chaque connexion. Les sauvegardes du nuage Steam sont
  listées et lues dans leur archive, sans être déballées.
- Compagnons d'un invité : l'achat est testé par ce que fait le « oui » du marchand, pas par son vrai dialogue.
  La consigne « ne pas s'éloigner » est celle du joueur du compagnon depuis `9155835` (D14) ; « ne pas vagabonder »
  regarde encore le jeu qui simule (la laisse est rejouée chez l'host depuis `8f39634`). Domptage à la brosse : le jeu
  compare
  l'animal au charisme de `EClass.pc`, donc à celui de l'host même quand c'est un invité qui brosse.
- Gardien du monde (`1b0f5c3`, `856d878`) : c'est l'host. Pas fait : les boucles à l'intérieur de `GameDate`
  (aventuriers, quêtes d'histoire ajoutées à date fixe), le passage du rôle à un autre joueur.
- Elin Together Server : les boutons du logiciel sont joués par `server_ui_test.ps1` (2026-10-04, 15/15 sans Elin et
  6/6 avec Elin : Put this save, les trois boîtes de confirmation, port pris, Start/Stop). **Pas joué** : un vrai
  choix de dossier dans « Browse… » (le test l'ouvre puis annule) et le message « The server could not start: … ».
  Les boutons Oui/Non des boîtes et le choix de dossier restent dans la langue de Windows. Le dépôt n'est
  pas chiffré : mot de passe en clair sur le réseau, à réserver à un réseau de confiance ou privé. Le jeu
  s'arrête le temps qu'un monde voyage (quelques dixièmes de seconde pour 74 Ko ; plus pour un gros monde).
- Serveur (`Emp/EmpServer.cs`, mode avec Elin) : testé entre deux fenêtres de ce PC, serveur et joueur sur le même compte
  Steam. **Pas testé** : entre deux PC (le mode sans Elin l'a été, voir plus bas), par Internet (port 55556 UDP à ouvrir ou réseau privé), avec un second
  joueur, et **avec le même compte Steam sur deux PC à la fois** (Steam peut refuser de lancer le jeu sur le
  second PC tant qu'il tourne sur le premier). Un joueur qui va sur la carte d'un autre joueur le rejoint par
  Steam, pas par l'adresse du serveur. Le personnage de l'host de la sauvegarde reste planté à la base.
- **Premier essai entre deux PC (2026-10-04 soir)** : même réseau local, serveur sans Elin (TCP 55557) sur le
  Steam Deck, joueur sur un autre PC. Le bouton « Join by address » ne parlait alors qu'à un serveur de jeu
  (mode avec Elin) : rien ne répondait et le jeu montrait la clé brute `emp_ui_timeout`. Contournement qui a marché :
  réglage « Depot » = `adresse:55557` puis bouton « Take the world… » : connexion et prise du monde réussies.
  Corrigé par `018091d` (un seul bouton pour les deux serveurs). Le mode sans Elin a donc été joué une fois
  entre deux PC sur un réseau local. **Pas encore essayé** : par Internet, le mode avec Elin entre deux PC, un
  second joueur qui rejoint par Steam, l'hébergeur qui part. Le message du mot de passe faux est fait (`899b221`).
- **Trous du parcours du premier joueur, corrigés le 2026-10-04 au soir** (commits `ab57854` et « the server
  path », détail dans `MODLOG.md`) : une partie neuve remplace le monde du serveur quand personne n'héberge ; après
  « Put this save on the server » le jeu recharge le monde depuis le serveur ; un monde remplacé est gardé en
  `replaced-<date>.zip` et les sauvegardes de secours sont au plus une par 30 minutes ; le logiciel demande avant
  de s'arrêter ou de remplacer un monde ; le mot de passe est vérifié avant de réserver la mémoire ; l'hébergeur
  est prévenu quand ses sauvegardes n'arrivent plus (`Save\world_depot.unsent`, envoi proposé ensuite) ; le deuxième
  joueur est guidé (rejoindre par Steam, attendre jusqu'à 3 minutes) ; le mode avec Elin affiche « The server could
  not start: … » (sauvegarde sans base, session qui ne s'ouvre pas). Tests : `depot_proto_test.py` 11/11,
  `depot_suite` dossier 13/13, avec `DEPOT_SERVER=1` 20/20, `server_suite` 9/9. **Pas testé** : le mode avec Elin
  sur une sauvegarde sans base ; un port UDP déjà pris n'est pas détecté (côté Steam ; côté TCP du logiciel sans
  Elin, la boîte « Port N is already in use on this PC. » est jouée par `server_ui_test.ps1`).
- **Passe large sur le code final (2026-10-04, `2dba2fd`)** : 22 suites, 19 vertes au premier passage ; les trois
  échecs : `server_suite` (erreur « Steamworks is not initialized. » à la fermeture, vient du jeu/Heathen, pas du
  mod ; ignorée par `scan_logs`, `7a4c2d1`, 9/9), et deux **tests fragiles** à cause non établie, verts au
  deuxième passage : `leave_suite` L2 (l'host revenu à 1 case de l'invité) et `time_suite` W3 (faim 31 → 31 après
  le saut de 5 heures, marge d'un point). Non rejouées : `trio_suite` et shared/economy/combat/party.
- Machine de développement (2026-10-04, dépassé à 19h30 : le jeu de cette machine a un build de TEST plus récent que la
  version publiée 0.26.463 ; `dev/build.ps1` avant tout test, `Installer.bat` du zip avant de jouer avec quelqu'un) : le jeu avait la version
  **publiée 0.26.442** (build Release) ; lancer
  `dev/build.ps1` avant tout test. Le logiciel serveur de l'utilisateur dans `Documents\ElinTogether-independance\`
  est encore celui de la 0.26.390 (en français) : à remplacer par celui du nouveau zip.
- Quêtes « Dummy » (description « Mokyu ») vues par l'utilisateur sur son serveur : **ni le mod ni le serveur**.
  Le monde venait de sa sauvegarde du nuage Steam `world_3`, où 6 quêtes étaient déjà écrites `QuestDummy`
  (identifiants `dmp_quest_*` : voyage, massacre_religion, haltérophilie) : des quêtes d'un autre mod, absent du
  Steam Deck. Elin fait cela lui-même quand il ne retrouve pas le type d'une quête à la lecture. Les quêtes du jeu
  sont intactes. L'utilisateur prend une partie neuve pour le serveur. Question ouverte : quel mod fournit
  `dmp_quest_*` (une réparation serait possible, le vrai identifiant est encore dans la sauvegarde).
- Dépôt de sauvegarde (`SaveDepot.cs`) : le verrou est une date de fichier (`host.txt`, rafraîchi chaque
  minute, périmé après trois) : deux joueurs qui prennent le monde dans la même minute l'ont tous les deux, et
  la dernière sauvegarde gagne. Quand celui qui héberge part pendant que d'autres jouent, ils retournent à
  l'écran titre et l'un d'eux reprend le monde du dépôt (pas de relais sans coupure). Pas essayé sur un vrai
  dossier synchronisé entre deux PC (délai de synchronisation), seulement entre deux fenêtres.
- D'autres mods du joueur peuvent mal vivre une session (le jeu d'un client est remplacé à chaque carte) : une
  garde existe pour Somewhat Enhanced Display (`Patches/Compat/OtherModsCompat.cs`), à étendre au cas par cas.
- Joué une seule soirée entre deux PC par Steam (2026-10-02) ; elle a trouvé le blocage de l'host après une nuit
  sur une carte sauvage, corrigé depuis. Le reste a été vérifié en local.
- Temps du monde : une seule date depuis `a76d6a9` (case `SharedWorldTime`). C'est encore le jeu de l'host qui
  fait ce qui se passe à chaque heure et à chaque jour (météo, quêtes, factions, expédition). Pas testé : deux
  joueurs qui tiennent chacun une carte, un joueur qui tient une carte avec des visiteurs, trois joueurs.

- **Décisions du conseil, 2026-10-04 au soir (branche `fix/points-restants`)** : chaque joueur reçoit une fois le
  familier et l'artefact de son dieu ; la prime de la guilde des guerriers va au joueur derrière le tueur ; un
  invité qui meurt chez l'host après le jour 90 perd une part de son or comme un joueur seul (elle tombe par
  terre : n'importe qui peut la ramasser) ; un piège et une lecture de grimoire ne sont tirés que dans le jeu du
  joueur concerné. Limites : sur une lecture ratée par un invité, la confusion et les monstres n'arrivent pas ;
  un piège de malédiction ou d'acide n'abîme l'équipement que dans le jeu de l'invité (pas vérifié) ; un invité
  qui prie seul en voyage puis chez l'host pourrait recevoir un cadeau deux fois (pas vérifié) ; la carte au
  trésor creusée par un invité sur la carte du monde avec l'host est corrigée mais **pas vérifiée en jeu**.
  Aussi : bénédiction du dieu d'un invité calculée comme celle d'un joueur ; les autels (invention, soin…)
  servent celui qui les touche, sauf les deux qui ouvrent une fenêtre (matière, armure).

- **Les trois lots de la nuit validés (2026-10-05, 0h25 → 1h05, branche `fix/points-restants`)** : gestes tenus
  en main rejoués chez l'host (`8f39634`, `guest_suite` G33–G39 : 98/98) ; abattage, appel à l'aide, dieu quitté
  et source chaude (`299c8bd`, `cf4797d`, `e9824ee`, `8e413a8`, `equal2_suite` en entier vert) ; quêtes à donjon
  à deux, l'host a la quête (`3eaedf8`, `together_suite` T1–T6 : 18/18). Pas fait : les effets du puits sur le
  potentiel et les mutations comparés entre les deux jeux ; un test d'un refus ; la portée de 2 cases ne regarde
  pas les murs ; le tirage du vœu du puits par l'invité s'ajoute à celui de l'host. Quêtes à donjon à deux : le
  test prend la quête et sort par les appels du jeu, pas par le dialogue ni en marchant ; pas de test pour « pas
  de boîte si l'autre a déjà une quête à donjon ou un échange » ; la boîte reste ouverte si la connexion tombe.
  La colère du dieu quitté est au tarif de base chez l'host. **À jouer à deux vrais joueurs** : l'host prend une
  quête à donjon, l'invité répond Oui à la boîte, puis une fois Non.

- **Étapes B et C (2026-10-05, 1h05 → 2h45, branche `fix/points-restants`)** : quêtes à donjon à deux dans le sens
  « l'invité a la quête » (`26756bf`, `together_suite` T1–T11 : 107/107) ; chasse aux différences, neuf commits de
  correction (`392266d`, `3d27d3f`, `f4c5b44`, `ea93c88`, `f00f5a6`, `f63a879`, `9046034`, `15d6e05`, `3ccad87`),
  `hunt_suite` D1–D11, un test rouge puis vert par point (les 28 lignes et leur état : `PLAN_chasse_differences.md`).
  Pas joués : le pinceau (le banc ne voit pas son mode), le vol à la tire (l'host peut encore avancer vers la
  victime pendant un vol), investir dans une ville, les runes d'arme à distance, un refus de rune, le vrai glisser dans
  la fenêtre de rune, le parchemin de retour (`world_lab` n'a pas de destination connue). Limites des quêtes à deux :
  voir plus haut. Non-régression large (`run_short.sh`) pas refaite depuis. **À jouer à deux vrais joueurs** en plus :
  l'invité prend une quête subjuguer, l'host répond Oui, puis une fois Non. Pièges : ne pas compiler pendant qu'un
  agent écrit dans le même dossier (travail à moitié fini dans la DLL : worktree propre) ; une zone créée par l'host
  « sans annonce » n'est jamais connue du client ; `ModCurrency` chez un client est une demande, pas un solde ; ce que
  fait l'host en appliquant le tick d'un autre joueur n'est pas envoyé (`ElinDelta.Simulate()`).

- **Version 0.26.442 et étape D, premier lot (2026-10-05, 2h45 → 9h30, branche `fix/points-restants`)** : publiée
  vers 9h25 (`f096255`), `feat/independent-travel` poussée sur GitHub (même commit). Dans la version : consigne « ne pas
  s'éloigner » propre à chaque joueur (`9155835`, D14) ; karma d'un visiteur chez un teneur de carte (`927f342`) ;
  recherche
  et compétences du foyer refusées pour un invité (`06a0f94`, `base_suite` 53/53) ; échange plus strict (`9cd8062`,
  `trade_suite` 122/122) ; tri du sac (`5ffa169`) ; messages « déjà vendu » et de retour de l'host (`211658e`) ; chasse
  :
  pied-de-biche (D13), noyade, ticket d'hôtesse, fenêtres d'alias / retour du vide / caisse de ferme. **Pas joués** :
  karma d'un visiteur, tri du sac, les deux messages, noyade, ticket d'hôtesse, les trois fenêtres. Non-régression,
  chaque
  suite sur un jeu relancé (`run_short.sh`) : equal2 35/35, together 107/107, death 11/11, parity 15/15, sleep 32/32,
  recruit 45/45, quest 59/59, instance 32/32, trade 122/122, hunt D1–D14, base 53/53, guest 317/317, leave 13/13, travel
  54/54, council vert. **Non relancées** : `shared_suite`, `trio_suite`, `companion_suite`, les suites du serveur.
  Limites : les étapes de dialogue « acheter des plans » et « améliorer le foyer » n'existent dans aucun dialogue du jeu
  installé ; lit, étiquettes de vente, notes et politiques réglés par un invité ne valent que sur son écran ;
  `run_short.sh` ne lance pas `travel_suite` ni `shared_suite`. Un test qui dépend d'un tirage du jeu peut échouer une
  fois (C5, D3 : corrigé). Habitude : pousser `feat/independent-travel` après chaque lot validé ; publier demande
  l'accord de l'utilisateur.

- **Étape D suite, Elin 23.352 (2026-10-05, 9h30 → 14h15, branche `fix/points-restants`)** : poussée sur GitHub après
  chaque lot ; **pas de nouvelle version publiée** (dernière : 0.26.442, compilée pour 23.351). Faits et testés :
  monture déjà prise refusée (`31faaac`, U6) ; notes, étiquettes, lits (`eccc52a`, S1–S3) ; recherche et compétences
  du foyer en vraies demandes à l'host (`b559952`, `base_suite` B1 20/20, B4) ; « ne pas vagabonder » par joueur
  (`0b48902`, D14 17/17) ; politiques (`e3b4de3`, S4) ; noms de la base, de la faction, d'un téléporteur (`ed99a6b`,
  S5–S6, `setting_suite` 25/25) ; **don d'un objet pris dans une pile par un invité : n'arrivait jamais chez l'host,
  corrigé** (`7cd9db2`, `unplayed_suite`) ; quêtes de récolte et de musique de l'invité à deux (`af18078`, T12, T13).
  Deuxième chasse aux différences : `PLAN_chasse_differences_2.md`, 37 lignes lues dans le code, rien de joué (liste de
  travail de l'étape E). **Barrière de version** (`ee374b7`, 14h) : seul le mod doit avoir la même version, Elin différent = avertissement,
  case côté host pour le contrôle strict (`version_suite` 8/8 en local). **Pas joués** : retenue de « ne pas vagabonder », nom de faction, score d'un concert, U2, U4,
  U7. Constat : un joueur peut « monter » un autre joueur sur la même case (comportement du mod d'origine). Pièges :
  panne de mémoire du banc après ~30 minutes sur les mêmes fenêtres (relancer le jeu entre les grandes suites) ;
  `mp_test.py` bloqué à « connexion demandée » (relancer) ; menu « buy » du jeu qui se referme sans souris ;
  `taskkill /PID <n> /F` depuis PowerShell (pas `Stop-Process` par bash avec `\$_`). Détail : `MODLOG.md`.

- **Depuis la 0.26.463 (2026-10-05, 15h40 → 19h30, branche `fix/points-restants`, 20 commits poussés sur
  `feat/independent-travel`, dernier `1d698a5`)** : mode construction d'un invité (conseil 5, étapes 1 à 7), terrain, zones
  et hauteurs, réglages de coffre, duel d'autel, prière sans dieu, jours et heures de l'invité, résurrection d'un
  compagnon, copie chez Kettle, outils et fouets, un joueur ne tue plus un joueur, dépôt GitHub (tableau de la section 1).
  Chaque lot a son test, rouge vu d'abord quand le message du commit le dit ; ce qui est écrit « pas joué » n'en a pas. **Rien de cela n'a été
  joué à deux PC, ni publié en version.** Les suites larges de non-régression sur ce build (`run_short.sh pub2`, 13 suites) ont
  été lancées à 17h : leur résultat n'est pas consigné ici (journaux `_shots/*-pub2.log`) ; `travel_suite` seule reste
  à lancer ; `shared_suite`, `trio_suite`, `companion_suite` et les suites du serveur : non relancées.
  - **Mode construction d'un invité, pas joué** : objet du stock ou du sac posé par le menu, pont, glisser sur
    plusieurs cases, creuser, mode rampe, case `GuestBuild` décochée, carte tenue par un invité. **Encore refusés avec
    un message** (dit par `b2a6f16`, pas revérifié depuis) : plans de construction, mode toit (Alt). Les marques « miner / couper / creuser » ne sont pas
    envoyées aux habitants de l'host (personne ne les lit : `GoalTask` n'est créé nulle part).
  - **Terrain, pas couvert** : récolte (la marque seulement est jouée, pas les objets créés), sol tourné (`RotateFloor`,
    `RotateObj`) ; le pinceau d'outil de terrain est joué par un seul coup, pas par un glisser bouton enfoncé ; le sens du
    pinceau est réglé par la variable, pas par le bouton du sous-menu ; la zone de base est celle de l'onglet « area »,
    l'effacement est le corps du bouton, pas le menu ; nom et accès sont posés dans les données, pas par les boîtes.
  - **Réglages de coffre, pas joués** : la boîte de saisie du filtre, le bouton de collage, les boutons d'autodump.
  - **Duel d'autel** : ne prouve pas un pair d'une ancienne version (graine absente), ni le glisser d'un artefact au clavier ;
    le glisser à la souris est remplacé par le dépôt, le dieu de l'autel est posé par le test.
  - **Résurrection** : parchemin et sort **pas joués** ; le clic sur la ligne du compagnon est celui du bouton.
  - **Kettle** : un coffre de copie par marchand pour tous les joueurs (comme le jeu).
  - **Outils et fouets, pas couverts** : tentes, nouvelle fiche des fouets « passe-temps » et « métier » chez l'invité.
  - **Un joueur ne tue pas un joueur, pas couvert** : saignement, poison, feu, condamnation à mort ; sorts et projectiles
    pas joués (le test utilise le coup de mêlée du jeu, ce que fait Maj + clic).
  - **Pas joués du tout** : prix d'expédition lu avec le dieu du joueur (`445fa5e`), carte à gratter du casino
    (`3459019`). Ligne 36 de la chasse 2 (Mifu, Nefu, Aquli) : à juger, chaque jeu lit le dieu de son joueur, ce que
    verrait un joueur solo.
  - **Dépôt GitHub, ce qui est prouvé** : (1) hors jeu, contre le faux GitHub local : `depot_github_test.py` 66/66 ;
    (2) hors jeu, contre le **vrai** GitHub (dépôt privé d'essai `devmarcpro/elin-together-monde-essai`) :
    `depot_github_real.py` 13/13 ; (3) en jeu, contre le faux GitHub : `DEPOT_GITHUB=1 depot_suite.py` 31/33 ; le dépôt
    « dossier » reste à 13/13. **Limite connue, rouge (G4)** : fermer le jeu pendant un envoi n'attend pas la fin de
    l'envoi ; le verrou n'est alors pas rendu et expire de lui-même après 3 minutes (un autre joueur ne peut pas prendre
    le monde avant). La suite attend le contraire (que le jeu attende la fin de l'envoi) : c'est elle qui est rouge,
    et c'est le défaut du mod, pas du test. Ce que devient alors la dernière sauvegarde : pas vérifié. **Pas joué** : le vrai GitHub depuis l'intérieur du jeu (le TLS
    de Mono, la première demande qui prend environ 7 s, la limite de débit de GitHub, la pause entre deux écritures) ;
    deux PC ; la fermeture brutale du jeu pendant un envoi (`taskkill`) ; le texte d'aide suivi avec une vraie clé
    créée à la main ; un dépôt tout à fait vide sur le vrai GitHub (le test réel accepte « vide » ou « pris ») ; la
    clé expirée ; la croissance réelle du dépôt (72 Mo par soirée : un calcul). La suite en jeu n'est pas jouée comme un
    joueur : dépôt et clé posés par le pont (pas par l'onglet), « prendre » et « mettre » sont les fonctions du mod
    (pas les boutons), les sauvegardes sont `EClass.game.Save`, l'attente de 5 minutes est court-circuitée, la fermeture
    est `Application.Quit()`, le texte exact des boîtes n'est pas lu. Pièges : une clé « fine-grained » ne vise
    peut-être que les dépôts de celui qui l'a créée (non vérifié) ; la clé est en clair dans le fichier de réglages du mod.
  - **Pièges de la séance** : plusieurs `[HarmonyPatch]` sur une même méthode ne font pas plusieurs cibles (utiliser
    `TargetMethods`) ; dans un test, compter une matière « avant / après » et pas en absolu ; `Area.Create` veut un
    identifiant de `sources.areas` (« Stockpile »), pas « public » ; le premier appel HTTPS du jeu prend 7 s ; le JSON du jeu
    numérote ses objets à neuf à chaque appel (ne pas comparer deux états par lui) ; `_decomp` a été refait pour 23.352
    (l'ancien est dans `_decomp/Elin_23351`) et `ilspycmd.exe` ne dit rien et ne fait rien sans
    `DOTNET_ROLL_FORWARD=LatestMajor` et `DOTNET_ROLL_FORWARD_TO_PRERELEASE=1`.

## 7. Reste à faire

### Mise à jour du 2026-10-11 (passe avant tout ce qui suit)

La liste à jour est en haut de `HANDOFF.md` (« État au 11 octobre 2026 »). En bref : rien n'est publié depuis la
0.26.621 ; à faire : les autres « une fois par monde » (`PLAN_une_fois_par_monde.md` : récompenses des quêtes
d'histoire, cadeaux de dialogue, guildes), les bugs de compagnons (pas de détail donné), le journal par joueur, les
factures fantômes des mondes déjà touchés, l'ancien host qui revient (R6) et le dépôt en bonus (R7), le joueur refusé
par le teneur d'une carte, l'expérience « de groupe » de l'host, le dépôt GitHub affiché comme un fork.

### Mise à jour du 2026-10-06, 22h30 (la 0.26.524 n'a JAMAIS été jouée)

Ce bloc passe avant tout ce qui suit. La liste à jour et l'ordre des suites à jouer sont dans `HANDOFF.md`, « État au 6 octobre, 22h30 ».

**Limites de la 0.26.524 : elle est écrite, relue, compilée en Release et en Debug, et rien n'a tourné en jeu, pas même les suites écrites ce soir.**
Seule la partie réseau en morceaux a été vérifiée, hors jeu (`chunk_check`, 20 vérifications). Chaque sujet ci-dessous a son plan avec les « pas sûr ».
- **Désynchronisation** (`PLAN_desync.md` et les trois plans liés) : le détecteur peut donner un faux positif sur une vraie carte habitée (à lire d'abord avec la case décochée) ; les sacs en écart ne sont pas réparés ;
  l'host ne vide pas sa file avant de copier la carte demandée ; le passage de main d'un invité à un autre invité garde l'ancien défaut ; D6 (aléatoire rejoué) et D9 (plages de numéros) seulement si les journaux les montrent ;
  le rechargement d'une carte pendant une fenêtre ouverte ou un combat n'a jamais été vu ; la taille réelle des messages n'est pas mesurée. Host et invités doivent avoir la même version du mod.
- **Boss de donjon** : cause lue, jamais vue ; la victoire d'un invité n'est pas transmise à l'host ; chez un invité sur la carte de l'host le boss n'est pas reconnu comme boss à sa mort (pas de fanfare).
- **Nuit** : la fenêtre pour « dormir ensemble » est celle de l'écran de nuit du premier couché (quelques secondes, non mesurée) ; un joueur parti ailleurs et ses messages de sommeil n'ont jamais été joués ; saignement, poison et miasme retirés au coucher : host seulement.
- **Date** : un invité ne fait jamais avancer la date (inégalité host/invité) ; l'avance rapide d'un joueur accélère encore tous les autres ; les transpileurs du pas sur la carte du monde se replient avec un avertissement si le jeu change.
- **Rangement, factures, banque** : le test d3b dira si la ceinture et la main étaient vraiment la cause ; l'impôt sur la renommée la plus haute n'est pas fait ; la banque garde une fenêtre de perte (lien coupé avant l'accusé) ; une facture payée par un invité compte sur l'or « gardé » par l'host, en retard possible.
- **Solo et salon** : S8, S10, C1 à C8 de `PLAN_joueur_seul.md` ne sont pas faits ; le salon Invisible ne se prouve qu'avec deux comptes Steam ; la preuve du dépôt (HMAC) pour un joueur qui n'a jamais joué le monde n'est pas écrite.
- **Lenteurs** : compression rapide des cartes, A5, B5, B2, B1/B6 et l'objet `perf` du pont de test restent à faire ; rien n'est chiffré.
- **Reprise automatique quand l'host part ou plante** (conseil 9, étapes 3 à 5) : pas commencée. C'est la suite prévue « une fois que tout le reste est bon ».
- Suites **écrites et jamais lancées** : `desync_suite`, `resync_suite`, `travel_suite` (s18, s19), `bank_suite`, `pickup_suite`, `sleep_suite` (n1 à n6, k1), `trio_sleep_suite`, `time_suite` (W7 à W9), `trio_place_suite`,
  `bills_suite`, `hunt_suite` d3b, `solo_suite`, `depot_suite` D8 ; outils `world_diff.py`, `perf_probe.py`. Détail et rouges connus : `MODLOG.md`, entrée du 6 octobre « de 18h à 22h30 ».


### Mise à jour du 2026-10-05, 19h30 (ce qui est décidé et pas fait)

Ce qui suit passe avant les listes plus bas, qui datent de 14h15 et du 2026-10-04 : elles restent écrites pour mémoire.
Faits depuis : voir le tableau de la section 1 (lignes « depuis la 0.26.463 »). Dans la deuxième chasse
(`PLAN_chasse_differences_2.md`), les lignes 1 à 11, 25, 26, 30, 33 et 34 sont corrigées (26 et 30 : pas jouées) ;
**restent** les lignes 12 à 24, 27 à 29, 31, 32, 35 et 37, et la 36 « à juger ».

- **Conseil 6 : où vit le monde partagé** (2026-10-05, 16h40 ; faits dans `PLAN_depot_steam.md` et
  `PLAN_depot_github.md`). **Pas commencé.** Verdict : (P) **une copie du monde chez chaque joueur, envoyée par Steam,
  par défaut** ; (G) GitHub en option (c'est le dépôt GitHub de la section 3, fait à part) ; le Workshop est écarté
  (pas de verrou, délai inconnu, objet retirable). Une copie qui descend de l'autre la remplace sans question ; si
  les deux mondes ont vraiment divergé, l'invité reçoit un Oui/Non (« vos mondes ont divergé depuis le …, rejoindre
  celui de X ? ») et sa copie va dans « écartées » (trois au plus) ; une lignée perdante n'est jamais supprimée. Ordre
  de livraison, chacun un test rouge puis vert à deux fenêtres : 1 `world.version` (compteur, empreinte, empreinte
  parente) à chaque sauvegarde ; 2 envoi du zip aux invités (au plus un par 5 minutes et à la sortie, `.part` puis
  renommage) ; 3 « héberger ce monde » chez l'invité (il joue SON personnage, or et sac de l'absent identiques) ; 4 retour
  de l'ami (copie descendante reçue sans question) ; 5 divergence (Oui/Non) ; 6 avertissement avant d'héberger seul.
  **Première chose à faire, sans code : vérifier que l'invité qui prend le monde joue son personnage et pas celui de
  l'host** (`SaveDepot.Take` fait `Game.Load("world_depot")` et rien d'autre ; non vérifié en jeu : si l'invité se
  réveille dans le personnage de l'ami, cette réparation devient l'étape 1). Deux fenêtres ne prouvent pas un relais
  par Steam : un essai réel avec un ami reste dû.
- **Conseil 7 : duels entre joueurs** (2026-10-05, 17h40 ; faits dans `PLAN_duels_et_membres.md`). Décidé : duel sur
  place d'abord ; « aucune perte », pas de renommée perdue, les deux sont soignés à la fin ; compagnons présents, PV
  plafonnés, ils ne combattent pas ; pari en or seul (0 / 100 / 1 000 / tout), plafonné au sac le plus pauvre, montant
  dans la boîte Oui/Non, rendu aux deux en cas de déconnexion ou de plantage, seul le bouton « Abandonner » perd la
  mise ; coups mortels entre joueurs bloqués hors duel, case `PlayerKill` ; potions, flèches et charges utilisées en
  duel restent dépensées ; faim, piège et poison tuent toujours. **Étape 1 faite** (`ca8d009`, `duel_suite` P1, section 1).
  **Étapes 2 à 7 : à faire** : 2 menu « Défier », boîte Oui/Non, case « Duels » ; 3 duel sur place (fin au plancher, soin
  des deux, compagnons plafonnés) ; 4 départ, déconnexion, double défi : fin sans gagnant ; 5 invité contre aventurier
  (état des lieux : un demi-état est possible, jamais joué) ; 6 arène (zone créée par l'host, retour de chacun sur
  sa case, zone détruite ; refusée si aucun duelliste n'est l'host) ; 7 pari + case « Paris ». Le chargement de
  l'arène n'est pas prouvable sur un seul PC. Certains sorts de zone épargnent les alliés : ils ne toucheront peut-être
  pas l'adversaire en duel (à mesurer). Écarté : option 4 (trois fenêtres), compagnons combattants, forfait sur
  déconnexion, plafond dur du pari, compteur de victoires.
- **Conseil 7 : base gérée par un invité** (même séance). Décidé : option (a) = tous les joueurs ont tous les droits sur
  toutes les bases, avec une case « seul l'host gère la base » (décochée, séparée de `GuestBuild`) ; abandonner la base
  pour de bon : refusé à l'invité (seule inégalité acceptée, perte irréversible) ; renvoi et réserve d'un résident :
  ouverts à tous, faits une seule fois par l'host avec un message à l'autre joueur. Écarté : membres par base, base par
  joueur (données nouvelles dans la sauvegarde). Ordre : 1 R6 (acte de propriété, sans code) ; 2 abandon refusé ;
  3 servante ; 4 type de résident, réserve, rappel ; 5 renvoi ; 6 réglages de coffre (**fait**, `57d5d3e`) ; 7 case
  `HostManagesBase`. **État : écrit et en test, pas encore commité** (copie de travail : `BaseRequestKind` `Maid`,
  `MemberType`, `Reserve`, `Recruit`, `Banish`, `RemoteResidentPatch.cs`, case `HostManagesBase`, clé 14, `base_suite.py`
  agrandie). Je n'ai pas pu vérifier dans cette copie où en sont R6 et le refus de l'abandon : à lire dans le code avant de
  les croire faits.

État au 2026-10-05, 14h15 (liste plus ancienne, voir la mise à jour ci-dessus). **La liste à jour, dans l'ordre, est « À faire ensuite » de `HANDOFF.md`** (branche de
travail `fix/points-restants`, au même commit que `feat/independent-travel` ; `wip/lots-non-compiles` est en retard ;
quêtes à donjon à deux :
`PLAN_quetes_donjon_a_deux.md` ; autres différences trouvées : `PLAN_chasse_differences.md`) ; ce qui suit date
du 2026-10-04 à 22h et reste un résumé. Détail de chaque point : `PLAN_retours_partie_reelle.md` et la fin de
`MODLOG.md`.

**Fait (voir le tableau de la section 1 et `MODLOG.md`, 2026-10-03 et 2026-10-04) :** les cinq corrections de la
première vraie partie ; déplacements fluides d'un invité (`move_suite`) ; rejoindre avec un personnage d'une
sauvegarde solo (`import_suite`) ; compagnons d'un invité (`recruit_suite`) ; une seule date pour le monde
(`SharedWorldTime`) ; gardien du monde (`WorldKeeper`) ; dépôt de sauvegarde ; serveur « comme Minecraft » ;
**Elin Together Server**, le logiciel (en anglais) ; un seul bouton « Join by address » pour les deux serveurs ;
mot de passe faux dit clairement ; trous du parcours du premier joueur corrigés (section 6) ; passe large sur le
code final (22 suites) ; boutons du logiciel serveur essayés par `server_ui_test.ps1` ; **version 0.26.399
publiée** (2026-10-04). Premier essai entre deux PC du serveur sans Elin sur un réseau local : réussi (section 6).
Nuit du 5 octobre : gestes tenus en main rejoués chez l'host, abattage, appel à l'aide, dieu quitté, source
chaude du groupe, quêtes à donjon à deux dans le sens « l'host a la quête » (boîte Oui/Non) : validés, un commit
par point (section 6, `equal2_suite`, `together_suite`, `guest_suite` G33–G39). Matin du 5 octobre : quêtes à
donjon à deux dans l'autre sens (l'invité a la quête, `26756bf`) ; chasse aux différences, 12 lignes jouées (10
corrigées, 2 fausses) dans `hunt_suite` D1–D11. 5 octobre, 9h30 : **version 0.26.442 publiée** et premier lot de l'étape
D (consigne des compagnons, karma d'un visiteur, base refusée à l'invité, échange plus strict, messages ; section 6).

**À faire tout de suite, dans l'ordre :**
1. fait : `depot_suite` avec `DEPOT_SERVER=1` relancé, 20/20 ;
2. fait : la passe large de régression sur le code final (section 6 pour les résultats et les deux tests
   fragiles) ;
3. fait : les boutons du logiciel essayés par un test (reste « Browse… » avec un vrai choix de dossier et le
   message « The server could not start: … ») ;
4. fait : version 0.26.399 publiée, puis 0.26.442 (2026-10-05) mise dans le jeu de cette machine (`dev/build.ps1` avant
   tout test) ;
5. sa soirée d'essai réelle avec la 0.26.442 (point 1 de la liste suivante, et la liste d'essais de `HANDOFF.md`) :
   l'ami installe le même zip, et
   l'utilisateur remplace le logiciel serveur de `Documents\ElinTogether-independance\` par celui du zip ;
6. savoir quel mod fournit les quêtes `dmp_quest_*` (réparation possible) ;
7. comprendre les deux tests fragiles (`leave_suite` L2, `time_suite` W3) s'ils reviennent.

**Ensuite, dans cet ordre sauf avis contraire de l'utilisateur :**
1. Essais réels qui restent : serveur par Internet (avec mot de passe), mode avec Elin entre deux PC, un deuxième
   joueur qui rejoint par Steam, l'hébergeur qui part.
2. Relais sans coupure quand l'hébergeur part du serveur sans Elin (`PLAN_serveur_depot.md`, étapes 3 et 4). Gros.
3. Petites améliorations du logiciel, seulement s'il les demande : plusieurs mondes, chiffrement (TLS) du mot de
   passe, journal visible, icône. Idée notée : le deuxième joueur rejoint l'hébergeur tout seul depuis « Join by
   address » (le serveur donnerait l'identifiant Steam de l'hébergeur ; il faut deux comptes Steam pour tester).
   Idée notée (2026-10-04, pas commencée, à lui demander) : **serveur sur un NAS Synology**. Mode sans Elin
   seulement. (a) Tout de suite, sans rien écrire : un dossier partagé du NAS comme dépôt (réglage « Depot » du jeu
   = chemin du dossier, mode dossier testé par `depot_suite` 13/13 ; réseau local ou réseau privé comme
   Tailscale ; pas d'adresse dans « Join by address »). (b) À écrire : une version **sans fenêtre** du serveur de
   dépôt (le logiciel actuel est un programme Windows .NET Framework à fenêtre) : un script Python d'environ 150
   lignes, ou Docker, testable par `depot_proto_test.py`. Le mode avec Elin ne peut pas tourner sur un NAS.
4. À ne commencer qu'après lui avoir demandé : retour de l'host sans rechargement (plan B), **profil de mods**
   (`PLAN_profil_mods.md`), touche « signaler un problème » en jeu, bot qui rejoue une vraie soirée, faux réseau lent.
5. Quêtes à donjon à deux : fait dans les deux sens (`3eaedf8`, `26756bf`), récolte et musique de l'invité aussi
   (`af18078`). Reste : la défense (sens « l'invité a la quête »), les jouer par le vrai dialogue, la déconnexion
   dans la zone, trois joueurs.
5 bis. **(Liste de 14h15 : republier sur 23.352 est fait, 0.26.463 ; les lignes 1 à 11 de l'étape E sont faites ; voir la mise à jour de 19h30.) Dans l'ordre (`HANDOFF.md`, état à 14h15)** : jouer la **barrière de version** (faite, `ee374b7` : seul le
   MOD doit avoir la même version, avertissement si Elin diffère, case côté host pour le contrôle strict) ;
   republier une version compilée sur 23.352, avec l'accord de l'utilisateur ; **étape E** =
   `PLAN_chasse_differences_2.md`, lignes hautes d'abord (1 mode construction d'un invité, 2 tailler un rondin) ; ce
   qui reste du conseil 4 (servante, type et réserve d'un résident, réglages de coffre, mesure du rechargement au
   retour de l'host) ; défense à deux ; fin de la première chasse (8 machine à gènes, 17, 25 à 28, tombe d'épée).
   Écrire des tests pour tout ce qui est « pas joué ».
6. Inégalités invité/host qui restent (`PLAN_egalite_invites.md` : M14 (en partie : recherche et foyer en demandes à
   l'host, politiques, lits, noms),
   mutation
   en double ; consigne « ne pas s'éloigner » et karma sur la carte d'un invité faits au 5 octobre ; M3, M5, M9, L1, L7,
   M13, L4, L5, L6, L8, L9, laisse et appel à
   l'aide sont corrigés).
7. Deux choix de jeu en attente : que faire quand un joueur meurt sur la carte de l'host ; quand la connexion tombe.
8. Jouer le début de l'histoire en vrai avec un client ; conflits rares listés dans les limites.

## 8. Historique du fork

| Commit | Contenu |
|---|---|
| `2d68eae`, `c15331f` | voyage indépendant (baux de zone) |
| `f77c916` | points de sauvegarde et chat en voyage |
| `1781eea`, `8f73f01` | plusieurs fenêtres de test sur un seul compte Steam |
| `ae5ab37` | cartes partagées et passation |
| `573e74b` | compagnons par joueur |
| `c16ddad`, `fd04af5` | options, expédition et combat par joueur, limite d'alliés |
| `1e1be22` | l'host ne traîne plus les joueurs, quêtes en voyage |
| `cde3425` | quêtes d'histoire et souvenirs de dialogue communs, correction 3 joueurs |
| `dbc7fa4` | équipement ajouté et équipé au même instant |
| `7dd32ec`, `0a77c9d` | bot lancé depuis le menu |
| `23f4eee`, `70ff98d` | objets et effets des dialogues d'histoire, échec de quête |
| `254974c` | quêtes aléatoires, renommée et karma par joueur |
| `53bd50d` | choix du personnage à la connexion |
| `85a08db`, `933330b`, `d944576` | objets en double, deux joueurs sur la même chose, numéros en double |
| `4ca15eb`, `36eccb3` | changements de carte : entrées bloquées, messages gardés, banque en voyage |
| `596f380` | quêtes à donjon pour tous |
| `23fd93b` | affinité et guildes communes |
| `b730280`, `a50f081` | fenêtre d'échange entre joueurs |
| `f247883` | karma et crime par joueur, prime des quêtes de défense |
| `4edfd63` | corrections de la relecture (échange, zone de quête, étages loués) |
| `307f897`, `853018f` | règlement des quêtes à donjon, écran « Server Setting » en sections |
| `388fae3` | build de développement sur un jeu jamais lancé |
| `a6819f1` | nouveau joueur bloqué à la création du personnage (objet détruit sous le pointeur) |
| `449c5fa` | joueur sans jeu en rentrant chez l'host avec une quête prise en ville |
| `895d5b0` | version 0.26.463 publiée (Elin EA 23.352) |
| `99c7353`, `1a25661`, `b2a6f16`, `d04114c` | mode construction d'un invité : garde-fou, état des cases, tâches demandées à celui qui tient la carte, zones et outil de terrain |
| `194c6d7`, `445fa5e`, `3459019`, `57d5d3e`, `915e6dd` | prière sans dieu et jours de l'invité, prix d'expédition, carte à gratter, réglages de coffre, duel d'autel |
| `1a89eed`, `cd7d652`, `fccee72` | outils et fouets, résurrection d'un compagnon, copie chez Kettle |
| `ca8d009` | un joueur ne peut plus tuer un autre joueur (case `PlayerKill`) |
| `1d698a5` | dépôt GitHub privé pour garder le monde |
