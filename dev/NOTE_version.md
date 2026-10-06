# Elin Together « indépendance » 0.26.524

(English below / version anglaise plus bas)

**Version non testée en jeu.** Elle répond aux retours d'une vraie soirée à trois joueurs et plus (« énormément de
désynchronisations »). Tout a été écrit, relu et compilé, mais **rien n'a été joué**, même pas par les tests
automatiques. Si elle se passe mal, revenez à la 0.26.510, qui reste en ligne. Compilé pour Elin **EA 23.352 Patch 1**
(canal Nightly). **Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Désynchronisations entre joueurs

- **Plus aucun message n'est jeté** quand la liaison Steam est saturée : il attend et repart dans l'ordre. Les gros
  envois (carte, monde) partent en morceaux. Avant, un message refusé par Steam était perdu sans trace.
- **Arrivée ou retour d'un joueur** : le monde et la carte partent ensemble, et ce que les autres font pendant son
  chargement est rejoué ensuite au lieu d'être perdu.
- **L'hébergeur quitte sa carte** : sa copie fait foi. Le joueur qui garde la carte ne la recharge que si la sienne
  diffère.
- **Objet inconnu de l'hébergeur** : il ne disparaît plus chez tout le monde.
- **Réparation automatique** : toutes les 2 secondes les jeux comparent quelques nombres par carte ; si un écart dure,
  il est écrit dans les journaux et la carte est rechargée sur place. Case « Repair the map by itself » (cochée).

## Corrigé

- **Boss de donjon invisible pour les invités, donjon « conquis » sans boss vaincu** : rejoindre un joueur à l'étage
  du boss ne le fait plus fuir.
- **Objets qui « disparaissent » quand un invité marche dessus, sac plein** : ils restent par terre, comme en solo.
- **Banque et coffre d'expédition d'un invité** seul sur une autre carte : la fenêtre montre le vrai contenu, on peut
  déposer et reprendre.
- **Recette apprise par un invité** comptée deux fois chez lui.
- **Quête de récolte ou de concert** qui échouait quand un autre joueur faisait passer le temps.

## Nouveau (chacun a sa case côté hébergeur, cochée)

- **Chacun dort pour soi** (« Everyone sleeps for themselves ») : on dort tout de suite sans attendre personne ; la
  nuit ne passe pour le monde que si tous dorment en même temps. L'invité lit son grimoire, profite de son lit et de
  son oreiller, tire sa propre recette.
- **Le temps ne saute que quand tous sautent** (« Time only jumps when everyone jumps ») : un pas sur la carte du
  monde ne fait plus avancer la date des autres ; le voyageur paie sa propre faim.
- **Le rangement automatique épargne la main et la ceinture à outils.**
- **Un invité peut payer une facture** ; tout le monde lit qui a payé.
- **Prendre le monde d'un dépôt ouvre la partie tout seul.**
- **Un joueur connu du monde entre sans être ami Steam** de l'hébergeur.
- **Seul dans sa partie**, l'hébergeur retrouve les règles du jeu solo.
- **Moins de lenteurs à plusieurs** : une seule sauvegarde quand un invité revient, un message au lieu de 120 par
  pas sur la carte du monde.

## En cas de problème pendant une partie

- L'hébergeur décoche la case de la nouveauté en cause (Échap → Mods → Elin Together → Server Setting) : l'ancien
  comportement revient tout de suite.
- Un joueur désynchronisé tape `emp.reconnect_self` dans la console du jeu.
- Après la partie, envoyez les journaux de l'hébergeur et d'un invité :
  `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs\Session_AAAAMMJJ.log`.

## Pas encore fait

- Quand l'hébergeur part ou plante, aucun invité ne reprend le monde tout seul.
- Un écart dans un sac est signalé au journal, pas encore réparé.
- Deux factures (impôt, livraison) ne sont pas un doublon ; l'impôt se calcule encore sur la renommée de l'hébergeur.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly**. Chacun télécharge `ElinTogether-independance.zip` (ci-dessous), le décompresse et lance `Installer.bat`
(`Desinstaller.bat` fait l'inverse). `LISEZMOI.txt` dans le zip explique le reste.

---

# Elin Together "independence" 0.26.524

**Not tested in game.** It answers the reports of a real evening with three players and more ("a lot of desync").
Everything was written, reviewed and compiled, but **nothing was played**, not even by the automated tests. If it goes
wrong, go back to 0.26.510, which stays online. Built for Elin **EA 23.352 Patch 1** (Nightly branch). **Every player
must install this same zip.** Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Desync between players

- **No message is dropped any more** when the Steam link is saturated: it waits and goes out in order. Big sends (map,
  world) go in pieces. Before, a message refused by Steam was lost without a trace.
- **A player arriving or coming back**: world and map are sent together, and what the others do while it loads is
  replayed afterwards instead of being lost.
- **The host leaves its map**: its copy is the reference. The player who keeps the map only reloads it when its own
  differs.
- **An item the host does not know** no longer vanishes for everyone.
- **Automatic repair**: every 2 seconds the games compare a few numbers per map; a lasting difference is written to
  the logs and the map is reloaded in place. Checkbox "Repair the map by itself" (checked).

## Fixed

- **Dungeon boss invisible to guests, dungeon "conquered" with its boss alive**: joining a player on the boss floor no
  longer makes it flee.
- **Items "vanishing" when a guest walks on them with a full bag**: they stay on the ground, as in solo.
- **Bank and shipping chest of a guest** alone on another map: the window shows the real content, deposit and take back.
- **A recipe learnt by a guest** counted twice for that guest.
- **Harvest or concert quest** failing when another player made time pass.

## New (each has a host checkbox, checked)

- **Everyone sleeps for themselves**: you sleep at once without waiting; the night only passes for the world when all
  sleep at the same time. A guest reads its spellbook, uses its own bed and pillow, draws its own recipe.
- **Time only jumps when everyone jumps**: a step on the world map no longer moves the others' date; the traveller pays
  its own hunger.
- **Auto-dump spares the hand and the tool belt.**
- **A guest can pay a bill**; everyone reads who paid.
- **Taking a world from a depot opens the session by itself.**
- **A player known to the world comes in without being a Steam friend** of the host.
- **Alone in its session**, the host gets the solo rules back.
- **Less slowness with several guests**: one save when a guest comes back, one message instead of 120 per step on the
  world map.

## If something goes wrong during a game

- The host unticks the checkbox of the feature (Esc → Mods → Elin Together → Server Setting): the former behaviour is
  back at once.
- A desynced player types `emp.reconnect_self` in the game's console.
- After the game, send the logs of the host and of a guest:
  `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs\Session_YYYYMMDD.log`.

## Not done yet

- When the host leaves or crashes, no guest takes the world over by itself.
- A difference in a bag is written to the log, not repaired yet.
- Two bills (tax, delivery) are not a duplicate; tax is still computed on the host's fame.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the **Nightly**
branch. Each player downloads `ElinTogether-independance.zip` (below), unzips it and runs `Installer.bat`
(`Desinstaller.bat` switches back). The installer and its notes (`LISEZMOI.txt` in the zip) are in French.
