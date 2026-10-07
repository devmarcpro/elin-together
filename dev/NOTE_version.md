# Elin Together « indépendance » 0.26.560

(English below / version anglaise plus bas)

Suite de la 0.26.557, d'après le journal d'une vraie partie jouée avec elle. **Écrit et compilé, pas joué.** Si cette
version se passe mal, la 0.26.557 reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal Nightly). **Tous les
joueurs doivent installer ce même zip, et avoir la même liste de mods.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé

- **Jeu cassé (une erreur à chaque instant) en rejoignant l'hébergeur** : un invité mort gardait la position de la
  carte où il était mort ; replacé sur une carte plus petite (un autre étage de donjon), il se retrouvait hors de la
  carte. Le personnage est maintenant posé à la place donnée par l'hébergeur avant l'affichage de la carte, et si
  l'affichage échoue quand même, le jeu replace le personnage et redemande la carte.

Confirmé par ce même journal : plus aucune erreur de la Guilde des guerriers depuis la 0.26.557.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
- Quand l'hébergeur rejoint un invité sur sa carte, l'écran de l'invité recharge (le monde entier est renvoyé).
- Quand l'hébergeur part ou plante, aucun invité ne reprend le monde tout seul.

## En cas de problème pendant une partie

- L'hébergeur décoche la case en cause (Échap → Mods → Elin Together → Server Setting).
- Un joueur désynchronisé tape `emp.reconnect_self` dans la console.
- Envoyez les journaux de chacun : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly**. Chacun télécharge `ElinTogether-independance.zip` (ci-dessous), le décompresse et lance `Installer.bat`
(`Desinstaller.bat` fait l'inverse). `LISEZMOI.txt` dans le zip explique le reste.

---

# Elin Together "independence" 0.26.560

Follows 0.26.557, from the log of a real game played with it. **Written and compiled, not played.** If this version
goes wrong, 0.26.557 stays online. Built for Elin **EA 23.352 Patch 1** (Nightly branch). **Every player must install
this same zip and have the same list of mods.** Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed

- **Game broken (an error at every moment) when joining the host**: a dead guest kept the position of the map it died
  on; put on a smaller map (another dungeon floor), it stood outside the map. The character is now placed where the
  host says before the map is shown, and if showing it still fails, the game places the character and asks for the map
  again.

Confirmed by that same log: no Fighters Guild error since 0.26.557.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- When the host joins a guest on its map, the guest's screen reloads (the whole world is sent again).
- When the host leaves or crashes, no guest takes the world over by itself.

## If something goes wrong during a game

- The host unticks the checkbox (Esc → Mods → Elin Together → Server Setting).
- A desynced player types `emp.reconnect_self` in the console.
- Send everyone's logs: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the **Nightly**
branch. Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French.
