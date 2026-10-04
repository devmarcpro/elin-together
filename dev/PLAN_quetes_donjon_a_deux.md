# Plan : quêtes à donjon jouées à deux (host + un invité, dans les deux sens)

Rendu par un agent (lecture seule) le 2026-10-04 au soir. Remplace l'ordre de `PLAN_quetes_donjon_phase2.md` (qui
commençait par « un client rejoint un client », inutile à deux). **Rien n'est écrit.**

## Principe

À deux, la zone d'une quête jouée ensemble est **toujours simulée par l'host** ; l'autre y est un client ordinaire.
On évite « l'host invité d'un client », et on réutilise l'arrivée normale sur la carte de l'host (`SendRejoin`).

## Faits d'aujourd'hui

- S1, l'host prend la quête : il entre, l'invité **reste en ville** avec le bail de la ville (`LeavePlayersBehind`,
  `Net/Host/ElinNetHostTravel.cs:139-193`). Aucun geste pour suivre. `SendRejoin()` (`ElinNetClientTravel.cs:609`)
  saurait l'amener. S'il arrivait, son jeu casserait : la quête n'est pas dans son journal, `ZoneEventQuest.quest` est
  nul (lu par `OnVisit` de Subdue/DefenseGame/Music, l'affichage de la date de Harvest et Music, la sortie
  `ZoneInstanceRandomQuest.OnLeaveZone`). `ZoneEventHarvest.OnLeaveZone` confisque dans les sacs de tout le groupe.
  `SpatialGenDelta.cs:71-73` pose l'instance de l'host sur la case de la ville chez les clients, sans garde.
- S2, l'invité prend la quête : zone louée, il la simule. L'host n'a aucun geste ; forcé, il rappelle la zone, la
  zone est détruite et il entre dans une zone détruite. L'instance ne transporte ni carte ni événements.

## Étapes

| Étape | Quoi | Fichiers | Test (`together_suite.py`, host + 1 client) |
|---|---|---|---|
| E1 | gardes « visiteur » (`Patches/ZoneEvents/QuestZoneVisitorPatch.cs`, remplace `ZoneEventHarvestPatch.cs` : préfixes `IsHost` sur `OnVisit` de toutes les sous-classes de `ZoneEventQuest`, `ZoneEventQuest.OnTickRound`, `ZoneEventHarvest.OnLeaveZone`, `ZoneInstanceRandomQuest.OnLeaveZone` ; `TextWidgetDate` de Harvest et Music rend "" sans quête) + `ElinNetClient.FollowHost()` près de `SendRejoin` | nouveau patch, `ElinNetClientTravel.cs` | T1 : H prend, A suit par `FollowHost()`, mêmes monstres, pas d'exception |
| E2 | on sort ensemble : `LeavePlayersBehind` ne laisse personne dans une instance | `ElinNetHostTravel.cs` ~141 | T2 : une seule récompense, zone détruite |
| E3 | garde `!IsInstance` sur `elomap.SetZone` | `SpatialGenDelta.cs:71` | icône de ville inchangée chez A |
| E4 | le geste côté invité quand l'host entre dans une instance | `ElinNetClientTravel.cs` (`OnHostZoneChangedWhileAway`), `ElinNetClientZone.cs:55-63`, textes | T3 : vrai dialogue chez H |
| E5 | S2 : l'host sait lire et régler la quête d'un joueur (getter `ZoneEventQuest.quest` tiré de `PersonalQuestLogs`, `ZonePreEnterOnCompleteQuestInstance.Execute` → `CompletePersonal`, confiscation limitée) | nouveau patch, `ElinNetHostPersonalQuests.cs` | T4 |
| E6 | S2 : à la demande de bail d'une instance, l'host peut la prendre chez lui et emmener l'invité (`LeaseZoneBlueprint` clés 8, 9) | `ElinNetHostTravel.cs:233-282, 887`, `ElinNetClientTravel.cs:535` | T5 |
| E7 | case host (si le conseil en veut une) | `EmpConfig.cs`, `NetSessionRules.cs`, `TabServerConfiguration.cs` | |

Pas vérifié par l'agent : si `OnVisit` tourne chez un client qui charge la carte de l'host ; Wedding et escorte.
Les décisions ouvertes (récompense, geste, sortie du preneur, case) sont tranchées par le conseil : voir `MODLOG.md`.
