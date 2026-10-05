# Plan : garder le monde partagé « tout par Steam »

Date de la recherche : 2026-10-05. Rien n'a été envoyé à Steam, rien n'a été publié, aucun jeu lancé.
Les pages Steamworks ont été lues en brut (texte complet), pas seulement résumées.
Les citations sont paraphrasées en français ; l'URL et l'endroit de la page sont donnés pour que tu puisses relire.

## Verdict en premier

| Idée | Verdict |
|---|---|
| (a) Un objet Workshop dont tous les joueurs sont « contributeurs » | **Pas faisable comme tu l'imagines, sauf si un test à deux comptes prouve le contraire.** Rien d'officiel ne dit qu'un contributeur peut envoyer le contenu ; plusieurs sources disent que non (dernière : juillet 2025). |
| (a bis) Un objet Workshop PAR JOUEUR, visibilité « Amis seulement », chacun met à jour le sien, on lit le plus récent | **Faisable**, avec limites (voir plus bas). C'est la vraie version « tout Steam » de ton idée. |
| (b) Partage Steam Cloud (`FileShare` / `UGCDownload`) | **Pas faisable utilement.** L'API existe encore, mais il faut transmettre un « handle » à l'autre joueur, et rien de permanent ne le garde. Pas mieux que (c). |
| (c) Chaque joueur garde une copie du monde, envoyée en pair à pair, avec un numéro de version | **Faisable, c'est le plus sûr.** Limite : il faut que celui qui a la dernière version soit en ligne au moment où quelqu'un d'autre veut héberger. Le mod a déjà tout ce qu'il faut côté réseau. |

Recommandation : faire (c) d'abord (aucun risque Steam), puis (a bis) comme « rangement à froid » facultatif, et lancer en parallèle le test de 10 minutes pour (a).

---

## Question 1. Un contributeur peut-il METTRE À JOUR le contenu ?

Faits sourcés :

1. La documentation officielle ne parle pas des contributeurs. Dans `ISteamUGC` (https://partner.steamgames.com/doc/api/ISteamUGC) les mots « contributor » et « collaborator » n'apparaissent nulle part. Il n'existe aucune fonction pour ajouter un contributeur : ça se fait à la main sur la page de l'objet (menu « Owner Controls » / « Add/Remove Contributors »). Je n'ai trouvé aucune API pour ça.
2. Le guide d'implémentation (https://partner.steamgames.com/doc/features/workshop/implementation, section « Updating a Workshop Item », dernière phrase) dit qu'il faut vérifier l'accord Workshop « au cas où l'utilisateur n'a pas créé l'objet à l'origine mais modifie un objet existant ». Cela montre que Valve imagine qu'un non-créateur modifie un objet, mais la page ne dit pas qui en a le droit.
3. Les codes d'erreur de `SubmitItemUpdateResult_t` (ISteamUGC, section des callbacks) : `k_EResultAccessDenied` est documenté seulement pour « l'utilisateur ne possède pas de licence pour l'application ». Aucun code documenté pour « tu n'es pas le propriétaire de l'objet ».
4. Sources communautaires, du plus ancien au plus récent :
   - 2015, https://steamcommunity.com/discussions/forum/10/618456760263925033/ : un contributeur ne peut ni modifier titre/description/images, ni publier de mise à jour ; « mon ami n'a pas pu rien modifier ».
   - 2016, https://steamcommunity.com/app/286160/discussions/0/215439774873034464/ (Tabletop Simulator) : le rôle « contributeur » ne sert qu'à donner du crédit ; l'envoi par le jeu affiche un faux « succès » mais rien ne change.
   - 2016, https://forums.unrealengine.com/t/is-it-possible-to-have-multiple-contributors-to-a-steam-workshop-item/56555 : « on ne peut pas avoir plusieurs comptes Steam qui mettent à jour un même objet ».
   - 2019, https://discourse.stonehearth.net/t/co-authors-cant-update-workshop-mods/39325 : les co-auteurs ne peuvent pas mettre à jour, aucun message d'erreur (échec silencieux).
   - 2020 (verrouillé en 2024), https://steamcommunity.com/discussions/forum/0/2149847423930469260/ : le propriétaire seul peut « mettre à jour le mod » ; le contributeur peut éditer les liens, les objets requis, et modérer les commentaires.
   - 12 juillet 2025, https://steamcommunity.com/discussions/forum/10/546740620659585483/ (« Co-Authors need the ability to upload files », verrouillé en mars 2026) : les co-auteurs peuvent maintenant modifier la description et les images (changement « d'il y a quelques années »), mais **pas** envoyer ni modifier les fichiers du mod.
   - **Contre-indication** : dans le même fil, un message du 15 août 2025 dit qu'un co-auteur peut en fait mettre à jour, que c'est RimWorld qui l'en empêche (le jeu vérifie le propriétaire), et que l'auteur du message l'a fait après avoir modifié RimWorld. Et dans https://steamcommunity.com/discussions/forum/10/1291817208504654487/ un message du 12 janvier 2024 dit « c'est possible maintenant, sauf l'image d'aperçu ». Ce sont deux témoignages isolés, non confirmés par Valve.
5. Condition d'application : l'appli doit avoir `ISteamUGC` activé dans la config Workshop de l'appli (sinon `k_EResultInvalidParam`), l'utilisateur doit posséder Elin (sinon `k_EResultAccessDenied`), et il doit avoir accepté l'accord Workshop (`m_bUserNeedsToAcceptWorkshopLegalAgreement`). Aucune source ne parle d'un réglage « autoriser les contributeurs » côté application.

Conclusion Q1 : par le site, les contributeurs ne peuvent pas envoyer de fichier (source la plus récente et la plus solide : juillet 2025). Par l'API, **deux témoignages disent que ça passe, un en 2024 et un en 2025, jamais confirmé officiellement**. Le jeu Elin lui-même refuse : son code ne met à jour que si `item.Owner.IsMe` (Steam.cs, `CreateOrUpdateUserContent`). Si ça marche, ce sera donc seulement en appelant l'API depuis le mod sans passer par cette vérification. Code d'erreur attendu en cas de refus : inconnu (peut-être `k_EResultAccessDenied`, peut-être un faux succès comme en 2016).

### Test à faire pour trancher (10 minutes, deux comptes qui possèdent Elin)
1. Compte A crée un objet (visibilité Privé) avec un petit dossier et ajoute le compte B comme contributeur sur le site.
2. Compte B appelle `StartItemUpdate` + `SetItemContent` (sans `SetItemPreview`) + `SubmitItemUpdate` sur l'ID de A.
3. Regarder `m_eResult` du callback, puis, côté A, si `m_rtimeUpdated` a changé et si le contenu est nouveau.
4. Refaire avec visibilité « Amis seulement ».

---

## Question 2. Visibilité

Faits sourcés (https://partner.steamgames.com/doc/api/ISteamRemoteStorage, énumération `ERemoteStoragePublishedFileVisibility`) :
- Public : visible par tous.
- Amis seulement : « visible aux amis seulement ».
- Privé : « visible seulement par le créateur ». La page ajoute que c'est le plus proche d'une suppression via l'API.
- Non répertorié (Unlisted) : visible par tous, mais **non renvoyé dans les requêtes globales**.

Ce que ça donne pour les contributeurs et les amis :
- Privé et contributeurs : la doc officielle dit « créateur » seulement. Une source communautaire (https://steamcommunity.com/app/431960/discussions/1/4354495041490085972/, réponse d'un utilisateur) dit que « caché » (Hidden) est visible par le créateur, les admins et « toute personne marquée comme créateur ». Non officiel.
- Amis seulement : un fil de 2016 (https://steamcommunity.com/discussions/forum/1/392183857617140034/) dit que les amis peuvent voir et s'abonner. Non officiel mais cohérent avec la doc.
- Télécharger sans s'abonner : oui pour `DownloadItem`. La doc (ISteamUGC et guide d'implémentation) dit que si l'utilisateur n'est pas abonné, l'objet est téléchargé et gardé en cache temporairement. L'exemple donné est un serveur de jeu anonyme ; rien n'interdit un joueur normal, mais l'exemple n'est pas le même cas (à tester).
- Non répertorié et appli : le même fil Wallpaper Engine dit que l'option « Unlisted » est désactivée « depuis presque deux ans » pour ce jeu (message de 2024). On ne sait pas si c'est un réglage de l'appli ou un changement de Valve. Le code d'Elin (`Steam.cs`, `CreateItemData`) sait pourtant envoyer en `Unlisted`, `Private` et `FriendsOnly`, donc au moins l'API ne le refuse pas dans le code du jeu. Pas testé.
- Regarder les objets d'un ami : `CreateQueryUserUGCRequest(accountID, k_EUserUGCList_Published, ...)` (ISteamUGC) est permis pour un autre compte ; seules les listes « votés » et « abonnés » sont réservées à soi. Donc on peut lister les objets publiés d'un ami, tant que leur visibilité nous les montre (Amis seulement oui).

---

## Question 3. Délais et version distante

Faits sourcés :
- Après `SubmitItemUpdate`, **aucun délai n'est documenté**. Un fil de 2016 (https://steamcommunity.com/app/222880/discussions/2/312265327162452138/) : « ça varie beaucoup », environ 2 minutes d'attente conseillées, un autre joueur dit que ça a été plus long et qu'il s'est désabonné puis réabonné pour avoir la nouvelle version tout de suite. Ancien, un seul jeu.
- `DownloadItem(id, highPriority)` : la doc dit seulement que `highPriority` met en pause les autres téléchargements Steam et commence tout de suite ce téléchargement. Pour une mise à jour, la doc dit qu'on l'appelle quand l'état est `k_EItemStateNeedsUpdate`. **Rien ne dit qu'il force Steam à vérifier le serveur.** À attendre le callback `DownloadItemResult_t` avant de lire le dossier.
- `k_EItemStateNeedsUpdate` (valeur 8) : « le créateur a mis à jour le contenu, ou pas encore installé » (ISteamUGC, énumération `EItemState`).
- Version distante : `SteamUGCDetails_t.m_rtimeUpdated` (heure Unix de la dernière mise à jour) renvoyé par `GetQueryUGCResult` après une requête (`CreateQueryUGCDetailsRequest` sur l'ID). La version locale se lit avec `GetItemInstallInfo` (`punTimeStamp`). Pour mettre un vrai numéro de version : `SetItemMetadata` (jusqu'à 10 000 octets, constante `k_cchDeveloperMetadataMax`, vue dans Steamworks.NET `SteamConstants.cs`), ou une étiquette clé-valeur ; le guide dit que ces métadonnées reviennent dans les requêtes sans télécharger le contenu.

Conséquence : ne pas compter sur la mise à jour automatique de Steam. Toujours demander l'état au serveur (requête), comparer le numéro, puis `DownloadItem` et attendre le callback.

---

## Question 4. Limites, modération, usage « stockage de sauvegarde »

Faits sourcés :
- Taille d'un objet : **je n'ai trouvé aucune limite de taille d'objet dans la doc officielle**. Limites trouvées : titre 129 caractères, description 8 000, métadonnées 10 000, aperçu moins de 1 Mo (`k_EResultLimitExceeded` « l'aperçu est trop gros » ou « pas assez de place dans le Steam Cloud de l'utilisateur », ISteamUGC). Donc l'envoi peut échouer si le Cloud de l'**envoyeur** est plein ; un zip de 1 à 20 Mo semble raisonnable mais n'est pas garanti.
- Fréquence : aucune limite de débit documentée. Des forums parlent d'un blocage temporaire si on envoie trop de fois (je n'ai pas pu relire la source ; voir « Non vérifié »).
- Modération : un objet Workshop d'Elin est visible dans le Workshop d'Elin (sauf Privé/Amis/Non répertorié). L'application peut lire `m_bBanned` (le `ModManager` d'Elin le fait). Valve ou le développeur d'Elin peut donc retirer un objet. Nous n'avons aucune garantie contre ça.
- L'accord Workshop doit être accepté par chaque envoyeur, sinon l'objet reste caché (guide d'implémentation, section « Workshop Legal Agreement »).
- Usage comme stockage de sauvegarde : je n'ai **trouvé aucune règle de Valve** qui l'interdise ou l'autorise. Preuve de tolérance indirecte : le produit « SaveSync » (https://store.steampowered.com/app/3832010/, accès anticipé depuis le 19 septembre 2025) est vendu sur Steam et range les sauvegardes de jeux coopératifs dans le Workshop, « chiffrées, non répertoriées et privées par défaut », avec historique de qui a modifié. C'est le cas exact de ton idée, et il existe en vente. Attention : son Workshop est sans doute celui de SaveSync lui-même, pas celui du jeu partagé, et la page ne dit pas comment les amis ont le droit d'écrire.

---

## Question 5. Autres moyens « tout Steam »

- Steam Cloud (`ISteamRemoteStorage`) : https://partner.steamgames.com/doc/features/cloud dit que le quota est appliqué **par utilisateur et par jeu**, et que l'API Cloud isole les fichiers de chaque utilisateur les uns des autres. Un fichier : 100 Mio au maximum, 200 Mio au total (doc `ISteamRemoteStorage`, constante `k_unMaxCloudFileChunkSize`). Le quota réel est fixé par le développeur d'Elin ; nous ne le connaissons pas. Elin utilise déjà le Cloud (le mod lit `cloud.zip` dans `Helper/CharaImport.cs`).
- Partage de fichier Cloud : `FileShare(fichier)` renvoie un handle (`m_hFileUGCHandle`), « qui peut être partagé avec des utilisateurs et des fonctions » (callback `RemoteStorageFileShareResult_t`) ; l'autre joueur appelle `UGCDownload(handle)`. Ces fonctions sont toujours dans la doc, sans mention « obsolète ». Mais la doc ne dit rien de la durée de vie du handle, ni de limites, ni de l'accès entre amis. Et surtout : il faut faire parvenir ce handle au joueur. Aucun endroit permanent ne le garde (voir plus bas).
- Données de salon : `SetLobbyData` accepte une valeur de 8 192 caractères au plus (`k_cubChatMetadataMax`, Steamworks.NET) et une clé de 255 (doc `ISteamMatchmaking`, constante `k_nMaxLobbyKeyLength`). Impossible d'y mettre un zip. Le salon disparaît quand son dernier membre part. On peut y mettre un numéro de version, un hash, ou un handle, tant que quelqu'un est présent.
- Présence enrichie (`SetRichPresence`) : 256 caractères par valeur, 30 clés (Steamworks.NET). Visible des amis seulement tant que le joueur est en ligne.
- Pair à pair direct : `ISteamNetworkingSockets` (déjà utilisé par le mod) : un message fiable peut faire jusqu'à 512 Kio (`k_cbMaxSteamNetworkingSocketsMessageSizeSend`, vu dans le fichier public `steamnetworkingtypes.h` de GameNetworkingSockets). Un zip de 20 Mo = environ 40 morceaux, à découper et à réassembler. La doc `ISteamNetworkingMessages` dit que c'est « comme UDP » et que `ISteamNetworkingSockets` convient mieux quand on a besoin de contrôle ; on garde donc les sockets du mod.

Aucune de ces voies ne garde quelque chose quand tous les joueurs sont hors ligne, sauf le Workshop. C'est la seule vraie différence entre (a bis) et (c).

---

## Question 6. Dans le code local

### Le mod (G:\ElinMods\ElinTogether\ElinTogether)
- Aucun appel à `SteamUGC` ni à `SteamRemoteStorage`. Le mod utilise `Steamworks.NET` (`using Steamworks`) et la couche Heathen (`HeathenEngineering.SteamworksIntegration`) que le jeu embarque.
- Salons : `Net/Steam/SteamNetLobby/SteamNetLobbyManager.cs` (`CreateLobby`, `JoinLobby`, filtres de liste, rich presence `connect`).
- Transport : `Net/Steam/SteamNetManager/*` (`CreateListenSocketP2P`, `ConnectP2P`, groupe de sondage) et `Net/Steam/SteamNetPeer/SteamNetPeer.cs` (`SendMessageToConnection`, tampon qui grandit). `Emp/ElinWith105gunAndRedgeioz.cs` appelle `SteamNetworkingUtils.InitRelayNetworkAccess()`.
- **Il existe déjà un dépôt de monde** : `Helper/SaveDepot.cs` (452 lignes). Il sait faire `Zip(save)`, `Unzip(bytes, dossier)` (avec protection contre les chemins sortants), un verrou, `HeldBy()`, `Take()`, `Put()`, `TakeFrom(adresse)`, deux backends (serveur `host:port` ou dossier partagé). C'est là qu'il faut brancher un backend Steam. Appelé depuis `Components/Tabs/TabLobbyBrowser.cs`, `Emp/EmpServer.cs`, `Patches/Synchronization/CoreSynchronizationContext.cs`.

### Le jeu (G:\ElinMods\ElinTogether\dev\_decomp\Elin et Plugins.BaseCore)
- `ModManager.cs` : le dossier Workshop est `<Steam>/../../workshop/content/2135150` (ligne 80). Au démarrage, si le joueur a des abonnements, le jeu les interroge par groupes de 50 (`QuerySubscriptions`), puis télécharge ceux qui ne sont pas installés ou qui `NeedsUpdate` (`DownloadSubscriptions`), avec écran de chargement.
- **Un objet sans `package.xml` est ignoré proprement.** `BaseModPackage.Init()` renvoie faux si `package.xml` est absent (BaseModPackage.cs ligne 146) ; `InitPackagesMeta` (ModManager.cs lignes 502-531) écrit « Not a package » dans le journal, retire le dossier de la liste et affiche « Ignored N folder(s) without a usable package.xml » à l'écran de chargement. Ce n'est pas une erreur. Seul un `package.xml` présent mais mal formé arrête le jeu (`Halt`, lignes 387-397). Un zip de sauvegarde sans `package.xml` ne risque donc rien.
- Détail à connaître : tout objet Workshop auquel le joueur est ABONNÉ est téléchargé à chaque démarrage du jeu s'il a changé. Avec (a bis), mieux vaut ne pas abonner : utiliser `DownloadItem` sans abonnement (cache temporaire).
- Code de publication déjà présent : `Steam.cs` (lignes 132-300) : `CreateUserContent` → `QueryAllMyPublished` (via `UgcQuery.GetMyPublished()`) → `CreateOrUpdateUserContent` (cherche un objet à soi dont l'étiquette clé-valeur `id` égale l'identifiant du paquet, sinon `Create`) → `CreateItemData` (Heathen `WorkshopItemData` : appId, titre, description, dossier de contenu, aperçu `preview.jpg`, métadonnée, tags, visibilité Public/Unlisted/Private/FriendsOnly). Réutilisable en esprit, **pas tel quel** : il est lié à un `BaseModPackage` et à un dossier de mod, il exige `item.Owner.IsMe`, il impose un aperçu. Il faut écrire notre propre appel avec les mêmes classes Heathen (`WorkshopItemData.Create` / `.Update`, `UgcQuery`), avec un dossier temporaire contenant le zip.

---

## Ce qu'il faudrait écrire, pour chaque option

### (c) Copie chez chaque joueur + pair à pair + numéro de version (à faire en premier)
1. Un fichier `world.version` à côté de la copie locale : compteur (entier croissant), hash du zip, date, nom du dernier hôte. Le compteur augmente à chaque sauvegarde de l'hôte.
2. À la fin d'une session (et à intervalle), l'hôte envoie le zip à chaque invité connecté ; les invités l'écrivent dans leur dossier `world_depot` (réutiliser `SaveDepot.Zip/Unzip`). Découpage en morceaux de 256 Kio, accusé de réception par morceau, contrôle du hash à la fin, écriture dans un fichier `.part` puis renommage.
3. À l'ouverture d'un salon : chacun annonce son compteur (dans `SetLobbyData` ou en premier message). Celui qui a le compteur le plus haut envoie son zip à celui qui veut héberger. Si le futur hôte n'a pas le plus haut compteur et que le détenteur est absent : avertissement clair « la dernière version est chez X ».
4. Réutiliser `SaveDepot.HeldBy/Take/Put` comme interface, avec un nouveau backend « pair à pair ». Taille : environ 200 à 300 lignes. Aucun nouveau service Steam.
5. Garde-fous : refuser d'écraser une version plus haute sans accord ; garder la version précédente en `.old`.

### (a bis) Un objet Workshop par joueur, Amis seulement, lecture du plus récent (rangement à froid, facultatif)
1. Chaque joueur, après sa session d'hôte : crée (ou met à jour) SON objet : dossier temporaire avec `world.zip` + `world.version`, visibilité Amis seulement, `SetItemMetadata` = compteur + hash + date, sans aperçu si possible (à tester). Via les classes Heathen `WorkshopItemData` comme `Steam.cs`.
2. Avant d'héberger : pour chaque ami du groupe (liste de SteamID stockée dans les réglages du mod, ou amis présents dans le salon), `CreateQueryUserUGCRequest(compte, Published, ...)`, lire `m_rtimeUpdated` et la métadonnée, garder la plus haute version.
3. `DownloadItem(id, true)` sans abonnement, attendre `DownloadItemResult_t`, lire le dossier via `GetItemInstallInfo`, puis `Unzip`.
4. Premier lancement : accepter l'accord Workshop (ouvrir `steam://url/CommunityFilePage/<id>` via `ActivateGameOverlayToWebPage`, comme le recommande le guide).
5. Limites : ne marche qu'entre AMIS Steam (pas de non-amis) ; un objet par personne dans le Workshop d'Elin ; Valve ou l'éditeur d'Elin peut le retirer ; délai de propagation non garanti ; l'envoyeur doit posséder Elin et avoir de la place Cloud ; taille réelle autorisée non confirmée.
6. Environ 300 à 400 lignes. À brancher comme backend de `SaveDepot` à côté de (c).

### (a) Un seul objet, tous contributeurs
Seulement si le test de la question 1 réussit avec le compte B. Alors : un seul objet créé par le premier joueur ; les autres appellent `StartItemUpdate/SetItemContent/SubmitItemUpdate` sur le même ID ; il faut aussi diffuser l'ID (dans `SetLobbyData` et dans les réglages du mod) et ajouter à la main chaque ami comme contributeur sur le site (pas d'API). Même code que (a bis) sauf l'étape « lister les objets des amis ». Si le test échoue, ne pas le faire. Même si le test réussit, rien ne garantit que Valve ne verrouille pas ça plus tard (témoignages contradictoires).

### (b) Partage Cloud
À écrire seulement pour mémoire : `FileWrite` du zip puis `FileShare` puis envoi du handle au joueur, `UGCDownload` chez lui. Je déconseille : le handle doit voyager par un salon (donc quelqu'un doit être en ligne : même contrainte que (c), avec un risque en plus et des limites non documentées) et le quota Cloud d'Elin est inconnu.

---

## Non vérifié

- Qu'un contributeur puisse envoyer du contenu par l'API `ISteamUGC` : deux témoignages (janvier 2024, août 2025) le disent, sept sources plus anciennes ou plus officielles le contredisent ; aucun test fait. Le code d'erreur exact en cas de refus n'est pas connu.
- Qu'un fichier envoyé par un contributeur soit réellement visible des autres (et pas un faux succès comme en 2016).
- Qu'un joueur non abonné puisse `DownloadItem` un objet « Amis seulement » (la doc donne l'exemple d'un serveur de jeu anonyme, pas d'un joueur).
- Que les contributeurs voient un objet Privé (une seule source non officielle).
- Que « Non répertorié » soit activé pour Elin (désactivé pour Wallpaper Engine depuis environ 2022 ; cause inconnue).
- Les délais après `SubmitItemUpdate` : seulement des témoignages de 2016 sur un autre jeu (2 minutes à beaucoup plus). Que `DownloadItem(..., true)` force une vérification serveur : non documenté.
- Toute limite de taille d'objet ou de débit d'envoi : aucune trouvée dans la doc officielle. Un résumé de recherche parlait d'un blocage de 2 heures après trop d'envois ; je n'ai pas pu relire la page source (protégée par une vérification de navigateur). À ne pas croire sans test.
- Le quota Cloud d'Elin (réglé par son développeur) et son effet sur l'envoi de l'objet.
- La durée de vie d'un handle `FileShare` et son fonctionnement entre amis.
- Une règle de Valve sur l'usage du Workshop comme stockage de sauvegardes : aucune trouvée (ni pour, ni contre). Seule preuve : un produit en vente qui le fait (SaveSync), dont je n'ai pas vu le fonctionnement interne.
- Que `k_cubChatMetadataMax` = 8 192 : lu dans Steamworks.NET (`Steam.cs`), pas sur la page Steamworks qui cite la constante sans sa valeur. Même chose pour 512 Kio, 256 caractères de présence, 10 000 octets de métadonnées : valeurs lues dans les sources publiques des bibliothèques, pas sur partner.steamgames.com.
- Que l'envoi fonctionne sans fichier d'aperçu (le jeu en envoie toujours un).
- Mon analyse du code local est une lecture, rien n'a été compilé ni exécuté.
