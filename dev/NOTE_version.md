# Elin Together « indépendance » 0.26.716

(English below / version anglaise plus bas)

Suite de la 0.26.708 : **les factures d'impôt « fantômes »**, une copie de secours automatique du monde, et un bouton
pour signaler un problème. Joué au banc de test (deux fenêtres sur un PC), rien encore entre deux PC. **Cette version
sort sans que toutes les séries de tests aient été rejouées** : celles qui touchent ce qui a changé l'ont été. Si elle
se passe mal, la 0.26.708 reste en ligne. Compilé pour Elin **EA 23.355**.
**Tous les joueurs doivent installer ce même zip.**

## Corrigé (joué au banc)

- **Factures d'impôt impossibles à solder.** Avant la 0.26.652, une facture payée par un invité seul sur une autre
  carte n'était pas toujours comptée : le monde gardait plus de factures « impayées » qu'il n'en existe, plus rien à
  payer pour faire baisser ce nombre, et 50 de karma en moins chaque mois. Le compteur est ramené aux factures qui
  existent vraiment (sacs de tous les joueurs et compagnons, courrier, banque, caisse d'expédition, carte où se trouve
  l'hébergeur). Il n'est jamais relevé. **Cela se fait tout seul**, une fois, quand l'hébergeur lance la partie avec
  cette version ; un bouton de l'onglet *Server Setting* le refait à la demande (« Unpaid tax bills: counted N,
  existing M (repair) »). Une facture rangée dans un coffre sur une autre carte n'est pas vue : si le compteur tombe
  à zéro, le jeu la refusera, elle est simplement annulée.

## Nouveau

- **Copie de secours avant une nouvelle version.** La première fois qu'un monde est hébergé avec une nouvelle version
  du mod, la sauvegarde telle qu'elle est sur le disque est d'abord copiée dans les sauvegardes de secours du jeu
  (celles que son écran de chargement sait restaurer).
- **Signaler un problème.** Le bouton « Prepare a bug report » de l'onglet *Client Settings* écrit sur le bureau un
  zip avec le journal du jeu, celui d'avant, les derniers journaux du mod et une courte fiche (versions, mods).
  Ni sauvegarde, ni fichier de réglages. C'est ce fichier qu'il faut envoyer.

## Limites connues

- Quand l'hébergeur dort seul, la date avance d'une dizaine de minutes (40 avant).
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Retrouvailles sans rechargement (case « No world reload when the host and a player meet again », cochée d'office) : au moindre doute le mod recharge le monde comme avant ; pas joué à quatre joueurs ni entre deux PC.
- Un compagnon qui se tient à 5 cases de son joueur : c'est le réglage « mes alliés gardent leurs distances » de ce joueur. Avec ce réglage coché, le jeu ne tire pas non plus la laisse.
- Rattrapage des anciens mondes : les recettes, les billets de la dette, les cadeaux du mariage et les cadeaux de dialogue ne sont pas redonnés.
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


---

# Elin Together "independence" 0.26.716

Follows 0.26.708: **"phantom" tax bills**, an automatic backup of the world, and a button to report a problem.
Played on the test bench (two windows on one PC), nothing between two PCs yet. **This release ships without every
test series having been replayed**: those covering what changed were. If it goes wrong, 0.26.708 stays online. Built
for Elin **EA 23.355**.
**Every player must install this same zip.**

## Fixed (played on the bench)

- **Tax bills that could not be settled.** Before 0.26.652, a bill paid by a guest alone on another map was not
  always counted: the world kept more "unpaid" bills than exist, with nothing left to pay to bring that number down,
  and 50 karma lost each month. The count is brought down to the bills that really exist (bags of every player and
  companion, mail, bank, shipping box, the map the host stands on). It is never raised. **It happens by itself**,
  once, when the host starts the game with this version; a button of the *Server Setting* tab does it again on
  request ("Unpaid tax bills: counted N, existing M (repair)"). A bill kept in a chest on another map is not seen:
  if the count drops to zero the game will refuse it, it is simply cancelled.

## New

- **Backup before a new version.** The first time a world is hosted with a new version of the mod, the save as it
  is on disk is first copied to the game's own backups (the ones its load screen can restore).
- **Reporting a problem.** The "Prepare a bug report" button of the *Client Settings* tab writes a zip on the desktop
  with the game's log, the previous one, the latest logs of the mod and a short note (versions, mods). No save, no
  settings file. That is the file to send.

## Known limits

- When the host sleeps alone, the date moves by about ten minutes (40 before).
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- Meeting again without a reload ("No world reload when the host and a player meet again", ticked by default): at the slightest doubt the mod loads the world as before; not played with four players nor between two PCs.
- A companion standing 5 tiles from its player: that is this player's own "allies keep their distance" setting. With it ticked the game does not pull the leash either.
- Catching up old worlds: recipes, the tickets of the debt, the wedding gifts and dialog gifts are not given again.
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

