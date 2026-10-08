# Elin Together « indépendance » 0.26.597

(English below / version anglaise plus bas)

Suite de la 0.26.590 : **une correction importante**, à installer par tout le monde. Compilé pour Elin **EA 23.352
Patch 1** (canal Nightly). **Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes
avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé

- **L'histoire principale ne pouvait plus avancer depuis la 0.26.557**, chez l'hébergeur comme chez un invité. Signalé
  par des testeurs : le premier dialogue d'Ashland tournait en boucle, on n'en sortait pas, et la hache et l'or étaient
  redonnés sans fin ; la partie relancée rouvrait le même dialogue. Une protection ajoutée dans la 0.26.557 refusait
  tout changement d'étape de la quête principale. Merci pour le retour.
  - **Joué au banc** (deux fenêtres sur un même PC) : première rencontre avec Ashland, acte lu, puis la hache et l'or,
    par un invité ; une seule hache, l'histoire avance dans les deux jeux, le dialogue revient à son menu.
  - **Pas joué** : une nouvelle partie depuis l'écran de création, la suite de l'histoire (même cause, même
    correction), deux vrais PC.
  - Un monde déjà pris dans la boucle garde ses haches et son or en trop : rien ne les retire.

## Signalé, pas corrigé

- **« L'invité plante à sa première connexion, puis entre à la deuxième »** : pas reproduit. Ce n'est peut-être pas un
  plantage : quand vos mods ne sont pas ceux de la partie, Elin se ferme et se relance **une fois** avec les mods de
  la partie (nouveauté de la 0.26.590), après un message court en haut à gauche de l'écran. Si cela vous arrive,
  envoyez `Player.log` et `ElinMP\Logs` : nous saurons. Pour garder vos mods et seulement être prévenu des
  différences : décochez « Fetch the mods of the game by itself » dans l'onglet « Client Settings ».

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

# Elin Together "independence" 0.26.597

Follows 0.26.590: **one important fix**, to be installed by everyone. Built for Elin **EA 23.352 Patch 1** (Nightly
branch). **Every player must install this same zip.** Back up your saves first:
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed

- **The main story could no longer move on since 0.26.557**, for the host and for a guest. Reported by testers:
  Ashland's first dialog looped, could not be left, and the axe and the gold were given again without end; the game
  loaded again reopened the same dialog. A guard added in 0.26.557 refused every change of step of the main quest.
  Thank you for the report.
  - **Played on the bench** (two windows on one PC): the first meeting with Ashland, the deed read, then the axe and
    the gold, by a guest; one axe, the story moves on in both games, the dialog comes back to its menu.
  - **Not played**: a new game from the creation screen, the rest of the story (same cause, same fix), two real PCs.
  - A world already caught in the loop keeps its extra axes and gold: nothing removes them.

## Reported, not fixed

- **"The guest crashes on its first join, then connects on the second"**: not reproduced. It may not be a crash: when
  your mods are not those of the game, Elin closes and restarts **once** with the mods of that game (new in
  0.26.590), after a short message at the top left of the screen. If it happens to you, send `Player.log` and
  `ElinMP\Logs`: we will know. To keep your own mods and only be told what differs: untick "Fetch the mods of the game
  by itself" in the "Client Settings" tab.

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
