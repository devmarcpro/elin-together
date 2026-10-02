# Plan : quêtes à donjon, phase 2 (les autres joueurs rejoignent le preneur)

Rendu par un agent (lecture du code seule) dans la nuit du 2026-10-02. **Rien n'est écrit.** Mod :
`ElinTogether\ElinTogether\`. Jeu : `_decomp\Elin\`.

## À savoir d'abord

- Aucune garde de la phase 1 n'interdit un invité. Ce qui bloque : personne ne connaît la zone, et le jeu de
  l'invité plante à l'entrée et à la sortie (les événements de la zone lisent `quest`, absent chez lui).
- L'host ne peut pas être invité (son `game` est le monde). Lot 2a = clients seulement, refus explicite pour
  l'host ; lot 2b = l'host, plus risqué, plus tard.
- `QuestEscort` n'est pas une quête à zone propre. Concernées : Subdue, Harvest, DefenseGame, Music, Wedding.
- Le bouchon de l'host n'avait pas d'`instance` (icône de ville effacée à la destruction) : **corrigé cette nuit**.

## Entrée d'un invité

La chaîne « carte partagée » marche telle quelle pour une instance (`TryTravel` → `RequestLease` →
`GrantGuestLease` → `SendGuestRequest` → `StartZoneSession` → `JoinZoneSession`). Ce qui manque : l'invité n'a
pas d'objet `Zone` à donner à `TryTravel`. Le plus simple : l'host diffuse la liste des zones de quête ouvertes ;
l'invité fabrique un bouchon détaché (`new Zone { id, uid, instance = new ZoneInstance() }`) et appelle
`TryTravel(bouchon, Center)`.

Interface : section « Quêtes en cours » dans `Components\Tabs\TabSessionInfo.cs` (bouton « Rejoindre <joueur> »),
et/ou clic sur le donneur de quête (postfix `ActPlan._Update`, modèle `Patches\PlayerTradePatch.cs`).

## Gardes à ajouter chez l'host

- `GetLeaseDenyReason` : refuser un bail ordinaire (sans blueprint) sur une zone de `_questZones` sans détenteur.
- `CanEnterNow` : refuser l'host (2a), sinon le rappel détruit la zone puis l'host y entre.

## Événements de zone chez l'invité (préfixes « seulement chez celui qui simule »)

| Cas | À faire |
|---|---|
| `OnVisit` de toutes les sous-classes de `ZoneEventQuest` (lit `quest`, fait réapparaître les monstres) | préfixe `IsHost` |
| `ZoneEventQuest.OnTickRound` (aggro, apparitions, limite de temps) | préfixe `IsHost` |
| `ZoneEventHarvest.TextWidgetDate`, Music (affichage) | `quest == null` → `""` |
| Cor de défense `TraitCoreDefense.TrySetAct` | préfixe `IsHost` |
| `ZoneEventHarvest.OnLeaveZone`, `ZoneInstanceRandomQuest.OnLeaveZone` quand l'invité sort | rien si la quête n'est pas dans son journal |
| Invité avec sa propre `QuestHarvest` | refuser l'entrée en `instance_harvest` |
| Le preneur sort ou se déconnecte, invité dedans | `ZoneLeaseRecall.Closed` → l'invité retourne à la zone de retour (bail ou `SendRejoin`) |

## Changements, dans l'ordre (lot 2a)

1. `LeaseZoneBlueprint` : `ReturnZoneUid`, `GiverUid`, `QuestUid`, `ReturnX`, `ReturnZ` (clés 8 à 12).
   `_questZones` devient un dictionnaire d'entrées (zone, retour, donneur, preneur, quête). Balayage des orphelins.
2. Case d'option `QuestZoneGuests` (`EmpConfig`, `NetSessionRules` clé 8, `TabServerConfiguration`).
3. `Patches\ZoneEvents\QuestZoneVisitorPatch.cs` : les préfixes du tableau.
4. `QuestZonesDelta` (union 815, `RequiresGameStarted => false`), envoyé à la création, à la destruction et à
   l'arrivée d'un joueur ; `PersonalQuests.OpenZones` côté client ; liste blanche du voyage.
5. Gardes de l'host (ci-dessus).
6. `ElinNetClient.JoinQuestZone(int zoneUid)`.
7. Sortie : `ZoneLeaseRecall.Closed` + branche dans `OnZoneLeaseRecall` ; mise en attente de la demande d'invité
   si le preneur est encore en chargement.
8. Interface + clés de langue.

## Test `_tools\join_suite.py` (H, A preneur, B invité ; `mp_test.py --clients 2`)

J1 entrée (mêmes monstres chez A et B, pas de doublon, quête absente du journal de B) ; J2 l'invité tue le
dernier monstre → réussite chez A ; J3 l'invité sort seul ; J4 le preneur sort, invité dedans → tous à la base,
une seule récompense, pour A ; J5 zone de retour différente de celle de l'host ; J6 preneur coupé.

## Risques

Monstres en double (`OnVisit` rejoué), quête réglée deux fois, zone orpheline chez l'host, course à la zone de
retour, confiscation de la récolte dans les sacs des invités, affichage figé chez l'invité (vague, poids).
