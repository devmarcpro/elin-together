# Récupérer les mods de l'host en rejoignant (demande du 2026-10-07) — faits établis, rien d'écrit, conseil à réunir

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
