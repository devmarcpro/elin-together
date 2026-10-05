# Message de départ pour une nouvelle session

Pour un travail **sans arrêt**, tape `/loop` puis colle le texte ci-dessous juste après, dans une nouvelle session
ouverte dans **`G:\ElinMods`** (le dossier a été déplacé le 2026-10-04 ;
`C:\Users\steamdeckwin\Documents\ElinMods` n'est plus qu'un raccourci vers lui). État décrit : 2026-10-05, 14h15.

---

Je reprends le travail sur ElinTogether (le fork « indépendance »), dans `G:\ElinMods\ElinTogether`. Réponds-moi en
français simple et court, sans jargon : je ne lis pas le code.

## Le but

**Aucune différence entre un joueur host et un joueur invité. Tout doit être fluide, tous les joueurs doivent pouvoir
tout faire.** On doit pouvoir jouer à Elin à plusieurs comme si le jeu avait été fait pour ça. Je joue comme invité,
avec un seul ami comme host : chaque chose doit marcher dans les deux sens à deux joueurs.

## Pour commencer, dans cet ordre

1. Charge le skill `ponytail:ponytail` (le plus petit changement qui marche) et garde-le. Active Remote Control.
2. Lis : `CLAUDE.md`, puis `dev/HANDOFF.md` en entier (l'état exact, les branches, ce qui est « pas joué »), la fin de
   `dev/MODLOG.md` à partir de « Étape D suite, Elin 23.352 », `dev/PLAN_chasse_differences_2.md` (la liste de travail
   de l'étape E), puis au besoin `dev/PLAN_egalite_invites.md`, `dev/PLAN_chasse_differences.md`, `dev/NOTE_version.md`.
3. Vérifie l'état : `git status` et `git branch` dans `G:\ElinMods\ElinTogether`. Tu dois être sur
   **`fix/points-restants`** (la branche de travail). `feat/independent-travel` est au même commit et **poussée sur
   GitHub** ; `wip/lots-non-compiles` est en retard, ne la supprime pas ; ne change pas de branche courante. Version
   publiée : **0.26.442** (5 octobre), compilée pour Elin 23.351. Si `git status` montre un travail non
   commité, c'est peut-être celui d'une session coupée : regarde `git diff`, ne l'écrase pas.
4. Vérifie qu'aucun Elin ne tourne (ferme par numéro de processus, jamais un jeu que j'ai lancé). **Elin est passé en
   EA 23.352** : si les copies de test ne sont pas à jour, refais `python _tools/make_lab.py Elin2 2` (depuis `dev/`,
   avec `PYTHONPATH=_tools/pylib`), sinon la connexion est refusée (« Version mismatch »). Puis compile :
   `powershell -ExecutionPolicy Bypass -File dev\build.ps1` avant tout test. Le code décompilé `dev/_decomp` est celui
   de 23.351 : refais-le avant de te fier à un numéro de ligne.
5. Dis-moi en cinq lignes ce que tu as compris de l'état, puis enchaîne sans attendre ma réponse.

## Le travail, dans cet ordre

**Fait** (ne le refais pas) : tout ce qui est dans la 0.26.442 ; depuis, la base réglée par un invité (recherche et
foyer en demandes à l'host, politiques, lits, étiquettes, notes, noms), « ne pas vagabonder » par joueur, le don d'un
objet pris dans une pile, la monture déjà prise, les quêtes de récolte et de musique de l'invité à deux, la deuxième
chasse aux différences (lue, pas jouée). Tout est poussé sur GitHub.

1. **Jouer la barrière de version** (faite à 14h15, commit `ee374b7`, `version_suite` 8/8 en connexion locale). Ma
   demande : « rendre les futures versions du mod compatibles avec les futures versions d'Elin sans forcément le mettre
   à jour, ne pas avoir de barrière ». Maintenant seule la version du MOD doit être la même ; une version d'Elin
   différente = un avertissement ; une case côté host revient au contrôle strict. Le chemin par le salon Steam n'est pas
   joué : à essayer à deux PC (ma liste d'essais, point 9), rien à réécrire avant.
2. **Republier une version compilée sur 23.352** : propose-le moi dans ton résumé, je dirai oui. Avant : refaire
   tourner les suites larges sur 23.352 (`run_short.sh`, puis `travel_suite` et `shared_suite` seules).
3. **Étape E = `dev/PLAN_chasse_differences_2.md`** (37 lignes lues dans le code, rien de joué), en commençant par les
   lignes hautes : 1 (mode construction d'un invité : il paie, rien ne se construit chez l'host) et 2 (tailler un
   rondin à la hache). Puis les « sûr » : 6 nourriture du sac de l'invité qui ne pourrit jamais, 25 prière sans dieu,
   26 prix d'expédition, 30 carte à gratter du casino, 33 jours et relance des quêtes, 36 Mifu / Nefu / Aquli ; puis les
   « probable » (5 prière qui ne soigne que l'invité, 8 résurrection d'un compagnon, 7 réglages de coffre, 9 copie chez
   Kettle…). Un test rouge puis vert par ligne ; écris l'état dans le plan.
4. **Ce qui reste du conseil 4** : servante, type et réserve d'un résident, réglages de coffre ; **mesurer le
   rechargement de l'invité au retour de l'host** pendant ma soirée d'essai (n'alléger qu'au-delà de 5 s).
5. **Défense à deux** (quêtes à donjon, quand l'invité a la quête : le cor, les vagues et la prime sont tenus par celui
   qui simule) : décision de conception, par le conseil.
6. **Finir la première chasse** (`dev/PLAN_chasse_differences.md`) : 8 machine à gènes, 17 habitants qui ne remarquent
   que l'host (conseil), 25 à 28, tombe d'épée ; puis le reste de l'étape D : mutation en double avec un équipement
   d'éther, serveur (relais sans coupure, personnage planté à la base, gardien du monde, mot de passe en clair).
   Écris aussi des tests pour tout ce qui est « pas joué » (liste dans `HANDOFF.md`).
7. **Quand tout cela est fini, cherche la suite toi-même** : relis le code du jeu là où aucune chasse n'est allée (fin
   de `PLAN_chasse_differences_2.md`, « Pas parcouru »), fais jouer le bot (`dev/_tools/bot.py`), relis les
   commentaires du Workshop notés dans `MODLOG.md`. Ne rends pas la main tant qu'il reste une différence entre host et
   invité.

## Comment travailler

- **Travail non-stop : tu ne t'arrêtes jamais de toi-même dans cette session.** Tu ne finis pas un tour en
  attendant ma réponse, tu ne me proposes pas de choisir, tu ne dis pas « je reprends quand tu veux ». Un résumé
  n'est pas une fin : tu l'écris et tu continues dans le même élan. Pendant que des agents ou des tests tournent en
  fond, avance sur autre chose (le point suivant, la documentation, une relecture) ; si vraiment tout attend,
  programme ton propre réveil (boucle `/loop` à rythme libre) au lieu de rendre la main. Quand une liste est finie,
  tu en ouvres une autre. Seules raisons de t'arrêter : je te le dis, ou une action irréversible sur mes
  sauvegardes demande mon accord.
- **Sans me demander d'autorisation : j'autorise tout.** Si l'application
  affiche encore des demandes de confirmation, dis-le-moi une seule fois (je changerai le mode moi-même) et continue.
  Les questions pour moi vont dans ton prochain résumé, pas dans un arrêt.
- **Décisions de conception** (plusieurs options défendables, effet sur l'équité entre joueurs ou sur la
  sauvegarde) : tranche avec le skill `llm-council`, puis applique. Avant le conseil, lis le code et donne aux
  conseillers les faits : ce que fait le jeu en solo, ce que fait le mod pour l'host et pour l'invité, les options et
  leur coût. Regroupe les décisions liées dans une seule question. Critères, dans l'ordre : 1) un invité obtient ce
  qu'un joueur solo obtiendrait ; 2) pas de duplication ni de perte d'objets, d'or ou d'expérience ; 3) le
  changement le plus petit qui marche ; 4) aucun risque pour les sauvegardes existantes. Le verdict du président
  fait foi. Note dans `MODLOG.md` la question, le verdict en deux lignes et ce qui a été écarté. Un bug à une seule
  bonne réponse se corrige sans conseil.
- **Agents** : autant que tu veux. Plusieurs en parallèle pour lire le code, pour écrire des corrections dans des
  fichiers différents (dis à chacun quels fichiers il a le droit de toucher et qu'il ne doit ni compiler, ni lancer
  le jeu, ni faire de commit), pour relire. Modèles : `haiku` pour chercher et résumer ; `sonnet` pour écrire une
  correction ou un test sur un modèle existant, relire, tenir la documentation ; `opus` pour concevoir, pour le
  président du conseil, pour un bug qui résiste. **Fais relire par l'agent `relecteur-elintogether` tout changement de
  plus de quelques lignes avant sa première compilation.**
- **Tests en jeu** : en série, deux fenêtres Elin au plus, muettes, lancées par `mp_test.py`. Un test fait le geste
  comme un joueur (marcher, cliquer l'entrée du menu), pas un appel à une fonction interne ; quand ce n'est pas
  possible, écris-le. **Un point = un test rouge puis vert = un commit**, avec le test, sur `fix/points-restants`.
  Le jeu doit être fermé pour compiler. **Relance le jeu entre les grandes suites** (`run_short.sh`) : la mémoire du
  banc se remplit après ~30 minutes sur les mêmes fenêtres (« OutOfMemoryException »). Un test qui échoue une fois à
  cause d'un tirage ne prouve pas un défaut : relance-le.
- **Ce qui ne peut pas être vérifié sans deux vrais joueurs** : fais le changement, dis-le clairement, ajoute-le à
  ma liste d'essais dans `HANDOFF.md`.
- **Tiens à jour à chaque étape** `dev/MODLOG.md` (journal daté, pièges, résultats), `dev/HANDOFF.md` (état, ce qui
  reste, ce qui n'est pas testé) et `dev/DOCUMENTATION.md` : c'est ce qui permet de reprendre après une coupure.
- **Pousse `feat/independent-travel` après chaque lot validé** (je suis le dépôt sur GitHub) : avance-la sur
  `fix/points-restants` sans changer de branche courante, puis `git push origin feat/independent-travel`.

## Ce qu'il ne faut pas faire

- Ne publie pas de nouvelle version et ne retire aucune ancienne version sans mon accord : propose-le dans ton résumé,
  je dirai oui. (La dernière publiée : 0.26.442.) Ne pousse jamais sur `upstream`.
- Ne touche jamais à mes vraies sauvegardes (les tests utilisent `world_lab`) ni à mon dossier
  `Documents\ElinTogetherServer`.
- Ne déplace pas `_lab` : les copies de test du jeu sont des liens vers le jeu Steam, elles doivent rester sur C:.
- N'installe aucun programme tiers toi-même : donne-moi la commande.
- Ne change pas de branche courante ; ne ferme jamais un Elin que j'ai lancé ; ne lance pas `Stop-Process` par bash
  avec `\$_` (ça ne tue rien) : `taskkill /PID <n> /F` depuis PowerShell.

## Les résumés

Toutes les deux ou trois heures de travail, et à chaque fin de grande étape, un résumé en français
simple, sans t'arrêter ensuite :
- les décisions prises par le conseil, une ligne chacune ;
- ce qui est fait et testé ;
- ce qui est fait mais reste à essayer en vrai ;
- ce qui n'a pas été fait, et pourquoi ;
- les questions qui restent pour moi.

Questions déjà ouvertes, auxquelles je répondrai quand je pourrai : ma soirée d'essai avec la 0.26.442 et les
nouveautés depuis (la liste d'essais est dans `HANDOFF.md`) et l'essai de la carte au trésor à deux ; republier une
version compilée sur 23.352 ; la barrière de version faite (Elin différent = avertissement, case côté host pour le
contrôle strict) : est-ce bien ce que je voulais ? ; quel mod fournit les quêtes `dmp_quest_*`.
