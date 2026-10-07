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
