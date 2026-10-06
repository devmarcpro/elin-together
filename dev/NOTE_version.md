# Elin Together « indépendance » 0.26.532

(English below / version anglaise plus bas)

Corrections tirées des journaux d'une vraie partie à quatre joueurs. **Peu testée** : deux jeux se connectent et trois
tests en jeu ont tourné (mannequin 47/50, placement des joueurs 24/27) ; le reste est écrit, relu et compilé, pas joué.
La correction principale ne peut pas être vue par mes tests : elle ne concerne que la version publiée. Si cette version
se passe mal, la 0.26.510 reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal Nightly). **Tous les joueurs
doivent installer ce même zip, et avoir la même liste de mods.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## La cause principale des désynchronisations

- **Le mod se débranchait en pleine partie.** Dès qu'une carte partagée entre deux joueurs se fermait, le mod retirait
  toutes ses modifications du jeu de l'invité, qui restait pourtant connecté : il n'envoyait plus rien, n'appliquait
  presque plus rien, changeait de carte sans prévenir. D'où les joueurs qui ne se voient plus, les personnages en
  moins, les expulsions « invalid zone ». Présent depuis que les cartes partagées existent, dans la version publiée
  seulement.

## Corrigé d'après les journaux

- **Un joueur qui arrive est toujours posé sur la carte** (il pouvait rester sur son écran de chargement).
- **L'hébergeur qui dort ne charge plus ses bases** quand des joueurs sont ailleurs.
- **Un invité sur la carte du monde n'est plus rappelé** chaque fois que l'hébergeur y passe (monde entier rechargé).
- **Plus d'expulsion « invalid zone »** : le joueur revient tout seul. **Plus d'expulsion « invalid source »** de la
  carte d'un autre invité.
- **L'hébergeur n'attend plus sans fin** devant une carte qu'un invité ne tient pas.
- **Récolte et coupe de bois d'un invité** annulées par l'hébergeur (un outil changé en marchant était perdu).
- **Mannequin d'entraînement** pour un invité ; **peinture** et activités d'autres mods ; un invité peut toujours
  arrêter une activité.
- **Joueurs invisibles** après un départ et un retour ; affaires de départ d'un nouveau joueur ; sacs des autres
  joueurs qui dérivaient.
- **Détecteur d'écart** : il ne signale plus les sacs en continu, nomme les personnages et objets qui diffèrent, et
  ne recharge la carte que si cela peut réparer.

## Aussi dans cette version

- Meuble déplacé par un invité : hauteur et pose libre gardées.
- Banque : un objet repris pendant une coupure retourne en banque ; dépôts et retraits d'or affichés pour tous.
- Un invité seul ailleurs peut payer une facture. Impôt sur la renommée la plus haute des joueurs connectés (case
  « Tax on the most famous player »).
- Passage d'une carte entre invités : la copie de celui qui part fait foi.
- Copie du monde chez les invités : disponible, **décochée par défaut** (« The other players keep a copy of the world »).

## En cas de problème pendant une partie

- L'hébergeur décoche la case en cause (Échap → Mods → Elin Together → Server Setting).
- Un joueur désynchronisé tape `emp.reconnect_self` dans la console.
- Envoyez les journaux de chacun : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Pas encore fait

- Quand l'hébergeur part ou plante, aucun invité ne reprend le monde tout seul.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
- Le contenu d'un coffre peut rester différent d'un jeu à l'autre.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly**. Chacun télécharge `ElinTogether-independance.zip` (ci-dessous), le décompresse et lance `Installer.bat`
(`Desinstaller.bat` fait l'inverse). `LISEZMOI.txt` dans le zip explique le reste.

---

# Elin Together "independence" 0.26.532

Fixes drawn from the logs of a real game with four players. **Lightly tested**: two games connect and three in-game
tests ran (training dummy 47/50, player placement 24/27); the rest is written, reviewed and compiled, not played. The
main fix cannot be seen by my tests: it only concerns the published build. If this version goes wrong, 0.26.510 stays
online. Built for Elin **EA 23.352 Patch 1** (Nightly branch). **Every player must install this same zip and have the
same list of mods.** Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## The main cause of the desyncs

- **The mod unplugged itself in the middle of a game.** As soon as a map shared between two players closed, the mod
  removed all its patches from the guest's game, which stayed connected: it sent nothing, applied almost nothing,
  changed map without telling anyone. Hence players who no longer see each other, missing characters, "invalid zone"
  kicks. There since shared maps exist, in the published build only.

## Fixed from the logs

- **A joining player is always put on the map** (it could stay on its loading screen).
- **A sleeping host no longer loads its bases** while players are elsewhere.
- **A guest on the world map is no longer pulled back** every time the host steps on it (whole world reloaded).
- **No more "invalid zone" kick**: the player comes back by itself. **No more "invalid source" kick** from another
  guest's map.
- **The host no longer waits for ever** at a map a guest does not hold.
- **A guest's harvesting and wood chopping** cancelled by the host (a tool changed while walking was lost).
- **Training dummy** for a guest; **painting** and tasks of other mods; a guest can always stop a task.
- **Invisible players** after leaving and coming back; a new player's starting items; other players' bags drifting.
- **Desync detector**: no longer reports bags all the time, names the characters and items that differ, and only
  reloads the map when that can repair.

## Also in this version

- Furniture moved by a guest keeps its height and free pose.
- Bank: an item taken during a link loss goes back to the bank; gold deposits and withdrawals told to all.
- A guest alone elsewhere can pay a bill. Tax on the highest fame among connected players (checkbox "Tax on the most
  famous player").
- A map handed from a guest to a guest: the copy of the one who leaves is the reference.
- Guests keep a copy of the world: available, **unchecked by default** ("The other players keep a copy of the world").

## If something goes wrong during a game

- The host unticks the checkbox (Esc → Mods → Elin Together → Server Setting).
- A desynced player types `emp.reconnect_self` in the console.
- Send everyone's logs: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`.

## Not done yet

- When the host leaves or crashes, no guest takes the world over by itself.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- A chest's content may stay different between games.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the **Nightly**
branch. Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French.
