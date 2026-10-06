# Retours de la soirée du 6 octobre 2026 (vraie partie, trois joueurs ou plus, version 0.26.506)

L'utilisateur jouait invité, un ami était host, d'autres amis invités. Chaque ligne : ce qu'il a dit, la cause trouvée,
l'état. « Écrit » = dans l'arbre, compilé (0 erreur) ; « rouge vu » = le test échoue sur la 0.26.506 ; « vert » = il passe
sur la nouvelle version. Rien n'est « fait » avant d'être vert ET commité. À tenir à jour.

| # | Ses mots | Cause (fichier de l'enquête) | État |
|---|---|---|---|
| 1 | « beaucoup de bugs avec le sommeil (des tp impromptus) » | Les familiers de tous les joueurs sautent sur le lit de l'host ; un invité qui dort seul voit sa carte rechargée ; monstres de rêve (`PLAN_sommeil_teleportations.md`) | Écrit (`SleepSynchronizationContext.cs`), relu ; rouge vu (`sleep_suite` P2, Y2) ; vert à lire |
| 2 | Capture : fenêtre d'erreur `GameIO.CanLoad` / `Game.TryLoad` | Le chargement rapide passait chez un invité, qui n'a pas de sauvegarde | Écrit (`GameSaveLoad.cs`, texte `emp_ui_load_blocked`), relu ; pas de test : à écrire |
| 3 | « mon ami hôte joue de la musique et mon personnage invité lui jette des orens » | Le personnage d'un autre joueur compte dans le public (`Point.ListWitnesses`) | Écrit (`AIPlayMusicPatch.cs`) ; rouge vu (`witness_suite`) ; vert à lire. À vérifier : même liste pour les témoins d'un crime |
| 4 | « mon ami hôte a fait auto dump, il a joué du luth et ses items ont été sortis de sa hotbar » | Le rangement du jeu prend aussi la ceinture à outils (rangée du haut) ; ou réglage `autodump` d'un coffre partagé depuis le 5 octobre (`PLAN_autodump_hotbar.md`). Objets dans les coffres, pas perdus (lu) | PAS ÉCRIT : deux choix de conception (ne plus ranger la ceinture ; `autodump` par joueur) : conseil |
| 5 | « un ami invité a été tp dans l'eau sur la carte monde » | Posé « à côté de l'host », case voisine pouvant être la mer (`PLAN_invites_tp_sur_host.md` C3, `PLAN_ancien_personnage_et_eau.md` B) | Écrit avec le point 7 ; rouge vu (`place_suite` P3, P4) ; vert à lire |
| 6 | « j'ai changé de personnage, j'ai vu mon ancien personnage en jeu qui se battait » | Un personnage de joueur que personne ne joue reste membre de la base et peut être remis sur une carte (`PLAN_ancien_personnage_et_eau.md` A, trois trous, pas prouvé) | Écrit, PAS COMPILÉ ni joué (`ElinNetHostPlayerManager.cs` : `RemoveRemoteChara`, `RemoveUnplayedCharas`, garde de `OnSessionNewPlayerResponse` ; `ZoneActivateEvent.cs`) ; hors carte = hors des habitants de la base aussi ; test `chara_suite` C5 écrit, jamais lancé |
| 7 | « les personnages invités ne font que se faire tp sur l'host » | Tout invité qui recharge une carte est posé à côté de l'host ; à trois, à chaque départ et retour de l'host (`PLAN_invites_tp_sur_host.md` C1) | Écrit (`ElinNetHostTravel.cs`, `ElinNetHostZone.cs`, `ElinNetClientTravel.cs`, `Models/ZoneLease/ZoneArrival.cs`), relu ; le cas à trois : `trio_place_suite.py`, trois fenêtres (accord donné) |
| 8 | « le temps des invités jump up de ouf… un invité meurt de faim et sa nourriture pourrie, il faudrait que les joueurs gardent leurs propres horloges internes » | Une seule date, celle du plus avancé ; un pas de carte du monde = 3 heures vécues par tous (`PLAN_horloge_par_joueur.md`) | Urgence écrite (`WorldDateAdvanceEvent.cs`, `WorldDateAdvanceDelta.cs`, `RemoteDecayPatch.cs`, `PersonalQuests.cs`), relecture en cours ; rouge vu (`time_suite` W6 : vie 22 -> -2) ; vert à lire. Reste pour le conseil : date par joueur ou non, pas sur la carte du monde avec l'host, objets posés |
| 9 | « invité rentre dans cave, descend, hôte rejoint le niveau -1 et la map est régénérée pour l'hôte, différente » | Les caves « jetables » sont refabriquées à l'entrée après un jour, le jeu supposant un seul joueur (`PLAN_donjon_regenere.md`, pas prouvé ; dépend de la cave) | Écrit, PAS COMPILÉ ni joué (`ElinNetHostTravel.cs` : `KeepAlive`, `IsHeld`, `HasPlayerIn` ; `ZoneActivateEvent.cs` ; `LeasedZonePatch.cs` pour tout le donjon) ; les deux sens et entre invités par la date envoyée avec le bail ; test `travel_suite` s18 écrit, jamais lancé (pas de Nefia dans le monde de test). Question posée : quelle cave ? |
| 10 | « vérifie si les invités apprennent des sorts et des recettes comme l'hôte quand ils dorment » | Sort en rêve : oui. Recette : celle de l'host seulement (un tirage pour tous). Manquent à l'invité : lecture de son grimoire, son oreiller, ses dons de karma (`ConSleep.cs:262-345`, `CharaSleepDelta.cs`) | PAS ÉCRIT : chaque joueur joue son propre réveil ; test : grimoire + oreiller chez l'invité |
| 11 | « la base a reçu 2 bills à payer, une de 500 et une de 35 en quelques jours… il devrait y avoir qu'un bill » | À trouver (`PLAN_factures.md`, enquête lancée) : une facture par joueur, ou par jeu qui passe la fin du mois ? | PAS ÉCRIT : enquête, puis conseil si c'est un choix (une pour le monde, ou une par joueur) |
| 12 | « plus on est de joueurs invités plus le jeu galère et plus il y a de bugs » | Audit `PLAN_plusieurs_invites.md` : gels à chaque retour d'un invité (monde + sauvegarde + carte entière), copie de carte toutes les 60 s par carte tenue ; cinq défauts à trois (nuit bloquée par un joueur, deux invités invisibles l'un à l'autre sur la carte du monde…) | PAS ÉCRIT ; mesure de la lenteur à ajouter au banc |
| 13 | « un joueur invité vient de déposer 1500 orens dans la banque, il a fermé et rouvert la banque et les orens avaient disparu » | À trouver (`PLAN_banque_invite.md`, agent lancé) : la banque est un conteneur global hors carte, le dépôt d'un invité n'arrive sans doute pas chez l'host. PERTE D'OR | Enquête + correction d'urgence en cours (dépôt par demande à l'host, ou refus propre) ; test `bank_suite.py` |
| 14 | « redirection : si quelqu'un héberge déjà le monde du dépôt, le deuxième est envoyé automatiquement dans sa partie » | Le verrou existait, pas la redirection | Écrit (`SaveDepot.cs`, `GitHubDepot.cs`, champ `join`, bouton « Join X »), relu ; hors jeu 73/73 ; en jeu : `depot_suite` D5b, D7 à lire. Limite : amis Steam seulement (`SteamNetLobbyManager.cs:383`) |

## Demandes de fond de la même journée

- « le jeu devrait savoir quel personnage est à qui… le joueur n'a pas à réfléchir » : fait, dans la 0.26.506.
- « si l'hôte se déconnecte est-ce qu'un des joueurs invités devient l'hôte ? » : conseil 9 (`PLAN_conseil9_verdict.md`). Étape 1
  (retour automatique, plus d'écran de choix) commitée `c34732d`, pas publiée ; étape 2 (sauvegarde régulière, partie qui
  s'ouvre seule dans un monde déjà partagé) écrite, relue, compilée, `autosave_suite` à lire ; étapes 3 à 5 pas commencées.
- Trois fenêtres du jeu sur ce PC pour les cas à trois joueurs : accord donné (« Oui »).

## Trouvé en chemin, à ne pas perdre

- Un joueur seul dans une session change de règles (pas de pause dans les menus `PauseGame.cs:43`, tours de combat
  `ActionModeCombat.cs`, limite d'alliés `CompanionAllyLimitPatch.cs:19`, sommeil) : relecture dédiée à faire.
- Sur la carte du monde avec l'host, le pas d'un invité ne coûte ni temps ni faim (`RemoteTravelRegionPatch.cs:29`).
- Après un duel, les PV du perdant ne sont pas toujours au maximum dans son jeu. La laisse G36. L'exception de T8.
- `hunt2_suite` E3 va rougir avec la correction du temps (elle attend la viande de l'invité vieillie par le saut de l'host).
- Lignes 38 à 52 de `PLAN_chasse_differences_3.md` (double paiement, artefact de dieu détruit…).
- Questions ouvertes pour l'utilisateur : retirer les 0.26.493 et 0.26.494 de GitHub ? ; quelle cave (point 9) ; dans quelle
  rangée de la barre étaient les objets (point 4) ; un invité avait-il réglé un coffre (point 4).

## Retour ajouté après la table (6 octobre, 19h)

| 15 | « un donjon est considéré comme conquis alors que le boss n'est pas vaincu » | À trouver. Pistes : le boss existe dans un seul jeu (celui qui tient l'étage) et l'autre jeu ne le trouve pas, donc croit l'étage vidé ; ou la cave gardée en vie (point 9) passe pour finie | PAS ÉCRIT : enquête après la 0.26.509. À demander : quel donjon, qui était à l'étage du boss (host ou invité), qui a vu « conquis » |
