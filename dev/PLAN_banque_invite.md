# La banque (et la caisse d'expédition) pour un invité : 6 octobre 2026

**Choix provisoire, à confirmer par l'utilisateur : banque commune.** Comme en solo, un seul compte pour le monde : celui
de l'host. Ce qu'un invité dépose y arrive, tout le monde le voit et peut le reprendre, c'est compté une seule fois.
**Rien de ceci n'a été compilé ni joué.** `bank_suite.py` n'a jamais tourné.

## 1. Ce que fait le jeu (lu)

- La banque est un conteneur du monde, hors de toute carte : `CardManager.container_deposit` (`CardManager.cs:58`), créé
  avec la partie (`Game.cs:819`) ; les vieilles sauvegardes y versent `player.bankMoney` (`Game.cs:436-441`).
- Le banquier (`TraitBanker`) : choix « déposer » (`DramaCustomSequence.cs:297-300`) → étape `_deposit` → une fenêtre de
  coffre ordinaire sur ce conteneur, `LayerInventory.CreateContainer(container_deposit)` (`DramaCustomSequence.cs:1718`).
  On y pose et on y reprend l'or (ou n'importe quel objet) comme dans un coffre. `_withdraw` (`:1760`, `bankMoney`) est un
  reste : aucun choix n'y mène (lu, non vérifié en jeu).
- Autres usages : revenus du mois versés à la banque si la politique 2711 est active (`FACTION.cs:399-403`), facture payée
  par la banque si la politique 2705 l'est (`FACTION.cs:426`, `InvOwnerDeliver.cs:74`), solde affiché (`WindowChara.cs:381`).
  `TraitBank` (objet « banque ») ouvre un dépôt d'or seulement dans le même conteneur (`InvOwnerDeliver.cs`, mode `Bank`).
- Même famille : `container_shipping` (caisse d'expédition, tout coffre d'expédition ouvre ce conteneur :
  `LayerInventory.cs:548-552`) et `container_deliver` (boîte de livraison, `:554-557`). Coffre des impôts : pas un
  conteneur (`TraitTaxChest`, paiement direct). Coffre « partagé » d'une base : un objet de la carte, autre chemin.

## 2. Ce que fait le mod (lu)

- Sur la carte de l'host : le monde de l'invité est une copie de la sauvegarde de l'host (`ElinNetClientPlayer.cs:184`),
  les trois conteneurs y ont les mêmes numéros et sont connus des deux côtés (`CardCache.cs:128-146`, à chaque carte :
  `ZoneActivateEvent.cs:32`). Un dépôt passe par le chemin des coffres ordinaires : `InvTransactionEvent.cs:44`
  (`ThingRequest`), puis `CardAddThingEvent` → `CardAddThingDelta`. **Lu comme correct, non vérifié en jeu** : B1 du test.
- **Invité seul sur une autre carte (voyage indépendant) : la cause.** Son jeu tourne en solo (`NetSession.cs:40`). À son
  départ ses trois conteneurs sont vidés (`ElinNetClientTravel.cs:851` → `EmptyWorldContainers`,
  `ElinNetClientShipping.cs:46`). Ce qu'il y pose est envoyé à l'host et détruit chez lui
  (`CardAddThingEvent.cs:98-114` → `ForwardShippingDeposit`, `ElinNetClientShipping.cs:18-39`) ; l'host le range dans le
  vrai conteneur (`ElinNetHostShipping.cs:91`, `OnShippingDeposit`). Rien ne revenait vers l'invité : sa fenêtre, relue
  sur sa copie vide, ne montrait rien, et il ne pouvait rien reprendre. Voulu le 3 octobre contre les doublons
  (`transfer_suite.py` X1/X2 vérifie seulement que l'objet arrive chez l'host).
- Invité dans la zone d'un autre invité : la caisse d'expédition était renvoyée à l'host (`CardAddThingDelta.cs:55-65`),
  **pas la banque ni la boîte de livraison** : l'objet restait dans la copie du joueur qui tient la zone et était
  **perdu** quand celui-ci rentrait (lu, non vérifié en jeu).

## 3. Où est l'or du joueur

- S'il était seul sur sa carte (le cas le plus probable : même symptôme pour la caisse, voir 6) : **les 1500 orens sont
  dans la banque de l'host**, dans sa sauvegarde. L'host les voit chez n'importe quel banquier ; l'invité aussi dès qu'il
  est sur la carte de l'host. Rien n'a été perdu ni doublé. À vérifier par l'host : ouvrir la banque.
- S'il était dans la zone d'un autre invité : perdus au retour de celui-ci (cas ci-dessus). Non récupérables.
- On ne sait pas lequel sans leur journal. L'host peut rendre l'or à la main si la banque ne l'a pas.

## 4. Les autres cas (lu)

- Reprendre l'or déposé par l'host : sur sa carte oui ; seul ailleurs non (copie vide), avant la correction.
- L'host : son conteneur est le vrai, rien à dire. Deux invités sur la carte de l'host : `ThingRequest` borne la pile
  à ce qui reste (`ThingRequest.cs:80`).
- Boîte de livraison : mêmes chemins que la banque, mêmes défauts, même correction.

## 5. Décision à prendre (pas prise ici)

- **Banque commune** (le jeu, et le choix provisoire) : un compte pour le monde. Simple, rien à inventer, les revenus et
  les factures de la base y passent déjà. Mais chacun peut reprendre l'or des autres : pour un groupe d'amis.
- **Un compte par joueur** : chaque dépôt marqué du joueur (comme `emp_shipper` pour la caisse), chacun ne voit et ne
  reprend que le sien. Il faut décider où vont les revenus du mois et qui paie les factures par la banque, et une case
  host. Plus gros : après accord seulement.

## 6. La caisse d'expédition d'un invité (complément du joueur)

« Mettre des items dans le shipping chest, fermer puis rouvrir n'affiche pas les items » : même cause que la banque.
- **Pas perdus** : chaque objet part chez l'host, dans la vraie caisse, marqué du joueur (`OnShippingDeposit`,
  `ShipperOverride`), et quitte le sac que l'host garde pour lui (sauvegarde demandée, `ElinNetClientShipping.cs:38`).
- **Vendus le lendemain, l'or lui revient** si la case host « expédition par joueur » est cochée (cochée par défaut,
  `EmpConfig.cs:210-213`) : `ShipPlayersGoods` (`ElinNetHostShipping.cs:145`), paiement tout de suite s'il est sur la carte
  de l'host ou seul sur la sienne, sinon gardé et versé à son retour (`PayShipping`, `:238-262`). Case décochée : tout va
  à l'host. Couvert par `economy_suite`, pas rejoué ici.
- **Reprendre avant l'envoi** : sur la carte de l'host oui (coffre ordinaire) ; seul ailleurs non, avant la correction.

## 7. Correction écrite (pas compilée)

Pas de nouveau delta (839 reste libre) : un invité seul ne reçoit pas les deltas ; les deux paquets d'expédition servent.
1. **L'invité seul voit le vrai contenu.** À l'ouverture de la fenêtre, et une seule fois (délai de 0,3 s, regroupé)
   après ses dépôts si la fenêtre est encore ouverte, il demande à l'host ce que contient le conteneur
   (`ShippingDeposit.Ask`, `AskWorldBoxSoon`) ; l'host ne répond qu'à ces demandes (`SendWorldBox`,
   `ElinNetHostShipping.cs:54`), jamais après un dépôt ; la copie
   est remplie d'**images** des objets de l'host (`OnWorldBox`, `ElinNetClientShipping.cs`), marquées
   `emp_box_uid` = numéro du vrai objet. Fenêtre fermée : le conteneur de cette fenêtre seul est vidé
   (`WorldBoxPatch.OnClose`, `EmptyWorldContainer`), pour que rien d'autre de son jeu (factures, fin de mois) ne compte
   sur des images, et que la banque et la caisse ouvertes ensemble ne se vident pas l'une l'autre.
2. **Reprendre = demander à l'host.** Une image ne peut entrer dans aucun sac ni se fondre dans une vraie pile
   (`CardAddThingEvent.cs:66-94`, `ShippingStackPatch.cs`) : au moment d'entrer dans le sac elle est détruite et l'host est
   prié de donner le vrai objet. L'host le retire de son conteneur, jamais plus que ce qui reste, et l'envoie ; l'invité le
   met dans son sac et demande une sauvegarde. Deux joueurs sur la même pile : le premier servi, l'autre lit « trop tard »
   (texte existant `emp_ui_thing_gone`). Image lâchée au sol : même demande (`WorldBoxPatch.OnDrop`).
3. **Zone d'un autre invité** : banque et boîte de livraison renvoyées à l'host comme la caisse
   (`CardAddThingDelta.cs:70-75`) : plus de perte. Rien ne s'y affiche encore : message `emp_ui_box_far` (trois langues).
4. Si l'invité a changé de carte entre la demande et la réponse, l'objet repart dans le conteneur de l'host.

Fichiers : `Helper/ShippingHelper.cs`, `Models/Shipping/ShippingPackets.cs`, `Net/Host/ElinNetHostShipping.cs`,
`Net/Client/ElinNetClientShipping.cs`, `Patches/DeltaEvents/Card/CardAddThingEvent.cs`,
`Models/Delta/Card/CardAddThingDelta.cs`, `Patches/ShippingStackPatch.cs`, nouveau `Patches/WorldBoxPatch.cs`, les deux
fichiers de textes, `dev/_tools/bank_suite.py`.

## 8. Ce qui reste fragile (à dire à l'utilisateur)

- Lien coupé entre l'envoi d'un objet repris par l'host et la sauvegarde suivante de l'invité (moins d'une seconde) :
  l'objet est perdu. Même fenêtre que le paiement d'une expédition aujourd'hui. Marqué `ponytail:` dans le code.
- Utiliser une image sans la sortir (boire une potion depuis la fenêtre de la caisse) : **impossible dans le jeu, donc
  pas de garde** (lu dans Elin 23.351). Clic droit, clic du milieu et menu contextuel d'une case passent par
  `InvOwner.ListInteractions(ButtonGrid, bool)`, dont la partie qui ajoute manger, boire, lire, utiliser
  (`trait.OnListInteraction`, `InvOwner.cs:1569`) est derrière `if (!owner.IsPC) return;` (`InvOwner.cs:1504-1507`) : une
  fenêtre de coffre (`new InvOwner(coffre, conteneur)`, `UIInventory.AddTab`, `LayerInventory.cs:569`) n'a pour
  propriétaire que le coffre, jamais le joueur. Il reste « prendre » (transaction) et « tenir en main »
  (`TryHold` → `Chara.HoldCard` → `Chara.Pick` → `Card.AddThing`, `Chara.cs:4805-4807`, `4653`) : les deux entrent dans le
  sac par `AddThing`, que `CardAddThingEvent` intercepte (image détruite, vrai objet demandé). La barre d'accès rapide ne
  garde que ce que le joueur tient (`HotItemHeld`, `Player.cs:2314`). À revérifier si une mise à jour du jeu ajoute un
  usage depuis un coffre.
- La réponse de l'host voyage dans le paquet `ShippingPayout` (seul paquet d'expédition qu'un invité en voyage laisse
  entrer, `ElinNetClientTravel.cs:983`, fichier interdit ce soir) : à sortir dans son propre paquet plus tard.
- Invité dans la zone d'un autre invité, et le joueur qui tient une zone avec des invités : dépôt sûr, mais toujours rien
  à l'écran ni de reprise avant le retour sur la carte de l'host.
- Équiper une image depuis la fenêtre, « tout prendre », rangement automatique : supposés passer par `Card.AddThing`
  (non vérifié).
- L'or qui revient passe par `pc.Pick` (ce que fait le jeu pour une reprise) : supposé rejoindre la bourse (non vérifié).

## 9. Test : `dev/_tools/bank_suite.py` (jamais lancé)

B1 invité sur la carte de l'host, B2 host, B3 invité seul ailleurs (le cas réel), B4 deux joueurs sur les mêmes pièces,
B5 banque et caisse ouvertes ensemble (fermer l'une laisse l'autre pleine), S1 caisse d'expédition. Rouge attendu sur la 0.26.506 : B3 (fenêtre, réouverture, dépôt de l'host visible, reprise,
bourse revenue), B4 (la fenêtre montre la pile), S1 (réouverture, reprise). B1 et B2 attendus verts avant comme après :
s'ils sont rouges avant, la cause du point 2 n'est pas la seule. Ce que le banc ne joue pas : en tête du fichier.
