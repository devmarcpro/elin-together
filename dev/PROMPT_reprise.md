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

Règles : celles de `CLAUDE.md`. En particulier : un changement = un test rouge puis vert = un commit ; teste
comme un joueur joue ; **pas plus de deux fenêtres Elin à la fois sur cette machine** (pas de `trio_suite`), et
seulement si je ne me sers pas du PC ; ferme tes fenêtres par numéro de processus, jamais un jeu que j'ai lancé ;
tiens `dev/MODLOG.md`, `dev/DOCUMENTATION.md` et `dev/HANDOFF.md` à jour et pousse sur GitHub à chaque étape ;
avant que je joue avec mon ami, remets une version publiée dans le jeu. Quand je te dis de continuer sans
t'arrêter, ne t'arrête pas pour me poser des questions : prends le choix que tu recommandes, note-le, avance.
Ne retire pas d'anciennes versions de la page GitHub sans mon accord.
