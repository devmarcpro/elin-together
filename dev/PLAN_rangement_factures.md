# Rangement automatique (i) et factures (v) : ce qui est fait, ce qui reste (6 octobre 2026)

Conseil 10 (`PLAN_conseil10_verdict.md`), points (i) et (v). Compile en ReleaseNightly, **rien n'a été lancé** : les trois
tests sont écrits sans avoir tourné. Faits de départ : `PLAN_autodump_hotbar.md`, `PLAN_factures.md`.

## Ce qui a changé

| Fichier | Quoi |
|---|---|
| `ElinTogether/Patches/DumpSparesBeltPatch.cs` (neuf) | postfix `TaskDump.ListThingsToPut` : en session (`Transport is not null`) et règle `DumpSparesBelt` vraie, le rangement ne prend ni `EClass.pc.held` ni ce dont le parent est une `TraitToolBelt` ; préfixe sur `Msg.Say(string, Card, Card, string, string)` : la ligne `dump_item` (une par objet rangé, dite par `TaskDump.Run`) écrit `dumped: objet, coffre` (Debug) |
| `ElinTogether/Patches/GuestPaysBillPatch.cs` (neuf) | préfixe/postfixe `InvOwnerDeliver.PayBill` (facture `bill_tax` ou `bill`, pas par la banque) |
| `ElinTogether/Models/Delta/Zone/BillPayDelta.cs` (neuf) | delta 839 : demande de l'invité, réponse de l'host, ligne pour tous |
| `ElinTogether/Models/Delta/ElinDelta.cs` | une ligne : `[Union(839, typeof(BillPayDelta))]` |
| `dev/_tools/hunt_suite.py` | étape `d3b` (+ fonction `where`) |
| `dev/_tools/bills_suite.py` (neuf) | étapes `c1 c2 c3 p1 p1h p2` |

La case host « DumpSparesBelt » (clé de règle 19, `EmpConfig.Server.DumpSparesBelt`, texte, onglet Server Setting)
existait déjà : rien n'a été touché.

## Rangement (i)

- `ExcludeDump` du jeu écarte déjà la rangée du bas (`IsHotItem`, `invY == 1`). Le patch ajoute la main (`pc.held`, que le
  jeu ne regarde pas quand l'objet n'est pas dans la barre) et le contenu de la ceinture.
- `ListThingsToPut` est aussi appelée par `IsValidContainer` : un coffre qui n'aurait que ces objets à prendre est
  ignoré, comme voulu.
- La trace est sur `Msg.Say` et non sur `ListThingsToPut` parce que `ListThingsToPut` sert aussi à décider si un coffre
  vaut la visite : y loguer écrirait des « rangé » pour des objets jamais rangés. `dump_item` n'est dit que par
  `TaskDump.Run` (`TaskDump.cs:114`).
- `pc.held` est celui de la partie qui range (le rangement ne prend que le sac de `EClass.pc`), donc chaque joueur est
  protégé dans son propre jeu.

### Test d3b (`python _tools/hunt_suite.py --only d3b`)

Pour l'invité puis pour l'host : un témoin ordinaire (`log`), un objet de la rangée du bas (`bucket`, `invY = 1`), un
objet dans la ceinture (`potion_empty`), un luth tenu en main hors de la barre (`HoldCard`) ; le coffre `chest3`, réglé
« ce qui s'y trouve déjà » dans les deux jeux, a un exemplaire de chacun. Après `TaskDump.TryPerform()` : pour chaque
objet, dans les DEUX jeux, sac / barre / ceinture / main / coffre. Attendu vert : témoin rangé (coffre = 2), barre,
ceinture et main restent (coffre = 1). **Attendu rouge sans le correctif : ceinture et main** (ils partent dans le coffre,
2 exemplaires), barre verte. Si la barre est rouge aussi : défaut du mod (l'objet a perdu son rang), pas la case.
Informatif : nombre de lignes `dumped:` dans le journal du mod (niveau Debug).

Ce qui n'est pas joué comme un joueur : la barre se pose par `invY = 1` (pas par glisser-déposer), la ceinture par
`AddThing` sur l'objet ceinture, le luth par `HoldCard` ; si le personnage n'a pas de ceinture, le test l'équipe par
`EQ_ID("toolbelt")` et le dit. La mise en place est vérifiée avant le rangement (« mise en place »).

## Factures (v)

### Ce que j'ai trouvé en plus de `PLAN_factures.md`

`InvOwnerOnProcessDelta` (Models/Delta/Inv) rejoue déjà chez l'host ce que fait un joueur au coffre des impôts :
`PaidByRemote` rend `TryPay` vrai sans toucher l'or de l'host (`RemoteBillPatch`), puis `PayBill` tourne chez l'host.
Et l'host re-diffuse le delta : les AUTRES invités rejouent aussi `PayBill`. Conséquences lues, jamais jouées :
- chez l'invité qui paie, `PayBill` lit son `taxBills` (0) : « mauvaise idée », son or n'est pas pris ;
- chez l'host le rejeu décrémente `taxBills`, détruit la facture et ne prend l'or de personne (impôt payé gratuitement) ;
- chez un troisième joueur, `PayBill` dit « mauvaise idée » et `EClass.pc.Pick(t)` ramasse la facture.
Le test P1 mesure tout cela (bourse, compteur, facture) : le rouge d'aujourd'hui peut donc être « or non pris » plutôt
que « compteur immobile ». Le verdict ne le savait pas.

### Le correctif

- Un seul chemin : l'invité d'une carte de l'host (`RemoteBasePaidPatch.IsRequester`) n'exécute pas `PayBill`, il envoie
  `BillPayDelta` (la facture) ; l'host relit tout (facture vivante et de ce type, pas dans le sac d'un autre joueur,
  `taxBills > 0` pour l'impôt, or du demandeur suffisant), puis prend l'or **du demandeur** (`sender.ModCurrency`, comme
  `BaseRequestDelta` pour le platine du foyer : le changement part vers l'invité par le chemin ordinaire), baisse
  `taxBills` (ou `unpaidBill`) UNE fois, détruit la facture, donne le cadeau d'impôt supplémentaire (`GetInt(35)/1000`,
  comme `PayBill`) et dit à tous.
- Une deuxième demande pour la même facture la trouve détruite : réponse `Gone`, **avant** tout mouvement d'or. Une
  deuxième facture quand le compteur est à 0 : `Gone` aussi. Or insuffisant chez l'host : `Poor` (ligne du jeu
  « notEnoughMoney »).
- Le rejeu de `InvOwnerOnProcessDelta` est coupé pour les deux factures (`ElinDelta.IsApplying` : `PayBill` ne fait
  rien), sinon double paiement (rejeu + demande). `bill_debt` et le paiement par la banque restent ceux du jeu.
- Paiement de l'host (clic normal) : le jeu paie, puis le postfixe dit à tous « X a payé ».

### Textes à ajouter (`package/LangMod/EN/emp_localization.xlsx` pour l'anglais et le japonais, `CN/SourceLocalization.json` pour le chinois)

| Identifiant | Anglais | Japonais | Chinois |
|---|---|---|---|
| `emp_ui_bill_paid` | `{0} paid a bill: {1} ({2})` | `{0}が請求書を支払いました：{1}（{2}）` | `{0} 支付了账单：{1}（{2}）` |
| `emp_ui_bill_already_paid` | `This bill is already paid: nothing was taken from you.` | `この請求書はすでに支払い済みです。所持金は減っていません。` | `这张账单已经付过了，没有扣你的钱。` |

`{0}` = le nom du payeur, `{1}` = le nom que le jeu donne à l'objet (`sources.things.map[id].GetName()`, dans la langue
de chaque joueur), `{2}` = `Lang._currency(montant, "money")` (« 500 orens »). Le code utilise `.Loc(...)`, qui est
`.lang()` plus `string.Format` (comme `emp_ui_sleep_wish`). Dans `CN/SourceLocalization.json` les clés sont
`LangGeneral.emp_ui_bill_paid.text` et `LangGeneral.emp_ui_bill_already_paid.text`. Sans ces lignes, le jeu montre
l'identifiant tel quel. Si le nom du jeu pour `bill_tax` se lit mal dans la phrase (c1 l'affiche), changer seulement
le libellé.

### Tests (`python _tools/bills_suite.py [--only c1,c2,c3,p1,p1h,p2]`)

- `c1` fin de mois par l'host (date posée au 30 à 23 h 50 dans les deux jeux, +20 min) : +1 `bill_tax`, +0 `bill` ;
  affiche les noms du jeu pour les deux objets et vérifie qu'ils diffèrent ;
- `c2` même chose par l'invité seul à Vernis ;
- `c3` trois objets dans le coffre de livraison, 5 h passées : +1 `bill` de 35, +0 impôt, déposés par l'invité puis par
  l'host (le dépôt est `InvOwner.Transaction.Process`, la fenêtre est ouverte par `CreateContainer`, pas par un clic
  sur un coffre de livraison ; l'invité est à la Prairie, pas de loin) ;
- `p1` l'invité dépose la facture d'impôt dans le coffre des impôts : bourse −500 (vue par les deux jeux), facture
  détruite partout, compteur de l'host −1, ligne « X a payé » dans les deux jeux ; `p1h` l'host (témoin) ;
- `p2` deux factures, compteur à 1, les deux joueurs paient en même temps (deux fils) : un seul a −500, la somme des
  variations d'or = −500, compteur à 0.
Si la politique 2705 (payer par la banque) est active, `c1` à `c3` le disent et s'arrêtent (la facture est payée à sa naissance).

## Pas fait, et où : « la renommée la plus haute » (quatrième étape du verdict)

`FACTION.GetFameTax(bool evasion)` (`FACTION.cs:553`) lit `EClass.player.fame` (l'host). L'endroit : un postfixe/préfixe
sur cette méthode (ou sur `GetTotalTax`, `FACTION.cs:541`, qui l'appelle, et sur `UIHomeInfo.cs:405` via
`GetTotalTax(false)`), qui remplace `player.fame` par le maximum des renommées des joueurs connectés. Les renommées des
invités arrivent à l'host par `PlayerStandingDelta` (`Helper/PersonalQuests.cs:~289`) ; à quel point elles sont à jour
n'est pas vérifié. Fichier neuf `Patches/` + une case host à ajouter (`EmpConfig`, `NetSessionRules`, onglet).

## Ce qui n'est pas sûr

- Rien n'a tourné. Les trois tests sont écrits « à l'aveugle » : noms de champs et de méthodes vérifiés dans le code
  décompilé, pas dans une partie.
- `chest_tax` (id du coffre des impôts) vient de `SurvivalManager.cs:466`, `container_delivery` de `Game.cs:818` : le
  test échoue clairement si l'un manque.
- L'ordre d'arrivée au host : le delta `InvOwnerOnProcessDelta` (qui détache la facture du sac) puis `BillPayDelta` ; si la
  facture n'est pas encore résolue chez l'host, la réponse est `Gone` (ligne « déjà payée » à tort). À surveiller en P1.
- Le montant d'or de l'invité chez l'host (sac « gardé » pour l'invité) peut être en retard de quelques centaines de
  millisecondes sur l'invité (l'or suit le chemin `CardModCurrencyDelta`, d'abord chez l'invité) : `Poor` possible à tort si
  l'invité vient de gagner l'or juste avant.
- Un invité seul sur une carte à lui, ou l'host dans la zone d'un invité : le jeu paie comme avant (pas de demande).
- `bill_debt` (dette d'un prêteur) n'est pas couvert.
- Le nom du payeur est `NameSimple` du personnage vu par l'host.

## Suite du 6 octobre 2026 : quatrième étape, banque, invité en voyage (compilé, rien joué)

- **Renommée la plus haute** : `Patches/SharedTaxPatch.cs` (neuf). `Faction.GetFameTax` : l'host, en session avec
  compagnie (`NetCompany.HasCompany`) et règle « quêtes personnelles » vraie (sinon personne ne tient la renommée des
  autres), remplace le temps du calcul `player.fame` par `HighestFame()` (maximum de la sienne et de celles de
  `PlayerStandings` pour les joueurs connectés, lecture seule), puis la remet (finaliseur). Seul ou hors session : le jeu.
  Pas de case host (les fichiers de règles sont interdits ici) : à ajouter si voulu. L'estimation d'impôt affichée dans
  le jeu d'un invité lit toujours sa propre renommée ; la facture, elle, vient de l'host. Fraîcheur : la renommée d'un
  invité arrive à l'host par `PlayerStandingDelta` quand elle change (`PersonalQuests.Tick`) : pas mesurée.
- **Paiement par la banque (politique 2705)** : lu, rien changé. `Faction.OnAdvanceMonth` ne tourne que chez le gardien du
  monde (`WorldKeeperHooks`, règle `UseWorldKeeper`, l'host) ; `CreateBill` puis `PayBill(fromBank: true)` y prennent la
  facture au vrai `container_deposit` de l'host, une fois ; la baisse de la pile passe par les événements ordinaires. Les
  dépôts d'un invité (carte de l'host, ou seul ailleurs) arrivent dans ce même conteneur : le solde lu est le bon. Règle
  `UseWorldKeeper` décochée : chaque jeu fait sa fin de mois dans sa copie (comportement d'origine, non traité). Pas de
  ligne « X a payé » pour un paiement par la banque (le postfixe l'écarte, `fromBank`).
- **Invité seul sur une autre carte qui paie une facture** : fait, plus petit que prévu mais non joué. L'invité seul
  paie dans son propre jeu (le jeu prend son or, sa copie des compteurs ; `IsRequester` est faux sans connexion) ; le
  postfixe de `GuestPaysBillPatch` envoie alors `BillPayDelta` en réponse `Paid` (identifiant, montant, cadeau d'impôt,
  nom) par `SendWhileAway` ; la ligne de `ElinNetHostUpdate.cs` laisse passer `BillPayDelta` d'un joueur en voyage ;
  l'host (`SettleAway`, seulement d'un joueur en voyage) baisse son compteur UNE fois si `taxBills > 0` (ou `unpaidBill`),
  donne le cadeau, et le dit à tous. Il ne relit pas la facture (elle est dans les mains de l'invité). Ne couvre pas : un
  invité dont la copie des compteurs dit 0 (le jeu répond « mauvaise idée », rien n'est envoyé) ; l'invité seul ne lit pas
  la ligne (liste de réception en voyage, `ElinNetClientTravel.cs`, fichier interdit ici : y ajouter `BillPayDelta`).
- Tests : `bills_suite.py` étapes `t1`, `b2705`, `p3`.

## Après relecture (6 octobre 2026, compilé, rien joué)

- **Préfixe sur `Msg.Say` retiré** (`DumpSparesBeltPatch.cs`) : il ne servait qu'à un journal Debug et `Msg.Say` est
  appelé très souvent. Pas de trace dans le postfixe : `ListThingsToPut` sert aussi à décider si un coffre vaut la visite,
  une ligne y dirait « rangé » pour des objets jamais rangés. Conséquence : l'information « lignes `dumped:` » du test
  `d3b` (`hunt_suite.py`, fichier non touché ici) vaudra 0 ; elle était informative seulement.
- **Condition « en session »** : laissée à `Transport is not null` (verdict : « dans une partie ouverte par le mod, host
  seul compris »), pas `NetCompany.HasCompany`. Rien changé.
