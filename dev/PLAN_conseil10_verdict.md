# Conseil 10 : verdict du Président (6 octobre 2026)

Sujet : ce qui est « au monde » et ce qui est « au joueur » (rangement, banque, nuit, date, factures).
Lu : la question, les cinq avis, les cinq relectures, les sept plans de faits. Vérifié dans le code du jeu
(`dev/_decomp/Elin_23351`) et du mod (`ElinTogether/`) ; rien n'a été lancé. « Lu » = vu dans le code, pas joué.

**La règle qui tranche les cinq points, en une phrase :**
ce qui est POSÉ quelque part est au monde (coffre, banque, caisse, base, facture, date) ; ce qui est PORTÉ ou VÉCU
par un corps est au joueur (sac, main, ceinture, faim, fatigue, sommeil, renommée, délais de ses quêtes).
Et pour le temps : **le temps ne saute pour personne qui est en train de jouer. Il ne saute que quand tous
sautent ensemble.**

Aucune décision ci-dessous n'ajoute de donnée dans la sauvegarde. Aucune ne pose de question au joueur.
Chacune est une case host, cochée par défaut.

## Là où le conseil est d'accord

- **Une seule date pour le monde.** Personne ne veut d'une date par joueur (1 500 lignes, risque fort pour les
  sauvegardes, deux joueurs côte à côte l'un en hiver l'autre en été).
- **La banque est commune** : un seul compte, tout le monde dépose et retire. Un compte par joueur casserait les
  revenus du mois et les factures payées par la banque.
- **La caisse d'expédition** : une seule, n'importe qui reprend un objet avant l'envoi, l'or de la vente va à celui
  dont la marque est sur l'objet.
- **Un seul impôt pour le monde**, pas un par joueur ; rendre les deux factures lisibles ; l'invité doit pouvoir payer.
- **Celui qui se couche dort tout de suite.** Pas d'attente, pas de vote, pas de question. Son sommeil est à lui
  (repos, sorts, recettes, grimoire, oreiller, ses propres familiers).
- **La vie personnelle au temps vécu** (faim, états, sac, délais de quête) : déjà fait en 0.26.510, on n'y touche pas.
- **Le pas gratuit de l'invité sur la carte du monde** (quand il marche avec l'host) est une inégalité à corriger.

## Là où le conseil s'oppose

1. **Rangement, la ceinture.** E : « c'est le jeu d'origine, ne rien changer ». A, B, C, D : protéger. B ajoute :
   la cause du retour n'est pas prouvée. **Je suis B.** Vérifié : la rangée de raccourcis du bas est DÉJÀ protégée
   par le jeu (`TaskDump.cs:273`, `IsHotItem`) ; ce qui ne l'est pas, c'est le contenu de la ceinture et l'objet
   tenu en main qui ne vient pas de la barre. Le joueur dit « hotbar » et « luth » : la ceinture seule n'explique
   peut-être rien. Donc : le test d'abord, le code ensuite, et seulement là où le test est rouge.
2. **Rangement, le réglage « ranger ici ».** C et D : par joueur. A, B, E : au coffre, donc au monde.
   **Au monde.** Un coffre est posé. Deux réglages du même coffre selon qui regarde, c'est « où est mon épée ? ».
   Et le réglage d'un invité ne survivrait pas à sa reconnexion (son monde est une copie de celui de l'host).
3. **La nuit : quand la date saute-t-elle ?** A et C : quand la majorité dort. D et E : quand tous dorment.
   B : selon la carte. **Tous.** La majorité impose un saut de huit heures à un joueur debout : c'est exactement
   « le temps a sauté » dont le joueur s'est plaint, et c'est un vote caché.
4. **La date : le voyage.** C : « l'urgence publiée suffit ». A, B, D, E : un pas sur la carte du monde ne doit
   plus faire sauter la date des joueurs qui sont ailleurs. **Je suis les quatre**, et j'ai trouvé un fait de plus
   qui leur donne raison (voir les angles morts, point 1).
5. **L'impôt : sur quelle renommée ?** A, B, C, E : celle de l'host. D seule : la plus haute du groupe.
   **Je suis D, contre la majorité**, mais en dernière étape. Raison : avec la renommée de l'host, la gloire d'un
   invité ne coûte jamais rien et celle de l'host coûte toujours. C'est une différence host/invité, la seule chose
   que le projet interdit. Les quatre autres n'ont donné qu'un argument : « c'est plus petit ».
6. **Le sommeil doit-il se payer ?** B et le relecteur 3 : oui, sinon c'est une machine à soin, et il faut un
   compteur. E : pas de mécanisme. **Les deux ont raison et le jeu a déjà la réponse** (angles morts, point 3) :
   pas de compteur à inventer.

## Angles morts trouvés à la relecture

1. **Les quêtes à chronomètre (récolte, concert, mariage : 180 minutes).** Personne ne l'a vu. Lu :
   `GameDate.AdvanceMin` ajoute les minutes au chronomètre de la carte (`GameDate.cs:88`), et le mod fait pareil
   chez l'invité (`WorldDateAdvanceDelta.cs:64-66`), sans regarder qui a fait passer ce temps. Un seul pas d'un ami
   sur la carte du monde vaut 180 minutes : la quête de récolte d'un autre joueur est finie d'un coup. Pas joué.
   La protection publiée en 0.26.510 couvre les délais en jours, pas ce chronomètre.
2. **La cause du retour « rangement » n'est pas prouvée** (B, relecteur 4). Voir plus haut.
3. **Le sommeil se paie déjà, en solo, par la fatigue.** Lu : en solo on ne peut se coucher que fatigué
   (`Chara.CanSleep`, `Chara.cs:1362`). La fatigue monte avec les tours que le personnage a vécus : c'est déjà une
   horloge personnelle. C'est le mod qui a levé cette règle (`AllowPartySleep` : « are you tired? yes you are »)
   pour que tout le monde puisse se coucher ensemble. Il suffit de la remettre. Et dormir n'est pas un gros soin :
   `OnSleep` rend en vie la « puissance » du lit (20 sans lit), recharge l'endurance, coûte 20 de faim.
4. **Deux pièges quand un seul dort** (lus, personne ne les a nommés) : le jeu endort tout le « groupe » de celui
   qui dort (`ConSleep.cs:131-137`) et réveille tout le groupe avec soin et +20 de faim (`LayerSleep.cs:76-79`).
   Or dans le mod, tous les joueurs sont dans le groupe de l'host. Aujourd'hui c'est caché parce que tout le monde
   dort en même temps. Avec un seul dormeur, l'host qui se couche endormirait et affamerait ses amis debout.
5. **Deux craintes de B qui sont déjà réglées** (vérifié) : deux déposants ne fusionnent jamais dans la caisse
   (`ShippingStackPatch.cs`) ; les délais des quêtes personnelles sont déjà repoussés quand un autre fait passer le
   temps (`PersonalQuests.Postpone`).
6. **Confirmé** : `taxBills` n'apparaît nulle part dans le mod. L'invité qui pose la facture d'impôt dans le coffre
   des impôts lit « mauvaise idée » (`InvOwnerDeliver.cs:65`). Et au bout de quatre factures impayées, c'est le
   personnage de l'HOST qui perd 50 de karma (`FACTION.cs`).
7. **Le monde va trop vite à plusieurs** (personne ne l'a chiffré). Aujourd'hui chaque nuit et chaque pas de chaque
   joueur s'ajoutent à la même date. « Deux factures en quelques jours » en est aussi un signe.
8. **Ce que le joueur voit quand le jeu agit seul** (relecteur 5) : aucun avis ne le dit. Chaque point ci-dessous
   a sa ligne à l'écran.
9. **Rôles échangés** (relecteur 2) : chaque test ci-dessous se joue deux fois, déclenché par l'host puis par l'invité.
10. **L'avance rapide** d'un joueur qui se repose accélère le monde de tous (`PLAN_plusieurs_invites.md` A5) : même
    frontière, même règle. Rangé en fin de liste.
11. **Les 1 500 orens déjà perdus** ne reviennent pas tout seuls s'ils ont été déposés dans la zone d'un autre invité.

## La recommandation

### (i) Le rangement automatique

**Décision.**
(a) Dans une partie ouverte par le mod (host seul compris : la session s'ouvre toute seule au chargement, donc
l'host ne vit jamais deux jeux), le rangement ne prend ni ce que le joueur tient en main, ni ce qui est dans sa
ceinture, comme il laisse déjà la rangée du bas. Case host « Le rangement épargne la main et la ceinture », cochée.
(b) Le réglage « ranger ici » d'un coffre reste au coffre, donc au monde. Rien à écrire.

**Première étape livrable : un test, pas de code.** `dev/_tools/hunt_suite.py`, nouvelle étape `d3b`, deux fenêtres,
jouée par l'host puis par l'invité. Trois sources, le même objet en double dans un coffre réglé « ce qui s'y trouve
déjà » : (1) rangée du bas, (2) contenu de la ceinture, (3) objet tenu en main sans être dans la barre (un luth).
- Attendu aujourd'hui : (1) reste (vert), (2) et (3) partent (rouge). Si (1) part aussi, c'est un défaut du mod
  (l'objet a perdu son rang) : on corrige à la cause, pas par la case.
- Puis le correctif, seulement pour ce qui est rouge : un fichier neuf dans `ElinTogether/Patches/`, 10 à 15 lignes
  (postfix sur `TaskDump.ListThingsToPut`), la case dans `EmpConfig.cs`, un texte. Vert : les objets restent, le
  coffre n'a qu'un exemplaire, et l'invité voit le même sac et le même coffre que l'host.
- Si rien n'est rouge : on n'écrit pas la case. On ajoute cinq lignes de trace dans le journal du mod (« rangé :
  objet, coffre, réglage ») pour que la prochaine fois s'explique sans rien demander à personne.
- Petit ajout, à part (10 lignes) : quand un autre joueur change le réglage d'un coffre, une ligne s'affiche.

**Ce que le joueur voit.** Les lignes « rangé … dans … » du jeu, comme en solo. En plus : « Alice a changé le
rangement du coffre X ».

**Ce qu'on peut perdre.** Rien en objets. Un joueur qui comptait sur le rangement pour vider sa ceinture doit le
faire à la main (la case se décoche). Un ami peut toujours régler un coffre commun autrement que vous : c'est un
coffre commun.

**Écarté.** « Ne rien changer » (E) : le fait de départ (« un joueur seul le vivrait aussi ») n'a jamais été joué,
et la fenêtre de la ceinture n'a pas de menu pour se protéger soi-même. « Seulement à plusieurs » (C) : l'host seul
et l'host à trois vivraient deux jeux. « Réglage par joueur » (C, D) : deux copies qui divergent, et un réglage
d'invité perdu à chaque reconnexion.

**À plusieurs vrais PC seulement.** Le rangement de l'host pendant qu'un invité a le même coffre ouvert, avec du
vrai délai (lu : si le coffre n'est pas connu de l'autre jeu, rien n'est envoyé, `CardAddThingEvent.cs:113-120`).

### (ii) La banque et la caisse d'expédition

**Décision.** Banque commune : un compte pour le monde. Caisse commune : n'importe qui reprend avant l'envoi ; l'or
va à celui dont la marque est sur l'objet au moment de l'envoi ; reposer l'objet remet la marque de celui qui le pose.

**Première étape livrable : jouer ce qui est écrit.** La correction existe (environ 300 lignes, 8 fichiers, liste
dans `PLAN_banque_invite.md` §7) et compile. Test `dev/_tools/bank_suite.py`, deux fenêtres :
- rouge sur la 0.26.510 : B3 (invité seul ailleurs : fenêtre vide après réouverture, reprise impossible), B4,
  S1 (caisse) ;
- vert sur la nouvelle : B1 à B5 et S1 ; l'or compté une seule fois chez l'host, la bourse de l'invité juste.
- B1 et B2 doivent être verts avant comme après. S'ils sont rouges avant, la cause n'est pas la seule : on s'arrête.

**Deuxième étape (30 à 50 lignes, `ElinNetHostShipping.cs`, `ElinNetClientShipping.cs`).** Fermer la fenêtre de
perte avouée : l'host garde l'objet repris « en attente » jusqu'à l'accusé de l'invité ; coupure ou silence : il le
remet dans la banque. Test : couper le lien de l'invité entre la demande et la réponse ; l'or est dans la banque.

**Ce que le joueur voit.** La fenêtre de la banque avec le vrai contenu, partout. Une ligne pour tous : « Alice a
déposé 1 500 orens à la banque », « Bob a retiré 1 500 orens » (à ajouter, 10 lignes : la banque commune montre
l'or de chacun à ses amis, il faut une trace). Deux mains sur la même pile : le second lit « trop tard ».

**Ce qu'on peut perdre.** Un ami peut prendre votre or ou reprendre votre objet de la caisse : c'est voulu, c'est
un coffre. Avant la deuxième étape : un objet repris pendant une coupure de moins d'une seconde. Les 1 500 orens
d'hier : s'ils sont dans la banque de l'host, ils y sont encore ; sinon l'host les rend à la main.

**Écarté.** Un compte par joueur (des semaines, casse les revenus et les factures par la banque). « Déposé par X »
sur chaque objet (D) : joli, pas nécessaire. Verrouiller l'objet d'un autre dans la caisse : un objet refusé sans
explication est pire que le risque entre amis.

**À plusieurs vrais PC seulement.** Une vraie coupure de réseau en plein retrait ; deux vrais joueurs sur la même
pile avec du délai ; l'invité en visite chez un autre invité (dépôt sûr, mais rien à l'écran : trois fenêtres au
moins, et c'est une inégalité qui reste).

### (iii) La nuit

**Décision.** Chacun dort pour soi, tout de suite. **La date du monde ne bouge pas quand un seul dort.** Elle
avance d'une nuit au moment où TOUS les joueurs vivants et connectés sont endormis en même temps, où qu'ils soient.
On ne peut se coucher que fatigué, comme en solo ; mais on peut toujours rejoindre un ami qui dort déjà, pour faire
passer la nuit ensemble. Case host « Chacun dort pour soi », cochée.

**La scène : Alice se couche à la base à 22 h 10 ; Bob est dans un donjon, Chloé fait ses courses en ville.**
- *Alice.* Elle n'attend personne. Elle s'endort comme en solo (quelques tours), l'écran de nuit dure ses quelques
  secondes habituelles. Elle se réveille **à l'heure du monde, vers 22 h 15, il fait encore nuit**. Son corps a
  eu sa nuit : fatigue à zéro, endurance rechargée, vie et mana rendues selon son lit, poison et saignement
  partis, +20 de faim, son rêve (sort), sa recette, son grimoire, son oreiller. Ses familiers à elle viennent
  dormir contre elle ; ceux des autres ne bougent pas. La date du monde n'a pas bougé.
  Elle lit : « Tu as dormi. Le monde n'a pas avancé : Bob et Chloé sont éveillés. »
- *Bob et Chloé.* Une ligne : « Alice dort (1 sur 3) ». Rien d'autre : pas de saut d'heure, pas de faim, pas de
  nourriture qui tourne, pas de monstre en plus, la quête de Bob garde son temps. Ils ne sont ni endormis ni
  déplacés.
- *Si Bob et Chloé se couchent pendant qu'Alice dort encore* : au moment où le troisième ferme les yeux, tous
  lisent « Tout le monde dort : la nuit passe. » La date avance des heures de la nuit du dernier couché, chacun
  se réveille au matin. C'est la nuit du jeu solo : cultures, boutiques, courrier suivent.
- *Mêmes rôles échangés* : si c'est l'host qui se couche seul, il vit exactement ce qu'Alice vit.
- Un joueur absent du clavier ne bloque le sommeil de personne. Il empêche seulement la nuit commune.

**Première étape livrable.** Fichiers : `Patches/Synchronization/SleepSynchronizationContext.cs` (le plus gros),
`Models/Delta/Misc/SleepRequestDelta.cs`, `Models/Delta/Chara/CharaSleepDelta.cs`, `EmpConfig.cs`, deux textes.
80 à 120 lignes, et l'attente « tout le monde prêt » disparaît. Deux commits, publiés ensemble :
1. *Chacun dort pour soi* : la nuit d'un joueur ne fait plus avancer la date ; le réveil se joue dans le jeu de
   celui qui dort (cela règle aussi le retour 10 : grimoire, oreiller, recette de l'invité) ; `AllowPartySleep` ne
   force plus « fatigué » que si un autre joueur dort déjà.
   Les deux pièges de l'angle mort 4 sont à garder sous les yeux : l'host qui dort ne doit ni endormir, ni soigner,
   ni affamer un joueur debout ou ses compagnons.
2. *Tous endormis* : l'host voit que tous dorment et ajoute les heures à la date, une fois (environ 20 lignes).
- Test `dev/_tools/sleep_suite.py`, deux fenêtres, étapes neuves :
  - `n1` l'invité se couche, l'host marche. **Rouge aujourd'hui** : l'invité attend sans fin. **Vert** : réveillé
    en moins de 20 secondes, fatigue à zéro, faim +20, date des deux jeux avancée de moins de 30 minutes, l'host
    sans sommeil et sans faim en plus.
  - `n2` l'inverse : l'host se couche, l'invité marche. Mêmes mesures, rôles échangés.
  - `n3` les deux se couchent : la date avance d'une nuit (les étapes z1, z2 actuelles restent vertes).
  - `n4` un joueur reposé essaie de se coucher seul : refusé comme en solo ; il peut si l'autre dort.
- Trois fenêtres (accord déjà donné) : deux couchés et un debout, pas de saut ; trois couchés, saut.

**Ce qu'on peut perdre.** Dormir seul ne fait plus venir le matin : on se réveille dans le noir. C'est le prix
pour que personne ne subisse la nuit d'un autre. Les nuits passent moins souvent, donc le monde va plus lentement
(voir iv). Pendant l'écran de nuit le monde n'est pas en pause : un monstre peut frapper un dormeur (déjà vrai
aujourd'hui).

**Écarté.** Attendre les autres : c'est le défaut actuel. Voter ou majorité : une question déguisée, et un saut
imposé à ceux qui jouent. « La nuit d'un seul avance la date de tous » : le matin pour le dormeur, mais le ciel qui
saute trois fois par jour pour chaque ami, et un monde deux à quatre fois trop rapide. « La nuit passe quand le
dernier a dormi » : le saut tombe sur ceux qui se sont déjà relevés. Un compteur de minutes vécues (B, D) : inutile,
la fatigue du jeu fait déjà ce travail, et c'est une donnée de moins dans la sauvegarde.

**À plusieurs vrais PC seulement.** La nuit commune avec des joueurs sur des cartes différentes (chaque jeu doit
dire à l'host qu'il dort) ; savoir si trois amis à la voix arrivent à se coucher « en même temps » (la fenêtre dure
une dizaine de secondes : si c'est trop court en vrai, on l'allonge, sans jamais faire attendre) ; le dormeur
attaqué pendant sa nuit ; un joueur qui se déconnecte endormi.
Attention : `SleepSynchronizationContext.cs` est en cours de modification par une autre session (retour 1).
Ce point se fait après que ce travail-là est vert et commité.

### (iv) La date

**Décision.** Une seule date pour le monde. Elle avance de trois façons seulement :
1. minute par minute, pendant qu'au moins un joueur joue (comme aujourd'hui) ;
2. d'une nuit, quand tous dorment (point iii) ;
3. de trois heures par pas sur la carte du monde, **seulement si tous les joueurs connectés voyagent ensemble**
   sur cette carte.
Sinon, le voyageur paie son pas avec son corps (ses tours de faim et d'états, comme en solo) et la date ne bouge
pas. L'invité qui marche sur la carte du monde avec l'host paie aussi son pas. Case host « Le temps ne saute que
quand tous sautent ensemble », cochée.

**Ce que deviennent les choses.**
- Cultures, boutiques, courrier, expédition, salaires, impôts, saisons, cartes qui se régénèrent, objets posés au
  sol et dans les coffres : ils suivent la date du monde. Rien ne change dans leur règle ; ils ne font plus de bond
  parce qu'un ami voyage ou dort.
- Faim, états, sac, délais de quête en jours : au joueur (fait).
- Chronomètre d'une quête de récolte, de concert, de mariage : au joueur qui la fait. Le temps d'un autre ne le
  touche plus.

**La même scène, côté date.** Pendant qu'Alice dort, Bob sort du donjon et fait dix pas sur la carte du monde.
Bob a faim comme en solo (dix pas, dix fois ses tours). Pour Alice et Chloé : rien. Pas de ciel qui tourne, pas de
trente heures d'un coup. Bob lit, une fois par voyage : « Tes amis sont ailleurs : ton voyage ne fait pas avancer
la date. » Si les trois marchent ensemble sur la carte du monde, la date avance de trois heures par pas de l'host,
comme aujourd'hui, et chacun paie ses propres pas.

**Première étape livrable, trois petits commits, dans cet ordre.**
1. *Le chronomètre des quêtes* (environ 10 lignes : `Patches/DeltaEvents/World/WorldDateAdvanceEvent.cs`,
   `Models/Delta/World/WorldDateAdvanceDelta.cs`). Test `time_suite.py` W7, deux fenêtres : l'invité tient une
   carte avec une quête à chronomètre, l'host fait `AdvanceMin(180)`. **Rouge attendu** : +180 au chronomètre.
   **Vert** : inchangé. Puis rôles échangés. (La mise en place de la quête au banc est à ajuster, pas essayée.)
2. *Le pas qui ne fait plus sauter les autres* (30 à 60 lignes : `Patches/Remote/RemoteTravelRegionPatch.cs`,
   la case). W8 : l'invité seul à Vernis, l'host fait cinq vrais pas sur la carte du monde. **Rouge aujourd'hui** :
   la date de l'invité avance de quinze heures. **Vert** : moins de quinze minutes d'écart, et l'host a bien payé
   ses tours. W8b : l'inverse (l'invité voyage, l'host en ville).
3. *Le pas de l'invité aux côtés de l'host* (dans le même fichier). W9 : les deux sur la carte du monde.
   **Rouge aujourd'hui** : le pas de l'invité ne lui coûte aucun tour. **Vert** : il paie environ 120 tours, pour
   lui et ses compagnons seulement, et la date n'avance que par les pas de l'host.
   À vérifier dans le même lot : le voyage express (`LayerTravel.cs:161`) passe par un autre chemin.
Plus tard, même règle, 6 lignes : l'avance rapide d'un joueur n'accélère plus le monde d'un joueur qui agit.

**Ce qu'on peut perdre.** Le monde ira plus lentement qu'en solo, nettement (pas mesuré) : cultures, réassort des
boutiques, ventes de la caisse, salaires viennent moins souvent par heure jouée ; les impôts aussi. Le levier est
dans le jeu : tout le monde se couche, la nuit passe. La nourriture du voyageur ne vieillit plus en route quand
ses amis sont ailleurs (petit avantage). Les suites `time_suite` W1 à W4 et `hunt2_suite` E3 sont à relire : elles
décrivent l'ancienne règle.
À mesurer après une vraie soirée : combien de jours du monde en quatre heures de jeu.

**Écarté.** Une date par joueur (unanime). La date du plus avancé telle quelle (C) : ciel qui saute, monde trop
rapide, quêtes à chronomètre tuées. La date au rythme du plus lent : un absent gèle tout. Le quart d'heure par pas
(D) : encore un saut, et un chiffre inventé. Le rattrapage borné des objets posés (400 à 600 lignes, une donnée
« dette » dont la sauvegarde n'est pas vérifiée) : avec moins de sauts, il n'a plus d'objet. Le compteur de minutes
vécues (D) : pas nécessaire.

**À plusieurs vrais PC seulement.** Trois joueurs dont deux voyagent ensemble et un reste en ville (le troisième
doit bloquer le saut) ; le visiteur d'un invité ; ce que donne le rythme du monde sur une vraie soirée ; l'heure
qui reste la même dans quatre jeux après deux heures.

### (v) Les factures

**Décision.** Un seul impôt pour le monde, une seule facture de livraison pour le monde (elle reste au compte
commun, pas au déposant). N'importe quel joueur peut payer, avec son or à lui, et tout le monde le voit. L'impôt
se calcule sur la renommée la plus haute parmi les joueurs connectés, et non plus sur celle du seul host (c'est
la dernière étape de ce point).
« Deux factures » n'était très probablement pas un doublon (500 = impôt ; 35 = 20 + 5 × 3 objets livrés) : on le
prouve, on ne l'affirme pas.

**Première étape livrable : un test, pas de code.** `dev/_tools/bills_suite.py` (à écrire sur le modèle de
`world_suite.py`), deux fenêtres, cas 1 à 3 de `PLAN_factures.md` §7 : fin de mois = une facture d'impôt en tout ;
trois objets livrés = une facture de 35 ; le test affiche aussi le NOM que le jeu donne aux deux objets.
Attendu vert. S'il sort deux factures d'impôt, le doublon est réel et on cherche là.
**Deuxième étape (environ 20 lignes : un patch sur `InvOwnerDeliver.PayBill`, l'envoi du compteur de l'host).**
Test P1 : l'invité pose la facture d'impôt dans le coffre des impôts. **Rouge aujourd'hui** : « mauvaise idée », la
facture reste, le compteur de l'host ne bouge pas. **Vert** : 500 orens de moins chez l'invité, facture disparue,
compteur de l'host à moins un. Puis l'host paie (déjà bon) : rôles échangés.
**Troisième étape (environ 15 lignes de textes).** Les lignes à l'écran, et un libellé seulement si les noms du
jeu ne se distinguent pas.
**Quatrième étape (10 à 20 lignes, `FACTION.GetFameTax`).** La renommée la plus haute. Lu : l'host reçoit déjà la
renommée des joueurs (`PersonalQuests.cs:289`) ; à quel point elle est à jour n'est pas vérifié.

**Ce que le joueur voit.** Pour tous : « Impôt du mois : 500 orens », « Livraison : 35 orens (3 objets) »,
« Alice a payé l'impôt (500 orens) ». Plus personne ne lit deux factures comme un doublon.

**Ce qu'on peut perdre.** Avec la quatrième étape, l'impôt monte quand un invité est plus célèbre que l'host.
Celui qui paie, paie tout : pas de partage automatique. Le karma perdu après quatre factures impayées reste sur le
personnage de l'host (maintenant n'importe qui peut l'éviter en payant).

**Écarté.** Un impôt par joueur : la base 500 payée N fois, un compteur et un karma par joueur, le plus gros des
trois choix. Couper la facture en parts : il faudrait suivre qui a payé quoi. Facturer la livraison au déposant :
il faudrait marquer chaque objet. Annoncer « pas de doublon » sans test.

**À plusieurs vrais PC seulement.** Une vraie fin de mois avec un invité en voyage et la case « gardien du monde »
telle que les amis l'ont réglée ; la renommée d'un invité vue par l'host après une longue soirée.

## L'ordre de réalisation

1. **(ii) Banque** : jouer `bank_suite` sur la correction écrite. Rien à écrire, c'est de l'or perdu.
2. **(iv-1) Chronomètre des quêtes** : dix lignes, protège tout de suite.
3. **(i) Rangement** : le test `d3b` d'abord, le correctif ensuite pour ce qui est rouge.
4. **(v) Factures** : `bills_suite`, puis le droit de payer de l'invité, puis les lignes.
5. **(iv-2, iv-3) Le pas sur la carte du monde.**
6. **(iii) La nuit** : la plus grosse, dans un fichier qu'une autre session modifie ; après que le retour 1 est
   vert et commité. Les deux commits publiés ensemble.
7. **(ii) deuxième étape** (objet en attente), **(v) renommée la plus haute**, **avance rapide**.
Un changement = un test = un commit ; pousser `feat/independent-travel` après chaque lot vert ; publier demande
l'accord de l'utilisateur. Deux fenêtres par défaut ; trois pour les cas marqués.

## La première chose à faire

Lancer l'host et un invité (`python _tools/mp_test.py`), puis `python _tools/bank_suite.py`, et lire B1 à B5 et S1.
B3 doit être rouge sur la 0.26.510 et vert sur la version qui contient la correction de la banque. Tant que ce
n'est pas lu, la correction n'est pas « faite ».
