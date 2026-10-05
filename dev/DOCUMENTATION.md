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
- État : 2026-10-05, 9h30, version 0.26.442 publiée (voir `HANDOFF.md` pour le détail à jour). Dossier de travail :
  `G:\ElinMods`.

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
| Quêtes à donjon à deux, l'invité a la quête (mêmes options, sans case à elle ; `26756bf`) | Quand l'invité accepte une quête « subjuguer » et part, la demande de zone est retenue chez l'host, qui voit la boîte Oui/Non (15 s ; l'invité lit « on demande à X… »). Oui : l'host crée la zone et la simule, l'invité y est un client ordinaire, la quête reste à son journal (l'host la lit sans l'avoir au sien). Quand l'invité sort, tout le monde sort ; la récompense est donnée une fois, à l'invité. L'host peut rentrer seul : la zone passe à l'invité, qui finit seul. Non ou pas de réponse : comme avant, l'invité simule sa zone seul. La sauvegarde de l'host ne contient rien de la quête de l'invité. Seulement les quêtes « subjuguer » : récolte, musique et défense restent en solo pour l'invité. | `together_suite.py` T7–T11 (107/107 avec T1–T6) |
| Chasse aux différences host / invité (5 octobre, `PLAN_chasse_differences.md`) | Un invité sous 20 % de vie ne prend plus peur et peut frapper (`392266d`) ; le guérisseur payant le soigne vraiment, lui et ses compagnons (`3d27d3f`) ; le rangement automatique est propre à chaque joueur : celui de l'invité n'emporte plus les objets de l'host, celui de l'host ne ferme plus les fenêtres de l'invité (`f4c5b44`) ; radio, juke-box, liste de lecture, livres des résidents et de l'équipe, détecteur, roue, vue de carte, pinceau : la fenêtre ne s'ouvre que chez celui qui s'en sert (`ea93c88`) ; l'ecopo de la faucille va à l'invité qui fauche, et son vol à la tire ne coûte plus d'endurance à l'host (`f00f5a6`) ; investir dans une boutique ou une ville arrive chez l'host au lieu d'être payé pour rien (`f63a879`) ; la bénédiction des prêtresses atteint l'invité et ses compagnons (`9046034`) ; une recette lue par un joueur n'est apprise qu'une fois par l'autre (`15d6e05`) ; runes et prises : fenêtre chez l'utilisateur seul, rune posée et usée dans les deux jeux (`3ccad87`). Déjà bons : parchemin d'évacuation, carte au trésor lue. Ensuite (0.26.442) : le pied-de-biche d'un invité force aussi le coffre chez l'host (`fb7a507`, D13) ; sous l'eau profonde l'invité perd son souffle (`cf62040`), son ticket d'hôtesse masse l'invité (`ab73333`), ses fenêtres d'alias, de retour du vide et de caisse de ferme ne s'ouvrent plus chez l'host (`2239dde`) : **pas joués**. | `hunt_suite.py` D1–D14 (D12 saute : pas d'eau profonde sur la carte de test) |
| Gestes tenus en main d'un invité | Ticket de meuble, seringues (gène, sang, paradis, licorne), puits, stéthoscope, laisse : le geste est rejoué chez l'host, l'objet est dépensé des deux côtés. Au puits, le vœu est tiré dans le jeu de l'invité (1 chance sur 21 par gorgée), pas chez l'host. Autres corrections de la nuit du 5 octobre : un invité qui abat un animal ne fait plus perdre l'endurance de l'host ; un habitant ami frappé par un invité appelle ses voisins (dans une ville ; le jeu n'appelle jamais dans une base) ; quitter son dieu punit l'invité ; la source chaude profite à l'invité et à son compagnon, pas à l'host. | `guest_suite.py` G33–G39, `equal2_suite.py` |
| Base réglée par un invité (`06a0f94`, sans case) | La recherche et les compétences du foyer sont refusées chez l'invité avec un message « à régler par l'host » : avant, il payait sans rien obtenir. Les étapes « acheter des plans » et « améliorer le foyer » n'existent dans aucun dialogue du jeu installé (le foyer monte tout seul). Étape suivante, en cours : en faire des demandes vérifiées par l'host. | `base_suite.py` 53/53 |
| Consigne « ne pas s'éloigner » (`9155835`) | C'est le réglage du joueur du compagnon, pas celui de l'host. « Ne pas vagabonder » lit encore le jeu qui simule. | `hunt_suite.py` D14 |
| Karma d'un visiteur (`927f342`) | Sur une carte tenue par un autre joueur que l'host, les gardes voient le karma d'un visiteur : il l'annonce au teneur de la carte, gardé en mémoire seulement, effacé à son départ. | pas joué |
| Messages d'achat et de retour (`211658e`) | Le second acheteur d'un même objet apprend qu'il est parti ; l'invité est prévenu de qui revient sur sa carte avant le rechargement de son écran. Tri du sac propre à chaque joueur (`5ffa169`) : seul le réglage partagé / personnel d'un conteneur de la carte voyage. | pas joués |
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

Les options sont envoyées aux clients à la connexion (`NetSessionRules`). Toute nouvelle fonction doit avoir sa case.

## 3. Installer

**Pour jouer (toi et ton ami, même zip des deux côtés)** : `_release/ElinTogether-independance.zip`, puis
`Installer.bat`. `Desinstaller.bat` remet le mod du Workshop. Refaire le zip : `make_release.ps1`. Le zip n'est
pas dans le dépôt : il se fabrique sur chaque machine.
La dernière version publiée est la **0.26.442** (2026-10-05, préversion `independance-0.26.442`, commit `f096255`),
pour Elin EA 23.351 ; le zip de `_release` est celui de la dernière publication. Il est aussi sur la page des versions
du dépôt (https://github.com/devmarcpro/elin-together/releases) : c'est le lien à donner à un ami. Le jeu de cette
machine a cette version (build Release). La note de version est `NOTE_version.md`, les README des quatre langues ont
8 captures dans `assets/screens/` (prises par `_tools/showcase.py`).
Après un `build.ps1` (tests), le jeu de cette machine n'a plus la version du zip : relancer `Installer.bat`
avant de jouer avec quelqu'un, sinon la connexion est refusée (versions différentes).

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
| Bot du menu | `Emp/EmpBot.cs`, `Emp/EmpBotLauncher.cs` |
| Options | `Emp/EmpConfig.cs`, `Components/Tabs/TabServerConfiguration.cs` |
| Pont de test (Debug) | `Emp/EmpDebugListener.cs` |

Règle à ne pas oublier : chaque type de delta a un numéro (`[Union(n, …)]` dans `Models/Delta/ElinDelta.cs`).
Deux deltas avec le même numéro cassent toute la communication.

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
| `together_suite.py` | quêtes à donjon à deux, dans les deux sens : boîte Oui/Non, entrer, sortir, fouille de l'accompagnant (T1–T6, l'host a la quête) ; l'invité a la quête, boîte chez l'host, récompense, l'host rentre seul, sauvegarde de l'host (T7–T11) ; `--only t7,t8` | 2 | ~16 min |
| `hunt_suite.py` | chasse aux différences host / invité, un test par ligne de `PLAN_chasse_differences.md` : peur, guérisseur, rangement, objets à fenêtre, faucille, investir, prêtresses, évacuation, recette, rune, carte au trésor, pied-de-biche, consigne « ne pas s'éloigner » (D1–D14 ; `--only d1,d3`). Sait dérouler un vrai dialogue (`talk`, `pick`, `hang_up` : choix cliqué par son texte anglais) | 2 | ~10 min |
| `base_suite.py` | base réglée par un invité : recherche et compétences du foyer refusées avec un message, rien de payé (53 vérifications) | 2 | ~4 min |
| `recruit_suite.py` | compagnons recrutés par un invité : dialogue, monture, boule à monstre, achat | 2 | ~5 min |
| `council_suite.py` | les décisions du conseil du 2026-10-04 : grimoires, prime de guilde, cadeaux du dieu, mort après le jour 90, pièges (à Vernis) ; `--only c6` carte au trésor (ne passe pas au banc) | 2 | ~5 min |
| `move_suite.py` | pas de l'invité : réguliers, host qui rame, écart de vitesse, accéléré partagé | 2 | ~2 min |
| `import_suite.py` | rejoindre avec le personnage d'une sauvegarde (copie du monde de test) | 2 | ~3 min |
| `time_suite.py` | une seule date pour le monde : invité seul ailleurs, host, saut de cinq heures, retour | 2 | ~2 min |
| `world_suite.py` | le gardien du monde : même météo partout, fin de mois comptée une fois | 2 | ~2 min |
| `depot_proto_test.py` | le protocole du serveur sans le jeu : monde remplacé, refus, mot de passe, sauvegardes de secours (11 vérifications) | 0 | ~10 s |
| `depot_suite.py` | dépôt de sauvegarde : déposer, prendre, refus quand c'est pris, relais entre deux joueurs, monde neuf (`DEPOT_SERVER=1` : à travers le logiciel serveur) | 2 | ~2 min |
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
  E1 à E6 faites). Dans le sens « l'invité a la quête », seulement les quêtes « subjuguer » : récolte, musique et
  défense restent en solo pour l'invité (les livraisons sont comptées par le jeu du preneur). Les tests prennent la
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
  est refusé (« invalid version ») sans que `mp_test.py` dise pourquoi.
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
- Machine de développement : le jeu a la version **publiée 0.26.442** (build Release) ; lancer
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

## 7. Reste à faire

État au 2026-10-05, 9h30. **La liste à jour, dans l'ordre, est « À faire ensuite » de `HANDOFF.md`** (branche de
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
5. Quêtes à donjon à deux : fait dans les deux sens (`3eaedf8`, `26756bf`). Reste : récolte, musique et défense dans
   le sens « l'invité a la quête » (livraisons comptées par le jeu du preneur), les jouer par le vrai dialogue, la
   déconnexion dans la zone, trois joueurs.
5 bis. **Dans l'ordre du conseil 4** (`HANDOFF.md`) : recherche et compétences du foyer d'un invité en vraies demandes à
   l'host (en cours) ; objets de la carte réglés par un invité (lit, étiquettes de vente, notes) ; politiques ; monture
   déjà prise refusée ; mesurer le rechargement au retour de l'host (soirée d'essai) ; puis la fin de la chasse aux
   différences (`PLAN_chasse_differences.md` : n°4 le reste de la base, 8 machine à gènes, 17, 19, 25 à 28, tombe
   d'épée) ; puis l'étape E (chercher la suite). Écrire des tests pour tout ce qui est « pas joué ».
6. Inégalités invité/host qui restent (`PLAN_egalite_invites.md` : M14 (en partie : recherche et foyer refusés),
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
