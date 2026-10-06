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
- Les nombres du passage de main (`ZoneLeaseState.Sums`, D2) comptaient la case ici : **ce n'est plus vrai**, voir
  « Après relecture (seconde passe) » en bas.
- `DesyncReportDelta` : le nom de la carte et le détail envoyés par l'invité sont coupés à 200 caractères avant
  d'entrer dans le journal de l'host.
- `resync_suite.py` R2 : le seau déplacé de 2 cases reste dans le test, mais l'écart n'est plus vu que par le seau
  retiré et le poulet ; le test vérifie toujours que le rechargement remet le seau déplacé à sa case.
- Le calcul a changé : host et invité doivent avoir la même version du mod (la connexion vérifie déjà la version du
  mod, `ElinNetHostIntegrity.cs`, non relu en détail), sinon l'écart serait permanent sur toute carte avec des objets
  au sol, jusqu'à l'arrêt des rechargements (3 sans effet).

## Sacs : un personnage renvoyé en entier (2026-10-06, nuit, seconde passe)

Écrit, compilé (`ReleaseNightly`, 0 erreur), **jamais lancé**. Remplace la section « Les sacs : avertis, pas réparés ».
Test : `resync_suite.py` R4 et R5.

- **Où vit la vérité d'un sac (lu).** Chez le jeu qui tient la carte où le personnage se trouve.
  - Sur la carte de l'host : chez l'host. Le personnage d'un invité est un personnage du monde de l'host
    (`SavedRemoteCharas`, enregistré dans sa sauvegarde) ; à la connexion l'invité reçoit le monde entier de l'host et
    joue le personnage qui s'y trouve (`SendSaveProbe`, `OnSaveDataProbe`). Rien ne remonte le sac de l'invité vers
    l'host tant qu'il est sur sa carte : s'il se déconnecte, c'est la copie de l'host qui reste.
  - Invité chez un autre invité : chez celui qui tient la carte (`CollectGuestCharas`, envoyé à l'host avec ses points
    de passage).
  - Invité parti seul : chez lui. Il part avec **son** sac tel qu'il est à l'écran (`TravelTo`), et son premier point
    de passage remplace la copie de l'host (`ReplaceRemoteChara`). **Un écart de sac devient donc vrai sans bruit le
    jour où ce joueur voyage seul** : l'objet en trop devient réel, l'objet en moins est perdu.
- **Le message** : `CharaBagDelta`, numéro 841 (`Models/Delta/Chara/CharaBagDelta.cs`). Sans contenu : la demande, du
  jeu qui constate l'écart vers celui qui tient la carte. Avec contenu : la réponse, **envoyée à tous dans le fil des
  messages ordinaires** et remplie au moment où la liste part : tout ce qui a été envoyé avant y est, rien de ce qui
  suit n'y est. Contenu : tout ce que porte le personnage (sac, équipement, sacs dans le sac), le mélange du
  détecteur, le numéro de l'objet tenu en main.
- **La demande** (`NetDesync.AskBags`) : écart de sac immobile (3 comparaisons), règle `AutoResync`, mêmes garde-fous
  que le rechargement de carte (pas de tâche, pas d'ennemi visé ni à 8 cases, pas de fenêtre, pas de glisser, pas de
  voyage en cours), pas dans la passe où la carte est redemandée ; au plus une fois par 30 s et par personnage, puis
  60, 120, 240, 480 s tant que ce sac ne redevient pas égal. L'host répond au plus une fois par 5 s et par personnage.
- **L'application** (`CharaBagDelta.Repair`) : carte par carte, sans remplacer les objets que les deux jeux
  connaissent (fenêtres, barre d'outils et tâches pointent dessus) : seuls changent la place, la quantité,
  l'emplacement d'équipement. Un objet connu ailleurs dans ce jeu (au sol, dans un autre sac) est déplacé, pas copié.
  Un objet que l'host n'a pas dans ce sac en sort (gardé en mémoire, comme `CardRemoveThingDelta`). Les objets « en
  attente de numéro » et les cartes d'aptitude ne sont jamais touchés.
- **Sac d'un AUTRE joueur** (la copie que j'en ai) : réparé dès que le mien diffère de la réponse, même si un autre
  joueur l'a demandée. Cette copie n'est enregistrée par personne.
- **MON PROPRE sac** : derrière une **sous-option éteinte**, `NetDesync.RepairOwnBag` (champ statique ; pas de case :
  `EmpConfig` et `NetSessionRules` ne sont pas dans les fichiers de ce lot). Éteinte : ni demande ni remplacement,
  l'avertissement reste. Allumée : seulement la réponse à ma propre demande, moins de 10 s après, et seulement si mon
  sac **et** celui de l'host ont encore exactement les nombres des 3 comparaisons.

### Ce qui peut être perdu ou doublé
| Sens | Perdu | Doublé |
|---|---|---|
| Sac d'un autre, copie locale <- host | rien de réel | rien de réel |
| Mon sac <- host (sous-option) | un objet que j'ai et que l'host n'a pas **dans mon sac** : il sort de mon jeu. Si l'host l'a au sol, il y revient au prochain rechargement de carte (à ramasser de nouveau) ; si l'host ne l'a nulle part, c'était un fantôme (perdu de toute façon à la reconnexion). Vraie perte : seulement si ce que j'avais fait était juste et n'a jamais atteint l'host (message perdu) | rien : dans le monde de l'host un objet n'est qu'à un endroit, et un objet rendu à mon sac que mon jeu voyait ailleurs (au sol) est déplacé, pas copié |
| Mon sac -> host (pas écrit) | ce que l'host m'a donné et que je n'ai pas reçu (butin, récompense) | ce que j'ai « ramassé » chez moi et qu'un autre joueur a vraiment pris : deux exemplaires |
| Ne rien faire (aujourd'hui) | l'objet en moins, pour de bon, si je pars voyager seul | l'objet en trop, pour de bon, si je pars voyager seul et que l'host l'a encore au sol |

Le sens « mon sac -> host » n'est pas sûr : l'host simule, c'est lui qui décide qui a ramassé quoi. Le sens « host ->
mon sac » ramène toujours vers un monde cohérent (celui de l'host, où un objet n'est qu'à un endroit).
**Message en route** : un geste fait après la demande change mes nombres, la réponse est alors refusée
(`it moved since we asked`). Un geste que l'host applique entre-temps change les siens : refusée aussi. Reste le geste
que je fais dans la même image que la réponse : il part après, l'host le rejoue sur son sac, son écho me revient.
Rien n'est joué : c'est pourquoi la sous-option est éteinte.

### Journal
- Invité, Information : `Asking for the bag of {Uid} again, ours {Own}, attempt {Asks} (here {Local:X8} | host {Host:X8})`
- Host, Information : `Player {PeerIndex} asks for the bag of {Uid} again, its copy differs: sent to everyone`
- Invité, Warning : `Bag of {Uid} brought to its keeper's copy (ours {Own}): {Added} added, {Removed} removed, {Moved} moved, {Counted} amounts, {Worn} worn or taken off, same now {Same}`
  (`Same` faux = le sac diffère encore après coup : à lire en premier).
- Invité, Information : `Bag of {Uid} differs from its keeper's and stays as it is: {Why}`
  (`rule off`, `busy`, `our own bag, sub-option off`, `not asked by us`, `it moved since we asked`).
- Host, Warning : `Refusing CharaBagDelta from peer {PeerIndex}, uid {Uid}` (un invité envoie un sac : jamais accepté).
- `emp.desync` : `bags asked …, own bag repair …`.

### Pas sûr
- Jamais lancé. Le plus fragile : `body.Equip` / `Unequip` rejoués sur un personnage (emplacements décalés entre deux
  jeux : alors rien n'est équipé et `Same` reste faux), et le remplacement du sac du joueur pendant qu'une fenêtre de
  sac flottante est ouverte (supposé : les fenêtres flottantes ne comptent pas comme « menu ouvert »).
- La réponse part à tous les invités, pas au seul demandeur : un gros sac (plusieurs centaines d'objets) pèse
  plusieurs dizaines de Ko, au plus une fois par 5 s et par personnage. Prix de l'ordre exact dans le fil.
- Un message déjà fait chez l'host mais placé après la réponse dans la même liste est rejoué sur un sac qui le
  contient : sans effet pour les types lus (`CardAddThingDelta`, `CardModNumDelta`, `CharaEquipDelta`,
  `CardRemoveThingDelta`, `CardGenDelta`), pas lu pour tous.
- Un objet que je porte moi-même et que l'host met dans le sac d'un autre : laissé (mon sac n'est pas touché sans la
  sous-option), le sac de l'autre reste en écart, redemandé de plus en plus rarement.
- Pas couvert : les sacs des compagnons et des habitants (pas dans les nombres), la case d'un objet dans la grille.
- Session de zone (invité chez un invité) : même code, pas dans la suite.

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

## Après relecture (seconde passe, 2026-10-06, nuit)

Compilé (`ReleaseNightly`, 0 erreur), **jamais lancé**.

- **Les nombres du passage de main ne comptent plus la case** des objets au sol (`ZoneLeaseState.Sums`) : numéro +
  quantité, comme `NetDesync.Collect`. Raison : un objet lancé ou éparpillé tombe aux dés de chaque jeu ; avec la case,
  le repreneur rechargeait la carte de l'host à chaque départ après un combat. Le contenu des coffres reste compté
  (numéro, contenant, quantité). Un objet à une case différente n'est donc plus vu par ce passage non plus.
  `dev/_tools/desync_suite.py` ne dépend pas de la case dans ses vérifications de rechargement (le seau retiré du sol
  change le nombre d'objets) : rien à y changer.
- **Demande de sac** (le drapeau `NetDesync.RepairBags` n'est pas changé, il reste éteint) : au plus **3 demandes par
  personnage et par séjour sur une carte** (`_bagAsksOnMap`, remis à zéro quand la carte comparée change, comme
  `MaxFruitless`), en plus de l'attente doublée ; côté host (`CharaBagDelta.Answer`) au plus **une réponse par 30 s et
  par personnage**, quel que soit le demandeur (c'était 5 s). La réponse part à tous : une demande refusée par cette
  attente est perdue, le demandeur ne la renouvelle qu'après sa propre attente (30 s puis 60 s...).
  La phrase plus haut « au plus une fois par 5 s et par personnage » est donc devenue « par 30 s ».
- Pas sûr : la suite `resync_suite.py` R4/R5 (non relue ici, hors de ma liste) peut compter sur l'ancienne attente de
  5 s de l'host ; la case des sacs est éteinte de toute façon.
