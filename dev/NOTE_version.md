# Elin Together « indépendance » 0.26.584

(English below / version anglaise plus bas)

Suite de la 0.26.566. Cette fois une bonne partie est **jouée au banc de test** (deux fenêtres sur un même PC), pas
encore dans une vraie partie. Si cette version se passe mal, la 0.26.566 reste en ligne. Compilé pour Elin **EA 23.352
Patch 1** (canal Nightly). **Tous les joueurs doivent installer ce même zip, et avoir la même liste de mods.** Faites
une copie de vos sauvegardes avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Nouveau

- **Compatibilité AutoAct** (mod du Workshop) : un invité peut répéter une action (récolter, creuser, miner,
  arroser…) comme l'hébergeur ; chaque tour est vraiment joué dans le monde. Joué au banc.
- **Compatibilité Dynamic Riding** (mod du Workshop) : plus d'erreur à chaque rechargement d'écran quand un joueur est
  sur une monture. Joué au banc.
- **Liste des mods du monde dans le dépôt GitHub** : un fichier `modlist.txt` est déposé à côté de la sauvegarde, une
  ligne par mod avec le lien de sa page du Workshop. Il est écrit une seule fois (par le premier joueur qui envoie le
  monde avec cette version) et n'est plus remplacé par le jeu : on le modifie à la main dans le dépôt.
- **Moins de rechargements d'écran, derrière une case décochée** (« Server Setting », chez l'hébergeur) : quand
  l'hébergeur rejoint un invité sur sa carte, ou qu'un invité rejoint l'hébergeur, l'invité ne reçoit plus le monde
  entier. Au banc : zéro rechargement complet sur six étages de donjon, au lieu d'un par étage. **Décochée par
  défaut** : pas encore jouée à trois joueurs ni avec des compagnons. Au moindre doute le jeu retombe en silence sur
  le rechargement d'avant.

## Corrigé

- **Villes qui ne se régénéraient plus, donjons qui n'expiraient plus** : une carte tenue par un invité puis rendue à
  l'hébergeur revenait marquée « jamais ». Corrigé, et les mondes déjà touchés sont réparés tout seuls au chargement
  par l'hébergeur. Écrit et compilé, pas joué.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
- Quand l'hébergeur et un invité se retrouvent sur une carte, l'écran de l'invité recharge (le monde entier est renvoyé), sauf si l'hébergeur coche la nouvelle case.
- Quand l'hébergeur part ou plante, aucun invité ne reprend le monde tout seul.
- Ce qui a été collecté dans le codex avant cette version par un invité ne revient pas.

## En cas de problème pendant une partie

- L'hébergeur décoche la case en cause (Échap → Mods → Elin Together → Server Setting).
- Un joueur désynchronisé tape `emp.reconnect_self` dans la console.
- Envoyez les journaux de chacun : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly**. Chacun télécharge `ElinTogether-independance.zip` (ci-dessous), le décompresse et lance `Installer.bat`
(`Desinstaller.bat` fait l'inverse). `LISEZMOI.txt` dans le zip explique le reste.

---

# Elin Together "independence" 0.26.584

Follows 0.26.566. This time a good part was **played on the test bench** (two windows on one PC), not yet in a real
game. If this version goes wrong, 0.26.566 stays online. Built for Elin **EA 23.352 Patch 1** (Nightly branch).
**Every player must install this same zip and have the same list of mods.** Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## New

- **AutoAct compatibility** (Workshop mod): a guest can repeat an action (harvest, dig, mine, water…) like the host;
  each round is really played in the world. Played on the bench.
- **Dynamic Riding compatibility** (Workshop mod): no more error at every screen reload when a player rides a mount.
  Played on the bench.
- **The mod list of the world in the GitHub depot**: a `modlist.txt` file next to the save, one line a mod with the
  link of its Workshop page. Written once (by the first player who sends the world with this version) and never
  replaced by the game: change it by hand in the repository.
- **Fewer screen reloads, behind an unticked checkbox** ("Server Setting", on the host): when the host joins a guest
  on its map, or a guest joins the host, the guest no longer receives the whole world. On the bench: no full reload on
  six dungeon floors, where there was one per floor. **Unticked by default**: not played yet with three players or
  with companions. At the slightest doubt the game silently falls back to the old reload.

## Fixed

- **Towns that no longer regenerated, dungeons that no longer expired**: a map held by a guest then handed back to the
  host came back marked "never". Fixed, and worlds already marked are repaired by themselves when the host loads
  them. Written and compiled, not played.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- When the host and a guest meet on a map, the guest's screen reloads (the whole world is sent again), unless the host ticks the new checkbox.
- When the host leaves or crashes, no guest takes the world over by itself.
- What a guest collected in the codex before this version does not come back.

## If something goes wrong during a game

- The host unticks the checkbox (Esc → Mods → Elin Together → Server Setting).
- A desynced player types `emp.reconnect_self` in the console.
- Send everyone's logs: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the **Nightly**
branch. Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French.
