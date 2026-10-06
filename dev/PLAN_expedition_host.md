# Le coffre d'expédition de l'host « ne fonctionne pas » (retour 22, LemiWinks, 0.26.532) : 7 octobre 2026

**Compilé (ReleaseNightly, 0 erreur), rien joué.** Test écrit : `bank_suite.py` S2 et S3, jamais lancés.

## Ce qui se passait (lu dans le code et dans le journal de l'host)

- LemiWinks hébergeait un monde pris au dépôt ; `TakeOverPc` lui fait jouer son personnage, l'uid 582 (dans le journal,
  582 est le seul personnage dont les changements partent de ce jeu ; 1 = 玉皇大帝 et 658 = Nardole arrivent des pairs).
- `TakeOverPc` retire l'host de `SavedRemoteCharas` mais son personnage reste dans `PlayerRosters` (la liste des
  personnages de son compte, écrite quand il était invité).
- À 5 h, `ShipPlayersGoods` (`ElinNetHostShipping.cs`) prenait pour « autres joueurs » tous les uid de
  `SavedRemoteCharas` ET de `PlayerRosters` : donc l'host lui-même. Ses objets (marqués `emp_shipper` = 582, normal)
  étaient vendus par `ShipFor` « pour le joueur 582 », l'or écrit dans `ShippingAccounts[582]` (`shipping_owed`, dans la
  sauvegarde), puis `PayShipping` cherchait un pair jouant 582 : aucun, il s'arrêtait là. La vente du jeu
  (`GameDate.ShipGoods`) ne trouvait plus rien : ni or, ni rapport.
- Vu par l'host : il dépose, le matin la caisse est vide, pas d'or, pas de rapport. Deux fois dans le journal :
  22:03:02Z (3 objets, 95, 1 lingot) et 22:09:49Z (10 objets, 171, 1 lingot), sans aucune ligne `Paid shipping` pour 582
  ni `Shipping result`.
- Ouverture, dépôt, fermeture, réouverture : rien de cassé pour un host (lu). Toutes les gardes des « images »
  (`WorldBoxPatch.OnOpen`/`OnClose`, `CardAddThingEvent`, `MirrorsWorldBoxes`, `EmptyWorldContainer`) demandent
  `Transport is ElinNetClient` ; chez un host `Transport` est un `ElinNetHost`, et `IsAway` (`AwayZone`) n'est écrit que
  par le client. Seul dans sa session ou personnage échangé, cela ne change pas.

## Où est l'or

Pas perdu : dans `ShippingAccounts[582]` de la sauvegarde de l'host (266 pièces et 2 lingots pour ces deux ventes, plus
les ventes d'avant le début du journal). Si la dernière sauvegarde date d'avant une vente, les objets sont encore dans
la caisse de cette sauvegarde : dans les deux cas rien ne manque.

## Les 1500 de Nardole

Pas de l'or déposé : un solde de ventes. `PayShipping(658)` est appelé à l'arrivée d'un joueur sur la carte de l'host
(`ElinNetHostZone.cs:182`) ; Nardole s'est connecté à 22:04:05Z, payé à 22:04:17Z, et l'host a bien reçu
`Mod currency money 1500` et `money2 14` sur le personnage 658. Les 14 lingots ne s'ajoutent que dans `ShipFor` (une
vente) ; l'or ne se vend pas (`TraitCurrency.CanBeShipped` = false). 14 lingots pour 1500 : au moins deux ventes (une
seule vente de 1500 donne 15 ou plus). Rien à voir avec l'envoi de 95, 75 secondes plus tôt.

## Correction (`ElinTogether/Net/Host/ElinNetHostShipping.cs`)

- `ShipPlayersGoods` : `players.Remove(pc.uid)`. Le personnage que ce jeu joue n'est jamais « un autre joueur » : ses
  objets restent pour la vente du jeu, qui paie et affiche le rapport comme en solo.
- `PayOwnShipping` (nouveau, appelé au début de `ShipPlayersGoods`, même si la règle « expédition par joueur » est
  décochée) : ce que la sauvegarde doit au personnage que l'host joue lui est versé (pièces et lingots, `pc.Pick` comme
  le jeu), le compte remis à zéro. Les mondes existants récupèrent donc leur or à la première vente du matin (5 h),
  sans rapport pour ces anciennes ventes. Sert aussi à un ancien invité devenu host avec un solde en attente.
- `ElinNetHostHandOver.cs` non touché : la liste des personnages d'un compte doit garder le personnage (il la faut si
  le monde change encore de main).

## Pas sûr

- Que `shipping_owed` ait été écrit dans la sauvegarde après la seconde vente (sinon les 10 objets sont dans la caisse).
- `pc.Pick` d'une pile neuve chez l'host : même geste que le jeu juste après, supposé vu des invités comme lui.
- Ce que « ne fonctionne pas » voulait dire pour LemiWinks : la lecture colle (caisse vidée, rien reçu), pas confirmée.
- Un host qui a plusieurs personnages dans la liste de son compte : les objets marqués d'un autre que celui qu'il joue
  restent vendus « pour ce personnage », payés quand quelqu'un le rejoue.
