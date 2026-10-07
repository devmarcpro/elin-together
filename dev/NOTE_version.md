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
