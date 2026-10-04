# Passation — ElinTogether « indépendance », état au 2026-10-05, 0h20

À lire en premier par la session suivante. Détail daté : fin de `MODLOG.md` (« Points restants traités en
autonomie »). Mode d'emploi : `DOCUMENTATION.md`. Règles : `../CLAUDE.md`. Message de départ : `PROMPT_reprise.md`.

## Où on en est

- **Le dossier de travail est maintenant `G:\ElinMods`** (C: était plein). `C:\Users\steamdeckwin\Documents\ElinMods`
  n'est plus qu'une suite de raccourcis vers G:. Seul `_lab` (les copies de test du jeu, des liens vers le jeu
  Steam) est resté sur C:. **Ouvrir la session depuis `G:\ElinMods`** : ouverte depuis C:, l'application demande une
  autorisation à chaque écriture.
- Dernière version **publiée** : 0.26.399 (inchangée). Rien n'a été poussé sur GitHub ni publié cette nuit.
- Le jeu de cette machine a un **build de test de la branche `wip/lots-non-compiles`** : avant de jouer avec
  quelqu'un, `Installer.bat` du zip 0.26.399 ; avant tout test, `dev/build.ps1`.
- Deux branches locales, parties de `feat/independent-travel` (`e08310a`) :
  - **`fix/points-restants`** : tout y est compilé et testé en jeu, sauf la carte au trésor (voir plus bas).
  - **`wip/lots-non-compiles`** (branche courante) : `fix/points-restants` + trois lots écrits par des agents. Ils
    compilent, le jeu se lance et un invité se connecte, mais **ils ne sont pas validés** (voir « À faire ensuite »).
- Consignes de l'utilisateur (4 octobre au soir) : **aucune différence entre un joueur host et un joueur invité,
  tout doit être fluide, tous doivent pouvoir tout faire** ; travailler en continu sans s'arrêter ni demander
  d'autorisation (« j'autorise tout ») ; autant d'agents que nécessaire ; les décisions de conception sont tranchées
  par le skill `llm-council` (critères dans l'ordre : l'invité obtient ce qu'un solo obtiendrait ; pas de
  duplication ni de perte ; le plus petit changement ; aucun risque pour les sauvegardes).

## Fait et testé cette nuit (branche `fix/points-restants`)

| Point | Commit | Test |
|---|---|---|
| Mort : l'invité qui meurt chez l'host après le jour 90 perd une part de son or (elle tombe par terre), lettre de testament comprise | `d9df4f6` | `council_suite` C2 |
| Prime de la guilde des guerriers : au joueur derrière le tueur | `a5d764a` | C3 |
| Cadeaux du dieu : chaque joueur reçoit une fois son familier et son artefact | `78c345d` | C4 |
| Pièges : tirés dans le jeu de celui qui marche dessus ; sommeil, cécité, paralysie demandés à l'host | `31c0c28` | C5 |
| Grimoires : tirés dans le jeu du lecteur ; un échec use le livre chez l'host | `202f026` | C1 (passait déjà avant : le double échec n'est pas prouvé corrigé) |
| Bénédiction du dieu d'un invité calculée comme celle d'un joueur | `e08940c` | `guest_suite` G31 |
| Autels (invention, soin…) : pour celui qui les touche, une seule recette pour tous | `5ee3209` | G32 |
| Non-régression sur ce code | | death 11/11, guest 220/220, parity 15/15, sleep 32/32, recruit 45/45 |

**Fait, pas vérifié en jeu** : carte au trésor (`4b45541`). Le banc n'arrive pas à faire creuser l'invité sur la
carte du monde comme un joueur (`council_suite --only c6`). → liste d'essais de l'utilisateur.

Décisions du conseil (détail dans `MODLOG.md`) : compte de cadeaux du dieu par joueur ; prime au tueur ; pénalité de
mort du solo pour l'invité, sans case ; carte au trésor cherchée chez celui qui creuse ; pièges et grimoires tirés
dans le jeu du joueur concerné ; quêtes à donjon à deux : boîte Oui/Non, récompense au preneur, tout le monde sort
avec le preneur, l'accompagnant peut rentrer seul, pas de nouvelle case.

## Les trois lots de `wip/lots-non-compiles` (écrits par des agents, compilent, **pas validés**)

1. **Gestes tenus en main rejoués chez l'host** (`Models/Delta/Card/CardActReplayDelta.cs`, union 817,
   `Patches/DeltaEvents/Card/CardActReplayEvent.cs`, `CharaMoveDelta.cs`) : ticket de meuble, seringues,
   stéthoscope, laisse, puits. Tests `guest_suite` G33 (ticket), G34 (seringue), G35 (puits) : **jamais lancés**.
   Remarques du relecteur à traiter : le puits lit les compteurs de l'host (`well_wish`, `wellWished` : un invité
   pourrait consommer la clé de l'host et ouvrir la fenêtre de vœu chez l'host → poser `wellWished = true` le temps
   du rejeu) ; les effets du puits sur les éléments (potentiel, mutation) touchent la copie de l'host, peut-être
   perdus ; laisse : le compagnon est peut-être tiré deux fois (jeu de l'invité + host) ; portée de 2 cases sans
   regarder les murs ; pas de test pour stéthoscope, laisse, les trois autres seringues, ni pour un refus.
2. **Appel à l'aide, abattage, dieu quitté, source chaude** (`Patches/Remote/RemoteHostilePatch.cs`,
   `Patches/DeltaEvents/Task/AISlaughterPatch.cs`, `CharaFaithDelta.cs`, `CharaFaithEvent.cs`,
   `AIPassTimePatch.cs`). Test `equal2_suite.py`, **lancé une fois : 19/25** (`_shots/equal2_suite-premier.log`) :
   - E3 dieu quitté : **vert** (une colère, une boule, jours remis à 0, des deux côtés ; exceptions du jeu
     respectées). Reste : la colère est au tarif de base chez l'host (les jours avec le dieu ne comptent pas).
   - E1 appel à l'aide : l'ami frappé une fois reste neutre (**vert**) ; le fanatique n'appelle pas ses voisins
     (rouge : 0 sur 4 ; test ou code, à voir).
   - E2 abattage : le chat n'est pas abattu chez l'host (rouge) ; l'host lève `NullReferenceException` dans
     `CharaTickDelta` au même instant, et « Progress begin … has no matching act ». **À comprendre en premier.**
   - E4 source chaude : ni l'invité ni son compagnon ne la reçoivent (rouge ; test ou code).
3. **Quêtes à donjon à deux, sens « l'host a la quête »** (`Patches/ZoneEvents/QuestZoneVisitorPatch.cs` qui
   remplace `ZoneEventHarvestPatch.cs`, `Models/Delta/Quest/QuestFollowDelta.cs` union 819, `FollowHost()`,
   boîte Oui/Non 15 s, textes EN/JP/CN ajoutés au xlsx et au json). Test `together_suite.py` T1 à T5 : **jamais
   lancé**. Après un changement de texte : supprimer `LangMod/EN/SourceLocalization.json` dans le mod installé.
   Pas relu par le relecteur.

## Ce qui n'est pas testé (à dire tel quel)

- Tout le point 1 de la liste de l'utilisateur (ses essais à deux PC) : deuxième joueur par Steam, hébergeur qui
  part, mode avec Elin entre deux PC, Internet avec mot de passe.
- La carte au trésor d'un invité sur la carte du monde avec l'host.
- Les trois lots de la branche `wip`.
- Limites connues des corrections de cette nuit : sur une lecture ratée par un invité, ni confusion ni monstres ; un
  piège d'acide ou de malédiction n'abîme l'équipement que dans le jeu de l'invité (pas vérifié) ; un invité qui prie
  seul en voyage puis chez l'host pourrait recevoir un cadeau deux fois (pas vérifié) ; l'or perdu à la mort est
  ramassable par n'importe quel joueur ; les jours passés avec son dieu ne sont comptés que dans le jeu de l'invité.

## À faire ensuite, dans l'ordre

1. **Valider la branche `wip/lots-non-compiles`**, lot par lot : `dev/build.ps1`, `mp_test.py`, puis
   `equal2_suite.py` (comprendre E2 d'abord : l'exception chez l'host), `guest_suite.py --only g33,g34,g35`,
   `together_suite.py`. Corriger, faire relire, et reporter chaque point vert sur `fix/points-restants` (un commit
   par point). Traiter les remarques du relecteur listées plus haut.
2. **Quêtes à donjon à deux, sens « l'invité a la quête »** : étapes E5 et E6 de `PLAN_quetes_donjon_a_deux.md`.
3. **`PLAN_chasse_differences.md`** : 28 différences trouvées par lecture, pas encore prouvées. En tête : la peur à
   20 % de points de vie qui empêche un invité de frapper, le guérisseur payant sans effet, le rangement
   automatique qui dérange l'host, puis la liste des objets dont la fenêtre s'ouvre chez tout le monde.
4. Reste de la liste de l'utilisateur, pas commencé :
   - réglages de la base faits par un invité (M14 : lit, nom de zone, panneaux, étiquettes de vente ; et, d'après la
     chasse, politiques, recherche, métiers des résidents) ;
   - consigne « ne pas s'éloigner » d'un compagnon (lit les réglages de l'host) ; karma des visiteurs sur une carte
     tenue par un invité ; mutation en double avec un équipement d'éther ;
   - échange : objets équipés, sacs pleins ; repos qui finit en sommeil (à revérifier) ; rechargement de l'invité au
     retour de l'host ; autres mods ;
   - serveur : relais sans coupure, personnage planté à la base, rôle du gardien du monde, mot de passe en clair ;
   - accidents rares : deux achats au même instant, deux constructions sur la même case, monture en double, plantage
     de celui qui tient une carte.
   Chacun de ces points demande une décision de conception : conseil, puis application.
5. Quand un ensemble est vert : passe large (`run_short.sh` sur les suites à deux fenêtres), fusion dans
   `feat/independent-travel`, puis proposer une nouvelle version à l'utilisateur (ne pas publier sans le lui dire).

## Questions qui restent pour l'utilisateur

- Sa soirée d'essai avec la 0.26.399, et l'essai de la carte au trésor à deux.
- Quel mod fournit les quêtes `dmp_quest_*`.
- Pousser les branches sur GitHub et publier une nouvelle version : quand il le voudra.

## Aide-mémoire

```
powershell -ExecutionPolicy Bypass -File dev\build.ps1
cd dev && set PYTHONPATH=_tools/pylib
python _tools/mp_test.py                       # host + 1 client ; échoue juste après run_short.sh : relancer
python _tools/council_suite.py                 # les décisions du conseil (C6 : --only c6, fenêtres neuves)
python _tools/guest_suite.py --only g31,g32    # ou g33,g34,g35 (lot 1 de la branche wip)
python _tools/equal2_suite.py                  # lot 2 de la branche wip
python _tools/together_suite.py                # lot 3 de la branche wip
bash _tools/run_short.sh <nom> death_suite guest_suite parity_suite sleep_suite recruit_suite
```

Pièges de la nuit : `new ActPray()` n'a pas d'identifiant (prendre `ACT.Create(6050)`) ; sur la carte du monde on
creuse sous ses pieds, `Teleport` n'y bouge pas un invité (`MoveImmediate` oui), y marcher peut déclencher une
rencontre ; quand l'host quitte une ville en premier, l'invité hérite de la carte ; un préfixe sur
`Chara.GetPietyValue` qui lit `IsPC` fige le chargement d'une sauvegarde (tester `core.IsGameStarted`) ; l'outil Bash
n'aime pas un texte long avec des apostrophes dans un « heredoc » : écrire le fichier avec l'outil d'écriture ;
`_lab` doit rester sur le même disque que le jeu (liens physiques). Les anciens pièges sont dans `MODLOG.md`.
