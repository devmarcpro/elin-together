# Elin Together « indépendance » 0.26.566

(English below / version anglaise plus bas)

Suite de la 0.26.560. **Écrit et compilé, pas joué**, et le changement sur le codex est plus large que les
précédents : si cette version se passe mal, la 0.26.560 reste en ligne. Compilé pour Elin **EA 23.352 Patch 1** (canal
Nightly). **Tous les joueurs doivent installer ce même zip, et avoir la même liste de mods.** Faites une copie de vos
sauvegardes avant : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé

- **Le codex est maintenant commun à tous les joueurs**, comme les recettes : cartes collectées ou retirées, monstres
  tués, points faibles appris, apparitions. Avant, ce qu'un invité collectait n'était compté que chez lui et
  disparaissait au rechargement suivant ; ses cartes n'arrivaient chez l'hébergeur que si celui-ci avait coché
  « collecter les cartes ». C'est maintenant le réglage de celui qui ramasse qui décide.
- **Une carte reçue était parfois refusée une première fois** puis redemandée : elle passe du premier coup.

## Pour les prochaines versions

- Le journal note, à chaque retour d'un invité auprès de l'hébergeur, la durée de son absence et la taille du monde
  reçu. Rien ne change en jeu : ces chiffres serviront à supprimer les rechargements d'écran.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
- Quand l'hébergeur rejoint un invité sur sa carte, l'écran de l'invité recharge (le monde entier est renvoyé).
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

# Elin Together "independence" 0.26.566

Follows 0.26.560. **Written and compiled, not played**, and the codex change is wider than the previous ones: if this
version goes wrong, 0.26.560 stays online. Built for Elin **EA 23.352 Patch 1** (Nightly branch). **Every player must
install this same zip and have the same list of mods.** Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed

- **The codex is now shared by all players**, like the recipes: cards collected or taken out, monsters killed, weak
  spots learnt, appearances. Before, what a guest collected only counted in its own game and was gone at the next
  reload; its cards reached the host only if the host had "collect cards" ticked. The setting of the player who picks
  the card up now decides.
- **A map received was sometimes refused once** and asked for again: it now goes through the first time.

## For the next versions

- The log notes, each time a guest comes back to the host, how long it was away and how big the world it received
  was. Nothing changes in game: these figures will be used to remove the screen reloads.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- When the host joins a guest on its map, the guest's screen reloads (the whole world is sent again).
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
