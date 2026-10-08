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


---

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


---

# Elin Together « indépendance » 0.26.590

(English below / version anglaise plus bas)

Suite de la 0.26.584. La nouveauté est **jouée au banc de test** (deux fenêtres sur un même PC), pas encore entre deux
vrais PC. Si cette version se passe mal, la 0.26.584 reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal
Nightly). **Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Nouveau

- **Les mods de la partie, sans s'abonner à rien.** Quand vous rejoignez une partie (ou prenez le monde dans le dépôt)
  et qu'il vous manque des mods du Workshop : ils sont téléchargés tout seuls, votre compte Steam ne s'abonne à rien,
  Elin se ferme et se relance **une fois** avec exactement les mods de la partie, puis vous y ramène sans rien
  cliquer. Si vous avez des mods en trop qui bloquent l'entrée, Elin se relance une fois sans eux. Au lancement
  suivant d'Elin, vous retrouvez votre propre liste de mods, intacte. Rien n'est jamais supprimé ni désabonné.
  - La liste de référence : le `modlist.txt` du dépôt quand le monde en vient, sinon les mods de l'hébergeur.
  - Si Elin ne se relance pas tout seul, relancez-le à la main dans la demi-heure : il vous ramène dans la partie.
  - Un mod installé à la main (hors Workshop) ne peut pas être téléchargé : son nom est affiché.
  - Pour garder vos mods et seulement être prévenu des différences : décochez « Fetch the mods of the game by itself » dans
    l'onglet « Client Setting ». **Ces mods sont choisis par l'hébergeur et tournent sur votre PC : à utiliser avec
    des gens de confiance.**
  - Joué au banc : téléchargement Steam sans abonnement, relance avec les mods de la partie, retour tout seul, liste
    du joueur retrouvée ensuite. **Pas joué** : la relance d'Elin par Steam, le retour par salon Steam et par dépôt
    GitHub (le banc relance lui-même et revient par une connexion locale), Steam Deck / Linux.
- **Un refus pour cause de mods nomme les mods** : ceux qui vous manquent, ceux à installer à la main, ceux en trop.
- **La liste des parties** indique combien de mods a chaque partie et combien vous manquent.

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

**Sur Mac** (Elin dans CrossOver, Whisky ou Wine) : téléchargez `ElinTogether-independance-mac.zip`, décompressez-le,
ouvrez le Terminal, tapez `bash` puis un espace, faites glisser `Installer-Mac.command` dans la fenêtre et appuyez sur
Entrée. C'est le même mod ; `LISEZMOI-MAC.txt` explique le reste. **Pas encore essayé sur un vrai Mac.**

---

# Elin Together "independence" 0.26.590

Follows 0.26.584. The new feature was **played on the test bench** (two windows on one PC), not yet between two real
PCs. If this version goes wrong, 0.26.584 stays online. Built for Elin **EA 23.352 Patch 1** (Nightly branch).
**Every player must install this same zip.** Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## New

- **The mods of the game, without subscribing to anything.** When you join a game (or take the world from the depot)
  and Workshop mods are missing: they are downloaded by themselves, your Steam account subscribes to nothing, Elin
  closes and restarts **once** with exactly the mods of that game, then brings you back into it without a click. If
  mods of yours block the join, Elin restarts once without them. At the next start of Elin your own mod list is back,
  untouched. Nothing is ever deleted or unsubscribed.
  - The reference list: the `modlist.txt` of the depot when the world comes from it, else the host's mods.
  - If Elin does not restart by itself, start it by hand within half an hour: it brings you back into the game.
  - A mod installed by hand (not on the Workshop) cannot be downloaded: its name is shown.
  - To keep your mods and only be told what differs: untick "Fetch the mods of the game by itself" in the "Client Setting" tab.
    **These mods are chosen by the host and run on your PC: use it with people you trust.**
  - Played on the bench: Steam download without subscribing, restart with the mods of the game, coming back by
    itself, the player's list back afterwards. **Not played**: Elin restarted by Steam, coming back through a Steam
    lobby or the GitHub depot (the bench restarts the game itself and comes back by a local connection), Steam Deck /
    Linux.
- **A join refused because of mods names the mods**: missing, to install by hand, extra.
- **The game list** shows how many mods each game has and how many you miss.

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

**On a Mac** (Elin in CrossOver, Whisky or Wine): download `ElinTogether-independance-mac.zip`, unzip it, open
Terminal, type `bash` and a space, drag `Installer-Mac.command` into the window and press Enter. Same mod;
`LISEZMOI-MAC.txt` (in French) has the rest. **Not tried on a real Mac yet.**


---

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


---

# Elin Together « indépendance » 0.26.566

(English below / version anglaise plus bas)

Suite de la 0.26.560. **Écrit et compilé, pas joué**, et le changement sur le codex est plus large que les
précédents : si cette version se passe mal, la 0.26.560 reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal
Nightly). **Tous les joueurs doivent installer ce même zip, et avoir la même liste de mods.** Faites une copie de vos
sauvegardes avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé

- **Le codex est maintenant commun à tous les joueurs**, comme les recettes : cartes collectées ou retirées, monstres
  tués, points faibles appris, apparitions. Avant, ce qu'un invité collectait n'était compté que chez lui et
  disparaissait au rechargement suivant ; ses cartes n'arrivaient chez l'hébergeur que si celui-ci avait coché
  « collecter les cartes ». C'est maintenant le réglage de celui qui ramasse qui décide.
- **Une carte reçue était parfois refusée une première fois** puis redemandée : elle passe du premier coup.

## Pour les prochaines versions

- Le journal note, à chaque retour d'un invité auprès de l'hébergeur, la durée de son absence et la taille du monde
  reçu. Rien ne change en jeu : ces chiffres serviront à supprimer les rechargements d'écran.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
- Quand l'hébergeur rejoint un invité sur sa carte, l'écran de l'invité recharge (le monde entier est renvoyé).
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

# Elin Together "independence" 0.26.566

Follows 0.26.560. **Written and compiled, not played**, and the codex change is wider than the previous ones: if this
version goes wrong, 0.26.560 stays online. Built for Elin **EA 23.352 Patch 1** (Nightly branch). **Every player must
install this same zip and have the same list of mods.** Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed

- **The codex is now shared by all players**, like the recipes: cards collected or taken out, monsters killed, weak
  spots learnt, appearances. Before, what a guest collected only counted in its own game and was gone at the next
  reload; its cards reached the host only if the host had "collect cards" ticked. The setting of the player who picks
  the card up now decides.
- **A map received was sometimes refused once** and asked for again: it now goes through the first time.

## For the next versions

- The log notes, each time a guest comes back to the host, how long it was away and how big the world it received
  was. Nothing changes in game: these figures will be used to remove the screen reloads.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- When the host joins a guest on its map, the guest's screen reloads (the whole world is sent again).
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

---

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

---

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

---

# Elin Together « indépendance » 0.26.548

(English below / version anglaise plus bas)

Suite de la 0.26.540. Cette fois une bonne partie est **jouée au banc de test**, à deux joueurs et à **cinq joueurs**
(un hébergeur et quatre invités sur un même PC), pas encore dans une vraie partie. Si cette version se passe mal, la
0.26.540 reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal Nightly). **Tous les joueurs doivent installer
ce même zip, et avoir la même liste de mods.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé

- **L'or et les objets qu'un invité prend dans un coffre, une boutique ou la banque** et qui vont dans sa bourse ou
  dans un sac de son sac n'apparaissaient pas dans son jeu (l'hébergeur, lui, les voyait) : une source des « sacs
  différents ». Vérifié : banque, coffre d'expédition, échanges entre joueurs.
- **Un invité paie sa facture** (impôt ou livraison) en la déposant dans le coffre des impôts : avant, rien ne se
  passait. Vérifié.
- **Nuit commune avec un hébergeur lent** : l'écran de nuit des invités se fermait après quelques secondes sans
  attendre la fin de la nuit. Il attend maintenant. Vérifié à cinq joueurs.
- Écrit et compilé, pas joué : une rune ou une prise posée par un invité ne compte plus deux fois dans son jeu, le
  plein de carburant non plus ; un philtre d'amour donné par un invité garde son effet ; un objet non identifié vendu
  par un invité est identifié chez l'hébergeur aussi.

## Vérifié à cinq joueurs

Connexion, objets posés vus par tous à la même case, une minute de jeu ensemble (les cinq jeux gardent exactement la
même carte), nuit commune (une seule nuit, même date partout, tout le monde reposé), deux joueurs qui partent sur une
autre carte puis reviennent. Pas encore essayé à cinq : combat, donjon, départ de l'hébergeur.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un invité mort qui attend sa réanimation au moment où l'hébergeur quitte la carte pourrait rester mort.
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

# Elin Together "independence" 0.26.548

Follows 0.26.540. This time a good part was **played on the test bench**, with two players and with **five players**
(a host and four guests on one PC), not yet in a real game. If this version goes wrong, 0.26.540 stays online. Built
for Elin **EA 23.352 Patch 1** (Nightly branch). **Every player must install this same zip and have the same list of
mods.** Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed

- **Gold and items a guest takes out of a chest, a shop or the bank** that go into its purse or a bag inside its bag
  did not show up in its own game (the host saw them): one source of "bags differ". Checked: bank, shipping chest,
  trades between players.
- **A guest pays its bill** (tax or delivery) by dropping it in the tax chest: nothing happened before. Checked.
- **Shared night with a slow host**: the guests' night screen closed after a few seconds without waiting for the end
  of the night. It now waits. Checked with five players.
- Written and compiled, not played: a rune or a plug applied by a guest no longer counts twice in its game, nor does a
  refuel; a love potion given by a guest keeps its effect; an unidentified item sold by a guest is identified on the
  host too.

## Checked with five players

Connection, dropped items seen by everyone on the same tile, a minute of play together (the five games keep exactly
the same map), shared night (one night, same date everywhere, everyone rested), two players leaving for another map
and coming back. Not tried with five yet: combat, dungeon, the host leaving.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A dead guest waiting to be revived when the host leaves the map might stay dead.
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

---

# Elin Together « indépendance » 0.26.540

(English below / version anglaise plus bas)

Suite de la 0.26.532, d'après les retours d'une partie jouée avec elle. **Écrit, relu en partie et compilé, pas joué.**
Si cette version se passe mal, la 0.26.532 reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal Nightly).
**Tous les joueurs doivent installer ce même zip, et avoir la même liste de mods.** Faites une copie de vos sauvegardes
avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé

- **Un invité garde ses réglages à chaque changement de carte et à la reconnexion** : fenêtres d'inventaire, de sacs
  et d'aptitudes rouvertes au même endroit ; type de combat automatique ; consignes des compagnons ; tris ; disposition
  de l'écran (mini-carte, widgets, zoom) ; filtre de ramassage automatique ; aptitudes favorites ; suivi de quête.
  Avant, ceux de l'hébergeur les remplaçaient à chaque carte.
- **Bloqué en lisant un livre** : quand l'hébergeur quittait la carte pendant la lecture d'un invité, elle restait figée
  sans pouvoir être annulée. Elle reprend maintenant chez l'invité. Plus aucune activité ne peut rester figée sans
  réponse.
- **Coffre d'expédition de l'hébergeur** quand il joue son propre personnage dans un monde pris sur un dépôt : ses
  objets étaient vendus sans qu'il reçoive l'or ni le rapport. Corrigé, et **l'or qui lui était dû est versé tout seul
  à la première vente du matin**.

## Nouveau

- **Bouton « Join »** sous chaque partie de la liste, depuis l'écran titre.

## Limites connues

- La toute première fois qu'un joueur rejoint un monde, il part des réglages de l'hébergeur ; les siens sont retenus
  ensuite. Le contenu des barres de raccourcis tient d'une carte à l'autre, pas après avoir fermé le jeu.
- Un invité mort qui attend sa réanimation au moment où l'hébergeur quitte la carte pourrait rester mort.
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

# Elin Together "independence" 0.26.540

Follows 0.26.532, from the reports of a game played with it. **Written, partly reviewed and compiled, not played.** If
this version goes wrong, 0.26.532 stays online. Built for Elin **EA 23.352 Patch 1** (Nightly branch). **Every player
must install this same zip and have the same list of mods.** Back up your saves first:
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed

- **A guest keeps its own settings at every map change and on reconnection**: inventory, bag and ability windows
  reopened at the same place; auto combat type; companion orders; sorting; screen layout (minimap, widgets, zoom);
  auto-pickup filter; favourite abilities; quest tracker. Before, the host's replaced them at every map.
- **Stuck while reading a book**: when the host left the map while a guest was reading, the reading stayed frozen and
  could not be cancelled. It now resumes in the guest's game. No task can stay frozen without an answer any more.
- **The host's shipping chest** when it plays its own character in a world taken from a depot: its goods were sold
  without gold or report. Fixed, and **the gold it was owed is paid by itself at the next morning sale**.

## New

- **"Join" button** under each game of the lobby list, from the title screen.

## Known limits

- The very first time a player joins a world, it starts from the host's settings; its own are kept afterwards. Hotbar
  content holds from one map to the next, not after closing the game.
- A dead guest waiting to be revived when the host leaves the map might stay dead.
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

---

# Elin Together « indépendance » 0.26.510

(English below / version anglaise plus bas)

## Nouveau dans la 0.26.510 (corrections après une vraie soirée à trois joueurs et plus)

- **Les invités ne sont plus téléportés sur l'hébergeur.** Quand l'hébergeur part ou revient, chaque invité garde sa
  case. Un invité qui entre sur une carte arrive par l'entrée, et jamais dans l'eau sur la carte du monde.
- **Le temps d'un autre joueur ne vous coûte plus rien.** Quand un joueur voyage ou dort, la date avance pour tous, mais
  vous n'avez pas plus faim, votre nourriture ne pourrit pas, vos états et vos délais de quête ne bougent pas.
- **Sommeil** : seuls les familiers du dormeur le rejoignent ; un invité qui dort seul ne voit plus sa carte rechargée.
- **Musique** : le personnage d'un autre joueur ne jette plus de pièces au musicien.
- **Ancien personnage** : un personnage de joueur que personne ne joue ne reste plus sur la carte à se battre.
- **Cave** : une cave où se trouve un joueur n'est plus refaite quand un autre y entre.
- **Coupure de liaison** : l'invité revient tout seul dans la partie (essais pendant 3 minutes). Plus d'écran « Who do you
  want to play? » à chaque connexion.
- **Hébergeur** : le monde est sauvegardé tout seul toutes les 2 minutes quand un autre joueur est là ; un monde déjà
  partagé ouvre sa partie tout seul au chargement (amis Steam).
- **Dépôt GitHub ou dossier** : si quelqu'un héberge déjà le monde, le deuxième joueur est envoyé dans sa partie
  (bouton « Join »), au lieu d'ouvrir une copie.
- **Chargement rapide** : il est arrêté dans une partie à plusieurs (il ouvrait une fenêtre d'erreur chez l'invité).
- **Pas encore corrigé** : la banque et le coffre d'expédition d'un invité seul sur une autre carte que l'hébergeur (ce
  qu'il dépose va chez l'hébergeur mais sa fenêtre se rouvre vide : déposez sur la carte de l'hébergeur) ; les objets de
  la barre d'outils rangés par le rangement automatique ; deux factures au lieu d'une ; recette et grimoire propres à
  l'invité au réveil ; lenteurs à plusieurs invités.
- Testé au banc sur un PC : à trois fenêtres, téléportations 17/17 et temps 25/25 ; à deux fenêtres, les suites
  habituelles. **Les corrections n'ont pas encore été rejouées entre vrais PC.**

**New in 0.26.510 (fixes after a real evening with three players and more).** Guests are no longer moved onto the host
when the host leaves or comes back; a guest enters a map by its entrance, never in water on the world map. Time passed by
another player costs you nothing (no hunger, no rotten food, no condition or quest deadline change). Only the sleeper's
own pets join it. Another player's character no longer throws coins at a musician. A player character nobody plays no
longer stays on the map. A cave with a player in it is not rebuilt when another enters. A guest whose link drops comes
back by itself; no character question at each connection. The host's world saves itself every 2 minutes while someone
else plays; a shared world opens its session by itself. With a save depot, the second player is sent into the game of
the one already hosting. Quick load is stopped in a shared game. Not fixed yet: bank and shipping chest of a guest alone
on another map than the host (deposit on the host's map), auto-dump taking toolbar items, two bills instead of one.
Bench-tested with three windows on one PC, not replayed on real PCs yet.

## Dans la 0.26.506

- **Le jeu sait tout seul quel personnage est à qui, sans jamais rien demander.** Celui qui reprend un monde (dépôt)
  joue son propre personnage ; celui de l'ancien hébergeur l'attend et lui revient quand il rejoint. Cela marche aussi
  pour un monde d'avant cette version. Un joueur qui n'a encore aucun personnage dans le monde passe par l'écran de
  création du jeu, puis joue le sien. Une copie de secours est faite avant chaque échange.
- **Corrigé : la 0.26.494 pouvait se tromper de personnage** en reprenant un monde (elle lisait les données de la partie
  précédente). Ne reprenez pas un monde avec la 0.26.493 ou la 0.26.494.
- **Dix petites gênes en moins** : boutons du dépôt qui débordaient, messages affichés en code brut ou faux à la
  connexion, textes japonais restés en anglais, « Add an item » muet dans l'échange, une boîte à valider en moins.
- **Limite connue**, seulement pour un monde d'avant et à trois joueurs ou plus : un nouveau venu arrivé avant l'ancien
  hébergeur recevrait son personnage. À deux joueurs, ce cas n'existe pas.
- **Pas encore dans cette version** (écrit, en test) : le retour automatique après une coupure, la fin de l'écran
  « Who do you want to play? » à chaque connexion.
- Testé au banc (deux fenêtres sur un PC) : reprise du monde dans tous les cas 33/33, dépôt GitHub 36/36, quinze autres
  suites vertes. **Jamais joué à deux vrais PC.** Rouges connus, intermittents : après un duel les points de vie du
  perdant ne sont pas toujours remis au maximum dans son jeu ; la laisse du compagnon d'un invité ne tire pas toujours.

**New in 0.26.506 (it replaces 0.26.494).** The game knows by itself whose character is whose, and never asks: the
player who takes a world over plays its own character, the former host's waits and is its own again when it joins;
worlds made before this version are covered; a player with no character yet makes one on the game's creation screen. A
backup is made before any exchange. Fixed: 0.26.494 could pick the wrong character when a world was taken over (do not
take a world over with 0.26.493 or 0.26.494). Ten small frictions removed. Known limit, old worlds with three players or
more only: a newcomer who arrives before the former host would get its character. Not in this version yet (written, in
test): automatic reconnection, no character question at each connection. Bench-tested with two windows on one PC, never
played on two real PCs.

## Pour qui

Pour ceux qui jouent déjà avec la 0.26.463, et pour ceux qui veulent essayer à deux, ou plus, un Elin où l'invité
joue comme un joueur solo. **Tous les joueurs doivent installer le même zip** : cette version ne se connecte ni à
la version du Workshop, ni à une autre version du fork. Elle est compilée pour Elin EA 23.352 (la dernière version
« nightly » d'Elin chez Steam).

**État : expérimental.** Tout est testé sur un seul PC avec deux fenêtres du jeu (suites de tests en jeu). Presque
rien de ce qui est nouveau dans cette version n'a été joué entre deux vrais PC. Faites une copie de vos sauvegardes
avant (`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`).

## Ce qui est nouveau

- **Construire dans la base, côté invité.** Un invité utilise le mode construction comme l'host : sols, murs,
  meubles du menu, miner, creuser, couper, zones, outil de terrain. Ce que l'un construit se voit chez l'autre tout
  de suite. Case côté host : « GuestBuild » (cochée).
- **Gérer la base, côté invité.** Recherche, foyer et politiques marchaient déjà ; maintenant aussi la servante, le
  type d'un résident (résident ou bétail), la réserve, le rappel et le renvoi. Les réglages de coffre (priorité,
  filtre…) passent dans les deux sens. Case côté host : « seul l'host gère la base » (HostManagesBase, décochée).
- **Duels entre joueurs.** Dans le menu sur le personnage d'un autre joueur : « Challenge to a duel ». L'autre
  répond par une boîte oui/non, puis compte à rebours. Personne ne meurt, les deux sont soignés à la fin, rien n'est
  perdu. Case côté host : « Duels » (cochée). Pas encore : l'arène, le pari, le bouton abandonner.
- **Un joueur ne peut plus tuer un autre joueur hors duel.** Case côté host : « PlayerKill » (décochée).
- **Pour l'invité, comme en solo** : ressusciter un compagnon chez le barman ; laisser un objet à copier chez Kettle
  et un grimoire chez Demitas ; duel d'autel au même résultat pour tous ; outils et fouets (clé à molette, etc.) qui
  agissent sur le monde de l'host ; prière sans dieu qui ne soigne plus ; jours et heures qui passent ; prix
  d'expédition ; carte à gratter du casino.
- **Garder le monde sur GitHub.** Un dépôt GitHub privé peut garder le monde partagé (troisième sorte de dépôt,
  réglage « github:proprietaire/depot », une seule clé). Fermer le jeu pendant un envoi attend maintenant la fin et
  rend le monde (corrigé ce soir).
- **Monde qui change de main (dépôt).** Celui qui reprend le monde joue SON personnage, pas celui de l'ancien host ;
  l'ancien host retrouve le sien quand il rejoint. Limite : un monde hébergé pour la dernière fois avec une ancienne
  version ne sait pas à qui est son personnage : l'ancien host doit l'héberger une fois avec cette version avant
  qu'un autre le reprenne.

## Ce qui n'est pas encore testé en vrai

Testé à deux fenêtres sur un seul PC. **Presque rien de ce qui est nouveau n'a été joué entre deux vrais PC.** Pas
joué du tout :

- construction : objet du stock ou du sac posé par le menu, pont, glisser sur plusieurs cases, creuser, mode rampe,
  la case décochée, une carte tenue par un invité ; plans de construction et mode toit : refusés avec un message ;
- réglages de coffre : la boîte du filtre, le collage, les boutons de rangement automatique ;
- duels : deux vrais PC, sorts et flèches, trois joueurs ;
- un joueur qui tue un joueur : saignement, poison, feu, condamnation à mort, sorts et projectiles ;
- résurrection par parchemin ou sort ; tentes et fouets « passe-temps » et « métier » ; prix d'expédition ; carte à
  gratter ;
- dépôt GitHub : le vrai GitHub depuis le jeu, deux PC, la clé expirée, un dépôt vide ; monde qui change de main : deux
  PC ;
- la base gérée par un invité : rien joué en vrai.

Limites connues : le temps du monde suit encore l'host ; la défense à deux n'existe pas ; quelques accidents rares
(deux joueurs qui construisent sur la même case, monture en double au retour d'un voyage). Liste complète :
`dev/DOCUMENTATION.md`.

## À essayer à deux

1. Un invité qui construit (sol, mur, meuble, miner, zone) : l'host le voit-il tout de suite ? Et l'inverse.
2. Un invité qui gère la base : servante, résident / bétail, réserve, rappel, renvoi, réglage d'un coffre.
3. Un duel dans les deux sens : accepter, refuser, quitter pendant le duel.
4. Le dépôt GitHub avec une vraie clé, et un monde repris par un autre joueur : chacun retrouve-t-il son personnage ?
5. Ressusciter un compagnon chez le barman, copie chez Kettle, outils et fouets, carte à gratter.

Si quelque chose ne va pas : [les tickets](https://github.com/devmarcpro/elin-together/issues), avec les fichiers
`Player.log` et `ElinMP/Logs/Session_<date>.log` des deux joueurs.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly** (compilé pour EA 23.352). Chacun télécharge `ElinTogether-independance-0.26.506.zip`, le décompresse et
lance `Installer.bat` (`Desinstaller.bat` fait l'inverse). **Tous les joueurs doivent avoir exactement ce zip.**
`LISEZMOI.txt` dans le zip explique le reste. Pour héberger : lancer Elin par Steam, charger une partie qui a un
terrain revendiqué, puis Échap → Mods → Elin Together.

---

# Elin Together "independence" 0.26.506

## Who it is for

For those already playing with 0.26.463, and for those who want to try, with one or more friends, an Elin where the
guest plays like a solo player. **Every player must install the same zip**: this version does not connect to the
Workshop version, nor to any other version of the fork. It is built for Elin EA 23.352 (Steam's latest "nightly"
Elin).

**Status: experimental.** Everything is tested on one PC with two game windows (in-game test suites). Almost nothing
that is new in this version has been played between two real PCs. Back up your saves first
(`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`).

## What is new

- **Building in the base, as a guest.** A guest uses build mode like the host: floors, walls, menu furniture,
  mining, digging, cutting, zones, the terrain tool. What one builds is seen by the other at once. Host checkbox:
  "GuestBuild" (checked).
- **Managing the base, as a guest.** Research, hearth and policies already worked; now also the maid, a resident's
  type (resident or livestock), the reserve, recall and sending away. Chest settings (priority, filter...) go both
  ways. Host checkbox: "only the host manages the base" (HostManagesBase, unchecked).
- **Duels between players.** In the menu on another player's character: "Challenge to a duel". The other answers a
  yes/no box, then a countdown. Nobody dies, both are healed at the end, nothing is lost. Host checkbox: "Duels"
  (checked). Not yet: the arena, betting, the give-up button.
- **A player can no longer kill another player outside a duel.** Host checkbox: "PlayerKill" (unchecked).
- **For the guest, as in solo**: bringing a companion back at the barman's; leaving an item to copy at Kettle's and
  a spellbook at Demitas'; the altar duel with the same result for everyone; tools and whips (wrench, etc.) that act
  on the host's world; a prayer with no god that no longer heals; days and hours that pass; shipping prices; the
  casino's scratch card.
- **Keeping the world on GitHub.** A private GitHub repository can keep the shared world (third kind of depot,
  setting "github:owner/repository", one key). Closing the game during an upload now waits for it to finish and
  frees the world (fixed tonight).
- **A world that changes hands (depot).** Whoever takes the world over plays THEIR OWN character, not the former
  host's; the former host gets theirs back when joining. Limit: a world last hosted with an older version does not
  know whose character is whose: the former host must host it once with this version before anyone else takes it
  over.

## What has not been tested for real yet

Tested with two windows on one PC. **Almost nothing that is new has been played between two real PCs.** Not played
at all:

- building: a stock or bag item placed from the menu, bridges, dragging over several tiles, digging, ramp mode, the
  checkbox unchecked, a map held by a guest; blueprints and roof mode are refused with a message;
- chest settings: the filter box, pasting, the auto-dump buttons;
- duels: two real PCs, spells and arrows, three players;
- a player killing a player: bleeding, poison, fire, the death sentence, spells and missiles;
- bringing back a companion with a scroll or spell; tents and the "hobby" and "work" whips; shipping prices; the
  scratch card;
- the GitHub depot: the real GitHub from inside the game, two PCs, an expired key, an empty repository; a world that
  changes hands: two PCs;
- the base managed by a guest: nothing played for real.

Known limits: the world's clock still follows the host; defense quests for two do not exist; a few rare accidents
(two players building on the same tile, a mount existing twice after a trip). Full list: `dev/DOCUMENTATION.md` (in
French).

## To try with two players

1. A guest building (floor, wall, furniture, mining, zone): does the host see it at once? And the other way round.
2. A guest managing the base: maid, resident / livestock, reserve, recall, sending away, a chest's settings.
3. A duel both ways: accept, refuse, leave during the duel.
4. The GitHub depot with a real key, and a world taken over by another player: does each get their own character?
5. Bringing a companion back at the barman's, copying at Kettle's, tools and whips, the scratch card.

If something goes wrong: [the issues](https://github.com/devmarcpro/elin-together/issues), with both players'
`Player.log` and `ElinMP/Logs/Session_<date>.log`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the
**Nightly** branch (built for EA 23.352). Each player downloads `ElinTogether-independance-0.26.506.zip`, unzips it
and runs `Installer.bat` (`Desinstaller.bat` switches back). **Every player must have exactly this zip.** The
installer and its notes (`LISEZMOI.txt` in the zip) are in French. To host: launch Elin through Steam, load a save
that has a claimed land, then Esc → Mods → Elin Together.

---

# Elin Together « indépendance » 0.26.463

(English below / version anglaise plus bas)

## Pour qui

Pour ceux qui jouent déjà avec la 0.26.442, et pour ceux qui veulent essayer à deux, ou plus, un Elin où l'invité
joue comme un joueur solo. **Tous les joueurs doivent installer le même zip** : cette version ne se connecte ni à
la version du Workshop, ni à une autre version du fork. Elle est compilée pour la nouvelle version d'Elin
(EA 23.352).

**État : expérimental.** Tout est testé sur un seul PC avec deux fenêtres du jeu (suites de tests en jeu). Très peu
de chose a été joué entre deux PC par Steam, et rien de ce qui est nouveau dans cette version n'a été essayé à deux
PC. Faites une copie de vos sauvegardes avant (`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`).

## Ce qui est nouveau

- **Versions d'Elin différentes : plus de mur.** Seule la version du MOD doit être la même pour tous. Deux joueurs
  qui n'ont pas la même version d'Elin peuvent se connecter ; ils sont prévenus par un avertissement. Une case côté
  host (« Require the same Elin version », décochée par défaut) redemande la même version d'Elin. Testé en connexion
  locale seulement ; par le salon Steam : pas joué.
- **Base réglée par un invité.** La recherche et les compétences du foyer sont de vraies demandes à l'host : il
  vérifie, paie une fois, et tout le monde voit le résultat (la 0.26.442 refusait avec un message). Les politiques,
  les lits, les étiquettes de vente, les notes, le nom de la base, de la faction et d'un téléporteur réglés par un
  joueur sont vus par l'autre, dans les deux sens.
- **« Ne pas vagabonder » propre à chaque joueur**, comme « garder ses distances » : c'est le réglage du joueur du
  compagnon, pas celui de l'host.
- **Quêtes à donjon à deux quand c'est l'invité qui a la quête** : en plus de « subjuguer », les quêtes de **récolte**
  et de **musique** se jouent à deux. La défense reste à faire seul.

## Ce qui est corrigé

- Un objet offert par un invité, pris dans une pile, arrive bien chez l'host (avant : le don n'avait aucun effet).
- Une monture déjà prise est refusée à un second cavalier.
- Un invité qui taille un rondin à la hache obtient ses planches, et le rondin est usé.
- La prière d'un invité soigne aussi ses compagnons.
- La nourriture dans le sac d'un invité vieillit comme celle de l'host.

## Ce qui n'est pas encore testé en vrai

Testé à deux fenêtres sur un seul PC. **Rien de ce qui est nouveau n'a été joué entre deux PC.** Pas joué du tout :

- les versions d'Elin différentes par le salon Steam (seule la connexion locale a été essayée) ;
- le nom de la faction réglé par un invité ; le fait de ne pas courir après un ennemi hors de vue (« ne pas
  vagabonder » lui-même) ; le score d'un concert dans une quête de musique jouée par l'host ;
- les quêtes à donjon à deux : les tests prennent la quête et sortent par des appels directs au code du jeu, pas par
  le dialogue ni en marchant jusqu'au bord ; pas de test à trois joueurs ni de coupure de connexion dans la zone ;
- la quête de récolte prise par l'invité : un test a échoué une fois sur Elin 23.352 (ce que l'invité livre n'a pas
  compté), pas encore rejoué ; à surveiller ;
- la carte au trésor d'un invité sur la carte du monde avec l'host ;
- noyade en eau profonde, ticket d'hôtesse, fenêtres d'alias / de retour du vide / de caisse de récolte, karma d'un
  visiteur chez un invité, tri du sac, achat au même instant ;
- vol à la tire, investir dans une ville, pinceau, runes d'arme à distance ;
- le temps que met l'écran d'un invité à se recharger quand l'host revient (pas mesuré entre deux PC).

Limites connues : le temps du monde suit encore l'host ; la défense à deux n'existe pas ; la servante, le type et
la mise en réserve d'un résident, et les réglages des coffres, faits par un invité, ne valent que sur son écran ; le
mode construction d'un invité (sols, murs, marques miner / couper) ne se fait que sur son écran : pour l'instant,
c'est l'host qui doit construire la base ; quelques accidents rares (deux joueurs qui construisent sur la même case,
monture en double au retour d'un voyage). Liste complète : `dev/DOCUMENTATION.md`.

## À essayer à deux

1. Un deuxième joueur qui rejoint par Steam ; l'hébergeur qui part (un autre reprend) ; le mode avec Elin entre deux
   PC ; par Internet avec un mot de passe.
2. Quêtes à donjon à deux, dans les deux sens : l'host prend une quête, l'invité répond Oui à la boîte, puis une
   autre fois Non ; l'invité prend une quête « subjuguer », « récolte » ou « musique », l'host répond Oui, puis une
   autre fois Non.
3. L'host revient sur une carte tenue par l'invité : combien de temps l'écran de l'invité met-il à se recharger ?
   (à chronométrer)
4. La carte au trésor, lue puis creusée par l'invité sur la carte du monde, avec l'host.
5. Ce qui n'a jamais été joué : un visiteur chez un invité (les gardes le voient-ils comme criminel après un vol ?),
   le tri du sac, « déjà vendu » quand deux joueurs achètent au même instant, le message qui nomme l'host avant le
   rechargement, le ticket d'hôtesse, les fenêtres d'alias / de retour du vide / de caisse de récolte, l'eau
   profonde, le vol à la tire, investir dans une ville, le pinceau, les runes d'arme à distance, le concert d'une
   quête de musique.
6. L'invité règle la base : recherche et compétences du foyer (payé une fois, résultat vu chez l'host), politiques,
   lit, étiquette de vente, note, nom de la base et d'un téléporteur : l'autre joueur doit le voir.
7. Un échange : un objet équipé, un sac plein, un objet qu'on ne peut pas lâcher.
8. Un invité qui offre un objet pris dans une pile (le don doit arriver chez l'host) ; une monture déjà prise.
9. Deux joueurs sur une version d'Elin différente : l'avertissement, la case de l'host, et un MOD de version
   différente qui doit rester refusé.

Si quelque chose ne va pas : [les tickets](https://github.com/devmarcpro/elin-together/issues), avec les fichiers
`Player.log` et `ElinMP/Logs/Session_<date>.log` des deux joueurs.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly** (compilé pour EA 23.352). Chacun télécharge `ElinTogether-independance-0.26.463.zip`, le décompresse et
lance `Installer.bat` (`Desinstaller.bat` fait l'inverse). **Tous les joueurs doivent avoir exactement ce zip.**
Une version d'Elin un peu différente entre joueurs n'empêche plus de se connecter. `LISEZMOI.txt` dans le zip
explique le reste. Pour héberger : lancer Elin par Steam, charger une partie qui a un terrain revendiqué, puis
Échap → Mods → Elin Together.

---

# Elin Together "independence" 0.26.463

## Who it is for

For those already playing with 0.26.442, and for those who want to try, with one or more friends, an Elin where the
guest plays like a solo player. **Every player must install the same zip**: this version does not connect to the
Workshop version, nor to any other version of the fork. It is built for the new version of Elin (EA 23.352).

**Status: experimental.** Everything is tested on one PC with two game windows (in-game test suites). Very little
has been played between two PCs over Steam, and nothing that is new in this version has been tried on two PCs. Back
up your saves first (`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`).

## What is new

- **Different Elin versions: no more wall.** Only the MOD's version must be the same for everyone. Two players who
  do not have the same version of Elin can connect; they are told by a warning. A checkbox on the host's side
  ("Require the same Elin version", unchecked by default) asks for the same Elin version again. Tested on a local
  connection only; through the Steam lobby: not played.
- **Home base settings changed by a guest.** Research and hearth skills are real requests to the host: it checks,
  pays once, and everyone sees the result (0.26.442 refused with a message). Policies, beds, sale tags, notes, the
  name of the base, of the faction and of a teleporter set by one player are seen by the other, both ways.
- **"Don't wander" is each player's own**, like "keep distance": it is the setting of the companion's player, not
  the host's.
- **Dungeon quests for two when the guest took the quest**: besides "subdue", **harvest** and **music** quests can
  be played by two. Defense quests are still settled alone.

## What is fixed

- An item given by a guest, taken out of a stack, now reaches the host (before: the gift had no effect).
- A mount that already carries someone is refused to a second rider.
- A guest chopping a log with an axe gets its planks, and the log is used up.
- A guest's prayer heals its companions too.
- Food in a guest's bag goes off like the host's.

## What has not been tested for real yet

Tested with two windows on one PC. **Nothing that is new has been played between two PCs.** Not played at all:

- different Elin versions through the Steam lobby (only the local connection was tried);
- the faction name set by a guest; not chasing an enemy out of sight ("don't wander" itself); the score of a
  concert in a music quest played by the host;
- dungeon quests for two: the tests take the quest and leave through direct calls to the game's code, not through
  the dialog or by walking to the edge; no three-player test, no connection loss inside the zone;
- the harvest quest taken by the guest: one test failed once on Elin 23.352 (what the guest delivered did not
  count), not replayed yet; keep an eye on it;
- a guest's treasure map on the world map with the host;
- drowning in deep water, hostess ticket, alias / void return / harvest chest windows, a visitor's karma on a
  guest's map, bag sorting, two purchases at the same instant;
- pickpocketing, investing in a town, the brush, ranged-weapon runes;
- how long a guest's screen takes to reload when the host returns (not measured between two PCs).

Known limits: the world's clock still follows the host; defense quests for two do not exist; the maid, a resident's
type and reserve, and chest settings, changed by a guest, only apply on its own screen; a guest's build mode (floors,
walls, mine / chop marks) only works on its own screen: for now, the host has to build the base; a few rare
accidents (two players building on the same tile, a mount existing twice after a trip). Full list:
`dev/DOCUMENTATION.md` (in French).

## To try with two players

1. A second player joining over Steam; the host leaving (another takes over); the mode with Elin between two PCs;
   over the Internet with a password.
2. Dungeon quests for two, both ways: the host takes a quest, the guest answers Yes to the box, then No another
   time; the guest takes a "subdue", "harvest" or "music" quest, the host answers Yes, then No another time.
3. The host returns to a map held by the guest: how long does the guest's screen take to reload? (to be timed)
4. The treasure map, read then dug by the guest on the world map, with the host.
5. What has never been played: a visitor on a guest's map (do the guards see it as a criminal after a theft?), bag
   sorting, "already sold" when two players buy at the same instant, the message that names the host before the
   reload, hostess ticket, alias / void return / harvest chest windows, deep water, pickpocketing, investing in a
   town, the brush, ranged-weapon runes, the concert of a music quest.
6. The guest changes the base: research and hearth skills (paid once, result seen by the host), policies, bed, sale
   tag, note, name of the base and of a teleporter: the other player must see it.
7. A trade: an equipped item, a full bag, an item that cannot be dropped.
8. A guest giving an item taken out of a stack (the gift must reach the host); a mount that is already taken.
9. Two players on different Elin versions: the warning, the host's checkbox, and a MOD of a different version that
   must still be refused.

If something goes wrong: [the issues](https://github.com/devmarcpro/elin-together/issues), with both players'
`Player.log` and `ElinMP/Logs/Session_<date>.log`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the
**Nightly** branch (built for EA 23.352). Each player downloads `ElinTogether-independance-0.26.463.zip`, unzips it
and runs `Installer.bat` (`Desinstaller.bat` switches back). **Every player must have exactly this zip.** A slightly
different Elin version between players no longer prevents connecting. The installer and its notes (`LISEZMOI.txt` in
the zip) are in French. To host: launch Elin through Steam, load a save that has a claimed land, then Esc → Mods →
Elin Together.
