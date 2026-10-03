# Prompt de reprise sur une autre machine (2026-10-03 au soir)

À coller dans une session Claude Code ouverte dans le dossier du dépôt (machine déjà installée, voir `SETUP.md`
sinon).

```
Je reprends le travail sur ElinTogether depuis cette machine. Fais d'abord `git pull` sur la branche
feat/independent-travel (et `git fetch` pour la branche wip/player-clock), puis lis dans cet ordre : CLAUDE.md,
la fin de dev/MODLOG.md (les trois dernières sections du 2026-10-03), dev/PLAN_retours_partie_reelle.md et la
section 7 de dev/DOCUMENTATION.md. Réponds-moi en français simple et court, sans jargon.

Où on en est : j'ai joué une vraie partie à deux PC comme invité avec la version publiée 0.26.337. J'ai signalé
quatre choses, plus une cinquième ensuite. Cinq corrections ont été faites et prouvées chacune par son test
(échec avant, réussite après), mais la passe complète a été interrompue et elles ne sont pas encore publiées :
  - un habitant de la base à qui un invité demande de rejoindre le groupe le suit maintenant (recruit_suite) ;
  - quand l'host revient sur une carte, l'invité reste à sa place et sa carte ne se recharge plus qu'une fois
    (leave_suite L2) ;
  - le mod Somewhat Enhanced Display ne produit plus une erreur par image après une session (compat_suite) ;
  - le bonus de première fabrication d'un invité (player_suite F6) ;
  - un invité seul sur sa carte peut dormir (sleep_suite Y1 : la limite notée n'existait pas).

Ce que je veux, dans cet ordre :

1. Vérifie que le banc marche ici (dev/build.ps1, puis mp_test.py), lance la passe complète des suites sur le code
   actuel (run_all.sh pour les longues, run_short.sh pour les courtes, avec recruit_suite et compat_suite en
   plus), corrige ce qui casse, puis publie une nouvelle version sur GitHub comme les précédentes (préversion,
   étiquette independance-<version>, note en anglais avec un résumé en français, zip vérifié identique). Dis-moi
   s'il faut retirer l'ancienne version de la page.

2. Fluidité des déplacements d'un invité : ils sont moins fluides que ceux de l'host. La cause a été lue dans le
   code (chez un client, chaque pas attend le temps de jeu de l'host reçu par le réseau) et une correction est
   écrite sur la branche wip/player-clock, JAMAIS lancée en jeu. Joue dev/_tools/move_suite.py sur le code actuel
   (un échec est attendu sur V2), puis sur la branche, puis combat_suite, guest_suite et sleep_suite. Si c'est bon,
   fusionne et mets-le dans la version. Regarde aussi le second point noté dans le journal (le rythme des pas
   dépend de l'écart de vitesse entre les joueurs) et dis-moi ce que tu proposes avant de le changer.

3. Je veux pouvoir rejoindre une partie avec un personnage d'une de mes sauvegardes solo. Le plan est dans
   dev/PLAN_retours_partie_reelle.md (version 1 : le personnage, son équipement, son sac, son or, sa renommée et
   son karma ; pas ses compagnons ni sa base ; la sauvegarde solo n'est jamais modifiée ; une case côté host).

4. Les autres façons de recruter un compagnon pour un invité (boule à monstre, domptage, monture, œuf : il suit
   l'host ; animal ou esclave acheté : il est perdu).

5. Ensuite seulement, et en me demandant avant de commencer chacun : le retour de l'host sans rechargement
   (plan B), le profil de mods (dev/PLAN_profil_mods.md), la touche « signaler un problème », le bot qui rejoue
   une vraie soirée et le faux réseau lent, le temps du monde commun et le serveur indépendant.

Règles : celles de CLAUDE.md. En particulier, teste comme un joueur joue (marcher, passer par les vrais dialogues
et menus, pas par des raccourcis) ; un changement = un test rouge puis vert = un commit ; ne lance des fenêtres
de jeu que si je ne me sers pas du PC (demande-moi en cas de doute) ; ferme tes fenêtres par numéro de processus,
jamais un jeu que j'ai lancé ; tiens dev/MODLOG.md et dev/DOCUMENTATION.md à jour et pousse sur GitHub à chaque
étape, parce que je change de machine. Si je dois jouer avec mon ami, remets dans le jeu une version publiée
(le build de test ne se connecte pas à la sienne).

Commence par me dire en quelques lignes ce que tu as compris de l'état et ce que tu lances en premier.
```

## À savoir pour la session qui reprend

- Sur l'ancienne machine, le jeu a la version publiée 0.26.337 et aucune modification locale n'attend : tout est
  sur GitHub (branche `feat/independent-travel` à jour, branche `wip/player-clock` pour le travail jamais lancé).
- GitHub répondait par une erreur 503 aux pages web depuis l'ancienne machine le 2026-10-03 (git et l'API
  marchaient) : la publication s'y fait par l'API avec l'identifiant déjà enregistré par git.
- Le mod Workshop « Somewhat Enhanced Display » (3781674985) est installé chez l'utilisateur, absent de
  `loadorder.txt` donc activé d'office ; `compat_suite.py` saute son test s'il n'est pas installé sur la machine.
