# Elin Together « indépendance » 0.26.605

(English below / version anglaise plus bas)

Suite de la 0.26.597 : **deux corrections venues d'une vraie soirée**, lues dans les journaux des joueurs. Elles sont
**écrites et compilées, pas jouées** : ni au banc de test, ni en vraie partie. Si cette version se passe mal, la
0.26.597 reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal Nightly). **Tous les joueurs doivent installer
ce même zip.** Faites une copie de vos sauvegardes avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé (pas joué)

- **Impossible de rejoindre une partie avec un personnage monté.** Le personnage était posé sur la case donnée par
  l'hébergeur, sa monture restait à sa place d'avant, hors de cette carte : le jeu levait une erreur au démarrage de la
  carte, puis la même erreur cinq fois par seconde. La monture (et ce qui chevauche le personnage) est maintenant
  amenée sur sa case avant que la carte démarre.
- **Une erreur à chaque dialogue avec un personnage, chez un joueur qui a un mod de langue** (français…), après la
  relance d'Elin « avec les mods de la partie » : la relance coupait aussi son mod de langue
  (`DirectoryNotFoundException … Lang\EN\Dialog\dialog.xlsx`). Le mod qui apporte la langue du joueur reste allumé.

## À savoir : la relance d'Elin pour les mods

Ce que des testeurs ont décrit comme « le jeu plante à la première connexion, puis entre à la deuxième » est la relance
voulue depuis la 0.26.590 : quand vos mods ne sont pas ceux de la partie, Elin se ferme et se relance **une fois** avec
les mods de la partie. Elle revient **à chaque lancement d'Elin**, parce que votre propre liste de mods revient à
chaque fois. Pour l'éviter : abonnez-vous sur le Workshop aux mods de la partie, ou décochez « Fetch the mods of the
game by itself » dans l'onglet « Client Settings ». Une façon plus simple est à l'étude.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
- Quand l'hébergeur et un invité se retrouvent sur une carte, l'écran de l'invité recharge (le monde entier est renvoyé), sauf si l'hébergeur coche la case « No world reload when the host and a player meet again ».
- Quand l'hébergeur part ou plante, aucun invité ne reprend le monde tout seul.

## En cas de problème pendant une partie

- L'hébergeur décoche la case en cause (Échap → Mods → Elin Together → Server Setting).
- Un joueur désynchronisé tape `emp.reconnect_self` dans la console.
- Envoyez les journaux de chacun : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly**. Chacun télécharge `ElinTogether-independance.zip` (ci-dessous), le décompresse et lance `Installer.bat`
(`Desinstaller.bat` fait l'inverse). `LISEZMOI.txt` dans le zip explique le reste.

**Sur Mac** (Elin dans CrossOver, Whisky ou Wine) : téléchargez `ElinTogether-independance-mac.zip`, décompressez-le,
ouvrez le Terminal, tapez `bash` puis un espace, faites glisser `Installer-Mac.command` dans la fenêtre et appuyez sur
Entrée. C'est le même mod ; `LISEZMOI-MAC.txt` explique le reste. **Pas encore essayé sur un vrai Mac.**

---

# Elin Together "independence" 0.26.605

Follows 0.26.597: **two fixes from a real evening**, read in the players' logs. They are **written and compiled, not
played**: neither on the test bench nor in a real game. If this version goes wrong, 0.26.597 stays online. Built for
Elin **EA 23.352 Patch 1** (Nightly branch). **Every player must install this same zip.** Back up your saves first:
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed (not played)

- **A mounted character could not join a game.** The character was put on the tile the host gives, its mount stayed
  where it was before, outside that map: the game threw when the map started, then the same error five times a second.
  The mount (and what rides the character) is now brought onto its tile before the map starts.
- **An error at every talk to a character, for a player with a language mod** (French…), after Elin restarted "with
  the mods of the game": the restart switched the language mod off too
  (`DirectoryNotFoundException … Lang\EN\Dialog\dialog.xlsx`). The mod that brings the player's language stays on.

## Good to know: Elin restarting for the mods

What testers described as "the game crashes on the first join, then connects on the second" is the restart meant
since 0.26.590: when your mods are not those of the game, Elin closes and restarts **once** with the mods of that
game. It comes back **at every start of Elin**, because your own mod list comes back each time. To avoid it: subscribe
on the Workshop to the mods of the game, or untick "Fetch the mods of the game by itself" in the "Client Settings"
tab. A simpler way is being looked at.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- When the host and a guest meet on a map, the guest's screen reloads (the whole world is sent again), unless the host ticks "No world reload when the host and a player meet again".
- When the host leaves or crashes, no guest takes the world over by itself.

## If something goes wrong during a game

- The host unticks the checkbox (Esc → Mods → Elin Together → Server Setting).
- A desynced player types `emp.reconnect_self` in the console.
- Send everyone's logs: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the **Nightly**
branch. Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French.

**On a Mac** (Elin in CrossOver, Whisky or Wine): download `ElinTogether-independance-mac.zip`, unzip it, open
Terminal, type `bash` and a space, drag `Installer-Mac.command` into the window and press Enter. Same mod;
`LISEZMOI-MAC.txt` (in French) has the rest. **Not tried on a real Mac yet.**
