# Passation — ElinTogether « indépendance »

## État au 11 octobre 2026, 1h (à lire en premier ; tout ce qui suit dans ce fichier est plus ancien)

- **Publiée : 0.26.621** (9 octobre, Elin EA 23.353). **Rien publié depuis** : l'accord n'a pas été donné (question posée le 10 au soir, réponse : « continue à travailler »). Tout le travail du 10 et du 11 est sur `fix/points-restants` = `feat/independent-travel` (poussée).
- **Le détail est dans `MODLOG.md`**, entrées du 2026-10-10 et du 2026-10-11 (causes, pièges du banc, ce qui n'est pas joué). Test du lot : `dev/_tools/oct10_suite.py` (étapes r1 implicite, b1, c1, h1, f1, l1, q1 ; f2 à trois fenêtres : `mp_test.py --clients 2`).
- **Fait et joué au banc** (vert) : personnage en double dans l'équipe ; offres de quêtes d'une ville après un tirage ; recette de bloc comptée une fois ; une seule bourse pour un invité neuf ; sorts des barres gardés d'une session à l'autre ; trois factures payées de suite depuis une autre carte ; PV du perdant après un duel (duel_suite 92/92) ; **monstre figé** quand un autre joueur que sa cible l'attaque (conseil 13 : l'horloge du monstre est celle du joueur engagé le plus rapide ; joué sur la carte de l'host ET sur une carte tenue par un invité, trois fenêtres) ; **boutiques à stock limité une fois par joueur** (`LimitedStockPatch`) ; compteurs « du joueur » propres à chacun (prix du titre de terrain, etc.).
- **Fait, compilé, relu, PAS prouvé par un test dédié** : recettes d'un joueur seul ailleurs (dans les deux sens) ; niveau gagné par un joueur absent ; saignement/poison en nuit commune ; file vidée avant la copie d'une carte ; mort d'un personnage déjà retiré de sa zone (T8 vert une fois) ; laisse d'un compagnon d'invité qui tire jusqu'à revenir à côté (g36, intermittent, pas reproduit sur commande) ; reprise automatique R4 (les autres invités rejoignent celui qui reprend : trois fenêtres, et Steam ne se prouve qu'entre vrais PC).
- **Règle de l'utilisateur rappelée le 10** : « aucune différence entre l'hôte et les invités » : une correction qui ne marche que quand l'HOST simule la carte n'est pas finie ; la prouver aussi sur une carte tenue par un invité (trois fenêtres), sans demander. Il a aussi dit : travailler en autonomie, sans s'arrêter, trouver seul la suite.
- **Demandes de l'utilisateur en attente** (ses mots dans la mémoire `elintogether-user-ideas`) : (1) les autres « une fois par monde » : `dev/PLAN_une_fois_par_monde.md` (récompenses des quêtes d'histoire et cadeaux de dialogue = le gros morceau, à passer au conseil ; trésor de Melilith ; guildes) ; (2) « beaucoup de bugs autour des compagnons » (sans détail : demander des exemples, ou chercher : montures, laisse, mort, réanimation) ; (3) journal séparé par joueur ; (4) factures fantômes des mondes déjà touchés (« on verra plus tard ») ; (5) que le dépôt GitHub apparaisse comme un fork ; (6) publier : à redemander.
- **Rouges connus du banc, pas des défauts** : `sleep_suite` (l'invité de test meurt pendant sa nuit, cascade) ; `hunt2_suite` E3 (test périmé : un seul joueur fait sauter trois heures) ; `guest_suite` baguette de l'host ; `bills_suite` politique 2705.
- **Trouvé, pas corrigé** : joueur refusé par le teneur d'une carte qui reçoit le monde entier ; expérience « de groupe » donnée par l'host à sa copie d'un invité (jardinage, voyage) ; bouton « Reroll Quests » chez un invité (influence dépensée, rien de tiré) ; monture qui garde la case d'une autre carte (garde en place, cause pas trouvée).
- **Ce PC (Steam Deck)** : le jeu contient le build de TEST (Debug) du dernier commit, pas une version publiée. `dev/_lab/Elin2` et `Elin3` refaits pour la 23.353 ; `dev/_decomp` date de la 23.352. L'utilisateur a donné l'accord pour lancer Elin le 10 au soir ; `run_short.sh` ferme TOUS les Elin entre deux suites.
- **Prochains numéros** : delta 846, règle de session 24.

## État au 7 octobre 2026, 11h30 (à lire en premier)

- **Publiée : 0.26.540.** Corrigé depuis, poussé, **pas publié** (accord à demander) :
  - facture d'un invité (joué, `bills_suite` 51/53) ; rune/prise, carburant, philtre, vente non identifiée (compilés) ;
  - **ce qu'un invité prend dans un coffre, une boutique ou la banque et qui s'empile dans sa bourse ou un sous-sac
    manquait dans son jeu** (`CardTryStackToEvent` : `IsRemoteStateLanding`) : `bank_suite` b1 rouge puis **86/86**,
    `trade_suite` 122/122, `guest_suite` 333/334 (une baguette qui rate, hasard) ;
  - l'écran de nuit d'un invité attend la fin de la nuit du monde 60 s réelles au lieu de 60 pas (4 s) ;
  - le réveil trop tôt de n7 était un bernard-l'ermite du monde de test (pas un défaut).
- **Cinq joueurs** (demande de l'utilisateur, 2026-10-07 : « des essais avec 5 clients ») : `_lab/Elin5` créé
  (`make_lab.py Elin5 5`), `mp_test.py --clients 4`, **`five_suite.py` 61/61** (connexion, objets, une minute de jeu,
  mêmes nombres de carte dans les cinq jeux, nuit commune, deux joueurs à Vernis puis retour). Six fenêtres ne
  tiennent pas (2,4 Go chacune, 14,8 Go) ; à cinq il reste 1,6 Go. La règle « deux fenêtres au plus » est levée par
  cette demande pour ces essais.
- Faux rouges connus du banc : `pickup_suite` « pas de place nulle part » (la bourse a une fenêtre mémorisée dans
  `ElinMP/OwnSettings` depuis `bank_suite`, elle compte comme une place) ; `economy_suite` veut trois fenêtres.
- **Publiée ensuite : 0.26.548** (commit `fab31de`), avec tout ce qui précède. Depuis, non publié : réanimation
  d'un invité redemandée si elle reste sans réponse 10 s ou si la carte change de teneur (`CharaReviveEvent.WatchRevive`,
  compilé, pas joué) ; `five_suite` f6 (combat), f7 (l'host part), f8 (un invité coupe) écrits, **jamais joués
  jusqu'au bout** (arrêtés : l'utilisateur joue) ; `windows_suite` W5 corrigé (plus d'écran de choix), pas rejoué.
- **« Mes attributs ne montent pas »** (utilisateur, 2026-10-07, rôle et activité demandés, pas de journal) : audit
  du code, aucune cause permanente. Le jeu cache la barre d'expérience des attributs (`Element.ShowXP`). Pertes
  possibles trouvées : (1) l'host jetait les `ElementChangeDelta`/`CharaLevelDelta` d'un joueur en arrivée ou parti
  (corrigé : `ElinNetHostUpdate.OwnGrowth`, compilé, pas joué) ; (2) un invité chez un autre joueur n'envoie son
  personnage qu'à la sortie (plantage = gains perdus) ; (3) `CharaProgressCompleteDelta` 44-55 : tâche arrêtée avant
  la réponse de l'host = l'expérience de fin (repas, minage, artisanat) n'est pas jouée ; (4) pénalité de mort décidée
  avec les jours de l'host (`CharaReviveDelta` 64) : -500 d'expérience, une chance sur cinq par attribut, à chaque
  mort dans un monde de plus de 90 jours. Lignes à lire dans un journal : `Element 70..77 changed on chara` (invité),
  `Applying element 7x` (host).
- **Erreurs « guild_fighter2, 3, 4… » en tuant des monstres** (journal réel du 7 octobre, 0.26.548, invité) :
  `KeyNotFoundException` dans `Quest.source` depuis `QuestChangePhaseEvent.OnClientChangePhase`. Cause : un invité
  « prend note » d'une phase venue d'un autre jeu (`QuestChangePhaseDelta`) sans lâcher la tâche de la phase quittée
  (le jeu fait `task = null` après un pas) ; chaque mort rejouée (`CardDamageHpDelta` -> `OnKillChara`) ou chaque karma
  (`PlayerStandingDelta` -> `OnModKarma`) la « termine » de nouveau, `NextPhase` va vers une phase sans ligne, le
  journal lève avant `task = null`, et ça recommence à chaque monstre. Corrigé (compilé, **pas joué**) : la tâche est
  lâchée à l'arrivée de la phase ; `ChangePhase` refuse une phase sans ligne (host et invité) ; une quête déjà à une
  phase sans ligne est remise sur la dernière qu'elle a (`QuestPhaseRepair`, préfixe de `Quest.source`). À jouer :
  essai de la guilde des guerriers fait par l'host, l'invité tue ensuite des monstres. Les erreurs du mod sont au
  niveau Debug avec `@x` : chercher `"@x"` dans un journal, pas seulement Warning/Error.
- **Publiée : 0.26.557** (commit `e5db1f1`, non jouée) : guilde, lancer, réanimation, apprentissages à l'arrivée.
- **Jeu cassé en rejoignant l'host** (journal réel 0.26.557, 14:01:42, invité) : l'host descend à l'étage du boss puis
  remonte en 7 s ; l'invité, qui tenait l'étage, reçoit le monde, deux états de carte (boss puis étage), l'activation
  de l'étage : `Scene.Init` lève `IndexOutOfRange` dans `Point.cell` (personnage hors de la carte), puis une erreur
  par message reçu jusqu'à ce que le joueur quitte. Corrigé (compilé, **pas joué, pas publié**) dans
  `ElinNetClientZone.OnZoneActivateResponse` : le personnage est posé à la place donnée par l'host avant `Scene.Init`,
  et un `Scene.Init` qui lève replace le personnage et redemande la carte. Cause exacte de la mauvaise position non
  établie (copie du monde prise pendant le va-et-vient de l'host). Vus aussi, anciens : `Handed zone … while not in
  it`, `Zone … unknown here and could not be built` (`Region._OnDeserialized`, clé nulle), rattrapés tout seuls.
- **Publiée : 0.26.560** (invité mort hors carte). Depuis, non publié : garde `Region._OnDeserialized`, mesure des
  retours (conseil 11, `PLAN_conseil11_rechargements.md`), **codex partagé**.
- **« Les cartes du codex ne se cumulent pas »** (utilisateur, 2026-10-07) : le codex est dans `Player`, qu'un invité
  reçoit de l'host à chaque copie du monde ; ce qu'un invité collectait n'était compté que chez lui (ou chez l'host
  seulement si l'host a « collecter les cartes » coché) et repartait à la copie suivante. Corrigé (compilé, **pas
  joué**) : codex commun comme les recettes, `CodexDelta` (844, prochain libre 845 ; sortes : carte, tué, point
  faible, apparition, carte donnée), `CodexPatch`, accepté d'un joueur absent et reçu par lui ; l'host qui rejoue le
  ramassage d'un autre joueur n'applique plus son propre réglage de collecte (`CharaPickThingDelta`). Règle : ce
  qu'un seul jeu sait (carte, point faible lu, carte donnée, apparition) est dit à tous ; un monstre tué est compté
  par chaque jeu de la carte (le coup y est rejoué), le jeu qui tient la carte ne le dit qu'à ceux qui n'y sont pas
  (host -> absents ; absent -> host -> joueurs de la carte de l'host). Limites : un joueur seul ailleurs n'apprend
  les morts des autres cartes qu'à sa copie du monde suivante ; une figurine tirée du codex par un invité est un objet
  créé par un client (à vérifier au banc). À jouer : invité qui collecte, tue seul ailleurs, revient ; totaux égaux.
- **Publiée : 0.26.566** (codex commun, garde de région, mesure des retours). **Depuis, non publié et à ne PAS publier
  avant le banc** : « retour sur place » (conseil 11, tranche 1), règle `SoftRecall` n° 23, **décochée par défaut**,
  écrit par un agent, relu une fois, compilé, jamais lancé. Tout est dans `PLAN_retour_sur_place.md` (séquence des
  messages, 18 points à vérifier au banc, ce qui retombe sur la copie). Fichiers neufs : `Net/Host/ElinNetHostSoftRejoin.cs`,
  `Net/Client/ElinNetClientSoftRejoin.cs`, `Models/ZoneLease/ZoneSoftRejoin.cs`. Test : `floors_suite.py` (étapes
  « invité d'abord » vertes case cochée ; « host d'abord » = tranche 2, pas écrite). Prochaine règle libre : 24.
  Suspects relevés à la lecture, non touchés : `dateExpire`/`dateRegenerate` à `int.MaxValue` renvoyés à l'host par
  un invité qui a hérité d'une carte ; `PropagateZoneChangeState` sans vidage du tampon avant la carte ; aucun délai
  côté invité en attendant la copie du monde après un rendu de carte.
- **Banc du 7 octobre, 19h40 (Elin rendu)** : `floors_suite` case décochée = 4 copies du monde pour 4 étages ;
  `floors_suite --soft` (règle `SoftRecall` cochée) = **0 copie quand l'host rejoint l'invité**, 9 fois sur 9 sur
  trois passes (4, 8 puis 6 étages), sommes de carte égales, objets posés vus des deux côtés, déplacements vus, sacs
  inchangés ; restent rouges les étapes « host d'abord » (tranche 2, pas écrite). Le « +1 objet » d'une passe était
  un seau posé sur la case de l'escalier, ramassé à l'arrivée (test corrigé). Pas encore joué : repli forcé, dialogue
  ouvert, compagnons, troisième joueur, tâche en cours, ville, les 18 points de `PLAN_retour_sur_place.md`.
- **AutoAct** (Workshop 3370686923, demande du 7 octobre) : compatible pour un invité (`CharaTaskRemoteEvent.
  OnStartUnderFake`, `FakeTask.MarkReal`, `CharaProgressCompleteDelta`), `autoact_suite` 11/11, `guest_suite` 332/334.
- **Dynamic Riding** (Workshop 3548942723, demande du 7 octobre) : mod d'affichage seul, il marchait déjà (chaque
  jeu dessine la vraie monture de l'autre joueur, cheval, poulet, dragon, y compris après un aller-retour de carte :
  captures `dev/_shots/zoom-mp-dynride*.png`). Seul défaut trouvé : une exception par cavalier à chaque rechargement
  (`SpriteProvider.SetSpriteIdle`, table d'une seule image posée par le mod) ; garde `Patches/Compat/
  RideSpriteGuardPatch.cs`, 0 exception après deux allers-retours. Le décalage du dragon sous le cavalier vu de dos
  est celui du mod lui-même (pareil en solo, pas touché).
- **Tranche 2 des retours (l'invité rejoint la carte de l'host)** : écrite par un agent, relue, **jouée** :
  `floors_suite --soft --floors 6` = **0 copie du monde sur 6 étages**, 72/72 (4 copies règle décochée, 2 avec la
  tranche 1 seule). Détail et 21 points à jouer dans `PLAN_retour_sur_place.md`. Pas encore joué : règle décochée
  après ces retouches (`guest_suite`, `floors_suite` sans `--soft`), trois joueurs, compagnons, repli forcé.
- **Dynamic Riding, « la monture et le cavalier ne glissent pas à la même vitesse »** (utilisateur) : **pas
  reproduit**. Mesuré au banc (monture dragon, invité qui marche, 400 à 500 relevés par jeu) : écart des positions de
  rendu cavalier/monture nul chez l'host, écart des acteurs constant à ±0,03 chez les deux. Un correctif essayé
  (monture collée au cavalier, `SetFirst` à chaque image) ne changeait rien de mesurable : **retiré**. Piste non
  vérifiée : sur l'écran du cavalier lui-même, le joueur local glisse par le chemin « PC » de `CharaRenderer.Draw`
  (ligne 214, `MoveTowards`) et sa monture par le chemin « PNJ » (ligne 258) ; ce serait pareil en solo. À demander :
  qui le voit (le cavalier ou les autres), en marche continue ou par à-coups, option de déplacement fluide.
- **Liste des mods dans le dépôt** : `modlist.txt` (GitHub), fait, `depot_github_test` 77/77 ; suite demandée :
  charger les mods du dépôt quand on héberge ou rejoint, téléchargement sans abonnement « comme Civ 6 »
  (`PLAN_mods_de_l_host.md`, conseil 12 tenu).
- **Mods essayés à deux fenêtres le 7 octobre au soir** (tous chargés des deux côtés, jeu en anglais) : Quest Board
  Plus (3811305522 : textes anglais, s'affiche chez l'host et l'invité, 0 exception ; **l'utilisateur n'en veut pas**,
  c'est à lui de se désabonner) ; TpStackableSpellbook (3358087231 : deux livres de 3 et 5 charges ramassés par
  l'invité = un livre de 8 charges dans les deux jeux) ; KK Grid Status (3705093639 : affichage seul, 0 exception).
  Une fenêtre lancée avant la fin du téléchargement d'un mod avait 7 mods contre 8 : la connexion est passée.
- **Trouvé en passant, PAS corrigé** : après `Zone.UpdateQuests(true)` chez l'host (relance des quêtes d'une ville :
  expiration du jour, bouton « Reroll Quests »), l'invité garde les anciennes offres sur les habitants (26 contre 8 à
  Mysilia, dont 11 quêtes `main#0`) : `QuestCreateDelta` annonce les créations, rien n'annonce les retraits
  (`item.quest = null` dans `UpdateQuests`). À regarder avec les quêtes par joueur (`PersonalQuests`) avant de toucher.
- **Demande en cours** : que l'invité récupère tout seul les mods de l'host en rejoignant (`PLAN_profil_mods.md`,
  rien d'écrit) : recherche des faits lancée, conseil à réunir (question : redémarrage et consentement contre « le
  joueur n'a pas à réfléchir »).
- **Demande de l'utilisateur (2026-10-07, soir)** : « travailler sur des choses vraiment importantes » = ce chantier
  puis la reprise quand l'host part ; il ne libère pas encore Elin (« tu peux pas encore »).
- **À-coups de trois cases** : les journaux réels d'après la 0.26.532 n'en ont presque plus (2 et 0 « Reconcile force
  move » contre 57 à 239 avant) : c'était surtout les patchs retirés. Classé, à rouvrir si un journal le remontre.
- **Joueur refusé qui reçoit le monde entier** : plan écrit (`PLAN_journal_invite_6_octobre.md` §3 c), non fait : le
  teneur fantôme qui causait les refus est corrigé, le reste demande le jeu pour être prouvé.
- **Le jeu de ce PC** : dernière ligne de `MODLOG.md`. L'utilisateur joue : ni Elin ni `build.ps1` sans son accord.
- **Ensuite** : jouer `five_suite --only f6,f7,f8` ; suites à cinq plus dures (combat, donjon, échanges, départ de l'host) ; puis le bloc de 4h.

## État au 7 octobre 2026, 4h (à lire en premier)

- **Publiée : 0.26.540** (`887405a`). **Corrigé depuis, pas publié** (`ecd5d47` et le commit suivant) :
  - **un invité ne payait jamais une facture** déposée dans le coffre des impôts : son geste reprend à l'intérieur de la
    réponse à sa demande d'objet (`InvTransactionEvent` -> `ThingRequest.OnApply`, `IsApplying` vrai,
    `IsReplayingIntent` vrai) et `GuestPaysBillPatch` le prenait pour un écho. Test : `bills_suite` p1 rouge puis vert
    (51/53, les deux rouges restants sont du banc : politique 2705 non posée, `ElinNetClient` inaccessible à l'eval).
    Règle à retenir : dans un patch atteint par le geste d'un invité, tester `ElinDelta.IsRemoteStateLanding`, pas
    `IsApplying`.
  - même famille, trouvée par relecture, **compilée, pas jouée** : rune ou prise posée deux fois chez l'invité, plein
    de carburant joué deux fois (`InvOwnerModEvent`, `InvOwnerRefuelEvent`), facture payée en session de zone jamais
    annoncée à l'host (`GuestPaysBillPatch.OnPaid`). **Restent, non corrigés** : philtre d'amour ou insecte à rêves
    lâché dans le sac d'un PNJ (affinité perdue, l'objet revient : `CharaAffinityPatch` 30/37, `CardDestroyEvent` 42) ;
    vente d'un objet non identifié (reste non identifié chez l'host, `CardIdentifyEvent` 29).
  - ligne de journal « Guest sleep ended here by ... » chez l'host (`SleepSynchronizationContext.OnPcWake`).
- **Série n7 lue** (`dev/_shots/*-n7.log`) :
  - `time_suite` 64/65 : la règle « le temps ne saute que quand tous sautent » tient en jeu ; rouge = l'invité ne lit
    pas le message « votre voyage ne fait pas avancer la date » (W8b), à regarder.
  - `sleep_suite` 69/86 puis rejouée 5 fois : nuit à soi et nuit commune vertes. Dans la série n7 l'invité a été
    réveillé avant la fin de sa nuit deux fois (n1 après 3,5 s, n3 après 1,1 s), sans repos : **expliqué** : un bernard-l'ermite
    du monde de test a frappé l'invité endormi (un coup réveille, voulu) puis l'a tué ; mort, l'invité attend ses
    « derniers mots », d'où tous les NullReference de n5 à k1 et les délais y1/y2 (fautes de mise en place, pas du mod).
    À retenir : pendant les quelques secondes de sa nuit à soi un joueur est vulnérable, le monde continue. Les « interrompu : NullReference » de n5 à k1 et les
    délais y1/y2 ne sont pas lus. Rouge constant : n2, la date avance de 34 à 46 min pendant la nuit à soi de l'host
    (son jeu tourne vite tant qu'il dort), le test en veut moins de 30. Petite limite, pas corrigée.
  - `bank_suite` 56/86 : **faute du banc** (« bouton de la pile du sac absent » : l'or du personnage de test n'est
    pas une pile visible du sac). Le dépôt en banque d'un invité n'est donc toujours pas prouvé.
  - `resync_suite` : R2 rouge = le seau « disparu » est dans le sac de l'invité, pareil des deux côtés (pas de perte) ;
    R3 plante (trace Python). `place_suite` 32/34 (P4 : l'host n'a pas bougé, mise en place) ; `pickup_suite` 46/47
    (P3 : pas de case pour poser le caillou, mise en place).
- **Le jeu de ce PC** : voir la dernière ligne du journal (`MODLOG.md`) pour savoir si la 0.26.540 y a été remise.
- **Ensuite** : publier ces corrections (accord de l'utilisateur à demander) ; corriger le banc (`bank_suite` dépôt,
  `windows_suite` W5, `resync_suite` R2/R3) ; les deux gestes non corrigés ci-dessus ; puis la liste du bloc de 2h25.

## État au 7 octobre 2026, 2h25 (à lire en premier ; juste avant un compactage de la session)

- **Publiée : 0.26.540** (commit `887405a`, `feat/independent-travel` au même commit), non jouée à la publication :
  réglages de l'invité gardés à chaque carte et à la reconnexion (`Helper/OwnSettings.cs`, fichier local
  `ElinMP/OwnSettings`), lecture d'un invité plus figée quand l'host quitte la carte (`Helper/PendingOnHost.cs`),
  coffre d'expédition de l'host qui joue un personnage échangé (`Net/Host/ElinNetHostShipping.cs`, l'or dû est reversé
  à 5 h), bouton « Join » dans la liste des parties. Notes : `PLAN_fenetres_invite.md`, `PLAN_bloque_lecture.md`,
  `PLAN_expedition_host.md`.
- **Joué au banc après la publication** : connexion à deux fenêtres ; `windows_suite` **69/70** (seul rouge : W5 attend
  l'écran de choix du personnage, qui n'existe plus : test à corriger).
- **En cours au moment du compactage** : `bash _tools/run_short.sh n7 place_suite bank_suite pickup_suite resync_suite
  bills_suite sleep_suite time_suite` (journaux `dev/_shots/<suite>-n7.log`). À LIRE en premier à la reprise. Ces
  suites n'ont jamais tourné : un rouge peut venir du test.
- **Le jeu de ce PC contient le build de TEST (Debug)** : remettre la version publiée avant que l'utilisateur joue
  d'ici : `rm -rf <jeu>/Package/Mod_ElinTogether && cp -r dev/_release/ElinTogether-independance/Mod_ElinTogether <jeu>/Package/`.
  Steam tourne sur ce PC (relancé avec l'accord de l'utilisateur : « tu peux te servir d'elin »).
- **Retours notés, pas commencés** (`PLAN_retours_soiree_6_octobre.md`, fin du fichier) : objet qu'on ne peut pas
  prendre au clic gauche « avec certains arrivés » ; niveau des monstres de la base sur le joueur connecté de plus bas
  niveau. **À faire ensuite** : réanimation d'un invité quand l'host quitte la carte (`CharaReviveEvent.cs`, voir
  `PLAN_bloque_lecture.md`) ; joueur refusé par le teneur d'une carte qui reçoit le monde entier ; invités qui avancent
  par à-coups de 3 cases chez l'host ; la liste « à décider » de `PLAN_fenetres_invite.md` (réglages de jeu qui sont
  ceux de l'host chez un invité) ; jouer toutes les suites jamais lancées (liste plus bas).

## EN PAUSE le 7 octobre 2026, 0h30 (plus ancien)

- **Publiée : 0.26.532** (commit `b2b1490`, `feat/independent-travel` au même commit). Elle corrige la cause principale
  des désynchronisations, trouvée dans les journaux d'une vraie partie à quatre : en build Release, le mod retirait TOUS
  ses patchs dès qu'un composant réseau était détruit (`Net/Base/ElinNetBase.cs`, `OnDestroy`), donc à chaque fermeture
  d'une session de zone, alors que le lien avec l'host continuait. Le banc (Debug) ne peut pas le voir.
- **Retours de la 0.26.532** : deux journaux (un invité, l'host) propres : dix avertissements bénins au lieu de centaines.
- **Le jeu de ce PC contient la 0.26.532 publiée** (remise à la pause). Refaire `dev/build.ps1` avant tout test au banc.
- **Steam doit tourner sur ce PC pour le banc** (sinon `state` rend NullReferenceException). Ne PAS le relancer sans
  l'accord de l'utilisateur s'il joue ailleurs avec le même compte : cela peut couper sa partie.
- **Piège du banc** : `TaskStop` sur un `run_short.sh` ne tue pas ses enfants : tuer `bash.exe` et `python.exe` par PID,
  sinon l'ancienne série pilote les fenêtres de la suivante.
- **Commité APRÈS la release, pas publié, pas joué** (branche `fix/points-restants`, pas poussé) :
  - bouton « Join » sous chaque partie de la liste (`Components/Tabs/TabLobbyBrowser.cs`) ;
  - commit `ee7c1ee` « wip PARTIAL » : agents arrêtés en plein travail, à relire avant de s'y fier :
    1. fenêtres d'inventaire et d'aptitudes fermées à chaque changement de carte chez un invité (retour 20) :
       `Helper/OpenWindows.cs`, `Net/Client/ElinNetClientPlayer.cs`, `ElinNetClientZone.cs`,
       `dev/PLAN_fenetres_invite.md`, `dev/_tools/windows_suite.py` ;
    2. invité bloqué en lisant un livre quand l'host quitte la carte (retour 21 ; hypothèse : progression « retenue »
       en attente de l'host, jamais libérée au passage de main) : `Helper/PendingOnHost.cs`,
       `Patches/DeltaEvents/Chara/CharaProgressBeginEvent.cs`, `CharaTaskCancelEvent.cs` ; pas de notes écrites.
  - **Rien d'écrit** pour le retour 22 : coffre d'expédition de l'host « ne fonctionne pas » (LemiWinks). Hypothèse :
    l'host joue un personnage échangé par `TakeOverPc` (uid 582), traité comme un invité par l'expédition : ses ventes
    sont comptées « pour le joueur 582 » et le paiement cherche un pair. Journal de l'host : `Shipped 3 goods of player
    chara 582 for 95`, `Paid shipping of player Nardole: 1500` (d'où viennent ces 1500 ?), `Shipped 10 goods … 171`.
- **Journaux de vraies parties** (hors dépôt) : dossier `uploads` de la session Claude, fichiers `*Session_2026100*.log`.
  Analyses : `PLAN_journal_reel_6_octobre.md`, `PLAN_journal_desync_6_octobre.md`, `PLAN_journal_reel_placement.md`,
  `PLAN_journal_invite_6_octobre.md`, `PLAN_joueurs_invisibles.md`.
- **Tests joués le 6 au soir** : connexion à deux fenêtres ; `dummy_suite` 47/50 (3 rouges : endurance d'une copie) ;
  `place_suite` 24/27 (P4 défaut du test, P2 case d'arrivée de l'host). **Jamais lancées** : `pickup`, `resync`,
  `bank`, `bills`, `sleep` (n1-n6), `trio_sleep`, `time` (W7-W9), `desync`, `worldcopy`, `craft`, `windows`, `solo`,
  `travel` s19, `depot` D8, `hunt` d3b, `guest` G40/G41, `trio_place` q4/q5.
- **Reste à faire, dans l'ordre** : finir les trois retours ci-dessus ; jouer les suites ; un joueur refusé par le teneur
  d'une carte reçoit encore le monde entier (`PLAN_journal_invite_6_octobre.md`, défaut 3) ; invités qui avancent par
  à-coups de 3 cases chez l'host (`Reconcile force move`) ; GitHub qui répond 500 au dépôt (message vide, vérifier le
  nouvel essai) ; `CardGenDelta` d'un joueur dès `SendSaveProbe` (`PLAN_joueurs_invisibles.md` 3.1) ; contenu des
  coffres ; demande notée : niveau des monstres de la base sur le joueur connecté de plus bas niveau ; puis la reprise
  automatique quand l'host part (conseil 9, étapes 4 et 5).
- **À dire aux joueurs** : même liste de mods pour tous (`Visible Equipment` et `Somewhat Enhanced Display` manquaient
  chez deux joueurs ; `SourceThing` différent).

## État au 6 octobre, 22h30

- **Publiée : 0.26.524** (commit `2c98607`, Elin EA 23.352 Patch 1, `feat/independent-travel` poussée au même commit, branche de travail `fix/points-restants`).
  **Écrite, relue par l'agent relecteur, compilée en Release et en Debug, JAMAIS JOUÉE**, pas même par les suites :
  l'utilisateur jouait et a demandé de publier sans test. La 0.26.510 (19h50, testée au banc : trio_place 17/17, trio_time 25/25, passe à
  deux fenêtres presque verte) reste en ligne : si la 0.26.524 se passe mal, c'est le retour arrière. La 0.26.493 et la 0.26.494 sont encore en ligne aussi.
- **Le jeu de ce PC contient le build Release 0.26.524** (l'utilisateur peut l'essayer). **Refaire `powershell -ExecutionPolicy Bypass -File dev\build.ps1` (Debug) avant tout test au banc**, jeu fermé,
  et attendre quelques secondes après la fermeture (DLL tenue). Steam doit tourner sur ce PC, et le jeu ne démarre pas tant que le compte joue ailleurs.
- **Non commité dans l'arbre (autre session, vu à la fin de la rédaction de cette passation, rien de ma part)** : `Models/ZoneLease/ZoneLeaseGrant.cs`, `ZoneLeaseRelease.cs`, `Net/Client/ElinNetClientTravel.cs`, `Net/Host/ElinNetHostTravel.cs`, et un dossier neuf `Net/Handover/` (`WorldCopyPackets.cs`) : sans doute le début du conseil 9, étape 3 (l'host envoie son monde aux invités). Pas lu ici : lire `git diff` avant de décider, ne pas l'écraser. La 0.26.524 publiée ne l'a pas.
- Tout est dans `MODLOG.md` (entrée « de 18h à 22h30 »), avec fichiers, pièges et liste des suites. Mode d'emploi : `DOCUMENTATION.md`. Règles : `../CLAUDE.md`. Message de départ : `PROMPT_reprise.md`.
  Table des retours : `PLAN_retours_soiree_6_octobre.md` (lignes 1 à 18, colonne « État » à jour).

### La PREMIÈRE chose à faire quand Elin est libre : jouer les suites écrites à l'aveugle
Rien de la 0.26.524 n'est « fait » avant un vert lu. **Chaque rouge se lit avant de conclure : la suite peut être fausse** (elles ont été écrites sans jamais tourner).
Depuis `dev/`, `set PYTHONPATH=_tools/pylib`, `python _tools/mp_test.py` (host + 1 client) puis la suite (souvent avec `--reuse`, voir l'en-tête de chacune) ; les suites à trois fenêtres (`trio_*`) lancent
elles-mêmes `mp_test.py --clients 2` : les jouer SEULES, jeu fermé. Trois fenêtres : accord donné le 6 octobre, à reconfirmer si le PC est partagé. Ordre :
1. `desync_suite.py` (d1a, d1b, d4, d5a, d5b, puis d2 à trois fenêtres) : le cœur de « énormément de desync ». Journaux : `Replaying … held deltas`, `World and map … sent together`, `Refusing stale … only that player is told`.
2. `resync_suite.py` (r1 à r3) : détecteur et rechargement. **Premier doute : le faux positif sur une carte habitée** ; jouer r1, puis une vraie soirée avec la case AutoResync **décochée**, lire les lignes `Map checksum differs`, et seulement après la laisser cochée.
3. `travel_suite.py` (s18 la cave, s19a et s19b le boss).
4. `bank_suite.py` (B1 à B5, S1) : or perdu, priorité haute. B1 et B2 doivent être verts avant comme après ; sinon la cause n'est pas la seule.
5. `pickup_suite.py` (P1 à P3).
6. `sleep_suite.py` (n1 à n6, k1, puis la suite entière) ; 7. `trio_sleep_suite.py` (Q1 à Q3).
8. `time_suite.py` (W7, W7e, W8, W8b, W9 ; `TOGETHER_OFF=1` : W8, W8b, W9 doivent échouer comme avant ; W1 à W4 décrivent l'ancienne règle, à relire).
9. `trio_place_suite.py` ; 10. `trio_time_suite.py`.
11. `bills_suite.py` (c1 à c3, p1, p1h, p2) ; 12. `hunt_suite.py` d3b (ceinture et main : rouges attendus sans le correctif ; barre : verte, sinon défaut du mod).
13. `solo_suite.py` (Z0 à Z10) ; 14. `depot_suite.py` D8 (et D5b, D7 refaits pour la redirection).
Puis la passe large habituelle (`run_all.sh`, PC libre : `dev/_tools/idle.ps1`). Mesure : `perf_probe.py` autour de trio_place Q1 et Q2 ; `emp.desync` donne le coût du calcul des nombres.
Rouges connus d'avant, à ne pas confondre : `hunt2_suite` E3 (le test voulait l'ancienne règle du temps ; adapté, à rejouer), `council_suite` C5 (case atteignable, adaptée), `equal2_suite` E1 et `recruit_suite` R7 (vus une fois),
`guest_suite` G36 (laisse), `together_suite` T8 (exception de `CharaDieDelta`, intermittente), duel : PV du perdant pas toujours au maximum.

### Ce qui reste à faire (sections « pas fait » des plans)
- **Conseil 9, étapes 3 à 5** : l'host envoie son monde aux invités après chaque sauvegarde, reprise automatique quand l'host part ou plante, dépôt en bonus (`PLAN_conseil9_verdict.md`). « On pourra commencer une fois que tout le reste est bon. »
- **Désynchronisation** (`PLAN_desync*.md`) : réparer les sacs en écart (message neuf « voici ce personnage en entier », ~40 lignes) ; l'host doit vider sa file avant de copier la carte demandée (`ElinNetHostZone.cs`, `OnMapDataRequest`) ; passage de main d'un invité à un autre (même défaut que D2) ;
  D6 (aléatoire rejoué) et D9 (plages de numéros de 50 000) seulement si les journaux les montrent ; mesurer la taille réelle des messages et le gel de chaque copie de carte.
- **Date** : un invité ne fait jamais avancer la date (inégalité host/invité) ; quand tous marchent ensemble, seuls le sac et les délais de l'host vivent les heures ; l'avance rapide d'un joueur accélère encore le monde de tous ; la mer sur la carte du monde pour l'invité à côté de l'host.
- **Factures** : l'impôt sur la renommée la plus haute (`FACTION.GetFameTax`) ; `bill_debt` non couvert. **Banque** : deuxième étape (objet repris gardé « en attente » jusqu'à l'accusé de l'invité). **Rangement** : ligne « Alice a changé le rangement du coffre X ».
- **Solo** (`PLAN_joueur_seul.md`) : S8 (pile d'expédition, avec `CardAddThingEvent.cs`), S10 (`AreaWatch`), C1 à C8 ; M9 (copie de chaque carte créée sans destinataire).
- **Lenteurs** (`PLAN_lenteurs_corrections.md`) : compression rapide des cartes (A4a, la forte est gardée), A5, B5, B2, B1/B6, objet `perf` dans le pont de test.
- **Réveil de l'invité** : saignement, poison, miasme retirés au coucher pour l'host seulement ; livre ancien déchiffré non envoyé aux autres ; recette de bloc comptée deux fois (`AddRecipeEvent`) ; recette d'un invité parti seul n'arrive pas chez l'host.
- **Salon** : preuve du dépôt (HMAC) pour un joueur qui a la clé mais n'a jamais joué le monde ; deux comptes Steam pour essayer.
- Anciens restes : lignes 38 à 52 de `PLAN_chasse_differences_3.md`, G36 et T8 (`PLAN_enquete_t8_g36.md`), `PLAN_plusieurs_invites.md`, captures du README pas refaites, `showcase.py reconnect` jamais lancé, la copie `_lab` est restée en 23.352 (refaire `make_lab.py Elin2 2` avant une passe large).

### Questions ouvertes pour l'utilisateur
1. **Ses journaux de la soirée** : `Session_AAAAMMJJ.log` de l'host et d'au moins un invité (`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs\`), `Player.log`, taille du dossier de sauvegarde de l'host. Les cinq questions de `PLAN_desync.md` §5 (quoi était différent, quand ça commençait, toujours le même joueur, `emp.reconnect_self` répare-t-il).
2. **Quel donjon** était « conquis » à tort ; qui était à l'étage du boss en premier (host ou invité) ; **a-t-il vu « le boss s'enfuit »** ou un message de victoire avec coffre (`PLAN_donjon_conquis.md` §7).
3. **Les objets « disparus » sac plein sont-ils revenus en libérant des cases** et en rouvrant le sac ? (oui : la cause est la bonne ; il était sur la carte de l'host ou seul ailleurs ?)
4. **Retirer la 0.26.493 et la 0.26.494 de GitHub ?** (la 0.26.494 pouvait se tromper de personnage).
5. **Refaire une clé GitHub** (droit « Contents : Read and write ») et ressaisir le dépôt et la clé : ses réglages de dépôt ont été effacés par un test le 6 octobre.
6. Quelle cave (retour 9) ; dans quelle rangée de la barre étaient les objets du rangement (retour 4) ; un invité avait-il réglé un coffre ; les 1 500 orens déposés sont-ils dans la banque de l'host (sinon l'host les rend à la main).

### Cases host nouvelles et valeurs par défaut (`Emp/EmpConfig.cs`, `Net/NetSessionRules.cs`)
Toutes cochées (« true ») par défaut ; les décocher ramène l'ancien comportement tout de suite :
- **OwnSleep** (règle de session 17) : chacun dort pour soi, la nuit ne passe que si tous dorment.
- **TimeJumpsTogether** (règle 18) : la date ne saute que si tous voyagent ensemble sur la carte du monde.
- **DumpSparesBelt** (règle 19) : le rangement automatique épargne la main et la ceinture à outils.
- **AutoResync** (règle 20) : rechargement automatique de la carte en écart (au plus un par 30 s).
- Déjà là : AutoReconnect (règle 16, vraie), AutoSave (vraie), AutoHost (vraie), AskCharacter (**fausse**, réglage et non règle). **Prochaine clé de règle libre : 21.**
- Sans case : le host seul vit le jeu solo ; les joueurs connus du monde entrent sans être amis ; le dépôt ouvre la partie.

### Numéros de delta
Pris : **839** `BillPayDelta`, **840** `SleepStateDelta`, **842** `DesyncReportDelta`. **841 est libre.** (837 et 838 : duels.) Clé 9 du bail de zone : `MapSums`. Prochains à prendre : 841, puis 843.

### Pièges de ce soir (détail dans `MODLOG.md`)
Le build Release refuse ce que Debug accepte (`init` avec initialiseur sur un message MessagePack, référence nulle) ; un script Python passé à bash par un heredoc transforme `\\n` en vrai saut de ligne ;
Steam refuse un message de plus de 512 Ko et sa file d'envoi fait 512 Ko ; un préfixe Harmony qui rend `false` n'empêche pas les autres préfixes ; `Zone.Simulate` fait fuir le boss à toute entrée avec `visitCount > 0`.

## État au 6 octobre, 18h (dépassé par 22h30)

- **Publiée : 0.26.506.** L'utilisateur a joué le soir à trois joueurs ou plus et a rendu douze retours : ils sont dans
  `PLAN_retours_soiree_6_octobre.md` (ses mots, la cause, l'état). **Lire ce fichier en premier.** Il veut une nouvelle
  version dès que c'est vert (accord donné : « je veux faire une nouvelle release »).
- **GROS TRAVAIL NON COMMITÉ dans l'arbre, compilé en Debug et installé** (ne pas l'écraser) : les invités gardent leur
  case et arrivent par l'entrée (`ElinNetHostTravel.cs`, `ElinNetHostZone.cs`, `ElinNetClientTravel.cs`,
  `Models/ZoneLease/ZoneArrival.cs`) ; le temps d'un autre n'affame pas (`WorldDateAdvanceEvent.cs`,
  `WorldDateAdvanceDelta.cs`, `RemoteDecayPatch.cs`, `PersonalQuests.cs`) ; sommeil (familiers du dormeur seulement,
  `SimulateFaction` coupé chez un client, `SleepSynchronizationContext.cs`) ; musicien (`AIPlayMusicPatch.cs`) ; chargement
  rapide arrêté dans une partie à plusieurs (`GameSaveLoad.cs`) ; ancien personnage jamais sur une carte
  (`RemoveRemoteChara`, `RemoveUnplayedCharas`, `ZoneActivateEvent.cs`) ; cave jamais régénérée sous un joueur
  (`KeepAlive`, `LeasedZonePatch.cs`) ; étape 2 du conseil 9 (`Emp/EmpAutoHost.cs` : sauvegarde toutes les 2 minutes quand
  un autre joueur est là, session ouverte seule dans un monde déjà partagé, `IsSharedWorld`) ; redirection vers celui qui
  tient le monde du dépôt (`SaveDepot.cs`, `GitHubDepot.cs`, champ `join` du verrou, bouton « Join X »).
- **Mis de côté** : le réveil complet de l'invité (`_shots/reveil_invite.patch`, à reprendre : le tirage de recette de
  l'invité ne se fait pas, sa recette n'arrive pas chez l'host ; test `sleep_suite` K1 rouge tant que ce n'est pas remis).
- **Verts sur ce code** (`_shots/*-lot1.log`, `-lot3.log`) : witness 5/5, reconnect 46/46, autosave 18/18, leave 13/13,
  travel 83/83 (dont s18 la cave), time W6 (vie 17 -> 17), place P1 à P3, chara C1 à C5 sauf une interruption en fin de C5.
  Rouges qui sont les tests : place P4 (l'host ne s'éloigne pas, une boîte du jeu s'ouvre), time W7 et la fin de chara C5
  (NullReference dans le test). **Pas clair** : `sleep_suite` B3 (« l'invité n'attend plus le sommeil ») et Y2 joué après
  les autres étapes ; Y2 seul est vert.
- **En cours à 18h** (`_shots/*-lot4.log`) : `trio_place_suite` et `trio_time_suite` (TROIS fenêtres, accord donné :
  `mp_test.py --clients 2` puis la suite), sleep sans K1, dépôt dossier et GitHub avec la redirection (D5b, D7).
- **Pièges du jour** : Steam doit tourner sur ce PC (sinon « Steamworks is not initialized », le pont ne répond pas) et le
  jeu ne démarre pas tant que le compte Steam joue ailleurs ; `Zone.GetTopZone()` rend null pour la carte du monde (parent
  non zone) et ne remonte que d'un niveau ; retirer un joueur de `branch.members` fait rejouer tout `AddMemeber` à son
  retour (détruit les artefacts de dieu en double) ; la copie `_lab` est restée en 23.352 (le jeu est en Patch 1 : refaire
  `make_lab.py Elin2 2` avant une passe large).
- **Décisions à faire trancher par le conseil** (faits écrits) : horloge par joueur au-delà de l'urgence
  (`PLAN_horloge_par_joueur.md`) ; rangement automatique et ceinture, `autodump` par joueur (`PLAN_autodump_hotbar.md`) ;
  factures (`PLAN_factures.md`) ; nuit bloquée par un joueur, gels à plusieurs invités (`PLAN_plusieurs_invites.md`).
- **Ajout de 18h30, avant compactage de la session** : tout le travail de la soirée est maintenant COMMITÉ sur
  `fix/points-restants` dans un commit « wip » (PAS poussé, `feat/independent-travel` reste à la 0.26.506 + étape 1 du
  conseil 9) : rien n'y est « fait » tant que son test n'est pas vert, voir la table de `PLAN_retours_soiree_6_octobre.md`.
  Deux retours de plus : (13) un invité dépose 1500 orens à la banque, ferme, rouvre : disparus ; même symptôme pour le
  coffre d'expédition (conteneurs globaux hors carte) : agent lancé, faits et correction dans `PLAN_banque_invite.md`, test
  `bank_suite.py` (s'ils existent : le lire ; sinon relancer) ; (14) la redirection du dépôt (écrite).
  **Les suites à trois fenêtres n'ont JAMAIS tourné** : `trio_place_suite.py` et `trio_time_suite.py` lancent elles-mêmes
  `mp_test.py --clients 2` : les lancer SEULES, jeu fermé, sans `mp_test` avant (deux essais ratés pour cela). C'est la
  preuve qui manque pour la priorité de l'utilisateur (« les invités ne font que se faire tp sur l'host »).
  En cours au moment d'écrire : `_shots/sleep_suite-lot4.log`, `depot-folder-lot4.log`, `depot-github-lot4.log`.
- **À faire ensuite** : 1) lire lot4, corriger, passe réduite, publier ; 2) accepter dans le salon un joueur connu du
  monde même non ami Steam (`SteamNetLobbyManager.cs:383`) ; 3) le réveil de l'invité ; 4) étapes 3 à 5 du conseil 9 ;
  5) `PLAN_plusieurs_invites.md` (mesure `perf`, gels) ; 6) chasse 3.

## État au 6 octobre, 15h (dépassé)

- **Publiée : 0.26.506** (accord de l'utilisateur : « fais la release dès que tu peux »), compilée pour Elin EA 23.352. Elle
  contient : le jeu sait seul quel personnage est à qui (`45acadd`, `29c4fa5`, plan `PLAN_personnages_sans_question.md`),
  dix frictions (`f0da018`). Elle NE contient PAS l'étape 1 du conseil 9.
- **Dans l'arbre, PAS COMMITÉ, compilé et installé en Debug** : l'étape 1 du conseil 9 (verdict `PLAN_conseil9_verdict.md`) :
  retour automatique après coupure (`Net/NetReconnect.cs`, case `AutoReconnect`, règle 16), plus d'écran de choix du
  personnage à chaque connexion (clé `AskCharacter`), ligne quand la sauvegarde d'un invité est refusée, commandes de test
  `emp.cut_link`, `emp.link_timeout`. `reconnect_suite.py` R1 à R3 verts (retour en 28 s) ; lire la fin de
  `_shots/reconnect-v1.log` (R4, R5) et `_shots/*-e1.log` (chara, import, leave, version) avant de commiter. Pas joué : le
  salon Steam.
- **Règle de l'utilisateur (6 octobre)** : aucune question au joueur, aucune démarche ; le jeu décide seul. Elle passe avant
  un verdict de conseil. Les décisions de conception passent toujours par le conseil.
- **Passe large sur le code publié** (`_shots/*-v32.log`) : dépôt GitHub 36/36, recruit 45, quest 59, build2 58, equal2 35,
  hunt 135, hunt2 133, together 131, death 11, parity 15, sleep 32, instance 32, base 178, setting 35, unplayed 75, council
  30, tous verts ; duel 91/92 (PV du perdant pas toujours au maximum dans son jeu après un duel : défaut réel intermittent,
  course entre le soin de l'host et le dernier coup) ; travel 34/35 (S15, délai, déjà vu) ; guest 316/317 (laisse G36 : le
  chat n'est ni en combat ni empêché ; piste : un obstacle laissé par un test d'avant).
- **Piège** : `depot_suite` vidait les réglages de dépôt du joueur ; corrigé (elle les remet). Les siens ont été effacés :
  il doit ressaisir dépôt et clé (et refaire une clé GitHub avec « Contents : Read and write »).
- **À faire ensuite** : 1) finir et commiter l'étape 1 du conseil 9, puis ses étapes 2 à 5 ; 2) les lignes 38 à 52 de
  `PLAN_chasse_differences_3.md` (double paiement, artefact de dieu détruit d'abord) ; 3) les frictions du groupe B de
  `PLAN_sans_friction.md` qui restent ; 4) le soin après duel ; 5) G36 et l'exception de T8 (`PLAN_enquete_t8_g36.md`).

## État au 6 octobre, 2h (dépassé)

- **Publiée : 0.26.494** (remplace la 0.26.493, toujours en ligne : la retirer ? question posée à l'utilisateur). Le jeu de
  cette machine a le build de TEST (Debug) du dernier commit : `Installer.bat` du zip avant de jouer avec quelqu'un.
- **Passe large sur le code de la 0.26.494** (jeu relancé entre les suites, journaux `_shots/*-nuit*.log`) : trade 122/122,
  quest 59/59, recruit 45/45, build2 58/58, equal2 35/35, hunt 135/135, hunt2 133/133, death 11/11, parity 15/15, sleep
  32/32, instance 32/32, base 178/178, unplayed 75/75, version 8/8, leave 13/13, council 32/32, travel 54/54, together
  130/131 puis T12 seul 20/20, setting 34/35 puis S7 seul 12/12 deux fois, guest 314/317.
- **Rouges expliqués, c'étaient les tests (corrigés)** : T12 (le poids d'une récolte créée varie de 60 à 180 : le test
  n'en donnait pas toujours assez) ; S7 (la viande créée s'appelle parfois « corpse », le filtre du coffre dit « meat »).
- **Rouges PAS expliqués** : (1) `guest_suite` G36, la laisse : rouge dans la suite trois fois de suite (le chat ne suit
  pas l'invité, distance 5 ou 6 ; puis « détacher » sans effet), vert seul (21/21), et rouge autrement après g31-g34 (le
  détachement par l'host). Existait avant ce soir (`pub2`). À chercher : le chat est-il à côté au moment de détacher
  (`use_held` dit ce que le menu offrait), et pourquoi la laisse ne tire pas. (2) `together_suite` T8 : 9 fois
  « Exception at processing delta CharaDieDelta, NullReferenceException » dans le jeu de l'invité, une fois sur trois
  passages, déjà vue l'après-midi (`pub`) ; le test passe quand même ; la pile n'est pas gardée (relire
  `_shots/elin2-player.log` juste après un passage rouge).
- G36, lu dans le code (pas prouvé) : la règle de la laisse du mod (`GuestLeash.Follow`) est la même que celle du jeu
  (`Chara.cs`, déplacement du joueur) : pas de traction si le compagnon est en combat ou si « garder ses distances » est
  actif. Dans la suite, un test d'avant laisse sans doute le chat en combat ; « détacher » échoue ensuite parce que le
  menu n'offre rien à la case lue (« action absente, proposées : » vide). Piste : `IsInCombat` du chat au moment du rouge.
- **Essai de l'utilisateur, dépôt GitHub** : sa clé avait le droit de lire, pas d'écrire (GitHub : 403 « Resource not
  accessible by personal access token », il faut `contents=write`) ; le message du mod était juste. Il doit refaire une clé
  (celle-ci est passée dans la conversation). Le dépôt `elin-together-monde-essai` contient un monde de test.
- **À faire ensuite** : 1) G36 et l'exception de T8 ; 2) conseil 6 : copie du monde par Steam ; 3) reste de la chasse 2 ;
  4) duels : arène, pari, abandon ; 5) « Put this save in the depot » sur un dépôt qui a déjà un monde : que fait-il ?

## État à 22h45 (dépassé)

- **23h : la 0.26.494 remplace la 0.26.493** (accord de l'utilisateur) : les boîtes de saisie du dépôt, de la clé GitHub et
  de l'adresse coupaient le texte vers 22 caractères (trouvé par l'utilisateur en jeu) ; `characterLimit = 0` (`8eb5286`),
  compilé, pas rejoué au banc. Le jeu de cette machine a le build RELEASE 0.26.494 (l'utilisateur essaie lui-même) :
  **refaire `devuild.ps1` (Debug) avant tout test**. La 0.26.493 est toujours en ligne (la retirer : à lui demander).
- Piège : `make_release.ps1` ne marche pas si un Elin tourne ; `scratchpad/rel.ps1` de la session compilait dans un
  dossier à part (`-p:OutputPath=`) puis faisait le même zip.

- **Publiée : 0.26.493** (2026-10-05 au soir, à la demande de l'utilisateur : « commit tout et sort une release »),
  compilée pour Elin EA 23.352 = build Steam 25723206, qui est aussi la dernière « nightly » (vérifié sur les données
  publiques de Steam ; le jeu de cette machine est sur la branche nightly). Elle contient tout jusqu'au commit de cette note.
- **Depuis 21h30** : dépôt GitHub, fermer le jeu pendant un envoi (G4) : corrigé (`a577cfa`, 36/36) ; **monde qui change
  de main : celui qui le reprend joue SON personnage** (`0a254ca`, `Net/Host/ElinNetHostHandOver.cs`, `depot_suite` P1
  22/22 ; choisi sans conseil, option A de `PLAN_depot_personnage.md`). Limite : un monde hébergé pour la dernière fois
  par une ancienne version ne sait pas à qui est son personnage.
- **Pas rejoué avant la publication** : la passe large (`run_short.sh` complet, `travel_suite`). Rejoués sur le build
  final : base, duels, dépôt dossier et GitHub, puis trade 122/122 et quest 59/59 (arrêt des tests demandé par l'utilisateur avant recruit, setting, build2 ;
  `_shots/*-rel.log`). À faire après, PC libre.
- **Graphify** (demandé par l'utilisateur) : installé par lui (pipx, `~/.local/bin`), dossier `graphify-out/` hors git
  (`.git/info/exclude`) ; le code est analysé, la carte reste à finir.
- **À faire ensuite** : 1) passe large + `travel_suite` ; 2) conseil 6 : copie du monde par Steam ; 3) reste de la
  chasse 2 ; 4) duels : arène, pari, abandon.

## État à 21h30 (dépassé par 22h45)

- **Publiée : 0.26.463.** Arbre propre, tout commité et poussé. Le jeu de cette machine a le build de test (Debug).
- **Base gérée par un invité : commitée (`23041ef`).** Le rouge (servante retirée par l'invité) venait de la fenêtre des
  habitants de l'invité, mal redessinée à la réponse de l'host (tous les onglets listés dans la même liste : la ligne
  cachée, le clic suivant redevenait celui du jeu). `base_suite` : B1 à B11 verts ; B12 vert au passage d'avant (le
  dernier passage s'est arrêté en B12 sur un manque de mémoire du PC). **Piège trouvé** : `send_raw` de `base_suite`
  n'envoyait rien (`Delta` est un champ, pas une propriété) : les trois « l'host refuse quand même » étaient de faux
  verts ; réparé, avec un témoin (case décochée, le même envoi passe).
- **Duels, étapes 2 à 4 : commités (`e77ea83`).** Menu « Challenge to a duel », boîte oui/non, compte à rebours, duel
  sur place, personne ne meurt, les deux soignés ; case host `Duels` (règle 15, cochée) ; deltas 837, 838 (prochain :
  839). `duel_suite` 90/91 puis D3 seul 13/13 (le rouge était le test). Pas faits : arène, pari, bouton Abandonner.
  Pas joués : deux PC, sorts et flèches, trois joueurs.
- **Piège** : `build.ps1` lancé tout de suite après la fermeture du jeu peut ne rien installer (DLL encore tenue) sans
  le dire dans un `grep` : attendre quelques secondes et lire « 0 Erreur(s) ».
- **Le PC était plein (300 Mo libres, un autre jeu ouvert)** : pas de passe large ce soir.
- **À faire ensuite, dans l'ordre** : 1) dépôt : l'invité qui reprend le monde doit jouer SON personnage (`depot_suite`
  P1 rouge) ; 2) dépôt GitHub : fermer le jeu pendant un envoi (G4) ; 3) conseil 6 : copie du monde par Steam ;
  4) passe large (`run_short.sh` + `travel_suite`), PC libre, puis proposer une 0.26.49x ; 5) reste de la chasse 2.

## État à l'arrêt de 20h (dépassé par 21h30)

- **Publiée : 0.26.463** (Elin EA 23.352). Depuis : tout est commité et poussé jusqu'à `b7b8cc5` (mode construction de l'invité
  complet, terrain, zones, coffres, autel, résurrection, Kettle, outils, pas de mort entre joueurs, dépôt GitHub, docs).
- **NON COMMITÉ dans l'arbre de travail (ne pas l'écraser : `git status`, `git diff`)** : la base gérée par un invité
  (conseil 7 : servante, type / réserve / rappel / renvoi d'un résident, abandon et acte refusés à l'invité, case
  `HostManagesBase` clé 14, textes), avec les corrections de la relecture ; `dev/_tools/depot_suite.py` (étape P1). Ça
  compile et c'est INSTALLÉ dans le jeu (build Debug). Preuve rouge faite sur l'ancien build ; **vert pas encore lu**.
- **Lus à 20h20** : `travel_suite` **54/54** (le S15 rouge d'avant était un tirage) ; `base_suite` **176/177** sur la base
  gérée par un invité, un seul rouge : « l'invité retire la servante du même clic (réel) : host 508, invité 0 » (le
  retrait de la servante par l'invité n'arrive pas chez l'host : à corriger, puis commiter la base) ; `depot_suite`
  P1 (`_shots/depot-p1.log`) : **l'invité qui reprend le monde du dépôt joue le personnage de l'HOST** (Josdear, uid 1,
  son or, son sac), pas le sien (uid 469, resté sur la carte comme un personnage ordinaire) : l'angle mort du conseil 6
  est confirmé ; c'est la première chose à régler avant la copie du monde par Steam, et cela vaut aussi pour le dépôt
  GitHub et le dépôt dossier d'aujourd'hui.
- **Duels, étapes 2 à 4 : écrits, pas joués.** Patch `_shots/duels_2_4.patch` (compile ; fait sur le commit `b7b8cc5`, à
  appliquer avec `git apply --3way` APRÈS avoir commité la base), ses 12 textes dans `_shots/duels_2_4.textes.md`. Puis
  relecture, rouge, vert (`duel_suite.py` D1 à D6).
- **À faire ensuite, dans l'ordre** : 1) lire les trois journaux, corriger, commiter la base (un commit), pousser ;
  2) S15 du voyage ; 3) duels 2-4 (appliquer le patch, relecture, rouge puis vert) ; 4) dépôt GitHub : fermer le jeu
  pendant un envoi (G4 rouge) ; 5) conseil 6 : copie du monde chez chaque joueur par Steam (selon P1) ; 6) passe large
  (`run_short.sh` + `travel_suite`) puis proposer une 0.26.49x à l'utilisateur ; 7) reste de la deuxième chasse.
- **Consigne de l'utilisateur (20h)** : effort faible, moins de jetons : réponses courtes, peu d'agents.
- Ses dépôts GitHub sont tous privés sauf `elin-together` (fait à sa demande) ; dépôt d'essai `elin-together-monde-essai`.

## État à 19h30 (le plus récent : lire ceci d'abord ; tout le reste du fichier date de 14h15 à 17h et est marqué)

Fait d'après `git log 895d5b0..HEAD` et `git status` à 19h30. Ce qui n'est pas joué est écrit « pas joué ».

- **Version publiée : 0.26.463** (2026-10-05, 15h35, commit `895d5b0`, Elin EA 23.352,
  https://github.com/devmarcpro/elin-together/releases/tag/independance-0.26.463). **Rien de ce qui suit n'est dedans.**
  Le jeu de cette machine a un build de TEST plus récent : avant de jouer avec quelqu'un, `Installer.bat` du zip publié.
- **Branches** : `fix/points-restants` (courante) et `feat/independent-travel` sont toutes deux à `1d698a5`, qui est
  aussi `origin/feat/independent-travel` : **tout ce qui est commité est poussé**. 20 commits depuis `895d5b0`.
- **Pas commité (copie de travail à 19h30, 20 fichiers en index + 2 non indexés)** : la **base gérée par un invité**
  (conseil 7) : servante, type de résident, réserve, rappel, renvoi (`BaseRequestKind` `Maid`, `MemberType`, `Reserve`,
  `Recruit`, `Banish`, `RemoteResidentPatch.cs` nouveau), case `HostManagesBase` (règle de session 14, « seul l'host gère
  la base », décochée), `base_suite.py` agrandie, textes (`emp_localization.xlsx`, `SourceLocalization.json`). Écrit,
  **en test, pas joué à ma connaissance** : ne pas le commiter avant un test rouge puis vert. Je n'ai pas vérifié si R6
  (acte de propriété) et « abandon refusé à l'invité » y sont.
- **Fait, testé, poussé depuis la 0.26.463** (un test rouge vu d'abord quand le message du commit le dit) :

| Point | Commit | Test |
|---|---|---|
| Prière sans dieu non soignée ; jours et heures de l'invité sur la carte de l'host (aucun crochet d'heure ou de jour ne tournait en jeu normal) | `194c6d7` | `hunt2_suite` E4, E5, 29/29 |
| Prix d'expédition lu avec le dieu du joueur | `445fa5e` | **pas joué** |
| Carte à gratter du casino qui arrive à l'invité | `3459019` | **pas joué** |
| Mode construction de l'invité refusé avec un message avant de payer | `99c7353` | `build2_suite` G1 |
| `together_suite` T12 attend les récoltes chez l'invité (le rouge était le test) | `6b62659` | T12, 20/20 |
| Terrain qui suit : l'état de chaque case changée est envoyé par celui qui simule (`TileStateDelta`) | `1a25661` | `build2_suite` C3, C4 |
| Réglages de coffre de la base (priorité, pas de pourri, catégories, filtre, drapeaux, distribution), deux sens | `57d5d3e` | `setting_suite` S7, 35/35 |
| Duel d'autel : même résultat dans tous les jeux, artefact reforgé à côté de celui qui offre | `915e6dd` | `hunt2_suite` E6, 58/58 |
| **Mode construction de l'invité** (menu, miner, creuser, couper ; case `GuestBuild`, cochée) : `AgentTaskDelta` | `b2a6f16` | `build2_suite` 28/28 ; `build_suite` 19/19 |
| Outils et fouets (clé à molette, marque écolo, brosse, marteau, fouets) agissent sur le monde de l'host | `1a89eed` | `unplayed_suite` U8, U9, 26/26 |
| Résurrection d'un compagnon chez le barman (`CharaReviveRequestDelta`) | `cd7d652` | `hunt2_suite` E7, 26/26 (parchemin et sort : pas joués) |
| Copie chez Kettle et grimoire chez Demitas (`CopyShopDelta`) | `fccee72` | `hunt2_suite` E8, 140/140 pour la suite |
| Zones de base, outil de terrain (hauteurs), cases changées hors `Map.Set*` (toit miné, mur tourné, pousse, labour, arrosage) | `d04114c` | `build2_suite` C7 à C9, 58/58 |
| Un joueur ne peut plus tuer un autre joueur (case `PlayerKill`, décochée) | `ca8d009` | `duel_suite` P1, 10/10, deux sens |
| **Dépôt GitHub privé** pour garder le monde (`github:proprietaire/depot`, une clé) | `1d698a5` | `depot_github_test` 66/66 (faux GitHub, hors jeu) ; `depot_github_real` 13/13 (vrai GitHub, hors jeu) ; `DEPOT_GITHUB=1 depot_suite` 31/33 (faux GitHub, en jeu) ; dossier 13/13 |

  Le reste des 20 commits est de la documentation (`8fe1a8a`, `e88a0e0`, `7013bc8`, `2e23dd5`, `fe34335`).
  **Rouge connu (G4)** : fermer le jeu pendant un envoi vers GitHub n'attend pas la fin de l'envoi ; le verrou expire
  alors de lui-même après 3 minutes. Pas corrigé.
- **Les quatre patchs d'agents de 17h sont tous commités** : `ligne8.patch` = `cd7d652`, `ligne11.patch` = `1a89eed`,
  `etape7.patch` = `d04114c`, `depot_github.patch` = `1d698a5` ; la copie chez Kettle (ligne 9) = `fccee72`.
- **Suites larges sur le build de test (`run_short.sh pub2`, lancé à 17h)** : leur résultat n'est pas écrit dans mes
  sources (journaux `_shots/*-pub2.log`) : **à relire avant de proposer une version**. `travel_suite` seule reste à lancer.
- **Conseils rendus** (verdicts complets dans `MODLOG.md`) :
  - **5, mode construction de l'invité** : fait jusqu'à l'étape 7 (zones, terrain). Restent refusés avec un message
    (d'après `b2a6f16`, pas revérifié) : plans de construction, mode toit (Alt).
  - **6, où vit le monde partagé** : une copie chez chaque joueur par Steam par défaut, GitHub en option, Workshop
    écarté. **Pas commencé.** Première chose à faire, sans code : avec le dépôt « dossier » et deux fenêtres, vérifier que
    l'invité qui prend le monde joue SON personnage et pas celui de l'host (`SaveDepot.Take` puis `Game.Load`). Puis les six
    étapes (`world.version`, envoi du zip, héberger la copie, retour de l'ami, divergence, avertissement).
  - **7, duels et base gérée par un invité** : duels, étape 1 faite (`ca8d009`), **étapes 2 à 7 à faire** (menu
    « Défier », duel sur place, départ et déconnexion, invité contre aventurier, arène, pari) ; base : écrite, en test,
    pas commitée (voir plus haut). Le verdict parle d'un « plancher à 1 PV » : le code laisse le joueur à **0** point de vie.
- **Numéros pris** : deltas jusqu'à **835** (832 `CharaReviveRequestDelta`, 833 `TerrainHeightDelta`, 834 `AreaStateDelta`,
  835 `CopyShopDelta`) ; arguments de tâche jusqu'à **227** ; règles de session jusqu'à la **clé 14** (12 `AllowGuestBuild`,
  13 `AllowPlayerKill`, 14 `HostManagesBase` pas commité). Prochain delta : 836.
- **Dépôt privé d'essai** pour le dépôt GitHub : `devmarcpro/elin-together-monde-essai` (créé avec l'accord de
  l'utilisateur ; `depot_github_real.py` y écrit `lock.json` et `world.zip`).
- **Deuxième chasse aux différences** (`PLAN_chasse_differences_2.md`) : lignes 1 à 11, 25, 26, 30, 33, 34 corrigées ;
  restent 12 à 24, 27 à 29, 31, 32, 35, 37 ; la 36 est « à juger » (chaque jeu lit le dieu de son joueur, comme un
  joueur solo).
- **À faire ensuite (19h30)** : (1) lire les résultats `pub2`, lancer `travel_suite` seule ; (2) finir la base gérée par
  un invité (test rouge puis vert, relecture par `relecteur-elintogether`, commit, pousser) ; (3) conseil 6 : la
  vérification sans code du personnage de l'invité, puis l'étape 1 ; (4) duels, étape 2 ; (5) lignes restantes de la
  chasse 2 ; (6) **proposer à l'utilisateur une version 0.26.47x** quand `pub2` et `travel_suite` sont verts (ne pas
  publier sans son accord) ; (7) pousser `feat/independent-travel` après chaque lot validé.

- **Suites larges `run_short.sh pub2`** (17h → 18h05, build du commit `b2a6f16`, jeu relancé entre chaque suite) : recruit 45/45,
  quest 59/59, instance 32/32, trade 122/122, base 63/63, version 8/8, leave 13/13, equal2 35/35, hunt 135/135, together
  131/131, sleep 32/32 ; unplayed 67/75 (les 8 rouges = U8, U9, alors pas encore corrigés : verts depuis) ; guest 314/317
  (G36, la laisse : rejouée seule 21/21, c'était un tirage). **`travel_suite` : pas rejouée depuis la 0.26.442.**
  Rien de large n'a été rejoué sur les commits d'après `b2a6f16` (résurrection, Kettle, outils, zones, terrain, pas de
  mort entre joueurs, dépôt GitHub) : seulement leurs propres suites.
- Conseil 6, « l'invité qui prend le monde joue-t-il SON personnage » : **pas vérifié**.
- Pas de mort entre joueurs : le coup laisse la victime à **0** point de vie (c'est ce que fait le jeu pour « ne peut pas
  mourir », `EvadeDeath`) ; le « 1 PV » du verdict était une image.
- `DEPOT_GITHUB=1 depot_suite` 31/33 : les deux rouges sont G4 et sa suite (la reprise du monde, bloquée 3 minutes par le
  verrou resté pris).

## Où on en est (texte de 14h15 : dépassé par « État à 19h30 » ; gardé pour mémoire)

- **Le dossier de travail est `G:\ElinMods`** (C: était plein). `C:\Users\steamdeckwin\Documents\ElinMods` n'est plus
  qu'une suite de raccourcis vers G:. Seul `_lab` (les copies de test du jeu, des liens vers le jeu Steam) est resté
  sur C:. **Ouvrir la session depuis `G:\ElinMods`** : ouverte depuis C:, l'application demande une autorisation à
  chaque écriture.
- **Dernière version publiée : 0.26.442** (2026-10-05 vers 9h25, préversion `independance-0.26.442`, commit `f096255`,
  https://github.com/devmarcpro/elin-together/releases/tag/independance-0.26.442). Depuis : une douzaine de commits non
  publiés en version (`git log --oneline 2935741..HEAD`), tous poussés sur GitHub.
- **ELIN S'EST MIS À JOUR : EA 23.351 → EA 23.352** (Steam, 2026-10-05, `version.json` dit canal « Stable »).
  Conséquences : (1) les copies de test `_lab` pointent vers les anciens fichiers, la connexion est refusée (« Version
  mismatch … game 0.23.351.2 -> 0.23.352.0 ») : **refaire `python _tools/make_lab.py Elin2 2` après chaque mise à jour
  d'Elin** (fait pour Elin2) ; (2) le mod compilé contre 23.352 se charge sans erreur ; rejoué sur 23.352 : hunt D1
  8/8, together 128/133 puis T1–T2 19/19 (les rouges étaient des tirages), unplayed 51/53 ; (3) le code décompilé
  `_decomp` est celui de 23.351 : **à refaire avant de s'y fier** pour ce qui a changé ; (4) **la version publiée
  0.26.442 a été compilée pour 23.351** : à republier, compilée sur 23.352, quand l'utilisateur le voudra.
- **Le jeu de cette machine** a le build de test (Debug ou Release selon le dernier `build.ps1`) : `dev/build.ps1` avant
  tout test ; `Installer.bat` du zip avant de jouer avec quelqu'un.
- **Fait à 14h15, commit `ee374b7` : la barrière de version.** L'utilisateur (14h) : « rendre les futures versions du
  mod compatibles avec les futures versions d'Elin sans forcément le mettre à jour, ne pas avoir de barrière ». Le mod
  s'accroche au jeu par les noms de ses fonctions, il n'y a pas de verrou de version ; la seule vraie barrière était le
  refus de connexion quand deux joueurs n'ont pas la même version d'Elin (quatre contrôles : clé de connexion Steam,
  filtre des salons, poignée de main côté client, côté host). Maintenant : seule la version du MOD doit être la même ;
  une version d'Elin différente = les joueurs sont prévenus ; une case côté host (onglet de configuration) redemande
  la même version d'Elin. Testé : `version_suite.py` 8/8 en connexion locale ; **le chemin par le salon Steam utilise
  le même contrôle, pas joué**. Fichiers : `Common/BuildVersionIntegrity.cs`, `Net/Client/ElinNetClientValidator.cs`,
  `Net/Host/ElinNetHostIntegrity.cs`, `Emp/EmpConfig.cs`, `Components/Tabs/TabServerConfiguration.cs`, les textes.
  La 0.26.442 publiée n'a pas ce changement : elle refusera toujours deux versions d'Elin différentes.
- **Branches** : `fix/points-restants` (branche courante, **la branche de travail**) et `feat/independent-travel` sont
  au **même commit** (`ee374b7`) ; `feat/independent-travel` est **poussée sur GitHub**.
  `wip/lots-non-compiles` est très en retard, gardée, pas supprimée.
- **Habitude demandée par l'utilisateur** : **pousser `feat/independent-travel` après chaque lot validé** (l'avancer sur
  `fix/points-restants` sans changer de branche courante, puis `git push origin feat/independent-travel`). **Publier
  une nouvelle version demande toujours son accord.** Ne jamais pousser sur `upstream`.
- Consignes de l'utilisateur (4 octobre au soir) : **aucune différence entre un joueur host et un joueur invité,
  tout doit être fluide, tous doivent pouvoir tout faire** ; travailler en continu sans s'arrêter ni demander
  d'autorisation (« j'autorise tout ») ; autant d'agents que nécessaire ; les décisions de conception sont tranchées
  par le skill `llm-council` (critères dans l'ordre : l'invité obtient ce qu'un solo obtiendrait ; pas de
  duplication ni de perte ; le plus petit changement ; aucun risque pour les sauvegardes).

## Fait et testé depuis la 0.26.442 (état de 14h15 ; la suite est dans « État à 19h30 »)

| Point | Commit | Test |
|---|---|---|
| Monture déjà prise refusée à un second cavalier | `31faaac` | `unplayed_suite` U6 vert |
| Notes, étiquettes de vente, lits (qui le tient, son type) : réglés par un joueur, vus par l'autre, deux sens | `eccc52a` | `setting_suite` S1–S3 |
| Recherche et compétences du foyer d'un invité : vraies demandes à l'host (il vérifie, paie une fois ; l'état de la base revient chez les joueurs) ; la recherche faite par l'host arrive chez l'invité | `b559952` | `base_suite` B1 20/20, B4 |
| « Ne pas vagabonder » propre à chaque joueur (en plus de « garder ses distances ») | `0b48902` | `hunt_suite` D14, 17/17 |
| Politiques de la base, deux sens | `e3b4de3` | `setting_suite` S4 (vraie fenêtre, clic), 20/20 |
| Nom de la base, de la faction, d'un téléporteur, deux sens | `ed99a6b` | `setting_suite` S5, S6, 25/25 (nom de faction non joué) |
| **Vrai défaut** : le don d'un objet pris dans une pile par un invité n'arrivait jamais chez l'host (objet non consommé, don sans effet) ; l'host annulait aussi le massage lancé par le jeu de l'invité | `7cd9db2` | `unplayed_suite` U1, U3, U5 (deux acheteurs : un exemplaire, un payeur), U6 |
| Quêtes à donjon à deux, sens invité : RÉCOLTE et MUSIQUE ouvertes (ce que livre l'un ou l'autre compte pour le preneur, même poids affiché, fouille des deux sacs, une récompense ; « tout livrer » passe par le même chemin qu'un dépôt) | `af18078` | `together_suite` T12, T13 |
| Deuxième chasse aux différences (37 lignes lues dans le code, rien de joué) | `e8dbc47` | |
| Barrière de version : seul le mod doit avoir la même version ; Elin différent = avertissement ; case de l'host pour le contrôle strict | `ee374b7` | `version_suite` 8/8 (connexion locale ; salon Steam non joué) |

Avant 9h30, déjà dans la 0.26.442 : mort après le jour 90, prime de guilde, cadeaux du dieu, pièges, grimoires,
bénédiction, autels, abattage, appel à l'aide, dieu quitté, source chaude, gestes tenus en main (G33–G39), quêtes à
donjon à deux dans les deux sens (subjuguer), chasse aux différences D1 à D14, échange plus strict, consigne « ne pas
s'éloigner » (détail : `MODLOG.md`).

Non-régression de la 0.26.442 (jeu relancé entre chaque suite) : equal2 35/35, together 107/107, death 11/11, parity
15/15, sleep 32/32, recruit 45/45, quest 59/59, instance 32/32, trade 122/122, hunt D1–D14, base 53/53, guest 317/317,
leave 13/13, travel 54/54, council vert. Sur 23.352, depuis : seulement hunt D1, together T1–T2 et unplayed.

Constats : les étapes de dialogue « acheter des plans » et « améliorer le foyer » n'existent dans aucun dialogue du jeu
installé ; un joueur peut « monter » un autre joueur sur la même case (comportement du mod d'origine, pas jugé).

**Pas joués par le banc** (`unplayed_suite`, seulement avec `--only`) : U2 bouton partagé d'un coffre (bouton
introuvable), U4 parchemin d'alias (aucun dans les données du jeu), U7 eau profonde (l'eau du banc n'étouffe personne).

## PAS JOUÉ (à dire tel quel ; liste de 14h15, complétée à 19h30 par les derniers points)

**Ajouté à 19h30 (depuis la 0.26.463) :**

- **Rien de ce qui est nouveau n'a été joué à deux PC** (mode construction, terrain, zones, coffres, résurrection, Kettle,
  outils, `PlayerKill`, dépôt GitHub).
- **Mode construction de l'invité** : pas joués : objet du stock ou du sac posé par le menu, pont, glisser sur plusieurs
  cases, creuser, mode rampe, la case `GuestBuild` décochée, une carte tenue par un invité. Plans de construction et mode
  toit : refusés avec un message (pas revérifié). Le banc choisit le mode et la recette par l'appel du bouton, pas à la souris.
- **Terrain** : pas couverts : récolte (seule la marque est jouée), sol tourné ; l'outil de terrain est joué par un coup,
  pas par un glisser bouton enfoncé.
- **Réglages de coffre** : la boîte du filtre, le collage et les boutons d'autodump ne sont pas joués.
- **Duel d'autel** : le glisser à la souris est remplacé par le dépôt ; un pair d'une ancienne version (graine absente)
  n'est pas essayé. **Résurrection** : parchemin et sort pas joués. **Outils et fouets** : tentes et nouvelle fiche des
  fouets « passe-temps » et « métier » chez l'invité pas couverts. **Prix d'expédition** (`445fa5e`) et **carte à gratter**
  (`3459019`) : jamais joués.
- **Un joueur ne tue pas un joueur** : saignement, poison, feu, condamnation à mort pas couverts ; sorts et projectiles
  pas joués ; le test utilise le coup de mêlée du jeu (Maj + clic).
- **Dépôt GitHub** : prouvé hors jeu (faux et vrai GitHub) et en jeu contre le faux GitHub ; **pas joué** : le vrai
  GitHub depuis le jeu (TLS de Mono, première demande d'environ 7 s, limite de débit), deux PC, la fermeture brutale du
  jeu pendant un envoi, un dépôt tout à fait vide sur le vrai GitHub, la clé expirée, le texte d'aide suivi avec une vraie
  clé, la croissance du dépôt (72 Mo par soirée : un calcul). **Rouge connu (G4)** : fermer le jeu pendant un envoi
  n'attend pas la fin ; le verrou expire après 3 minutes.
- **Base gérée par un invité** : écrite, en test, pas commitée ; rien de joué.
- Suites larges sur le build de test (`pub2`) : résultat non consigné ici. `shared_suite`, `trio_suite`,
  `companion_suite`, suites du serveur : non relancées.

**Liste de 14h15 (toujours vraie sauf ce qui est dit plus haut) :**

- **Corrigé dans le code, aucun test ne le prouve** : karma d'un visiteur chez un teneur de carte (`927f342`) ; noyade
  en eau profonde (`cf62040`, U7 saute) ; fenêtres d'alias, de retour du vide et de caisse de ferme (`2239dde`, U4
  saute) ; carte au trésor d'un invité sur la carte du monde (`4b45541`, `council_suite --only c6` à refaire) ; la
  retenue de « ne pas vagabonder » elle-même (un ennemi hors de vue du joueur) ; le nom de faction ; le score d'un
  concert de la quête de musique joué par l'host.
- **Deuxième chasse** : les 37 lignes de `PLAN_chasse_differences_2.md` sont lues dans le code, aucune n'est jouée.
- **Rien de ce qui est nouveau depuis la 0.26.442 n'a été joué à deux PC**, ni la 0.26.442 elle-même. Pour
  l'utilisateur : tout le point 1 de sa liste d'essais (deuxième joueur par Steam, hébergeur qui part, mode avec Elin
  entre deux PC, Internet avec mot de passe).
- Suites non relancées sur 23.352 : presque toutes (sauf hunt D1, together T1–T2, unplayed) ; `shared_suite`,
  `trio_suite` (trois fenêtres), `companion_suite` et les suites du serveur : non relancées depuis avant la 0.26.442.
  `run_short.sh` ne lance pas `travel_suite` ni `shared_suite`.
- Gestes tenus en main : pas comparés entre les deux jeux, les effets du puits sur le potentiel et les mutations ;
  pas de test d'un refus ; la portée de 2 cases ne regarde pas les murs.
- Quêtes à donjon à deux : les tests prennent la quête, tuent et sortent par les appels du jeu, pas par le dialogue ni
  en marchant ; pas de test pour « pas de boîte si l'autre a déjà une quête à donjon ou un échange » ; pas de test de
  déconnexion dans la zone ; trois joueurs pas essayé ; la boîte reste ouverte si la connexion tombe ; `instance_suite`
  et le bot attendent 15 s à chaque entrée. **La défense reste en solo pour l'invité** (cor, vagues et prime tenus par
  celui qui simule).
- Chasse 1, pas joués : le pinceau, le vol à la tire (l'host peut encore avancer vers la victime), investir dans une
  ville, les runes d'arme à distance, un refus de rune, le vrai glisser dans la fenêtre de rune, le parchemin de retour.
- Limites connues : sur une lecture ratée par un invité, ni confusion ni monstres ; un piège d'acide ou de malédiction
  n'abîme l'équipement que dans le jeu de l'invité ; un invité qui prie seul en voyage puis chez l'host pourrait
  recevoir un cadeau deux fois ; l'or perdu à la mort est ramassable par n'importe quel joueur ; les jours passés avec
  son dieu ne sont comptés que dans le jeu de l'invité ; la colère du dieu quitté est au tarif de base chez l'host.
  Réglages de la base encore locaux à l'écran de l'invité : servante, type et réserve d'un résident, réglages de coffre.

## À faire ensuite, dans l'ordre (liste de 14h15 : la version de 19h30 est dans le premier bloc ; ici les points 2 et 3 sont en partie faits)

1. **Barrière de version : la jouer.** Elle est faite et testée en local (`ee374b7`). Reste : la regarder en vrai
   (deux PC, deux versions d'Elin, par le salon Steam), vérifier le texte de l'avertissement et la case de l'host, et
   que la version du MOD, elle, refuse toujours clairement. Rien d'autre à écrire tant que ce n'est pas essayé.
2. **Republier une version compilée sur 23.352** (elle contiendra la barrière de version), **avec l'accord de
   l'utilisateur** : `dev\make_release.ps1`, note de version, README. Avant : relancer les suites larges sur 23.352
   (`run_short.sh`, puis `travel_suite` et `shared_suite` seules), refaire `_decomp` pour 23.352.
3. **Étape E = `PLAN_chasse_differences_2.md`**, en commençant par les lignes **hautes** : 1 (mode construction d'un
   invité : il paie, rien ne se construit chez l'host) et 2 (tailler un rondin à la hache : `TaskChopWoodArgs`). Puis
   les « sûr » : 6 (nourriture du sac de l'invité qui ne pourrit jamais), 25 (prière sans dieu), 26 (prix d'expédition),
   30 (carte à gratter du casino), 33 (jours, relance des quêtes), 36 (Mifu, Nefu, Aquli) ; puis 5 (prière qui ne
   soigne que l'invité), 8 (résurrection d'un compagnon), 11, 28, 29… Un test rouge puis vert par ligne, dans
   `hunt_suite.py` (prochain numéro : D15) ou `unplayed_suite.py`. Cocher l'état dans le plan.
4. **Ce qui reste du conseil 4** : servante, type et réserve d'un résident, réglages de coffre (ligne 7 de la deuxième
   chasse), **mesurer le rechargement de l'invité au retour de l'host** pendant la soirée d'essai (n'alléger qu'au-delà
   de 5 s).
5. **Défense à deux** (quêtes à donjon, sens invité) : le cor, les vagues et la prime sont tenus par celui qui simule ;
   gros, à décider par le conseil.
6. **Première chasse, ce qui reste** (`PLAN_chasse_differences.md`) : 8 (machine à gènes), 17 (habitants qui ne
   remarquent que l'host : conseil), 25 à 28, tombe d'épée (21). **Étape D, ce qui reste** : mutation en double avec un
   équipement d'éther ; serveur (relais sans coupure, personnage planté à la base, rôle du gardien du monde, mot de
   passe en clair).
7. Après chaque lot validé : pousser `feat/independent-travel`. Quand un ensemble est vert : passe large, puis proposer
   une nouvelle version à l'utilisateur (ne pas publier sans son accord).

## Liste d'essais de l'utilisateur (à deux vrais joueurs) — mise à jour 19h30 : points 10 à 18 ajoutés en fin de liste

Un seul point par ligne, dans cet ordre :

1. Un deuxième joueur qui rejoint par Steam ; l'hébergeur qui part ; le mode avec Elin entre deux PC ; Internet avec
   mot de passe.
2. Quêtes à donjon à deux, **dans les deux sens** : l'host prend une quête à donjon, l'invité répond Oui à la boîte,
   puis une fois Non ; l'invité prend une quête « subjuguer », « récolte » ou « musique », l'host répond Oui, puis une
   fois Non.
3. **Le temps de rechargement de l'invité quand l'host revient sur sa carte** (à chronométrer).
4. **La carte au trésor**, lue puis creusée par l'invité sur la carte du monde, avec l'host.
5. Tout ce qui est PAS JOUÉ : karma d'un visiteur chez un invité (les gardes le voient-ils ?), tri du sac (celui de
   l'autre ne change pas), « déjà vendu » à l'achat au même instant, message qui nomme l'host avant le rechargement,
   ticket d'hôtesse, fenêtres d'alias / retour du vide / caisse de ferme, eau profonde, vol à la tire, investir dans une
   ville, pinceau, runes d'arme à distance, concert d'une quête de musique.
6. L'invité règle la base : recherche et compétences du foyer (payé une fois, résultat visible chez l'host), politiques,
   lit, étiquette de vente, note, nom de la base et d'un téléporteur : l'autre joueur doit le voir.
7. Un échange : un objet équipé, un sac plein, un objet qu'on ne peut pas lâcher.
8. Un invité qui offre un objet pris dans une pile (le don arrive chez l'host) ; une monture déjà prise.
9. Deux joueurs sur une version d'Elin différente (barrière de version, `ee374b7`) : l'avertissement, la case de
   l'host, et un mod de version différente qui reste refusé.
10. **Construire dans la base de l'host** (invité) : un sol, un mur, un meuble neuf du menu, miner, couper ; l'or est
    pris une fois, ce qui est construit se voit chez l'host tout de suite. Puis l'inverse : l'host construit, l'invité
    le voit sans changer de carte. Ensuite, avec la case « Other players can use build mode » décochée : un message, rien
    n'est payé.
11. **Zones et outil de terrain** : l'invité dessine une zone de stockage, la renomme, l'efface ; il monte et baisse le
    terrain ; l'host voit la même chose, et dans l'autre sens.
12. **Réglages de coffre** : l'invité règle la priorité et « pas de pourri » d'un coffre de la base ; l'host les voit ; ses
    habitants rangent en en tenant compte.
13. **Résurrection d'un compagnon chez le barman** (invité) : l'or part une fois, le compagnon se relève à côté de
    l'invité, toujours à lui. Essayer aussi un parchemin (pas joué).
14. **Copie chez Kettle** (invité) : laisser un objet, voir la copie en vente, reprendre l'objet.
15. **Clé à molette** sur un coffre par l'invité (le coffre grandit chez l'host aussi), fouet-œuf sur un animal.
16. **Se frapper sans se tuer** : un joueur frappe l'autre jusqu'à 0 point de vie (Maj + clic) : personne ne meurt ; puis
    avec la case « les joueurs peuvent se tuer » cochée : la mort a lieu comme avant. Essayer aussi un sort et une flèche
    (pas joués).
17. **Dépôt GitHub avec une vraie clé** : créer un dépôt privé et la clé en suivant seulement l'aide du mod (onglet
    « Client Settings », quatre étapes), la donner à l'ami, prendre le monde, jouer, quitter, que l'ami reprenne. Vérifier
    que le jeu ne se fige pas pendant un envoi et que la clé n'est visible nulle part dans le jeu.
18. **Fermer le jeu pendant un envoi vers GitHub** (rouge connu G4) : voir si l'ami peut reprendre le monde tout de suite
    ou seulement après 3 minutes, et si la dernière sauvegarde est là.

## Questions qui restent pour l'utilisateur (de 14h15 ; voir aussi 19h30)

- Sa soirée d'essai (liste ci-dessus), et l'essai de la carte au trésor à deux.
- **Republier maintenant une version compilée sur 23.352 ?** (la 0.26.442 est compilée pour 23.351 ; elle marche
  sans doute, mais deux joueurs sur deux versions d'Elin se verraient refuser la connexion.)
- La barrière de version (`ee374b7`) : est-ce bien ce qu'il voulait (Elin différent = avertissement, case côté host
  pour le contrôle strict) ? Faut-il aussi laisser passer un mod d'une autre version ?
- Quel mod fournit les quêtes `dmp_quest_*`.

## Aide-mémoire

```
powershell -ExecutionPolicy Bypass -File dev\build.ps1
cd dev && set PYTHONPATH=_tools/pylib
python _tools/make_lab.py Elin2 2              # APRÈS CHAQUE MISE À JOUR D'ELIN (sinon connexion refusée)
python _tools/mp_test.py                       # host + 1 client ; peut rester à « connexion demandée » : relancer
python _tools/council_suite.py                 # les décisions du conseil (C6 : --only c6, fenêtres neuves)
python _tools/guest_suite.py --only g31,g32    # ou g33 à g39 (gestes tenus en main)
python _tools/equal2_suite.py                  # abattage, appel à l'aide, dieu quitté, source chaude
python _tools/together_suite.py                # quêtes à donjon à deux, les deux sens (T1 à T13, ~20 min)
python _tools/hunt_suite.py                    # chasse aux différences host / invité (D1 à D14 ; --only d1,d3)
python _tools/base_suite.py                    # base réglée par un invité (recherche, foyer : B1, B4…)
python _tools/setting_suite.py                 # notes, étiquettes, lits, politiques, noms (S1 à S6, 25 vérifs)
python _tools/unplayed_suite.py                # corrections jamais jouées (U1, U3, U5, U6 ; U2, U4, U7 : --only)
python _tools/trade_suite.py                   # échange, dont les refus R6 à R11
python _tools/version_suite.py                 # barrière de version (8 vérifications, connexion locale)
python _tools/hunt2_suite.py                   # deuxième chasse (E1 à E8 ; --only e7,e8)
python _tools/build2_suite.py                  # mode construction à deux, terrain, zones (G1, C1 à C9)
python _tools/duel_suite.py                    # un joueur ne tue pas l'autre (P1)
python _tools/depot_github_test.py             # dépôt GitHub contre le faux GitHub, sans le jeu (66 vérifications)
python _tools/depot_github_real.py proprietaire/depot   # contre le VRAI GitHub, dépôt privé d'essai seulement
DEPOT_GITHUB=1 python _tools/depot_suite.py    # en jeu contre le faux GitHub (~10 min ; 31/33, G4 rouge)
bash _tools/run_short.sh <nom> death_suite guest_suite parity_suite sleep_suite recruit_suite
git push origin feat/independent-travel        # après chaque lot validé, une fois la branche avancée
```

`run_short.sh <nom> suite1 suite2…` relance le jeu entre deux suites (journaux `_shots/<suite>-<nom>.log`) : c'est la
façon de faire la non-régression ; il ne sait pas lancer `travel_suite` ni `shared_suite` (elles lancent elles-mêmes le
jeu : les lancer seules, jeu fermé).

Pièges du 5 octobre (après-midi) : la panne de mémoire du banc (« OutOfMemoryException » du pont) revient après ~30
minutes de tests sur les mêmes fenêtres : relancer le jeu entre les grandes suites ; `mp_test.py` peut rester bloqué à
« connexion demandée » (relancer) ; le menu contextuel « buy » du jeu se referme sans souris dessus (le test le
reconstruit à l'identique) ; ne pas lancer `Stop-Process` par bash avec `\$_` (ça ne tue rien) : `taskkill /PID <n> /F`
depuis PowerShell ; un test qui dépend d'un tirage peut échouer une fois (monstre non tué en 40 coups, vérification
faite trop tôt : relancer avant de croire à un défaut) ; après une mise à jour d'Elin, `make_lab.py` d'abord.

Pièges du matin du 5 octobre : le « Yes. » des boîtes du jeu a un point (chercher par `StartsWith`) ; une fenêtre Elin
peut rester après `Stop-Process` : vérifier, puis `taskkill /PID <n> /F` ; D3 : la matière d'un seau est tirée au hasard
et le coffre ne prend que ce qui s'empile (le test copie les mêmes seaux).

Pièges de la nuit : ne pas compiler pendant qu'un agent écrit dans le même dossier (son travail à moitié
fini part dans la DLL : compiler depuis un worktree propre, `git worktree add`) ; une zone créée par l'host « sans
annonce » n'est jamais connue du client (« Remote zone does not exist… », puis « invalid zone ») ; `ModCurrency` chez
un client est une demande (sa bourse ne baisse qu'à la réponse de l'host : pas pour savoir « a-t-il payé ») ; ce que
fait l'host en appliquant le tick d'un autre joueur n'est pas envoyé (il faut `ElinDelta.Simulate()`) ; le banc sait
dérouler un vrai dialogue (`talk`, `pick`, `hang_up` dans `hunt_suite.py`, choix cliqués par leur texte anglais) ;
le gel occasionnel de la fenêtre host au chargement existe déjà (noté dans `mp_test.py`), ce n'est pas le code testé.
`new ActPray()` n'a pas d'identifiant (prendre `ACT.Create(6050)`) ; sur la carte du monde on
creuse sous ses pieds, `Teleport` n'y bouge pas un invité (`MoveImmediate` oui), y marcher peut déclencher une
rencontre ; quand l'host quitte une ville en premier, l'invité hérite de la carte ; un préfixe sur
`Chara.GetPietyValue` qui lit `IsPC` fige le chargement d'une sauvegarde (tester `core.IsGameStarted`) ; l'outil Bash
n'aime pas un texte long avec des apostrophes dans un « heredoc » : écrire le fichier avec l'outil d'écriture ;
`_lab` doit rester sur le même disque que le jeu (liens physiques). Un geste du banc qui prend un objet en main et
l'utilise dans la même commande allait plus vite qu'un joueur : c'était un vrai défaut du mod (l'objet tenu arrivait
chez l'host une image après la tâche, `CharaTaskRemoteEvent`). Dans un test, `check(cond=eventually(...),
label=f"...")` : Python évalue les arguments nommés dans l'ordre écrit, la condition (qui attend) avant le libellé ;
l'inverse affiche la valeur d'AVANT l'attente (« 0 -> 0 » marqué OK = faux vert). Le jeu n'appelle jamais à l'aide
dans une base du joueur (`Chara.DoHostileAction`, `!EClass._zone.IsPCFaction`) : tester ça à Vernis, pas à la
Prairie. Les anciens pièges sont dans `MODLOG.md`.


## Ajout de 14h35 (daté : étape E commencée ; lignes 1 à 11 faites depuis, voir 19h30)

- Trois lignes de la deuxième chasse corrigées et vertes (`python _tools/hunt2_suite.py`, 21/21) : rondin à la hache,
  prière qui soigne aussi les compagnons de l'invité, nourriture du sac de l'invité qui vieillit.
- Reprendre par la ligne 1 de `PLAN_chasse_differences_2.md` (mode construction d'un invité), test rouge d'abord ;
  détail et ordre dans la dernière entrée de `MODLOG.md`.
- À proposer à l'utilisateur : publier une version compilée sur Elin 23.352 (la 0.26.442 date de 23.351).

## Arrêt de 14h45 (daté ; demandé par l'utilisateur pour compacter la session ; la 0.26.463 est publiée depuis)

- Rien en cours : arbre propre, tout poussé, aucun Elin ouvert, aucun agent en route. Le jeu de cette machine contient
  un build de test (Debug) du dernier commit : avant de jouer avec quelqu'un, `Installer.bat` du zip publié.
- **L'utilisateur a dit oui (14h40) à une nouvelle version compilée sur Elin 23.352** : c'est la première chose à
  faire à la reprise ; la marche à suivre exacte est le point 2 de `PROMPT_reprise.md` (suites larges d'abord).
- Ensuite : ligne 1 de `PLAN_chasse_differences_2.md` (mode construction d'un invité). L'agent qui devait écrire les
  faits dans `dev/PLAN_construction_invite.md` a été arrêté avant la fin : le relancer.
- Pour reprendre : coller le contenu de `dev/PROMPT_reprise.md` (à jour à 14h45) dans une nouvelle session.

## Demandes de l'utilisateur du 5 octobre, 15h (daté ; conseils rendus et dépôt GitHub fait, voir 19h30)

- **Un invité doit pouvoir gérer la base de l'host** ; idée : un système de membres par base. Le mode construction de
  l'invité (conseil 5, `PLAN_construction_invite.md`) en est la première moitié ; reste : qui a le droit (membres), les
  réglages encore locaux (servante, résidents, coffres).
- **Duels entre joueurs**, comme contre les aventuriers : les deux joueurs envoyés sur une autre carte, combat à mort, la
  mort finit seulement le combat, aucune perte des deux côtés, pari possible. Lire d'abord l'arène du jeu (`bout_win`,
  `Zone_Arena`, section « Pas parcouru » de `PLAN_chasse_differences_2.md`).
- **Dépôt GitHub pour garder le monde** (demandé le 5 octobre, 16h45, accord donné : « ça serait top ») : troisième sorte de
  dépôt du mode « sans Elin », en plus du dossier partagé et du logiciel serveur. Un dépôt **à part, privé** (jamais le
  dépôt public du mod), et **le fonctionnement expliqué dans le mod lui-même** (textes d'aide dans l'onglet, 4 langues :
  créer le dépôt, inviter les joueurs, créer la clé d'accès, où la coller). Faits : `PLAN_depot_github.md` (agent lancé).
