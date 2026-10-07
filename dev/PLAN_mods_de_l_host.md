# Récupérer les mods de l'host en rejoignant (demande du 2026-10-07) — faits établis, conseil 12, puis ce qui est écrit (dernière section)

Suite de `PLAN_profil_mods.md` (2 octobre). Recherche en lecture seule du 7 octobre sur le jeu 23.352 :

- **Pas d'activation à chaud** : `RefreshMods`/`ActivatePackages` ne tournent qu'au démarrage (`Core.StartCase`) ; le
  Mod Viewer n'affiche qu'un « redémarrage requis ». Changer de mods = relancer le jeu.
- **`loadorder.txt`** à côté d'`Elin.exe` : `chemin,0|1,id`. Installé mais non listé = **activé**. Listé mais absent =
  ignoré. Les préréglages officiels sont dans `LocalLow\Lafrontier\Elin\User\Load Order\*.txt` (pas à côté de
  l'exe) : `id,0|1,workshopId,titre`, API `ModLoadOrderPreset.TryParse/Serialize/FindMissing/Apply`,
  `ModManager.ApplyPreset` (réécrit `loadorder.txt`).
- **Synchronisation au démarrage du jeu lui-même** (`config.other.syncMods`, vrai sur ce PC, faux par défaut) : au
  lancement, le jeu télécharge les abonnements manquants (`DownloadSubscriptions`, écran « Downloading mods n/m ») et,
  réglage coché, ne charge que les dossiers du Workshop auxquels le compte est **abonné**. Donc : s'abonner +
  relancer = le jeu fait le téléchargement lui-même.
- **API à portée** : Steamworks.NET et l'enveloppe Heathen (`UserGeneratedContent.Client.SubscribeItem`,
  `DownloadItem`, `GetItemState`, `UgcQuery.Get(ids)` pour titre et taille). Le jeu ne s'abonne jamais lui-même ;
  ElinTogether n'utilise rien de tout cela aujourd'hui.
- **Identifiant Workshop d'un paquet** : `EMod.workshopId` (nom du dossier). Mod local (`Package/Mod_*`) : pas d'id,
  ne peut pas être récupéré. Plugin `BepInEx/plugins` : hors de la liste, ne peut ni être récupéré ni coupé.
  **Le fork lui-même** a le même id que le mod d'origine du Workshop (3773298709) : à traiter à part.
- **`version` de `package.xml`** = version du JEU visée, pas celle du mod : inutilisable pour comparer. Steam sert
  toujours la dernière révision ; seul le hachage de la DLL ou `TimeUpdated` distingue deux révisions.
- **Poignée de main actuelle** : les « actes » (toutes les sous-classes d'`Act` de toutes les DLL) sont TOUJOURS
  comparés : un mod à DLL qui ajoute un acte d'un seul côté = refus (`ActMappingMismatch`). Sources/plugins/fichiers
  seulement si l'host l'a réglé (vide par défaut). Aucun message ne porte la liste des mods. L'host coupe un invité
  qui ne répond pas en 15 s (`Policy.Timeout`). Endroits où porter la liste : champ de `SourceValidationRequest`,
  nouveau message, ou **données du salon Steam** (lues avant même de se connecter, ~8 Ko par valeur).
- **Relance** : `+connect_lobby <id>` est déjà compris au démarrage (Release) ; rien n'est gardé entre deux
  lancements (à écrire dans `ElinMP\`) ; une seule instance à la fois (attendre la fin du processus) ; `Elin.exe`
  direct ne marche que s'il y a `steam_appid.txt` (absent chez un joueur normal) -> passer par Steam
  (`steam://rungameid/2135150`, arguments à vérifier) ; retirer les variables `DOORSTOP*` si on lance un enfant.
- **Banc** : `Package` et le dossier Workshop sont partagés par toutes les fenêtres, les abonnements sont ceux du vrai
  compte ; seul `loadorder.txt` est propre à chaque copie `_lab`. On peut jouer : la liste dans la poignée de main,
  la comparaison, l'écriture et la remise de `loadorder.txt`, la relance d'une copie `_lab`. On ne peut pas jouer :
  un vrai mod manquant, un vrai téléchargement, la relance par Steam, Proton.

Pistes (aucune choisie) : 1. seulement dire ce qui manque ; 2. s'abonner + « relancez » ; 3. s'abonner + liste de
l'host + quitter, relancer et rejoindre tout seul + remettre la liste du joueur au démarrage suivant ; 4. profil
temporaire sans abonnement. Question pour le conseil : la relance et l'installation de programmes contre « le joueur
n'a pas à réfléchir, aucune question » ; que faire des abonnements ajoutés (ils restent sur le compte) ; mods locaux
de l'host ; mods en trop chez l'invité ; mods d'affichage seul.

## Conseil 12 (2026-10-07, soir) — verdict

Cinq avis, deux relectures croisées, synthèse par la session.

- **Accord (4 avis sur 5, les deux relectures)** : le vrai besoin est « rejoindre sans être refusé et sans aligner
  les listes à la main ». Tout de suite, ce qui se joue au banc : l'host **publie sa liste** (données du salon Steam,
  lisibles avant de se connecter, et poignée de main), l'invité **compare** ; seul ce qui change la simulation bloque
  (la comparaison des actes, déjà là) ; le reste est seulement listé ; un refus **nomme les mods** (« l'host a X, il
  vous manque Y »). Le téléchargement et la relance automatiques : pas avant un essai sur de vrais PC.
- **« Aucune question » contre l'installation de programmes** : la règle vise les ambiguïtés, pas les autorisations.
  Installer du code sur le compte Steam d'un autre et relancer son jeu ne peut pas être décidé par une case de l'host.
  Un seul avis voulait tout automatique, coché par défaut ; il est jugé l'angle mort par les deux relectures.
- **Angles morts relevés** : l'utilisateur a demandé le TÉLÉCHARGEMENT, pas un message : lui donner un chemin réel
  tout de suite, le moins risqué = **un bouton « s'abonner aux mods manquants »** dans le message (le clic du joueur
  est l'autorisation, aucun réglage à trouver), puis le joueur relance lui-même ; la liste de l'host est une donnée
  non fiable (vérifier les identifiants, montrer titre et taille) ; protection contre la boucle de relances ; version
  du format de la liste ; un abonnement vaut pour tous les PC du compte ; délai de 15 s de la poignée de main.
- **Abonnements** : les garder, les noter dans un fichier ; pas de désabonnement automatique (autre changement
  silencieux du compte, impossible à tester). Ne pas réécrire `loadorder.txt` dans la première version.
- **Ce qui ne peut pas être récupéré** (mods locaux de l'host, le fork lui-même) : listé « à installer à la main ».
  Le fork est comparé par sa version de build, jamais récupéré (il partage l'identifiant du mod d'origine du Workshop).

### Découpage retenu
| Tranche | Contenu | Banc |
|---|---|---|
| M1 | Liste de l'host (id, id Workshop, titre) dans le salon et la poignée de main ; comparaison chez l'invité ; refus qui nomme les mods ; la liste des parties montre « n mods, il vous en manque k » | jouable (liste, comparaison, message) |
| M2 | Bouton « S'abonner aux mods manquants » (Steam), progression, puis « relancez Elin » ; fichier des abonnements ajoutés | l'appel Steam ne se joue pas au banc (aucun mod vraiment manquant) |
| M3 | Relance et retour automatiques, profil temporaire, remise de la liste du joueur | après essai sur de vrais PC ; réglage côté invité |

**À trancher par l'utilisateur** : M2 par un bouton (un clic) ou sans aucun clic (application stricte de « aucune
question ») ; M3 un jour ou jamais.

## Remarque de l'utilisateur après le conseil (2026-10-07) : « comme Civ 6 : téléchargé pour la partie, sans abonnement »

Elle lève l'objection principale du conseil (abonnement permanent, valable sur tout le compte, actif en solo).
- Steam le permet : `SteamUGC.DownloadItem(id)` télécharge un objet du Workshop **sans y abonner le compte** (copie
  gardée en cache par Steam, qu'il peut nettoyer plus tard). Le jeu lui-même s'en sert déjà pour ses abonnements.
- Ce que Civ 6 a et qu'Elin n'a pas : Civ 6 charge les mods au lancement d'une PARTIE, Elin au démarrage du JEU.
  Une relance reste donc nécessaire.
- Obstacle à lever : avec la synchronisation du jeu cochée (`syncMods`), Elin ne charge du dossier Workshop que les
  objets auxquels le compte est abonné : un objet téléchargé sans abonnement y serait ignoré. Piste : le rendre
  visible comme mod local le temps de la session (dossier ou jonction dans `Package/`, toujours chargé), puis le
  désactiver dans `loadorder.txt` à la fin et le retirer au lancement suivant. À concevoir et à essayer sur un vrai PC.
- Conséquence sur le découpage : M2 devient « télécharger sans abonnement » ; le compte Steam et le jeu solo de
  l'invité ne sont plus touchés, ce qui rouvre la question « un clic ou aucun ».

## Demandes de l'utilisateur du 7 octobre au soir : la liste des mods vit dans le dépôt du monde

1. « Dans le repo, une modlist, un fichier txt avec les liens des mods » : **fait** pour le dépôt GitHub
   (`Helper/ModList.cs`, `GitHubDepot.WriteModList`) : `modlist.txt` à côté de `world.zip`, un mod par ligne (titre,
   puis la page du Workshop ; « installé à la main » sinon ; le fork renvoie à ses versions GitHub). Écrit quand le
   dépôt n'en a pas, **jamais remplacé par le jeu** : c'est la liste du MONDE, on la change à la main dans le dépôt
   (un lien par ligne). `depot_github_test.py` G15, 77/77. Pas fait : dépôt en dossier et serveur de dépôt.
2. « Quand un joueur héberge ou rejoint la partie, qu'il charge les mods du repo » : la liste du dépôt devient la
   référence. À écrire (tranches M2/M3 revues) : lire `modlist.txt` à la prise du monde (héberger) et la liste
   publiée par l'host (rejoindre), comparer aux mods chargés, télécharger ce qui manque **sans abonnement** (comme
   Civ 6), relancer Elin, revenir tout seul ; mods en trop coupés le temps de la session. La lecture doit accepter
   un fichier modifié à la main (toute ligne contenant `filedetails/?id=<nombre>`).

## Écrit le 2026-10-07 (nuit) : M1 actif, M2 écrit derrière un réglage décoché

Compilé dans les deux configurations (0 erreur). `depot_github_test.py` : 85/85 (G16 ajouté). **Rien n'a été joué
dans le jeu** (les fenêtres de test étaient prises) : `modlist_suite.py` est écrit, pas joué.

### Ce que le joueur voit avec les réglages par défaut (M1)
- Case host « Show the mods of the game to the players » (`PublishMods`, cochée) : l'host écrit la liste de la
  partie dans son salon Steam et l'envoie à chaque invité avant le monde. La liste est celle du dépôt
  (`modlist.txt`) quand le monde vient d'un dépôt, sinon les mods de l'host.
- Onglet Lobby : sous chaque partie, « 6 mods » ou « 6 mods, 2 missing here ».
- Un invité refusé (actes différents) lit dans la fenêtre du refus, par nom : les mods de l'host qui lui manquent,
  ceux à installer à la main, ceux qu'il a en trop. Le journal a les pages du Workshop.
- Qui prend le monde du dépôt avec une liste différente de la sienne lit une ligne : « n mods of this world are not
  loaded here: … ». Il héberge quand même.
- Rien d'autre ne change : ce qui bloque reste la comparaison des actes, inchangée.

### Fichier par fichier
| Fichier | Ce qui a changé |
|---|---|
| `Helper/ModListFile.cs` (neuf) | Lit `modlist.txt`, sans rien du jeu (compilé aussi par `github_depot_cli`). Toute ligne avec `filedetails/?id=<nombre>` est un mod, titre = la ligne d'avant ou ce qui précède le lien ; `#` = commentaire ; ligne « installed by hand » = mod sans numéro ; la ligne du fork et son numéro d'origine 3773298709 sont écartés ; un titre ne garde ni balise ni accolade, 60 caractères au plus. |
| `Helper/ModList.cs` | `Here` (mods actifs sans le fork : id, numéro Workshop, titre), `Reference` (liste publiée), `Compact` (salon : `mods sans numéro;numéros`, seulement un compte au-delà de 4000 caractères), `Summary` (ligne du salon), `Compare` (trois listes + une ligne Information), `Tell`, `Lines`. `World` = liste du dépôt ; `Bench` (Debug) = liste donnée par le banc. |
| `Helper/GitHubDepot.cs` | Commande `MODS` : rend `modlist.txt` tel quel, texte vide s'il n'existe pas ; ne tient ni n'écrit rien. |
| `Helper/SaveDepot.cs` | `Take` lit la liste du monde (`WorldMods` : GitHub ou fichier du dépôt en dossier), compare, la garde dans `ModList.World`, dit ce qui manque. Dépôt en dossier : `modlist.txt` écrit à côté de `world/` s'il n'existe pas, jamais remplacé. |
| `Models/SourceValidation/SourceValidationRequest.cs` | Champ `Mods` (`[Key(3)]`, texte, nul si l'host ne publie pas). Pas de nouveau message, donc rien à ajouter à la table des paquets permis. |
| `Net/Host/ElinNetHostIntegrity.cs` | L'host remplit `Mods`. |
| `Net/Client/ElinNetClientValidator.cs` | L'invité compare à la réception de la demande (avant toute copie du monde) ; le refus ajoute les trois lignes de noms. |
| `Net/Client/ElinNetClient.cs` | `ReturnTo` : où est la partie, en mots (`lobby id`, `address hôte:port`, `port n` au banc). |
| `Net/Steam/SteamNetLobby/SteamNetLobbyManager.cs`, `Common/EmpLobbyData.cs` | Clé `EmpMods` écrite à la création du salon. |
| `Components/Tabs/*` | Ligne des mods dans la liste des parties ; case `PublishMods` (Server Setting) ; case `FetchMods` (Client Settings). |
| `Emp/EmpConfig.cs` | `Server.PublishMods` (vrai), `Client.FetchMods` (faux). |
| `Helper/ModFetch.cs` (neuf) | Toute la tranche M2, voir plus bas. |
| `Emp/ElinWith105gunAndRedgeioz.cs`, `Net/NetShutdown.cs` | `ModFetch.Boot()` au démarrage du mod, `ModFetch.Update()` à chaque image (sans patch : en Release les patches n'existent que pendant une session), `ModFetch.OnQuit()` à la fermeture. |
| `dev/_tools/github_depot_cli`, `depot_github_test.py` | Commandes `MODS <fichier>` et `PARSE <fichier>` ; étape G16. |
| `dev/_tools/modlist_suite.py` (neuf, pas joué) | L1 à L5, voir son en-tête. |
| `package/LangMod` | 16 textes `emp_ui_mods_*`, `emp_ui_sv_*_publish_mods`, `emp_ui_cl_*fetch_mods` (anglais, japonais, chinois). |

### M2 : ce que fait `FetchMods` quand il est coché (jamais joué)
Déclenché à deux endroits : l'invité reçoit la liste de l'host et il lui manque au moins un mod du Workshop ; ou
un joueur prend le monde du dépôt et il lui en manque un (la liste est lue AVANT de tenir le monde). Aussi : invité
refusé pour ses actes alors qu'il ne lui manque rien mais qu'il a des mods en trop (relance sans eux, rien à
télécharger). Jamais dans un jeu déjà relancé une fois, ni après un abandon dans le même jeu.

Fichiers : `L` = `loadorder.txt` à côté d'`Elin.exe` ; `P` = `loadorder.elintogether-player.txt` au même endroit ;
`T` = `LocalLow\Lafrontier\Elin\ElinMP\modsession.txt` (date, où revenir, liste appliquée) ; `J` = jonctions
`Package\EmpSession_<numéro>` vers le dossier que Steam a téléchargé.

| Étape | Ce qui est sur le disque après | Un plantage juste après laisse | Le démarrage suivant |
|---|---|---|---|
| 1. `Hide` : `L` reçoit une ligne `dossier,0` pour chaque dossier qui va apparaître (dossier du Workshop, et jonction si elle sera faite) | `L` = liste du joueur + lignes pour des dossiers absents | rien de visible : une ligne pour un dossier absent est ignorée | jeu du joueur, inchangé |
| 2. Téléchargements (`SteamUGC.DownloadItem`, un par un, ligne à l'écran, Échap annule ; arrêt si rien ne bouge 20 s hors file d'attente, 90 s dans tous les cas, 15 min au total) | dossiers dans le cache de Steam, éteints par les lignes de l'étape 1 | des mods téléchargés mais éteints | jeu du joueur, inchangé |
| 3. Ticket `T` | + `T` | `T` seul | `T` lu puis effacé ; le jeu revient dans la partie avec les mods du joueur (pas de seconde relance) |
| 4. `P` = copie de `L` | + `P` (identique à `L`) | `P` et `L` identiques | `P` remis sur `L`, effacé |
| 5. Jonctions `J` (seulement si le jeu ne charge que les dossiers abonnés : réglage « sync mods » coché et au moins un abonnement) | + `J`, éteintes par les lignes de l'étape 1 | des jonctions éteintes | elles sont retirées (la cible n'est pas touchée) |
| 6. `L` = liste de session (première ligne `# elintogether session`) : tous les mods connus, allumés seulement si la liste de la partie les a ; ElinTogether, YK Framework et leurs dépendances restent comme le joueur les a ; ce qui a été téléchargé n'y est pas listé (non listé = allumé) | `L` = session, `P` = joueur | la liste de session sur le disque | le jeu démarre avec les mods de la partie, UNE fois : `Boot` remet `P` sur `L` aussitôt, le dit à l'écran, et revient dans la partie si le ticket a moins de 30 minutes |
| 7. Relance (un `cmd` caché attend la fin d'Elin puis ouvre `steam://rungameid/2135150`) et fermeture d'Elin | comme 6 | comme 6 | comme 6 |
| 8. Dans le jeu relancé, dès qu'ElinTogether démarre (`Boot`) : `P` remis sur `L`, `P` effacé, `T` lu puis effacé, « Mod Viewer » empêché de réécrire `L` | `L` = liste du joueur ; `J` encore là (le jeu lit ses mods à travers elles) | les jonctions, éteintes dans `L` | jonctions retirées, jeu du joueur |
| 9. Fermeture normale du jeu relancé | jonctions retirées ; restent les dossiers du cache de Steam, éteints dans `L` | | jeu du joueur |

Abandon propre (téléchargement refusé, bloqué, annulé, écriture impossible) : `T`, `P`, `J` sont défaits, `L` garde
seulement les lignes de l'étape 1 ; un message le dit, et la partie est rejointe tout de suite sans M2 (le refus
éventuel nomme alors les mods).

**Ce que le démarrage ne répare PAS tout seul** : si le jeu relancé plante AVANT qu'ElinTogether démarre (un mod
téléchargé casse le démarrage), `L` reste la liste de session à chaque lancement. Réparation à la main : copier
`loadorder.elintogether-player.txt` sur `loadorder.txt`, effacer les dossiers `Package\EmpSession_*` (ce sont des
liens : les effacer ne touche pas le Workshop).

**Trace durable chez le joueur** : son `loadorder.txt` garde une ligne `dossier,0` par mod téléchargé. Sans elle, avec
« sync mods » décoché (le réglage par défaut du jeu), tout dossier du cache de Steam serait chargé dans ses parties
solo. S'il s'abonne plus tard à ce mod, il le verra « désactivé » dans le Mod Viewer et devra le cocher.

Jamais : `SubscribeItem`, `UnsubscribeItem`, suppression d'un dossier du Workshop, suppression récursive.

### Ce qui n'a PAS pu être vérifié (à essayer avec un ami avant de cocher `FetchMods` par défaut)
1. `SteamUGC.DownloadItem` sur un mod auquel le compte n'est pas abonné, depuis Elin : le téléchargement part,
   les états (`DownloadPending`, `Downloading`, `Installed`) se suivent comme supposé, `GetItemInstallInfo` donne le
   dossier, la ligne de progression bouge.
2. Steam garde-t-il ce dossier jusqu'à la relance (elle passe par Steam) ? S'il le nettoie, le mod manque encore
   après la relance : le jeu ne relance pas deux fois, le message de M1 s'affiche.
3. La relance : le `cmd` caché est un enfant d'Elin ; Steam peut considérer le jeu « encore en cours » tant qu'il
   vit et refuser `steam://rungameid`. La ligne de commande a été essayée hors du jeu avec `echo` à la place du
   lancement (elle attend bien la fin du processus). Si la relance ne part pas : le joueur relance Elin lui-même,
   le ticket le ramène (30 minutes).
4. La jonction dans le Mono du jeu : `File.GetAttributes` dit bien `ReparsePoint`, `Directory.Delete(lien, false)`
   retire le lien seul pendant que le jeu a des fichiers ouverts dessous, le jeu et BepInEx chargent un mod (DLL
   comprise) à travers elle. Vérifié avec .NET hors du jeu, pas avec Mono.
5. Que `NeedsLinks` prédit bien ce que le jeu fera au démarrage suivant (réglage « sync mods », zéro abonnement).
6. Qu'une ligne `dossier,0` écrite par le mod désigne le même chemin que celui du jeu (bibliothèque Steam sur un
   autre disque, majuscules, barres) : sinon le mod téléchargé reste allumé en solo.
7. Le retour tout seul : `ConnectLobby` deux secondes après l'écran titre, le salon encore valide, la poignée de
   main qui ne trouve plus rien de manquant ; pour le dépôt : `Take` puis ouverture de la session.
8. Le « Mod Viewer » pendant une session : son enregistrement est bien empêché, et le jeu le supporte.
9. L'ordre de chargement n'est pas celui de l'host (la liste du dépôt est triée par titre) : deux mods qui
   changent la même ligne d'une table peuvent donner un résultat différent des deux côtés.
10. Qu'ElinTogether et YK Framework restent allumés dans la liste de session sur une vraie installation (repérés
    par leurs DLL ; le fork ne déclare pas YK Framework dans son `package.xml`).
11. La ligne « n mods, k missing » de la liste des parties avec un vrai second compte (au banc, les deux fenêtres ont
    le même compte et se rejoignent par le port local).
12. Steam Deck / Proton : `cmd`, `mklink /J`, `tasklist`, `find`. Probablement à faire à la main là-bas.
13. Antivirus devant un `cmd` caché lancé par un jeu.
14. Au banc, toutes les fenêtres partagent `LocalLow` : un ticket écrit par l'une serait lu par l'autre. Ne pas
    cocher `FetchMods` sur le banc sans y penser.

### Pas fait
- Serveur de dépôt (Elin Together Server) : pas de `modlist.txt`, il faudrait une commande de plus dans son
  protocole. GitHub et dossier : faits.
- Titre et taille demandés à Steam avant de télécharger (les titres affichés sont ceux de la liste reçue). Ce qui
  est vérifié : numéro valide, 200 mods au plus, le dossier reçu contient un `package.xml`.
- Reproduire l'ordre de chargement de l'host.
- Relance automatique d'une copie qui démarre sans Steam (`steam_appid.txt`, le banc) : message « relancez Elin ».
- Mise à jour de la clé du salon si la case change en cours de session (elle est écrite à la création du salon).
- Le message de la prise du monde n'est dans aucune suite (à ajouter à `depot_suite.py`).
- `MODLOG.md`, `DOCUMENTATION.md`, `HANDOFF.md` : pas mis à jour par ce lot.
