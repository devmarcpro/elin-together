# ElinTogether « indépendance » — documentation

Fork du mod multijoueur ElinTogether pour Elin. But : **en jeu, aucune différence entre l'host et les autres
joueurs**. Chacun va où il veut, avec ses compagnons, et le monde (quêtes, base, argent de la base) reste commun.

- Dépôt : https://github.com/devmarcpro/elin-together (public), branche `feat/independent-travel`. Le code du
  mod est dans `ElinTogether/`, tout ce qui sert à développer et tester dans `dev/` (ce dossier).
- Installer une nouvelle machine : `SETUP.md`. Consignes pour une session Claude : `CLAUDE.md` à la racine.
- Journal détaillé (pièges, essais, dates) : `MODLOG.md`. Ce document-ci dit ce qui existe et comment s'en servir.
- Les chemins `_tools/`, `_lab/`, `_shots/`, `_release/` de ce document sont relatifs à `dev/`. Le journal parle
  encore de `Documents\ElinMods\` : c'était leur place avant le 2026-10-02.
- État : 2026-10-02 matin (après la nuit de tests).

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
| Échange entre joueurs (option) | Clic sur un autre joueur → « Échanger » : une fenêtre où chacun met des objets et de l'or, puis confirme. Rien ne change de mains tant que les deux n'ont pas confirmé ; s'éloigner annule. | `trade_suite.py` |
| Choix du personnage (option) | À la connexion, le joueur choisit parmi ses personnages de cette partie ou en crée un nouveau. | `chara_suite.py` |
| Karma et crime par joueur (avec l'option « quêtes par joueur ») | Tuer un habitant, voler, creuser la rue : c'est le joueur qui l'a fait qui perd du karma, plus l'host ni les autres. Les gardes de l'host ne poursuivent que le joueur criminel. | `parity_suite.py` Y3–Y4 |
| Affinité et guildes communes | L'affinité d'un habitant est la même pour tous ; rejoindre une guilde ou y monter en grade vaut pour le groupe. | `parity_suite.py` |
| Mort en voyage | Le joueur choisit où revenir, et retrouve l'host s'il revient à la base. | vu une fois avec le bot |
| Déplacements fluides d'un invité (option) | Un invité marche et agit sur l'horloge de son propre jeu, comme l'host : ses pas ne dépendent plus du réseau ni d'un host qui rame. L'accéléré est partagé : quand un joueur accélère, tous ceux de la carte accélèrent. | `move_suite.py` V1–V3, V6 |
| Chacun marche comme en solo (option) | La durée d'un pas ne dépend plus de la vitesse des autres joueurs. En combat la vitesse compte toujours. | `move_suite.py` V4–V5 |
| Personnage d'une sauvegarde solo (option, décochée par défaut) | À la connexion : « un personnage d'une de mes sauvegardes », puis la liste des dernières sauvegardes. Il arrive avec ses caractéristiques, son apparence, son équipement, son sac, son or, sa renommée et son karma. Pas ses compagnons, sa base, ses quêtes ni sa banque. La sauvegarde est seulement lue. Un seul exemplaire par sauvegarde et par joueur. | `import_suite.py` |
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
| Personnage d'une sauvegarde solo (`ImportCharacter`, décochée par défaut) | le joueur peut amener le personnage d'une de ses sauvegardes | choix absent |

Les options sont envoyées aux clients à la connexion (`NetSessionRules`). Toute nouvelle fonction doit avoir sa case.

## 3. Installer

**Pour jouer (toi et ton ami, même zip des deux côtés)** : `_release/ElinTogether-independance.zip`, puis
`Installer.bat`. `Desinstaller.bat` remet le mod du Workshop. Refaire le zip : `make_release.ps1`. Le zip n'est
pas dans le dépôt : il se fabrique sur chaque machine.
Le zip actuel date du 2026-10-02 20h32, commit `f17ad6c`, mod 0.26.309, pour Elin EA 23.351. Il est aussi sur la page des versions
du dépôt (https://github.com/devmarcpro/elin-together/releases) : c'est le lien à donner à un ami.
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
| `trade_suite.py` | échange entre joueurs | 2 | ~2 min |
| `chara_suite.py` | choix du personnage à la connexion | 2 | ~3 min |
| `parity_suite.py` | affinité, guildes, karma et gardes | 2 | ~1 min |
| `transfer_suite.py` | ce qui se passe pendant un changement de carte | 2 | ~3 min |
| `economy_suite.py` | expédition par joueur | 2 | ~5 min |
| `combat_suite.py` | combat au rythme du joueur | 2 | ~5 min |
| `build_suite.py` | poser, construire, mur cassé par un monstre | 2 | ~3 min |
| `player_suite.py` | dons à la fabrication, apparence au miroir, slime | 2 | ~4 min |
| `death_suite.py` | mourir sur la carte de l'host puis repartir seul | 2 | ~3 min |
| `sleep_suite.py` | dormir à plusieurs, à la base ou sur une carte sauvage (`--only w0,z0,z1,z2`) | 2 | ~3 min |
| `guest_suite.py` | le même geste par l'invité puis par l'host : repos, pêche, baguette, coffres de pari, bouteille vide | 2 | ~3 min |
| `recruit_suite.py` | compagnons recrutés par un invité : dialogue, monture, boule à monstre, achat | 2 | ~5 min |
| `move_suite.py` | pas de l'invité : réguliers, host qui rame, écart de vitesse, accéléré partagé | 2 | ~2 min |
| `import_suite.py` | rejoindre avec le personnage d'une sauvegarde (copie du monde de test) | 2 | ~3 min |
| `compat_suite.py` | cohabitation avec d'autres mods (Somewhat Enhanced Display) | 2 | ~2 min |
| `run_short.sh` | les suites courtes à la suite, chacune sur un monde neuf (pas `economy` ni `combat`, qui ouvrent leurs fenêtres : `run_all.sh`) | 2 | ~50 min |
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
  l'histoire sont gérés, mais testés par appels directs, **pas encore en cliquant dans les vrais dialogues**.
  Restent locaux au joueur : les alliés offerts par un dialogue (animal de Fiama), le mariage. En voyage seul, seuls les effets « sur le monde entier » sont répétés chez l'host.
- Quêtes à donjon : seul le preneur entre dans la zone de sa quête, les autres joueurs ne peuvent pas encore l'y
  rejoindre. L'escorte prise par un client n'a été testée que par le code, pas en marchant.
- Échange : pas d'objets équipés, ni de sacs pleins ; fenêtre simple (liste + boutons).
- Karma : sur une carte tenue par un joueur (pas l'host), les gardes suivent encore le karma de ce joueur-là.
  Un habitant attaqué par un invité n'appelle pas à l'aide. Affinité de la tonte et de l'abattage perdue pour un
  invité. Expérience de guilde : si deux joueurs en gagnent au même instant, un des deux gains est perdu.
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
- Compagnons d'un invité : le domptage à la brosse n'est pas testé en jeu ; l'achat est testé par ce que fait le
  « oui » du marchand, pas par son vrai dialogue ; l'animal de Fiama perd sa marque (posée après le recrutement,
  sur la copie locale). La laisse et la consigne « ne pas s'éloigner » regardent encore l'host.
- D'autres mods du joueur peuvent mal vivre une session (le jeu d'un client est remplacé à chaque carte) : une
  garde existe pour Somewhat Enhanced Display (`Patches/Compat/OtherModsCompat.cs`), à étendre au cas par cas.
- Joué une seule soirée entre deux PC par Steam (2026-10-02) ; elle a trouvé le blocage de l'host après une nuit
  sur une carte sauvage, corrigé depuis. Le reste a été vérifié en local.
- Le temps du monde suit encore l'host.

## 7. Reste à faire

État au 2026-10-03 au soir. Détail de chaque point : `PLAN_retours_partie_reelle.md` et la fin de `MODLOG.md`.

**D'abord (demandes de l'utilisateur après sa première vraie partie comme invité, dans cet ordre) :**
1. Fait le 2026-10-04 : passe complète verte sur les cinq corrections du 3 au soir, version publiée ensuite.
2. Fait le 2026-10-04 : fluidité des déplacements d'un invité (`move_suite` 17/17), avec la case « chacun marche
   comme en solo » et l'accéléré partagé. À jouer entre deux PC.
3. Fait le 2026-10-04 : rejoindre avec un personnage d'une sauvegarde solo (`import_suite` 21/21).
4. Fait le 2026-10-04 : compagnons d'un invité par boule à monstre, monture, achat (`recruit_suite` 41/41).
   Reste : tester la brosse en jeu, l'animal de Fiama, la laisse.
5. Retour de l'host sur une carte tenue par un invité **sans rechargement** (plan B, gros, derrière une case).
6. **Profil de mods** (validé le 2026-10-02) : `PLAN_profil_mods.md`, plan détaillé prêt.

**Tests plus proches d'une vraie partie (proposé à l'utilisateur le 2026-10-03, il n'a pas encore dit oui) :**
- une touche « signaler un problème » en jeu (capture d'écran + repère dans le journal) ;
- un bot qui rejoue une vraie soirée (l'host sort et rentre, l'invité suit, recruter, dormir, se battre) ;
- un faux réseau lent entre les fenêtres (délai, à-coups) : le banc local n'a aucun délai.

**Ensuite :**
7. Plan écrit le 2026-10-04 : `PLAN_serveur_depot.md` (six étapes, cinq décisions à prendre avec lui).
   Temps du monde commun (à décider avec l'utilisateur), puis **serveur indépendant**. L'utilisateur a tranché
   le 2026-10-03 au soir : un serveur « dépôt de sauvegarde » (un petit programme sans Elin qui garde la
   sauvegarde et dit qui tient quelle carte ; toute la simulation est faite par les joueurs, un joueur par
   carte). À commencer quand les points 1 à 4 sont bons, **plan à lui présenter avant de coder**. Première
   marche : le temps du monde commun. Détail dans `MODLOG.md`, « Idées de l'utilisateur ».
8. Quêtes à donjon : laisser les autres joueurs y rejoindre le preneur (`PLAN_quetes_donjon_phase2.md`).
9. Inégalités invité/host qui attendent une décision (`PLAN_egalite_invites.md` : M3, M5, M9, L1, L7, M13).
10. Deux choix de jeu en attente : que faire quand un joueur meurt sur la carte de l'host ; quand la connexion tombe.
11. Jouer le début de l'histoire en vrai avec un client ; conflits rares listés dans les limites.

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
