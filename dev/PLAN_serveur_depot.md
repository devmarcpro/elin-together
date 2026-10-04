# Plan — serveur « dépôt de sauvegarde » (idée de l'utilisateur, 2026-10-03)

L'utilisateur a confirmé le 2026-10-04 au matin que c'est bien son idée, et demandé d'avancer sans attendre.
**Étape 1 faite le 2026-10-04** (`a76d6a9`, case `SharedWorldTime`, `time_suite` 12/12), avec le choix proposé
ci-dessous : la date la plus avancée gagne.
**Étape 2 commencée le 2026-10-04** (`1b0f5c3`, case `WorldKeeper`, `world_suite` 10/10) : ce qu'une heure, un jour
ou un mois fait au monde n'est fait que par le gardien, qui est encore l'host ; sa météo est envoyée à tous.
Reste de l'étape 2 : les boucles internes de `GameDate`, les données du jour, puis le passage du rôle (ce qui
doit voyager avec lui : météo, données du jour, journal de quêtes, colis en attente, coffres du monde, factures,
niveau et expérience de la base, aventuriers).

## L'idée

Le serveur est un petit programme, **sans Elin**. Il garde la sauvegarde et dit qui tient quelle carte. Toute la
simulation est faite par les joueurs : un joueur par carte. Plus personne n'est l'host, tout le monde est invité.

## Ce qui existe déjà et qui sert

- Un invité sait déjà **tenir une carte** : il la simule seul, d'autres invités le rejoignent, il la passe à un
  autre quand il part, il la rend avec des points de sauvegarde réguliers (le « prêt de carte »).
- Les **numéros d'objets** sont déjà distribués par plages (50 000 par prêt) : de simples compteurs.
- Les fichiers d'une carte voyagent déjà comme des blocs que personne n'ouvre en route.
- Sur ~237 endroits du mod qui disent « si je suis l'host », environ 170 concernent la simulation d'une carte :
  ils marchent déjà pour un invité qui tient une carte. Restent ~35 qui touchent au **monde** (quêtes, expédition,
  date, karma, ressources de la base) et ~15 à la sauvegarde et à la session. C'est là qu'est le travail.

## Ce qui dépend encore du jeu de l'host (recensement du 2026-10-04, lu dans le code)

| Sujet | Aujourd'hui | Un programme sans le jeu peut-il le faire ? |
|---|---|---|
| Date du monde | seul l'host l'avance ; un invité seul sur sa carte avance la sienne, puis reprend celle de l'host au retour | **oui** pour le compteur ; **non** pour ce qui se passe à chaque heure, jour et mois (météo, quêtes, factions, expédition, habitants) : c'est du jeu |
| Le monde entier | c'est le jeu en cours de l'host ; chaque invité en reçoit une copie complète à la connexion | garder le fichier : oui ; le fabriquer ou le corriger : non, il faut un jeu |
| Ce qu'un invité change hors de sa carte (base, faction, religion…) | pas renvoyé à l'host | à inventer |
| Rendre une carte | fichiers et compteurs : simples ; le personnage et ses compagnons sont rebranchés dans le monde par le jeu de l'host | fichiers : oui ; rebrancher : non |
| Quêtes par joueur, expédition, renommée | décidés dans le jeu de l'host | stocker : oui ; décider : non |
| Arrivée d'un joueur | il arrive toujours sur la carte de l'host, qui doit avoir une base | à changer : il arrive sur une carte que quelqu'un tient, ou la prend |
| Réseau | uniquement les connexions Steam, depuis le jeu | il faut un autre moyen de se parler pour un programme sans jeu ni Steam |
| Sauvegarder | seul l'host sauvegarde | à changer |
| Fin de session | si l'host part, tout le monde retourne à l'écran titre | le serveur reste, c'est le but |
| Un joueur plante en tenant une carte | on garde son dernier point de sauvegarde ; un invité présent hérite de sa copie | pareil, à durcir |

## Les trois vrais problèmes

1. **Ce qui n'appartient à aucune carte.** Un programme sans le jeu ne sait pas faire passer un jour. Proposition :
   un des joueurs connectés est le **gardien du monde** (celui qui tient la carte de la base, sinon le premier
   connecté) : son jeu fait passer les heures, les jours, l'expédition, les quêtes. S'il part, un autre reprend,
   comme pour une carte. Le serveur garde le résultat. Ce n'est plus « l'host » : le rôle se passe, et le monde
   survit quand personne n'est là.
2. **Le réseau et le démarrage.** Le serveur ne peut pas utiliser Steam comme le fait le jeu. Il faut ajouter au mod
   une connexion directe par adresse (le banc de test en a déjà une forme), et décider comment naît un monde :
   proposition, on **dépose** une sauvegarde existante sur le serveur.
3. **Deux joueurs qui décident en même temps.** Aujourd'hui « la copie de l'host gagne ». Sans host il faut une
   règle pour chaque sujet : une carte = celui qui la tient ; le monde = le gardien ; la date = la plus avancée.

## Étapes proposées (chacune jouable, testée au banc, derrière une case)

| # | Étape | Ce que le joueur voit | Taille |
|---|---|---|---|
| 1 | **Temps du monde commun** (l'host existe encore) : la date appartient à la session. Chaque joueur qui tient une carte dit de combien il a avancé, la session garde la date la plus avancée et la redit à tous. | un invité parti seul a la même date que les autres ; rentrer ne fait plus sauter la date | moyenne |
| 2 | **Le gardien du monde** : ce qui se passe à chaque heure, jour, mois est fait par un joueur désigné, et ce rôle se passe d'un joueur à l'autre. L'host est encore là mais n'est plus obligé d'être le gardien. | rien de visible, c'est la fondation | grosse |
| 3 | **Arriver sans passer par la carte de l'host** : un joueur qui se connecte arrive là où il s'était arrêté, sur une carte qu'il prend ou que quelqu'un tient. | on peut jouer sans jamais croiser l'host | grosse |
| 4 | **L'host peut partir** : la session continue sans lui, un autre joueur garde le monde et le sauvegarde. | la partie ne s'arrête plus quand l'host quitte | grosse |
| 5 | **Le programme serveur** : il garde la sauvegarde, la liste de qui tient quoi, les compteurs, la date ; connexion directe par adresse. Le premier joueur connecté devient le gardien. | un serveur allumé en permanence, on rejoint quand on veut | grosse |
| 6 | Durcir : joueur qui plante, serveur qui redémarre, deux joueurs qui prennent la même carte, sauvegardes de secours. | moins de pertes | moyenne |

Les étapes 1 à 4 se font **sans écrire le programme serveur** : elles enlèvent à l'host, une par une, ce qui fait
de lui « le monde ». À la fin de l'étape 4 le plus dur est fait et déjà utile (une partie qui survit au départ de
l'host). L'étape 5 remplace alors le dernier rôle de l'host, garder les fichiers, par le programme.

## Décisions à prendre avec l'utilisateur

1. **Le temps** (étape 1) : la date la plus avancée gagne-t-elle ? Conséquence : si un joueur dort huit heures
   seul sur sa carte, tout le monde avance de huit heures. L'autre choix (chacun son heure) casse les quêtes à
   échéance et l'expédition.
2. **Le gardien** : celui qui tient la base, ou le premier connecté ?
3. **Naissance d'un monde sur le serveur** : déposer une sauvegarde existante (proposé), ou créer depuis le serveur ?
4. **Personne de connecté** : le monde est figé (proposé, comme une carte sans joueur aujourd'hui).
5. **Confiance** : celui qui tient une carte ou garde le monde décide. Sans importance entre amis ; à savoir pour
   un serveur ouvert.

## Tests prévus

- Étape 1 : `time_suite.py` — un invité part seul, attend, dort ; sa date et celle de l'host restent égales ; au
  retour la date ne saute pas ; les quêtes à échéance et l'expédition tombent au même moment pour tous.
  `travel_suite`, `shared_suite`, `sleep_suite`, `quest_suite`, `economy_suite` inchangées.
- Ensuite : le bot qui rejoue une vraie soirée, avec le départ de l'host au milieu.
