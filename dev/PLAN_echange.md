# Plan : fenêtre d'échange entre joueurs

Plan établi par un agent (lecture du code seule) dans la nuit du 2026-10-02. `MOD` = `ElinTogether\ElinTogether`,
`GAME` = `_decomp\Elin`.

## Recommandation

Fenêtre d'offre à deux côtés, **sans mise sous séquestre**. Une offre est une liste `(numéro d'objet, quantité)` plus
un montant d'or. Les objets restent dans le sac de leur propriétaire jusqu'à ce que les deux confirment ; alors
l'autorité de la carte revérifie tout et déplace les vrais objets en une passe. S'éloigner, changer de carte ou se
déconnecter annule la session : il n'y a rien à rendre.

- Fenêtre : nouveau calque YKF (comme `MOD\Components\LayerElinTogether.cs`), deux colonnes, champ or, Ajouter /
  Confirmer / Annuler.
- Ajouter un objet : `LayerList.SetList2` du jeu (`GAME\LayerList.cs:181`) sur le sac du joueur, avec
  `UIContextMenu.AddSlider` pour les quantités (`GAME\ActPlan.cs:649`).
- Glisser-déposer : plus tard (un glisser passe par `InvOwner.Transaction`, qui déclenche chez un client l'aller-retour
  `ThingRequest` et une pile fantôme).
- Option : `EmpConfig.Server.PlayerTrade`, règle `NetSessionRules.AllowPlayerTrade`, case `emp_ui_sv_cfg_player_trade`.

## Ce qui existe

- Jeu : clic milieu « actTrade » → `LayerInventory.CreateContainer(c)` pour tout personnage `IsPCFaction` à 2 cases
  (`GAME\ActPlan.cs:566-572`). « give » du dialogue = `LayerDragGrid.CreateGive`, mais `InvOwnerGive._OnProcess` ne
  fait que jouer un son. `Chara.GiveGift` est la logique d'affinité des PNJ (consomme l'objet) : inadapté.
- Mod aujourd'hui : `ActPlan._Update` n'est pas patché ; les joueurs distants sont des alliés, donc « actTrade » ouvre
  sans doute déjà le sac d'un autre joueur. Depuis un client, prendre chez un autre joueur est refusé
  (`ThingRequest`, `CardAddThingDelta`, `CharaPickThingDelta`) ; y déposer passe. **L'host n'a pas ce garde-fou : il
  peut vider le sac d'un client.**
- Or : un client envoie `CardModCurrencyDelta` relatif, l'host applique sous `Simulate()`.

## Messages (unions 704 et 705)

- `TradeIntentDelta` (joueur → autorité) : `Kind` (Invite, Accept, Decline, SetOffer, Confirm, Cancel), `TradeId`,
  `PartnerUid`, `List<TradeItem{Uid, Num}> Items`, `Gold`, `Revision`.
- `TradeStateDelta` (autorité → les deux joueurs seulement, `SendDeltaTo`) : `TradeId`, `Phase` (Invited, Open, Done,
  Cancelled), `UidA`, `UidB`, `ItemsA/ItemsB` (RemoteCard, Num = offert), `GoldA`, `GoldB`, `ReadyA`, `ReadyB`,
  `Revision`, `Reason`.

## Règles

- L'autorité est `NetSession.Instance.Connection` quand c'est un `ElinNetHost` (vrai host ou joueur qui tient une
  carte). L'expéditeur est reconnu par `OriginPeer` → `ActiveRemoteCharas` ; le personnage de l'autorité est traité
  localement.
- Tout changement d'offre incrémente `Revision` et efface les deux « prêt ». Une confirmation sur une ancienne
  révision est ignorée.
- À chaque image, l'autorité annule si l'un des deux n'est plus sur la carte, est mort, ou à plus de 2 cases.
- Validation avant tout déplacement : objet vivant, `GetRootCard()` = propriétaire, `Num` ≥ offert, pas équipé, pas
  « important », pas `TraitAbility`, pas un conteneur non vide, or ≤ bourse, sac du receveur pas plein. Un échec
  annule tout.
- Puis `part = Num == n ? t : t.Split(n)`, `receiver.AddThing(part)`, `ModCurrency(±or)`, sous `ElinDelta.Simulate()`
  (les patchs existants diffusent). Rien n'est créé, donc pas de doublon.

## Fichiers, dans l'ordre

1. `MOD\Emp\EmpConfig.cs` : `Server.PlayerTrade` (vrai par défaut).
2. `MOD\Net\NetSessionRules.cs` : `[Key(7)] AllowPlayerTrade`.
3. `MOD\Components\Tabs\TabServerConfiguration.cs` : la case ; textes EN (xlsx) et CN (json).
4. `MOD\Models\Delta\Inv\PlayerTradeDeltas.cs` + deux lignes `[Union]` dans `ElinDelta.cs`.
5. `MOD\Helper\PlayerTrade.cs` (public static, pour le pont de test) : sessions côté autorité, `Update()`,
   `Commit()`, `Clear()` ; état vu par le client ; API `Invite(uid)`, `Accept()`, `Offer(uid, num)`, `SetGold(n)`,
   `Confirm()`, `Cancel()`, `Describe()`.
6. `MOD\Components\LayerPlayerTrade.cs` : reconstruit à chaque `TradeStateDelta` ; invitation par `Dialog.YesNo`.
7. `MOD\Patches\PlayerTradePatch.cs` : postfix sur `ActPlan._Update` (`GAME\ActPlan.cs:473`) ; pour chaque joueur
   distant sur la case visée à 2 cases : retirer l'action `actTrade` du jeu, ajouter `emp_act_trade`
   (`TrySetAct`, `GAME\ActPlan.cs:372`).
8. `PlayerTrade.Update()` dans `CoreSynchronizationContext`, `PlayerTrade.Clear()` avec `CardCache.Reset`.
9. `_tools\trade_suite.py`, puis `DOCUMENTATION.md`.

## Test par le pont (A = client 27552, B = host 27551)

Préparation : l'host donne à A l'objet X et 100 or, à B l'objet Y, et place les deux à 2 cases.
1. A : `ElinTogether.Helper.PlayerTrade.Invite(bUid)` ; 2. B : `Accept()` ; 3. A : `Offer(xUid, 1); SetGold(50)` ;
4. B : `Offer(yUid, 1)` ; 5. les deux : `Confirm()`.

Vérifier des deux côtés : X chez B et plus chez A, Y l'inverse ; or de A −50, de B +50, somme inchangée ; X et Y
présents une seule fois dans tous les sacs et au sol ; `Describe()` = Done ; journaux propres.
Cas négatifs : A change l'offre après la confirmation de B → le « prêt » de B est effacé ; A s'éloigne de 5 cases →
annulé, rien n'a bougé ; à trois jeux, refaire entre deux clients.
