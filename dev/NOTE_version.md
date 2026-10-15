# Elin Together « indépendance » 0.26.757

(English below / version anglaise plus bas)

Suite de la 0.26.754 : une correction (fureur au combat). Jouée au banc de test (deux fenêtres sur un PC), rien entre deux PC. La série complète des tests a tourné sur le code de la 0.26.751 (les corrections des hallucinations et de la fureur ont leur propre test, vert) : **11 séries vertes sur 14** ; deux des trois rouges sont vertes rejouées seules sur un monde
neuf, la troisième est un réglage de test (voir plus bas). Compilé pour Elin **EA 23.356**.
**Tous les joueurs doivent installer ce même zip.**

## Corrigé (joué au banc)

- **Fureur au combat (« Strife ») partagée** (0.26.757) : dans le jeu de l'hébergeur, la fureur d'un invité était
  remplacée par celle de l'hébergeur, ou retirée s'il n'en avait pas, et celle de l'hébergeur était donnée à
  l'invité et à ses compagnons. Chacun garde maintenant la sienne ; ses compagnons copient celle de leur joueur.

- **Hallucinations partagées** (0.26.754) : quand l'hébergeur mangeait un champignon blanc, l'écran de l'invité
  hallucinait aussi, et ça ne partait pas. L'écran de chaque joueur ne suit plus que son propre personnage (et un
  invité qui hallucine le voit enfin lui-même).

- **Médailles (et tout objet en pile) qui disparaissent quand un invité en lâche une partie.** Le menu « partager »
  du jeu ne marchait pas chez un invité : toute la pile tombait, et il gardait dans son sac une copie fantôme du
  reste, perdue ensuite. L'hébergeur fait maintenant le partage : 2 lâchées sur 5, il en reste 3, pareil partout.
- **Tente améliorée à la clé par un invité** (électricité, sol fertile, fond marin) : l'amélioration ne vivait que
  dans un jeu et se perdait au bout d'un moment. Elle est maintenant connue de tous les jeux, même faite seul sur
  sa carte. Une tente déjà touchée : repasser la clé une fois.

## Nouveau

- **Un invité peut supprimer un de ses personnages** : dans la liste des personnages à la connexion, « Supprimer un
  personnage », puis une confirmation. Le personnage disparaît avec ce qu'il porte ; ses compagnons restent dans le
  monde. Case de l'hébergeur « Les joueurs peuvent supprimer leurs personnages » (cochée). La liste n'apparaît que
  si « demander le personnage » est cochée, ou si l'invité a plusieurs personnages sans en avoir joué un en dernier.
  Pas joué : les deux fenêtres côté invité (testé côté hébergeur).

## Tests encore instables

- En toute fin de longue série seulement : l'amélioration de tente faite seul, et une quête à deux où l'invité doit
  tuer le dernier monstre. Les deux sont vertes rejouées seules sur un monde neuf.

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

# Elin Together "independence" 0.26.757

Follows 0.26.754: one fix (strife). Played on the test bench (two windows on one PC), nothing between two PCs. The whole test series ran on 0.26.751's code (the hallucination and strife fixes have their own tests, green): **11 series green out of 14**; two of the three red ones are green replayed alone on a fresh world, the
third is a test setting (see below). Built for Elin **EA 23.356**.
**Every player must install this same zip.**

## Fixed (played on the bench)

- **Shared strife** (0.26.757): in the host's game a guest's strife was replaced by the host's, or removed when the
  host had none, and the host's was given to the guest and its companions. Each player now keeps its own; its
  companions copy their player's.

- **Shared hallucinations** (0.26.754): when the host ate a white mushroom, the guest's screen hallucinated too, for
  good. Each player's screen now follows its own character only (and a guest who hallucinates finally sees it).

- **Medals (and any stacked item) vanishing when a guest drops part of a stack.** The game's split menu did not work
  for a guest: the whole stack fell, and the guest kept a phantom copy of the rest in its bag, lost later. The host
  now does the split: 2 dropped out of 5, 3 left, the same everywhere.
- **A tent upgraded with a wrench by a guest** (electricity, fertile soil, sea bed): the upgrade lived in one game only
  and was lost after a while. It is now known to every game, even done alone on one's own map. A tent already hit:
  use the wrench once more.

## New

- **A guest can delete one of its characters**: in the list of characters when joining, "Delete a character", then a
  confirmation. The character goes with what it carries; its companions stay in the world. Host checkbox "Players can
  delete their characters" (ticked). The list only shows when "ask the character" is ticked, or when the guest has
  several characters and none played last. Not played: the two windows on the guest's side (tested on the host's).

## Tests still unstable

- Only at the very end of a long series: the tent upgrade done alone, and a quest for two where the guest kills the
  last monster. Both are green replayed alone on a fresh world.

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

