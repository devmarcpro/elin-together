# Elin Together « indépendance » 0.26.621

(English below / version anglaise plus bas)

Suite de la 0.26.608 : **trois corrections venues de vraies parties**, et **une nouveauté à l'essai, éteinte au
départ**. Les corrections ont été jouées au banc de test (deux fenêtres sur un PC), pas encore entre deux PC. Si
cette version se passe mal, la 0.26.608 reste en ligne. Compilé pour Elin **EA 23.353** (canal Nightly).
**Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé

- **Le monde du dépôt ne se chargeait plus, chez personne (nouveau dans la 0.26.621).** Quand les personnages de
  joueurs étaient montés au moment de la sauvegarde, leur monture pouvait être enregistrée « hors de la carte » : le
  chargement s'arrêtait sur une erreur et l'écran restait bloqué. Ces montures sont maintenant remises sur la case de
  leur cavalier et le monde se charge. Vérifié sur une copie du monde en cause.

- **Un joueur renvoyé à l'écran titre quand la liaison Steam tombe (« Connection dropped »).** Vu en vraie partie :
  la liaison entre deux joueurs est tombée une demi-minute, aucun jeu n'avait planté, mais le joueur invité se
  retrouvait à l'écran titre et devait rejoindre à la main. Il revient maintenant tout seul dans la partie, avec le
  message de reconnexion, comme pour les autres coupures.
- **Les réglages d'un coffre faits par un invité n'étaient pas gardés.** Seules les règles de rangement (priorité,
  catégories, filtre, partagé ou personnel) partaient chez l'hébergeur. Le nom du coffre, son icône, la taille, les
  colonnes et la couleur de sa grille, le tri et « toujours trier » sont maintenant enregistrés avec le coffre, pour
  tous les joueurs. Conséquence : la taille et le tri d'un coffre de la base sont les mêmes pour tout le monde ; seule
  la place de la fenêtre à l'écran reste à chacun. Les sacs que chacun porte restent personnels.

## Nouveau, à l'essai (case décochée au départ)

- **« Another player takes over when the host leaves »** (onglet « Server Setting », a besoin de la case « The other
  players keep a copy of the world »). Quand l'hébergeur quitte par le menu du jeu ou par le bouton Disconnect, il
  envoie d'abord sa dernière sauvegarde, puis un autre joueur rouvre le monde chez lui en moins d'une minute, sans
  clic, avec son propre personnage ; le personnage de l'ancien hébergeur l'attend, et il le retrouve en rejoignant.
  Le monde repris est rangé dans une sauvegarde neuve chez celui qui reprend ; aucune sauvegarde existante n'est
  touchée.
  - **Joué à deux fenêtres sur un PC seulement.** Pas joué : trois joueurs (les autres invités ne suivent pas encore
    le nouvel hébergeur tout seuls), un plantage de l'hébergeur (rien ne se passe dans ce cas, comme avant), deux
    vrais PC.
  - **Risque connu** : un hébergeur qui rouvre sa partie juste après l'avoir quittée se retrouve à côté d'un
    deuxième hébergeur du même monde. Laissez la case décochée si vous ne voulez pas essayer.

## Déjà dans la 0.26.608 (pas joué)

- La case « Keep the mods of the game » (onglet « Client Settings ») pour ne plus voir Elin se relancer à chaque
  soirée dans une partie avec mods.
- Rejoindre avec un personnage monté ; l'erreur à chaque dialogue avec un mod de langue.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Chez l'hébergeur, les invités qui marchent avancent par à-coups de trois cases.
- Quand l'hébergeur et un invité se retrouvent sur une carte, l'écran de l'invité recharge (le monde entier est renvoyé), sauf si l'hébergeur coche la case « No world reload when the host and a player meet again ».
- Quand l'hébergeur plante, aucun invité ne reprend le monde tout seul (la nouvelle case ne couvre que le départ
  volontaire).
- « Keep the mods of the game » : un mod retiré de la partie plus tard reste abonné chez vous ; les mods que vous avez
  en trop ne sont pas touchés.

## En cas de problème pendant une partie

- L'hébergeur décoche la case en cause (Échap → Mods → Elin Together → Server Setting).
- Un joueur désynchronisé tape `emp.reconnect_self` dans la console.
- Envoyez les journaux de chacun : `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`, et le fichier
  `Player.log` du dossier `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly**. Chacun télécharge `ElinTogether-independance.zip` (ci-dessous), le décompresse et lance `Installer.bat`
(`Desinstaller.bat` fait l'inverse). `LISEZMOI.txt` dans le zip explique le reste.

**Sur Mac** (Elin dans CrossOver, Whisky ou Wine) : téléchargez `ElinTogether-independance-mac.zip`, décompressez-le,
ouvrez le Terminal, tapez `bash` puis un espace, faites glisser `Installer-Mac.command` dans la fenêtre et appuyez sur
Entrée. C'est le même mod ; `LISEZMOI-MAC.txt` explique le reste. **Pas encore essayé sur un vrai Mac.**

---

# Elin Together "independence" 0.26.621

Follows 0.26.608: **three fixes that came from real games**, and **one new thing to try, off at first**. The fixes
were played on the test bench (two windows on one PC), not between two PCs yet. If this version goes wrong, 0.26.608
stays online. Built for Elin **EA 23.353** (Nightly branch). **Every player must install this same zip.**
Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed

- **The depot's world could not be loaded any more, by anyone (new in 0.26.621).** When players' characters were
  mounted as the world was saved, their mount could be saved "outside the map": the load stopped on an error and the
  screen stayed stuck. These mounts are now put back on their rider's tile and the world loads. Checked on a copy of
  the world it happened to.

- **A player sent to the title screen when the Steam link drops ("Connection dropped").** Seen in a real game: the
  link between two players dropped for half a minute, no game had crashed, yet the guest ended up on the title screen
  and had to join again by hand. It now comes back into the game by itself, with the reconnection notice, as for the
  other kinds of lost link.
- **The settings a guest made on a chest were not kept.** Only the storage rules (priority, categories, filter,
  shared or personal) reached the host. The name of the chest, its icon, the size, columns and colour of its grid,
  the sort and "always sort" are now saved with the chest, for every player. Consequence: the size and sort of a
  chest of the base are the same for everyone; only the place of the window on the screen stays each player's. The
  bags each player carries stay personal.

## New, to try (unticked at first)

- **"Another player takes over when the host leaves"** ("Server Setting" tab, needs "The other players keep a copy
  of the world"). When the host leaves through the game's menu or the Disconnect button, it first sends its last
  save, then another player opens the world on its own PC in under a minute, without a click, with its own
  character; the former host's character waits for it, and it gets it back when it joins. The world taken over is
  kept in a new save of the player who takes it; no existing save is touched.
  - **Played with two windows on one PC only.** Not played: three players (the other guests do not follow the new
    host by themselves yet), a crash of the host (nothing happens then, as before), two real PCs.
  - **Known risk**: a host that opens its game again right after leaving ends up beside a second host of the same
    world. Leave the box unticked if you do not want to try.

## Already in 0.26.608 (not played)

- The "Keep the mods of the game" checkbox ("Client Settings" tab), so Elin no longer restarts at every evening in
  a game with mods.
- Joining with a mounted character; the error at every talk with a language mod.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- On the host, walking guests move in jumps of three tiles.
- When the host and a guest meet on a map, the guest's screen reloads (the whole world is sent again), unless the host ticks "No world reload when the host and a player meet again".
- When the host crashes, no guest takes the world over by itself (the new checkbox only covers a host that leaves
  by choice).
- "Keep the mods of the game": a mod removed from the game later stays subscribed on your side; the extra mods you
  have are not touched.

## If something goes wrong during a game

- The host unticks the checkbox (Esc → Mods → Elin Together → Server Setting).
- A desynced player types `emp.reconnect_self` in the console.
- Send everyone's logs: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs`, and the `Player.log` file of
  the folder `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the **Nightly**
branch. Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French.

**On a Mac** (Elin in CrossOver, Whisky or Wine): download `ElinTogether-independance-mac.zip`, unzip it, open
Terminal, type `bash` and a space, drag `Installer-Mac.command` into the window and press Enter. Same mod;
`LISEZMOI-MAC.txt` (in French) has the rest. **Not tried on a real Mac yet.**
