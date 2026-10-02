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
| H1 | se reposer / méditer ne rend pas ses points de vie à un invité (seulement le mana) | `AI_PassTime`, `AI_Meditate` | à prouver |
| H2 | à la pêche, un invité a 20 fois moins de prises bonus et 50 fois moins de poissons étoilés | `AI_Fish.Makefish` | à prouver |
| H3 | les baguettes d'un invité n'ont aucun effet sur le monde | `TraitRod`, `ActZap` | à prouver (un maillon déduit) |
| H4 | coffres de pari : l'invité ne reçoit pas l'argent, les coffres ne s'usent pas, l'host est interrompu | `TraitGambleChest`, `AI_OpenGambleChest` | à prouver |
| H5 | un invité ne peut pas remplir une bouteille vide | `TraitPotionEmpty` | à prouver |
| H6 | un invité ne peut pas allumer une torche | `TraitToolTorch` | à prouver |

### Moins fréquent

| Id | Ce que voit le joueur | Classes du jeu | État |
|---|---|---|---|
| M1 | colis, boîtes cadeau, maquettes, statue de dieu dorée : le contenu va dans le sac de l'host | `TraitParcel`, `TraitGiftPack`, `TraitPlamoBox`, `TraitGodStatue` | à prouver |
| M2 | boule de gacha : le lot tombe aux pieds de l'host | `TraitGachaBall`, `Player.DropReward` | à prouver |
| M3 | un invité ne reçoit jamais les cadeaux de son dieu (familier, artefact) | `ActPray`, `Religion.TryGetGift` | à prouver |
| M4 | un livre ancien déchiffré par un invité tombe en poussière | `TraitBaseSpellbook.OnRead` | à prouver |
| M5 | un piège peut toucher un invité deux fois | `TraitFloorSwitch`, `TraitTrap` | à prouver (pas tout suivi) |
| M6 | les graines récoltées par un invité suivent le talent Agriculture de l'host | `TraitSeed.MakeSeed` | à prouver |
| M7 | une recette trouvée en récoltant / creusant / minant est oubliée à la reconnexion | `TaskHarvest`, `TaskDig`, `TaskMine`, `AddRecipeEvent` | à prouver |
| M8 | l'arrosoir d'un invité ne se remplit pas pour de vrai | `TraitToolWaterCan`, `ActDrawWater` | à prouver (même maillon que H3) |
| M9 | carte au trésor d'un invité : pas de coffre en creusant | `TaskDig` | à prouver |
| M10 | le vœu d'un invité ne donne rien | `ActEffect.Wish` | à prouver |
| M11 | la bénédiction du dieu d'un invité est calculée comme celle d'un familier | `Chara.GetPietyValue` | à prouver |
| M12 | banque, coffre des impôts, mannequin, outil du sac… : la fenêtre s'ouvre chez l'host ; le mannequin prend l'équipement de l'host | plusieurs `Trait*.OnUse` | à prouver |
| M13 | un invité rate deux fois plus souvent la lecture d'un grimoire | `AI_Read`, `TraitBaseSpellbook.TryProgress` | à prouver (pas tout suivi) |
| M14 | réglages de la base faits par un invité (lit, nom de zone, panneaux, étiquettes de vente…) : seulement sur son écran | lambdas de `TraitBed`, `TraitCoreZone`, `TraitSalesTag`… | à prouver |

### Rare ou mineur

L1 un invité qui meurt ne perd pas d'or · L2 livre de plan / politique sans effet · L3 parchemin
d'identification / enchantement appliqué deux fois · L4 un puits ne se vide jamais pour un invité · L5 tickets de
meuble pas dépensés · L6 pas de punition en quittant son dieu · L7 prime de la guilde des guerriers payée à
l'host · L8 pas de bonus de source chaude · L9 seringues, stéthoscope, clé, teinture… sans effet ou pas
consommés · L10 petits bonus réservés au joueur (point faible du codex, fièvre de pêche…) · L11 un invité déjà
repu qui mange perd la nourriture pour rien.

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
