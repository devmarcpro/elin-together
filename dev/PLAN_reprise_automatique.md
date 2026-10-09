# Reprise automatique quand l'host part ou plante (conseil 9, étapes 3 à 5)

Ouvert le 2026-10-09 à la demande de l'utilisateur (« commence le chantier sur la reprise automatique »). Le verdict
est déjà rendu : `PLAN_conseil9_verdict.md`. Les faits : `PLAN_hote_qui_part.md`. Ce plan dit où en est le code,
dans quel ordre le faire, et ce que chaque tranche doit prouver. Rien de ce plan n'est encore joué.

## Ce que le joueur doit voir à la fin

- L'host quitte proprement : chez les invités, « X est parti, la partie continue chez Y », 30 à 90 s, rien de perdu.
- L'host plante ou perd Internet : le jeu des invités se fige environ 25 s, attend, puis l'un d'eux rouvre le monde
  et les autres le rejoignent. Au pire 2 minutes de jeu perdues, pour tous, les mêmes.
- L'ancien host relance son jeu : il rejoint la partie comme invité, sans question, et retrouve son personnage.
- Aucun clic, aucun réglage, aucun dépôt à configurer. Une case de l'host sert seulement à éteindre.

## Ce qui est décidé (verdict du conseil 9, ne pas rouvrir)

| Question | Décision |
|---|---|
| Qui reprend | Le plus petit identifiant Steam parmi les invités présents ; s'il n'a pas rouvert en 2 minutes, le suivant |
| Avec quel monde | La copie que chaque invité garde sur son disque (envoyée par l'host après chaque sauvegarde automatique) ; le dépôt n'est qu'un bonus |
| L'ancien host | Revient en invité ; ce qu'il a joué seul entre-temps est gardé de côté, jamais effacé |
| Deux hosts à la fois | Chaque reprise augmente un numéro écrit dans le monde ; le plus grand gagne, puis la sauvegarde la plus récente |
| Par défaut | Allumé |
| Objets en double | Tout le monde recule ensemble à la même sauvegarde |

## Où en est le code (lu le 2026-10-09, rien lancé)

| Pièce | État | Où |
|---|---|---|
| Retour automatique d'un invité après une coupure (étape 1) | Fait, joué au banc, vu marcher en vraie soirée | `Net/NetReconnect.cs` |
| Sauvegarde automatique toutes les 2 minutes, partie ouverte toute seule (étape 2) | Fait, joué au banc | cases `AutoSave`, `AutoHost` |
| Copie du monde chez chaque invité (étape 3) | Écrit, relu, **jamais lancé** ; case `WorldCopy` **décochée** | `Net/Handover/ElinNetHostWorldCopy.cs`, `WorldCopyReceiver.cs`, `WorldCopyStore.cs` ; `worldcopy_suite.py` (jamais lancée) |
| Numéro de reprise dans le monde | Écrit avec la copie (`ElinNetHost.HandoverNumber`, porté par chaque copie), jamais augmenté | `ElinNetHostWorldCopy.cs:56` |
| Qui reprend, à quel tour | Écrit, appelé par personne | `Net/Handover/WorldHandover.cs` (`Successor`, `IsMyTurn`, `Mine`, `Verify`) |
| Rouvrir le monde depuis la copie | **Pas écrit** | — |
| Les autres invités rejoignent le nouvel host | **Pas écrit** (`NetReconnect` ne retente que l'ancien host, 3 minutes) | `Net/NetReconnect.cs` |
| L'ancien host qui revient | **Pas écrit** | — |
| Reprendre le monde avec SON personnage | Fait pour le dépôt, à réutiliser | `Net/Host/ElinNetHostHandOver.cs` (`TakeOverPc`) |
| Verrou du dépôt à 45 s (étape 5) | Pas fait (3 minutes aujourd'hui) | `Helper/SaveDepot.cs`, `Helper/GitHubDepot.cs` |

Trous connus de la copie, notés dans `worldcopy_suite.py` : un invité parti seul sur une autre carte ne reçoit rien
(il manque une ligne dans `ElinNetClientTravel.ShouldReceiveWhileAway`) ; un deuxième invité, le mode serveur et un
disque plein ne sont pas joués.

## Les tranches, dans l'ordre

Chaque tranche : un test rouge d'abord, puis vert, puis un commit. Le banc a besoin de deux fenêtres, trois pour R4
et R5 (accord de l'utilisateur à demander pour trois).

**R0. Le banc sait tuer un host et donner deux identités.** Une fenêtre de test a déjà son identité (`Dev.Identity`).
Il manque : tuer l'host par son numéro de processus (plantage) et le quitter proprement (retour au titre) depuis une
suite, et un « faux salon » pour que l'invité qui reprend soit trouvable sans Steam (le verdict : un fichier avec le
port, le monde et le numéro de reprise). Test : aucun, c'est l'outil des suivantes.

**R1. La copie du monde arrive vraiment (étape 3).** Lancer `worldcopy_suite.py` (C1 à C4), corriger jusqu'au vert.
Ajouter : la copie continue d'arriver à un invité parti seul sur une autre carte. Puis cocher `WorldCopy` par défaut.
Rouge attendu : inconnu, la suite n'a jamais tourné.

**R2. Un invité rouvre le monde depuis sa copie, à la main.** Une commande de test (`emp.take_over`) : la copie
vérifiée est posée dans un dossier de sauvegarde à part, chargée, le joueur y joue SON personnage (`TakeOverPc`), le
numéro de reprise augmente de 1, la partie s'ouvre. Rouge : la commande n'existe pas. Vert : l'invité est host du même
monde, à la date de la dernière copie, avec son personnage, son sac et son or ; le personnage de l'ancien host attend.
C'est la tranche qui dit si la reprise est possible ; les suivantes ne font que la déclencher.

**R3. Départ propre de l'host.** L'host qui quitte prévient (« je pars »), envoie une dernière copie, et l'invité
désigné fait R2 tout seul. Rouge : l'invité est à l'écran titre avec « la partie ne répond plus ». Vert : il est host
en moins de 90 s sans rien cliquer, rien n'est perdu.

**R4. Les autres invités suivent (trois fenêtres).** `NetReconnect` apprend à qui s'adresser : d'abord l'ancien host,
puis, quand `WorldHandover.Successor` désigne quelqu'un d'autre que soi, ce joueur-là. Rouge : le troisième joueur reste
au titre au bout de 3 minutes. Vert : il est dans la partie du nouvel host, à sa place, avec son personnage.

**R5. Plantage de l'host.** L'host est tué. Les invités attendent le délai du lien, puis R2 et R4 se font seuls. Tour
suivant si le premier désigné n'ouvre pas en 2 minutes. Rouge : tout le monde au titre. Vert : partie rouverte, au
plus une sauvegarde automatique de perdue, la même pour tous.

**R6. L'ancien host revient.** Au chargement de son monde, le mod cherche le même monde avec un numéro de reprise
plus grand chez un ami : trouvé, il le rejoint en invité sans question ; sa partie isolée est gardée de côté. Et le
cas « deux hosts » : l'host qui a seulement perdu Internet lit « hors ligne, ce que tu joues ne sera pas gardé ».
Rouge : l'ancien host rouvre un deuxième monde.

**R7. Le dépôt en bonus (étape 5).** Verrou à 45 s, rendu à la fermeture. À faire en dernier, sur le dépôt d'essai,
jamais sur le vrai.

## Ce que le banc ne prouvera pas

Tout ce qui passe par Steam entre deux vrais PC : le temps que met un lien à être déclaré mort, la survie du salon
quand son créateur disparaît, retrouver le nouvel host sans invitation, le relais, les temps de chargement d'un vrai
monde. R3 à R6 peuvent donc réussir au banc et échouer chez l'utilisateur : dans ce cas on retombe à l'écran titre,
comme aujourd'hui, sans rien perdre de plus. Une vraie soirée à trois tranche. Les notes de version diront « non testé
entre deux PC » tant que ce n'est pas fait.

## Risques à garder en tête

- Rouvrir un monde depuis une copie touche aux sauvegardes d'un joueur : la copie est posée dans un dossier à part,
  jamais par-dessus une sauvegarde existante, et rien n'est effacé.
- Une copie incomplète ou trop vieille ne doit jamais servir : elle est relue en entier avant d'ouvrir (`Verify`).
- La sauvegarde automatique fige peut-être le jeu sur un grand monde : à chronométrer sur le vrai monde de
  l'utilisateur avant d'allumer `WorldCopy` pour tous.
- Version du mod différente entre l'host parti et celui qui reprend : refus, comme pour toute connexion.

## Journal du chantier

- 2026-10-09 : plan écrit, code lu, rien lancé. Prochaine chose : R1 (lancer `worldcopy_suite.py`), qui demande le jeu
  de l'utilisateur environ 25 minutes.
- 2026-10-09, 10h20 : **R1, première passe de `worldcopy_suite.py` : 24/26, la copie marche.** C1 à C4 verts sur le
  fond : copie entière en 16 s (28 fichiers, 1 084 117 octets, mêmes sommes que chez l'host), la sauvegarde suivante
  n'envoie que le fichier changé (1 sur 28), une copie coupée au milieu ne remplace pas la précédente et l'invité
  revient seul, aucune sauvegarde de l'invité touchée (copies dans `ElinMP/WorldCopy_2`). Deux rouges : (1) le jeu de
  l'invité a gelé une fois 536 ms pendant la réception (limite du test : 200 ms ; PC lent, fenêtre réduite : à mesurer
  de nouveau avant d'allumer la case pour tous) ; (2) 7 845 exceptions `RenderTextureDesc height must be greater than
  zero` dans le journal de l'invité : **ce n'est pas le mod**, c'est la fenêtre de test réduite (demande de
  l'utilisateur : fenêtres hors de sa vue). Corrigé côté banc : les fenêtres sont posées hors de l'écran, pas réduites
  (`keep_back.ps1`, hors dépôt). Journaux lus : host 0 exception ; mod chez l'invité, 4 « Message not sent » et une
  déconnexion, tous pendant la coupure voulue de C3. Reste pour finir R1 : rejouer fenêtres non réduites, la copie pour
  un invité parti seul sur une autre carte, puis cocher `WorldCopy` par défaut. Vu en passant : les `world_6`…
  `world_emp_2` qui traînent dans les sauvegardes sont les sauvegardes locales de l'invité de test.
- 2026-10-09, 11h : **R2 faite et jouée au banc : `takeover_suite.py` 29/29.** Un invité rouvre le monde depuis sa
  copie par `emp.take_over` (`Net/Handover/WorldTakeover.cs`) : la copie est relue en entier, posée dans un dossier
  de sauvegarde neuf (`world_N`, écrit à côté puis renommé d'un coup), chargée comme une sauvegarde ; la suite est le
  chemin du dépôt (`TakeOverPc` : il joue SON personnage, celui de l'ancien host attend son joueur ; `EmpAutoHost`
  ouvre la partie). Le numéro de reprise passe à 1 et est sauvegardé. Mesuré : 42 s entre la commande et la partie
  ouverte (petit monde, PC lent, deux chargements). Vérifié : son personnage, son or, le personnage de l'ancien host
  gardé et hors de la carte, aucune fenêtre ouverte, la sauvegarde de l'host inchangée à l'octet, aucune autre
  sauvegarde touchée, un seul dossier ajouté, la copie toujours là. **T3 (avant-goût de R6) : l'ancien host rejoint
  le nouvel host et retrouve son personnage, sans écran de création.** Rouge de la première passe : « the copy is not
  whole » alors qu'elle l'était ; le dossier d'une copie est écrit avec les deux sortes de barres et
  `Path.GetDirectoryName` les change, la comparaison de chemins ratait (`WorldHandover.Verify` avait le même défaut,
  jamais appelé jusque-là). Journaux lus : 0 exception dans les deux jeux, aucune pile dans celui du mod, fenêtres
  hors écran sans l'erreur d'affichage. Vu en passant : la ligne de `ShouldReceiveWhileAway` pour la copie existe
  déjà, il ne manque que le test de l'invité parti seul. Pas joués : voir l'en-tête de `takeover_suite.py`. À
  décider en R6 : le monde repris a un nouvel identifiant de sauvegarde (`world_N`) et un nouvel host, donc ses
  copies sont rangées sous un autre nom ; reconnaître « le même monde » demandera un identifiant écrit dans le monde.
  Prochaine tranche : R3 (l'host qui quitte prévient, l'invité désigné fait R2 tout seul).
- 2026-10-09, 11h30 : **R3 (première moitié) faite et jouée au banc : `takeover_suite.py --auto` 33/34.** Nouvelle
  case de l'host, décochée au départ : « Another player takes over when the host leaves » (`Takeover`, règle
  `AllowTakeover`, demande aussi la copie du monde). L'host qui cesse d'héberger (session fermée, écran titre, Elin
  fermé) envoie `HostLeaving` avec la liste des joueurs avant de fermer ses liens (`ElinNetHost.AnnounceLeaving`,
  appelé de `NetSession.RemoveComponent` et de `NetShutdown`) ; l'invité dont c'est le tour (`WorldHandover.IsMyTurn`)
  lance `WorldTakeover.Begin` et lit « The host left. You are taking the world over… ». Mesuré : message reçu en
  1 s, invité host du monde 38 s après le départ, sans un clic (case décochée : il met 26 s à seulement constater la
  coupure, puis reste à l'écran titre). Tout le reste comme R2, T3 compris. T0 prouve la case décochée : personne ne
  reprend, et l'invité revient seul quand l'host rouvre. Le seul rouge est de l'outil : « aucun dossier de sauvegarde
  ajouté » comparait des ensembles égaux alors que la copie de travail de l'invité (`world_emp_2`) est effacée à
  chaque coupure ; vérification corrigée (dossiers en plus seulement), **pas rejouée**. Journaux lus : 0 exception
  dans les deux jeux, aucune pile dans celui du mod. Constat utile pour R5 : sur le banc, la fermeture du lien par
  l'host n'arrive pas à l'invité (la prise d'écoute est jetée avec les liens), il ne l'apprend que par le délai.
  **Reste de R3 : la dernière copie.** Aujourd'hui l'invité repart de la dernière sauvegarde automatique : jusqu'à
  2 minutes perdues pour tous. Il faut que l'host qui part sauvegarde et envoie ce qui a changé avant de fermer.
  **Pas joués** : départ par le menu du jeu (retour au titre) et par la fermeture d'Elin (même fonction appelée, pas
  le même chemin), un invité parti sur une autre carte, deux invités (qui est désigné, que fait l'autre : R4), la
  case cochée dans l'onglet. **Risque connu tant que R6 n'est pas fait** : un host qui recharge sa sauvegarde ou
  rouvre sa partie juste après l'avoir fermée se retrouve avec un deuxième host du même monde.
