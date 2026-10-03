# Plan — retours de la vraie partie du 2026-10-03 (l'utilisateur était l'invité)

Quatre demandes de l'utilisateur, plus ce que ses journaux ont montré. Trois agents ont lu le code (lecture seule).

## État

| Sujet | État |
|---|---|
| Habitant de la base à qui un invité demande de « rejoindre le groupe » : ne suivait personne | **corrigé** `1189ac0`, `recruit_suite` rouge 10/22 → vert 21/21 |
| L'host revient : l'invité était replacé à côté de lui | **corrigé** `23554f2`, `leave_suite` L2 rouge 8/10 → vert 13/13 |
| L'host revient : la carte était chargée deux fois de suite chez l'invité | **corrigé** `23554f2` (second état de zone ignoré) |
| Somewhat Enhanced Display : une erreur par image après la fin de la session | **corrigé** `7238c7a`, `compat_suite` rouge 356 erreurs → 0 |
| Bonus de première fabrication d'un invité noté chez l'host | **corrigé** `b164dd7`, `player_suite` F6 |
| « Un joueur seul sur une carte qu'il tient ne peut pas dormir » | **n'existe pas** : `sleep_suite` Y1 6/6 |
| Alliés faits par l'host à la place d'un invité (boule à monstre, brosse, monture, œuf) : suivent l'host | à faire (cause 2) |
| Esclave ou animal acheté par un invité, animal de Fiama : la demande est jetée, l'or est payé | à faire (cause 3) |
| L'host revient : le rechargement lui-même | plan B ci-dessous, gros |
| Rejoindre avec un personnage d'une sauvegarde solo | plan ci-dessous, à coder |
| Déplacements de l'invité moins fluides que ceux de l'host | à l'étude (agent + mesure) |

## Compagnons : causes restantes

- **Cause 2** : l'host exécute `MakeAlly`/`AddMemeber` pour l'invité sans savoir pour qui (boule à monstre
  `ActThrowDelta`, brosse `AI_Fuck`, effet « allié », familier du dieu, œuf, monture `ActRide`). Correction :
  donner le « joueur qui agit ». Dans `ElinDelta.Apply` côté host, ouvrir `CharaMakeAllyEvent.GiftsFor(joueur)` quand
  `OriginPeer` est un joueur actif ; dans `OnMakeAlly` et `PartyJoinEvent` côté host, si le propriétaire est 0 et que
  `CharaProgressCompleteEvent.Chara` est un joueur distant, le prendre.
- **Cause 3** : le personnage acheté n'existe que chez l'invité ; `CharaMakeAllyRequestDelta.ReplayLocalCopy`
  n'accepte que « mamani2 ». Correction : joindre les données du personnage à la demande, le créer chez l'host.
- Pas couvert même avec un propriétaire : la laisse et la consigne « ne pas s'éloigner » regardent l'host ; les
  invocations ne changent pas de carte avec l'invité.
- Test : `recruit_suite` R7 (vrai « inviter » par le dialogue), R8 (boule à monstre ou monture).

## Retour de l'host sans rechargement (plan B)

Aujourd'hui : l'host sort → l'invité hérite de la carte sans rechargement (il garde son jeu, `AwayZone`, plages de
numéros). L'host rentre → rappel : l'invité rend carte et personnage, reçoit le monde entier de l'host, recharge.

Proposé, derrière une case décochée par défaut (`SoftRecall`), seulement si : carte héritée à l'instant, retour
dans les 120 s, aucun autre invité, ni carte du monde ni zone de quête.

1. Host → invité : `ZoneLeaseRecall{Soft}`.
2. L'invité se met en pause, envoie `ZoneLeaseRelease{KeepLoaded, carte, personnage, compagnons, habitants}` et
   garde sa carte chargée.
3. L'host applique, inscrit le joueur sans renvoyer le monde, entre sur la carte.
4. L'host envoie `ZoneSoftRejoin{date, uidNext, arrivants, empreinte}`.
5. L'invité compare l'empreinte à sa carte, bascule en simple client, ajoute l'host et ses compagnons, accuse
   réception.
6. Au moindre écart ou délai : repli sur le rechargement actuel.

Taille estimée : 500 à 700 lignes, 2 messages nouveaux. Étapes : découper `SendSaveProbe` et la fin de
`OnZoneDataReceivedResponse` sans changer le comportement ; habitants rendus avec la carte
(`ZoneLeaseRelease.Residents`, utile aussi au chemin actuel) ; option ; messages ; host ; client.
Tests : `leave_suite` L2 doux (`pc_id` inchangé), repli forcé, option décochée, `shared` et `trio` inchangés.

Les variantes « annuler la passation si l'host revient vite » et « garder la carte chez l'invité » ne marchent pas :
la carte de l'host se décharge à l'instant où il sort, et l'host ne peut pas être invité (son jeu est le monde).

## Personnage d'une sauvegarde solo (version 1)

- Troisième choix à l'écran de connexion : « A character from one of my saves… », case host `ImportCharacter`
  (décochée par défaut), deuxième liste : les 8 sauvegardes les plus récentes lisibles.
- Lecture **à côté** du jeu : désérialiser le `Game` de `Save/<id>/game.txt` (LZ4 éventuel, `GameIO.jsReadGame`,
  `ModUtil.fallbackTypes` de l'index), sans `Game.Load`, remettre `Game.Instance` ; prendre
  `cards.globalCharas.Find(player.uidChara)`, `player.fame`, `player.karma`. Fichier ouvert en lecture seule.
- Emporté : le personnage entier (caractéristiques, talents, dons, apparence, équipement, sac, or), renommée et
  karma. Laissé : compagnons, monture, base, quêtes, banque, recettes, objets-clés.
- `CharaImport.Detach` (champs seulement) : `party/ride/parasite/host/held/quest/enemy/global = null`, zones à 0,
  conditions vidées, objets `TraitAbility`/`TraitBill`/`TraitChestMerchant` retirés, `c_uidZone`/`c_uidRefCard` à 0.
- Host : `CharaImport.Adopt` = `game.cards.AssignUIDRecursive(chara)` (numéros neufs), `c_uidAttune` remis,
  `SetGlobal`, faction, puis `SavedRemoteCharas`, `RosterOf`, `PlayerStandings`, `SendSaveProbe` comme d'habitude.
- Message : `SessionCharaImportResponse{Chara, Fame, Karma, Source}` ; `SessionCharaSelectRequest.AllowImport`.
  Refus d'un second import de la même source tant que la copie est dans la liste du joueur.
- Risques : artefacts divins en double détruits par `PurgeDuplicateArtifact` (à prouver), mods différents (objet
  inconnu → cendre), cadeaux du dieu reçus de nouveau, grosses sauvegardes (gel de quelques secondes).
- Test `import_suite.py` : copier `world_lab` en `world_import`, importer, vérifier niveau, or, équipement et objet
  repère chez l'host et le client, aucun numéro en double, sauvegarde inchangée, reconnexion, refus du doublon.
