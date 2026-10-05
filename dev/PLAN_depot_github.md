# Plan — dépôt GitHub privé (troisième sorte de dépôt)

Écrit le 2026-10-05, en lecture seule (rien compilé, rien lancé, aucun appel vers GitHub). Les chemins sont relatifs à
`G:\ElinMods\ElinTogether`. Ce qui est lu dans le code est dit « lu » ; ce qui vient de ma connaissance de l'API
GitHub, sans l'avoir essayé ici, est marqué **(à vérifier)** et repris dans « Non vérifié » à la fin.

## 0. En une phrase

Ajouter UN fichier (`ElinTogether/Helper/GitHubDepot.cs`) qui répond aux cinq mêmes demandes que le logiciel serveur
(`WHO`, `TAKE`, `PUT`, `BEAT`, `RELEASE`) mais en parlant à l'API « Contents » de GitHub, et brancher `SaveDepot.Ask`
dessus quand le réglage « Depot » vaut `github:proprietaire/depot`. Le reste de `SaveDepot` ne change presque pas.

---

## 1. Comment marche le dépôt aujourd'hui

### 1.1 Il n'y a pas d'interface : un seul fichier, deux `if`

Tout est dans `ElinTogether/Helper/SaveDepot.cs` (452 lignes, classe statique). Le serveur (le logiciel) et le dossier
sont deux branches du même code :

- `Remote` (`SaveDepot.cs:53`) : vrai si le réglage ressemble à `hote:port` (regex `^[^\\/\s]+:\d+$`) → logiciel
  `ElinTogetherServer.exe`. Sinon c'est un dossier.
- `Enabled` (`:62`) : réglage non vide ET (adresse OU dossier qui existe).
- `Holding` (`:64`) : le dépôt est activé, une partie tourne, c'est le monde `world_depot` (`WorldId`, `:29`) et on
  n'est pas un client de session (donc c'est nous qui hébergeons).

Les opérations (le serveur les nomme en toutes lettres, le dossier les fait avec des fichiers) :

| Opération | Serveur (`dev/server/ElinTogetherServer.cs`, `Handle` `:141-191`) | Dossier (`SaveDepot.cs`) | Appelée par |
|---|---|---|---|
| lire l'état (qui héberge ?) | `WHO` `:147` | `HeldBy` `:70-87` : `host.txt` plus récent que 3 min | bouton Lobby (`TabLobbyBrowser.cs:25`), `Take` (`:94`), `Put` (`:187`), `TakeFrom` (`:159`) |
| prendre le verrou et le monde | `TAKE` `:149` (refuse si un autre tient, `NO empty` si pas de monde) | `Take` `:112-131` copie `world/` puis `Beat` | `Take` `:92`, aussi `EmpServer.cs:62` |
| rendre le monde (sauvegarde) | `PUT` `:161` (refuse si un autre tient ; si personne ne tient, un autre monde remplace l'ancien, gardé en `replaced-<date>.zip`) | `CopyTo` `:255-267` : écrit `world.new`, déplace l'ancien, échange | `OnSaved` `:384`, `Put` `:185`, `SendUnsent` `:173` |
| battement de cœur | `BEAT` `:175` | `Beat` `:373` réécrit `host.txt` | `Update` `:422` (chaque minute), `Take` |
| relâcher | `RELEASE` `:182` | `ReleaseAtTitle` `:435` supprime `host.txt` | retour à l'écran titre |

- Sauvegardes de secours : **côté serveur seulement** (`Store` `:251-281` : `replaced-<date>.zip` pour un monde remplacé,
  `world.1..3.zip` au plus une par 30 min). Le dossier garde `world.replaced-<date>` (`SaveDepot.cs:261`) quand on
  remplace. Le jeu, lui, garde sa copie locale `Save/world_depot` (`:43`) et un marqueur `world_depot.unsent` quand le
  dépôt n'a pas reçu la dernière sauvegarde (`:48`, `:222-238`) ; au prochain `Take`, le jeu propose de l'envoyer
  (`:99-110`, `SendUnsent` `:173`).
- Mot de passe : réglage `DepotPassword` (`EmpConfig.cs:57-61`), envoyé en clair en première ligne de chaque demande
  (`SaveDepot.cs:334`). Le serveur le vérifie avant d'allouer la mémoire (`ElinTogetherServer.cs:107`).

### 1.2 Où le type de dépôt est choisi

- Réglage `Client.DepotPath` (`ElinTogether/Emp/EmpConfig.cs:49-55`, déclaré `:281`), fichier
  `BepInEx\config\dk.elinplugins.elintogether.cfg` (vu : `DepotPath =` et `DepotPassword =` y sont, en clair).
- Onglet « Client Settings » : deux boutons, `TabClientConfiguration.cs:29-37` (dépôt) et `:39-47` (mot de passe,
  affiché `***`). La boîte de saisie du mot de passe est préremplie avec la valeur en clair (`:41`).
- Bouton « Join by address » : `TabLobbyBrowser.cs:32-43` → `JoinAddress` `:68` → `SaveDepot.TakeFrom` `:149`, qui met
  l'adresse dans le réglage, pose `WHO`, et retombe sur la connexion de jeu si personne ne répond. Un seul bouton
  pour les deux sortes de serveur depuis `018091d` (`DOCUMENTATION.md:330-331`).
- Bouton « Take the world… » (`TabLobbyBrowser.cs:24-29`) et « Put this save in the depot » (`:51-52`).
- Le logiciel sans Elin n'est pas touché par un type de plus : `Remote` ne reconnaît pas `github:…` (il y a un `/`).

### 1.3 Ce qui est envoyé

- **Un seul zip du dossier de sauvegarde**, fabriqué en mémoire (`Zip` `:274-291`, tous les fichiers sauf `Temp/`),
  envoyé tel quel après une ligne de longueur. Pas de plusieurs fichiers, pas de différence.
- Format du protocole TCP (`Ask` `:324-357`) : `mot de passe \n commande \n Me \n nom \n longueur \n` + octets ;
  réponse `OK|NO texte \n longueur \n` + octets. `Me` = `NomMachine:numéro de processus` (`:58`), le nom = nom du personnage.
- Taille : le serveur accepte jusqu'à 300 Mo (`ElinTogetherServer.cs:33`). Mesures lues sur cette machine :
  le monde de test `world_depot` = 28 fichiers, 1,03 Mo décompressé (dont `game.txt` 853 Ko) ; la vraie sauvegarde
  du nuage Steam de l'utilisateur `world_3` = 1,56 Mo (déjà un `cloud.zip`). Un monde qui s'agrandit (une carte
  explorée = une vingtaine de fichiers d'une dizaine de Ko, vu sur `world_depot/7/…`) devrait rester de l'ordre de
  quelques Mo (**à vérifier** sur une longue partie ; la doc dit « 74 Ko » pour un monde de test, `DOCUMENTATION.md:321`).
- Le même zip dans le serveur s'appelle `world.zip` : un monde du serveur peut donc être déposé tel quel dans GitHub.

### 1.4 À quels moments

- **Entrée** : `Take` (bouton Lobby, « Join by address », ou `-empserver world_depot` : `EmpServer.cs:62`). Il refuse si
  `HeldBy` dit qu'un autre héberge (`:94-97`), propose d'abord d'envoyer un `.unsent` (`:99`), puis télécharge, vide
  `Save/world_depot` (`IO.DeleteDirectory`), dézippe (`Unzip` `:293`, chemins gardés dans le dossier de sauvegarde),
  et appelle `Game.Load` (`:140`).
- **Chaque sauvegarde** : un correctif Harmony après `Game.Save` (`OnSaved`, `:384-399`) renvoie le monde si `Holding`.
  Elin sauvegarde au changement de carte (`dev/_decomp/Elin_23351/Chara.cs:3614-3622`), après un trésor de boss
  (`Chara.cs:6148`), au « retour au titre » (`Game.cs:1033-1036`), et à la main. Donc une sauvegarde par carte
  traversée, plus la sortie.
- **Battement** : `Update` (`:422-433`) chaque minute (`BeatSeconds` `:34`), appelé chaque image par
  `CoreSynchronizationContext.cs:30`.
- **Sortie** : `ReleaseAtTitle` (`:435-451`) à l'arrivée à l'écran titre : `RELEASE`.

### 1.5 Si l'hébergeur plante

- Le verrou n'est jamais repris de force : il **expire**. 3 minutes sans battement (`_lockLife` `SaveDepot.cs:33`,
  `LockLife` `ElinTogetherServer.cs:34`). Après cela, `WHO` dit « libre », un autre peut `TAKE` et récupère la dernière
  sauvegarde envoyée (chaque sauvegarde est allée au dépôt, donc on perd au plus ce qui s'est passé depuis la dernière
  sauvegarde).
- Si l'ancien hébergeur revient (il était seulement coupé) : son prochain `BEAT` ou `PUT` reçoit `NO held <nom>` →
  `Lost` (`:405-417`) : une boîte, une fois, « nom a repris le monde ». Ses sauvegardes restent sur son PC (`.unsent`).
- Le dossier a la faiblesse écrite dans le code (`:31-32`) : deux joueurs dans la même minute ont tous deux le monde.
  Le serveur a un vrai verrou (un seul processus, `lock (_gate)` `ElinTogetherServer.cs:129`).

### 1.6 Fil d'exécution : tout est sur le fil du jeu, le jeu se fige

- `Ask` est synchrone sur le fil principal : connexion jusqu'à 5 s (`:328`), lecture/écriture jusqu'à 60 s (`:333`).
  Deux commentaires l'admettent (`:147-148`, `:322-323`) : « un fil quand les mondes seront gros ou le lien lent ».
- `OnSaved` envoie donc le zip pendant que le jeu attend (quelques dixièmes de seconde pour 74 Ko, dit
  `DOCUMENTATION.md:321`). `Update` envoie un `BEAT` bloquant chaque minute. `HeldBy` est appelé **à la construction de
  l'onglet Lobby** (`TabLobbyBrowser.cs:25`) : un aller-retour réseau à chaque ouverture.
- Pour un serveur en réseau local ce n'est pas gênant. Pour GitHub (0,3 à 1 s par requête, plus en envoi), ce ne serait
  pas acceptable sur le fil du jeu : voir 2.6.

### 1.7 Tests existants

- `dev/_tools/depot_proto_test.py` : parle au `.exe` comme le jeu (`ask()` `:46-54`), 11 vérifications P1–P5 (monde mis,
  monde remplacé gardé à part, cinq sauvegardes, refus quand un autre héberge, mauvais mot de passe sans réserver de
  mémoire). ~10 s, sans Elin.
- `dev/_tools/depot_suite.py` : deux fenêtres Elin, D1–D6 (déposer, prendre, refus, sauvegarder, quitter, rejoindre).
  Dossier par défaut ; `DEPOT_SERVER=1` (`:42`, port 55558) pour le logiciel. Les eval de réglage passent par
  `EmpConfig+Client.DepotPath` (`:52`) et `JoinAddress` (`:57`).

---

## 2. Faire la même chose avec l'API REST de GitHub

### 2.1 Les trois voies, et celle que je recommande

| Voie | Écriture conditionnelle | Taille | Historique | Verdict |
|---|---|---|---|---|
| **Contents API** `PUT /repos/{o}/{r}/contents/{path}` avec `sha` | oui : `sha` = version attendue, sinon refus 409/422 | JSON + base64 (+33 %), limite fichier 100 Mo (**à vérifier** pour la limite de la requête) | un commit par écriture | **retenue** : deux verbes (GET, PUT), pas d'objets Git à construire |
| Git Data API (blobs, trees, commits, `PATCH /git/refs` non forcé) | oui, par la référence : un `PATCH` qui n'avance pas en ligne droite est refusé (422) | blob jusqu'à 100 Mo, base64 aussi | on choisit : on peut repartir d'un commit sans parent | 4 à 5 requêtes par écriture (blob, arbre, commit, référence) ; le verrou demande un commit entier par battement. Plus gros pour rien. Garder en réserve |
| Releases (assets) | non : suppression + envoi, pas de `sha` ; seul « le nom existe déjà » est refusé | jusqu'à 2 Go, binaire brut (pas de base64) | aucun historique dans le dépôt | bonne pour le monde (pas de grossissement du dépôt), mais **pas pour le verrou**, et la lecture passe par une redirection (le jeton ne doit pas la suivre) : deux mécanismes. Plan B si le dépôt grossit trop |

**Recommandation : Contents API pour les deux fichiers, `world.zip` et `lock.json`, sur la branche par défaut.**

### 2.2 Les appels utilisés (quatre en tout)

Tous avec `Authorization: Bearer <jeton>`, `User-Agent: ElinTogether` (GitHub refuse une requête sans User-Agent),
`Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`.

1. `GET /repos/{o}/{r}/contents/lock.json` → JSON `{sha, content(base64)}` ; 404 si absent. Le fichier est petit
   (< 1 Mo), le JSON par défaut suffit.
2. `GET /repos/{o}/{r}/contents/world.zip` avec `Accept: application/vnd.github.raw+json` → les octets du zip.
   **Obligatoire** : au-delà de 1 Mo le JSON par défaut ne renvoie plus `content`, et un vrai monde fait déjà 1,5 Mo
   (1.3). Pas de base64 au téléchargement.
3. `GET /repos/{o}/{r}/contents/` (liste de la racine) → `[{name, sha, size}, …]` : donne le `sha` actuel de
   `world.zip` sans le télécharger.
4. `PUT /repos/{o}/{r}/contents/{path}` avec `{"message", "content": base64, "sha": <version attendue>}` → 200 (changé) ou 201
   (créé), réponse avec `content.sha` (à garder pour la fois suivante). Sans `sha` sur un fichier qui existe : 422.
   `sha` périmé : 409. **C'est ce refus qui fait le verrou** (voir 2.3).

Le `sha` d'un fichier est son empreinte Git, `SHA1("blob " + taille + "\0" + octets)`. On n'a pas besoin de la
calculer : on la lit (appels 1, 3, 4).

### 2.3 Le verrou devient sûr

Fichier `lock.json` : `{"id": "<Me>", "name": "<nom du joueur>", "beat": "<date UTC>"}`. Une écriture avec `id` vide =
« libre » (un verbe de moins que `DELETE`).

- **Prendre le verrou** = lire `lock.json` (garder son `sha`), décider (libre ? expiré ? à moi ?), puis `PUT` avec ce
  `sha`. Deux joueurs qui lisent la même version et écrivent en même temps : **un seul** reçoit 200, l'autre 409. Celui
  qui a 409 relit et répond `NO held <nom>`, exactement le texte du serveur, donc `Refusal`/`Lost`/`HeldBy` marchent tels quels.
  C'est plus fort que la date de fichier du dossier (`SaveDepot.cs:31-32`) : la course d'une minute disparaît.
- **Verrou périmé** : `beat` plus vieux que 3 minutes. La reprise est **le même `PUT` conditionnel** avec le `sha`
  du verrou périmé : si deux joueurs le reprennent en même temps, un seul gagne. Aucun cas particulier.
- **L'heure** : jamais celle du PC des joueurs (deux PC ne s'accordent pas à la seconde). Le « maintenant » est l'en-tête
  `Date` de la réponse de GitHub ; `beat` est écrit avec l'heure de GitHub vue à la dernière réponse. Marge de 3 min :
  une seconde d'écart ne compte pas.
- **Battement** : un `PUT lock.json` avec le dernier `sha` connu (en mémoire). Si 409 : relire. Si le verrou est toujours à
  moi, c'était une course d'écriture (voir ci-dessous) → réessayer une fois. Si c'est à un autre et frais → `NO held X`.
  Si personne ne le tient (j'ai été coupé, pas remplacé) → le reprendre, comme `BEAT` du serveur (`:176-179`).
- **Rendre le monde** (`PUT`) en deux écritures, **verrou d'abord** : (a) `PUT lock.json` (« je tiens toujours »,
  refuse si perdu) ; (b) `PUT world.zip` avec le `sha` que j'ai lu à la prise ou reçu à la dernière sauvegarde.
  Deux garde-fous : si on a perdu le verrou, (a) échoue et le monde n'est pas écrit ; si on l'a perdu entre (a) et (b),
  le `sha` du monde a changé et (b) échoue. Reste un cas : quelqu'un a pris le verrou et n'a pas encore sauvegardé
  alors que l'ancien écrit son monde (gel de plus de 3 min pile entre (a) et (b), en une seconde) : le nouveau verra
  409 à sa première sauvegarde, gardera son `.unsent` local, et rien n'est détruit (les deux versions sont dans
  l'historique GitHub). Texte à dire : « le monde a changé pendant que vous jouiez ».
- **Monde remplacé / sauvegarde de secours** : on ne les code pas. L'historique Git garde toutes les versions de
  `world.zip` (les « replaced-… » et `world.1..3.zip` du serveur sont gratuits). Restaurer = bouton « History » de la page
  du fichier sur github.com.
- **Course entre deux fichiers du même dépôt** : deux `PUT` presque simultanés sur deux chemins différents peuvent
  recevoir un 409 parce que la branche a bougé entre-temps (**à vérifier**, connu des utilisateurs de l'API).
  Règle : un joueur n'écrit jamais deux fichiers à la fois (un seul fil, une requête à la fois, une seconde entre deux
  écritures) ; sur un 409, relire l'état avant de conclure.
- **Dépôt vide** : un dépôt créé sans README n'a pas de branche : le premier `PUT` peut échouer (**à vérifier**). Consigne
  à l'utilisateur : créer le dépôt avec « Add a README ».

### 2.4 Limites de débit

- 5000 requêtes/heure avec jeton (limite « primaire »). Notre usage : un hébergeur fait ~1 battement/min + 2 écritures par
  sauvegarde + 4 requêtes à la prise = **moins de 100 requêtes/heure**. Les autres joueurs n'en font presque pas
  (une lecture à l'ouverture du Lobby). Très loin de 5000.
- Limite « secondaire » des écritures : GitHub dit (de mémoire) pas plus de 80 écritures par minute et 500 par heure, et
  d'attendre une seconde entre deux écritures (**à vérifier**). Nous : ~60 battements + ~24 écritures par heure. OK, mais :
  une seconde de pause entre l'écriture du verrou et celle du monde, et sur 403/429 avec `Retry-After`, on traite ça
  comme une panne passagère (ne pas dire « mot de passe faux »).

### 2.5 Taille raisonnable et historique

- **Taille** : base64 gonfle de 33 %. En mémoire, un monde de N Mo coûte N (zip) + 2×1,33 N (chaîne UTF-16) + 1,33 N (UTF-8) +
  1,33 N (tampon) ≈ 6 N. À 20 Mo de zip : ~120 Mo de mémoire pendant l'envoi : supportable, mais pas plus. Je propose :
  **refus clair au-delà de 20 Mo de zip** (« monde trop gros pour le dépôt GitHub, utilisez le logiciel serveur ou un
  dossier »), le JSON écrit à la main (`{"message":…,"content":"…","sha":…}`, sans passer par Newtonsoft) pour ne
  pas doubler la chaîne. Limite dure de GitHub : 100 Mo par fichier ; réserve conseillée : rester sous 50 Mo.
  Un monde actuel de 1,5 Mo laisse beaucoup de place.
- **L'historique grossit** : chaque `world.zip` est un nouveau fichier dans le dépôt, un zip ne se « delta-compresse »
  pas à coup sûr (les en-têtes de zip portent l'heure de chaque entrée, `Zip` `:274-291` ne la fixe pas). Calcul prudent :
  1,5 Mo × 12 sauvegardes/heure × 4 h = 72 Mo par soirée ; 1 Go (limite conseillée par GitHub) en ~14 soirées.
  Ce n'est pas un problème tout de suite, mais ça en devient un.
- **Que faire** (je recommande dans l'ordre) :
  1. **Limiter les envois** : au plus un envoi du monde toutes les 5 minutes (le reste attend, voir 2.6) + toujours un
     envoi à la sortie. Divise le grossissement par 2 à 4.
  2. **Laisser l'historique** : c'est la sauvegarde de secours gratuite. Quand le dépôt approche 1 Go, l'utilisateur le
     supprime et en recrée un (deux minutes sur github.com, `Settings`, `Delete this repository`), le jeton n'a pas
     besoin d'autre droit.
  3. **Ne pas écraser l'historique** par l'API : une branche orpheline + `PATCH refs force` casse la branche, et les
     anciens objets restent dans le dépôt tant que GitHub ne les ramasse pas (rien ne se déclenche par l'API) : on
     risque de perdre les sauvegardes de secours sans gagner d'espace. À ne faire que s'il le demande (**à vérifier**).
  4. Si le dépôt grossit trop vite quand même : Plan B = monde en « Release asset » (voir tableau), verrou toujours dans `lock.json`.
- **Le verrou grossit aussi** : 60 petits commits par heure (quelques centaines d'octets chacun, ~1 Mo par jour d'hébergement
  continu). Pas un souci de taille ; seulement du bruit dans l'historique. Si ça gêne : battement toutes les 90 s et
  expiration à 5 min, ou verrou sur une branche `lock` à part (une requête de plus au démarrage : `POST git/refs`).

### 2.6 Le fil d'exécution

- `Take`, `HeldBy` (au clic) et `Put` explicite : synchrones comme aujourd'hui (l'utilisateur vient de cliquer, il attend
  un monde). Ils tiennent le jeu 1 à 3 s.
- **Battement, envoi à chaque sauvegarde, `RELEASE`** : sur **un fil de fond unique** (`Thread`), avec une file de tâches
  traitées dans l'ordre (le `RELEASE` du retour au titre passe donc après l'envoi en cours). Le fil du jeu fabrique le zip
  (opération locale, rapide), le met dans la file, et `SaveDepot.Update` (déjà appelé chaque image,
  `CoreSynchronizationContext.cs:30`) lit les résultats : effacer `.unsent`, ouvrir la boîte « Lost », le message
  `emp_ui_depot_unsaved` (`SaveDepot.cs:397`). Si une seconde sauvegarde arrive pendant un envoi, on garde seulement la
  dernière.
- Le marqueur `world_depot.unsent` est posé **avant** l'envoi et retiré quand GitHub a répondu 200 : un plantage du jeu
  pendant l'envoi laisse le marqueur, le prochain `Take` proposera de renvoyer (mécanisme existant, `:99-110`).
- `HeldBy` pour l'onglet Lobby (`TabLobbyBrowser.cs:25`) : résultat gardé 15 s, pour ne pas faire un aller-retour HTTPS
  à chaque ouverture.
- Le zip fait attention au « Temp/ » comme aujourd'hui (`Zip` `:280`).

### 2.7 GitHub en panne ou coupure réseau : ce que fait le jeu

Les mêmes réactions qu'avec le logiciel (le code existant les gère déjà, il suffit de lever `IOException`, qui est ce qu'il
attrape : `SaveDepot.cs:84`, `:430`, `:448`) :

- au `Take` : « impossible de joindre le dépôt » (`emp_ui_depot_fail`), rien n'est effacé (`Take` ne vide `Save/world_depot`
  qu'après une réponse, `:120`). Si une erreur survient entre la prise du verrou et la fin du téléchargement : `RELEASE`.
- pendant la partie : le battement échoue en silence (« la minute suivante », `:431`) ; une sauvegarde qui n'arrive pas
  → marqueur `.unsent` + message « pas reçu, gardé sur ce PC » (`:397`). Le monde local est intact.
- panne de plus de 3 minutes : le verrou expire ; si un autre le reprend, l'ancien hébergeur voit la boîte « Lost » à son retour.
- jeton refusé (401) ou sans droit : texte `password` → message existant « mot de passe refusé » (`:214`, mis à jour pour
  dire « jeton »). 404 sur le dépôt : `emp_ui_depot_fail` (message générique).

---

## 3. Ce que le mod sait faire en HTTP aujourd'hui

**Rien en HTTPS, rien en HTTP non plus dans le mod.** Lu :

- Le mod : `grep` de `HttpClient|UnityWebRequest|WebClient|HttpWebRequest|ServicePointManager|SecurityProtocol` sur
  `ElinTogether/**/*.cs` = **aucun résultat**. Le seul réseau est Steam (messages) et TCP brut pour le dépôt
  (`TcpClient`, `SaveDepot.cs:327`) ; le journal va dans un fichier et la console (`Emp/Logger/EmpLogger.cs:109-120`, pas
  de `WriteTo.Http`). Le paquet `Serilog.Sinks.Http` est référencé (`ElinTogether.csproj:72`) et copié dans le dossier du
  mod, mais jamais utilisé : il ne prouve rien.
- Le jeu : `Net.cs:155-475` (décompilé `dev/_decomp/Elin_23351/Net.cs`) fait des `UnityWebRequest.Get/Post` (chat, vote,
  livre, téléversement) vers `http://elin.cloudfree.jp/script/` (`Net.cs:77`) : **HTTP simple, pas HTTPS**. Les `https://`
  du jeu sont des `Application.OpenURL` (navigateur). Donc aucune preuve ici que HTTPS marche dans ce Mono.
- Ce qui est dans le dossier du jeu (lu) : Unity **2021.3.45** (`UnityPlayer.dll`), Mono embarqué (`MonoBleedingEdge`),
  `Elin_Data/Managed/System.Net.Http.dll`, `System.dll`, `Mono.Security.dll`, `netstandard.dll` (2.1),
  **`UnityEngine.TLSModule.dll`** et `UnityEngine.UnityWebRequestModule.dll`. Le mod vise `netstandard2.1`
  (`ElinTogether.csproj:3`), qui contient `HttpClient` et `HttpWebRequest` : **ils se compilent** et se résolvent à
  l'exécution par `netstandard.dll` vers le `System.Net.Http.dll` du jeu.
- TLS 1.2 : Unity 2021.3 sait en principe faire du TLS 1.2 par son propre module TLS (la présence de `UnityEngine.TLSModule.dll`
  le laisse penser), et api.github.com n'exige que TLS 1.2. **Pas vérifié** : ni la prise de contact, ni la confiance dans
  le certificat de GitHub (le magasin d'autorités de Mono sous Windows). Premier essai à faire, sans écrire de mod (3.1).
- JSON : **Newtonsoft.Json 12.0.2 est dans le jeu** (`Elin_Data/Managed/Newtonsoft.Json.dll`) et le mod l'utilise déjà
  (`Helper/CharaImport.cs:9,107`, `Helper/JsonFormatter.cs:3`, `Emp/EmpDebugListener.cs:17-18` avec `JObject`). Le build
  supprime sa propre copie pour utiliser celle du jeu (`ElinTogether.csproj:90`). Disponible. Les réponses de GitHub qu'on
  lit sont petites ; `JObject.Parse` suffit.

### 3.1 Essai préalable (étape 0 du plan, sur une fenêtre Elin de dev, sans rien changer au mod)

Dans la version Debug, le pont de test (`dev/_tools/emp.py`, commande `eval`) exécute du C# dans le jeu. Trois lignes :
`ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072;` puis
`new WebClient{Headers={["User-Agent"]="x"}}.DownloadString("https://api.github.com/zen")`, puis la même avec
`HttpWebRequest`. Si ça marche : on continue avec `HttpWebRequest`. Si le certificat ou TLS est refusé : repli sur
`UnityWebRequest` (HTTPS par le système, mais seulement sur le fil principal, avec `UniTask` que le jeu a déjà : le
mod pourrait alors le piloter sans fil de fond, mais moins testable hors du jeu). **À ne pas contourner** en désactivant
la validation des certificats : le jeton passerait en clair pour n'importe qui.

Choix pour le code : `HttpWebRequest` synchrone (comme `Ask` est synchrone et fait déjà `.Wait` sur le fil du jeu) plutôt que `HttpClient` + `await` :
les `await` sur le fil principal d'Unity (contexte de synchronisation d'Unity) sont un piège d'interblocage ; sur
le fil de fond, `HttpWebRequest.GetResponse()` suffit.

---

## 4. Où le joueur met `propriétaire/dépôt` et sa clé

- **Dépôt** : le réglage « Depot » existant (`EmpConfig.Client.DepotPath`, `EmpConfig.cs:49`), sous la forme
  `github:proprietaire/depot` (ex. `github:marc/elin-monde`). Aucun conflit avec les deux autres : un dossier Windows
  ne commence pas par `github:`, une adresse `hote:port` finit par des chiffres (`SaveDepot.cs:53`). Il suffit
  d'ajouter `private static bool GitHub => Root.StartsWith("github:")` et de faire dire à `Enabled` (`:62`) « c'est un
  dépôt GitHub avec un jeton ». Le même texte tapé dans « Join by address » (`TabLobbyBrowser.cs:32`) marchera aussi par
  `TakeFrom` (`:149`) si `Remote` est élargi à « dépôt en réseau ».
- **Jeton** : on **réutilise `DepotPassword`** (`EmpConfig.cs:57`) : un seul champ de plus à comprendre, et le bouton du
  mot de passe l'affiche déjà en `***` (`TabClientConfiguration.cs:40`). Deux corrections : (1) la boîte de saisie (`:41`)
  ne doit pas préremplir le jeton en clair (passer `""` quand c'est un dépôt GitHub) ; (2) le texte
  « Depot password (if set in Elin Together Server) » devient « mot de passe du serveur, ou jeton GitHub ».
  Alternative non retenue : un champ `DepotToken` séparé (plus clair, trois lignes de plus, un texte de plus).
- **Stockage** : fichier de config du mod `BepInEx/config/dk.elinplugins.elintogether.cfg`, **en clair** (comme le mot de
  passe aujourd'hui). Il n'est ni dans la sauvegarde, ni envoyé aux autres joueurs, ni dans le zip de dépôt (le zip est
  fait à partir de `Save/world_depot` seulement). Le jeton ne va jamais dans une URL (seulement l'en-tête `Authorization`), ni dans
  `DepotPath`.
- **Jetons** : jeton « fine-grained », propriétaire = l'utilisateur, **un seul dépôt**, droit **Contents : Read and write** (le droit
  « Metadata : Read » vient d'office). Durée de vie maximale 1 an par défaut (30 jours si on ne change rien) :
  prévenir l'utilisateur de la date, un jeton expiré donne 401, donc « jeton refusé ».
- **Attention, à vérifier avant de promettre quoi que ce soit aux amis** : un jeton « fine-grained » ne peut (de ma
  connaissance) viser que les dépôts du compte qui l'a créé ou d'une organisation, pas ceux d'un autre utilisateur
  même s'il est « collaborateur ». Donc les amis ne pourraient pas faire leur propre jeton sur le dépôt de l'utilisateur.
  Deux sorties : **(a) recommandée : l'utilisateur crée UN jeton et le donne à ses amis** (ils n'ont même pas besoin de
  compte GitHub ; ce jeton ne donne accès qu'à ce dépôt ; on le révoque d'un clic), ou (b) une organisation GitHub gratuite qui possède le dépôt.
- Le dépôt doit être **privé**. Le mod peut le vérifier à la première utilisation (`GET /repos/{o}/{r}` → `"private": true`) et refuser
  sinon : une requête, évite qu'un monde (et son historique) soit public par erreur.

---

## 5. Fichiers, taille, risques

### 5.1 À créer / modifier

| Fichier | Quoi | Taille estimée |
|---|---|---|
| **nouveau** `ElinTogether/Helper/GitHubDepot.cs` | `Ask(commande, corps, moi, nom)` qui rend le même `(Ok, Texte, Corps)` que `SaveDepot.Ask` ; lecture/écriture de `lock.json`, `world.zip` ; file de tâches + un fil ; décalage d'horloge ; aucune dépendance au jeu (BCL + Newtonsoft) pour pouvoir le compiler aussi dans un petit programme de test | ~250-300 lignes |
| `ElinTogether/Helper/SaveDepot.cs` | `GitHub`/`Network` (`:53`, `:62`), `Ask` envoie vers `GitHubDepot` (`:324`), `Copy`/`OnSaved` : envoi en tâche de fond, marqueur `.unsent` posé avant (`:222-238`, `:384-399`), `Update` lit les résultats (`:422`), limite de fréquence + envoi forcé à la sortie (`:435`), `HeldBy` en cache (`:70`) | ~50 lignes touchées |
| `ElinTogether/Emp/EmpConfig.cs` | texte du réglage (`:49-61`) ; **Debug seulement** : `Dev.GitHubApi` (adresse de l'API, pour le faux serveur ; en Release l'adresse est `https://api.github.com` écrite en dur) | ~10 lignes |
| `ElinTogether/Components/Tabs/TabClientConfiguration.cs` | ne pas préremplir le jeton en clair (`:41`) | 2-3 lignes |
| `package/LangMod/EN/emp_localization.xlsx` + `CN/SourceLocalization.json` | 3 textes existants à adapter : `emp_ui_depot_folder_ask`, `emp_ui_depot_password_ask`, `emp_ui_depot_password_wrong` (+ éventuellement `emp_ui_depot_password`). Après coup : effacer `LangMod/EN/SourceLocalization.json` du mod installé (règle `CLAUDE.md`) | ~3 lignes × 2 langues |
| `ElinTogether.csproj` | normalement rien ; si le compilateur ne trouve pas `HttpWebRequest`, une ligne `<Reference Include="System.Net.Http">` (`Elin_Data/Managed`, `Private=false`) comme pour `System.IO.Compression` (`:53-56`) | 0-4 lignes |
| `dev/_tools/fake_github.py` (nouveau) | faux serveur (6) | ~150 lignes |
| `dev/_tools/github_depot_cli/` (nouveau) + `dev/_tools/github_proto_test.py` | petit programme qui compile `GitHubDepot.cs` seul, et le test | ~60 + ~200 lignes |
| `dev/_tools/depot_suite.py` | variante `DEPOT_GITHUB=1` (comme `DEPOT_SERVER=1`) | ~20 lignes |
| `dev/_tools/github_real_test.py` (nouveau) | essai réel (6.3) | ~100 lignes |
| `dev/DOCUMENTATION.md`, `dev/MODLOG.md`, `dev/_release/template/LISEZMOI.txt` | comment créer le dépôt privé et le jeton, la limite de taille, ce qui n'est pas testé | texte |

Total : ~350 lignes de mod, ~550 lignes d'outils de test. **Aucune case côté host** : comme les deux autres sortes, c'est un
réglage du joueur (« Client », pas « Server Setting »), parce qu'un dépôt est un choix du joueur qui prend le monde, pas
d'une règle du monde.

### 5.2 Ce qui touche aux sauvegardes existantes : **rien**

Le zip est le même que celui du logiciel serveur (`Zip` `:274-291`), le dossier local `Save/world_depot` est le même, le
marqueur `.unsent` aussi. Aucun delta réseau, aucun format de sauvegarde, aucun numéro d'union ne change. Un monde peut
passer du logiciel à GitHub en déposant son `world.zip` (« Put this save in the depot » le fait depuis le jeu).

### 5.3 Risques

| Risque | Gravité | Réponse prévue |
|---|---|---|
| **Jeton qui fuit dans un journal** | haute | le jeton n'est jamais dans une URL ni dans un message d'exception ; jamais écrit par `EmpLog` (le journal écrit `{Root}` = `github:o/r` seulement, `:133`, `:139`, `:249`) ; ne pas journaliser les en-têtes ni le corps d'une réponse 401 ; boîte de saisie vide ; test T9 (6.1) : on fait tourner un scénario avec un faux jeton reconnaissable, puis on cherche ce texte dans `ElinMP/Logs/*.log`, la console BepInEx, le zip, le dossier de sauvegarde : doit être **absent** partout sauf `.cfg`. Rappeler à l'utilisateur : ne pas envoyer le `.cfg` ni une capture de l'écran de réglages (le jeton y est masqué `***`, mais pas dans le fichier) |
| **Jeton volé** | moyenne | il ne donne que Contents sur ce dépôt privé (pas d'accès au reste du compte) ; révocation d'un clic ; durée de vie limitée |
| **Monde perdu si deux joueurs écrivent** | haute | double garde `sha` : du verrou, puis du monde (2.3). Aucune écriture « forcée » nulle part. Reste le cas de gel de 3 min pile entre les deux écritures : rien n'est détruit (historique + `.unsent`), on le dit. Test de course T4 |
| **Sauvegarde trop grosse** | moyenne | refus à 20 Mo de zip avec message clair ; mémoire ≈ 6 × la taille (2.5). Mesurer la vraie taille de la partie de l'utilisateur d'abord |
| **Dépôt qui grossit** | moyenne | limite de fréquence (5 min), historique laissé comme sauvegarde, recréer le dépôt au-delà de 1 Go (2.5) |
| **GitHub en panne / limite de débit / réseau coupé** | moyenne | voir 2.7 : le monde reste sur le PC, `.unsent`, rien n'est effacé avant la réponse. Les 403/429 ne sont pas pris pour un mauvais jeton |
| **Jeu qui se fige** | moyenne | fil de fond pour tout ce qui arrive en cours de partie (2.6) ; `Take` synchrone mais borné (délai 20 s, au lieu de 60 s) |
| **HTTPS refusé par ce Mono** (TLS, certificat) | **bloquante si vrai** | étape 0 avant d'écrire quoi que ce soit (3.1) ; repli `UnityWebRequest` |
| **Course d'écriture entre deux fichiers (409 sans cause)** | faible | une requête à la fois, une seconde entre deux écritures, relire sur 409 |
| **Dépôt public par erreur** | moyenne | `GET /repos/{o}/{r}` au premier usage, refus si `private` est faux |
| **Horloges des PC** | faible | l'heure vient de GitHub (en-tête `Date`) |
| **Lecture périmée juste après une écriture** (cache) | faible | une écriture conditionnelle ne se trompe pas ; sur 409, relire (**à vérifier**) |
| **Nom de machine dans `lock.json`** | négligeable | dépôt privé ; `Me` = `Machine:PID` comme aujourd'hui |

---

## 6. Comment tester sans deux PC

### 6.1 Faux GitHub local, sur le modèle de `depot_proto_test.py`

Le faux serveur `dev/_tools/fake_github.py` (bibliothèque standard, `http.server`, port libre type 55560) imite **seulement** les
appels du 2.2 :

- `GET /repos/{o}/{r}/contents/{path}` : JSON `{sha, content}` ou, si `Accept` contient `raw`, les octets ; 404 `{"message":"Not Found"}` ;
  `GET …/contents/` : liste `[{name, sha, size, type}]`.
- `PUT …/contents/{path}` : corps `{message, content, sha?}`. **Refus** : fichier existant sans `sha` → 422 ; `sha` différent → 409 (c'est
  le comportement qu'on prouve). Sinon 200/201 avec `content.sha` = `sha1(b"blob %d\0" % len + octets)` (la vraie formule Git, donc
  comparable à un `git hash-object`). Garde l'historique `{chemin: [(sha, message, date)]}`.
- `GET /repos/{o}/{r}` → `{"private": true}`.
- Authentification : `Authorization: Bearer <jeton>` attendu, sinon 401.
- Date : l'en-tête `Date` vient d'une horloge **pilotable** (`POST /__clock`) pour tester l'expiration sans attendre 3 min.
- Pannes pilotables (`POST /__fault`) : 500 pendant N demandes, 403 + `Retry-After` (limite de débit), réponse lente, coupure.
- Et `GET /__state` : fichiers, historique, journal des demandes (pour vérifier le nombre de requêtes et qu'aucune n'a de `branch` ni de `force`).

Test sans jeu `dev/_tools/github_proto_test.py` : le programme `github_depot_cli` (3 lignes de plus que `GitHubDepot.cs` :
une ligne de commande qui appelle `Ask(WHO|TAKE|PUT|BEAT|RELEASE)` avec `Me`/`nom` en arguments, comme `ask()` de `depot_proto_test.py:46`)
est lancé contre le faux. C'est **le même C# que celui du mod**. Cas, calqués sur P1–P5 :

- G1 dépôt vide : `WHO` libre ; `TAKE` → `NO empty` ; `PUT` d'un monde → `OK`, 2 écritures (verrou puis monde).
- G2 un autre joueur met son monde pendant que personne n'héberge : l'ancien reste dans l'historique du faux (remplace `replaced-*.zip`).
- G3 cinq `PUT` de suite : le monde est le dernier ; l'historique en a six.
- G4 **course** : deux `cli` lancés en même temps sur le même verrou libre (barrière sur un fichier) : exactement un `OK`, l'autre `NO held <nom>` ; répété 20 fois. Idem pour la reprise d'un verrou périmé.
- G5 pendant que B tient : `TAKE` et `PUT` de C → `NO held B`, le monde n'a pas changé ; avec l'horloge avancée de 4 min, C prend le verrou (reprise) ; B revient : `BEAT` → `NO held C`.
- G6 mauvais jeton → statut `password` (401), **sans** rien envoyer d'autre.
- G7 `sha` du monde périmé (quelqu'un a écrit `world.zip` à la main dans le faux) : `PUT` refusé, rien n'est écrasé.
- G8 pannes : 500, 403 avec `Retry-After`, coupure : `IOException`, pas « mot de passe » ; après la panne, tout reprend.
- G9 gros monde : zip de 19 Mo accepté, 21 Mo refusé avec le message de taille (pas de mémoire démesurée).
- G10 fuite : le programme tourne avec un faux jeton `ghp_TESTJETON_ne_pas_voir` et son journal est cherché ; le faux ne le voit que dans l'en-tête `Authorization`.

Test avec jeu (le vrai chemin, comme `DEPOT_SERVER=1`) : `DEPOT_GITHUB=1 python _tools/depot_suite.py` rejoue D1–D6 avec deux fenêtres :
réglage `DepotPath = github:test/monde`, `DepotPassword = jeton de test`, et `[Dev] GitHubApi = http://127.0.0.1:55560`
(**Debug seulement**), puis on lit l'état par `/__state`. Ajouts : la sauvegarde ne fige pas le jeu (le temps de
l'image entre deux sauvegardes reste court pendant que le faux est mis en « lent » 3 s) ; panne du faux pendant une
sauvegarde → `.unsent`, puis renvoi au retour ; sortie au titre → verrou libre dans le faux.

### 6.2 Test réel, par l'utilisateur (une fois, ~10 minutes)

L'utilisateur crée : un dépôt **privé** `elin-monde-test` (avec README), puis un jeton fine-grained limité à ce dépôt, Contents lecture/écriture,
qu'il donne dans l'environnement du test (`GITHUB_TEST_TOKEN`), **jamais dans la conversation ni dans un fichier du dépôt Git** du mod.
Étapes :

1. **Étape 0** (3.1) : `GET https://api.github.com/zen` depuis une fenêtre Elin de dev. Rouge = on s'arrête là.
2. `dev/_tools/github_real_test.py` (urllib, hors du jeu) : (a) la course de `sha` : deux `PUT` simultanés avec le même `sha` → un 200, un 409 (c'est
   **la** propriété qu'on achète, à voir une fois en vrai) ; (b) l'échelle de taille : 1, 5, 20, 40 Mo → ce que GitHub accepte réellement et
   en combien de temps (trace la limite de requête **à vérifier**) ; (c) en-têtes de débit (`x-ratelimit-remaining`) ; (d) le `GET raw` d'un fichier de 5 Mo
   rend les mêmes octets (SHA-256) ; (e) lecture juste après écriture : périmée ou non ; (f) deux `PUT` simultanés sur deux fichiers différents : 409 ou pas.
3. Une soirée à deux (ou une fenêtre + un PC) sur le dépôt réel : prendre, sauvegarder, quitter, reprendre ; vérifier dans `Settings` de GitHub qu'aucune
   chose étrange n'a été publiée, et regarder l'historique du fichier.
4. Supprimer le jeton de test et le dépôt.

---

## 7. Étapes proposées (chacune un commit testé, comme demandé dans `CLAUDE.md`)

0. Essai HTTPS dans une fenêtre de dev (3.1). Rien d'écrit.
1. `GitHubDepot.cs` (synchrone) + `fake_github.py` + `github_depot_cli` + `github_proto_test.py` G1–G10. Sans le jeu.
2. Branchement dans `SaveDepot` (synchrone d'abord : `Take`, `Put`, `HeldBy`, `Beat`, `RELEASE`), réglage, texte. `depot_suite` avec `DEPOT_GITHUB=1` D1–D6.
3. Fil de fond, limite de fréquence, envoi forcé à la sortie, marqueur `.unsent` posé avant. Cas « le jeu ne se fige pas » et « panne puis renvoi ».
4. Documentation + `LISEZMOI.txt` (comment créer le dépôt et le jeton) + relecture par l'agent `relecteur-elintogether`.
5. Essai réel (6.2).

---

## Non vérifié

- **Rien n'a été exécuté** : ni compilation, ni test, ni appel vers GitHub (consigne). Tout ce qui suit est donc de mémoire ou de lecture.
- HTTPS depuis ce Mono (TLS 1.2 et confiance dans le certificat de api.github.com) : jamais essayé ; aucune requête HTTPS dans le mod ni dans le jeu.
- Limite exacte de taille d'une requête `PUT contents` (100 Mo par fichier de la doc, mais corps JSON/base64 : peut-être plus bas en pratique).
- Que le `GET` brut (`Accept: application/vnd.github.raw+json`) rende un fichier de 1 à 20 Mo sans passer par le JSON.
- Que deux `PUT` simultanés avec le même `sha` donnent bien un 200 et un 409 (et pas deux 200 ou un 5xx).
- Les 409 sans cause entre deux fichiers du même dépôt ; la lecture périmée juste après une écriture.
- Les limites « secondaires » (80 écritures/min, 500/heure, une seconde entre deux écritures) : de mémoire.
- Qu'un `PUT` crée bien le premier fichier d'un dépôt vide (sans README).
- Qu'un jeton fine-grained ne puisse pas viser le dépôt personnel d'un autre utilisateur, même collaborateur.
- Le comportement du zip dans l'historique Git (delta ou non) : la crainte est calculée, pas mesurée.
- La taille réelle d'un long monde (je n'ai que des mondes de 1 à 1,5 Mo).
- Que ces ~350 lignes suffisent : l'estimation vient de la taille de `SaveDepot.cs` (452 lignes pour un protocole plus simple).

## Questions pour l'utilisateur

1. **Jeton** : un seul jeton que tu donnes à tes amis (recommandé, ils n'ont pas besoin de compte GitHub), ou chacun le sien (il faudrait alors une organisation GitHub gratuite) ?
2. **Fréquence** : limiter l'envoi du monde à une fois toutes les 5 minutes (l'historique grossit 2 à 4 fois moins ; en cas de plantage de l'hébergeur, les autres reprennent
   un monde vieux de 5 minutes de plus), ou envoyer à chaque sauvegarde comme le logiciel serveur ?
3. **Historique** : le laisser comme sauvegarde de secours et recréer le dépôt quand il dépasse 1 Go (recommandé) ?
4. **Taille** : refuser les mondes de plus de 20 Mo de zip avec un message, d'accord ? Quelle est la taille de ta vraie partie en cours ?
5. **Jeton dans le réglage « mot de passe »** (le plus petit changement) ou un réglage séparé « jeton GitHub » ?
6. **Verrou** : un petit commit par minute dans l'historique (plus simple) ou une branche `lock` à part (plus propre, une requête et un peu de code en plus) ?
7. Le dépôt doit être **privé** : le mod refuse un dépôt public, d'accord ?
8. OK pour faire d'abord l'essai HTTPS de 3 lignes dans une fenêtre de dev, sur ton réseau, avant d'écrire le moindre code ?
