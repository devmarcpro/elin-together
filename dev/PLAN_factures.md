# Enquête : « la base a reçu 2 bills, une de 500 et une de 35 » (retour du 6 octobre 2026, 0.26.506)

Faite par lecture du code seule (rien compilé, rien lancé). « Non vérifié » = supposé, pas lu ni joué.

## 1. Réponse courte

- **Je n'ai trouvé AUCUN chemin qui crée l'impôt du mois en double** (ni par joueur, ni par jeu, ni en rattrapage).
- **Les deux factures sont très probablement de deux sortes différentes, pas un doublon** :
  - 500 = la facture d'**impôt** du mois (une par mois, créée par le jeu de l'host) ;
  - 35 = la facture de **livraison** : le jeu compte 20 + 5 par objet envoyé par le coffre de livraison. 35 = 20 + 5 x 3, donc
    trois objets partis par la poste le matin (5 h). Ce coffre est commun au monde, et l'invité peut y déposer de loin.
- Un tel total de 35 ne peut pas être un impôt : l'impôt de base vaut 500 au minimum (voir 2a). Mais le **nom** de chaque
  facture dans la boîte et le contenu du coffre ne sont pas vérifiés : d'où les questions du point 5.

## 2. Dans le jeu (dev/_decomp/Elin)

a. **Facture d'impôt** : `Faction.OnAdvanceMonth` (FACTION.cs:387-419), appelée une seule fois par `GameDate.AdvanceMonth`
   (GameDate.cs:275-297), lui-même appelé par `AdvanceDay` (GameDate.cs:170-186) quand le jour dépasse 30.
   Elle paie aussi, le même jour : impôt des habitants, revenu de rang, salaire de faction (colis `parcel_salary` ou banque).
   Montant = `GetTotalTax` (FACTION.cs:541-565) = **500 + 500 par année écoulée (10 ans au plus)** + impôt de renommée
   (`player.fame`, courbe) + `player.extraTax`, le tout réduit par le don d'évasion fiscale (feat 2119) des bases.
   Au début d'une partie : 500 + 0 = 500. Cela colle avec « 500 ».
   Elle crée `bill_tax` (ThingGen.cs:85-99), ajoute au compteur `player.taxBills`, puis `TryPayBill` : payée par la banque
   si la politique 2705 est active et que le compte suffit, sinon `World.SendPackage` (liste `game.cards.listPackage`).
   Elle est adressée au **joueur** (`EClass.player`, `EClass.pc.faction`), jamais à une base précise. Si `taxBills >= 4` : karma -50.
b. **Facture de livraison** : `GameDate.ShipPackages` (GameDate.cs:446-489), à 5 h chaque jour (AdvanceHour, hour == 5) :
   pour chaque carton rempli depuis `container_deliver`, `CreateBill(20 + 5 par objet, tax: false)` puis `TryPayBill` (même chemin).
   Le compteur est `player.unpaidBill`. Sans objet dans le coffre, aucune facture.
c. **Arrivée dans la boîte** : `FactionBranch.ReceivePackages` (FactionBranch.cs:788-817) vide `listPackage` et appelle
   `PutInMailBox` (boîte aux lettres de la base, sinon par terre devant elle). Toutes les factures arrivent par là.
d. Salaire, colis, lettre de Lutz, cadeaux : tous passent par `World.SendPackage` ; mêmes crochets que la facture d'impôt.

## 3. Dans le mod : qui fait tourner quoi

- `GameDate.AdvanceMin` est coupé chez tout invité (`WorldDateAdvanceEvent.OnAdvanceMin`, retourne `IsHost`) : **un invité sur
  la carte de l'host ne fait jamais tourner AdvanceHour/Day/Month**.
- Chez l'invité, `WorldDateAdvanceDelta.OnApply` (commit 194c6d7) refait SEULEMENT ce qui touche son joueur : `player.OnAdvanceHour`,
  jours (`stats.days`, coût de relance des quêtes, prière, `player.OnAdvanceDay`), mois (`stats.months`, `nums.OnAdvanceMonth`,
  puits), année. **Aucune facture, aucun salaire, aucun colis** : `Faction.OnAdvanceMonth` n'y est pas.
- Invité seul sur une carte (copie à lui, `IsZoneAuthority`) : son `AdvanceMin` tourne, donc `GameDate.AdvanceMonth` aussi, mais
  `WorldKeeperHooks` (Patches/WorldKeeper.cs:66-92) saute `Faction.OnAdvanceDay/OnAdvanceMonth`, `World.SendPackage`,
  `ReceivePackages`, `ShipLetter`, `ShipRandomPackages` pour tout jeu qui n'est pas l'host (règle `UseWorldKeeper`, **vraie
  par défaut**, EmpConfig.cs:170). `ShipGoods` et `ShipPackages` sont sautés chez un invité ou un jeu « away »
  (WorldShipGoodsEvent.cs). Puis l'host rattrape (`WorldTimeReportDelta` -> `CatchUp` -> `AdvanceMin(retard)`) et fait la fin de mois
  **une seule fois**, parce que sa date saute le mois une seule fois.
- `PlayerStandIn.For` n'est utilisé que pour des étapes de quête, de voyage et d'artisanat (PersonalQuests.cs:411, NetHostTravel,
  CardActReplayDelta) : **pas** pendant un crochet de jour ou de mois. Il ne change pas `player.chara` pendant la fin de mois.
- Le test `world_suite.py` K2 « fin de mois comptée une fois » le dit bien : +1 `taxBills` chez l'host, 0 chez l'invité, 0 colis
  fabriqué chez l'invité. Mais il ne compte que le **compteur** `player.taxBills` et les colis de l'invité, pas les objets dans la boîte
  ni dans les sacs, et pas la facture de livraison. `hunt2_suite` E5 ne regarde que le compteur de jours et le coût de relance.
- Dépôt de loin : un invité qui voyage seul envoie des objets au coffre de livraison de l'host (`ElinNetHostShipping`,
  `BoxDelivery`, ligne 75). Le coffre est commun et **ne retient pas qui y a mis quoi** (contrairement à la boîte de vente, clé
  `emp_shipper`). La facture de 35 va donc au compte de l'host, quel que soit celui qui a déposé.
- Salaires, paie des habitants, colis, journal : **pas en double** par lecture (mêmes crochets, un seul jeu). Non vérifié en jeu.

## 4. Ce qui est possible mais non vérifié

- Hôte avec la case `WorldKeeper` décochée : alors chaque copie d'invité seul compte sa fin de mois (test K4 le montre rouge
  à dessein : +1 facture chez l'invité). Cela ferait un doublon d'impôt, mais le montant serait 500 aussi, pas 35.
- Le nom affiché des deux objets (`bill_tax` / `bill`) : non lu (données du jeu non décompilées ici).
- Un invité ne peut peut-être pas payer l'impôt : `InvOwnerDeliver.PayBill` (InvOwnerDeliver.cs:65) refuse (`badidea`) si
  `player.taxBills <= 0`, et ce compteur n'est copié chez l'invité par aucun code du mod (déjà noté dans PLAN_chasse_differences_3.md,
  lignes 82-84). Non vérifié.

## 5. La règle attendue, trois options (sans trancher : décision du conseil)

Solo : une facture d'impôt par mois, calculée sur le joueur. Aujourd'hui à plusieurs : **une seule facture d'impôt pour le monde,
calculée sur l'host** (année, renommée et impôt supplémentaire de l'host ; la renommée de l'invité n'y entre pas).

| Option | Ce que chacun paie | Taille du changement |
|---|---|---|
| A. Une facture pour le monde, sur l'host (l'état actuel) | l'host a sa renommée dans le prix ; l'invité ne paie que s'il ouvre le coffre (et seulement si l'on corrige son droit de payer) ; celui qui paie, paie tout | **le plus petit** : rien à changer pour créer la facture ; seulement le droit de payer pour l'invité, et le nom des factures |
| B. Une facture pour le monde, partagée | un seul objet, mais le prix est coupé en parts (ex. 500 / nombre de joueurs) et chacun paie sa part, ou la renommée la plus haute compte | moyen : prix à définir, une part par joueur, suivi de qui a payé |
| C. Une facture par joueur, chacune payée par son joueur | host : 500 + sa renommée ; invité : 500 + sa renommée à lui (la base 500 est payée N fois) ; chacun son compteur de factures impayées et son karma | **le plus gros** : boucle par joueur dans le crochet du mois, `taxBills` et `extraTax` propres à chaque joueur, objets rangés par propriétaire |

La facture de livraison (35) a le même choix : au compte du monde (aujourd'hui), ou au déposant (il faudrait marquer l'objet
déposé, comme `emp_shipper`).

## 6. Correction du défaut certain

**Il n'y a pas de défaut certain de doublon d'impôt à corriger.** Je ne propose donc aucun changement de code avant la réponse du joueur.
Si la réponse montre que le 35 est bien un impôt (voir questions), le doublon vient alors d'ailleurs et il faut rejouer le banc ci-dessous.

## 7. Le test à deux fenêtres (à écrire : `dev/_tools/bills_suite.py`, modèle `world_suite.py`)

Il ne peut pas être « rouge » aujourd'hui sur l'impôt, puisque je n'ai pas trouvé de défaut. Il sert à prouver ou à réfuter
mon explication, et à verrouiller la règle choisie ensuite.

- Compter les factures par IDENTIFIANT, pas par compteur : `listPackage` (en route), les objets de la carte de l'host dans la
  boîte aux lettres et par terre, le sac de l'host, le sac de l'invité. Mesure en C# par `ev()` : `id == "bill_tax"` et `id == "bill"`
  (écriture exacte à ajuster, non essayée).
- Cas 1 : host et invité à la Prairie, coffre de livraison vide. Poser la date au 30 à 23 h 50 (chez l'host), laisser passer 20
  minutes. Attendu : **+1 `bill_tax` en tout**, +0 `bill`. Mesuré avant/après aussi chez l'invité (rien chez lui).
- Cas 2 : même chose, invité seul à Vernis qui franchit le mois (comme K2) : attendu +1 `bill_tax` en tout, chez l'host.
- Cas 3 : l'invité dépose 3 objets de loin dans le coffre de livraison, on passe 5 h : attendu **+1 `bill` de 35** (20 + 5 x 3),
  +0 `bill_tax`. Si le cas 1 donne 2 `bill_tax`, le doublon est réel : le test est alors rouge et c'est là qu'on cherche.
- Cas 4 (après décision) : la règle choisie (A, B ou C) écrite en chiffres : combien de factures, de quel montant, au nom de qui.
- Ne pas lancer tant que d'autres tests tournent (règle de la machine : deux fenêtres au plus).

## 8. Deux questions pour le joueur

1. Dans la boîte aux lettres, que dit le nom de chaque facture (impôt / « tax » pour l'une, autre chose pour l'autre) ? Et, juste
   avant la facture de 35, vous ou l'ami aviez-vous mis environ trois objets dans le coffre de livraison de la base ?
2. Pour l'impôt du mois, que voulez-vous : une seule facture pour toute la base (payée par qui veut), ou une facture pour chaque
   joueur, payée par son joueur ?
