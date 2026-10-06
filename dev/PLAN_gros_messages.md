# Gros messages et file d'envoi pleine (2026-10-06)

État : écrit, compilé (ReleaseNightly, 0 erreur), testé hors jeu (`dev/_tools/chunk_check`, 20 vérifications).
**Pas encore vu en jeu.**

## Les faits

- Steam refuse un message de plus de 512 Kio : `k_cbMaxSteamNetworkingSocketsMessageSizeSend = 524288`, lu dans
  `com.rlabrecque.steamworks.net.dll` du jeu (`Steamworks.Constants`). Retour : `k_EResultInvalidParam`.
- La file d'envoi d'une connexion est de 512 Kio par défaut (`k_ESteamNetworkingConfig_SendBufferSize`, valeur 9 dans
  l'énumération de la DLL). Le mod ne la change nulle part (aucun `SetConfigValue` hors la perte simulée de la
  console). Quand « octets en attente + message » dépasse, Steam rend `k_EResultLimitExceeded` et ne prend rien.
- Tous les messages du mod sont fiables (aucun envoi non fiable hors du transport). Avant ce changement, un refus =
  message perdu : avec un avertissement pour un pair seul, **sans rien dans le journal** pour l'envoi à tous dès
  deux invités (`SteamNetPeerBroadcast.Send`, ancienne boucle).
- La liaison locale du banc (`StartServerUdp`) est la même bibliothèque Steam (`CreateListenSocketIP`) et le même
  `SteamNetPeer.Send` : mêmes limites, donc le banc peut prouver la correction.
- Pas de découpage avant ce changement. Pas de mesure de taille par message : seulement le cumul par pair
  (`SteamNetPeerStat.BytesSent`).

## Ce qui change

- `ElinTogether/Net/NetFragments.cs` (neuf, sans Steam ni Unity) : `NetFragments.Split` et `NetFragmentAssembler`.
  En-tête de 20 octets : marque, numéro de message, index, nombre de morceaux, taille totale. Morceaux de 128 Kio,
  message de 64 Mio au plus.
- `SteamNetPeer.Send` : un message fiable ne se perd plus. S'il dépasse 128 Kio il est découpé ; si Steam répond
  « file pleine », il attend dans une file locale du pair. Tant que cette file n'est pas vide, tout message fiable
  suivant passe derrière (ordre d'envoi gardé). `Flush` la vide à chaque image (`SteamNetManager.Poll`) et s'arrête
  au premier « file pleine ». Un avertissement par épisode : « Send queue of … is full: N bytes in M messages ».
- `SteamNetPeerBroadcast.Send` : un message fiable passe par le `Send` de chaque pair.
- `SteamNetManager.Poll` : un morceau va à l'assembleur du pair ; le message entier suit le chemin habituel.

Pourquoi étaler plutôt que relever `SendBufferSize` : la limite de 512 Kio par message reste de toute façon, aucun
tampon raisonnable ne tient un monde de plusieurs Mo, et « essayer, garder si refusé » ne demande aucun réglage Steam.

## Limites connues

- File locale bornée à 64 Mio par pair : au-delà le message est refusé avec un avertissement.
- Un pair qui part pendant un gros envoi : ce qui attendait est perdu (un dernier `Flush` est tenté).
- Pendant l'envoi d'un gros message vers un pair, ses petits messages fiables attendent derrière.
- Les deux côtés doivent avoir ce changement ; l'empreinte de connexion ne change que si la version du mod change.

## Preuve au banc (jeu libre)

1. `cd dev/_tools/chunk_check && dotnet run -c Release` : `ALL OK`.
2. Fabriquer une grosse carte : sur l'host, par `emp.py eval`, poser quelques milliers d'objets variés dans la base
   (boucle `ThingGen.Create(...)` + `zone.AddCard(thing, point)`), sauvegarder, regarder la taille du dossier de la
   zone ; viser plus de 1 Mo compressé.
3. Rouge sur l'ancien build : le client rejoint ou revient, journal de l'host « Message of N bytes not sent ».
   Vert sur le nouveau : « Message of N bytes sent in K pieces », le client charge, `parity_suite` reste verte.
4. Faire partir un invité avec cette carte, attendre un point de passage (60 s), revenir : carte identique.

## Après relecture (6 octobre 2026, compilé, `chunk_check` : ALL OK, rien joué)

- **Trou définitif fermé** (`SteamNetPeer.cs`, `Break`) : au-delà de 64 Mio en attente, ou sur une erreur de Steam autre
  que « file pleine » pendant `Flush`, le pair est marqué cassé (`BrokenReason = RemoteClosed`), sa file est vidée,
  avertissement au journal, et `SteamNetManager.Poll` appelle `Disconnect` sur lui à l'image suivante. Les deux côtés
  lisent `RemoteClosed` comme un lien perdu (`IsLinkLost`) : l'invité se reconnecte seul (`NetReconnect`). Pas de fermeture
  depuis `Send` même : il tourne chez n'importe qui (diffusion, gestionnaires) et `Disconnect` rappelle l'écouteur.
  Pas couvert : une erreur autre que « file pleine » sur le chemin direct de `Send` (message fiable seul, file vide)
  renvoie encore `false` sans fermer (le lien est sans doute déjà mort ; à décider si on veut le même traitement).
- **`SteamNetTypeRegistry`** : un type dont le hash vaut `NetFragments.Magic` fait lever une exception à
  l'enregistrement du gestionnaire (au démarrage), message qui dit de renommer le type.
- **`InterruptedMessages`** est lu dans `SteamNetManager.Poll` : avertissement « A big message of … was given up ».
- **Mémoire à la demande** (`NetFragments.cs`) : l'assembleur garde les morceaux reçus et ne fabrique le message entier
  qu'au dernier morceau (une copie de plus, jamais de réservation de 64 Mio sur la foi de l'en-tête). Test ajouté dans
  `chunk_check` : « a first piece claiming 64 MB reserves nothing ».
