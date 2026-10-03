# Plan : profil de mods pour le multijoueur (en file d'attente)

Idée de l'utilisateur (2026-10-02) : un joueur garde ses mods à lui, mais dès qu'il joue avec ElinTogether, seuls
les mods de la partie sont chargés. Approche validée par l'utilisateur le 2026-10-02 (« ça me paraît bien comme
tu dis »). **Rien n'est écrit. Rien n'a encore été lu dans le code d'Elin.**

## Contrainte

Elin charge les mods au démarrage. On ne peut pas en retirer un proprement en pleine partie (il a déjà modifié le
code du jeu et ajouté ses objets). Donc : **changer de mods = relancer le jeu**.

## Étapes prévues

1. **Profil multijoueur avec redémarrage** (à faire en premier).
   - L'host a sa liste de mods (nom, identifiant, version).
   - Un joueur qui rejoint avec une liste différente voit « Redémarrer avec les mods de l'host ? ».
   - ElinTogether n'active que ces mods-là, relance le jeu et rejoint la partie tout seul.
   - En quittant, la liste du joueur est remise au lancement suivant.
2. **Mods tolérés** : ceux qui ne changent que l'affichage (portraits, interface, sons) n'ont pas besoin d'être
   identiques. L'host coche lesquels sont tolérés ; le redémarrage n'est demandé que pour les autres.
3. **Mods manquants** : d'abord seulement les lister (« il te manque X et Y »). Plus tard, peut-être
   l'abonnement automatique pour les mods du Workshop. Pas d'envoi de mods locaux par l'host (ce serait exécuter
   du code reçu d'un autre joueur).

Comme tout le reste : une case à cocher côté host.

## À lire avant d'écrire

- Où Elin range la liste des mods actifs et leur ordre (`ModManager`, `BaseModManager`, écran « Mod Viewer »),
  et si on peut la changer avant le chargement.
- Ce que fait déjà la validation à la connexion (`SourceValidationSet` : `sources`, `plugins`, `all`,
  `CreateValidation`), pour s'appuyer dessus plutôt que la refaire.
- La relance automatique : `Emp/EmpBotLauncher.cs` lance déjà une autre fenêtre qui rejoint seule (`-empbot`).
- Abonnement Workshop par l'API Steam : à vérifier.

## Questions restées ouvertes

- Le redémarrage automatique (environ une minute) convient-il ? (supposé oui)
- Étape 2 tout de suite ou plus tard ? (supposé : après l'étape 1)

## Test prévu

Deux copies du jeu avec des listes de mods différentes (`_lab/Elin2` a son propre dossier `Package`) : le client
rejoint, accepte, redémarre avec la liste de l'host, arrive en jeu ; il quitte, relance : sa liste est revenue.

## Plan détaillé (agent, lecture seule, 2026-10-03) — rien n'est écrit

Ce que la lecture du jeu (23.350, fonctions revérifiées dans 23.351) a établi :
- Elin lit `loadorder.txt` (à côté de `Elin.exe`, format `chemin,0|1,id`) **avant** de charger les DLL des mods ;
  ElinTogether ne peut donc jamais changer la liste du démarrage en cours : écrire la liste de l'host, relancer.
  Un mod installé mais absent du fichier est **activé** : le fichier écrit doit tout lister.
- Le jeu a des préréglages officiels (`User/Load Order/*.txt`, `ModManager.ApplyPreset`, `SaveLoadOrder`,
  `ModLoadOrderPreset.FindMissing` pour les mods manquants) : à réutiliser plutôt qu'écrire le fichier à la main.
- Les DLL de `BepInEx/plugins` se chargent sans tenir compte de la liste : impossibles à couper.
- Aujourd'hui aucun message d'ElinTogether ne transporte la liste des mods de l'host (seulement des écarts de
  DLL, par GUID BepInEx) : à ajouter dans `SourceValidationRequest` (`HostMods`).
- Relancer : attendre la fin du processus (une seule instance permise), `Elin.exe` direct si `steam_appid.txt`
  existe, sinon `steam://rungameid/2135150` ; retirer les variables `DOORSTOP*` (sinon le jeu relancé n'a aucun
  mod, comme pour le bot) ; les informations pour rejoindre (port, lobby, host) dans un fichier, pas en arguments.
- Remettre la liste du joueur **dès le démarrage relancé** (`EmpMod.Awake`, état `boot` → `session`) : le jeu
  tourne avec les mods de l'host mais le fichier sur le disque est déjà celui du joueur ; un plantage ne peut donc
  pas laisser la liste de l'host, sauf plantage avant le chargement d'ElinTogether (réparation : renommer la copie
  `loadorder.elintogether-player.txt`). Bloquer `SaveLoadOrder` (fermeture du Mod Viewer) pendant une telle session.
- Ordre : modèle + case host `ModProfile` ; envoi par l'host ; comparaison et question chez le client
  (« Restart with the host's mods » / « Keep my mods ») ; `Emp/EmpModProfile.cs` (comparer, relancer, remettre,
  rejoindre) ; fin de session (proposer de relancer avec ses mods, avertir avant de charger une partie solo) ;
  liste des manquants ; mods tolérés ; textes.
- Test prévu `modprofile_suite.py` sur le banc (copie `_lab/Elin2` avec une autre liste) ; ne teste pas la relance
  par Steam ni le retour dans un lobby Steam (il faut un vrai second compte).
- Risques : boucle de redémarrages (ne jamais reproposer pour la même liste), délai de 15 s de l'host pendant la
  question (le porter à 120 s), abonnement Workshop ajouté entre-temps (activé par défaut), antivirus et
  PowerShell caché, Proton/Steam Deck (relance à la main).
