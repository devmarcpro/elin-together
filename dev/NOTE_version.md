# Elin Together « indépendance » 0.26.708

(English below / version anglaise plus bas)

Suite de la 0.26.691 : **les personnages recrutés seul qui disparaissaient** (signalé par un joueur), **un défaut de la
0.26.691 sur la brosse**, et plusieurs différences entre l'hébergeur et les invités en moins. Joué au banc de test (deux
fenêtres sur un PC), rien encore entre deux PC. Si cette version se passe mal, la 0.26.691 reste en ligne. Compilé pour
Elin **EA 23.355**.
**Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé (joué au banc)

- **Personnages recrutés seul qui disparaissaient.** Un invité seul sur une autre carte (un champ, une ville) qui
  recrutait un personnage puis le renvoyait à la base, ou dont la recrue mourait et attendait à la base : ce personnage
  n'existait plus chez l'hébergeur. Il lui est maintenant remis au retour de l'invité, à sa base. Une recrue gardée
  dans l'équipe est aussi inscrite comme habitante de la base chez tout le monde.
- **« Reste ici » oublié.** Réglé par un invité seul, puis de retour chez l'hébergeur : la case où le compagnon devait
  rester était perdue dans le jeu de l'invité, une fois sur deux.
- **Brosser un animal (défaut de la 0.26.691).** L'animal apprivoisé à la brosse par un invité appartenait à
  l'hébergeur. Il est de nouveau à l'invité.
- **Objet non identifié vendu par un invité** : il restait « non identifié » dans la boutique chez l'hébergeur.
- **Boss d'une zone.** Quand il tombe, tous les joueurs présents ont la victoire (message, fanfare, renommée), et le
  donjon est noté conquis dans le monde, même battu par un invité seul.
- **Expérience « d'équipe »** (une récolte apprend le jardinage à tous) : chaque joueur la reçoit, d'où qu'elle
  vienne ; avant, seul celui qui agissait.
- **Impôt supplémentaire** choisi par un invité auprès de la servante : il vaut pour le monde.

## Nouveau

- **Une part pour chacun dans les mondes déjà joués.** À la première ouverture d'un ancien monde avec cette version,
  les récompenses des quêtes d'histoire déjà terminées sont données une fois à chaque joueur, hébergeur compris, dans un
  colis à son nom (l'hébergeur tout de suite, les autres à leur arrivée sur sa carte). Vous pouvez recevoir en double
  ce que vous aviez déjà : on ne sait pas qui avait gagné quoi. Dans un monde que seul l'hébergeur a joué, lui ne
  reçoit rien en double.

## Signalé, pas reproduit

- **Des compagnons qui « s'en vont souvent » quand un invité est seul dans les champs.** Tous les réglages d'un
  compagnon faits seul ont été comparés avant et après le retour (82 valeurs) sans autre écart que « reste ici ».
  Si cela vous arrive, dites quel compagnon, quel réglage, et où vous le retrouvez ; le fichier `Player.log` aide.

## Limites connues

- Quand l'hébergeur dort seul, la date avance d'une dizaine de minutes (40 avant).
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Retrouvailles sans rechargement (case « No world reload when the host and a player meet again », cochée d'office) : au moindre doute le mod recharge le monde comme avant ; pas joué à quatre joueurs ni entre deux PC.
- Un compagnon qui se tient à 5 cases de son joueur : c'est le réglage « mes alliés gardent leurs distances » de ce joueur.
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

# Elin Together "independence" 0.26.708

Follows 0.26.691: **characters recruited alone that vanished** (reported by a player), **a defect of 0.26.691 with the
brush**, and several fewer differences between the host and the guests. Played on the test bench (two windows on one
PC), nothing between two PCs yet. If this version goes wrong, 0.26.691 stays online. Built for Elin **EA 23.355**.
**Every player must install this same zip.** Back up your saves first:
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed (played on the bench)

- **Characters recruited alone that vanished.** A guest alone on another map (a field, a town) who recruited a
  character then sent it home, or whose recruit died and waited at the base: that character no longer existed on the
  host's side. It is now handed to the host when the guest comes back, at its base. A recruit kept in the party is
  also registered as a resident of the base for everyone.
- **"Stay here" forgotten.** Set by a guest alone, then back with the host: the tile the companion had to stay on was
  lost in the guest's game, one time out of two.
- **Brushing an animal (a defect of 0.26.691).** An animal tamed with the brush by a guest belonged to the host. It
  is the guest's again.
- **Unidentified item sold by a guest**: it stayed "unidentified" in the shop on the host's side.
- **Boss of a zone.** When it falls, every player present gets the victory (message, fanfare, fame), and the dungeon
  is marked conquered in the world, even when beaten by a guest alone.
- **"Party" experience** (a harvest teaches gardening to everyone): every player gets it, wherever it comes from;
  before, only the one who acted.
- **Extra tax** chosen by a guest with the maid: it counts for the world.

## New

- **A share for everyone in worlds already played.** The first time an old world is opened with this version, the
  rewards of the story quests already completed are given once to every player, the host included, in a parcel in
  its name (the host at once, the others when they reach its map). You may get a spare of what you already had:
  nothing records who earned what. In a world only its host ever played, the host gets no spare.

## Reported, not reproduced

- **Companions that "often wander off" while a guest is alone in the fields.** Every setting of a companion made
  alone was compared before and after the return (82 values) with no gap other than "stay here". If it happens to
  you, say which companion, which setting, and where you find it afterwards; the `Player.log` file helps.

## Known limits

- When the host sleeps alone, the date moves by about ten minutes (40 before).
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- Meeting again without a reload ("No world reload when the host and a player meet again", ticked by default): at the slightest doubt the mod loads the world as before; not played with four players nor between two PCs.
- A companion standing 5 tiles from its player: that is this player's own "allies keep their distance" setting.
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

