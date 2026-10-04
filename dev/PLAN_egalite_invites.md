# Plan — ce qu'un invité perd par rapport à l'host (même carte)

Demande de l'utilisateur (2026-10-02 au soir, après sa première soirée à deux PC, lui en invité) : « voir les
autres inégalités du genre entre invités et hôte ». Les trois premières trouvées ce jour-là (lit du sac laissé
par terre, fabrication avec les dons de l'host, vitesse en combat) ont la même cause : **le jeu ne fait certaines
choses que pour le joueur local**. Chez l'host, le personnage d'un invité n'est pas « le joueur » ; chez
l'invité, l'action est remplacée par une demande à l'host. Ce que le jeu réservait au joueur n'est alors fait
nulle part, ou est fait pour l'host.

Cette liste vient d'une **lecture du code** (jeu décompilé + mod), le 2026-10-02. **Rien n'a été joué** : chaque
ligne est à prouver par un test rouge avant d'être corrigée. Le rapport complet de l'audit (avec les numéros de
ligne) n'est pas dans le dépôt ; il se refait en relisant les classes citées.

## Les sept mécanismes

| # | Dans le mod | Conséquence |
|---|---|---|
| K1 | un client ne peut pas s'ajouter une condition (`CharaAddConditionEvent`) | un effet que seul le jeu de l'invité applique ne fait rien |
| K2 | un client ne peut pas changer le nombre d'une pile (`CardModNumEvent`) | l'objet utilisé n'est pas consommé |
| K3 | un objet créé chez un client est détruit à la fin de l'image (`CardGenEvent`, `CardCache`) | l'objet gagné disparaît |
| K4 | les points de vie viennent de l'host, 5 fois par seconde (`CharaStateSnapshot`) | un soin fait seulement chez l'invité est effacé |
| K5 | `Trait.OnUse(Chara)` est une demande, l'host l'exécute (`CardOnUseEvent`) | chez l'host, « le joueur » et l'écran sont ceux de l'host |
| K6 | les actions du menu contextuel (lambdas) et les actes construits par `new` ne sont pas envoyés (`CharaActPerformDelta`) ; `OnUse(Chara, Card)` et `OnUse(Chara, Point)` non plus | ces actions ne tournent que chez l'invité, où K1–K4 s'appliquent |
| K7 | une IA absente de la table est envoyée comme `FakeTask` (`CharaTaskRemoteEvent`) ; une tâche connue tourne chez l'host pour un « non-joueur » | les branches réservées au joueur sont sautées |

## La liste

État : `à prouver` (lu dans le code seulement), `rouge` (test écrit, défaut vu en jeu), `corrigé` (commit), `faux`
(le test montre que ça marche).

### Gênant dans une soirée ordinaire

| Id | Ce que voit le joueur | Classes du jeu | État |
|---|---|---|---|
| H1 | se reposer / méditer ne rend pas ses points de vie à un invité (seulement le mana) | `AI_PassTime`, `AI_Meditate` | **rouge** le 2026-10-02 : +0 pour l'invité, +21 pour l'host. Et pour **tous**, host compris, le repos finit en sommeil en quelques secondes |
| H2 | à la pêche, un invité a beaucoup moins de prises bonus | `AI_Fish.Makefish` | **rouge** : 0,6 % contre 7,1 % sur 4000 prises. La pêche elle-même marche |
| H3 | les baguettes d'un invité n'ont aucun effet sur le monde | `TraitRod`, `ActZap` | **rouge** : cible intacte, charge usée chez lui seul, et une exception chez l'autre joueur à chaque coup (dans les deux sens) |
| H4 | coffres de pari : les coffres d'un invité ne s'usent jamais, il les rouvre sans fin | `TraitGambleChest`, `AI_OpenGambleChest` | **rouge** : 32 points d'endurance perdus en 15 s, le personnage de test en est mort. L'host n'est pas interrompu (la lecture se trompait) |
| H5 | un invité ne peut pas remplir une bouteille vide | `TraitPotionEmpty` | **rouge** |
| H6 | un invité ne peut pas allumer une torche | `TraitToolTorch` | **sans objet** : aucun objet du jeu ne porte ce trait en EA 23.351 |

Tests : `guest_suite.py` (G1 à G5), journal rouge `_shots/guest_suite-red.log` sur `3eb0741`.

**Corrigés le 2026-10-02 à 21h35**, `guest_suite.py` 41/41 (`_shots/guest_suite-green.log`) :
H5 `88f1241` (sert aussi à la teinture et à la viande sur une tombe, pas jouées), H3 `7aa1cc6`, H2 `94b7b56`,
H1 et H4 `a9fe6ee`. Pas dans le zip 0.26.309. Passe complète à refaire avec ces cinq corrections.

**Troisième lot, 2026-10-03 vers 1h30**, `guest_suite.py` G10 à G16 : rouge 42/59
(`_shots/guest_suite-lot3-red.log`), vert 53/53 (`_shots/guest_suite-lot3-green.log`). Corrigés : L3 parchemin
d'identification `8e1c7ee` ; M8 arrosoir `8925eea` (plus une exception à chaque usage, dans les deux sens) ; M4 livres
anciens et livres d'un dieu `ed51490` ; M6 graines `453a5f0` ; M10 vœu `c0ab2e2`. Conception détaillée (avec M3, M5,
M9) : rapport d'agent, pas dans le dépôt.
**À décider par l'utilisateur** : M3 (deux joueurs du même dieu : un seul familier et un seul artefact par monde,
qui les reçoit ?), M5 (pièges : le jeu de l'invité ne tirerait plus ; prix, l'invité ne gagne plus d'expérience
de désamorçage), M9 (carte au trésor : correction simple, mais le vrai test demande les deux joueurs sur la carte
du monde).

**Quatrième lot, 2026-10-03 vers 3h55**, G19 à G25 : rouge 46/64, vert 63/63. Corrigés : outil de fabrication du
sac `9114ca3` (fin de M12 hors munitions) ; repas d'un invité repu L11 `8a1443b` ; **mannequin** `4b1455c` (il prenait
l'équipement de l'host) ; livres de plan L2 `5c5d125` ; paquets du Nouvel An et de Jure, statue dorée d'un dieu
`0fc19ee` (fin de M1 ; l'allié du Nouvel An appartient à celui qui ouvre).
Préparés, pas faits : M11 bénédiction (touche au drapeau « est le joueur » que le mod enlève exprès aux invités :
à faire avec prudence), M13 grimoires (l'host tirerait seul ; prix : un échec de lecture ne coûterait plus de mana
ni de téléportation à l'invité), L4 puits et L5 tickets de meuble (un petit mécanisme nouveau).
**Munitions corrigées** `1f774e7` (G30 : celles de l'invité rechargeaient l'arme de l'host).
**À décider par l'utilisateur** en plus : L1 (un invité qui meurt doit-il perdre de l'or, comme le joueur seul
après le jour 90 ?), L7 (prime de la guilde des guerriers : à celui qui tue, ou au maître du compagnon qui tue).

Vu en testant, pas corrigé : **premier clic de pêche d'un invité déjà au bord de l'eau** — le jeu dit « pas
d'appât », l'appât s'équipe un instant après (l'équiper est une demande à l'host), il faut recliquer. Chez l'host
l'appât s'équipe tout de suite. **Corrigé** `316160e` : G11 passait seul mais échouait dans la suite complète
(passe « nuit2 ») ; vert ensuite (15/15).

Laissé de côté, noté dans les commits :
- une baguette ou un parchemin qui fait choisir un objet (identification…) : appliqué deux fois pour un invité
  (L3, `LayerDragGrid.TryProc`) ;
- le mécanisme « action de menu rejouée chez l'host » écrit pour la torche (H6) : retiré faute d'objet pour le
  tester ; il servirait au puits (L4), aux tickets de meuble (L5), aux réglages de la base (M14) ;
- sons joués chez tout le monde, compteurs de l'host (pêche du jour, coffres ouverts) qui comptent aussi les
  invités.

### Moins fréquent

| Id | Ce que voit le joueur | Classes du jeu | État |
|---|---|---|---|
| M1 | colis, boîtes cadeau, maquettes, statue de dieu dorée : le contenu va dans le sac de l'host | `TraitParcel`, `TraitGiftPack`, `TraitPlamoBox`, `TraitGodStatue` | **corrigé** `11ca53d` (G6) pour colis, paquet cadeau, maquette. Restent : paquets du Nouvel An et de Jure (ils donnent aussi un allié), statue de dieu |
| M2 | boule de gacha : le lot tombe aux pieds de l'host | `TraitGachaBall`, `Player.DropReward` | **corrigé** `11ca53d` (G7) |
| M3 | un invité ne reçoit jamais les cadeaux de son dieu (familier, artefact) | `ActPray`, `Religion.TryGetGift` | **corrigé** `78c345d` (conseil du 2026-10-04 : un compte de cadeaux par joueur ; `council_suite` C4) |
| M4 | un livre ancien déchiffré par un invité tombe en poussière | `TraitBaseSpellbook.OnRead` | à prouver |
| M5 | un piège peut toucher un invité deux fois | `TraitFloorSwitch`, `TraitTrap` | **corrigé** `31c0c28` (conseil : tiré dans le jeu de l'invité seulement, il garde l'expérience ; sommeil, cécité, paralysie demandés à l'host ; C5) |
| M6 | les graines récoltées par un invité suivent le talent Agriculture de l'host | `TraitSeed.MakeSeed` | à prouver |
| M7 | une recette trouvée en récoltant / creusant / minant est oubliée à la reconnexion | `TaskHarvest`, `TaskDig`, `TaskMine`, `AddRecipeEvent` | **corrigé** `e3772ef` (G9, en creusant ; récolte et mine pas jouées) |
| M8 | l'arrosoir d'un invité ne se remplit pas pour de vrai | `TraitToolWaterCan`, `ActDrawWater` | à prouver (même maillon que H3) |
| M9 | carte au trésor d'un invité : pas de coffre en creusant | `TaskDig` | **corrigé, pas vérifié en jeu** `4b45541` (seulement quand l'invité est sur la carte du monde avec l'host ; le banc n'arrive pas à y faire creuser l'invité) |
| M10 | le vœu d'un invité ne donne rien | `ActEffect.Wish` | à prouver |
| M11 | la bénédiction du dieu d'un invité est calculée comme celle d'un familier | `Chara.GetPietyValue` | **corrigé** (`RemotePietyPatch`, G31). Reste : les jours passés avec son dieu ne sont comptés que dans le jeu de l'invité |
| M12 | banque, coffre des impôts, mannequin, outil du sac… : la fenêtre s'ouvre chez l'host ; le mannequin prend l'équipement de l'host | plusieurs `Trait*.OnUse` | **corrigé** `3f45072` (G8) pour banque, coffre des impôts, panneau des politiques, **corde** (l'host se voyait proposer de se pendre) et **pierre de retour** (l'host était emmené sur la carte du monde) ; table de blackjack et machine à sous par le même chemin, pas jouées. Restent : mannequin, munitions, outil de fabrication utilisé depuis le sac |
| M13 | un invité rate deux fois plus souvent la lecture d'un grimoire | `AI_Read`, `TraitBaseSpellbook.TryProgress` | **corrigé** `202f026` (conseil : tiré dans le jeu du lecteur seulement, un échec use le livre chez l'host ; C1). Limite : sur un échec, ni confusion ni monstres |
| M14 | réglages de la base faits par un invité (lit, nom de zone, panneaux, étiquettes de vente…) : seulement sur son écran | lambdas de `TraitBed`, `TraitCoreZone`, `TraitSalesTag`… | à prouver |

### Rare ou mineur

L1 un invité qui meurt ne perd pas d'or (**corrigé** `d9df4f6`, C2) · L2 livre de plan / politique sans effet ·
L3 parchemin d'identification / enchantement appliqué deux fois · L4 un puits ne se vide jamais pour un invité
(**corrigé** `8f39634`, G35 et G39) · L5 tickets de meuble pas dépensés (**corrigé** `8f39634`, G33) · L6 pas de
punition en quittant son dieu (**corrigé** `e9824ee`, `equal2_suite` E3) · L7 prime de la guilde des guerriers payée
à l'host (**corrigé** `a5d764a`, C3) · L8 pas de bonus de source chaude (**corrigé** `8e413a8`, E4 : l'invité et son
compagnon, pas l'host) · L9 seringues (**corrigé** `8f39634`, G34 et G38), stéthoscope (**corrigé** `8f39634`, G37),
clé (faux), teinture (`88f1241`)… sans effet ou pas consommés · L10 petits bonus réservés au joueur (point faible du
codex, fièvre de pêche…) · L11 un invité déjà repu qui mange perd la nourriture pour rien. Aussi corrigés avec
`equal2_suite` : laisse (`8f39634`, G36), appel à l'aide (`cf4797d`, E1), abattage (`299c8bd`, E2).

Vu en passant, pareil pour tous : pendant une session, se reposer finit vite en sommeil (ou en demande de
sommeil), parce que le mod rend « peut dormir » toujours vrai. À voir avec H1.

### Soupçons, pas suivis dans le code
Tirages faits une fois de chaque côté (mutations, maladie de l'éther) ; mana ou endurance changés par quelqu'un
d'autre ; autel de l'invention (deux recettes différentes) ; liste des combinaisons connues d'un atelier.

### Vérifié, en ordre
Manger et boire, lancer des sorts, niveau et points de dons, butin des récoltes, fabrication, crochetage,
boutiques, dépôts à la banque et au coffre des impôts, pourboires de musique, lancer, tir, faim et surcharge,
météo, prière quotidienne et offrandes, guildes et drapeaux d'histoire, portes, gènes de slime, mort et retour.

## Comment s'y prendre

1. Une suite `guest_suite.py` : pour chaque ligne, **le même geste fait par l'host puis par l'invité**, et on
   compare. Rouge d'abord.
2. Une correction couvre plusieurs lignes : exécuter chez l'host « à la place du joueur » (`RemoteCraft.AsCrafter`,
   déjà utilisé pour la fabrication) → H2, M1, M2, M4, M6, M9, L2. **Trait par trait**, pas en bloc : M12 montre
   ce qui arrive quand du code d'écran réservé au joueur tourne chez l'host.
3. H3 + M8 (+ L9) : envoyer le type de l'acte et l'outil avec `CharaActPerformDelta`.
4. H5 (+ L9) : intercepter aussi `OnUse(Chara, Card)` et `OnUse(Chara, Point)`.
5. H6, L4, L8 : une petite demande « condition sur soi », avec liste fermée.
6. H1 : faire tourner le repos d'un invité chez l'host (soin seulement).
7. M14 est le plus coûteux (un message par famille de réglages) : à décider avec l'utilisateur, ou écrire que la
   base se règle chez l'host.

Ordre : H1 → H6 dans l'ordre, puis M1/M2/M4/M6/M9 (même correction), puis le reste.
Règle du fork : chaque nouveau comportement a sa case côté host. Ici ce sont des défauts, pas des comportements
nouveaux : pas de case, sauf si une correction change ce que l'host vit lui-même.

## État au 2026-10-04, nuit (conseil et vérification)

Les six décisions en attente (M3, M5, M9, M13, L1, L7) ont été tranchées par le conseil et corrigées : voir le
tableau ci-dessus et `MODLOG.md`.

**Mis à jour le 2026-10-05, 1h05** : tout ce qui est marqué corrigé ci-dessous l'est, avec son commit et son
test (branche `fix/points-restants`). Restent : consigne « ne pas s'éloigner », karma sur la carte d'un invité,
mutations, M14.

Vérifié dans le code par un agent le même soir (rien joué) :

| Point | Verdict | Correction la plus petite |
|---|---|---|
| L4 puits | réel : il ne se vide pas pour l'invité, et l'invité ne voit pas l'host le vider ; les mauvais effets ne lui arrivent pas | **corrigé** `8f39634` (G35, G39) : le geste est rejoué chez l'host, le vœu n'y est plus tiré pour l'invité, c'est son jeu qui le tire (1 chance sur 21 par gorgée) |
| L5 tickets de meuble | réel : meuble gratuit, ticket gardé | **corrigé** `8f39634` (G33) : geste tenu en main rejoué chez l'host |
| L6 quitter son dieu | réel par le choix d'un nouveau dieu ; déjà en ordre par l'autel | **corrigé** `e9824ee` (E3 : une colère, une boule, jours remis à 0, des deux côtés) |
| L8 source chaude | déjà corrigé `a9fe6ee` ; reste : le groupe de l'invité ne reçoit pas le bonus | **corrigé** `8e413a8` (E4) : le bain va à l'invité et à son compagnon, pas à l'host |
| L9 teinture | déjà corrigé `88f1241`, jamais joué | — |
| L9 seringues | réel : ni effet ni consommation | **corrigé** `8f39634` (G34 gène, G38 sang, paradis, licorne) |
| L9 stéthoscope | partiel : ses charges ne sont pas à jour chez l'host | **corrigé** `8f39634` (G37 : une charge de moins des deux côtés) |
| L9 clé | faux : aucun objet de ce genre | — |
| Laisse, consigne | réel : la laisse tire vers l'host ; « ne pas s'éloigner » lit les réglages de l'host | laisse **corrigée** `8f39634` (G36 : une seule position, ce n'était pas tiré deux fois) ; consigne : à faire |
| Appel à l'aide | réel : un habitant ami frappé par un invité devient hostile sans appeler | **corrigé** `cf4797d` (E1 : 4 voisins sur 4 hostiles à Vernis, l'host sans ennemi ; le jeu n'appelle jamais dans une base du joueur) |
| Affinité tonte, abattage | faux à la lecture (elle arrive par le jeu de l'invité) ; **confirmé** par E2 (tonte bonne). Trouvé : c'est l'host qui perdait de l'endurance quand un invité abat | abattage **corrigé** `299c8bd` (E2 : l'objet tenu part avant la tâche ; endurance et karma de l'invité, pas de l'host) |
| Karma sur la carte d'un invité | réel : un visiteur n'y est jamais criminel | envoyer karma et renommée des visiteurs à celui qui tient la carte |
| Mutations | réel mais étroit : seulement avec un équipement d'éther, une mutation de plus chez l'host | — |
| Autels (invention, soin du groupe…) | réel : l'effet allait à l'host, une recette différente par jeu | **corrigé** (`CardOnUseDelta`, G32) ; pas les deux autels à fenêtre (matière, armure) |
