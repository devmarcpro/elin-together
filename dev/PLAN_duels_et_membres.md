# Duels entre joueurs et gestion de la base par un invité : les faits, les options, les tests

Écrit le 2026-10-05 par **lecture seule** : jeu décompilé EA 23.352 (`dev/_decomp/Elin/*.cs`), mod (`ElinTogether/ElinTogether/`), bancs
`dev/_tools/`, plans et journal. **Rien compilé, rien joué, aucun commit.** Chaque fait a son `fichier:ligne` ; ce que la lecture ne
permet pas d'affirmer est écrit « non vérifié » en fin de partie. Abréviations : `JEU` = `dev/_decomp/Elin/`, `MOD` =
`ElinTogether/ElinTogether/`. Numéros d'union libres au moment de l'écriture : **833 et suivants** (`MOD/Models/Delta/ElinDelta.cs:118`
= 832, `CharaReviveRequestDelta`) ; clé suivante de `NetSessionRules` : **13** (`MOD/Net/NetSessionRules.cs:88`, `AllowGuestBuild` = 12).

Les deux demandes de l'utilisateur (5 octobre 2026, 15h) viennent de `HANDOFF.md` (« Demandes de l'utilisateur du 5 octobre »).
Elles sont de la conception : pour un conseil, pas à coder avant son verdict (`CLAUDE.md` : demander avant une grosse nouveauté).

---

# PARTIE 1 — Duels entre joueurs

Mots de l'utilisateur : « comme contre les aventuriers, la possibilité de faire des duels : téléporter les deux joueurs sur une autre
carte, combat à mort mais la mort d'un des joueurs signifie juste la fin du combat, aucune perte des deux côtés, peut-être la
possibilité de parier ».

## 1.1 Le duel du jeu contre un aventurier : de bout en bout

**Proposer le duel (dialogue).** Dans `DramaCustomSequence`, le choix « Duel » (`daBout`, étape `_bout`) apparaît dans deux cas :
- `JEU/DramaCustomSequence.cs:82-86` : le PNJ est unique ou global, `GetInt(111) == 0` (jamais battu), pas encore de la faction, et
  `trait.NeedBoutToJoin` (`JEU/TraitChara.cs:50`, vrai par défaut, faux pour `TraitMani`). Le duel remplace alors le choix « inviter » :
  un unique ne se recrute qu'après avoir été battu.
- `JEU/DramaCustomSequence.cs:206-209` : le PNJ a `trait.CanBout` (`JEU/TraitAdventurer.cs:13`, faux ailleurs : `TraitChara.cs:94`),
  est global, pas de la faction, et le dernier duel date de plus de 7 jours de jeu (`GetInt(59) + 10080 < date.GetRaw()`, `CINT.dateBout = 59`,
  `JEU/CINT.cs:95`). Pas dans une zone d'instance (`!EClass._zone.IsInstance`).
- Les textes du dialogue (`bout1`, `bout2`) sont dans la feuille `_chara`; le jeu installé a `bout_win` « I yield! You are good. » et
  `bout_lose` « That's it, weakling. » (`Package/_Elona/Lang/_Dialog/Drama/_chara.xlsx`, lus dans les chaînes partagées).

**Créer la zone, entrer** (`JEU/DramaCustomSequence.cs:1574-1598`, étape `_bout`) : sur « Oui »,
1. `SpatialGen.CreateInstance("field", new ZoneInstanceBout { uidTarget = c.uid, targetX/Z = c.pos })`. Cette fonction
   (`JEU/SpatialGen.cs:39-48`) crée la zone sous la région, pose `instance.x/z` = case du joueur, `instance.uidZone` = zone d'origine
   et `dateExpire` = maintenant + 1440 (un jour). La zone est un champ (`Zone_Field`, `JEU/Zone_Field.cs`), pas une arène.
2. `c.SetGlobal()` (l'adversaire devient un personnage global, qui peut changer de carte).
3. `zone.events.AddPreEnter(new ZonePreEnterBout { target = c })`, puis `c.SetInt(59, date)` (compte à rebours de 7 jours).
4. À la fermeture du dialogue : `EClass.pc.MoveZone(z, EnterState.Center)`.

**À l'arrivée** (`JEU/ZonePreEnterBout.cs:8-47`) : l'adversaire est déplacé au centre de la carte ; la musique 102 ; pour chaque membre du
groupe du joueur **sauf un** (`EClass.pc.party.members.Count - 1`), un renfort neutre de niveau `LV + 10` est créé, rendu « Superior »,
placé près de l'adversaire. Tous (adversaire et renforts) sont passés `Hostility.Enemy`, tournés vers le joueur, soignés
(`HealAll`). Donc **les compagnons du joueur viennent** (ils suivent le joueur, `JEU/Zone.cs:1749-1767` : les membres du groupe sont
placés près de l'arrivée), et l'adversaire amène autant de renforts qu'il y a de compagnons.

**Défaite et victoire** (`JEU/Card.cs:4567` lit `EClass._zone.instance as ZoneInstanceBout`) :
- Dans `Card.DamageHP`, quand `hp < 0` et que les protections habituelles (garde-fous, résurrection…) n'ont rien fait :
  `JEU/Card.cs:4621-4624` : si un dialogue est ouvert (`LayerDrama.Instance`), on esquive la mort ; sinon on arrive à
  `JEU/Card.cs:4745-4768` : le **joueur** (`IsPC`) qui tombe : `hp = 0; Heal();` (soin complet, il ne meurt pas), renommée −10 − 5 %,
  dialogue `bout_lose` de l'adversaire, `return` (pas de `Die`). L'**adversaire** qui tombe (`target == this`) : `hp = 0; Heal();`,
  affinité +10, dialogue `bout_win`, `return`. Les renforts et les compagnons tombent normalement (`Die`).
- Les actions de dialogue `bout_win` / `bout_lose` (`JEU/DramaManager.cs:1025-1041`) : à la fermeture du dialogue, le jeu retrouve la
  zone d'origine (`instance.uidZone`) ; pour `bout_win` seulement, il y pose l'événement `ZonePreEnterBoutWin` (récompense), puis
  `pc.MoveZone(zone)`.
- Récompense de victoire (`JEU/ZonePreEnterBoutWin.cs:11-38`) : l'objet **équipé** le plus cher de l'adversaire (non offert) lui est
  retiré et donné au joueur, sinon `plat × (LV/10 + 2)` à peu près ; `target.SetInt(111, +1)` (« battu » : le recrutement s'ouvre),
  renommée `+10 + (LV adversaire − LV joueur) × 3`.
- Autres règles de la zone : pas de vol à la tire (`JEU/ActEffect.cs:1954`). Le duel contre un aventurier n'a **pas** de limite de temps :
  la zone expire au bout d'un jour (`SpatialGen.cs:46`) ; elle est déchargée à la sortie (`JEU/Zone.cs:1850-1853`) et détruite (`Zone.CanDestroy`,
  instance = vrai, `JEU/Zone.cs:1957-1966`).

**Retour** (`JEU/Chara.cs:3631-3644`) : quand le joueur quitte une zone à `instance`, le jeu fixe la destination à `instance.uidZone`
(ou la maison) avec l'état `instance.ReturnState` : `Exact` pour le duel (même case qu'au départ, `ZoneInstanceBout.cs:5`), puis
`instance.OnLeaveZone()` (`JEU/ZoneInstanceBout.cs:12-33`) : l'adversaire est ressuscité s'il est mort, soigné, remis `Friend`,
`SetEnemy()`, `NoGoal`, et ramené sur sa case d'origine. Les compagnons du joueur ne sont **pas** soignés par ce code (ni remis en vie
par lui : un compagnon mort dans le duel est mort pour de bon, `Die` normal, avec une perte d'affinité de −10 (ou −5) envers le joueur,
`JEU/Chara.cs:5874-5881`).

**Ce qui est perdu à la mort normale, pour comparaison** (`JEU/Chara.cs:5499-5532, 5605-5630`) : après le jour 90 (ou option
« sans protection »), un tiers de l'or au hasard tombe par terre, et chaque attribut principal peut perdre 500 d'expérience
(1 chance sur 5) ; avant le jour 90 rien (« noDeathPenalty »). Les objets plus lourds que la charge sont lâchés. Une tombe est dressée
(`MakeGrave`). `Player.returnInfo` est remis à zéro (`JEU/Chara.cs:5843`). Dans un duel contre un aventurier, rien de cela n'arrive au
joueur, parce que `Die` n'est jamais appelé pour lui (voir plus haut). Le jeu n'applique donc **aucune** perte au joueur battu, sauf la
renommée.

**L'arène du jeu.** `Zone_Arena` (`JEU/Zone_Arena.cs`) : construction interdite (`RestrictBuild`), criminel permis (`AllowCriminal` : un
coup donné n'y est pas un crime), brouillard, `MakeTownProperties`. `Zone_Arena2` (`Zone_Arena2.cs`) : profil aléatoire forêt ou plaine,
nom vide. L'identifiant de zone `instance_arena` est celui des **zones des quêtes à donjon** (`JEU/QuestInstance.cs:5`,
`QuestDefenseGame.cs:16`) : c'est cette carte-là qu'une « arène partagée » réutiliserait. Elle est vide tant qu'un `ZoneEvent` (quête)
n'y met rien ; `Zone.PrespawnRate` vaut 0 par défaut (`JEU/Zone.cs:334`), donc pas de monstres tout seuls (à confirmer en jeu : la classe
exacte de `instance_arena` est dans la table des zones, introuvable ici). Aucun code du jeu décompilé ne crée une zone `arena` : il y a bien
`Package/_Elona/Map/arena.z`, mais je n'ai pas trouvé comment un joueur l'atteint (peut-être débogage seul).

## 1.2 Ce que le mod sait déjà faire et qui peut servir

| Besoin du duel | Ce qui existe | Fichier:ligne | Limite |
|---|---|---|---|
| Une zone d'instance partagée à deux | L'host entre dans la zone d'une quête de l'invité (`TakeQuestZone`) ou l'invité y entre seul avec un bail ; l'autre « suit » : `SendRejoin` / `FollowHost`, comme pour revenir sur la carte de l'host | `MOD/Net/Host/ElinNetHostTravel.cs:430-489` (`TakeQuestZone`), `:221-254` (`InviteToQuestZone`), `MOD/Net/Client/ElinNetClientTravel.cs:739-753` | Tout est **bâti pour `ZoneInstanceRandomQuest`** avec un `uidQuest` : `ElinNetHostTravel.cs:160` et `:527` (`LeavePlayersBehind`, `LeaveAccompaniedZone`), `:223-225` (`InviteToQuestZone`), `:365-376` (`CanRunQuestZoneFor` : seulement subjuguer / récolte / musique), `LeaseZoneBlueprint.Create` (`MOD/Models/ZoneLease/ZoneLeaseRequest.cs:97-107`, `QuestUid`, `GiverUid`). Un duel n'est pas une quête : il faut généraliser ces tests |
| La boîte Oui/Non de 15 secondes à l'autre joueur | `Dialog.YesNo` ouverte avec une échéance, « pas de réponse = non » ; chez l'host `QuestAskSeconds`, chez l'invité `QuestInviteSeconds` ; fermée sans clic = refus | `MOD/Net/Host/ElinNetHostTravel.cs:259, 343-346, 378-407` ; `MOD/Net/Client/ElinNetClientTravel.cs:659-733` ; messages : `QuestFollowDelta` (`MOD/Models/Delta/Quest/QuestFollowDelta.cs`) | Les deux boîtes disent « X fait une quête, venez-vous ? » (clé `emp_quest_follow_ask`). Il faut un texte « X vous défie » et un message propre. Conditions d'ouverture : pas de boîte si un échange est ouvert, pas de quête à donjon, pas d'autre boîte (`:331-335`, `:671-674`) |
| Proposer une action sur l'autre joueur | Le menu de clic sur un autre joueur : le jeu y met « ouvrir son sac » ; le mod le remplace par « Échanger » (`emp_act_trade`) | `MOD/Patches/PlayerTradePatch.cs:13-33` (postfix de `ActPlan._Update`, test `item.tc is Chara { IsRemotePlayer: true }`) | Même crochet pour « Défier » (ajouter une entrée, ne rien remplacer) |
| Mise retenue puis versée | **Pas d'entiercement.** `PlayerTrade` ne met rien de côté : une offre est « une liste de nombres », l'autorité revérifie tout à la confirmation puis déplace d'un seul coup (`Commit`, `Resolve`, `Move`) ; pas de somme qui sort du sac pendant la discussion | `MOD/Helper/PlayerTrade.cs:10-17, 378-407, 409-437, 486-499` | Sert de modèle pour revérifier et payer sans doublon ; **pas** pour retenir. Pour retenir, le modèle est `ShippingAccounts` (`[ElinGameIOProperty("shipping_owed")]`, argent dû, sauvegardé, versé quand le joueur est de retour sur la carte) |
| Argent sûr d'un joueur absent ou hors carte | Compte « dû » par joueur dans la sauvegarde de l'host, versé plus tard par `ShippingPayout` (le client ajoute l'argent lui-même) | `MOD/Net/Host/ElinNetHostShipping.cs:17-37, 188-243` | À réutiliser tel quel pour un remboursement ou un gain destiné à un joueur parti en voyage (sinon le bail de l'invité écrase le portefeuille que l'host vient de modifier : `ZoneLeaseRelease.Chara` « remplace la copie de l'host », `ZoneLeaseRelease.cs:32-33`) |
| Mort d'un invité | Les morts sont tranchées par l'host seul (`CharaDieDelta` rejeté s'il vient d'un client, `MOD/Models/Delta/Chara/CharaDieDelta.cs:25-29`) ; relevé par `CharaReviveDelta` : une part d'or tombe après le jour 90, une tombe est faite | `MOD/Patches/DeltaEvents/Chara/CharaDieEvent.cs:11-47`, `MOD/Models/Delta/Chara/CharaReviveDelta.cs:47-77` ; test `death_suite` | Le point de passage pour « ne pas mourir en duel » existe déjà côté host |
| Dégâts : qui les calcule | **Seul l'host** exécute `Card.DamageHP` ; un client ne l'exécute jamais (sauf pour son propre personnage, il l'envoie à l'host), et reçoit `HpAfter` | `MOD/Patches/DeltaEvents/Card/CardDamageHpEvent.cs:30-50, 53` (`return connection.IsHost`), `CardDamageHpDelta.cs:62-71` | Un seul endroit où « figer les PV » : le crochet de l'host (mais attention au bail : celui qui tient une carte est l'host de cette carte) |
| Case côté host | `GuestBuild` : trois lignes de config + une dans la règle de session + une dans l'onglet + les textes | `MOD/Emp/EmpConfig.cs:178-184, 305`, `MOD/Net/NetSessionRules.cs:88-92`, `MOD/Components/Tabs/TabServerConfiguration.cs:30`, `package/LangMod/CN/SourceLocalization.json:121-122` + `EN/emp_localization.xlsx` | Règle du fork : chaque comportement a sa case |

## 1.3 Aujourd'hui, un joueur peut-il frapper un autre joueur ?

**Oui, sans protection, et si ça tue, c'est une vraie mort.** Faits :
- Le jeu : un coup au corps à corps sur n'importe quel personnage se fait par **Maj + clic** (`altAction`, `JEU/ActPlan.cs:493, 587` :
  `c.IsHostile() || altAction || c.isRestrained` → `ACT.Melee`). Entre membres de la faction du joueur, un coup ne fait que « froncer les
  sourcils » (`JEU/Chara.cs:6778-6781` : `IsPCFaction` des deux côtés → `Say("frown")`, aucune hostilité) : les dégâts, eux, s'appliquent.
- `Chara.IsHostile(c)` (`JEU/Chara.cs:6953-6998`) : un membre de la faction du joueur n'est hostile qu'à un non-membre. Tous les personnages
  de joueur sont de la faction `home` (`JEU/Player.cs:1428` pour le personnage de départ ; `MOD/Helper/CharaImport.cs:196-205` n'y touche pas
  à l'import ; `faction` est un champ du personnage, `JEU/Chara.cs:432-442`) : **aucun joueur n'est hostile à un autre**, ses compagnons non
  plus, et `IsPCParty` vaut vrai pour tous les joueurs chez l'host (`MOD/Patches/Remote/RemotePartyPatch.cs:12-17`).
- Le mod le sait : `RemoteHostilePatch` (`MOD/Patches/Remote/RemoteHostilePatch.cs:8-17`) dit « blows at another player (or a companion of
  its own) stay as they were » : rien n'est fait pour ou contre. Aucun test de joueur contre joueur dans `dev/_tools/` (recherche
  `pvp|duel` : seulement le duel d'autel de la ligne 10).
- L'host exécute le coup de l'invité (rejeu `CharaActPerformDelta`), calcule les dégâts, et si `hp < 0` le personnage meurt vraiment
  (`CharaDieEvent`) : tombe, tiers de l'or après le jour 90 (`CharaReviveDelta.cs:56-77`), perte d'expérience d'attributs chez celui qui
  meurt (`:105-114`). Le jeu ne protège pas non plus l'host d'un coup mortel d'un invité.
- Les sorts et projectiles sur un autre joueur : non vérifié (`ActEffect` filtre-t-il les alliés ? non lu).

Question de conception à poser au conseil, parce qu'elle précède le duel : **faut-il interdire hors duel de se blesser** (ce que ferait un
« mode ami »), ou laisser comme le jeu solo (on peut frapper son allié) ? Le duel ne dépend pas de la réponse.

## 1.4 Options (de la plus petite à la plus complète)

Convention : « taille » = lignes de C# nouvelles (hors textes et tests), estimées d'après les fichiers voisins (`PlayerTrade.cs` 556 lignes,
`BaseRequestDelta.cs` 170, `AgentTaskDelta.cs` ~200).

Brique commune à toutes (écrite une fois, servie par chaque option) :
- **Menu** « Défier » (`emp_act_duel`) sur un autre joueur : un postfix comme `PlayerTradePatch.cs`, **ajoute** l'entrée (~40 lignes).
- **Invitation** : `DuelIntentDelta` (union 833 : défier, accepter, refuser, abandonner) et `DuelStateDelta` (union 834 : phase, mise,
  gagnant, compte à rebours). L'autre joueur voit la boîte Oui/Non de 15 s (copie du code `ElinNetClientTravel.cs:659-733`) ; l'invitation
  tombe si l'un est mort, en échange, en quête à donjon, absent de la carte ou déjà en duel. Les deux deltas ~120 lignes.
- **Autorité** `Helper/PlayerDuel.cs` (~300 lignes) : tient les duels en cours (à l'image de `PlayerTrade._sessions`), vérifie les conditions
  au début et à la fin, annonce l'état aux deux, fait la fin.
- **Aucune perte** : crochet unique sur `Card.DamageHP` (préfixe de l'host, avant `CardDamageHpEvent`), `dmg = min(dmg, hp − 1)` pour les
  deux duellistes (et leurs compagnons, option 4). Avantage sur un crochet de `Chara.Die` : `Card.DamageHP` après `Die` continue à compter
  des morts (`JEU/Card.cs:4821-4850` : `stats.kills++`, `codex.AddKill`, contribution de la guilde des guerriers, **prime** `Guild.Fighter.HasBounty`)
  même si `Die` a été refusé par un préfixe : un `Die` coupé donnerait ces gains au vainqueur. Avec le plafond à 1 PV, `hp < 0` n'arrive jamais et
  rien de tout cela n'est atteint. En plus, `CharaDieEvent.OnCharaDie` (côté host) refuse `Die` d'un duelliste en duel (ceinture et bretelles).
  Fin du duel quand un duelliste est à son plancher (≤ 1 PV après le coup) : le gagnant est l'autre, le perdant est soigné (`HealAll`, comme le jeu).
- **Case côté host** « Players may duel each other » (`Duels`, coché par défaut comme `GuestBuild`), règle de session clé 13, onglet « own »
  de `TabServerConfiguration`, textes EN/JP (xlsx) et CN (json). ~30 lignes + ~10 clés de texte × 3 langues.
- **Aucune sauvegarde** : le duel vit en mémoire de l'host (comme `_accompanied`, `ElinNetHostTravel.cs:262-270`), sauf la mise (option 3).

### Option 1 — Duel sur place (même carte, pas de téléportation)

- **Ce que ça fait.** Défi par le menu, boîte Oui/Non ; compte à rebours de 3 s annoncé aux deux ; les deux se frappent (Maj + clic, sorts, tirs :
  tout ce que le jeu laisse viser un allié) ; PV plafonnés à 1 ; le premier à ce plancher perd. Fin : message aux deux (« X a gagné »), PV, mana et
  endurance du perdant remis à plein, conditions guéries ; le gagnant n'est pas soigné (comme le jeu) ou l'est (choix). Rien d'autre ne bouge.
- **Fichiers.** La brique commune seulement : `Helper/PlayerDuel.cs`, `Models/Delta/Misc/DuelDeltas.cs`, `Patches/PlayerDuelPatch.cs` (menu +
  crochet de dégâts) + `EmpConfig.cs`, `NetSessionRules.cs`, `TabServerConfiguration.cs`, textes. **~550 lignes, 3 fichiers neufs, 3 retouchés.**
- **Ce que voit chaque joueur.** Les deux sont à l'écran de l'autre dans la même scène ; un bandeau (message du jeu) « Duel : A contre B » ; à la
  fin, le message de victoire. Un troisième joueur présent voit tout et peut se faire toucher par un sort de zone (rien ne le protège).
- **Risques.** (1) Consommables : potions, flèches, parchemins, charges, mana utilisés pendant le duel sont dépensés pour de bon (le duel ne les
  rend pas) : « aucune perte » = pas de mort, pas de pénalité, pas d'objet lâché ; c'est à dire clairement au conseil. (2) Sorts de zone et
  invocations : un coup perdu peut toucher un compagnon ou un habitant (un habitant touché devient hostile : `JEU/Chara.cs:6788-6816` avec
  `RemoteHostilePatch` ; un garde peut s'en mêler, crime). (3) Les compagnons ne se battent pas (pas hostiles) mais peuvent être tués par erreur :
  plafonner aussi leurs PV (option 4 le fait proprement). (4) Un joueur qui part, meurt d'autre chose (faim, piège, condition) ou se
  déconnecte : le duel s'arrête, **sans gagnant** (sauf abandon explicite). (5) Un joueur sur une carte différente (voyage indépendant) n'est
  pas dans la même scène : refuser (même condition que l'échange : `Present`, `Reach`).
- **Mise.** Possible (voir 1.5), c'est le seul endroit où l'argent bouge.
- **Test.** Voir D1 à D6.
- **Effet sur la sauvegarde.** Aucun (sans mise).

### Option 2 — Arène partagée (autre carte, comme le duel contre un aventurier)

- **Ce que ça fait.** Défi, Oui/Non ; si oui, l'host crée une zone `instance_arena` vide (`SpatialGen.CreateInstance`), les deux y sont emmenés
  (cases de départ éloignées), compte à rebours, mêmes règles qu'à l'option 1 ; à la fin, retour de chaque joueur **à sa case de départ** dans la
  zone d'origine, la zone est détruite. À deux joueurs, un des duellistes est toujours l'host : la zone est simulée par lui et l'invité y arrive
  « comme sur la carte de l'host » (voie déjà testée par les quêtes à donjon à deux : `together_suite` T1 à T13).
- **Fichiers en plus de la brique commune.** `Net/Host/ElinNetHostDuel.cs` (créer la zone, y entrer, annoncer, détruire ; ~150 lignes) ;
  retouches de `ElinNetHostTravel.cs` (généraliser les 4 tests sur `ZoneInstanceRandomQuest` cités en 1.2 : « un duel est une instance dont
  tout le monde sort avec celui qui part » ; ~40 lignes), `ElinNetClientTravel.cs` (la boîte qui dit « défie » au lieu de « quête » ; ~60
  lignes), `QuestFollowDelta.cs` ou un delta neuf (~30 lignes), positions de départ (~40 lignes). **~900 à 1000 lignes en tout**, 5 fichiers neufs, 6
  retouchés. Pas d'`instance` propre au duel : on pose la classe de base `ZoneInstance` du jeu, jamais une classe du mod, pour qu'une sauvegarde
  de l'host contenant la zone se recharge sans le mod (le mod le fait déjà : `CreateQuestZone`, `ElinNetHostTravel.cs:1431`, `zone.instance = new()`).
- **Ce que voit chaque joueur.** Écran de chargement (la carte change pour les deux ; l'invité recharge le monde comme au retour de l'host :
  1 à 2 s mesurées sur le banc, **jamais chronométré à deux PC**, `HANDOFF.md` point 3), musique de combat, une carte vide. Au retour, chacun là
  où il était. Un troisième joueur reste sur la carte d'origine (il en devient le gardien tant que l'host est parti : `LeavePlayersBehind`,
  `ElinNetHostTravel.cs:152-215`) et reçoit la boîte « suivre ? » existante si on étend `InviteToQuestZone` (spectateur : option 4).
- **Risques.** (1) Retour : le jeu pose l'arrivée au retour sur `instance.x/z` ; le mod, lui, fait arriver le joueur « à côté de l'host »
  (`PLAN_quetes_donjon.md:82`, fait connu de la phase 1) : sans réglage, les deux reviennent côte à côte, pas chacun à sa case. (2) Les deux
  arrivent l'un contre l'autre : cases de départ à fixer (l'arrivée du jeu est « près de l'host », `Zone.cs:1749`). (3) Un joueur qui se
  déconnecte pendant le duel : la zone de l'host tient, l'autre revient seul (voie des quêtes à donjon : `ReleaseLeaseOnDisconnect`). (4) Duel
  d'**invité contre invité** (3 joueurs) : l'un des deux doit tenir la zone par un bail, l'autre l'y suit « en invité de zone » ; ce chemin
  existe (`GrantGuestLease`, `ElinNetHostTravel.cs:967`) mais **n'a jamais été essayé à trois** (`PLAN_quetes_donjon_a_deux.md`, « à trois
  joueurs : pas essayé ») : annoncer « duel entre invités : non testé » ou le refuser à trois au début. (5) `ZonePreEnterBout` du jeu : si un
  invité parle à un aventurier (voir 1.6), le jeu fabrique des renforts d'après `EClass.pc.party.members.Count − 1` : le groupe de l'host
  contient tous les joueurs (`ElinNetHostPlayerManager.cs:50` : le joueur est retiré du groupe de l'host quand il part, donc il y est ; `RemotePartyPatch`) ; non vérifié si ce nombre compte des
  invités restés sur la carte.
- **Mise.** Même mécanisme qu'à l'option 1 (la mise est prise avant le départ, rendue ou versée à la fin).
- **Test.** D1 à D8.
- **Effet sur la sauvegarde.** La zone d'instance est dans la liste des zones de l'host tant qu'elle existe (un jour d'expiration) ; la détruire
  proprement à la fin et au chargement d'une sauvegarde faite pendant le duel (`LeasedZonePatch`, `Zone.CanDestroy` : une instance non louée est
  détruite à la sauvegarde, `JEU/Zone.cs:1957-1966`). Même risque que les zones de quête : si le duel est en cours quand l'host quitte, la zone
  est une zone sans propriétaire : prévoir la destruction au chargement.

### Option 3 — Option 2 + pari en or retenu chez l'host

Voir 1.5 pour le détail. **+~250 lignes** (`Helper/PlayerDuel.cs` : pari ; une propriété sauvegardée ; fenêtre de saisie ; textes).
Risques : perte ou doublon de l'or (voir 1.5).

### Option 4 — Option 3 + compagnons et spectateurs

- **Compagnons.** Ils viennent déjà avec leur joueur (`CompanionHelper`, `TakeCompanionsAlong`). Dans la carte du duel, ils ne se battent pas (pas
  hostiles entre eux, voir 1.3) : « avec compagnons » veut donc dire « qui ne meurent pas ». Les PV de chaque compagnon des deux duellistes
  sont plafonnés comme ceux de leur maître. Pour qu'ils **combattent**, il faudrait leur donner l'adversaire comme ennemi (`SetEnemy`)
  et **surcharger `Chara.IsHostile`** pour la paire (adversaire, compagnons) pendant le duel : l'astuce du jeu (passer l'adversaire en
  `Hostility.Enemy`, comme `ZonePreEnterBout`) est **fausse ici** : `CharaStateSnapshot` diffuse `hostility` (`MOD/Models/WorldState/
  CharaStateSnapshot.cs:33, 52, 102`), et un joueur à `Enemy` serait hostile aussi à ses propres compagnons
  (`IsHostile`, `JEU/Chara.cs:6953-6962`) et à tous les autres joueurs. À éviter.
- **Spectateurs (3 joueurs).** Le troisième joueur est invité à suivre (étendre `InviteToQuestZone`, `ElinNetHostTravel.cs:221-254`, qui ne
  traite que les quêtes) ; il y arrive sans pouvoir être touché (prévoir un plafond de PV pour lui aussi, ou le tenir hors de portée : invulnérable
  `ConInvulnerable` pendant le duel).
- **+~300 lignes.** Le plus risqué : chemin à trois joueurs jamais testé, plusieurs `_settled` / `_departed` à tenir.

## 1.5 Le pari

Règles à fixer par le conseil : un seul montant pour les deux, l'or seulement (pas d'objets : `PlayerTrade.Refuse` en refuse déjà beaucoup,
`MOD/Helper/PlayerTrade.cs:440-475`), plafond (par exemple ce qui reste dans le sac de celui qui a le moins), avec un menu de montants simple
(0 / 100 / 1 000 / tout).

Mécanisme proposé (le seul qui ne perd ni ne double) :
1. Au début, l'autorité **revérifie** que les deux ont la somme (`GetCurrency() ≥ mise`), exactement comme `PlayerTrade.Resolve`
   (`PlayerTrade.cs:409-437`). Sinon, pas de duel.
2. Elle **retire** la mise de chacun (`chara.ModCurrency(-mise)` sous `ElinDelta.Simulate()`, comme `Move`, `PlayerTrade.cs:486-499`) et la
   **note** dans une propriété sauvegardée `[ElinGameIOProperty("duel_stakes")] Dictionary<int, long[]>` (uid du joueur → somme retenue +
   identifiant du duel), à l'image de `ShippingAccounts` (`ElinNetHostShipping.cs:17-37`). Écrire la note et retirer l'or dans la même image :
   une sauvegarde automatique ne peut pas tomber entre les deux (même fil, `Simulate` dans une image).
3. À la fin : **supprimer** d'abord les deux notes (la première opération), **puis** verser `2 × mise` au gagnant. Un second appel de la fin
   ne trouve plus rien à verser (pas de doublon). Annulé, sans gagnant, déconnexion, carte quittée : rendre à chacun sa mise de la même façon.
4. Au chargement d'une sauvegarde qui contient des notes sans duel en cours (l'host a quitté pendant le duel) : rendre à chacun ; si le joueur
   n'est pas connecté, passer par le compte « dû » de l'expédition (`GetShippingAccount(uid)[AccountOwedMoney] += mise`, versé à son retour par
   `PayShipping`, `ElinNetHostShipping.cs:188-243`). C'est aussi le seul chemin sûr si le gagnant est un joueur qui simule sa propre carte
   (bail) : écrire dans sa bourse depuis l'host serait écrasé par son retour (`ZoneLeaseRelease.Chara`).
5. Pendant le duel, l'or retenu n'est dans aucun sac : un joueur ne peut ni le dépenser ni le donner (et l'échange lui est refusé, voir les
   conditions d'invitation).

Pourquoi pas « sans retenue, on revérifie à la fin » (le modèle exact de `PlayerTrade`) : c'est sûr pour un échange de quelques secondes ;
pour un combat de plusieurs minutes, un joueur peut dépenser l'or entre-temps (boutique, don, jeu) et la mise est alors impayable (le
perdant s'en tire gratuitement). La retenue est donc nécessaire, et c'est elle qui fait toute la difficulté (une note sauvegardée, un
remboursement au chargement).

## 1.6 Cas à ne pas oublier : un invité contre un aventurier, aujourd'hui

`PLAN_chasse_differences_2.md:70` (« Pas parcouru ») : `DramaCustomSequence` « Duel » tourne chez le joueur qui parle. Pour un invité sur la
carte de l'host : `SpatialGen.CreateInstance("field", new ZoneInstanceBout { … })` s'exécute dans **son** jeu ; `SpatialGenEvent` annonce la zone
comme créée localement (`MOD/Patches/DeltaEvents/Zone/SpatialGenEvent.cs:36-45`), puis son `MoveZone` demande un bail avec
`Instance = zone.IsInstance` (`ZoneLeaseRequest.cs:97-107`) : l'host fabrique une zone vide (`CreateQuestZone`, `zone.instance = new()`),
l'invité la joue **seul**, avec sa copie de l'aventurier déplacé dans **sa** copie du monde (`c.SetGlobal()`, `ZonePreEnterBout`,
`ZoneInstanceBout.OnLeaveZone`). Au retour, la copie de l'aventurier (un personnage **global**) est dans le jeu de l'invité, pas dans celui de
l'host : doublon ou perte possibles ; l'événement `ZonePreEnterBoutWin` est posé sur la zone d'origine **de l'invité**. Rien ne le prouve :
`grep Bout` dans `MOD/` ne trouve rien. À jouer avant de bâtir sur ce chemin (test D9). Pour le duel entre joueurs on n'utilise pas ce chemin.

## 1.7 Brouillons de tests (`dev/_tools/duel_suite.py`, nouvelle suite ; non exécutés, non compilés)

Même forme que `hunt2_suite.py` (host `27551`, invité `27552`, `ev`, `check`, `eventually`, `both`, `chara`, `stand`, `free_next_to`, `click_yes`,
`dialog_open`, `use_menu`). **Conditions de mise en place indispensables** : `EClass.player.stats.days = 100` sur les deux jeux avant les tests de
mort (avant le jour 90 le jeu n'applique aucune pénalité : sans ça, le test ne verrait jamais la perte qu'il doit empêcher,
`JEU/Chara.cs:5526`) ; 1 000 pièces d'or dans chaque sac ; `clear_conditions` ; `close_layers` avant chaque cas. Gestes réels : défi par le menu
(`use_menu` avec `pick='i.act is DynamicAct d && d.id == "emp_act_duel"'`), réponse par `click_yes`, coups par Maj + clic (`ActPlan` avec
`input = ActInput.AllAction`, `JEU/ActPlan.cs:493` : à ajouter comme paramètre de `use_menu`), pas par `Die` ni `ModCurrency` directs.

```python
# --- aides ---
def hp(port, uid):
    return int(ev(port, f'{chara(port, uid)}.hp.ToString()'))

def gold(port, uid):
    return int(ev(port, f'{chara(port, uid)}.GetCurrency().ToString()'))

def graves(port):
    return int(ev(port, 'EClass._map.things.Count(t => t.trait is TraitGrave).ToString()'))

def kills(port):
    return int(ev(port, 'EClass.player.stats.kills.ToString()'))

def start_duel(ctx, challenger, bet=0):
    """Defi par le menu du jeu, l'autre repond Oui dans la vraie boite ; renvoie True si les deux voient le duel ouvert"""
    cp, cuid = ctx[challenger]; op, ouid = ctx["h" if challenger == "a" else "a"]
    stand(cp, cuid, *(int(v) for v in free_next_to(H, ouid, 2).split(",")))
    pos = ev(cp, f'var c = {chara(cp, ouid)}; return c.pos.x + "," + c.pos.z;').split(",")
    r = use_menu(cp, (int(pos[0]), int(pos[1])), 'i.act is DynamicAct d && d.id == "emp_act_duel"')
    if bet:
        ev(cp, f'ElinTogether.Helper.PlayerDuel.SetBet({bet}); "ok"')      # saisie du montant : raccourci du banc
    if not check(f"{challenger} defie par le menu ({r}) : l'autre voit la boite", eventually(lambda: dialog_open(op), timeout=10)):
        return False
    click_yes(op)
    return eventually(lambda: all(ev(p, 'ElinTogether.Helper.PlayerDuel.Describe()').startswith("Open") for p in (H, A)), timeout=15)
```

- **D1 le menu et la boîte.** Pour chaque joueur : le menu de l'autre joueur offre « Défier » (liste `p.list` de `ActPlan._Update`, comme
  `use_menu` l'affiche) ; sans la case host (`Duels` décochée) l'entrée est absente ; la boîte arrive chez l'autre, **Non** la ferme et rien ne
  change (pas de compte à rebours, aucun delta), **pas de réponse en 15 s** : même chose, le défieur reçoit « pas de réponse ».
- **D2 la mort ne tue pas (option 1).** Après `start_duel`, régler les PV du défié à 1 chez l'host, le défieur le frappe (Maj + clic) : on vérifie
  chez **les deux jeux** `hp > 0`, `isDead == False`, le duel est « terminé » avec le défieur gagnant ; **aucun** `CharaDieDelta` (compter dans le
  journal de l'host avant/après), `graves(H)` inchangé, l'or des deux sacs et au sol inchangé (`gold(...)` et pièces par terre à moins de 3 cases),
  `kills(H)` inchangé (pas de gain de mort), pas de prime, pas de perte d'expérience (`elements.GetOrCreate(...).vExp` des attributs principaux
  identiques). Les deux sens (l'invité frappe l'host, l'host frappe l'invité). **Rouge d'abord** : sans le crochet, l'invité de PV 1 meurt
  (tombe, un tiers de l'or).
- **D3 la fin remet à neuf.** Perdant : PV, mana, endurance pleins, conditions guéries (`conditions.Count == 0`) ; une potion de poison bue
  avant le duel est guérie. Les objets consommés pendant le duel ne reviennent pas (une potion bue reste bue : le test le **documente**, ne
  l'exige pas).
- **D4 les compagnons ne meurent pas.** Un compagnon (`tame(ctx, "cat", key)`) de chaque duelliste ; le duelliste frappe le chat de l'autre
  (à 1 PV) : le chat survit, aucun `CharaDieDelta` ; le karma de personne ne baisse.
- **D5 abandon, départ, déconnexion.** L'un des deux part (voyage seul, `Teleport` sur une autre carte, `Leave`) : le duel finit **sans gagnant**,
  personne ne gagne ni ne perd, la mise (D7) est rendue. L'un des deux meurt d'autre chose (poison mis à 1 PV puis tick) : le duel finit sans
  gagnant et la mort est une vraie mort (le duel ne couvre pas cela).
- **D6 pas de double duel.** Pendant un duel, un troisième défi ou un échange sont refusés ; un défi pendant un échange ouvert est refusé.
- **D7 le pari, de bout en bout (rouge puis vert).** Mise 200, deux fois 1 000 : après le début, chacun a 800 et la propriété `duel_stakes` a deux
  notes (lire par le pont) ; le dépôt du jeu `ElinNetHost.SavedStakes` (nom à fixer) ; à la fin, gagnant 1 200, perdant 800, notes vidées ;
  **somme conservée à chaque instant** (sacs + notes = 2 000, vérifié avant, pendant, après). Appeler la fin **deux fois** : rien de plus n'est
  versé. Mise supérieure au sac d'un des deux : refus avant le début, rien retiré.
- **D8 le pari interrompu.** (a) Déconnexion de l'invité en plein duel : l'host rend les deux mises, la somme est conservée, la note du perdant
  absent passe par le compte « dû » (`ShippingAccounts`) et arrive à son retour. (b) Sauvegarde de l'host pendant le duel, rechargement : les
  notes sont rendues, pas doublées (une sauvegarde qui contient les notes **et** les sacs sans la mise doit être impossible, le test
  compare). (c) La case `Duels` décochée en cours de duel : le duel en cours finit normalement.
- **D9 (option 2) carte d'arène.** Après `start_duel`, les deux sont dans la même zone d'instance (`zone_uid` identique, `_zone.IsInstance`),
  chacun sur sa case de départ, distance ≥ 10 ; après la fin, retour à la zone d'origine, **zone détruite** (`game.spatials.Find(uid) == null`
  après le rechargement), les compagnons suivent dans les deux sens, pas de monstre (`_map.charas` hostiles = 0 après 60 s), aucun objet dupliqué
  (compter l'inventaire avant / après), l'or du pari (D7).
- **D10 un invité contre un aventurier, aujourd'hui** (état des lieux, avant tout code) : l'invité parle à un aventurier (`talk`, `pick("Duel")`
  dans `hunt_suite.py`), répond Oui, joue (le test tue l'adversaire d'un coup d'`ev` : raccourci à dire), sort : compter les exemplaires de
  l'aventurier dans les deux jeux (`globalCharas.Find(uid)`, `currentZone`), la renommée, le jeu de l'host voit-il l'événement
  `ZonePreEnterBoutWin` ? Résultat attendu : à noter, pas à exiger.

## 1.8 Non vérifié (Partie 1)

- Si les sorts, projectiles et sorts de zone tirés sur un autre joueur le touchent (`ActEffect` filtre-t-il les alliés ?) : non lu.
- La classe exacte et le profil de `instance_arena` (table `SourceZone`, absente de `Data/Source/`) ; si elle a des monstres tout seuls.
- Comment un joueur atteint la carte `arena.z` du jeu (si seulement par débogage).
- Si l'équipement s'abîme en combat (il n'y a pas d'usure vue dans `AttackProcess`, non relu) : un duel pourrait coûter de la durabilité.
- Le temps de rechargement de l'invité quand l'host change de carte (jamais chronométré à deux PC).
- Ce que fait le jeu quand `hp == 1` et que le coup suivant est un effet qui ne passe pas par `DamageHP` (poison de faim, noyade,
  `ConDeath`) : ces morts ne sont pas couvertes par le plafond.
- Le comportement à trois joueurs (invité contre invité, spectateur) : jamais essayé par le mod.
- Si `Dialog.YesNo` peut être ouvert à un joueur qui a déjà une boîte du jeu ouverte (la boîte du tutoriel retient le temps de ce joueur, `guest_suite.awake`).
- Si `ElinGameIOProperty` (dans `ElinModdingKit`, DLL non lue) ignore une clé inconnue quand le mod est retiré (utilisé déjà par six propriétés).
- Le dialogue du jeu `bout1` / `bout2` : texte non lu.

## 1.9 Questions pour le conseil (Partie 1)

1. **Quelle option ?** Le minimum qui répond au mot « autre carte » est l'option 2 ; l'option 1 est un tiers de sa taille et aucun risque de
   carte. Faire 1 d'abord, puis 2 sur la même brique ?
2. **Duel hors duel** : empêcher de se blesser entre joueurs (hors duel), ou laisser comme le jeu solo ?
3. **« Aucune perte »** : les consommables utilisés (potions, flèches, mana, charges) restent perdus ; est-ce acceptable, ou le duel doit-il
   interdire les consommables (impossible sans surcharger tout le jeu) ou rendre les objets (copie de l'inventaire au début, restauration à la
   fin, lourd) ?
4. **Le gagnant est-il soigné** à la fin ? (Le jeu ne soigne que le perdant.)
5. **Pari** : or seulement, montant unique, plafond ? Retenue avec note sauvegardée (recommandé) ou sans retenue (plus simple, tricherie possible) ?
6. **Duel entre deux invités** (3 joueurs) : l'annoncer « non testé », le refuser, ou imposer l'host comme tiers ?
7. **Compagnons** : seulement protégés, ou aussi combattants (exige une surcharge de `Chara.IsHostile`, risque d'effets de bord) ?
8. **Spectateurs** : oui / non / plus tard.
9. Un duel contre un **aventurier** par un invité : le refuser avec un message en attendant d'avoir joué D10 ?
10. Case host : une case « duels » seule, ou aussi une case « paris » (plafond) ?

---

# PARTIE 2 — Gérer la base de l'host en tant qu'invité

Mots de l'utilisateur : un invité doit pouvoir gérer la base de l'host, « peut-être un système de membres pour chaque base ».

## 2.1 À qui « appartient » une base dans le jeu

- **Une seule faction de joueur.** Le personnage de départ est mis dans la faction `home` (`JEU/Player.cs:1428`) ; `FactionManager.Home =
  Find("home")` (`JEU/FactionManager.cs:45`). `Zone.IsPCFaction => mainFaction == EClass.pc.faction` (`JEU/Zone.cs:480`) : **toute zone
  revendiquée** appartient à `home`, quelle que soit la personne qui a lu l'acte de propriété. `Spatial.mainFaction` est un champ texte
  (`idMainFaction`, `JEU/Spatial.cs:22, 441-452`).
- **Une branche par zone.** `FactionBranch` (`JEU/FactionBranch.cs`) est un champ de la zone (`Zone.branch`, `JEU/Zone.cs:34`). `EClass.Branch =
  game.activeZone.branch` (`JEU/EClass.cs:23`) : la branche de la **zone où l'on est** ; `EClass.Home` est la faction. La faction fait ses
  passages de jour et de mois sur toutes ses branches (`JEU/FACTION.cs:195-570`, boucles `foreach (FactionBranch child in GetChildren())`) :
  le jeu gère donc déjà **plusieurs bases d'un même joueur**.
- **Les habitants d'une base** (`branch.members`) sont les personnages dont `homeZone == zone && faction == pc.faction`
  (`JEU/FactionBranch.cs:266-273`, `SetOwner`). `Chara.homeZone` est un champ **du personnage** : celui du joueur est sa maison
  (`EClass.pc.homeZone`, `homeBranch`, `JEU/Chara.cs:1115`) ; il est utilisé sans test nul à de nombreux endroits (`JEU/HotbarManager.cs:139-167`,
  `JEU/GameDate.cs:365, 412, 541`, `JEU/ContentHomeReport.cs:44`, `JEU/FACTION.cs:400`) et pour réclamer une zone de champ
  (`JEU/Zone_Field.cs:61` : `isClaimable => EClass.pc.homeBranch != null` ; `Zone_StartSite` : toujours ; `Zone_Vernis` : après la quête).
- **Ce que la faction contient et qui n'est pas par base** : `EClass.Home.listReserve` (réserve de résidents, `JEU/BaseListPeople.cs:454-463`),
  `charaElements`, relations. Ce qui est par base : recherche, ressources, politiques, bonheur, effectif, `uidMaid` (la servante,
  `JEU/FactionBranch.cs:49`), nom, lit, notes.
- **Réclamer, abandonner** : `TraitDeed.OnRead` (`JEU/TraitDeed.cs:7-31`) : boîte « réclamer ? » dont le « oui » appelle `Zone.ClaimZone()`
  (`JEU/Zone.cs:1887-1904` : `SetMainFaction(pc.faction)`, nouvelle branche, `dateExpire = 0`, `Register()`), consomme l'acte
  (`owner.ModNum(-1)`), et, dans la zone de départ, avance la quête de maison. Abandonner : `TraitCoreZone` (`JEU/TraitCoreZone.cs:86-102`) :
  boîte « abandonner ? », un délai de 30 jours depuis la prise (`GetInt(2) + 43200`), puis `owner.Die()` (la pierre de foyer disparaît),
  un acte de propriété rendu (`DropReward`), `AbandonZone()` (`JEU/Zone.cs:1941-1955` : les résidents passent à la base maison ou à celle de
  départ, `SetMainFaction(null)`).
- **Les autres actes de la pierre de foyer** (`TraitCoreZone.cs:35-85`), tous des lambdas locales : réserve (`actCallReserve`), nom
  (`actNameZone`, déjà couvert par `NameDelta`), point de renaissance (`actSetSpawn`, champ de `Player`), **maison** (`actSetHome`, champ du
  personnage), téléversement de carte, abandon.

## 2.2 Comment le mod traite la faction et l'appartenance aujourd'hui

- **Aucun traitement de la faction ni de la propriété** : `grep` de `mainFaction`, `SetFaction`, `ClaimZone`, `isClaimable`, `homeZone` dans
  `MOD/` ne trouve que : `NameDelta.cs:44` (`IsPCFaction: true` pour savoir si un nom de zone est celui d'une base), `CharaImport.cs:196-205`
  (`homeZone = null` à l'import d'un personnage), `PartyMemberDelta.cs:54`, `ElinNetHostCompanions.cs:109-154`, `ElinNetHostShipping.cs:107, 226`
  (`pc.homeZone` de l'**host**). Un personnage de joueur garde donc la faction `home` ; pour un invité, **`IsPCFaction` des zones de l'host
  est vrai** (si sa faction est bien `home` : non vérifié sur un invité qui n'a pas importé de personnage).
- **L'invité est un membre du groupe de l'host** chez l'host (`RemotePartyPatch.cs:12-17` : `IsPCParty` = « est dans un groupe »), mais pas
  un membre d'une branche : `branch.members` ne compte que les résidents (`homeZone` = la base).
- **L'host est « le joueur » de toutes les boucles de la faction** : mois, impôts, expédition, `GameDate.cs:325, 365, 412` lisent
  `EClass.pc.homeZone` de la machine qui calcule (le gardien du monde, l'host : `WorldKeeper.cs:21-31`). La base « maison » de l'host est
  donc celle qui reçoit les journaux, et la seule dont la zone de départ est `pc.homeZone`.
- **La propriété d'un invité n'est écrite nulle part.** `ElinGameIOProperty` existe (six propriétés, toutes dans l'host : `remote_chara`,
  `remote_chara_roster`, `personal_quests`, `player_standing`, `shipping_owed`, `lease_range_floor` ; `MOD/Net/Host/ElinNetHost*.cs`), l'attribut est
  dans `ElinModdingKit` (non lu).

## 2.3 Ce qu'un invité peut et ne peut pas faire dans la base de l'host (état au 2026-10-05, 17h)

Légende : **oui** = fait avec test ; **message** = refusé avec « la base se règle chez l'host » (`emp_base_host_only`) ; **local** = le geste
marche sur son écran seulement, l'autre ne le voit pas ; **?** = non vérifié. Sources : `HANDOFF.md`, `PLAN_egalite_invites.md` (M14),
`PLAN_chasse_differences_2.md` (lignes 1, 3, 4, 7, 14, 24, état 16h30), `PLAN_construction_invite.md`, code.

| Geste | État | Où |
|---|---|---|
| Recherche (plans) | **oui** (demande vérifiée par l'host, l'état revient à tous) | `BaseRequestDelta.cs:104-121`, `RemoteBasePaidPatch.cs:86-97`, `base_suite` B1 |
| Compétences du foyer (platine) | **oui** | `BaseRequestDelta.cs:123-142`, `RemoteBasePaidPatch.cs:145-192` |
| Plans du marchand, amélioration du foyer | **message** (étapes de dialogue absentes du jeu installé) | `RemoteBasePaidPatch.cs:127-137` |
| Politiques | **oui** (deux sens) | `PolicyStateDelta.cs`, `setting_suite` S4 |
| Lit : qui, type | **oui** | `CardSettingDelta.cs` (`Bed`) |
| Note, étiquette de vente, téléporteur | **oui** | `CardSettingDelta.cs` |
| Nom de la zone, de la faction | **oui** (faction non jouée) | `NameDelta.cs`, `setting_suite` S5, S6 |
| Construire, miner, creuser, couper (menu) | **oui**, case host `GuestBuild` | `AgentTaskDelta.cs`, `RemoteBuildModePatch.cs`, `build2_suite` 28/28 |
| Poser un objet tenu, déplacer un meuble installé | **oui** | `CharaBuildDelta`, `ZoneAddCardEvent` |
| Zones de base (stockage…), terrain (hauteurs), plans, mode toit (Alt) | **message** | `RemoteBuildModePatch.cs:34-44` |
| Marquer « à démonter » | **local** | `Card.cs:8296` (`SetDeconstruct`), aucun patch |
| Réglage de coffre : priorité, pourri, filtres, distribution | **local** (seul « partagé / personnel » part) | `InvSaveDataDelta.cs` ; ligne 7 ; `PLAN_lignes_7_a_11.md` : diff proposé |
| Servante (`uidMaid`) | **local** | `BaseListPeople.cs:413-423`, `DramaCustomSequence.cs:444-448` (dialogue), `FactionBranch.cs:49` ; **reporté** au conseil 4 |
| Type de résident (résident / bétail), réserve, rappel de réserve | **local** | `BaseListPeople.cs:432-463`, `ListPeopleCallReserve.cs:47`, `FACTION.cs:338-362` ; **reporté** |
| Recruter par le tableau des quêtes | via `StoryOutcomeDelta.cs:56-59, 102` (l'host exécute) : probablement **oui** ; `recruit_suite` 45/45 couvre les compagnons | `LayerQuestBoard.cs:128-140` ; **?** pour un invité qui recrute un résident |
| Renvoyer un résident | **local** | `DramaCustomSequence.cs:499` (`BanishMember`) ; **reporté** (« bannir ») |
| Tableau de bord (`LayerHome`, `LayerPeople`, `TraitHomeBoard`, `ContentHomeRanking`, rapport) | lecture **oui**, mais chaque action de ces fenêtres est une lambda locale (liste ci-dessus) | `TraitHomeBoard.cs:5-15` |
| Impôts (coffre), salaires | dépôt payé par le joueur **oui** (`InvOwnerOnProcessDelta.cs:179-195`) ; le mois et les salaires sont tenus par l'host (`WorldKeeper`) | `TraitTaxChest.cs` |
| Point de renaissance, maison (`actSetSpawn`, `actSetHome`) | **local** (champs de `Player` / du personnage) ; effet sur l'autre jeu non vérifié | `TraitCoreZone.cs:51-70` |
| Réclamer un terrain (acte de propriété) | **local, non synchronisé** : l'host saute `OnRead` pour un joueur distant (`TraitOnReadPatch.cs:20`) ; chez l'invité le jeu appelle `ClaimZone` sur **sa** copie de la zone, que la prochaine entrée dans la zone écrase probablement | `TraitDeed.cs:7-31` |
| Abandonner la base (pierre de foyer) | **local**, irréversible chez lui (ligne 24 du plan) : « refuser pour un invité » proposé | `TraitCoreZone.cs:86-102` |
| Réglages par menu d'objet (figurine, plaque de pièce, tableau de carte, tableau de maison, ascenseur…) | **local** (ligne 14) | `CardSettingDelta.cs` : seulement note, étiquette, lit, téléporteur |

## 2.4 Un invité peut-il avoir SA base à lui dans le monde de l'host, aujourd'hui ?

**Non, pas comme fonction.** Lecture :
1. Pour revendiquer, il faut lire un acte de propriété sur une zone `isClaimable` (`JEU/TraitDeed.cs:9`). Pour un champ, il faut que `pc.homeBranch`
   existe (`JEU/Zone_Field.cs:61`) : un invité qui vient de créer son personnage a `homeZone` à zéro d'après `CharaImport.Adopt` (importé), et
   rien dans `MOD/` ne la pose pour un personnage neuf (non vérifié : valeur de `EClass.pc.homeZone` d'un invité ; le banc la lit par `eval`).
2. La lecture de l'acte par un invité est **sautée chez l'host** (`MOD/Patches/Trait/TraitOnReadPatch.cs:20`) et exécutée chez lui seulement :
   `ClaimZone()` modifie sa copie de la zone (`idMainFaction`, `branch`), qui n'est **pas** dans ce que le mod échange : le bail rend les
   fichiers de carte, `_ints` de la zone, le personnage et ses compagnons (`MOD/Models/ZoneLease/ZoneLeaseRelease.cs:11-70`,
   `ZoneLeaseState.cs:40-60`) ; ni `idMainFaction`, ni l'objet `branch`. `ClaimZone` écrit une date dans `_ints[2]` (`SetInt(2, …)`,
   `JEU/Zone.cs:1899`) qui, elle, **voyagerait** : demi-état possible (une date de prise sans zone prise). **Non vérifié, à jouer.**
3. Si l'host revendique, tout va bien pour lui : il est « le joueur ». Les invités voient une zone `IsPCFaction` (si leur faction est `home`),
   et la fenêtre de la base s'ouvre (`TraitHomeBoard.cs:7`).
4. Même corrigé, ce que le jeu fait avec **plusieurs** bases dépend du « joueur » qui calcule : journaux, expédition, mois, rapport de la base
   sont lus sur `EClass.pc.homeZone` / `uidLastShippedZone` du jeu qui les calcule (voir 2.2).

## 2.5 Options

Le jeu n'a pas de notion de propriétaire : tout ce que ces options ajoutent est un registre du mod.

### (a) Pas de membres : tous les joueurs ont tous les droits sur toutes les bases (le plus simple, « zéro différence ») + case host

- **Ce que c'est.** Finir ce que le conseil 4 a reporté : servante, type et réserve d'un résident, renvoi, coffres (diff proposé en
  `PLAN_lignes_7_a_11.md`, ligne 7), puis les actes de la pierre de foyer (maison, renaissance), puis refuser l'abandon pour un invité
  (ligne 24 : une ligne, comme `06a0f94`). Le motif est celui de `BaseRequestDelta` : une **demande** à l'host qui exécute « à la place » de
  l'expéditeur (`RemoteCraft.AsCrafter`, comme `AgentTaskDelta.cs:72-95`), répond fait/refusé, puis renvoie l'état.
- **Case host « Seul l'host gère la base »** (`HostManagesBase`, décochée par défaut, règle de session clé 13) : refuse côté host les demandes de
  `BaseRequestDelta`, `PolicyStateDelta`, `CardSettingDelta`, `NameDelta`, `AgentTaskDelta`, le nouveau `BaseSettingDelta` (6 points d'entrée,
  chacun une ligne en tête de `OnApply`), et côté client coupe les fenêtres avec le message qui existe déjà (`emp_base_host_only`,
  `RemoteBasePaidPatch.cs:41-48`). `GuestBuild` (clé 12) est déjà la case de la construction : soit on la garde et on ajoute celle-ci pour
  « tout le reste », soit on fusionne (une seule case « les autres joueurs gèrent la base », qui remplace `GuestBuild` : changement de
  nom visible pour qui a déjà coché).
- **Fichiers.** `Models/Delta/Zone/BaseSettingDelta.cs` (union 833 : servante, type de résident, réserve, rappel, renvoi : ~200 lignes, 5 genres
  avec test de propriétaire du résident et de zone), `Patches/Remote/RemoteBaseSettingPatch.cs` (~150 lignes, les lambdas de
  `BaseListPeople` et `DramaCustomSequence` : la même technique que `RemoteBasePaidPatch.OnYesNo` et `OnAddButton`), `InvSaveDataDelta.cs` (~60
  lignes, ligne 7), `NetSessionRules.cs`, `EmpConfig.cs`, `TabServerConfiguration.cs`, textes. **~700 lignes, 2 fichiers neufs, 6 retouchés.**
- **Pour deux joueurs.** L'invité fait tout ce que fait l'host dans la base, y compris renvoyer un résident ou abandonner (si on ne le
  refuse pas). Un invité qui abandonne la base de l'host la fait perdre à l'host : risque de **perte irréversible** pour l'autre joueur ; d'où
  « refuser l'abandon » (ligne 24) même dans l'option (a) : c'est un acte qu'on ne rend pas.
- **Sauvegarde.** Aucune nouvelle donnée : tout vit dans la zone de l'host (branche, résidents) qui est déjà sa sauvegarde.
- **Risques.** Chaque lambda de menu à rejouer est une source de doublons (le conseil 4 le dit : « une demande ne doit jamais être exécutée
  deux fois », « vérifier le sens inverse » : l'host qui visite une zone tenue par un invité) ; un résident déplacé (réserve) pendant qu'un
  autre joueur le regarde.

### (b) Liste de membres par base, réglée par le propriétaire

- **Ce que c'est.** Pour chaque base (zone), un **propriétaire** et une liste de **membres** avec des droits. Droits possibles : construire
  (`AgentTaskDelta`, `RemoteBuildModePatch`), régler (politiques, noms, lits, notes, coffres, tableaux), dépenser (savoir de la base,
  platine du foyer, ressources de la base), gérer les résidents (servante, type, réserve, renvoi, recrutement). Réglée par le propriétaire dans
  une fenêtre ouverte depuis la pierre de foyer (un acte de plus ajouté par un postfix comme `PlayerTradePatch`).
- **Où ranger la liste.** Dans la sauvegarde de l'host par `[ElinGameIOProperty("base_members")] Dictionary<int, BaseMembers>` (uid de zone →
  propriétaire, liste de `ulong` = identifiant du joueur `peer.User`, masque de droits), à l'image de `SavedRemoteCharas`
  (`ElinNetHostPlayerManager.cs:25-31`, `Dictionary<ulong, int>`). **Clé par identité du joueur, pas par personnage** : un joueur peut
  changer de personnage (`RosterOf`, `ElinNetHostPlayerManager.cs:107-125`). Les noms des absents sont gardés en texte (liste affichable
  hors ligne). Un monde sans entrée = « tous tous les droits » (compatibilité avec (a) et avec les parties en cours).
- **Où ça s'applique.** Les 6 points d'entrée de l'option (a) lisent `BaseRights.Can(sender, zone, droit)` : **côté host, jamais côté client**
  (un client modifié contournerait sinon ; le client n'ajoute que le grisage). Il faut donc aussi un delta de l'host vers tous
  (`BaseMembersDelta`, union 834) pour que chaque client sache ses droits sur la base où il se trouve.
- **Fichiers.** `Helper/BaseRights.cs` (~150), `Models/Delta/Zone/BaseMembersDelta.cs` (~120 : liste, ajout, retrait, droits ; seul le
  propriétaire ou l'host peut l'envoyer), `Components/LayerBaseMembers.cs` (~250, fenêtre : liste des joueurs connus avec cases à cocher),
  `Patches/Remote/BaseRightsPatch.cs` (~100, entrée « Membres » sur la pierre de foyer), les 6 points d'entrée de (a), `NetSessionRules`,
  `EmpConfig`, onglet, ~25 clés de texte × 3 langues, la fin de (a) (servante etc.). **~1 300 lignes (option (a) comprise), 5 fichiers neufs,
  10 retouchés.**
- **Pour deux joueurs.** À deux, une liste ne protège que l'host contre l'invité (et inversement pour la base de l'invité si (c) existe).
  C'est de la **politique de partie**, pas de la sécurité : l'host peut toujours tout faire. Son intérêt réel apparaît à trois joueurs et plus.
- **Effet sur la sauvegarde.** Une propriété de plus dans le même fichier que les six existantes ; un monde sans elle se charge avec la liste
  vide (« tous les droits »). Retirer le mod laisse la clé dans le fichier (non vérifié que `ElinModdingKit` l'ignore). Une liste qui référence
  une base abandonnée : à nettoyer à l'abandon.
- **Risques.** (1) Qui est propriétaire d'une base existante ? Par défaut l'host. (2) Un propriétaire qui s'exclut seul ou qui est absent :
  un droit « tous les joueurs » par défaut évite les bases bloquées. (3) Les gestes qui ne passent pas par un delta de demande (poser un objet
  tenu, déplacer un meuble, `CharaBuildDelta`) : à rattacher un par un à un droit, ou à laisser libres et à le dire. (4) Droit de
  « dépenser » : l'argent de la base et celui des joueurs ne sont pas la même chose (`BaseRequestDelta.cs:117, 138` : savoir de la base,
  platine du joueur) : à définir précisément, sinon un droit mal défini est pire que pas de droit.

### (c) Chaque joueur peut réclamer sa propre base dans le monde commun

- **Ce que c'est.** (b) plus un acte de propriété utilisable par un invité : la demande de revendication part à l'host, qui l'exécute
  (`Zone.ClaimZone()` avec l'expéditeur comme « le joueur » : `AsCrafter`), consomme l'acte dans son sac (`ModNum` : un client ne peut pas,
  `CardModNumEvent.cs:13-18`), inscrit l'invité comme **propriétaire** dans la liste de (b). Le jeu supporte déjà plusieurs branches
  (`FACTION.cs` : boucle sur tous les enfants).
- **Fichiers.** Les fichiers de (b), plus `Models/Delta/Zone/BaseRequestDelta.cs` (un genre « Claim » : ~60 lignes), un patch de `TraitDeed` pour
  un invité (**ne pas** sauter `OnRead` chez l'host : l'envoyer comme demande ; ~80 lignes), l'abandon à rendre propre (le propriétaire,
  `TraitCoreZone.cs:86-102`, la perte de l'acte), la maison du joueur (`pc.homeZone`, `Chara.homeZone`, `isClaimable` des champs : voir
  2.1) : **~1 600 lignes en tout**.
- **Pour deux joueurs.** Une base à chacun, sur la carte commune ; les deux peuvent construire dans les deux (si les droits le disent). Les
  habitants, la réserve, les compétences de faction (`charaElements`) restent **communs** (une seule faction : `JEU/FACTION.cs`), l'expédition
  est déjà par joueur (`ShippingAccounts`) mais lue sur la maison de l'host pour le journal (`GameDate.cs:325`).
- **Effet sur la sauvegarde.** La zone revendiquée est dans la sauvegarde de l'host, comme toute zone ; la propriété `base_members` y ajoute le
  propriétaire. Une zone revendiquée par un invité **qui voyage** (zone louée, simulée chez lui) a le défaut du 2.4 point 2 : le bail ne rend
  pas la branche ; la revendication doit se faire **sur la carte de l'host, par l'host** (jamais dans un bail) ; refuser ailleurs.
- **Risques.** (1) `EClass.pc.homeBranch` : un invité n'a pas de maison, plusieurs lectures du jeu en dépendent (`HotbarManager.cs:139-167`,
  `GameDate.cs:365, 412, 541`, `ContentHomeReport.cs:44`) : lire la valeur réelle d'un invité avant de bâtir (test R6). (2) Le gardien
  du monde (l'host) fait tourner les mois et l'expédition avec **sa** maison ; les bases des invités n'ont pas de journal propre. (3) Une
  base abandonnée perd son propriétaire : la liste de (b) doit suivre. (4) C'est la plus grosse des trois et elle dépend de (b).

## 2.6 Brouillons de tests (`dev/_tools/base2_suite.py` ; non exécutés)

Mêmes aides que `setting_suite.py` (S4 sert de modèle : vraie fenêtre, clic, deux sens), `base_suite.step_played`, `click_yes`, `use_menu`.

```python
# R1 : (a) la servante choisie par un invite est la servante de l'host, et inversement (rouge d'abord : aujourd'hui local)
def r1(ctx):
    for who, key in both(ctx):
        port, uid = ctx[key]
        # le resident : une servante de la base (creee par l'hote, ajoutee a la base)
        cid = ev(H, 'var c = CharaGen.Create("maid"); EClass._zone.AddCard(c, EClass.pc.pos.GetNearestPoint(false, false)); EClass._zone.branch.AddMemeber(c); return c.uid.ToString();')
        try:
            eventually(lambda: ev(port, f'(EClass._map.charas.Find(x => x.uid == {cid}) != null).ToString()') == "True", timeout=10)
            ev(port, 'EClass.ui.AddLayer<LayerPeople>(); "ok"')           # la vraie fenetre ; le clic du menu « servante » ensuite
            # menu contextuel de la ligne du resident : l'entree "makeMaid" (BaseListPeople.cs:413) ; le banc la declenche par UIContextMenu
            ev(port, f'/* trouver ButtonChara du resident {cid} dans LayerPeople, ouvrir le menu, cliquer makeMaid */ "ok"')
            check(cond=eventually(lambda: ev(H, 'EClass._zone.branch.uidMaid.ToString()') == str(cid) and
                                          ev(A, 'EClass._zone.branch.uidMaid.ToString()') == str(cid), timeout=10),
                  label=f"{who} choisit la servante : les deux jeux disent {cid}")
        finally:
            ev(H, f'var c = EClass._map.charas.Find(x => x.uid == {cid}); if (c != null) {{ EClass._zone.branch.RemoveMemeber(c); c.Destroy(); EClass._zone.branch.uidMaid = 0; }} "ok"')
            for p in (H, A):
                ev(p, 'foreach (var l in EClass.ui.layers.ToList()) l.Close(); "ok"')

# R2 : la case « seul l'host gere la base » : une demande de l'invite est refusee, celle de l'host passe (rouge d'abord : la case n'existe pas)
def r2(ctx):
    for want in (True, False):
        ev(H, f'ElinTogether.Emp.EmpConfig.Server.HostManagesBase.Value = {str(want).lower()}; "ok"')   # case de l'onglet
        time.sleep(2)
        # la politique de S4, par l'invite
        ...                                   # meme code que setting_suite.s4, seul l'invite
        check(cond=..., label=f"case {'cochee' if want else 'decochee'} : la politique de l'invite {'est refusee' if want else 'passe'} chez l'host")
        check(cond=..., label="la recherche (BaseRequestDelta) suit la meme regle")
        check(cond=..., label="construire (AgentTaskDelta) suit la meme regle")

# R3 : (b) droits : l'invite membre sans « construire » ne construit pas ; avec, construit ; l'host (proprietaire) retire le droit : refuse a nouveau
# R4 : (b) la liste survit a une sauvegarde de l'host (sauver, recharger, relire la propriete) et a la deconnexion/reconnexion de l'invite (meme ulong)
# R5 : (b) un client modifie qui envoie un BaseMembersDelta alors qu'il n'est pas proprietaire : ignore (host revalide)
def r6(ctx):
    """etat des lieux AVANT tout code de (c) : ce que lit le jeu de la maison d'un invite, et ce que devient une prise de zone faite par lui"""
    for who, key in both(ctx):
        port, uid = ctx[key]
        out = ev(port, 'var h = EClass.pc.homeZone; return (h == null ? "null" : h.Name + "/" + (h.branch != null)) + "|" + EClass.pc.faction.id + "|" + '
                       '(EClass._zone.IsPCFaction).ToString() + "|" + (EClass.pc.homeBranch == null).ToString();')
        log(f"{who} : maison|faction|zone de l'host IsPCFaction|pas de branche maison = {out}")
    # puis : l'invite lit un acte de propriete sur une zone revendicable (champ), repond Oui ; on lit chez les deux jeux
    # `Zone.mainFaction`, `branch != null`, `GetInt(2)` de la zone : resultat a NOTER, pas a exiger
```

R1 à R5 : rouge d'abord sur le code actuel, vert après. R6 est un état des lieux (à jouer **avant** de choisir (c)). Test d'une zone tenue par
un invité (bail) : refus propre de la base.

## 2.7 Non vérifié (Partie 2)

- La valeur de `EClass.pc.homeZone` / `homeBranch` / `faction` d'un invité (R6) ; si les lectures sans test nul de `homeBranch` s'exécutent
  chez un invité (il joue sans erreur aujourd'hui, donc probablement non nul ou protégées : à confirmer).
- Ce que devient exactement, chez l'host, une revendication faite par un invité (R6) : zone toujours `Wilds`, demi-état, ou prise.
- Si `ElinGameIOProperty` accepte un dictionnaire de structures (les six existantes : `Dictionary<ulong, int>`, `Dictionary<ulong,
  List<int>>`, `Dictionary<int, long[]>`, `Dictionary<int, byte[]>` imbriqué) ou doit rester sur ces formes simples ; et ce qu'il en advient sans le mod.
- Les gestes qui ne passent pas par une demande (poser un objet tenu, déplacer un meuble) : à quel droit les rattacher.
- Si le recrutement d'un résident par un invité (tableau de quêtes, étape `_hire`) arrive vraiment chez l'host (`recruit_suite` 45/45 couvre les
  compagnons, pas les résidents).
- L'effet d'un renvoi ou d'une mise en réserve fait par un invité sur le groupe de l'autre.
- Le comportement à trois joueurs (droits d'un membre quand l'host est parti : la zone peut être tenue par un invité, `IsZoneSession`) ; une
  carte tenue par un invité (bail) : toutes les demandes de base y sont refusées (`BaseRequestDelta.cs:88`, `PolicyStateDelta`) et le restent.
- `ContentHomeRanking`, `LayerHomeReport` : lus par l'invité, le contenu est celui de **sa** copie de la branche (à jour parce que la branche voyage
  par `BaseStateDelta`), non relu.

## 2.8 Questions pour le conseil (Partie 2)

1. **(a), (b) ou (c) ?** (a) donne « zéro différence » à deux joueurs et reste petit ; (b) n'a de sens qu'à trois joueurs ou pour un host qui
   veut protéger sa base ; (c) demande de résoudre la maison d'un invité d'abord (R6).
2. Une case « seul l'host gère la base » : séparée de `GuestBuild` (clé 12) ou fusionnée avec elle ?
3. **Abandonner la base** par un invité : refuser (recommandé : irréversible pour l'autre), ou permettre avec une confirmation de l'host ?
4. **Renvoyer** un résident, **mettre en réserve** : permis à tout joueur ?
5. **Dépenser** : l'argent du joueur reste le sien (aujourd'hui) ; le « savoir de la base » et les ressources de la base : à tous ?
6. Pour (b) : le propriétaire par défaut est l'host ; un joueur peut-il devenir propriétaire d'une base existante (don, vote) ?
7. Où ranger la liste : propriété `ElinGameIOProperty` (recommandé) ou dans la zone elle-même (nouveau champ du jeu, risqué pour une sauvegarde
   qui perd le mod) ?
8. Faut-il d'abord **jouer R6** (état des lieux d'une prise de zone par un invité) avant que le conseil choisisse entre (b) et (c) ?
