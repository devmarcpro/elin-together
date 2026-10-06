# Elin Together « indépendance » 0.26.510

(English below / version anglaise plus bas)

Corrections après une vraie soirée à trois joueurs et plus. Compilé pour Elin **EA 23.352 Patch 1** (canal Nightly).
**Tous les joueurs doivent installer ce même zip.**

## Corrigé

- **Les invités ne sont plus téléportés sur l'hébergeur.** Quand l'hébergeur part ou revient, chaque invité garde sa
  case. Un joueur entre sur une carte par son entrée, et n'arrive plus dans l'eau sur la carte du monde.
- **Le temps d'un autre joueur ne vous coûte plus rien.** Quand un joueur voyage ou dort, la date avance pour tous, mais
  vous n'avez pas plus faim, votre nourriture ne pourrit pas, vos états et vos délais de quête ne bougent pas.
- **Sommeil** : seuls les familiers du dormeur le rejoignent ; un invité qui dort seul ne voit plus sa carte rechargée.
- **Musique** : le personnage d'un autre joueur ne jette plus de pièces au musicien.
- **Ancien personnage** : un personnage de joueur que personne ne joue ne reste plus sur la carte à se battre.
- **Cave** : une cave où se trouve un joueur n'est plus refaite quand un autre y entre.
- **Chargement rapide** : arrêté dans une partie à plusieurs (il ouvrait une fenêtre d'erreur chez l'invité).

## Nouveau

- **Coupure de liaison** : l'invité revient tout seul dans la partie (essais pendant 3 minutes).
- **Plus d'écran « Who do you want to play? »** à chaque connexion : chacun retrouve son personnage.
- **Sauvegarde automatique** chez l'hébergeur, toutes les 2 minutes quand un autre joueur est là.
- **Un monde déjà partagé ouvre sa partie tout seul** au chargement (amis Steam).
- **Dépôt (GitHub ou dossier)** : si quelqu'un héberge déjà le monde, le joueur suivant est envoyé dans sa partie
  (bouton « Join ») au lieu d'en ouvrir une copie.

## Pas encore corrigé

- Banque et coffre d'expédition d'un invité seul sur une autre carte que l'hébergeur : sa fenêtre se rouvre vide (ce
  qu'il a déposé est chez l'hébergeur). En attendant, déposez sur la carte de l'hébergeur.
- Le rangement automatique peut ranger des objets de la barre d'outils.
- Deux factures au lieu d'une ; un donjon marqué conquis sans que le boss soit vaincu.
- Au réveil, la recette apprise est celle de l'hébergeur ; le grimoire et l'oreiller de l'invité ne comptent pas.
- Le jeu ralentit quand le nombre d'invités augmente.
- Quand l'hébergeur part ou plante, aucun invité ne reprend le monde tout seul : il faut le reprendre à la main.

## Ce qui a été testé

Sur un seul PC : à trois fenêtres du jeu, les places des joueurs (17/17) et le temps (25/25) ; à deux fenêtres, les
suites habituelles. **Ces corrections n'ont pas encore été rejouées entre vrais PC**, et la redirection par Steam
n'a jamais été jouée entre deux comptes. La cave et l'ancien personnage sont les corrections les moins sûres.
Faites une copie de vos sauvegardes avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly**. Chacun télécharge `ElinTogether-independance.zip` (ci-dessous), le décompresse et lance `Installer.bat`
(`Desinstaller.bat` fait l'inverse). `LISEZMOI.txt` dans le zip explique le reste. Pour héberger : lancer Elin par
Steam, charger une partie qui a un terrain revendiqué, puis Échap → Mods → Elin Together.

---

# Elin Together "independence" 0.26.510

Fixes after a real evening with three players and more. Built for Elin **EA 23.352 Patch 1** (Nightly branch).
**Every player must install this same zip.**

## Fixed

- **Guests are no longer teleported onto the host.** When the host leaves or comes back, every guest keeps its tile. A
  player enters a map by its entrance, and no longer lands in water on the world map.
- **Another player's time costs you nothing.** When a player travels or sleeps, the date moves on for all, but you are
  no hungrier, your food does not rot, your conditions and quest deadlines do not move.
- **Sleep**: only the sleeper's own pets join it; a guest sleeping alone no longer gets its map reloaded.
- **Music**: another player's character no longer throws coins at the musician.
- **Former character**: a player character nobody plays no longer stays on the map and fights.
- **Cave**: a cave with a player in it is no longer rebuilt when another player enters.
- **Quick load**: stopped in a shared game (it opened an error window for the guest).

## New

- **Dropped link**: the guest comes back into the game by itself (tries for 3 minutes).
- **No more "Who do you want to play?" screen** at each connection: everyone gets their character back.
- **Automatic save** on the host, every 2 minutes while someone else plays.
- **A world already shared opens its session by itself** on load (Steam friends).
- **Depot (GitHub or folder)**: if someone already hosts the world, the next player is sent into that game ("Join"
  button) instead of opening a copy.

## Not fixed yet

- Bank and shipping chest of a guest alone on another map than the host: the window reopens empty (what was deposited
  is with the host). Until then, deposit on the host's map.
- Auto-dump may put toolbar items away.
- Two bills instead of one; a dungeon marked as conquered while its boss is alive.
- On waking, the recipe learned is the host's; the guest's spellbook and pillow do not count.
- The game slows down as guests are added.
- When the host leaves or crashes, no guest takes the world over by itself: it is taken over by hand.

## What was tested

On one PC: with three game windows, player positions (17/17) and time (25/25); with two windows, the usual suites.
**These fixes have not been replayed between real PCs yet**, and being sent to the current host through Steam has
never been played between two accounts. The cave and former-character fixes are the least certain. Back up your saves
first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the **Nightly**
branch. Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French. To host:
launch Elin through Steam, load a save that has a claimed land, then Esc → Mods → Elin Together.
