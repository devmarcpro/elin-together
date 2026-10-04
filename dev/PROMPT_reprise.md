# Message de départ pour une nouvelle session

À coller tel quel dans une nouvelle session ouverte dans `Documents\ElinMods` (ou dans le dépôt).

---

Je reprends le travail sur ElinTogether (le fork « indépendance »), dans `ElinTogether\`. Charge d'abord le skill
`ponytail:ponytail` et garde-le pour toute la session ; charge aussi `universal-modder` si le travail s'y prête.
**Active Remote Control tout de suite.** Fais `git pull` sur la branche `feat/independent-travel`, puis lis dans
cet ordre : `CLAUDE.md`, `dev/HANDOFF.md`, la fin de `dev/MODLOG.md` (les sections du 2026-10-04) et la section 7
de `dev/DOCUMENTATION.md`. Réponds-moi en français simple et court, sans jargon.

Où on en est (4 octobre, 22h) : la version publiée est la 0.26.399 ; c'est elle qui est dans le jeu de cette
machine, avec toutes les corrections du serveur (« Join by address » pour les deux modes, logiciel serveur en
anglais, parcours du premier joueur). La passe large sur le code final est faite (22 suites ; deux tests fragiles
notés : `leave_suite` L2 et `time_suite` W3) et les boutons du logiciel sont joués par `server_ui_test.ps1`.
**Avant tout test : `dev/build.ps1`** (le jeu a la version publiée, pas le build de test). Pas encore fait : ma
soirée d'essai avec la 0.26.399 (deuxième joueur par Steam, hébergeur qui part, mode avec Elin entre deux PC,
Internet) ; me demander ce que j'en dis.

Ce que je veux :

1. Dis-moi en quelques lignes ce que tu as compris de l'état, et ce qui n'est pas testé.
2. Ensuite enchaîne sur la liste « À faire ensuite » de `dev/HANDOFF.md`, sans attendre. Pose-moi seulement les
   questions de la liste « décisions qui restent à lui » ; mets les autres questions dans ton résumé.

Instructions permanentes (4 octobre) :
- **Carte blanche** (« j'autorise tout ») : ne t'arrête pas pour demander. Prends le choix que tu recommandes, note-le
  dans `dev/MODLOG.md`, avance.
- **Plusieurs agents en parallèle** pour décider et pour relire, quand les questions sont indépendantes.
- **Remote Control activé au début de chaque session.**
- **Tout ce que je vois dans le logiciel serveur doit être en anglais.**
- **Écris toujours tout ce qui reste à faire** (dans `dev/HANDOFF.md`), à chaque étape.
- Trois dépôts que je veux voir utilisés : `DeusData/codebase-memory-mcp` (je l'installe moi-même avec
  `install.ps1` dans `Documents\ElinMods`, puis je relance Claude Code : cherche ses outils avec ToolSearch
  « codebase-memory » et, s'ils sont là, utilise-les pour chercher dans le code à la place des agents haiku ;
  indexe le mod et `Documents\ElinMods\_decomp`) ; `msitarzewski/agency-agents` (le relecteur
  `Documents\ElinMods\.claude\agents\relecteur-elintogether.md` en vient : utilise-le pour les relectures) ;
  `trailhq/Graft` : écarté (en double, plus lourd). **N'installe jamais un programme tiers toi-même** : dis-moi la
  commande, je la lance.
- Le serveur `fal` de `universal-modder` a échoué (jeton refusé, HTTP 401) : dis-moi si tu as besoin d'art ou de
  son généré, je renouvellerai le jeton.
- À me demander avant de commencer (liste inchangée) : le relais sans coupure quand l'hébergeur part ; quoi faire
  quand un joueur meurt sur la carte de l'host et quand la connexion tombe ; les six inégalités en attente
  (`PLAN_egalite_invites.md`) ; retour de l'host sans rechargement, profil de mods, touche « signaler un
  problème », bot qui rejoue une soirée, faux réseau lent ; retirer les dix anciennes versions de GitHub ; un serveur sur mon NAS Synology.
- Question ouverte pour moi : quel mod fournit les quêtes `dmp_quest_*` (les « Dummy / Mokyu »).

Modèles : je ne veux pas que tout passe par le modèle le plus cher. Choisis le modèle selon la tâche et
dis-le-moi en une ligne quand tu délègues.
- **Le plus petit modèle (haiku)**, par un agent : chercher dans le code ou dans le code décompilé, lire un
  journal de test ou de jeu et en sortir les échecs, lister des fichiers, résumer un document. Tout ce qui est
  « trouve et rapporte ».
- **Le modèle intermédiaire (sonnet)**, par un agent : relire un changement avant sa première compilation,
  recenser ce qu'un chantier touche, écrire un test sur le modèle d'un test existant, mettre à jour la
  documentation et le journal à partir de faits que tu lui donnes.
- **Le gros modèle (opus)** seulement pour : concevoir (serveur, protocole, ce qui change l'architecture),
  comprendre un bug qui résiste après deux essais, trancher entre deux rapports qui se contredisent.
- Toi, dans la session principale : garde les tests en jeu, les commits et les décisions. Ne délègue pas ce qui
  tient en deux ou trois commandes, et ne lance pas plusieurs agents pour la même question.
- Pendant qu'une suite de tests tourne, n'occupe pas le temps avec du travail en plus : attends le résultat.
- Si une tâche simple s'annonce longue (beaucoup de lecture, de la paperasse), propose-moi de passer la session
  sur un modèle plus petit plutôt que de la faire au prix fort ; redemande le gros modèle quand il le faut.

Règles : celles de `CLAUDE.md`. En particulier : un changement = un test rouge puis vert = un commit ; teste
comme un joueur joue ; **pas plus de deux fenêtres Elin à la fois sur cette machine** (pas de `trio_suite`), et
seulement si je ne me sers pas du PC ; ferme tes fenêtres par numéro de processus, jamais un jeu que j'ai lancé ;
tiens `dev/MODLOG.md`, `dev/DOCUMENTATION.md` et `dev/HANDOFF.md` à jour et pousse sur GitHub à chaque étape ;
avant que je joue avec mon ami, remets une version publiée dans le jeu. Quand je te dis de continuer sans
t'arrêter, ne t'arrête pas pour me poser des questions : prends le choix que tu recommandes, note-le, avance.
Ne retire pas d'anciennes versions de la page GitHub sans mon accord.
