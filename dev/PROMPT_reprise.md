# Message de départ pour une nouvelle session

Pour un travail **sans arrêt**, tape `/loop` puis colle le texte ci-dessous juste après, dans une nouvelle session
ouverte dans **`G:\ElinMods`** (le dossier a été déplacé le 2026-10-04 ;
`C:\Users\steamdeckwin\Documents\ElinMods` n'est plus qu'un raccourci vers lui).

---

Je reprends le travail sur ElinTogether (le fork « indépendance »), dans `G:\ElinMods\ElinTogether`. Réponds-moi en
français simple et court, sans jargon : je ne lis pas le code.

## Le but

**Aucune différence entre un joueur host et un joueur invité. Tout doit être fluide, tous les joueurs doivent pouvoir
tout faire.** On doit pouvoir jouer à Elin à plusieurs comme si le jeu avait été fait pour ça. Je joue comme invité,
avec un seul ami comme host : chaque chose doit marcher dans les deux sens à deux joueurs.

## Pour commencer, dans cet ordre

1. Charge le skill `ponytail:ponytail` (le plus petit changement qui marche) et garde-le. Active Remote Control.
2. Lis : `CLAUDE.md`, puis `dev/HANDOFF.md` en entier (l'état exact, les branches, ce qui est rouge), la fin de
   `dev/MODLOG.md` à partir de « Points restants traités en autonomie », `dev/PLAN_egalite_invites.md`,
   `dev/PLAN_quetes_donjon_a_deux.md`, `dev/PLAN_chasse_differences.md`.
3. Vérifie l'état : `git status` et `git branch` dans `G:\ElinMods\ElinTogether`. Tu dois être sur
   **`wip/lots-non-compiles`**, sans changement en attente. Cette branche et `fix/points-restants` **n'existent que
   sur cette machine** : pas de `git pull`, ne les supprime pas, ne reviens pas sur `feat/independent-travel`.
4. Vérifie qu'aucun Elin ne tourne (ferme par numéro de processus, jamais un jeu que j'ai lancé), puis
   `powershell -ExecutionPolicy Bypass -File dev\build.ps1`.
5. Dis-moi en cinq lignes ce que tu as compris de l'état, puis enchaîne sans attendre ma réponse.

## Le travail, dans cet ordre

**A. Valider la branche `wip/lots-non-compiles`.** Elle contient trois lots écrits par des agents : ils compilent, le
jeu se lance, mais ils ne sont pas validés. Depuis `dev/`, avec `PYTHONPATH=_tools/pylib` :
`python _tools/mp_test.py` (host + 1 client ; s'il échoue juste après une autre suite, relance-le), puis :
- `python _tools/equal2_suite.py` : il était à 19/25. À comprendre **en premier** : pendant l'abattage d'un animal
  par l'invité, l'host lève `NullReferenceException` dans `CharaTickDelta` et l'animal n'est pas abattu chez lui.
  Puis : la source chaude n'arrive ni à l'invité ni à son compagnon ; le fanatique frappé n'appelle pas ses
  voisins. Pour chaque rouge, établis d'abord si c'est le test ou le code. « Quitter son dieu » est déjà vert.
- `python _tools/guest_suite.py --only g33,g34,g35` (ticket de meuble, seringue, puits) : jamais lancés. Traite
  aussi les remarques du relecteur notées dans `HANDOFF.md` (le puits lit les compteurs de l'host ; la laisse tire
  peut-être deux fois ; pas de test pour le stéthoscope ni la laisse).
- `python _tools/together_suite.py` (quêtes à donjon à deux quand l'host a la quête, boîte Oui/Non) : jamais lancé,
  jamais relu. Fais-le relire par l'agent `relecteur-elintogether` avant de le tester. Après un changement de texte,
  supprime `LangMod/EN/SourceLocalization.json` dans le mod installé.
Chaque point devenu vert est reporté sur `fix/points-restants` par un commit à lui (`git cherry-pick` ou un commit
propre), avec son test. Ce qui reste rouge après trois essais : note-le dans `MODLOG.md` et change d'approche.

**B. Quêtes à donjon à deux quand c'est l'invité qui a pris la quête** : étapes E5 et E6 de
`dev/PLAN_quetes_donjon_a_deux.md`. Les décisions sont déjà prises (conseil 3, dans `MODLOG.md`) : ne les rouvre pas.

**C. `dev/PLAN_chasse_differences.md`** : 28 différences trouvées en lisant le code, rien de joué. Pour chacune, un
test rouge d'abord (le même geste par l'invité puis par l'host), puis la correction. Commence par la peur à 20 % de
points de vie, le guérisseur payant, le rangement automatique, puis la liste des objets dont la fenêtre s'ouvre chez
tout le monde.

**D. Le reste de ma liste**, détaillé au point 4 de « À faire ensuite » dans `HANDOFF.md` : réglages de la base par
un invité, consigne « ne pas s'éloigner », karma sur la carte d'un invité, échange d'objets équipés, repos, retour
de l'host, autres mods, serveur, accidents rares.

**E. Quand tout cela est fini, cherche la suite toi-même** : relis le code du jeu là où la chasse n'est pas allée
(liste à la fin de `PLAN_chasse_differences.md`), fais jouer le bot (`dev/_tools/bot.py`), relis les commentaires du
Workshop notés dans `MODLOG.md`. Ne rends pas la main tant qu'il reste une différence entre host et invité.

## Comment travailler

- **Travail non-stop : tu ne t'arrêtes jamais de toi-même dans cette session.** Tu ne finis pas un tour en
  attendant ma réponse, tu ne me proposes pas de choisir, tu ne dis pas « je reprends quand tu veux ». Un résumé
  n'est pas une fin : tu l'écris et tu continues dans le même élan. Pendant que des agents ou des tests tournent en
  fond, avance sur autre chose (le point suivant, la documentation, une relecture) ; si vraiment tout attend,
  programme ton propre réveil (boucle `/loop` à rythme libre) au lieu de rendre la main. Quand une liste est finie,
  tu en ouvres une autre (étape E). Seules raisons de t'arrêter : je te le dis, ou une action irréversible sur mes
  sauvegardes demande mon accord.
- **Sans me demander d'autorisation : j'autorise tout.** Si l'application
  affiche encore des demandes de confirmation, dis-le-moi une seule fois (je changerai le mode moi-même) et continue.
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
  le jeu, ni faire de commit), pour relire. Fais relire par `relecteur-elintogether` tout changement de plus de
  quelques lignes avant sa première compilation. Modèles : `haiku` pour chercher et résumer ; `sonnet` pour relire,
  écrire une correction ou un test sur un modèle existant, tenir la documentation, les avis et relectures du
  conseil ; `opus` pour concevoir, pour le président du conseil, pour un bug qui résiste.
- **Tests en jeu** : en série, deux fenêtres Elin au plus, muettes, lancées par `mp_test.py`. Un test fait le geste
  comme un joueur (marcher, cliquer l'entrée du menu), pas un appel à une fonction interne ; quand ce n'est pas
  possible, écris-le. Un point = un test rouge puis vert = un commit, avec le test, sur `fix/points-restants`.
  Le jeu doit être fermé pour compiler.
- **Ce qui ne peut pas être vérifié sans deux vrais joueurs** : fais le changement, dis-le clairement, ajoute-le à
  ma liste d'essais dans `HANDOFF.md`.
- **Tiens à jour à chaque étape** `dev/MODLOG.md` (journal daté, pièges, résultats), `dev/HANDOFF.md` (état, ce qui
  reste, ce qui n'est pas testé) et `dev/DOCUMENTATION.md` : c'est ce qui permet de reprendre après une coupure.

## Ce qu'il ne faut pas faire

- Ne publie pas de version, ne pousse rien sur GitHub, ne retire aucune ancienne version : propose-le dans ton
  résumé, je dirai oui.
- Ne touche jamais à mes vraies sauvegardes (les tests utilisent `world_lab`) ni à mon dossier
  `Documents\ElinTogetherServer`.
- Ne déplace pas `_lab` : les copies de test du jeu sont des liens vers le jeu Steam, elles doivent rester sur C:.
- N'installe aucun programme tiers toi-même : donne-moi la commande.

## Les résumés

Toutes les deux ou trois heures de travail, et à chaque fin de grande étape (A, B, C…), un résumé en français
simple, sans t'arrêter ensuite :
- les décisions prises par le conseil, une ligne chacune ;
- ce qui est fait et testé ;
- ce qui est fait mais reste à essayer en vrai ;
- ce qui n'a pas été fait, et pourquoi ;
- les questions qui restent pour moi.

Questions déjà ouvertes, auxquelles je répondrai quand je pourrai : ma soirée d'essai avec la 0.26.399 et l'essai
de la carte au trésor à deux ; quel mod fournit les quêtes `dmp_quest_*`.
