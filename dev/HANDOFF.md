# Passation — ElinTogether « indépendance », état au 2026-10-05, 2h45

À lire en premier par la session suivante. Détail daté : fin de `MODLOG.md` (« Étapes B et C »).
Mode d'emploi : `DOCUMENTATION.md`. Règles : `../CLAUDE.md`. Message de départ : `PROMPT_reprise.md`.

## Où on en est

- **Le dossier de travail est maintenant `G:\ElinMods`** (C: était plein). `C:\Users\steamdeckwin\Documents\ElinMods`
  n'est plus qu'une suite de raccourcis vers G:. Seul `_lab` (les copies de test du jeu, des liens vers le jeu
  Steam) est resté sur C:. **Ouvrir la session depuis `G:\ElinMods`** : ouverte depuis C:, l'application demande une
  autorisation à chaque écriture.
- Dernière version **publiée** : 0.26.399 (inchangée). Rien n'a été poussé sur GitHub ni publié cette nuit.
- Le jeu de cette machine a un **build de test (Debug) du code de `fix/points-restants`** : avant de jouer avec
  quelqu'un, `Installer.bat` du zip 0.26.399 ; avant tout test, `dev/build.ps1`.
- Deux branches locales, parties de `feat/independent-travel` (`e08310a`) :
  - **`fix/points-restants`** (branche courante, **la branche de travail**) : tout y est compilé et testé en jeu, y
    compris les trois lots de la nuit, les quêtes à donjon à deux dans les deux sens et la chasse aux différences
    (un commit par point), sauf la carte au trésor (voir plus bas). Depuis 1h05 : 10 commits (`392266d` à
    `26756bf`).
  - **`wip/lots-non-compiles`** : même contenu que `fix/points-restants` à 1h05, **en retard de ces 10 commits** ;
    gardée, pas supprimée.
- Consignes de l'utilisateur (4 octobre au soir) : **aucune différence entre un joueur host et un joueur invité,
  tout doit être fluide, tous doivent pouvoir tout faire** ; travailler en continu sans s'arrêter ni demander
  d'autorisation (« j'autorise tout ») ; autant d'agents que nécessaire ; les décisions de conception sont tranchées
  par le skill `llm-council` (critères dans l'ordre : l'invité obtient ce qu'un solo obtiendrait ; pas de
  duplication ni de perte ; le plus petit changement ; aucun risque pour les sauvegardes).

## Fait et testé depuis le 4 octobre au soir (branche `fix/points-restants`)

| Point | Commit | Test |
|---|---|---|
| Mort : l'invité qui meurt chez l'host après le jour 90 perd une part de son or (elle tombe par terre), lettre de testament comprise | `d9df4f6` | `council_suite` C2 |
| Prime de la guilde des guerriers : au joueur derrière le tueur | `a5d764a` | C3 |
| Cadeaux du dieu : chaque joueur reçoit une fois son familier et son artefact | `78c345d` | C4 |
| Pièges : tirés dans le jeu de celui qui marche dessus ; sommeil, cécité, paralysie demandés à l'host | `31c0c28` | C5 |
| Grimoires : tirés dans le jeu du lecteur ; un échec use le livre chez l'host | `202f026` | C1 (passait déjà avant : le double échec n'est pas prouvé corrigé) |
| Bénédiction du dieu d'un invité calculée comme celle d'un joueur | `e08940c` | `guest_suite` G31 |
| Autels (invention, soin…) : pour celui qui les touche, une seule recette pour tous | `5ee3209` | G32 |
| Abattage par un invité : l'objet tenu part avant la tâche (l'host levait `NullReferenceException`) ; l'endurance et le karma sont ceux de l'invité | `299c8bd` | `equal2_suite` E2 |
| Appel à l'aide : un habitant frappé par un invité appelle ses voisins comme pour l'host (le test va à Vernis : le jeu n'appelle jamais dans une base du joueur) | `cf4797d` | E1 |
| Dieu quitté par un invité : la punition du jeu, des deux côtés | `e9824ee` | E3 |
| Source chaude : le bain va à l'invité et à son compagnon, pas à l'host | `8e413a8` | E4 |
| Gestes tenus en main rejoués chez l'host : ticket de meuble, seringues (gène, sang, paradis, licorne), puits (le vœu est tiré dans le jeu de l'invité), stéthoscope, laisse | `8f39634` | `guest_suite` G33–G39 : 98/98 |
| Quêtes à donjon à deux, l'host a la quête : boîte Oui/Non chez l'invité (15 s), tout le monde sort avec l'host, l'accompagnant rentre seul et est fouillé pour la récolte | `3eaedf8` | `together_suite` T1–T6 : 18/18 |
| Quêtes à donjon à deux, **l'invité a la quête** : boîte Oui/Non chez l'host (15 s), zone simulée par l'host, récompense à l'invité, l'host peut rentrer seul ; sens « subjuguer » seulement | `26756bf` | `together_suite` T7–T11 : 107/107 avec T1–T6 |
| Chasse n°1 : un invité sous 20 % de vie ne prend plus peur et peut frapper | `392266d` | `hunt_suite` D1 |
| Chasse n°2 : le guérisseur payant soigne vraiment l'invité et ses compagnons (le soin est demandé à l'host) | `3d27d3f` | D2 (vrai dialogue) |
| Chasse n°3 : rangement automatique propre à chaque joueur (celui de l'invité emportait les objets de l'host, celui de l'host fermait les fenêtres de l'invité) | `f4c5b44` | D3 |
| Chasse n°5, 9, 20, 21 et la roue : radio, juke-box, liste de lecture, livres des résidents et de l'équipe, détecteur, roue, vue de carte, pinceau : fenêtre chez celui qui s'en sert seulement | `ea93c88` | D4 (pinceau non observable par le banc) |
| Chasse n°24 : l'ecopo de la faucille va à l'invité qui fauche ; n°14 vol à la tire : plus d'endurance perdue par l'host | `f00f5a6` | D5 (le vol : pas joué) |
| Chasse n°11 : investir dans une boutique ou une ville arrive chez l'host (avant : payé pour rien) | `f63a879` | D6 (boutique par le vrai dialogue ; ville pas jouée) |
| Chasse n°12 : la bénédiction des prêtresses atteint l'invité et ses compagnons | `9046034` | D7 (vrai dialogue) |
| Chasse n°23 : une recette lue par un joueur n'est apprise qu'une fois par l'autre (avant : deux fois) ; n°16 évacuation : déjà bon | `15d6e05` | D9, D8 |
| Chasse n°7 : runes et prises : fenêtre chez l'utilisateur seul, rune posée et usée dans les deux jeux (celle de l'host n'arrivait jamais chez l'invité) | `3ccad87` | D10 (arme à distance, refus : pas joués) |
| Chasse n°10 carte au trésor lue : déjà bon (fenêtre chez le lecteur, même carte) | | D11 |
| Non-régression sur ce code (au 1h05) | | death 11/11, guest 220/220, parity 15/15, sleep 32/32, recruit 45/45 ; `equal2_suite` en entier vert (E1 9/9, E2 + E4 19/19, E3) |

**Fait, pas vérifié en jeu** : carte au trésor (`4b45541`). Le banc n'arrivait pas à faire creuser l'invité sur la
carte du monde (`council_suite --only c6`) ; la cause probable est l'objet tenu envoyé trop tard, corrigé par `299c8bd`.
**À réessayer** avec `council_suite --only c6` (pas refait), puis dans la liste d'essais de l'utilisateur.

Décisions du conseil (détail dans `MODLOG.md`) : compte de cadeaux du dieu par joueur ; prime au tueur ; pénalité de
mort du solo pour l'invité, sans case ; carte au trésor cherchée chez celui qui creuse ; pièges et grimoires tirés
dans le jeu du joueur concerné ; quêtes à donjon à deux : boîte Oui/Non, récompense au preneur, tout le monde sort
avec le preneur, l'accompagnant peut rentrer seul, pas de nouvelle case.

## Ce qui n'est pas testé (à dire tel quel)

- Tout le point 1 de la liste de l'utilisateur (ses essais à deux PC) : deuxième joueur par Steam, hébergeur qui
  part, mode avec Elin entre deux PC, Internet avec mot de passe ; **à deux vrais joueurs : l'host prend une quête à
  donjon, l'invité répond Oui à la boîte, puis une fois Non ; à deux : l'invité prend une quête subjuguer, l'host
  répond Oui** (puis une fois Non).
- La carte au trésor d'un invité sur la carte du monde avec l'host (`council_suite --only c6` à refaire d'abord).
- Gestes tenus en main (lot 1) : pas comparés entre les deux jeux, les effets du puits sur le potentiel et les
  mutations ; pas de test d'un refus ; la portée de 2 cases ne regarde pas les murs. Le tirage du vœu du puits par
  l'invité s'ajoute à ce que l'host tire pour la gorgée, il ne le remplace pas.
- Quêtes à donjon à deux (lot 3) : le test prend la quête et sort par les appels du jeu, pas par le dialogue ni en
  marchant jusqu'au bord ; pas de test pour « pas de boîte si l'autre a déjà une quête à donjon ou un échange ». Le nom
  affiché dans « a refusé » vient du message de l'invité (pas grave à deux) ; la boîte reste ouverte si la connexion
  tombe.
- Quêtes à donjon à deux, sens « l'invité a la quête » (`26756bf`) : seulement les quêtes « subjuguer » (récolte,
  musique, défense restent en solo pour l'invité, car les livraisons sont comptées par le jeu du preneur) ; le test
  prend la quête, tue et sort par les appels du jeu, pas par le dialogue ni au combat ; pas de test de déconnexion
  dans la zone ; trois joueurs pas essayé ; `instance_suite` et le bot attendront 15 s à chaque entrée (boîte sans
  réponse chez l'host). Le banc sait maintenant dérouler un vrai dialogue (`hunt_suite.py`) : à faire pour ces quêtes.
- Chasse aux différences : pas joués : le pinceau (le banc ne voit pas son mode), le vol à la tire (n°14, même
  garde que l'abattage ; l'host peut encore avancer vers la victime pendant un vol), investir dans une ville (même
  code que la boutique), les runes d'arme à distance, un refus de rune, le vrai glisser dans la fenêtre de rune, le
  parchemin de retour (`world_lab` n'a pas de destination connue). Non-régression (`run_short.sh`) pas refaite depuis
  les corrections de la chasse ni depuis `26756bf`.
- Limites connues des corrections de cette nuit : sur une lecture ratée par un invité, ni confusion ni monstres ; un
  piège d'acide ou de malédiction n'abîme l'équipement que dans le jeu de l'invité (pas vérifié) ; un invité qui prie
  seul en voyage puis chez l'host pourrait recevoir un cadeau deux fois (pas vérifié) ; l'or perdu à la mort est
  ramassable par n'importe quel joueur ; les jours passés avec son dieu ne sont comptés que dans le jeu de l'invité,
  et la colère du dieu quitté est au tarif de base chez l'host.

## À faire ensuite, dans l'ordre

1. **Finir la chasse aux différences** (`PLAN_chasse_differences.md`, colonne « État ») : n°4 (base réglée par
   l'invité), 6 (caisse de ferme : la fenêtre s'ouvre chez tous, la livraison marche déjà), 8 (machine à gènes :
   même défaut que la roue, plus gros), 13 (noyade, pluie), 15 (pied-de-biche), 17 (habitants qui ne remarquent que
   l'host : conseil), 18 (tickets d'hôtesse), 19 (notes, noms), 22 (alias, retour du vide), 25, 26, 27, 28. Un test
   rouge puis vert par point, dans `hunt_suite.py` (prochains numéros : D12 et suivants). Refaire aussi
   `council_suite --only c6` (carte au trésor).
2. **Étape D, reste de la liste de l'utilisateur**, pas commencé :
   - réglages de la base faits par un invité (M14 : lit, nom de zone, panneaux, étiquettes de vente ; et, d'après la
     chasse, politiques, recherche, métiers des résidents : recoupe le n°4) ;
   - consigne « ne pas s'éloigner » d'un compagnon (lit les réglages de l'host) ; karma des visiteurs sur une carte
     tenue par un invité ; mutation en double avec un équipement d'éther ;
   - échange : objets équipés, sacs pleins ; repos qui finit en sommeil (à revérifier) ; rechargement de l'invité au
     retour de l'host ; autres mods ;
   - serveur : relais sans coupure, personnage planté à la base, rôle du gardien du monde, mot de passe en clair ;
   - accidents rares : deux achats au même instant, deux constructions sur la même case, monture en double, plantage
     de celui qui tient une carte.
   Chacun de ces points demande une décision de conception : conseil, puis application.
3. **Étape E, chercher la suite soi-même** : relire le code du jeu là où la chasse n'est pas allée (liste à la fin de
   `PLAN_chasse_differences.md`), faire jouer le bot, relire les commentaires du Workshop notés dans `MODLOG.md`.
4. Quand un ensemble est vert : passe large (`run_short.sh` sur les suites à deux fenêtres), fusion dans
   `feat/independent-travel`, puis proposer une nouvelle version à l'utilisateur (ne pas publier sans le lui dire).

## Questions qui restent pour l'utilisateur

- Sa soirée d'essai avec la 0.26.399, et l'essai de la carte au trésor à deux.
- À deux vrais joueurs : l'host prend une quête à donjon, l'invité répond Oui à la boîte, puis une fois Non ; et
  dans l'autre sens : l'invité prend une quête subjuguer, l'host répond Oui, puis une fois Non.
- Quel mod fournit les quêtes `dmp_quest_*`.
- Pousser les branches sur GitHub et publier une nouvelle version : quand il le voudra.

## Aide-mémoire

```
powershell -ExecutionPolicy Bypass -File dev\build.ps1
cd dev && set PYTHONPATH=_tools/pylib
python _tools/mp_test.py                       # host + 1 client ; échoue juste après run_short.sh : relancer
python _tools/council_suite.py                 # les décisions du conseil (C6 : --only c6, fenêtres neuves)
python _tools/guest_suite.py --only g31,g32    # ou g33,g34,g35,g36,g37,g38,g39 (gestes tenus en main)
python _tools/equal2_suite.py                  # abattage, appel à l'aide, dieu quitté, source chaude
python _tools/together_suite.py                # quêtes à donjon à deux, les deux sens (T1 à T11, ~16 min)
python _tools/hunt_suite.py                    # chasse aux différences host/invité (D1 à D11 ; --only d1,d3)
bash _tools/run_short.sh <nom> death_suite guest_suite parity_suite sleep_suite recruit_suite
```

Pièges de la nuit et du matin : ne pas compiler pendant qu'un agent écrit dans le même dossier (son travail à moitié
fini part dans la DLL : compiler depuis un worktree propre, `git worktree add`) ; une zone créée par l'host « sans
annonce » n'est jamais connue du client (« Remote zone does not exist… », puis « invalid zone ») ; `ModCurrency` chez
un client est une demande (sa bourse ne baisse qu'à la réponse de l'host : pas pour savoir « a-t-il payé ») ; ce que
fait l'host en appliquant le tick d'un autre joueur n'est pas envoyé (il faut `ElinDelta.Simulate()`) ; le banc sait
dérouler un vrai dialogue (`talk`, `pick`, `hang_up` dans `hunt_suite.py`, choix cliqués par leur texte anglais) ;
le gel occasionnel de la fenêtre host au chargement existe déjà (noté dans `mp_test.py`), ce n'est pas le code testé.
Pièges de la nuit : `new ActPray()` n'a pas d'identifiant (prendre `ACT.Create(6050)`) ; sur la carte du monde on
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
