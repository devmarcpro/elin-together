# Passation — ElinTogether « indépendance », état au 2026-10-04, 17h40

À lire en premier par la session suivante. Le détail daté est dans `MODLOG.md` (fin du fichier), le mode d'emploi
dans `DOCUMENTATION.md`, les règles dans `../CLAUDE.md`.

## Où on en est

- Branche `feat/independent-travel`, tout est poussé sur GitHub. Dernière version publiée : **0.26.390**
  (préversion `independance-0.26.390`), et **c'est elle qui est installée dans le jeu de cette machine**
  (Steam Deck sous Windows). Avant tout test : `dev/build.ps1` (remet le build de test). Avant que
  l'utilisateur joue avec son ami : remettre une version publiée (`make_release.ps1`, ou recopier le dossier
  `Mod_ElinTogether` d'un zip de `dev/_release/` dans `Elin\Package`).
- Elin : EA 23.351 Patch 2, canal Nightly. Si Steam met le jeu à jour : `make_lab.py Elin2 2` (3, 4), sinon le
  client de test est refusé (« invalid version ») sans message clair.
- Aucun jeu ni serveur ne tourne. Rien n'est en cours.

## Ce qui a été fait depuis la reprise sur cette machine (3 au soir → 4 octobre)

| Sujet | Commit clé | Test |
|---|---|---|
| Cinq corrections de la première vraie partie (habitant recruté, retour de l'host, première fabrication, Somewhat Enhanced Display, sommeil) | publiées en 0.26.349 | passe complète 21/21 |
| Déplacements d'un invité aussi fluides que ceux de l'host (`PlayerClock`), « chacun marche comme en solo » (`PlayerStepPace`), accéléré partagé | `48930ce`, `5584c51`, `6af7ffa` | `move_suite` 18/18 |
| Rejoindre avec un personnage d'une sauvegarde solo, nuage Steam compris (`ImportCharacter`, décochée par défaut) | `6d43567`, puis la correction du nuage | `import_suite` 27/27 |
| Compagnons d'un invité : boule à monstre, monture, achat, brosse (avec son propre charisme), marque de l'animal de Fiama | `7b0c70e`, `d3d5622`, `d7a83ab` | `recruit_suite` 45/45 |
| Une seule date pour le monde (`SharedWorldTime`) | `a76d6a9` | `time_suite` 14/14 |
| Ce que le temps fait au monde n'arrive qu'une fois : météo, impôts, salaires, colis, chance du jour (`WorldKeeper`) | `1b0f5c3`, `856d878` | `world_suite` 11/11 |
| Dépôt de sauvegarde : le monde vit dans un dépôt, le premier arrivé l'héberge (`SaveDepot.cs`, réglage « Depot ») | « a save depot » | `depot_suite` 11/11 |
| Serveur « comme Minecraft » : `Elin.exe -empserver <sauvegarde>`, « Join by address » | « a server like a Minecraft server » | `server_suite` 9/9 |
| **Elin Together Server**, le logiciel (`dev/server/`, `ElinTogetherServer.exe`, 26 Ko) : mode sans Elin (garde le monde, vrai verrou, choix de la sauvegarde) et mode avec Elin (sans fenêtre) | `7e0a4ea`, `452f89e` | `depot_suite` avec `DEPOT_SERVER=1` 11/11 |

Dernière passe large (sur le code de 0.26.375) : 24 suites sur 25 vertes. Depuis, seules les suites touchées par
chaque ajout ont été rejouées.

## Ce que l'utilisateur veut (dans ses mots)

- But du fork : en jeu, aucune différence entre l'host et les autres joueurs.
- Serveur : « un programme qui héberge une sauvegarde et les joueurs s'y connectent, toute la simulation est
  gérée par les joueurs, un joueur simule une carte ». Puis : « héberger un serveur comme un serveur Minecraft »
  sur son PC de dev, « un vrai logiciel avec une interface, le plus light possible », « pas besoin d'avoir une
  copie d'Elin pour que ça tourne », et « sélectionner la sauvegarde, c'est un peu tout l'intérêt ».
- Travail : continuer sans s'arrêter ni poser de questions quand il l'a dit (prendre le choix recommandé, le
  noter, avancer) ; utiliser les skills **ponytail** (la plus petite solution qui marche) ; réponses courtes en
  français simple ; **pas plus de deux fenêtres Elin à la fois** sur cette machine (« c'est trop 4 clients »,
  une autre session y travaille sur un serveur privé Dofus) : ne pas lancer `trio_suite`.

## Ce qui n'est pas testé (à dire tel quel si on en parle)

- Rien de ce qui touche au serveur n'a été joué **entre deux PC** ni par Internet : tout entre deux fenêtres ici.
  Ports : TCP 55557 (sans Elin), UDP 55556 (avec Elin), ou un réseau privé (Tailscale, ZeroTier).
- Mode avec Elin : le même compte Steam sur le PC serveur et sur le PC où il joue en même temps (Steam peut
  refuser). Le test local a marché avec serveur et joueur sur le même compte, sur une seule machine.
- Les boutons du logiciel ne sont pas joués par un test (le test le lance par sa ligne de commande :
  `--depot <dossier> --port N --import <sauvegarde>`). Le bouton « Parcourir » et le mode « avec Elin » lancé
  depuis le logiciel n'ont pas été essayés à la main non plus.
- Le dépôt n'est pas chiffré (mot de passe en clair). Sans Elin, quand l'hébergeur part pendant que d'autres
  jouent, ils reviennent à l'écran titre et l'un d'eux reprend le monde au serveur.
- `trio_suite` (4 fenêtres) : verte sur `a76d6a9`, pas rejouée depuis.
- Fluidité : mesurée au banc, pas entre deux PC ; marche touche enfoncée non testée.
- Import d'un personnage : essayé au niveau 1 et avec un vrai personnage de niveau 4, pas avec une grosse sauvegarde.

## À faire ensuite (dans cet ordre, sauf avis contraire de l'utilisateur)

1. **Son essai réel** du serveur avec son ami (les deux modes), et ce qu'il en dit.
2. Si le mode sans Elin lui convient : le **relais sans coupure** quand l'hébergeur part (plan long, étapes 3 et 4
   de `PLAN_serveur_depot.md` : arriver sans passer par la carte de l'host, l'host peut partir). Gros.
3. Petites améliorations possibles du logiciel, seulement s'il les demande : plusieurs mondes, chiffrement,
   journal visible, icône, interface en anglais.
4. Ce qu'il avait demandé de ne commencer **qu'après lui avoir demandé**, un par un : retour de l'host sans
   rechargement (plan B de `PLAN_retours_partie_reelle.md`), profil de mods (`PLAN_profil_mods.md`), touche
   « signaler un problème », bot qui rejoue une vraie soirée, faux réseau lent.
5. **Page des versions GitHub** : neuf anciennes préversions y sont encore (0.26.388, .385, .382, .375, .366,
   .362, .349, .337, .309). Aucune ne se connecte à la 0.26.390. Ne pas les retirer sans son accord (il n'a pas
   répondu à la question).

## Aide-mémoire

```
powershell -ExecutionPolicy Bypass -File dev\build.ps1            # build de test dans le jeu (jeu fermé)
cd dev && set PYTHONPATH=_tools/pylib
python _tools/mp_test.py                                         # host + 1 client
python _tools/depot_suite.py            (DEPOT_SERVER=1 : à travers Elin Together Server)
python _tools/server_suite.py           (SERVER_ARGS="-batchmode -nographics" : serveur sans fenêtre)
bash _tools/run_short.sh <nom> quest_suite chara_suite ...        # suites à 2 fenêtres, monde neuf à chaque fois
bash _tools/run_all.sh <nom> travel_suite shared_suite ...        # suites qui lancent leurs fenêtres (3 pour shared, economy, combat, party)
powershell -ExecutionPolicy Bypass -File dev\server\build.ps1     # recompile ElinTogetherServer.exe
powershell -ExecutionPolicy Bypass -File dev\make_release.ps1     # zip (contient le logiciel) ; laisse le build Release dans le jeu
python dev/_tools/publish_release.py <version> <commit entier> <note.md> dev/_release/ElinTogether-independance.zip
```

Pièges du jour, à relire dans `MODLOG.md` avant de tomber dedans : l'outil Bash casse `\\n` et certains scripts
en ligne (écrire les fichiers C# et les scripts Python avec l'outil d'écriture) ; arrêter une tâche de fond ne
ferme ni les scripts ni les jeux (les fermer par numéro de processus) ; `mp_test.py` lancé juste après
`run_short.sh` échoue (« Elin tourne déjà ») ; `EClass.pc` lève une exception sans jeu ; plusieurs
`[HarmonyPatch]` sur une méthode ne font qu'une cible ; `move_suite` est sensible à la souris et au clavier.
