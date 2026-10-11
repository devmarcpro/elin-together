# Elin Together « indépendance » 0.26.662

(English below / version anglaise plus bas)

Suite de la 0.26.652 : **deux plantages remontés par un joueur le 11 octobre**, et **« une part pour chacun »** : ce
que l'histoire donne une fois par monde, chaque joueur le reçoit. Joué au banc de test (deux ou trois fenêtres sur un
PC), rien encore entre deux PC. Si cette version se passe mal, la 0.26.652 reste en ligne. Compilé pour Elin
**EA 23.355**.
**Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé (joué au banc)

- **Erreur « Index was outside the bounds of the array » en priant, ou à la fin d'une nuit**, quand un autre joueur
  (ou un de ses compagnons) était sur une autre carte, plus grande. Le jeu regardait la case de chaque membre de
  l'équipe sur la carte affichée ; pour un membre parti ailleurs, cette case n'existe pas. La prière le soigne quand
  même, la nuit le repose quand même, sans erreur ; son réveil non plus ne plante plus.
- **Trésor du manoir maudit** : un pour chaque joueur. La quête du groupe avance une seule fois ; en prendre un second
  maudit toujours celui qui le prend.

## Nouveau

- **Une part pour chacun** (case de l'hébergeur « Une fois par monde = une fois par joueur », cochée). Ce qu'une quête
  de l'histoire ou un dialogue donne est donné à chaque autre joueur du monde : dans son sac s'il est sur la carte,
  sinon en colis à son nom dans le courrier de la base. Un joueur qui arrive plus tard dans le monde reçoit en un
  colis ce qu'il n'a pas eu. Les recettes, les actes de propriété et les artefacts ne sont pas multipliés.
  Pas fait : ce qu'un monde a donné **avant** cette version (rien ne l'avait noté).

## À l'essai (case décochée au départ)

- **Reprise du monde quand l'hébergeur part ou plante** (case « Takeover »). Nouveau : l'ancien hébergeur qui recharge
  son monde rejoint tout seul, en invité, la partie de celui qui l'a repris, au lieu d'en ouvrir une seconde. Joué à
  trois fenêtres sur un PC ; par Steam entre de vrais PC : écrit, pas joué.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Quand l'hébergeur et un invité se retrouvent sur une carte, l'écran de l'invité recharge (le monde entier est renvoyé), sauf si l'hébergeur coche la case « No world reload when the host and a player meet again ».
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

# Elin Together "independence" 0.26.662

Follows 0.26.652: **two crashes reported by a player on October 11**, and **"a share for everyone"**: what the story
gives once per world, every player gets. Played on the test bench (two or three windows on one PC), nothing between two
PCs yet. If this version goes wrong, 0.26.652 stays online. Built for Elin **EA 23.355**.
**Every player must install this same zip.** Back up your saves first:
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed (played on the bench)

- **"Index was outside the bounds of the array" when praying, or at the end of a night**, while another player (or one
  of its companions) was on another, bigger map. The game looked at the tile of every party member on the map shown;
  for a member gone elsewhere that tile does not exist. The prayer still heals it, the night still rests it, without
  an error; its waking up does not throw either.
- **Treasure of the cursed manor**: one for each player. The quest of the group moves on once; taking a second one
  still curses whoever takes it.

## New

- **A share for everyone** (host checkbox "Once per world = once per player", ticked). What a story quest or a dialog
  gives is given to every other player of the world: into its bag when it is on the map, else as a parcel in its name
  in the base's mail. A player who comes to the world later gets what it did not have as one parcel. Recipes, deeds and
  artifacts are not multiplied. Not done: what a world gave **before** this version (nothing recorded it).

## To try (unticked at first)

- **Taking the world over when the host leaves or crashes** ("Takeover" checkbox). New: a former host that loads its
  world again joins, on its own and as a guest, the game of the player who took it over, instead of opening a second
  one. Played with three windows on one PC; through Steam between real PCs: written, not played.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- When the host and a guest meet on a map, the guest's screen reloads (the whole world is sent again), unless the host ticks "No world reload when the host and a player meet again".
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
