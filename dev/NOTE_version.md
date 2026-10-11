# Elin Together « indépendance » 0.26.678

(English below / version anglaise plus bas)

Suite de la 0.26.662 : **sept différences entre l'hébergeur et les invités en moins**. Joué au banc de test (deux
fenêtres sur un PC), rien encore entre deux PC ; la plupart des essais appellent la fonction du jeu sans passer par
le dialogue ou le menu. Si cette version se passe mal, la 0.26.662 reste en ligne. Compilé pour Elin **EA 23.355**.
**Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé (joué au banc)

- **Artefact de dieu.** Le second joueur qui prenait le sien détruisait celui du premier. Chaque joueur garde le
  sien ; un même joueur qui en prend un second perd toujours son premier, comme dans le jeu.
- **Terre achetée à la servante de la base.** Un invité payait sa platine et l'agrandissement ne se voyait que chez
  lui. Il vaut maintenant pour tous les joueurs.
- **Réglages d'un habitant par son dialogue** (« reste ici », « dors à côté », équipement partagé, les « pas de… »).
  Réglés par un invité, ils restaient sans effet ; ils valent pour tous, d'où qu'ils viennent.
- **Parchemin de reconstruction lu par un invité.** L'objet neuf lui était mis d'office à la place de ce qu'il
  portait. Il va dans son sac. Pas corrigé : son niveau suit la progression de l'hébergeur.
- **Pêche.** Les cinq prises « de qualité » du jour (don du pêcheur) sont comptées par joueur ; pour un invité elles
  duraient sans fin ou n'arrivaient jamais. Le compte repart si l'hébergeur relance le jeu.

## Nouveau

- **Une part pour chacun**, suite : le crochet et le coffre verrouillé de Fiama (donnés au début de sa quête) et son
  livre d'histoire sont donnés à chaque joueur. Le joueur qui reçoit sa part d'une récompense le lit dans son journal
  (dans la langue de l'hébergeur).

## Limites connues

- Quand l'hébergeur dort seul, la date avance d'une dizaine de minutes (40 avant).
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

# Elin Together "independence" 0.26.678

Follows 0.26.662: **seven fewer differences between the host and the guests**. Played on the test bench (two windows
on one PC), nothing between two PCs yet; most trials call the game's function without going through the dialog or the
menu. If this version goes wrong, 0.26.662 stays online. Built for Elin **EA 23.355**.
**Every player must install this same zip.** Back up your saves first:
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed (played on the bench)

- **God artifact.** The second player to take its own destroyed the first player's. Each player keeps its own; one
  player taking a second copy still loses its first, as in the game.
- **Land bought from the maid of the base.** A guest paid its platinum and only its own game grew. It now counts for
  every player.
- **Settings of a resident from its dialog** ("stay here", "sleep beside me", shared equipment, the "no ..."
  switches). Set by a guest, they had no effect; they now count for everyone, whoever sets them.
- **Scroll of reconstruction read by a guest.** The new item was put on the guest in place of what it wore. It goes
  to its bag. Not fixed: its level follows the host's progress.
- **Fishing.** The five "quality" catches of the day (fisher's feat) are counted per player; for a guest they never
  ended or never came. The count starts again if the host restarts the game.

## New

- **A share for everyone**, continued: Fiama's lockpick and locked chest (given when her quest starts) and her story
  book are given to each player. A player who gets its share of a reward reads it in its log (in the host's
  language).

## Known limits

- When the host sleeps alone, the date moves by about ten minutes (40 before).
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
