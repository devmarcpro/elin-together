# Elin Together « indépendance » 0.26.652

(English below / version anglaise plus bas)

Suite de la 0.26.621 : **les bugs remontés par les joueurs le 10 octobre**, **les boutiques à vente unique pour chaque
joueur**, et la **reprise du monde quand l'hébergeur part ou plante**, toujours à l'essai. Presque tout a été joué au
banc de test (deux ou trois fenêtres sur un PC), rien encore entre deux PC. Si cette version se passe mal, la 0.26.621
reste en ligne. Compilé pour Elin **EA 23.355** (la mise à jour du 11 octobre).
**Tous les joueurs doivent installer ce même zip.** Faites une copie de vos sauvegardes avant :
`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Corrigé (joué au banc)

- **Monstre figé en combat.** Quand un joueur attaquait le monstre qui visait un autre joueur, et que ce dernier ne
  faisait rien, le monstre ne bougeait plus et mourait sans se défendre. Un monstre suit maintenant le joueur le plus
  rapide parmi ceux qui se battent avec lui (sa cible, ou qui l'a attaqué, touché ou raté) ; il ne va pas deux fois
  plus vite quand deux joueurs jouent, et il s'arrête quand personne ne joue, comme en solo. Vaut aussi sur une carte
  tenue par un invité.
- **Erreur « An item with the same key has already been added »** (liste de l'équipe à l'écran) : un personnage
  pouvait se retrouver deux fois dans l'équipe.
- **Les invités commençaient avec deux bourses.** Un nouvel invité en a une seule, celle de la ceinture à outils,
  comme l'hébergeur. Les personnages déjà créés gardent la leur.
- **Les sorts posés sur les barres de raccourcis d'un invité étaient perdus** d'une session à l'autre.
- **Trois factures payées de suite par un invité seul sur une autre carte : une seule comptait.** Elles comptent
  toutes. Les mondes déjà touchés gardent un compteur trop haut : pas encore réparé.
- **Monture d'un invité.** Au retour d'un invité monté, l'hébergeur le faisait monter une copie invisible de sa
  monture, et la vraie restait ailleurs avec une vieille position : c'est ce qui avait rendu un monde impossible à
  charger. Cavalier et monture sont de nouveau reliés, sur la même case.
- **Offres de quêtes d'une ville** : après un renouvellement, un invité gardait les anciennes en plus des nouvelles ;
  et son bouton « Reroll Quests » dépensait l'influence sans rien tirer.
- **Points de vie du perdant après un duel** : pas toujours au maximum dans son propre jeu.
- **Recette de bloc** (avec variante pilier ou pont) comptée deux fois chez les autres joueurs.
- La laisse d'un compagnon d'invité le ramène à côté de lui (défaut intermittent, pas reproduit sur commande).

## Corrigé (relu, pas prouvé par un essai)

- Une recette apprise par un joueur seul sur une autre carte arrive chez les autres, et les leurs chez lui.
- Un niveau gagné par un joueur loin de l'hébergeur n'est plus refusé.
- En nuit commune (case « chacun dort pour soi » décochée), les invités perdent aussi saignement et poison.
- Une erreur à la mort d'un personnage qui venait de quitter la carte chez un invité.

## Nouveau

- **Boutiques à vente unique : une fois par joueur.** Ce qu'un marchand ne vend qu'une fois par monde (livres de
  compétence, recettes, quelques armes) peut être acheté une fois par CHAQUE joueur. Dans un monde déjà joué, ces
  objets reviennent au prochain réapprovisionnement du marchand. Pas dans une partie que personne d'autre ne joue.
  Pas essayé : marchand ambulant, marchands ajoutés par un autre mod.
- **Ce que le jeu compte « pour le joueur » est à chacun** : le prix du titre de terrain et du marteau de Garokk (qui
  double à chaque achat), les prix de musicien, la recette de cuisine inventée.

## À l'essai (case décochée au départ)

- **« Another player takes over when the host leaves »** (onglet « Server Setting »). La case suffit maintenant : elle
  entraîne la copie du monde chez les invités.
  - L'hébergeur quitte : il envoie sa dernière sauvegarde, l'invité désigné rouvre le monde chez lui, **les autres
    invités le rejoignent tout seuls** (au banc : 14 s puis 33 s).
  - **L'hébergeur plante** : les invités attendent son retour une minute, puis c'est la même chose (au banc : 94 s
    puis 97 s). Au plus deux minutes de jeu perdues, les mêmes pour tous.
  - **Joué à trois fenêtres sur un PC seulement.** Entre de vrais PC, retrouver le nouvel hébergeur passe par Steam :
    pas encore prouvé.
  - **Risque connu** : un joueur dont seul le lien tombe plus d'une minute rouvre une copie du monde pour lui seul ;
    un hébergeur qui a seulement perdu Internet continue de son côté. Laissez la case décochée si vous ne voulez pas
    essayer.

## Limites connues

- Pendant les quelques secondes de sa nuit « à soi », un joueur peut être attaqué : le monde continue pour les autres.
- Quand l'hébergeur dort seul, la date avance d'environ 40 minutes.
- Sur la carte du monde, quand tous voyagent ensemble, seuls les pas de l'hébergeur font avancer la date.
- Un joueur refusé par celui qui tient une carte reçoit encore le monde entier.
- Quand l'hébergeur et un invité se retrouvent sur une carte, l'écran de l'invité recharge (le monde entier est renvoyé), sauf si l'hébergeur coche la case « No world reload when the host and a player meet again ».
- Les récompenses des quêtes d'histoire et les cadeaux de dialogue ne vont qu'au premier joueur qui les obtient.
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

# Elin Together "independence" 0.26.652

Follows 0.26.621: **the bugs players reported on 10 October**, **one-time shop items for every player**, and the
**takeover of the world when the host leaves or crashes**, still to try. Nearly all of it was played on the test bench
(two or three windows on one PC), nothing between two PCs yet. If this version goes wrong, 0.26.621 stays online.
Built for Elin **EA 23.355** (the update of 11 October). **Every player must install this same zip.**
Back up your saves first: `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

## Fixed (played on the bench)

- **Frozen monster in a fight.** When a player attacked the monster that targeted another player, and that player did
  nothing, the monster stood still and died without fighting back. A monster now follows the fastest of the players
  fighting it (its target, or whoever attacked it, hit or miss); it does not go twice as fast when two players play,
  and it stops when nobody plays, as in single player. Also on a map kept by a guest.
- **"An item with the same key has already been added"** (the party list on screen): a character could be in the
  party twice.
- **Guests started with two purses.** A new guest has one, the tool belt's, like the host. Characters already made
  keep theirs.
- **The spells a guest laid on its hotbars were lost** from one session to the next.
- **Three bills paid in a row by a guest alone on another map: only one counted.** They all count. Worlds already
  hit keep a counter that is too high: not repaired yet.
- **A guest's mount.** When a mounted guest came back, the host made it ride an invisible copy of its mount while the
  real one stayed elsewhere with an old position: this is what made a world impossible to load. Rider and mount are
  tied together again, on the same tile.
- **Quest offers of a town**: after a reroll a guest kept the old ones on top of the new; and its "Reroll Quests"
  button spent the influence and drew nothing.
- **Hit points of the loser after a duel**: not always full in its own game.
- **A block recipe** (with a pillar or bridge variant) counted twice for the other players.
- The leash of a guest's companion brings it back beside its player (intermittent, not reproduced on demand).

## Fixed (reviewed, not proven by a trial)

- A recipe learnt by a player alone on another map reaches the others, and theirs reach that player.
- A level gained by a player away from the host is no longer refused.
- In a shared night ("everyone sleeps for itself" unticked), guests lose bleeding and poison too.
- An error at the death of a character that had just left the map, in a guest's game.

## New

- **One-time shop items: once per player.** What a merchant sells once per world (skill books, recipes, a few
  weapons) can be bought once by EACH player. In a world already played, these items come back at the merchant's
  next restock. Not in a game nobody else plays in. Not tried: travelling merchant, merchants added by another mod.
- **What the game counts "for the player" is each player's own**: the price of a land deed and of Garokk's hammer
  (which doubles with each one bought), a musician's prizes, the recipe a cook comes up with.

## To try (unticked at first)

- **"Another player takes over when the host leaves"** ("Server Setting" tab). The checkbox is enough now: it brings
  the copy of the world kept by the guests with it.
  - The host leaves: it sends its last save, the designated guest opens the world, **the other guests join it by
    themselves** (bench: 14 s then 33 s).
  - **The host crashes**: the guests wait a minute for it, then the same happens (bench: 94 s then 97 s). At most two
    minutes of play lost, the same for everyone.
  - **Played with three windows on one PC only.** Between real PCs, finding the new host goes through Steam: not
    proven yet.
  - **Known risk**: a player whose own link drops for more than a minute opens a copy of the world for itself; a host
    that only lost its Internet goes on on its side. Leave the checkbox unticked if you do not want to try.

## Known limits

- During the few seconds of a night "of its own", a player can be attacked: the world goes on for the others.
- When the host sleeps alone, the date moves by about 40 minutes.
- On the world map, when everyone travels together, only the host's steps move the date.
- A player refused by the holder of a map still receives the whole world.
- When the host and a guest meet on a map, the guest's screen reloads (the whole world is sent again), unless the host ticks "No world reload when the host and a player meet again".
- Story quest rewards and dialog gifts only go to the first player who gets them.
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
