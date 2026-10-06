# Lenteurs et défauts à plusieurs invités : corrections prêtes à coder (2026-10-06, soir)

Suite de `PLAN_plusieurs_invites.md` (l'audit). Travail par lecture du code de la 0.26.510 : **rien n'a été lancé ni
chronométré**. « lu » = vu dans le code aujourd'hui, avec la ligne. « supposé » = déduit, à vérifier au banc.
Chemins : `M:` = `ElinTogether/ElinTogether/`, `J:` = `dev/_decomp/Elin/`. N = nombre d'invités (soirée à 4 : N = 3).

## 0. Ce qui a changé depuis l'audit (lu)

- A1 est **pire que décrit**. Au retour d'un invité l'host fait, dans la même image : copie du monde
  (`M:Net/Host/ElinNetHostTravel.cs:1149` -> `ElinNetHostPlayerManager.cs:238-264` -> `Models/SessionState/SaveDataProbe.cs:25`),
  puis sauvegarde (`ElinNetHostTravel.cs:1153-1155`). Quand c'est l'host qui entre dans une carte tenue, **le jeu
  sauvegarde encore une fois de lui-même** si c'est une ville ou une base (`J:Chara.cs:3616-3624`, déclenché par
  `ResumePendingHostMove`, `ElinNetHostTravel.cs:1229`). Host qui revient sur une carte tenue par A et visitée par B et C :
  3 copies du monde + 3 sauvegardes du mod + 1 du jeu. S'y ajoute `EmpAutoHost` toutes les 2 min.
- La raison écrite à la ligne 1152 (« garder game.txt cohérent avec les fichiers de carte ») **ne tient plus** : chaque
  point de passage écrit déjà les fichiers de carte dans le dossier de sauvegarde sans sauvegarder
  (`ApplyCheckpoint`, `:1164-1185`, `ZoneLeaseState.WriteMap`, `:1249`). L'écart existe donc déjà, 60 s sur 60.
- `EmpAutoHost` a déjà ce qu'il faut pour une sauvegarde « due » (`M:Emp/EmpAutoHost.cs:24, 123-134, 140-152`) et écrit
  déjà la durée de chaque sauvegarde dans le journal (`:173`, « Autosave: saved in X ms ») : **premier chiffre gratuit**.
- B1 : les cases sont corrigées et prouvées (`trio_place` 17/17, `HANDOFF.md`). Il reste le **coût** : à chaque départ
  de l'host, chaque invité sauf le premier recharge un monde entier, servi par le teneur
  (`ElinNetHostTravel.cs:181-214`, `950-970`).
- A2, A3, A4, A5, B2, B3, B4, B5 : inchangés, relus aux lignes données plus bas.
- Le pont de test répond sur le fil principal du jeu (`M:Emp/EmpDebugListener.cs:69-79`) et chaque réponse porte `ms`
  (`:157`) : pendant un gel la réponse attend. **Un gel se chronomètre donc sans recompiler** (voir lot 0).

## 1. Classement : gain pour une soirée à 4 / taille du changement

| Rang | Point | Changement | Taille | Gain attendu | Nature |
|---|---|---|---|---|---|
| 1 | A3 | lire le réseau jusqu'au bout, borné à 4 ms | ~8 lignes, 2 fichiers | le retard après un gel ne s'accumule plus | bug |
| 2 | A1a | une seule sauvegarde, différée, pour tous les retours | ~14 lignes, 2 fichiers | 4 sauvegardes -> 1 par retour de l'host | bug |
| 3 | A2 | ménage des cartes une fois par seconde, sans copie | ~10 lignes, 1 fichier | plus d'allocation par image, dans les 4 jeux | bug |
| 4 | A4a | compression rapide des cartes envoyées | ~4 lignes, 1 à 3 fichiers | compression ~10 fois plus courte (supposé) | bug |
| 5 | B4 | inviter aussi les visiteurs de la ville à la quête | ~15 lignes, 2 fichiers | B n'est plus oublié | bug |
| 6 | B3a | dire à l'écran **qui** on attend pour dormir | ~8 lignes + 1 texte | on sait à qui parler | bug |
| 7 | A1b | le teneur rappelé charge-t-il deux cartes ? | à vérifier d'abord | jusqu'à 1 chargement sur 2 en moins | supposé |
| - | A5, B3, B5, B2, A4b, B1 | voir « Pour le conseil » | - | - | choix |

Le lot 0 (mesure) passe avant tout : sans lui aucun « gain » de ce tableau n'est prouvé.

## 2. Lot 0 : mesurer (à faire en premier, sans toucher au mod)

- **Nouveau fichier `dev/_tools/perf_probe.py`** (~40 lignes, Python seul). Un fil par port : `emp.call(port, "state")`
  toutes les 50 ms ; on garde, par fenêtre de temps nommée, le plus grand `ms` rendu et le plus grand trou entre deux
  réponses. Gel de l'image = ce maximum (précision ~50 ms). Usage : `with probe.window("retour host"): ...`.
- **Compter les sauvegardes** : `ev(H, "EClass.game.saveCount")` avant et après (`J:Game.cs:1113`, lu).
- **Durée d'une sauvegarde** : ligne « Autosave: saved in X ms » du journal de l'host, après `emp.autosave_every 120`
  (commande du banc, `M:Emp/EmpConsole.cs:154`). Sans cette commande le banc ne sauvegarde jamais seul (`EmpAutoHost.cs:102`).
- **Plus tard, dans le mod (Debug, ~40 lignes, `EmpDebugListener.State`)** : objet `perf` remis à zéro à chaque lecture
  (image la plus longue, `GC.CollectionCount(0)`, nombre de cartes en cache, lots réseau pleins). À écrire **après** les
  lots 1 à 4 pour ne pas toucher les mêmes fichiers ; `perf_probe.py` suffit pour le rouge/vert de ces lots.
- Non vérifié : que `EClass.debug.ignoreAutoSave` est faux dans les fenêtres du banc (sinon aucune sauvegarde à compter).

## 3. Section A : lenteurs

### A3. Réseau lu 8 messages par image — rang 1
- **Fait (lu).** `M:Common/EmpConstants.cs:13` (8), tampon `M:Net/Steam/SteamNetManager/SteamNetManager.cs:13`, un seul
  appel par image `:76`, appelé par `M:Net/Base/ElinNetBase.cs:59`. Un invité envoie 5 états par seconde (réponse à chaque
  instantané, `M:Net/Client/ElinNetClientUpdate.cs:70`) + jusqu'à 50 listes (`:113`). Débit réel en marche : supposé.
- **Changer.** `SteamNetManager.Poll` (`:70-105`) : entourer la lecture et la boucle `for` d'un
  `do { ... } while (received == _batchedMessages.Length && chrono.ElapsedMilliseconds < 4)`, avec un `Stopwatch` lancé à
  l'entrée. Passer `MaxBatchedMessages` de 8 à 32. Rien d'autre : l'ordre des messages ne change pas.
- **Gain (calcul, pas mesure).** L'host lit aujourd'hui 8 x images/s ; il reçoit jusqu'à 55 x N. À N = 3 : 165/s.
  À 60 images/s tout va bien ; à 20 images/s (160 lus) le retard **ne se rattrape jamais**. Après un gel de 2 s
  (A1, A4, sauvegarde) : 330 messages en attente ; à 30 images/s il faut 4,4 s pour les vider, à 60 images/s 1 s.
  Après le changement : vidé en une ou deux images. C'est ce qui transforme chaque gel en « tout est mou ensuite ».
- **Risque.** Une image plus longue quand il y a du retard (bornée à 4 ms + le dernier message, qui peut être une carte
  entière). Pas de perte, pas de doublon : même file, même ordre.
- **Test.** Deux fenêtres. Rouge : `ev(H, "QualitySettings.vSyncCount=0; Application.targetFrameRate=5")` (40 lus/s),
  l'invité marche 20 s (`travel_suite.move` ou le bot) ; chaque seconde, comparer la case de l'invité chez lui et chez
  l'host : l'écart grandit. Puis remettre 60 : temps pour que l'écart revienne à 0. Vert : écart stable, retour < 0,5 s.
  Trois fenêtres (accord à demander) : même chose à `targetFrameRate=20` sans autre bride.

### A1a. Une seule sauvegarde pour tous les retours — rang 2
- **Fait (lu).** Section 0. Rappel des visiteurs : `ElinNetHostTravel.cs:940-947` ; rappel du teneur : `:712-718`.
- **Changer.** (1) `M:Emp/EmpAutoHost.cs` : nouvelle `internal static bool RequestSave(float within = 5f)` : rend `false`
  si `EmpServer.Requested`, si `!EmpConfig.Server.AutoSave.Value`, ou si le banc n'a pas demandé de sauvegarde
  (`_bench && _benchSeconds <= 0`) ; sinon `_owed = true; _nextSave = Mathf.Min(_nextSave, Time.unscaledTime + within);`
  et rend `true`. (2) `ElinNetHostTravel.cs:1153-1155` : `if (!EClass.debug.ignoreAutoSave && !EmpAutoHost.RequestSave())
  game.Save(isAutoSave: true);`. (3) Dans `EmpAutoHost.Update` (`:127-130`) : si la sauvegarde est due depuis plus de 30 s
  et que `CanSave()` refuse toujours, sauvegarder quand même (aujourd'hui le retour sauvegarde sans rien regarder).
  Même traitement possible à `:1579-1581` (teneur qui plante) : à laisser tel quel dans ce lot.
- **Gain.** Host qui revient sur une carte tenue, N = 3 : 4 sauvegardes -> 1 (celle du jeu, ou la due). Retour d'un seul
  invité : la sauvegarde sort de l'image du retour et se fait au calme, 5 s plus tard, une fois pour plusieurs retours
  rapprochés. Durée gagnée par sauvegarde : celle du journal (`EmpAutoHost` appelle « lourd » au-delà de 500 ms).
  La copie du monde, elle, reste : 1 par retour.
- **Risque.** L'host plante dans les 5 à 30 s : la carte rendue est sur le disque, le personnage rendu ne l'est pas.
  Un objet ramassé là-bas depuis la dernière sauvegarde est perdu, un objet posé existe deux fois. **Ce risque existe
  déjà** entre deux points de passage (section 0) ; on l'allonge de quelques secondes par retour. Case `AutoSave`
  décochée ou serveur dédié : comportement d'aujourd'hui, rien ne change.
- **Test.** Trois fenêtres, `trio_place_suite.py` Q2 (l'host revient, A et B rappelés), après `emp.autosave_every 120`
  chez l'host. Rouge : `saveCount` augmente de 3 (2 retours + le déplacement de l'host) et `perf_probe` montre le gel.
  Vert : augmente de 1 ou 2, gel plus court ; 10 s après, `saveCount` a bien bougé (la due est faite). Deux fenêtres :
  `travel_suite` (retour d'un invité) doit rester 83/83, et `autosave_suite` 18/18.

### A2. Table des cartes recopiée à chaque image — rang 3
- **Fait (lu).** `M:Models/CardCache.cs:213` : `_cards.ToArray()` à chaque image, dans chaque jeu, appelé par
  `M:Patches/Synchronization/CoreSynchronizationContext.cs:44`.
- **Changer.** `CardCache.Update` : garder à chaque image les deux premières lignes (`_keepalive`, `_invalidCards`).
  Le parcours de `_cards` : une fois par seconde (`Time.unscaledTime >= _nextSweep`), en notant les numéros morts dans
  une `List<int>` statique réutilisée, puis en les retirant après le parcours. Plus de `ToArray`.
- **Gain (calcul).** 16 octets par carte en cache et par image. 10 000 cartes : 160 Ko par image, 9,6 Mo/s à 60 images/s
  jetés au ramasse-miettes, dans chacun des 4 jeux. Nombre réel de cartes : inconnu, à lire au banc. Après : zéro.
- **Risque.** Aucun de comportement : une entrée morte rend déjà `null` dans `Find` (`:101-109`) ; elle traîne 1 s de plus.
- **Test.** Deux fenêtres, 60 s immobile puis 60 s en marche : `ev(p, "System.GC.CollectionCount(0)")` avant et après,
  des deux côtés. Rouge/vert : le nombre de passages baisse. Non-régression : `guest_suite`, `together`.

### A4a. Point de passage : compression rapide — rang 4
- **Fait (lu).** Toutes les 60 s (`M:Emp/EmpConfig.cs:276-284`), chaque invité qui **tient** une carte envoie la carte
  entière, son personnage, ses compagnons, et le personnage + compagnons de chaque visiteur
  (`M:Net/Client/ElinNetClientTravel.cs:898-913, 953-973`). La carte passe par `ZoneLeaseState.CollectMap`
  (`M:Models/ZoneLease/ZoneLeaseState.cs:19-30`) : sauvegarde de la carte + compression **forte** de chaque fichier
  (`M:Models/LZ4Bytes.cs:52`). L'host décompresse, écrit, relit les personnages (`ElinNetHostTravel.cs:1164-1185, 1232-1265`).
  La même compression forte sert à chaque carte envoyée à un joueur (`M:Models/ZoneState/ZoneDataResponse.cs:47-49`).
- **Changer.** `LZ4Bytes.CreateFromFile` : retirer `LZ4StreamFlags.HighCompression` (ou paramètre `fast`, vrai pour les
  points de passage et `ZoneDataResponse`). Le lecteur lit déjà les deux formes (`Decompress`, `:75-83`, sert aux deux).
- **Gain.** Envois par minute = nombre de cartes tenues, au plus N : à 4 dispersés, 3 gels par minute chez l'host.
  Compression forte contre rapide : ordre de grandeur connu de LZ4, environ 10 fois plus lente pour 20 à 40 % d'octets en
  moins (pas mesuré ici). Profite aussi à A1 et A6 (chaque carte servie). Reste : la sauvegarde de la carte et le texte
  des personnages, non touchés.
- **Risque.** Messages plus gros : à mesurer (taille de `release.Map`) avant de choisir. Aucun sur la sauvegarde.
- **Test.** Deux fenêtres, l'invité tient Vernis ; `perf_probe` sur les deux ports pendant 130 s (deux points de
  passage) : gel maximum chez l'invité et chez l'host, avant et après. Trois fenêtres : avec un visiteur en plus.

### A1b. Le teneur rappelé charge peut-être deux cartes — rang 7, à vérifier avant d'écrire
- **Supposé.** La copie du monde part à la ligne 1149, **avant** que l'host bouge (`ResumePendingHostMove`, `:1158`).
  Le monde reçu dit donc « l'host est sur son ancienne carte ». L'invité la demande ; puis l'host change de carte, la
  nouvelle part à tous (`M:Patches/DeltaEvents/Zone/ZoneActivateEvent.cs:47`), et une réponse en retard est corrigée par
  un second envoi (`M:Net/Host/ElinNetHostZone.cs:86-93`).
- **Vérifier.** Journal de l'host pendant `trio_place` Q2 : compter « Dispatching zone to player » par invité. Plus
  d'un = confirmé. Correction alors : quand `_pendingHostMove` vise la carte rendue, garder le joueur en attente et
  n'envoyer sa copie du monde qu'une fois l'host arrivé (~12 lignes, même fichier que A1a : à faire après lui).

## 4. Section B : défauts à trois joueurs ou plus

### B4. Quête de l'host : les visiteurs de la ville ne sont pas invités — rang 5
- **Fait (lu).** `ElinNetHostTravel.cs:239-253` n'invite que celui qui a le bail de la ville. Chez l'invité, la question
  est refusée à qui ne tient pas la carte (`ElinNetClientTravel.cs:681` et `:703`, `!Session.IsZoneAuthority`).
- **Changer.** (1) Host, boucle `:239` : accepter aussi `_guests.TryGetValue(peer.Id, out var at) && at.ZoneUid ==
  instance.uidZone`. (2) Invité : aux deux lignes, remplacer `!Session.IsZoneAuthority` par
  `!Session.IsAway` (`IsZoneAuthority` = `IsAway && !IsGuest`, `M:Net/NetSession.cs:61`). (3) `FollowHost` : supposé bon pour un visiteur (il quitte la session
  du teneur puis rejoint l'host par `SendRejoin`) ; **jamais joué**, à lire avant d'écrire. Pas de nouvelle case : c'est
  la case existante des quêtes à deux.
- **Gain.** À 4 : les deux visiteurs reçoivent la question comme le teneur. « B suit A sans l'host » : hors de ce lot.
- **Risque.** Le visiteur part pendant que le teneur garde son personnage : c'est le chemin normal d'un visiteur qui
  s'en va (`OnZoneGuestLeave`), mais un doublon de personnage est le défaut à guetter.
- **Test.** Trois fenêtres : host + A (tient Vernis) + B (visiteur). L'host prend une chasse (`hunt_suite` a le chemin).
  Rouge : chez B aucune boîte. Vert : boîte chez A et chez B ; B dit oui : B est sur la carte de la quête, une seule
  fois, avec son sac ; A dit non : A n'a pas bougé.

### B3a. Sommeil : dire qui on attend — rang 6 (le reste de B3 est au conseil)
- **Fait (lu).** Il faut tous les joueurs vivants couchés (`M:Patches/Synchronization/SleepSynchronizationContext.cs:46-62`).
  La nuit ne passe que par le sommeil de **celui qui simule la carte** (`:257-277`). Le message dit qui vient de se
  coucher et « 2/3 » (`M:Models/Delta/Misc/SleepReadyDelta.cs:34-41`), jamais qui manque.
- **Changer.** `SleepReadyDelta` : champ `Waiting` (liste d'index) rempli dans `Announce` (`:90-103`) ; `Play()` ajoute
  « en attente de : noms » ; un texte dans les deux fichiers de langue. Répéter toutes les 20 s tant que ça attend.
- **Risque.** Aucun sur le jeu. **Test.** Trois fenêtres : deux couchés, un debout ; le texte nomme le troisième.

### B1. Le deuxième invité et les suivants rechargent — rien à coder ici
- Cases : faites et vertes. Reste le coût, lié au choix « qui tient la carte » : voir le conseil. À ajouter au test :
  `perf_probe` autour de Q1 et Q2 de `trio_place_suite.py` (durée de l'écran de chargement de chaque invité).

### B2 et B5 : voir « Pour le conseil ».

## 5. Pour le conseil (choix, pas bugs : options et coût, sans trancher)

**A5. Le repos d'un joueur accélère le monde de tous.** Lu : `M:Patches/Synchronization/GameSynchronizationContext.cs:113-128`
(l'avance rapide d'un joueur présent accélère l'host), `:56-61` (les autres jeux suivent) ; `M:Patches/PauseGame.cs:34-36`
(le monde ne s'arrête que si tous sont immobiles).
1. Garder. Coût : à 4, « le temps saute » dès que quelqu'un se repose ou travaille.
2. L'avance rapide ne vaut que si aucun autre joueur de la carte n'agit (~6 lignes). Coût : celui qui se repose attend
   en temps réel dès qu'un autre bouge ; un joueur actif bloque le repos des trois autres.
3. À la majorité. Coût : à 4, deux contre deux ne tranche pas ; règle à expliquer au joueur.
4. Le repos n'avance que l'horloge de celui qui se repose. Coût : c'est le « temps du monde commun », à ne pas commencer
   sans l'utilisateur ; touche la date, la faim, les quêtes à délai.

**B3. Nuit bloquée par un joueur.**
1. Tous (aujourd'hui) + B3a. Coût : un joueur absent de son clavier bloque la nuit, sans limite.
2. Majorité couchée depuis 30 s. Coût : les éveillés perdent des heures de jeu sans l'avoir voulu (faim, délais).
3. Un seul dormeur + 60 s sans refus. Coût : le même, en plus fort.
4. Chacun dort pour soi, la date ne bouge pas. Coût : le sommeil ne fait plus passer la nuit ; horloge par joueur.
   Contrainte lue pour 2 et 3 : si c'est **l'host** qui reste debout, la nuit ne peut pas passer aujourd'hui
   (`:271`, il faut le sommeil de celui qui simule). Sans réécrire cela, la règle resterait inégale entre host et invités.

**B5. Deux invités ne se voient pas sur la carte du monde.** Lu : chacun reçoit sa propre copie
(`ElinNetHostTravel.cs:183-199`, `:1538-1541`), et l'host y entre toujours sans rappel (`:696-698`).
1. Garder. Coût : avec l'host on se voit, entre invités non.
2. Afficher les autres comme des repères (la case de chacun passe par l'host, une fois par seconde). Coût : ~60 lignes,
   on se voit mais on ne peut ni se parler de près ni échanger ; aucun rechargement.
3. Une vraie carte du monde commune (le premier la tient, les autres le rejoignent). Coût : un rechargement de monde à
   chaque entrée et sortie de la carte du monde pour tous sauf un, donc plus de gels ; passations en plus.

**B2. L'invité encore en chargement est emmené par l'host.** Lu : `ElinNetHostTravel.cs:165-170` (seuls les installés
restent), installé = `ElinNetHostZone.cs:147`. A1a raccourcit l'attente, sans la supprimer.
1. Garder. Coût : l'invité atterrit sur l'host sans l'avoir voulu, plus souvent à 4.
2. L'host attend au plus 10 s que les joueurs en chargement soient installés avant de changer de carte. Coût : l'host
   est retenu par les autres (aujourd'hui personne ne le retient) ; ~15 lignes, sur le modèle de `_pendingHostMove`.
3. Le joueur en chargement devient visiteur du teneur, ou reçoit la carte avec un bail s'il est seul. Coût : ~25 lignes,
   un rechargement de plus pour lui ; risque de personnage en double pendant le croisement.

**A4b. Point de passage sans la carte deux fois sur trois.** L'host l'accepte déjà (`:1241`). Coût : si le teneur
plante, la carte a jusqu'à 3 min et le personnage 1 min : un objet ramassé entre les deux existe deux fois, un objet
posé est perdu. Aujourd'hui carte et personnage partent ensemble. À ne peser qu'après la mesure de A4a.

**B1/B6. Qui tient la carte quand l'host part.** Aujourd'hui le premier connecté (`:168-184`) ; les autres rechargent.
Options : garder ; choisir le meilleur lien (`AvgPingMs` est déjà connu) ; que l'host parti continue de simuler la
carte pour ceux qui restent (personne ne recharge, mais l'host simule deux cartes : gros chantier).

## 6. Ordre de réalisation, en lots indépendants

| Lot | Contenu | Fichiers du mod | Fenêtres | Peut s'écrire en même temps que |
|---|---|---|---|---|
| 0 | `perf_probe.py`, chiffres « avant » | aucun | 2 puis 3 | tout |
| 1 | A3 | `SteamNetManager.cs`, `EmpConstants.cs` | 2 | 2, 3, 4, 5, 6 |
| 2 | A2 | `CardCache.cs` | 2 | 1, 3, 4, 5, 6 |
| 3 | A1a | `EmpAutoHost.cs`, `ElinNetHostTravel.cs` (l. 1153) | 3 | 1, 2, 4, 6 |
| 4 | A4a | `LZ4Bytes.cs` (+ `ZoneLeaseState.cs`, `ZoneDataResponse.cs` si paramètre) | 2 | 1, 2, 3, 5, 6 |
| 5 | B4 | `ElinNetHostTravel.cs` (l. 239), `ElinNetClientTravel.cs` (l. 681, 703) | 3 | 1, 2, 4, 6 ; **pas 3** (même fichier) |
| 6 | B3a | `SleepSynchronizationContext.cs`, `SleepReadyDelta.cs`, textes | 3 | 1 à 5 |
| 7 | A1b, objet `perf` dans `state` | `ElinNetHostTravel.cs`, `EmpDebugListener.cs` | 3 | après 3 et 5 |
| C | A5, B3, B5, B2, A4b, B1/B6 | selon le verdict | - | après le conseil |

- Un lot = un test = un commit ; compiler une seule fois pour les lots 1 à 4 est possible (fichiers disjoints), mais
  les chiffres « après » se prennent **lot par lot** si on veut savoir lequel a payé.
- Les lots 3, 5, 6, 7 demandent trois fenêtres : accord de l'utilisateur à redemander (règle du Steam Deck).
- Trois fenêtres sur un PC se partagent le processeur : comparer avant/après sur la même machine, pas avec la vraie soirée.
- Non testable au banc : le débit réel sur Internet (A3, A4a). Le dire dans le résumé de version.

## 7. Questions restées ouvertes

1. « Ça galère » : des arrêts nets (A1, A4, sauvegarde) ou tout mou en continu (A3, A2) ? La réponse change le rang 1.
2. Pire chez l'host ou chez les invités ? Pire tous ensemble, ou dispersés (dispersés = A4 à plein) ?
3. Les cinq choix du conseil ci-dessus.
