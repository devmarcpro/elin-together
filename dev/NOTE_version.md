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
