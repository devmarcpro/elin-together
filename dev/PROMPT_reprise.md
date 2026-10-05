# Message de départ pour une nouvelle session

Pour un travail **sans arrêt**, tape `/loop` puis colle le texte ci-dessous juste après, dans une nouvelle session
ouverte dans **`G:\ElinMods`** (le dossier a été déplacé le 2026-10-04 ;
`C:\Users\steamdeckwin\Documents\ElinMods` n'est plus qu'un raccourci vers lui). État décrit : 2026-10-05, 14h45 (session arrêtée à ma demande pour compacter ; rien en cours, arbre propre).

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
   `dev/MODLOG.md` à partir de « Étape D suite, Elin 23.352 » (deux entrées : celle-là et « Étape E commencée »), `dev/PLAN_chasse_differences_2.md` (la liste de travail
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
chasse aux différences (lue ; ses lignes 2, 5 et 6 sont corrigées et testées : rondin à la hache, prière qui soigne
les compagnons, nourriture du sac ; `hunt2_suite.py` 21/21), la barrière de version d'Elin levée (`version_suite`
8/8). Tout est poussé sur GitHub ; le dernier commit est `docs: step E started, state for a restart`. Le jeu de cette
machine contient un build de TEST (Debug) : avant de jouer avec quelqu'un, installe le zip de la version publiée.

1. **Jouer la barrière de version** (faite à 14h15, commit `ee374b7`, `version_suite` 8/8 en connexion locale). Ma
   demande : « rendre les futures versions du mod compatibles avec les futures versions d'Elin sans forcément le mettre
   à jour, ne pas avoir de barrière ». Maintenant seule la version du MOD doit être la même ; une version d'Elin
   différente = un avertissement ; une case côté host revient au contrôle strict. Le chemin par le salon Steam n'est pas
   joué : à essayer à deux PC (ma liste d'essais, point 9), rien à réécrire avant.
2. **Publier une nouvelle version, compilée sur Elin 23.352 : j'ai dit OUI le 5 octobre à 14h40.** C'est la première
   chose à faire. Dans l'ordre : (a) `dev\build.ps1`, puis les suites larges, chacune sur un jeu relancé :
   `bash _tools/run_short.sh pub equal2_suite council_suite hunt_suite hunt2_suite together_suite death_suite
   parity_suite sleep_suite recruit_suite quest_suite instance_suite trade_suite base_suite setting_suite
   unplayed_suite version_suite leave_suite guest_suite`, puis `travel_suite` seule (elle lance le jeu elle-même) ; un
   rouge isolé se relance seul avant de conclure. (b) Mets à jour les README (4 langues : nouveautés et limites depuis
   la 0.26.442, « compilé pour EA 23.352 », la ligne sur les versions d'Elin différentes) et refais les captures
   (`python _tools/showcase.py`) si une nouveauté se montre. (c) `dev/NOTE_version.md` : nouvelle note (français puis
   anglais) pour cette version. (d) Avance `feat/independent-travel`, `git checkout feat/independent-travel` le temps
   de `dev\make_release.ps1` (le numéro de version vient du nombre de commits : lis-le sur la DLL installée), copie
   le zip sous `dev/_release/ElinTogether-independance-<version>.zip`, pousse, puis
   `python dev/_tools/publish_release.py <version> <commit entier> dev/NOTE_version.md dev/_release/ElinTogether-independance.zip`
   (il vérifie que le zip en ligne est identique). Reviens sur `fix/points-restants` et refais `dev\build.ps1`.
   (e) Donne-moi le lien et dis-moi ce qui n'a pas été rejoué.
3. **Étape E = `dev/PLAN_chasse_differences_2.md`** (37 lignes lues dans le code ; 2, 5 et 6 faites). Le plus gros
   d'abord : **ligne 1, le mode construction d'un invité** (il paierait matériaux et or sans que rien ne se construise
   chez l'host ; ses marques « miner / couper… » ne seraient jamais vues des habitants ; ce que l'host construit
   n'apparaîtrait pas chez l'invité) avec les lignes 3 et 4. Marche à suivre : un agent `sonnet` en lecture seule écrit
   les faits dans `dev/PLAN_construction_invite.md` (comment marche le mode construction en solo, ce que fait le mod
   pour chaque geste, comment les cases de la carte sont tenues à jour entre les jeux, 2 à 4 options avec leur coût,
   comment un test peut faire le geste) ; un test rouge prouve le défaut ; le conseil tranche ; puis écriture, relecture,
   test. (Cet agent avait été lancé puis arrêté à 14h45 : le fichier n'existe peut-être pas, relance-le.) Ensuite :
   8 résurrection d'un compagnon, 7 réglages de coffre (étendre `InvSaveDataDelta`), 9 copie chez Kettle, 10 duel
   d'autel, 11, puis les « sûr » du bas : 25 prière sans dieu, 26 prix d'expédition, 30 carte à gratter du casino,
   33 jours et relance des quêtes, 36 Mifu / Nefu / Aquli. Un test rouge puis vert par ligne ; écris l'état dans le
   plan.
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

- Ne publie pas d'autre version que celle du point 2 (déjà accordée) et ne retire aucune ancienne version sans mon
  accord : propose-le dans ton résumé, je dirai oui. (La dernière publiée : 0.26.442.) Ne pousse jamais sur `upstream`.
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
nouveautés depuis (la liste d'essais est dans `HANDOFF.md`) et l'essai de la carte au trésor à deux ; (republier sur 23.352 : j'ai dit oui) ; la barrière de version faite (Elin différent = avertissement, case côté host pour le
contrôle strict) : est-ce bien ce que je voulais ? ; quel mod fournit les quêtes `dmp_quest_*`.
