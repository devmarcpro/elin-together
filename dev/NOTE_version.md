# Elin Together « indépendance » 0.26.744

(English below / version anglaise plus bas)

Version corrective de la 0.26.730. Jouée au banc de test (deux fenêtres sur un PC), rien entre deux PC. La série
complète des tests a tourné sur ce code exact : **12 séries vertes sur 14** ; les deux rouges ne passent qu'en fin de
longue série et sont vertes rejouées seules (voir plus bas). Compilé pour Elin **EA 23.356** (mise à jour de Steam du 13 octobre ; les tests ont tourné sur cette version).
**Tous les joueurs doivent installer ce même zip.**

## Corrigé (joué au banc)

- **Un invité tiré chez l'hébergeur quand les deux changent de carte en même temps** (signalé par un joueur : il
  allait au concert de sa quête et s'est retrouvé dans le donjon de l'hébergeur). Trois cas selon l'ordre des
  messages, les trois corrigés : l'invité va où il allait. Test : l'invité part pendant que l'hébergeur part, cinq
  fois de suite ; avant, 4 ratés sur 5 ; maintenant 5 sur 5. Pas joué : le concert lui-même, ni un escalier.
- **Journal des quêtes** : une quête d'histoire finie puis recommencée se fermait chez l'invité (défaut de la
  0.26.730).
- **Dette de Loytel prise par un invité** : Loytel devient le compagnon de cet invité, plus celui de l'hébergeur.
- **Monture d'un invité vue deux fois** : dans le jeu de l'invité, une case pouvait garder un personnage deux fois
  (une passe de test sur trois, après un retour à la base derrière l'hébergeur). Le jeu de l'invité retire ces
  doublons toutes les deux secondes. La cause d'origine n'est pas trouvée.

## Tests encore instables (pas des défauts prouvés)

- Seringue de gène sur soi et laisse, chez un invité : rouges en fin de longue série seulement, vertes rejouées
  seules deux fois.
- Un sort appris en rêve par l'hébergeur identique au livre de l'invité : sans doute le hasard du tirage.

## Toujours pas reproduit

- Le nombre de compagnons affiché avec un de trop ; un invité qui ne pouvait pas miner. Envoyez le zip du bouton
  « Prepare a bug report » (onglet *Client Settings*) d'une partie où ça arrive.

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

# Elin Together "independence" 0.26.744

Bug-fix release of 0.26.730. Played on the test bench (two windows on one PC), nothing between two PCs. The whole test
series ran on this exact code: **12 series green out of 14**; the two red ones only fail at the end of a long series and
are green replayed on their own (see below). Built for Elin **EA 23.356** (Steam update of 13 October; the tests ran on this version).
**Every player must install this same zip.**

## Fixed (played on the bench)

- **A guest pulled to the host when both change maps at the same moment** (reported by a player: going to the concert
  of their quest, they ended up in the host's dungeon). Three cases depending on the order of messages, all three
  fixed: the guest goes where it was going. Test: the guest leaves while the host leaves, five times in a row; before,
  4 failures out of 5; now 5 out of 5. Not played: the concert itself, nor stairs.
- **Quest journal**: a story quest finished then started again was closed on the guest (defect of 0.26.730).
- **Loytel's debt taken by a guest**: Loytel becomes that guest's companion, no longer the host's.
- **A guest's mount seen twice**: in the guest's game a tile could hold a character twice (one test pass in three,
  after coming back to the base behind the host). The guest's game removes such doubles every two seconds. The
  original cause is not found.

## Tests still unstable (not proven defects)

- Gene syringe on oneself and leash, by a guest: red at the end of a long series only, green replayed alone twice.
- A spell learnt in a dream by the host equal to the guest's book: most likely the luck of the draw.

## Still not reproduced

- The ally count shown one too many; a guest who could not mine. Send the zip of the "Prepare a bug report" button
  (*Client Settings* tab) from a game where it happens.

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

