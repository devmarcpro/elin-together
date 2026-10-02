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
