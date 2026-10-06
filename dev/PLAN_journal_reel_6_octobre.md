# Journal réel du 6 octobre 2026 (partie à 4, version 0.26.524)

Journal lu : `Session_20261006.log` du joueur (hors dépôt). Il est client jusqu'à 19:54Z (plusieurs sessions depuis
12:59Z), puis host de 20:12Z à 20:31Z avec trois invités (582 LemiWinks, 541 Arma Minima, 658 Nardole).
Corrections ci-dessous : compilées, **pas jouées** (l'utilisateur jouait). Tests écrits : `guest_suite.py` G40 et G41.

## Défaut A : `CharaActPerformDelta` avec `ActId` 0 qui lève chez l'invité (107 fois : 47 + 60)

**Ce n'est pas une baguette.** `ToolKind: "Zap"` est la valeur par défaut du champ quand il n'y a pas d'outil
(`CharaActPerformDelta.ToolOf` rend `(null, ToolAct.Zap)` pour tout acte qui n'est pas un acte d'outil).

Faits du journal : toujours `Owner.Uid` 1 (le personnage de l'host), toujours une cible monstre (20 monstres
différents), en plein combat, par salves à 0,3 à 0,8 s d'intervalle (19:49:14 à 19:49:42 : 23 fois). Quand le joueur
est host lui-même (après 20:12Z), aucun acte 0 n'est envoyé : son personnage ne pare pas.

Cause (lue) : `ActMelee.Perform` du jeu, quand le défenseur pare, fait
`new ActMeleeParry().Perform(orgTC.Chara, cC)` (et `new ActMeleeCounter()` pour la contre-attaque, `ActMeleeBladeStorm`,
`ActMeleeSwarm`, `ActMeleeWhilrwind` pour chaque coup d'une rafale). Ces actes sont créés par `new`, sans numéro
(`id` 0). Le patch `CharaActPerformEvent` est posé sur toutes les redéfinitions de `Act.Perform` : il voit ce coup
imbriqué, avec `Act.CC` = celui qui pare, et l'envoie. À l'arrivée, `ACT.Create(0)` cherche l'élément 0, qui n'est pas
un acte : `InvalidCastException`. L'host de cette partie avait de la parade (élément 437) : chaque parade = une exception
chez chaque invité.

Qui applique l'effet : les dégâts ne viennent jamais du rejeu chez un invité (`CardDamageHpEvent` coupe `DamageHP`
hors host, l'host envoie `CardDamageHpDelta` avec les points de vie). Le rejeu d'un acte n'est que l'animation, tirée
avec les dés de l'invité. Le rejeu de l'attaque du monstre tire donc déjà sa propre parade chez l'invité.

Correction : `Patches/DeltaEvents/Chara/CharaActPerformEvent.cs` (après `Create`) : un acte sans numéro et sans outil
n'est plus envoyé. Rien n'est perdu (il levait toujours), rien n'est doublé (le rejeu de l'acte autour frappe le sien).
Même chose dans l'autre sens : la parade tirée chez un invité pendant le rejeu partait vers l'host (`Act.CC.IsPC`) et y
aurait levé pareil.

Avant / après pour le joueur : les dégâts de la parade arrivaient déjà ; ce qui change est 60 exceptions en vingt
minutes en moins dans le journal. Ce défaut n'explique pas à lui seul une « desync » visible.

Reste vrai : l'animation de parade chez l'invité est tirée chez lui, elle ne tombe pas forcément sur le même coup que
chez l'host (comme touché / raté aujourd'hui).

## Défaut B : `Progress begin … has no matching act` (12 TaskHarvest, 5 TaskChopWood pour 582 ; 1 AI_UseCrafter pour 658)

Le message veut dire : quand l'invité annonce qu'il commence, la copie de sa tâche chez l'host n'existe plus (ou n'a
jamais tourné). Deux causes différentes.

### B1. Coupe de bois : toujours au dernier rondin (5 sur 5)

Séquence (20:20:28 à 20:20:33, case 42,45) : arbre abattu (3 cartes d'un coup), planche 200677 à :30.867, planche
200678 à :31.730, puis à :33.230, dans le même tick : `no matching act TaskChopWood`, planche 200684 et l'expérience
de bûcheron. Pareil à 20:22:33 (2 rondins), 20:22:41 (3), 20:22:45 (1), 20:23:05 (2) : l'avertissement tombe
**toujours avec la dernière planche**.

Cause (lue) : `TaskChopWood.Loop => GetLog() != null`. Chez l'host, la dernière planche vide la pile, la tâche finit.
Chez l'invité, `CharaProgressCompleteDelta.OnApply` fait `ai.Tick()` **avant** d'appliquer `DeltaList` (où se trouve
le rondin retiré : `Card.ModNum` ne fait rien chez un invité hors delta). L'invité voit encore un rondin, relance un
tour, l'annonce ; l'host n'a plus la tâche et demande l'annulation.

Ce que vivait l'invité : après le dernier rondin, le message « vous commencez à tailler » une fois de trop, puis
l'arrêt un aller-retour réseau plus tard. Les planches sont bien là. Gêne légère, pas de perte.

Correction : `Patches/DeltaEvents/Chara/CharaProgressBeginEvent.cs` : chez l'invité, pour son personnage, un tour qui
commence **pendant** le rejeu de la fin du précédent, sous une tâche à boucle (`TaskPoint`), n'est pas annoncé tout de
suite : `progress = -1`, le début est sauté, et `AIProgress.Run` le rejoue au tick suivant (progress revenu à 0), après
avoir revérifié `CanProgress` avec l'état à jour. S'il n'y a plus de rondin, la tâche s'arrête sans rien annoncer.
Vaut aussi pour puiser / verser de l'eau (`TaskDrawWater`, `TaskPourWater`, même boucle sur les charges).

Correction plus directe, hors des fichiers autorisés (à décider) : dans `CharaProgressCompleteDelta.OnApply`, appliquer
`DeltaList.ForEach(action => action.Apply(net))` **avant** `ai.Tick()` (aujourd'hui après). La tâche finirait alors
par `SetNoGoal`, sans passer par une annulation. Non fait : l'ordre actuel sert peut-être aux ramassages rejoués
(`CharaPickThingDelta` lit `IsReplaying`), à vérifier en jeu.

### B2. Récolte : rafales de refus sans rien de récolté (12 sur 12)

Séquence (20:17:42 à 20:18:23), tout ce qui concerne 582 :
- :42.857 `Replaced remote chara 582` (il revient sur la carte de l'host), :42.886 `Reset remote … NoGoal / NoGoal`.
- :45.7, :47.1, :48.4, :49.3, :51.0 : cinq cueillettes réussies (expérience 250, cartes posées en 40,42 / 40,38 / 41,36).
- :53.247 : un arbre abattu en 43,36 (expérience 225 bûcheron, 3 cartes). L'host connaît donc sa hache à ce moment.
- :56.347, :57.145, :57.695, puis 18:02.278 et 18:23.808 : `no matching act TaskHarvest`, **aucune carte, aucune
  expérience**. Écart de 0,55 à 0,8 s : c'est le rythme du clic droit maintenu.
Même dessin à 20:22:48 à 20:22:58 : deux cueillettes réussies, puis sept refus, puis un arbre abattu à 20:23:00.7.

Ce que vivait l'invité : il clique sur un arbre, « vous commencez à récolter », arrêt aussitôt, et ça recommence tant
qu'il garde le bouton. Rien n'est récolté, ni chez lui ni chez l'host. C'est une vraie différence host / invité.

Cause la plus probable (le mécanisme est lu dans le code ; le journal ne peut pas la prouver, il n'a aucune ligne à
l'arrivée d'une tâche ou d'un changement d'outil) : **l'outil en main de l'invité n'est pas le même chez l'host.**
- `Card.Tool` d'un personnage, dans ce mod, est `chara.held` (`RemoteGetToolPatch`).
- `CharaSwitchHeldDelta.OnApply` ne met pas l'outil en main si `chara.ai is GoalRemote { child.status: Running }`
  (« do not update tool if running task »), et `NetProfileSynchronizationContext` ne le renvoie jamais (il n'envoie
  qu'au changement).
- Or toute tâche que l'host ne sait pas tenir (marcher : `GoalManualMove`, `AI_Goto`…) part en `FakeTask`, dont la
  copie chez l'host est un `NoGoal` qui se relance sans fin (`Restart`) : « Running » jusqu'à la tâche suivante.
- Donc : l'invité change d'outil **en marchant** → perdu chez l'host. Il clique un arbre → chez l'host,
  `TaskHarvest.OnCreateProgress` / `onProgressBegin` fait `TryGetAct(owner, pos) == null` (pas d'outil de bûcheron en
  main) → `p.Cancel()` → la tâche tombe aussitôt → l'annonce de l'invité ne trouve rien. Les cueillettes (élément 250)
  ne demandent pas d'outil : elles passent, ce qui colle au journal (cueillettes réussies juste avant chaque rafale).

Correction : `Models/Delta/Chara/CharaTaskDelta.cs`, juste avant `remote.InsertAction(act)` : si l'outil annoncé par le
joueur (`NetProfile.RemoteMainHand` = `RemoteOffHand`, gardés même quand la mise en main est refusée) n'est pas celui
que la copie tient, et qu'il est bien dans son sac, `chara.HoldCard(...)`. Vaut chez l'host et chez les autres invités.
Ajout d'une ligne de journal (Debug, host) : `Task {ActType} of chara {Uid} was over as soon as started here, tool
{ToolUid}` : la prochaine vraie partie dira pourquoi une tâche tombe.

Correction plus directe, hors des fichiers autorisés : dans `CharaSwitchHeldDelta.OnApply`, remplacer
`if (chara.ai is GoalRemote { child.status: AIAct.Status.Running })` par
`if (chara.ai is GoalRemote { child: { status: AIAct.Status.Running } and not NoGoal })` (même test dans
`CharaBagDelta.cs` ligne 265).

Pas couvert : main vide chez l'invité et outil resté en main chez l'host (le profil par défaut est vide aussi, on ne
peut pas les distinguer ici) ; un personnage « remplacé » (`Replaced remote chara`) repart avec un profil vide, son
outil vient alors de `CharaBagDelta`.

Autres causes possibles non écartées : l'objet n'existe plus sur la carte de l'host (carte différente), ou trop dur
chez l'host seulement. La nouvelle ligne de journal tranchera.

### Le 18e : `AI_UseCrafter` de 658 (20:23:52)

`Remote craft round 2 complete` puis `Remote craft aborted on host` (AIUseCrafterPatch.NotifyClientCancel : l'host
arrête la fabrication, ingrédient épuisé) et, 115 ms après, l'annonce du tour suivant de l'invité, déjà partie.
Croisement attendu, sans effet.

## Au passage (non corrigé)

| Message | Nombre | Lecture |
|---|---|---|
| `Dropping {MessageType} from host at handshake stage` | 3114 (168 après 19:32) | `ElinNetClientIntegrity` : instantanés du monde reçus pendant que l'invité est encore à la vérification des sources (fenêtre « sources différentes » ouverte). Attendu, mais bruyant : il noie le journal |
| `Reconcile force move chara` | 94 chez l'host (582 : 41, 658 : 38, 541 : 15) | `CharaStateSnapshot` : la copie d'un invité est à plus de 2 cases de sa position annoncée sans déplacement récent. 85 sur 94 à 3 ou 4 cases : chez l'host, les invités qui marchent sautent de 3 cases. **Défaut réel, visuel.** Une fois (20:22:32) un aller-retour 40,50 ↔ 62,51 dans la même milliseconde à un retour de zone |
| `Player {PeerIndex} reports a map checksum that differs` | 34 chez l'host | `NetDesync` : 20 fois « bags of 1 » (le sac de l'host vu par un invité), 4 avec rechargement. **Défaut réel** : le sac de l'host n'est pas le même chez les invités. Côté client, 5 fois « bags of 1 » à Nymelle |
| `Falling behind with {DroppedTicks}` | 25 (11 après 19:32 : 7 à 116) | `ElinNetClientUpdate` : trou entre deux instantanés. Les 11 tombent tous juste après un changement de zone ou un retour : attendu (chargement). 116 à 19:52:09 = environ 14 s |
| `Relay Pick … failed to store in 1, forcing local` | 16 (5 après 19:32) | `CharaPickThingDelta` : l'host ramasse, chez l'invité l'objet ne rentre pas dans la copie du sac de l'host et y est mis de force. Même famille que « bags of 1 » : **réel**, sans effet pour l'invité |
| `Dropping CardAddThingDelta from peer 0, uid … cannot be resolved here` | 5 (19:36:09 à 19:37:01) | `CardAddThingDelta` : l'host range un objet que l'invité n'a jamais reçu (uids 122644xx, 122645xx : butin créé chez l'host). **Réel** : objet manquant chez l'invité, sans doute la source de « bags of 1 » |
| `Card uid conflict … refusing incoming` | 10 (avant 19:32, ex. `axe`) | `CardCache` : deux cartes avec le même numéro chez l'invité. « if there is nothing wrong, this shouldn't happen ». **Réel**, version précédente, à revoir si ça revient |
| `Exception … CharaAddConditionDelta` | 1 (19:36:37) | `ConWeapon.SetOwner` → `BaseCondition.GetElementSource` : clé `''`. Condition 56 (arme enchantée) envoyée sans son élément. **Réel**, rare : la condition n'apparaît pas chez l'invité |
| `Source validation failed — 2 mismatches` | 16 | `SourceThing` différent et `ciryl.elin.visibleequipment` absent chez l'invité. Attendu (mods différents), le joueur a continué |
| `Attempting to add destroyed item 250757` + `Refusing stale ZoneAddCardDelta from peer 2` | 1 + 1 | Un invité qui vient de se connecter renvoie la pose d'une planche déjà ramassée et empilée. Refusé proprement. Attendu |
| `Remote craft aborted on host` | 1 | Voir plus haut. Attendu |
| `Removing quest from player chara` | 4 | `QuestSynchronizationContext` : quête d'un personnage joueur retirée (`meal_fruit`). À regarder : un joueur perd-il sa quête ? |
| `Disconnected from host` (host shut down, connection timed out), `Zone state mismatch`, `Zone sync failed after 3 attempts`, `Host entered away zone … without recall`, `Handed zone … while not in it`, `Client copy of chara … destroyed, not synced`, `Lobby enter refused` | 14, 3, 1, 3, 1, 1, 1 | Presque tous avant 19:32 (versions précédentes de l'après-midi). `Zone sync failed` (13:20) a déconnecté le joueur |
| `Dropping ZoneDataReceivedResponse from {Peer} at handshake stage Joined` | 7 chez l'host | `ElinNetHostIntegrity` : réponse d'un invité « ailleurs ». Attendu |

## Tests écrits (pas lancés)

`dev/_tools/guest_suite.py` :
- **G40** : l'host zappe un monstre à côté de l'invité, puis pare les coups d'un monstre (élément 437) : mêmes points
  de vie du monstre dans les deux jeux, aucune `Exception at processing delta` dans le journal.
- **G41** : l'invité clique pour marcher vers un arbre, prend sa hache en marchant, abat l'arbre (un clic droit par
  tour), taille trois rondins à la chaîne : arbre et rondins partis dans les deux jeux, même bois dans son sac des deux
  côtés, aucun `no matching act` dans le journal.

À vérifier au premier lancement : que le journal lu par `session_log_lines` contient bien les lignes de l'invité (les
fenêtres du banc partagent-elles le même fichier ?), sinon G40 ne voit pas l'exception.
