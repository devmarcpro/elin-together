# Message de départ pour une nouvelle session

À coller tel quel dans une nouvelle session ouverte dans `Documents\ElinMods` (ou dans le dépôt).

---

Je reprends le travail sur ElinTogether (le fork « indépendance »), dans `ElinTogether\`. Charge d'abord le skill
`ponytail:ponytail` et garde-le pour toute la session. Fais `git pull` sur la branche `feat/independent-travel`,
puis lis dans cet ordre : `CLAUDE.md`, `dev/HANDOFF.md`, la fin de `dev/MODLOG.md` (les sections du 2026-10-04),
et la section 7 de `dev/DOCUMENTATION.md`. Réponds-moi en français simple et court, sans jargon.

Où on en est : la version publiée est la 0.26.390, c'est elle qui est dans le jeu de cette machine. Elle contient
la fluidité des déplacements d'un invité, l'import d'un personnage d'une sauvegarde solo, les compagnons d'un
invité, une seule date et un seul « monde » pour tous, et surtout **Elin Together Server** : un petit logiciel
serveur (`ElinTogetherServer.exe`) avec deux modes, « sans Elin » (il garde le monde, les joueurs l'hébergent,
on choisit la sauvegarde dans le logiciel) et « avec Elin sur ce PC » (le monde tourne en permanence, on rejoint
par adresse). Tout a été testé entre deux fenêtres de ce PC, rien entre deux PC.

Ce que je veux :

1. Dis-moi en quelques lignes ce que tu as compris de l'état, et ce qui n'est pas testé.
2. Ensuite je te dirai ce que mon essai du serveur a donné, ou la suite que je veux. Tant que je n'ai rien dit,
   ne lance pas de gros chantier : propose-moi la suite de `dev/HANDOFF.md` et attends ma réponse.

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
