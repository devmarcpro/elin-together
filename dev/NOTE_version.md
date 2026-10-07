# Elin Together « indépendance » 0.26.557

(English below / version anglaise plus bas)

Suite de la 0.26.548, d'après le journal d'une vraie partie jouée avec elle. **Écrit, relu en partie et compilé, pas
joué** (le jeu n'était pas disponible pour les essais). Si cette version se passe mal, la 0.26.548 reste en ligne.
Compilé pour Elin **EA 23.352 Patch 1** (canal Nightly). **Tous les joueurs doivent installer ce même zip, et avoir la
même liste de mods.** Faites une copie de vos sauvegardes avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé

- **Messages d'erreur « guild_fighter2 », « guild_fighter3 »… à chaque monstre tué** chez un invité : quand un autre
  joueur faisait avancer la quête de la Guilde des guerriers, le jeu de l'invité gardait l'ancienne tâche et poussait
  la quête vers des étapes qui n'existent pas. La tâche est maintenant abandonnée, une quête refuse une étape qui
  n'existe pas, et une quête déjà coincée se répare toute seule.
- **Objet lancé par un autre joueur** (une balle, par exemple) : l'animation du vol plantait parfois et l'objet
  n'atterrissait pas dans votre jeu. Le lancer continue maintenant même si l'animation ne peut pas être dessinée.
- **Invité mort au moment où l'hébergeur quitte la carte** : sa demande de réanimation est redemandée (trois fois au
  plus) au lieu de le laisser mort.
- **Compétences et niveau** : l'hébergeur n'ignore plus ce que le personnage d'un joueur apprend pendant les quelques
  secondes de son arrivée.
- **Rune ou carburant** utilisé sur un objet ramassé à l'instant : dans la 0.26.548 il pouvait ne rien se passer.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
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

# Elin Together "independence" 0.26.557

Follows 0.26.548, from the log of a real game played with it. **Written, partly reviewed and compiled, not played**
(the game was not available for testing). If this version goes wrong, 0.26.548 stays online. Built for Elin **EA
23.352 Patch 1** (Nightly branch). **Every player must install this same zip and have the same list of mods.** Back up
your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed

- **Error messages "guild_fighter2", "guild_fighter3"… at every monster killed** on a guest: when another player moved
  the Fighters Guild quest on, the guest's game kept the old task and pushed the quest to steps that do not exist. The
  task is now dropped, a quest refuses a step it does not have, and a quest already stuck repairs itself.
- **A thing thrown by another player** (a ball, for instance): the flight animation sometimes failed and the thing
  never landed in your game. The throw now goes on even when the animation cannot be drawn.
- **A guest dead when the host leaves the map**: its revive request is asked again (three times at most) instead of
  leaving it dead.
- **Skills and level**: the host no longer ignores what a player's character learns during the few seconds of its
  arrival.
- **A rune or fuel** used on a thing picked up a moment before: in 0.26.548 nothing could happen.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- When the host leaves or crashes, no guest takes the world over by itself.

## If something goes wrong during a game

- The host unticks the checkbox (Esc → Mods → Elin Together → Server Setting).
- A desynced player types `emp.reconnect_self` in the console.
- Send everyone's logs: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the **Nightly**
branch. Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French.
