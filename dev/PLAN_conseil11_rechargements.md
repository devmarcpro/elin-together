# Conseil 11 (2026-10-07) : ne plus recharger le monde entier quand un invité retrouve l'host

Question et faits : voir la carte des chemins plus bas. Cinq avis (sonnet), trois relectures croisées (au lieu de cinq :
elles convergeaient), synthèse par la session. Mesure de départ : journal réel, 9 copies du monde en 13 minutes de donjon.

## Verdict

- **D'accord (5/5)** : la copie du monde reste le **filet**, silencieux, jamais une question au joueur ; pas de liste
  de rattrapage choisie à la main comme seule garantie ; le nouveau retour sort **case décochée** à sa première
  version (exception à « coché par défaut » : jamais joué, touche aux objets), cochée dès que le banc passe.
- **Ordre retenu** (réponse la mieux notée par les trois relectures) : 0. mesurer sans rien changer ; 6. alléger la
  copie (un monde + UNE carte au lieu de monde + ancienne carte + nouvelle carte) ; 1. retour sur place quand l'host
  arrive sur la carte d'un invité ; 2. retour par la seule carte pour les changements d'étage. Pas de 4 ni de 5
  maintenant. Désaccord : 2 avant 1 (les escaliers sont le cas le plus fréquent) contre 1 avant 2 (1 réutilise le
  schéma éprouvé du départ de l'host). Tranché : 1 d'abord, parce que c'est lui qui pose le passage « seul -> client »
  sur place dont 2 a besoin aussi.
- **Ce qui doit être vrai avant un retour sans copie**, par risque : (1) le compteur d'uid et les nouveaux numéros des
  cartes « en attente » du personnage renumérotées par l'host (seul point qui peut dupliquer un objet) ; (2) les
  boîtes du monde (expédition, livraison, banque) renvoyées à l'invité ; (3) les personnages de l'host et des autres
  joueurs. Maison, faction, relations : peuvent attendre.
- **Monde périmé** : pas de hachage du monde à chaque retour (c'est une sérialisation, le coût qu'on veut éviter) ni
  simple compteur de messages jetés (un changement puis son contraire). Des **drapeaux « sali » posés côté host aux
  endroits qui changent** boîtes / personnages globaux / zones / maison, remis à zéro par invité à chaque copie. Un
  drapeau levé hors des catégories rattrapées = copie du monde.
- **Angles morts relevés** : l'option 6 n'est pas « sans risque » (ne PAS sauter la sauvegarde de l'host sans savoir
  ce qu'elle garantit ; seulement l'ordre des cartes) ; ce que l'invité a changé lui-même pendant son absence (uid de
  sa plage) ; les messages qui arrivent pendant la bascule ; le verrou ramasser/poser pendant le passage de main ; host
  et invités doivent avoir la même version (déjà la règle) ; l'invité mort et les deux cartes, à rejouer sur le
  nouveau chemin.

## Découpage

| Tranche | Contenu | État |
|---|---|---|
| 0 | Ligne de journal à chaque retour : durée d'absence, taille de la copie, messages de l'host non pris par sorte (`ElinNetClientTravel.ReportReturn`) | **écrit, compilé** ; aucun changement de comportement |
| 6 | Au rappel : l'host ne diffuse plus son ancienne carte avec le monde, seulement celle où il arrive | à écrire ; à jouer avant de publier |
| 1 | Retour sur place (cas a) : message « client de nouveau » avec les sommes de la carte chargée par l'host, uid, boîtes, personnages globaux ; comparaison comme `AdoptHostCopy` ; filet = copie | à écrire derrière une case décochée ; **banc obligatoire** avant de cocher |
| 2 | Retour par la carte seule (cas b, c), `AdoptHostUid` sur le refus `emp_travel_host_zone` | après 1 |

## À mesurer au banc (5 étages, puis 20 passages de main, 2 puis 5 fenêtres)

Copies du monde par étage (cible 0), durée du gel, tâche et fenêtres gardées, totaux d'objets / or / expérience avant
et après avec un ramassage pendant le passage, doublons d'uid des deux côtés, sommes de carte égales 10 s après, un
écart forcé qui retombe sur la copie, une sauvegarde puis rechargement après le retour, taux de retombée sur la copie.

## Carte des chemins (résumé de la recherche)

- La copie = `SaveDataProbe` (tout `Game` en JSON + LZ4), envoyée seulement par `SendSaveProbe`
  (`ElinNetHostPlayerManager.cs` 238-281) ; au retour, depuis `OnZoneLeaseRelease` (`ElinNetHostTravel.cs` 1173).
- (a) `ZoneLeaseRecall` -> l'invité rend carte + personnage + compagnons + compteur (`CreateLeaseRelease`) -> l'host
  applique (`ApplyLeasedZone`, `ReplaceRemoteChara`) -> copie du monde -> l'host bouge -> deuxième carte diffusée.
- (b) `TryTravel` vers la carte de l'host -> `SendRejoin` -> même suite. (c) se ramène à (a) ou (b).
- Absent, l'invité ne prend que quêtes, drapeaux, date, météo, sommeil, discussion, factures ; tout le reste est jeté.
- Sans copie existe déjà : le départ de l'host (`TakeOverZone` / `AdoptHostCopy`, sommes `ZoneLeaseState.Sums`), et le
  rechargement de la seule carte (`OnZoneActivateResponse`, branche `player.zone != null`).
- Plan B « rappel doux » de `PLAN_retours_partie_reelle.md` 34-57 : écarté « jusqu'à la mesure » ; la mesure est faite.
