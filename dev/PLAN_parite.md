# Plan : ce qui reste réservé à l'host (karma, affinité, guildes)

État des lieux par un agent (lecture du code seule) dans la nuit du 2026-10-02. Jeu : `_decomp\Elin\`. Mod :
`ElinTogether\ElinTogether\`.

**Faits vérifiés.** Un joueur distant est, chez l'host, un allié : `IsPCFaction`/`IsPCParty` vrais, `IsPC` faux.
`Chara.Die` tourne chez l'host puis est rejoué en entier chez chaque client (`CharaDieDelta.cs:41`). Les actions
tournent chez le client qui agit puis chez l'host sous `IsApplying`. Les fins de tâches tournent chez l'host et sont
rejouées chez chaque client. Les dialogues ne tournent que chez le client qui parle.

## A. Karma et crime

| Endroit | Condition | Aujourd'hui avec un joueur distant |
|---|---|---|
| Tuer un citoyen, `Chara.cs:5895-5917` | `origin.IsPCParty` | l'host perd du karma, et chaque client aussi par le rejeu |
| `AI_Steal.cs:189-196`, `AI_Slaughter.cs:121` | aucune | pareil : tout le monde est sanctionné |
| `Chara.HoldCard`, `Chara.cs:4776` | `IsPC` | karma du client correct ; chez l'host l'objet reste « propriété de PNJ », pas de témoin |
| `Zone.IsCrime`, `Zone.cs:3843` | `c.IsPC` | pas de témoin chez l'host |
| `ActRestrain.cs:44` | aucune | client sanctionné, host aussi |
| `Chara.DoHostileAction`, `Chara.cs:6786-6814` | `IsPC` | pas d'appel à l'aide ; la victime devient quand même ennemie |
| Gardes : `Chara.IsHostile` `Chara.cs:6966`, `GoalCombat.cs:143`, `Zone.RefreshCriminal`, `Player.IsCriminal` | `EClass.player` de l'host | les gardes attaquent tout le groupe si l'host est criminel, personne si seul un client l'est |

Changements proposés (derrière l'option `UsePersonalQuests`) :
1. `PlayerStandingPatch.OnModKarma`, côté client : ignorer le karma reçu pendant `ElinDelta.IsApplying` ; dans
   `PlayerStandingDelta.OnApply`, appeler `ModKarma` sous `ElinDelta.Simulate()`.
2. Côté host : coupable = propriétaire de `origin` pendant `Chara.Die` (prefix/finalizer ; `CompanionHelper.OwnerOf`
   pour les compagnons), sinon `CharaProgressCompleteEvent.Chara`. Coupable distant → `PlayerStandingDelta` relatif,
   ajuster `PlayerStandings`, sauter l'original. Pas de coupable et `IsApplying` → sauter. Sinon original.
3. `ElinNetHostPersonalQuests` : `KarmaOf(uid)` ; quand le karma d'un joueur passe sous 0,
   `chara.pos.TryWitnessCrime(chara)` et `_zone.RefreshCriminal()`.
4. Host : prefix/finalizer sur `Chara.IsHostile(Chara c)` qui note `c` ; postfix sur `Player.IsCriminal` qui répond
   pour ce joueur (karma < 0, pas de `ConIncognito`) ; sans sujet : vrai si un joueur de la carte est criminel.
5. Host : `Zone.IsCrime` (postfix) et `Chara.HoldCard` (prefix) traitent `IsRemotePlayer` comme `IsPC`.

Test : chez l'host `victim.Die(null, remoteChara)` sur un humain amical → seul l'acteur perd 5 de karma dans les
trois jeux. Puis `EClass.player.ModKarma(-40)` chez le client → chez l'host `guard.IsHostile(remoteChara)` vrai et
`guard.IsHostile(EClass.pc)` faux.

## B. Affinité des PNJ

Rangée par PNJ dans `Chara._affinity` (`_cints[5]`), une seule valeur, sauvegardée avec le personnage.
`ModAffinity` (`Chara.cs:8445`) ne l'écrit que si `c.IsPC`, avec un tirage aléatoire par point.

Aujourd'hui : cadeau → le client tire, l'host retire (`CharaGiveGiftDelta.cs:33`), les autres clients retirent au
relais : **trois valeurs différentes**. Tonte, dressage : seul le client change. Dialogues : client seul. Aucun
message ne porte `_affinity` ; elle se resynchronise seulement au rechargement du monde.

Changements proposés (le jeu de l'acteur tire, l'host garde et rediffuse) :
1. `Models\Delta\Chara\CharaAffinityDelta.cs` : `{RemoteCard Owner, int Value, bool Relative}`, union 226. Host +
   relatif : `_affinity += Value` puis diffusion en absolu. Client : `_affinity = Value`.
2. `Patches\DeltaEvents\Chara\CharaAffinityPatch.cs` sur `Chara.ModAffinity` (prefix garde l'ancienne valeur,
   postfix agit si elle a changé) : client hors application (ou rejouant sa propre fin de tâche) → envoi relatif à
   l'host ; client en application → restaurer ; host en application → restaurer (le pair le signale) ; host sinon →
   diffusion en absolu.

Risques : à sauter en voyage seul ; `RemoteCard.Find` doit trouver les PNJ globaux hors carte (non vérifié).
Test : client `npc.affinity.OnTalkRumor()` puis lire `npc._affinity` dans les trois jeux.

## C. Guildes

Essai : `DramaOutcome.cs:536` lance la quête `guild_*`. Adhésion : `:548-557` (`relation.type = Member`, phase 10).
Promotion : `:566` (`FactionRelation.Promote`). Contrôles : `Player.Is*GuildMember` lit la phase de la quête ;
`Guild.IsMember` lit `relation.type`. Contribution : `Faction.AddContribution`.

Déjà commun : la quête `guild_*` et sa phase. Pas synchronisé : `relation.type/rank/exp` (sauvés dans
`game.factions`). Adhésion et promotion ne changent que la copie du client, perdues à son prochain chargement ;
l'host a la phase 10 sans être membre.

Recommandé : **commun** (moins de travail, moins de risque).
1. `Helper\DialogFlagSync.cs` : dans `Read`/`Learn`, ajouter `g:{faction.id}:t|r|e` pour les quatre guildes.
2. Prefix côté client sur `Faction.AddContribution` : sauter pendant `IsApplying`.

Par joueur demanderait un stockage des relations par joueur, de sortir les quêtes de guilde du journal commun, et
d'attribuer contributions et salaire : en conflit avec le développement commun de la zone.
Test : client `Guild.Fighter.relation.type = Member; rank = 2; AddContribution(50)` → lire type/rang/exp ailleurs
après 1 s, puis après reconnexion.
