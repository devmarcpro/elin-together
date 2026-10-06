# Invité bloqué en lisant un livre quand l'host quitte la carte (retour 21, 0.26.532)

État au 2026-10-07 : **écrit, compilé (Release, 0 erreur), jamais joué.** Test écrit : `place_suite.py` P8, jamais lancé.

## 1. Ce qui a bloqué le joueur

Journal `891537ac-Session_20261007.log` (le joueur est l'invité, son personnage a le numéro 1) :

| Heure (UTC) | Ligne | Lecture |
|---|---|---|
| 22:06:26 | `Received zone activation` (étage -3) | il rejoint l'host, rôle `Client` |
| 22:06:36 | `Requesting party sleep` | demande de sommeil, sans suite visible |
| 22:06:41 à 22:06:44 | `Replaying progress complete AI_Eat of chara 1` | il mange : il n'est donc ni endormi ni figé à ce moment |
| 22:06:50.156 | `Taking over Zone_dungeon_plain@-3 from the host: our copy is the same, kept` | l'host descend, la carte lui est laissée telle quelle, rôle `Away`, `Connection` nul |
| 22:07:22 | `Blocked saving game as client`, puis retour au titre | il quitte |

Aucune ligne ne parle de lecture : le mod n'écrit rien quand une tâche commence ou est retenue. La lecture a donc
commencé entre 22:06:44 et 22:06:50, ou juste pendant le départ de l'host.

**Cause la plus probable (lue dans le code, cohérente avec le journal, pas prouvée par lui).**
- Sur la carte de l'host, une tâche à progression d'un invité est retenue : `CharaProgressBeginEvent.cs`, le compteur
  est mis à `HeldProgress.Held` (un nombre très négatif) et seule la fin envoyée par l'host
  (`CharaProgressCompleteDelta`) la termine.
- Une lecture ne peut pas être arrêtée à la main : `AI_Read` ne redéfinit pas `AIAct.CanManualCancel` (faux), et
  `AM_Adv.TryCancelInteraction` avale alors chaque clic et chaque touche de déplacement tant que la tâche tourne.
- Au passage de main (`ElinNetClientTravel.cs`, « Took over zone »), rien ne touche à la tâche du joueur. `Connection`
  devient nul, plus aucun patch ne s'applique, le jeu compte les tours depuis -2 milliards : la lecture ne finit jamais.
  Le filet de 2 s de `CharaTaskCancelEvent` ne sert à rien ici : il ne part que si un arrêt est demandé, et le jeu
  n'en demande pas pour une lecture.
- Seule sortie pour le joueur : prendre un coup (la lecture s'arrête aux dégâts) ou quitter.

**Variantes du même défaut** (même remède) :
- l'host ne joue pas la lecture sans le dire (`CharaProgressBeginDelta.OnApply` sort sans réponse si le personnage
  n'est pas trouvé, n'est pas en `GoalRemote`, ou si l'acte est inconnu) : retenue pour toujours, même sans passage
  de main ;
- l'invité visite la carte d'un autre invité et la session de zone se ferme pendant la tâche.

**Pistes écartées.**
- Sommeil : la demande de 22:06:36 n'a pas endormi le joueur (il mange 5 s après) ; `_requested` s'efface seul après
  5 s (`RequestLife`). Trois demandes dans ce journal, aucune trace de nuit côté invité (l'ouverture de l'écran de
  nuit chez un invité n'écrit rien : on ne peut pas dire si elles ont abouti).
- Fenêtre de livre : un livre ordinaire (`TraitBook`) se lit en zéro tour, sans progression ; sa fenêtre se ferme.
- Patch qui regarde `Transport is ElinNetClient` : aucun de ceux-là ne retient une tâche (liste lue : compagnons,
  expédition, base, quêtes, sommeil).

**Ce qui confirmerait** : la réponse du joueur (question en bas) ; le journal de l'host entre 22:06:44 et 22:06:50
(un `Progress begin AI_Read … requesting cancel` irait vers la variante) ; P8 rouge sur la 0.26.532 et vert ensuite.
Avec la correction, le journal de l'invité dira désormais `The game that kept the map is gone, AI_Read goes on here`.

## 2. La correction

Choix pour une lecture retenue au passage de main : **elle reprend ici**, au nombre de tours déjà attendus. Raison :
l'invité tient maintenant la carte et son sac, l'host n'a pas fini la lecture (sa fin serait arrivée avant le passage
de main), donc la finir ici la fait une seule fois ; l'annuler aurait fait perdre au joueur les tours déjà lus.
Exceptions, arrêtées sans rien consommer : une fabrication (son produit est fait par le jeu qui tient la carte, ici
elle finirait à vide) et le cas où un autre jeu tient la carte (il ne connaît pas la tâche).

- `ElinTogether/Helper/PendingOnHost.cs` (repris du commit `ee7c1ee`, gardé pour l'essentiel)
  - `Watch` (l. 26) : une surveillance par progression retenue du joueur local, image par image, dans ce fichier
    seul (aucun appel dans les fichiers réseau). Elle s'éteint dès que la progression n'est plus retenue.
  - l. 51 : `Connection` n'est plus le jeu à qui la tâche a été annoncée → `Release` (l. 74) : reprise locale
    (l. 81 à 86) ou arrêt propre (l. 89 à 92). Une ligne `Information` dans le journal dans les deux cas.
  - l. 56 à 68, filet général : plus de 6 s ET (plus de 3 × la durée + 20 tours attendus, OU plus de 6 s + 1 s par
    tour de durée) sans fin → `Warning` « No end to … » et arrêt par le chemin normal (dit à l'host, fait ici après
    2 s sans réponse). Pas de limite fixe en secondes : une fabrication ou un minage long est légitime, la limite suit
    la durée de la tâche (lecture de 5 tours : 11 s au pire ; grimoire de 25 tours : 31 s au pire, quelques secondes
    en pratique car les tours passent vite).
  - Ajouté : une image d'attente avant la première vérification (l. 48 ; la surveillance est lancée depuis le premier
    tour de la progression, avant qu'elle soit en place) ; la limite en secondes quand les tours ne passent pas.
  - Défait : `Release()` sans argument, que personne n'appelait.
- `ElinTogether/Patches/DeltaEvents/Chara/CharaProgressBeginEvent.cs` l. 62 à 65 : gardé tel quel (lance la surveillance).
- `ElinTogether/Patches/DeltaEvents/Chara/CharaTaskCancelEvent.cs` l. 73 à 103 : gardé (un arrêt en attente n'attend
  plus un jeu qui ne tient plus la carte : fait aussitôt) ; ajouté une ligne de journal distincte pour ce cas
  (avant : « pas de réponse après 2 s », faux).
- `dev/_tools/place_suite.py` : étape P8 (`reading`, `within`, `read_while_host_leaves`, `p8`).

Non touchés : les deltas, `HeldProgress`, `CharaProgressCompleteEvent`, `CharaTaskRemoteEvent`.

**Attention, dépôt** : le commit `e47ecd2` d'une autre session (« a guest keeps its own settings… ») a emporté ces
changements pendant le travail (`PendingOnHost.cs`, `CharaTaskCancelEvent.cs`, `place_suite.py`). Son message n'en
parle pas. Ce fichier de notes, lui, n'est pas commité.

## 3. Les autres attentes « de l'host » au passage de main

| État du joueur local | Bloqué ? | Pourquoi / correction |
|---|---|---|
| Progression retenue (lecture, récolte, minage, repas, pêche…) | **oui avant**, corrigé | section 2 |
| Arrêt de tâche en attente | non (2 s) ; immédiat maintenant | `CharaTaskCancelEvent.StopIfNoAnswer` |
| Fabrication `AI_UseCrafter` retenue | **oui avant**, arrêtée proprement maintenant | rien n'est consommé chez l'invité. **Pas sûr** : l'host a déjà posé les ingrédients près de l'atelier dans SA copie (cachés pour le micro-ondes) ; si c'est sa copie qui est chargée (« our copy differs »), ils sont au sol. Bon remède, hors de mes fichiers (`Net/Host/ElinNetHostTravel.cs`) : avant de laisser la carte, l'host arrête la tâche en cours de chaque invité (`TaskCache.RequestCancel`), ce qui rend les ingrédients et prévient l'invité |
| Demande d'objet `ThingRequest` (glisser, partager une pile, acheter) | non | la réponse ne vient pas, le geste ne se fait pas, rien n'est modal. Les rappels en attente restent en mémoire jusqu'au prochain rechargement (`ThingRequest.Clear`). **Pas sûr** : si l'host avait déjà sorti l'objet de son coffre (objet « en suspens », rendu après 10 s chez lui seulement), l'objet peut manquer dans la copie laissée. Fenêtre de quelques millisecondes |
| Glisser déjà commencé | non | l'objet est dans la main du joueur, il le pose chez lui ; même doute que ci-dessus |
| Demande de sommeil | non | `_requested` s'efface en 5 s ; une nuit déjà commencée finit comme en solo (`OnAdvance`, `guest is null`). Lu, pas joué. Reste possible : lit et oreiller posés au sol par le jeu avant la demande, à ramasser à la main |
| Question de quête (`SharedQuests._awaitingHost`) | non | délai `HostAnswerTimeout` |
| Demande à la base (`BaseRequestDelta`) | non | délai de 5 s |
| Copie d'objet en boutique (`CopyShopDelta`) | non | le dialogue reste ouvert, l'étape ne se joue pas ; le joueur le ferme |
| Échange entre joueurs, duel | non | `PlayerTrade.WatchSession` ferme tout dès que `Connection` change (même méthode qu'ici) |
| Combat au tour par tour | non | `ActionModeCombat.CheckIfPauseNeeded` : phase inactive dès que `Connection` est nul |
| **Mort en attente de réanimation** (`CharaReviveEvent.OnCharaRevive`) | **peut-être** | la réanimation est demandée à l'host et celle du jeu est sautée ; si la demande se perd au passage de main, le joueur reste mort. Fenêtre courte. Correction en quelques lignes, hors de mes fichiers (`Patches/DeltaEvents/Chara/CharaReviveEvent.cs`) : noter l'heure de la demande, et à l'image suivante où `Connection` n'est plus le client à qui elle est partie alors que `pc.isDead`, rappeler `pc.Revive()` (qui passe alors par le jeu) |

## 4. Le test (P8, `place_suite.py`, jamais lancé)

`python _tools/place_suite.py --only p8`, deux fenêtres à la Prairie. Deux passes :
- **livre** (livre de compétence, 5 tours) : l'host part à Vernis, la lecture commence pendant son départ ;
- **grimoire** (au moins 200 tours : niveau du livre monté, lecture en `godMode` pour qu'elle ne rate pas) : la
  lecture est d'abord vue retenue (compteur négatif), puis l'host part.

Vérifié à chaque passe : moins de 5 s après que l'invité tient la carte, sa lecture n'est plus retenue ; elle finit ;
le livre a perdu une charge (ou un exemplaire) au plus ; l'invité est libre (`HasNoGoal`) et avance d'une case.

Limites : la lecture est posée par `SetAI(new AI_Read)` et l'host part par `MoveZone`, pas par un escalier ; le livre
de 5 tours peut être fini avant le départ de l'host (seul le grimoire prouve le cas) ; le filet général (host présent
qui ne répond pas) n'a pas de test : il faudrait un host qui ignore la tâche.

## 5. Pas sûr

- Rien n'a été joué. La cause est déduite du code ; le journal ne la contredit pas mais ne montre pas la lecture.
- Reprise locale quand la copie de l'host remplace la nôtre (« our copy differs ») : la surveillance s'éteint si le
  personnage est remplacé, sinon la tâche reprend sur une cible peut-être rechargée (elle s'annule alors d'elle-même
  par `CanProgress`). Lu, pas joué.
- Le filet général compte sur des tours qui passent à peu près au même rythme chez l'invité et chez l'host
  (accéléré partagé). Si l'invité allait plus de trois fois plus vite, une longue fabrication légitime serait arrêtée
  (rien de perdu, mais agaçant). À surveiller dans les journaux : la ligne `No end to …`.
- Les trois demandes de sommeil du journal sans nuit visible : à regarder à part (fichier du sommeil en lecture seule).

## 6. Question pour le joueur

« Quand tu es resté bloqué, quel livre lisais-tu (un grimoire de sort, un livre ancien, un livre de compétence), et
est-ce que la barre de lecture était affichée et figée au moment où l'autre joueur a pris l'escalier ? »
