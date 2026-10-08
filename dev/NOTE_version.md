# Elin Together « indépendance » 0.26.608

(English below / version anglaise plus bas)

Suite de la 0.26.605, avec **une nouvelle option pour les parties avec mods**. Elle est **écrite et compilée, pas
jouée**, comme les deux corrections de la 0.26.605 qu'elle contient aussi. Si cette version se passe mal, la 0.26.597
reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal Nightly). **Tous les joueurs doivent installer ce même
zip.** Faites une copie de vos sauvegardes avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Nouveau (pas joué)

- **Garder les mods de la partie, pour ne plus voir Elin se fermer à chaque soirée.** Depuis la 0.26.590, quand il vous
  manque des mods de la partie, Elin se ferme et se relance avec ces mods ; comme votre propre liste revient à chaque
  lancement, cela recommençait à la première connexion de chaque lancement (des testeurs l'ont décrit comme « le jeu
  plante à la première connexion, puis entre à la deuxième »). Nouvelle case, décochée au départ, onglet « Client
  Settings » : **« Keep the mods of the game (subscribe on the Workshop) »**.
  - Cochée : votre compte Steam s'abonne aux mods de la partie et ils restent allumés dans votre liste. Elin se relance
    encore **une fois**, puis plus jamais pour cette partie, même après avoir fermé le jeu.
  - Pour revenir en arrière : désabonnez-vous sur le Workshop, ou éteignez ces mods dans le Mod Viewer.
  - Décochée : comme avant.
- Le message affiché après une relance dit maintenant comment l'éviter la fois suivante.

## Corrigé dans la 0.26.605 (pas joué)

- Impossible de rejoindre une partie avec un personnage monté.
- Une erreur à chaque dialogue avec un personnage, chez un joueur qui a un mod de langue, après la relance d'Elin.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
- Quand l'hébergeur et un invité se retrouvent sur une carte, l'écran de l'invité recharge (le monde entier est renvoyé), sauf si l'hébergeur coche la case « No world reload when the host and a player meet again ».
- Quand l'hébergeur part ou plante, aucun invité ne reprend le monde tout seul.
- « Keep the mods of the game » : un mod retiré de la partie plus tard reste abonné chez vous ; les mods que vous avez
  en trop ne sont pas touchés.

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

# Elin Together "independence" 0.26.608

Follows 0.26.605, with **a new option for games with mods**. It is **written and compiled, not played**, like the two
fixes of 0.26.605 that it also holds. If this version goes wrong, 0.26.597 stays online. Built for Elin **EA 23.352
Patch 1** (Nightly branch). **Every player must install this same zip.** Back up your saves first:
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## New (not played)

- **Keep the mods of the game, so Elin no longer closes at every evening.** Since 0.26.590, when mods of the game are
  missing, Elin closes and restarts with them; as your own list comes back at every start, this happened again at the
  first join of every start (testers described it as "the game crashes on the first join, then connects on the
  second"). New checkbox, unticked at first, "Client Settings" tab: **"Keep the mods of the game (subscribe on the
  Workshop)"**.
  - Ticked: your Steam account subscribes to the mods of the game and they stay on in your list. Elin restarts **once**
    more, then never again for that game, even after closing Elin.
  - To undo: unsubscribe on the Workshop, or switch these mods off in the Mod Viewer.
  - Unticked: as before.
- The message shown after a restart now says how to skip it next time.

## Fixed in 0.26.605 (not played)

- A mounted character could not join a game.
- An error at every talk to a character, for a player with a language mod, after Elin restarted.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- When the host and a guest meet on a map, the guest's screen reloads (the whole world is sent again), unless the host ticks "No world reload when the host and a player meet again".
- When the host leaves or crashes, no guest takes the world over by itself.
- "Keep the mods of the game": a mod removed from the game later stays subscribed on your side; the extra mods you
  have are not touched.

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
