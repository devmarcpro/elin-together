# Plan : quêtes à donjon jouées à deux (host + un invité, dans les deux sens)

Rendu par un agent (lecture seule) le 2026-10-04 au soir. Remplace l'ordre de `PLAN_quetes_donjon_phase2.md` (qui
commençait par « un client rejoint un client », inutile à deux).

**État au 2026-10-05, 2h45 : E1 à E6 sont faites, dans les deux sens.** E1 à E4 (sens « l'host a la quête »),
commit `3eaedf8`, `together_suite.py` T1 à T6 (18/18). E5 et E6 (sens « l'invité a la quête »), commit `26756bf`,
T7 à T11 : **107/107** avec T1 à T6 (`_shots/together_b-run3.log`). Écrites par un agent (opus), relues par
`relecteur-elintogether`, corrigées, jouées. Limites : voir « Sens S2, ce qui est fait » plus bas.

## Principe

À deux, la zone d'une quête jouée ensemble est **toujours simulée par l'host** ; l'autre y est un client ordinaire.
On évite « l'host invité d'un client », et on réutilise l'arrivée normale sur la carte de l'host (`SendRejoin`).

## Faits du 2026-10-04 au soir (S1 est réglé depuis le 2026-10-05, `3eaedf8` ; S2 reste)

- S1, l'host prend la quête : il entre, l'invité **reste en ville** avec le bail de la ville (`LeavePlayersBehind`,
  `Net/Host/ElinNetHostTravel.cs:139-193`). Aucun geste pour suivre. `SendRejoin()` (`ElinNetClientTravel.cs:609`)
  saurait l'amener. S'il arrivait, son jeu casserait : la quête n'est pas dans son journal, `ZoneEventQuest.quest` est
  nul (lu par `OnVisit` de Subdue/DefenseGame/Music, l'affichage de la date de Harvest et Music, la sortie
  `ZoneInstanceRandomQuest.OnLeaveZone`). `ZoneEventHarvest.OnLeaveZone` confisque dans les sacs de tout le groupe.
  `SpatialGenDelta.cs:71-73` pose l'instance de l'host sur la case de la ville chez les clients, sans garde.
- S2, l'invité prend la quête : zone louée, il la simule. L'host n'a aucun geste ; forcé, il rappelle la zone, la
  zone est détruite et il entre dans une zone détruite. L'instance ne transporte ni carte ni événements.
  (Réglé le 2026-10-05 à 2h45 par E5 et E6, `26756bf`.)

## Étapes

| Étape | Quoi | Fichiers | Test (`together_suite.py`, host + 1 client) | État |
|---|---|---|---|---|
| E1 | gardes « visiteur » (`Patches/ZoneEvents/QuestZoneVisitorPatch.cs`, remplace `ZoneEventHarvestPatch.cs` : préfixes `IsHost` sur `OnVisit` de toutes les sous-classes de `ZoneEventQuest`, `ZoneEventQuest.OnTickRound`, `ZoneEventHarvest.OnLeaveZone`, `ZoneInstanceRandomQuest.OnLeaveZone` ; `TextWidgetDate` de Harvest et Music rend "" sans quête) + `ElinNetClient.FollowHost()` près de `SendRejoin` | nouveau patch, `ElinNetClientTravel.cs` | T1 : H prend, A suit par `FollowHost()`, mêmes monstres, pas d'exception | **faite** `3eaedf8`, T1–T6 |
| E2 | on sort ensemble : `LeavePlayersBehind` ne laisse personne dans une instance | `ElinNetHostTravel.cs` ~141 | T2 : une seule récompense, zone détruite | **faite** `3eaedf8`, T1–T6 |
| E3 | garde `!IsInstance` sur `elomap.SetZone` | `SpatialGenDelta.cs:71` | icône de ville inchangée chez A | **faite** `3eaedf8`, T1–T6 |
| E4 | le geste côté invité quand l'host entre dans une instance | `ElinNetClientTravel.cs` (`OnHostZoneChangedWhileAway`), `ElinNetClientZone.cs:55-63`, textes | T3 : vrai dialogue chez H | **faite** `3eaedf8`, T1–T6 |
| E5 | S2 : l'host sait lire et régler la quête d'un joueur (getter `ZoneEventQuest.quest` tiré de `PersonalQuestLogs`, `ZonePreEnterOnCompleteQuestInstance.Execute` → `CompletePersonal`, confiscation limitée) | nouveau patch, `ElinNetHostPersonalQuests.cs` | T7, T8, T11 | **faite** `26756bf`, T7–T11 |
| E6 | S2 : à la demande de bail d'une instance, l'host peut la prendre chez lui et emmener l'invité (`LeaseZoneBlueprint` clés 8, 9) | `ElinNetHostTravel.cs:233-282, 887`, `ElinNetClientTravel.cs:535` | T9, T10 | **faite** `26756bf`, T7–T11 |
| E7 | case host (si le conseil en veut une) | `EmpConfig.cs`, `NetSessionRules.cs`, `TabServerConfiguration.cs` | | pas de case (conseil) |

Les numéros T de la colonne « Test » pour E1 à E4 sont ceux du plan ; `together_suite.py` numérote T1 à T6 ce qui a
été fait pour E1 à E4 (la boîte Oui/Non, entrer, sortir, un seau posé en ville, la fouille de l'accompagnant), et T7
à T11 ce qui a été fait pour E5 et E6 (ci-dessous). La colonne « Test » de E5 et E6 donne les numéros réels.

## Sens S2, ce qui est fait (`26756bf`, T7 à T11)

- **T7** : l'invité prend une quête « subjuguer » et part. La demande de zone est retenue chez l'host, qui voit la boîte
  Oui/Non (15 s ; l'invité lit « on demande à X… »). Oui : l'host crée la zone et l'invité y est un client ordinaire,
  mêmes monstres, pas de doublon ; la quête reste au journal de l'invité, l'host la lit sans l'avoir au sien.
- **T8** : l'invité sort, tout le monde sort ; la récompense est donnée une fois, à l'invité ; la zone est détruite.
- **T9** : Non ou pas de réponse : comme avant, l'invité simule sa zone seul, ressort, la quête est ratée pour lui seul.
- **T10** : l'host peut rentrer seul : la zone passe à l'invité, qui finit seul et touche la récompense.
- **T11** : la sauvegarde de l'host ne contient rien de la quête de l'invité (ni événement ni numéro de quête).
- **Limites** : seulement les quêtes « subjuguer » (récolte, musique, défense restent en solo pour l'invité : les
  livraisons sont comptées par le jeu du preneur). Le test prend la quête, tue et sort par les appels du jeu, pas par
  le dialogue ni au combat (le banc sait pourtant dérouler un vrai dialogue depuis `hunt_suite.py`). Pas de test de
  déconnexion dans la zone. À trois joueurs : pas essayé. `instance_suite` et le bot attendront 15 s à chaque entrée
  (boîte sans réponse chez l'host).
- **Pièges** : une zone créée par l'host « sans annonce » n'est jamais connue du client (« Remote zone does not
  exist, waiting for new spatial gen », puis déconnexion « invalid zone ») : l'invité garde la zone qu'il s'était
  faite et adopte le numéro de celle de l'host. Un gel de la fenêtre host au chargement n'est pas dû à ce code (gel
  occasionnel déjà noté dans `mp_test.py`). Ne pas compiler pendant qu'un agent écrit dans le même dossier.

Pas vérifié par l'agent : si `OnVisit` tourne chez un client qui charge la carte de l'host ; Wedding et escorte.
Les décisions ouvertes (récompense, geste, sortie du preneur, case) sont tranchées par le conseil : voir `MODLOG.md`.
