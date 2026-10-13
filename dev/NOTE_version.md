# Elin Together « indépendance » 0.26.730

(English below / version anglaise plus bas)

Suite de la 0.26.716 : **la progression des quêtes d'histoire** (une quête ne recule plus, les journaux des joueurs se
rattrapent, les mondes abîmés sont réparés), et **un invité peut prendre une terre**. Joué au banc de test (deux
fenêtres sur un PC), les étapes de quêtes y sont posées à la main : aucune vraie quête n'a été jouée de bout en bout,
rien entre deux PC. **Cette version sort avant que toutes les séries de tests aient été rejouées** sur son code. Si
elle se passe mal, la 0.26.716 reste en ligne. Compilé pour Elin **EA 23.355**.
**Tous les joueurs doivent installer ce même zip.**

## Corrigé (joué au banc)

- **Quête de Vernis revenue en arrière, pas de dragon.** Un joueur seul sur une carte, avec un journal en retard,
  pouvait ramener la quête de tout le monde à une étape passée ; le boss de la mine ne revenant pas, la quête ne
  pouvait plus finir. Une quête ne recule plus. **Pour un monde déjà touché** : l'hébergeur lance la partie avec cette
  version (la quête est remise où la mine dit que le monde en était), redescend une fois à l'étage du boss, puis
  parle à Loytel à la base.
- **Le journal de chaque joueur suit celui du monde.** Toutes les 20 secondes l'hébergeur dit à chacun l'étape des
  quêtes d'histoire, celles qui sont finies et celles qui sont proposées. Un joueur en retard rattrape, même seul sur
  une autre carte ; un joueur en avance n'est jamais ramené en arrière.
- **Même réparation pour Nymelle et Lesimas** : Nymelle est remise à l'étape que ses étages ouverts prouvent ;
  l'étage du boss de Lesimas, boss déjà mort, fait avancer la quête.
- **Une terre prise pendant la partie n'était jamais connue des invités**, même prise par l'hébergeur : Vernis
  restait « à personne, sans base » chez eux, même en y revenant. Ils la reçoivent maintenant tout de suite.
- **Fin de la quête de Nasu faite par un invité** : elle plantait chez l'hébergeur (le sac à dos repris était le
  sien) et les récompenses étaient perdues.
- **Rêves de Lesimas** : deux joueurs sur la même carte faisaient avancer la quête chacun de son côté, un rêve
  était sauté.
- **Recette apprise en dormant par un invité** : comptée deux fois chez l'hébergeur.
- Quête d'impôt : l'invité connaît les factures du monde. Dette de Loytel prise par un invité : la cassette est pour
  lui. L'hébergeur ne refuse plus de commencer une quête d'histoire dont le numéro a changé.

## Nouveau

- **Un invité peut prendre une terre.** Il lit l'acte de propriété sur la carte de l'hébergeur, le jeu lui pose sa
  question, et son oui fait de la terre une base pour tout le monde. Encore refusé : seul sur une carte qu'il tient,
  et quand la case « seul l'hébergeur gère la base » est cochée.
- Le zip du bouton « Prepare a bug report » liste le groupe du joueur (pour trouver un compagnon compté en trop).

## Pas corrigé, signalé cette semaine

- Le nombre de compagnons affiché avec un de trop : pas reproduit. Envoyez le zip « Prepare a bug report ».
- Un invité qui ne pouvait pas miner : rien pour chercher, dites où et quoi.
- Un invité sur la carte du monde envoyé dans le donjon de l'hébergeur : pas reproduit, même demande.
- Loytel, quand un invité prend la dette, rejoint l'équipe comme compagnon de l'hébergeur.

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

# Elin Together "independence" 0.26.730

Follows 0.26.716: **story quest progression** (a quest no longer goes backwards, the players' journals catch up, damaged
worlds are repaired), and **a guest can claim land**. Played on the test bench (two windows on one PC), where quest
steps are set by hand: no real quest was played from end to end, nothing between two PCs. **This release ships before
every test series was replayed** on its code. If it goes wrong, 0.26.716 stays online. Built for Elin **EA 23.355**.
**Every player must install this same zip.**

## Fixed (played on the bench)

- **Vernis quest gone backwards, no dragon.** A player alone on a map, with a late journal, could take everyone's
  quest back to a past step; the mine boss does not come back, so the quest could not finish. A quest no longer goes
  backwards. **For a world already hit**: the host starts the game with this version (the quest is put back where the
  mine says the world was), goes down once to the boss floor, then talks to Loytel at the base.
- **Each player's journal follows the world's.** Every 20 seconds the host tells everyone the step of the story
  quests, those that are done and those on offer. A late player catches up, even alone on another map; a player ahead
  is never taken back.
- **Same repair for Nymelle and Lesimas**: Nymelle is put back at the step its open floors prove; the Lesimas boss
  floor, boss already dead, moves the quest on.
- **Land claimed during a game never reached the guests**, even claimed by the host: Vernis stayed "nobody's, no
  base" for them, even when coming back to it. They get it at once now.
- **End of the Nasu quest done by a guest**: it threw on the host (the backpack taken back was the host's) and the
  rewards were lost.
- **Dreams of Lesimas**: two players on one map each moved the quest on, a dream was skipped.
- **Recipe learnt while sleeping by a guest**: counted twice on the host.
- Tax quest: the guest knows the world's bills. Loytel's debt taken by a guest: the cassette is the guest's. The host
  no longer refuses to start a story quest whose number changed.

## New

- **A guest can claim land.** It reads the deed on the host's map, the game asks its question, and its yes makes the
  land a base for everyone. Still refused: alone on a map it keeps, and when "only the host manages the base" is
  ticked.
- The "Prepare a bug report" zip lists the player's party (to find a companion counted in excess).

## Not fixed, reported this week

- The ally count shown one too many: not reproduced. Send the "Prepare a bug report" zip.
- A guest who could not mine: nothing to go on, say where and what.
- A guest on the world map sent into the host's dungeon: not reproduced, same request.
- Loytel, when a guest takes the debt, joins the party as the host's companion.

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

