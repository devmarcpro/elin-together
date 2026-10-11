# Elin Together « indépendance » 0.26.691

(English below / version anglaise plus bas)

Suite de la 0.26.678 : **trois limites connues en moins** et **deux différences entre l'hébergeur et les invités
corrigées**. Joué au banc de test (deux fenêtres sur un PC, une série à trois), rien encore entre deux PC. Si cette
version se passe mal, la 0.26.678 reste en ligne. Compilé pour Elin **EA 23.355**.
**Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Changement de réglage

- **Retrouver l'hébergeur sans recharger le monde** : la case « No world reload when the host and a player meet
  again » est maintenant **cochée d'office** (et allumée une fois chez les hébergeurs qui ont déjà le mod). Quand
  l'hébergeur arrive sur la carte d'un joueur, ou l'inverse, l'écran de ce joueur ne recharge plus tout le monde. Au
  moindre doute le mod recharge comme avant. Si cela se passe mal chez vous, l'hébergeur peut décocher la case : son
  choix reste.

## Corrigé (joué au banc)

- **Service payé dans un dialogue** (taverne, etc.) : un invité payait dans le dialogue, puis une seconde fois à la
  fin. Il ne paie plus qu'une fois.
- **Renvoyer un habitant qui porte un artefact de dieu** : demandé par un invité, l'artefact allait à l'hébergeur. Il
  va à celui qui renvoie.
- **Nuit « à soi »** : un joueur pouvait être frappé, voire tué, pendant les quelques secondes de sa nuit. Il ne
  prend plus de coups tant que sa nuit se joue, comme en solo où le jeu est figé.
- **L'hébergeur qui dort seul** faisait avancer la date de 40 minutes ; une dizaine maintenant.

## Signalé, pas reproduit

- **Monture ou parasite qui disparaît en rejoignant l'hébergeur** : corrigé depuis la 0.26.652. Rejoué ici dans tous
  les sens (l'invité revient, l'hébergeur le rejoint, ils rentrent ensemble, coupure puis retour ; monture, parasite,
  les deux) sans le revoir. Si cela vous arrive encore avec cette version, envoyez le fichier `Player.log` juste après.

## Limites connues

- Quand l'hébergeur dort seul, la date avance d'une dizaine de minutes (40 avant).
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Retrouvailles sans rechargement (case « No world reload when the host and a player meet again », cochée d'office) : au moindre doute le mod recharge le monde comme avant ; pas joué à quatre joueurs ni entre deux PC.
- Un compagnon d'invité ne suit parfois pas son joueur (vu au banc, pas expliqué).
- « Keep the mods of the game » : un mod retiré de la partie plus tard reste abonné chez vous ; les mods que vous avez
  en trop ne sont pas touchés.

## En cas de problème pendant une partie

- L'hébergeur décoche la case en cause (Échap → Mods → Elin Together → Server Setting).
- Un joueur désynchronisé tape `emp.reconnect_self` dans la console.
- Envoyez les journaux de chacun : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`, et le fichier
  `Player.log` du dossier `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin **EA 23.355**.
Chacun télécharge `ElinTogether-independance.zip` (ci-dessous), le décompresse et lance `Installer.bat`
(`Desinstaller.bat` fait l'inverse). `LISEZMOI.txt` dans le zip explique le reste.

**Sur Mac** (Elin dans CrossOver, Whisky ou Wine) : téléchargez `ElinTogether-independance-mac.zip`, décompressez-le,
ouvrez le Terminal, tapez `bash` puis un espace, faites glisser `Installer-Mac.command` dans la fenêtre et appuyez sur
Entrée. C'est le même mod ; `LISEZMOI-MAC.txt` explique le reste. **Pas encore essayé sur un vrai Mac.**

---

# Elin Together "independence" 0.26.691

Follows 0.26.678: **three known limits gone** and **two differences between the host and the guests fixed**. Played
on the test bench (two windows on one PC, one series with three), nothing between two PCs yet. If this version goes
wrong, 0.26.678 stays online. Built for Elin **EA 23.355**.
**Every player must install this same zip.** Back up your saves first:
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Setting changed

- **Meeting the host again without reloading the world**: the checkbox "No world reload when the host and a player
  meet again" is now **ticked by default** (and switched on once for hosts who already have the mod). When the host
  walks onto a player's map, or the other way round, that player's screen no longer reloads the whole world. At the
  slightest doubt the mod reloads as before. If it goes wrong for you, the host can untick it: that choice stays.

## Fixed (played on the bench)

- **Service paid in a dialog** (tavern and the like): a guest paid in the dialog, then a second time at the end. It
  pays once.
- **Sending away a resident who carries a god artifact**: asked by a guest, the artifact went to the host. It goes
  to the player who sends the resident away.
- **A night "of its own"**: a player could be hit, even killed, during the few seconds of its night. It takes no
  damage while its night plays, as in a solo game, which is paused then.
- **The host sleeping alone** moved the date by 40 minutes; about ten now.

## Reported, not reproduced

- **Mount or parasite gone when joining the host**: fixed since 0.26.652. Replayed here every way (the guest comes
  back, the host joins it, they go home together, a dropped link and return; mount, parasite, both) without seeing
  it. If it still happens with this version, please send the `Player.log` file right after.

## Known limits

- When the host sleeps alone, the date moves by about ten minutes (40 before).
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- Meeting again without a reload ("No world reload when the host and a player meet again", ticked by default): at the slightest doubt the mod loads the world as before; not played with four players nor between two PCs.
- A guest's companion sometimes does not follow its player (seen on the bench, not explained).
- "Keep the mods of the game": a mod removed from the game later stays subscribed on your side; the extra mods you
  have are not touched.

## If something goes wrong during a game

- The host unticks the checkbox (Esc → Mods → Elin Together → Server Setting).
- A desynced player types `emp.reconnect_self` in the console.
- Send everyone's logs: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`, and the `Player.log` file of
  the folder `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin **EA 23.355**.
Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French.

**On a Mac** (Elin in CrossOver, Whisky or Wine): download `ElinTogether-independance-mac.zip`, unzip it, open
Terminal, type `bash` and a space, drag `Installer-Mac.command` into the window and press Enter. Same mod;
`LISEZMOI-MAC.txt` (in French) has the rest. **Not tried on a real Mac yet.**
