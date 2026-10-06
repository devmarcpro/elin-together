# Somme de contrôle de la carte et remise à niveau toute seule (2026-10-06)

Outil du §4 de `PLAN_desync.md`. Écrit, compilé (ReleaseNightly, 0 erreur), **jamais lancé** : `dev/_tools/resync_suite.py`
est à jouer (deux fenêtres, ~3 minutes).

## Ce que ça fait
- Le jeu qui tient la carte (l'host, ou l'invité qui tient une carte en session de zone) calcule quelques nombres et les
  joint à `SessionPlayersSnapshot` (toutes les 2 s, `ElinNetHostUpdate.cs:265`, et à chaque départ d'un joueur).
- Chaque autre jeu sur la même carte calcule les mêmes nombres à la réception (`SessionPlayersSnapshot.Apply`) et compare.
- Écart retenu seulement s'il est **immobile** : mêmes nombres des deux côtés pendant 3 comparaisons de suite (4 à 6 s).
  Tout ce qui est en route (pas, ramassage, message en vol) fait bouger un des deux côtés et remet le compteur à 1.
- Alors : une ligne Warning chez l'invité (`Map checksum differs on {ZoneFullName} (here/host): {Detail}`), la même
  envoyée à l'host (`DesyncReportDelta`, numéro 842 : `Player {PeerIndex} reports a map checksum that differs on …`).
- Règle `AutoResync` (case host, cochée) : l'invité redemande la carte (`RequestZoneState(CurrentRemoteZone)`, le chemin
  « Reloading active zone from received snapshot »), avec la ligne à l'écran `emp_ui_resync`.
- `emp.desync` (console) : nombres locaux, coût du calcul, derniers nombres comparés, compteurs, dernier avertissement.

## Ce que les nombres comptent
| Nombre | Compte | Laisse de côté |
|---|---|---|
| personnages | combien, et un mélange de leurs numéros | les morts, les numéros en attente, **la case** |
| objets au sol | combien, et un mélange numéro + case + quantité | détruits, numéros en attente, jetons de capacité |
| sac de chaque joueur présent | mélange numéro + quantité + « équipé ou non », sacs dans le sac compris | idem |

Pas comptés du tout : le contenu des coffres, le terrain, la carte du monde (copie locale de chacun), l'état des
personnages (vie, états), les sacs des compagnons et des habitants.

**La case des personnages n'y est pas, exprès** : l'instantané tolère 2 cases d'écart sans corriger
(`CharaStateSnapshot.cs:160`). Un habitant décalé d'une case serait un écart immobile et légitime : rechargement pour rien.
Les positions sont déjà réparées 5 fois par seconde au-delà de 2 cases.

## Bornes (le danger est le faux positif)
- 3 comparaisons immobiles de suite ; deux listes à moins de 1,5 s comptent pour une ; 6 s de silence après un
  chargement de carte (12 s après une remise à niveau).
- Rechargement : au plus un par 30 s, puis 60, 120, 240, 480 s sur la même carte ; arrêt après 3 rechargements sans
  qu'une seule comparaison soit égale entre-temps, ou 5 sur la même carte (ligne
  `Map checksum still differs on … no more reload of this map`).
- Jamais pendant : une tâche du joueur, un ennemi visé, un ennemi à 8 cases ou moins, une fenêtre ou un menu ouvert,
  un glisser d'objet, la mort, un voyage demandé ou accordé, une carte en cours de chargement.
- Sans D4 corrigé, ce qui arrive à la carte pendant le rechargement est perdu chez ce joueur : l'écart reparaît, un
  deuxième rechargement 30 s plus tard le reprend. C'est la raison des bornes ci-dessus.

## Les sacs : avertis, pas réparés
Rien de léger ne renvoie le sac d'un joueur. `CardGenDelta` ne remplace pas une carte déjà connue
(`CardGenDelta.cs:32-36`) ; `emp.reconnect_self` recharge le monde entier, coupe le lien, et ne marche que par un salon
Steam. Il faudrait un message neuf « voici ce personnage en entier » que l'invité applique en remplaçant le contenu du
sac (et la mémoire des cartes), demandé par l'invité en écart : ~40 lignes, à faire avec D5 (même besoin).

## À ajouter ailleurs (fichiers que cet outil ne touche pas)
1. `ElinTogether/Net/Host/ElinNetHostZone.cs:121` : sans cela le joueur remis à niveau saute d'une case (la case qu'il
   occupe est refusée parce qu'il y est). Remplacer
   `pos = _zone.IsRegion ? at.Copy() : at.GetNearestPoint(allowChara: false) ?? at.Copy();` par
   `pos = _zone.IsRegion || (chara.pos.x == at.x && chara.pos.z == at.z) ? at.Copy() : at.GetNearestPoint(allowChara: false) ?? at.Copy();`
2. Textes (`package/LangMod`) : `emp_ui_resync`, `emp_ui_sv_cfg_auto_resync`, `emp_ui_sv_desc_auto_resync`.
3. En session de zone, la ligne arrive dans le journal de l'invité qui tient la carte, pas dans celui de l'host : il
   faudrait la faire suivre (`SendWhileAway`) et l'ajouter à la liste de `ElinNetHostUpdate.cs:116`.

## Après relecture (2026-10-06, nuit)

Compilé (`ReleaseNightly`, 0 erreur), **jamais lancé**.

- **La case des objets au sol n'est plus dans les nombres** (`NetDesync.cs`, `Collect`) : numéro + quantité seulement,
  comme pour les personnages. Raison : un objet lancé, une flèche, un butin éparpillé tombent selon les dés de chaque
  jeu ; une case d'écart aurait fait un écart immobile, donc des rechargements pour rien. Ceci remplace la ligne
  « objets au sol » du tableau plus haut. Un objet qui n'est pas à la même case chez deux joueurs n'est donc **plus
  vu** ; il est remis à sa case par tout rechargement de la carte. Le texte de l'avertissement dit maintenant
  `(not the same ones or amounts)`.
- Les nombres du passage de main (`ZoneLeaseState.Sums`, D2) comptent toujours la case : non touché.
- `DesyncReportDelta` : le nom de la carte et le détail envoyés par l'invité sont coupés à 200 caractères avant
  d'entrer dans le journal de l'host.
- `resync_suite.py` R2 : le seau déplacé de 2 cases reste dans le test, mais l'écart n'est plus vu que par le seau
  retiré et le poulet ; le test vérifie toujours que le rechargement remet le seau déplacé à sa case.
- Le calcul a changé : host et invité doivent avoir la même version du mod (la connexion vérifie déjà la version du
  mod, `ElinNetHostIntegrity.cs`, non relu en détail), sinon l'écart serait permanent sur toute carte avec des objets
  au sol, jusqu'à l'arrêt des rechargements (3 sans effet).

## Coût
Un passage sur `_map.charas` et `_map.things`, 4 multiplications par carte, plus le sac des joueurs présents ; une fois
toutes les 2 s chez l'host et chez chaque invité. Estimé sous 0,2 ms pour 5 000 objets ; **non mesuré** : `emp.desync`
donne le temps réel sur la carte courante. Le message grossit de ~30 octets + 10 par joueur.
Une remise à niveau coûte à l'host une copie de la carte (comme une arrivée de joueur).

## Pas sûr
- Jamais lancé. Le premier doute est le faux positif sur une vraie carte habitée (base, ville) : jouer R1 de la suite,
  puis une soirée case **décochée** et lire les lignes avant de laisser cochée par défaut dans une version publiée.
- `pc.HasNoGoal` chez un invité au repos : supposé vrai (sinon aucune remise à niveau ne part, sans danger).
- Session de zone (invité chez un invité) : même code, pas dans la suite.
- Le rechargement de la carte active d'un invité installé est un chemin peu emprunté (`ElinNetClientZone.cs:184-188`).
