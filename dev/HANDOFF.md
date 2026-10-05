# Passation — ElinTogether « indépendance », état au 2026-10-05, 9h30

À lire en premier par la session suivante. Détail daté : fin de `MODLOG.md` (« Version 0.26.442, étape D premier lot »).
Mode d'emploi : `DOCUMENTATION.md`. Règles : `../CLAUDE.md`. Message de départ : `PROMPT_reprise.md`.

## Où on en est

- **Le dossier de travail est `G:\ElinMods`** (C: était plein). `C:\Users\steamdeckwin\Documents\ElinMods` n'est plus
  qu'une suite de raccourcis vers G:. Seul `_lab` (les copies de test du jeu, des liens vers le jeu Steam) est resté
  sur C:. **Ouvrir la session depuis `G:\ElinMods`** : ouverte depuis C:, l'application demande une autorisation à
  chaque écriture.
- **Version 0.26.442 publiée** le 2026-10-05 vers 9h25 (préversion `independance-0.26.442`,
  https://github.com/devmarcpro/elin-together/releases/tag/independance-0.26.442, commit `f096255`, zip vérifié
  identique). L'utilisateur l'a demandée. README des quatre langues mis à jour, avec 8 captures dans `assets/screens/`
  (prises par `dev/_tools/showcase.py`, qui sait maintenant photographier les quêtes à deux et le message de la base).
- **Le jeu de cette machine a la version publiée (build Release)** : `dev/build.ps1` avant tout test ; `Installer.bat`
  du zip avant de jouer avec quelqu'un.
- **Branches** : `fix/points-restants` (branche courante, **la branche de travail**) et `feat/independent-travel` sont
  au **même commit** (`2935741`) ; `feat/independent-travel` est **poussée sur GitHub**. `wip/lots-non-compiles` est
  très en retard, gardée, pas supprimée.
- **Nouvelle habitude demandée par l'utilisateur** (« ça fait 11h que t'as pas commit » : il suit le dépôt sur GitHub) :
  **pousser `feat/independent-travel` après chaque lot validé** (l'avancer sur `fix/points-restants` sans changer de
  branche courante, puis `git push origin feat/independent-travel`). **Publier une nouvelle version demande toujours son
  accord.** Ne jamais pousser sur `upstream`.
- Consignes de l'utilisateur (4 octobre au soir) : **aucune différence entre un joueur host et un joueur invité,
  tout doit être fluide, tous doivent pouvoir tout faire** ; travailler en continu sans s'arrêter ni demander
  d'autorisation (« j'autorise tout ») ; autant d'agents que nécessaire ; les décisions de conception sont tranchées
  par le skill `llm-council` (critères dans l'ordre : l'invité obtient ce qu'un solo obtiendrait ; pas de
  duplication ni de perte ; le plus petit changement ; aucun risque pour les sauvegardes).

## Fait et testé depuis le 4 octobre au soir (branche `fix/points-restants`)

Jusqu'à 2h45 (détail et commits dans `MODLOG.md`) : mort après le jour 90 (C2), prime de guilde (C3), cadeaux du dieu
(C4), pièges (C5), grimoires (C1), bénédiction (G31), autels (G32), abattage (E2), appel à l'aide (E1), dieu quitté
(E3), source chaude (E4), gestes tenus en main (G33–G39, 98/98), quêtes à donjon à deux dans les deux sens (T1–T11,
107/107), chasse aux différences D1 à D11 (peur sous 20 %, guérisseur, rangement, fenêtres d'objets, faucille,
investir, prêtresses, recette lue, runes ; carte au trésor lue et évacuation : déjà bons).

Depuis 2h45, tout est dans la 0.26.442 :

| Point | Commit | Test |
|---|---|---|
| Chasse : pied-de-biche forcé aussi chez l'host | `fb7a507` | `hunt_suite` D13 vert (rouge lu dans le code) |
| Consigne « ne pas s'éloigner » propre à chaque joueur pour ses compagnons | `9155835` | D14 vert |
| Base : recherche et compétences du foyer refusées pour un invité, avec un message (plus de paiement pour rien) | `06a0f94` | `base_suite.py` (nouvelle) 53/53 |
| Échange : refus du jeu solo (non lâchable, propriété d'un PNJ, cadeau, lié), sac plein refusé avant tout transfert, message pour un objet équipé | `9cd8062` | `trade_suite` R6–R11, 122/122 |
| Non-régression avant publication, chaque suite sur un jeu relancé | | equal2 35/35, together 107/107, death 11/11, parity 15/15, sleep 32/32, recruit 45/45, quest 59/59, instance 32/32, trade 122/122, hunt D1–D14, base 53/53, guest 317/317, leave 13/13, travel 54/54, council vert (C5 : 9/9 seul) |

Constat : les étapes de dialogue « acheter des plans » et « améliorer le foyer » n'existent dans aucun dialogue du jeu
installé (le foyer monte tout seul) : il n'y a rien à bloquer ni à demander à l'host de ce côté.

**Fait, pas joué (PAS JOUÉ)** — corrigé dans le code, aucun test ne le prouve :
karma d'un visiteur chez un teneur de carte (`927f342`) ; tri du sac qui ne déborde plus chez l'autre (`5ffa169`) ;
message « déjà vendu » et message nommant l'host avant le rechargement de l'invité (`211658e`) ; noyade en eau profonde
(`cf62040` : D12 saute, pas d'eau profonde sur la carte de test) ; ticket d'hôtesse (`ab73333`) ; fenêtres d'alias, de
retour du vide et de caisse de ferme (`2239dde`) ; carte au trésor d'un invité sur la carte du monde (`4b45541`,
`council_suite --only c6` à refaire).

Décisions du conseil (détail dans `MODLOG.md`) : compte de cadeaux du dieu par joueur ; prime au tueur ; pénalité de
mort du solo pour l'invité, sans case ; carte au trésor cherchée chez celui qui creuse ; pièges et grimoires tirés
dans le jeu du joueur concerné ; quêtes à donjon à deux : boîte Oui/Non, récompense au preneur, tout le monde sort
avec le preneur, l'accompagnant peut rentrer seul, pas de nouvelle case ; **conseil 4 (étape D)** : bloquer d'abord les
actions payantes de la base chez l'invité, puis en faire des demandes vérifiées par l'host ; consigne des compagnons
propre à chaque joueur ; karma d'un visiteur annoncé au teneur de carte, en mémoire seulement ; échange plus strict ;
prévenir l'invité du retour de l'host, mesurer avant d'alléger ; « déjà vendu » ; monture déjà prise refusée.

## Ce qui n'est pas testé (à dire tel quel)

- Tout ce qui est marqué PAS JOUÉ ci-dessus (aucun test) ; et, pour l'utilisateur, tout le point 1 de sa liste d'essais
  (deuxième joueur par Steam, hébergeur qui part, mode avec Elin entre deux PC, Internet avec mot de passe). **Rien de
  ce qui est nouveau dans la 0.26.442 n'a été joué à deux PC.**
- Suites non relancées avant la publication : `shared_suite` et `trio_suite` (trois fenêtres), `companion_suite`, les
  suites du serveur. `run_short.sh` ne lance pas `travel_suite` ni `shared_suite` (elles lancent elles-mêmes le jeu).
- La carte au trésor d'un invité sur la carte du monde avec l'host (`council_suite --only c6` à refaire d'abord).
- Gestes tenus en main (lot 1) : pas comparés entre les deux jeux, les effets du puits sur le potentiel et les
  mutations ; pas de test d'un refus ; la portée de 2 cases ne regarde pas les murs. Le tirage du vœu du puits par
  l'invité s'ajoute à ce que l'host tire pour la gorgée, il ne le remplace pas.
- Quêtes à donjon à deux : les tests prennent la quête, tuent et sortent par les appels du jeu, pas par le dialogue ni
  en marchant jusqu'au bord ; pas de test pour « pas de boîte si l'autre a déjà une quête à donjon ou un échange » ;
  pas de test de déconnexion dans la zone ; trois joueurs pas essayé ; la boîte reste ouverte si la connexion tombe ;
  le nom affiché dans « a refusé » vient du message de l'invité. Dans le sens « l'invité a la quête », seulement les
  quêtes « subjuguer » (récolte, musique, défense restent en solo pour l'invité : les livraisons sont comptées par le
  jeu du preneur) ; `instance_suite` et le bot attendront 15 s à chaque entrée. Le banc sait dérouler un vrai
  dialogue (`hunt_suite.py`) : à faire pour ces quêtes.
- Chasse aux différences, pas joués : le pinceau (le banc ne voit pas son mode), le vol à la tire (n°14 ; l'host peut
  encore avancer vers la victime pendant un vol), investir dans une ville (même code que la boutique), les runes
  d'arme à distance, un refus de rune, le vrai glisser dans la fenêtre de rune, le parchemin de retour (`world_lab`
  n'a pas de destination connue).
- Limites connues : sur une lecture ratée par un invité, ni confusion ni monstres ; un piège d'acide ou de malédiction
  n'abîme l'équipement que dans le jeu de l'invité (pas vérifié) ; un invité qui prie seul en voyage puis chez l'host
  pourrait recevoir un cadeau deux fois (pas vérifié) ; l'or perdu à la mort est ramassable par n'importe quel joueur ;
  les jours passés avec son dieu ne sont comptés que dans le jeu de l'invité, et la colère du dieu quitté est au tarif
  de base chez l'host ; « ne pas vagabonder » lit encore le jeu qui simule ; lit, étiquettes de vente, notes et
  politiques réglés par un invité ne valent que sur son écran.

## À faire ensuite, dans l'ordre du conseil

1. **Base réglée par un invité, suite** : recherche et compétences du foyer en **vraies demandes à l'host** (réponse
   succès / échec, jamais exécutées deux fois) : en cours d'écriture à 9h30. Puis les objets de la carte réglés par un
   invité (lit, étiquettes de vente, notes), puis les politiques. Reporté par le conseil : réserve et rappel d'un
   résident, servante, type de résident, bannir, changer de maison, noms.
2. **Monture déjà prise refusée** avec un message ; deux poses sur la même case et plantage du teneur de carte : rien,
   documenté.
3. **Mesurer le rechargement de l'invité au retour de l'host** pendant la soirée d'essai ; n'alléger qu'au-delà de 5 s.
4. **Finir la chasse aux différences** (`PLAN_chasse_differences.md`, colonne « État ») : n°4 (le reste de la base), 8
   (machine à gènes, même défaut que la roue, plus gros), 17 (habitants qui ne remarquent que l'host : conseil), 19
   (notes, noms), 25, 26, 27, 28, tombe d'épée (21). Un test rouge puis vert par point, dans `hunt_suite.py` (prochains
   numéros : D15 et suivants). Écrire aussi des tests pour ce qui est « PAS JOUÉ » quand le banc le permet.
5. **Étape D, ce qui reste** : mutation en double avec un équipement d'éther ; serveur (relais sans coupure, personnage
   planté à la base, rôle du gardien du monde, mot de passe en clair). Chacun demande une décision : conseil, puis
   application.
6. **Étape E, chercher la suite soi-même** : relire le code du jeu là où la chasse n'est pas allée (liste à la fin de
   `PLAN_chasse_differences.md`), faire jouer le bot, relire les commentaires du Workshop notés dans `MODLOG.md`.
7. Après chaque lot validé : pousser `feat/independent-travel`. Quand un ensemble est vert : passe large (`run_short.sh`
   sur les suites à deux fenêtres, `travel_suite` seule), puis proposer une nouvelle version à l'utilisateur (ne pas
   publier sans son accord).

## Liste d'essais de l'utilisateur (à deux vrais joueurs)

Un seul point par ligne, dans cet ordre :

1. Un deuxième joueur qui rejoint par Steam ; l'hébergeur qui part ; le mode avec Elin entre deux PC ; Internet avec
   mot de passe.
2. Quêtes à donjon à deux, **dans les deux sens** : l'host prend une quête à donjon, l'invité répond Oui à la boîte,
   puis une fois Non ; l'invité prend une quête « subjuguer », l'host répond Oui, puis une fois Non.
3. **Le temps de rechargement de l'invité quand l'host revient sur sa carte** (à chronométrer).
4. **La carte au trésor**, lue puis creusée par l'invité sur la carte du monde, avec l'host.
5. Tout ce qui est PAS JOUÉ : karma d'un visiteur chez un invité (les gardes le voient-ils ?), tri du sac (celui de
   l'autre ne change pas), « déjà vendu » à l'achat au même instant, message qui nomme l'host avant le rechargement,
   ticket d'hôtesse, fenêtres d'alias / retour du vide / caisse de ferme, eau profonde, vol à la tire, investir dans une
   ville, pinceau, runes d'arme à distance.
6. L'invité règle la base (recherche, compétences du foyer) : il doit voir un message et ne rien payer.
7. Un échange : un objet équipé, un sac plein, un objet qu'on ne peut pas lâcher.

## Questions qui restent pour l'utilisateur

- Sa soirée d'essai avec la 0.26.442 (liste ci-dessus), et l'essai de la carte au trésor à deux.
- Quel mod fournit les quêtes `dmp_quest_*`.
- Une prochaine version : à publier quand un nouveau lot sera validé, avec son accord (la dernière : 0.26.442).

## Aide-mémoire

```
powershell -ExecutionPolicy Bypass -File dev\build.ps1
cd dev && set PYTHONPATH=_tools/pylib
python _tools/mp_test.py                       # host + 1 client ; échoue juste après run_short.sh : relancer
python _tools/council_suite.py                 # les décisions du conseil (C6 : --only c6, fenêtres neuves)
python _tools/guest_suite.py --only g31,g32    # ou g33,g34,g35,g36,g37,g38,g39 (gestes tenus en main)
python _tools/equal2_suite.py                  # abattage, appel à l'aide, dieu quitté, source chaude
python _tools/together_suite.py                # quêtes à donjon à deux, les deux sens (T1 à T11, ~16 min)
python _tools/hunt_suite.py                    # chasse aux différences host / invité (D1 à D14 ; --only d1,d3)
python _tools/base_suite.py                    # base réglée par un invité (53 vérifications)
python _tools/trade_suite.py                   # échange, dont les refus R6 à R11
bash _tools/run_short.sh <nom> death_suite guest_suite parity_suite sleep_suite recruit_suite
git push origin feat/independent-travel        # après chaque lot validé, une fois la branche avancée
```

`run_short.sh <nom> suite1 suite2…` relance le jeu entre deux suites (journaux `_shots/<suite>-<nom>.log`) : c'est la
façon de faire la non-régression ; il ne sait pas lancer `travel_suite` ni `shared_suite` (elles lancent elles-mêmes le
jeu : les lancer seules, jeu fermé).

Pièges du matin du 5 octobre : un test qui dépend d'un tirage du jeu peut échouer une fois (C5 : quatre pièges de
sommeil évités de suite ; D3 : la matière d'un seau est tirée au hasard et le coffre ne prend que ce qui s'empile, le
test copie maintenant les mêmes seaux) ; le « Yes. » des boîtes du jeu a un point (chercher par `StartsWith`) ; une
fenêtre Elin peut rester après `Stop-Process` : vérifier, puis `taskkill /PID <n> /F`.

Pièges de la nuit : ne pas compiler pendant qu'un agent écrit dans le même dossier (son travail à moitié
fini part dans la DLL : compiler depuis un worktree propre, `git worktree add`) ; une zone créée par l'host « sans
annonce » n'est jamais connue du client (« Remote zone does not exist… », puis « invalid zone ») ; `ModCurrency` chez
un client est une demande (sa bourse ne baisse qu'à la réponse de l'host : pas pour savoir « a-t-il payé ») ; ce que
fait l'host en appliquant le tick d'un autre joueur n'est pas envoyé (il faut `ElinDelta.Simulate()`) ; le banc sait
dérouler un vrai dialogue (`talk`, `pick`, `hang_up` dans `hunt_suite.py`, choix cliqués par leur texte anglais) ;
le gel occasionnel de la fenêtre host au chargement existe déjà (noté dans `mp_test.py`), ce n'est pas le code testé ;
ne pas enchaîner les grandes suites sur les mêmes fenêtres (mémoire du jeu, « OutOfMemoryException » après 35 minutes
d'`eval` à la chaîne). `new ActPray()` n'a pas d'identifiant (prendre `ACT.Create(6050)`) ; sur la carte du monde on
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
