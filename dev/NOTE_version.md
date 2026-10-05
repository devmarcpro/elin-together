# Elin Together « indépendance » 0.26.463

(English below / version anglaise plus bas)

## Pour qui

Pour ceux qui jouent déjà avec la 0.26.442, et pour ceux qui veulent essayer à deux, ou plus, un Elin où l'invité
joue comme un joueur solo. **Tous les joueurs doivent installer le même zip** : cette version ne se connecte ni à
la version du Workshop, ni à une autre version du fork. Elle est compilée pour la nouvelle version d'Elin
(EA 23.352).

**État : expérimental.** Tout est testé sur un seul PC avec deux fenêtres du jeu (suites de tests en jeu). Très peu
de chose a été joué entre deux PC par Steam, et rien de ce qui est nouveau dans cette version n'a été essayé à deux
PC. Faites une copie de vos sauvegardes avant (`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`).

## Ce qui est nouveau

- **Versions d'Elin différentes : plus de mur.** Seule la version du MOD doit être la même pour tous. Deux joueurs
  qui n'ont pas la même version d'Elin peuvent se connecter ; ils sont prévenus par un avertissement. Une case côté
  host (« Require the same Elin version », décochée par défaut) redemande la même version d'Elin. Testé en connexion
  locale seulement ; par le salon Steam : pas joué.
- **Base réglée par un invité.** La recherche et les compétences du foyer sont de vraies demandes à l'host : il
  vérifie, paie une fois, et tout le monde voit le résultat (la 0.26.442 refusait avec un message). Les politiques,
  les lits, les étiquettes de vente, les notes, le nom de la base, de la faction et d'un téléporteur réglés par un
  joueur sont vus par l'autre, dans les deux sens.
- **« Ne pas vagabonder » propre à chaque joueur**, comme « garder ses distances » : c'est le réglage du joueur du
  compagnon, pas celui de l'host.
- **Quêtes à donjon à deux quand c'est l'invité qui a la quête** : en plus de « subjuguer », les quêtes de **récolte**
  et de **musique** se jouent à deux. La défense reste à faire seul.

## Ce qui est corrigé

- Un objet offert par un invité, pris dans une pile, arrive bien chez l'host (avant : le don n'avait aucun effet).
- Une monture déjà prise est refusée à un second cavalier.
- Un invité qui taille un rondin à la hache obtient ses planches, et le rondin est usé.
- La prière d'un invité soigne aussi ses compagnons.
- La nourriture dans le sac d'un invité vieillit comme celle de l'host.

## Ce qui n'est pas encore testé en vrai

Testé à deux fenêtres sur un seul PC. **Rien de ce qui est nouveau n'a été joué entre deux PC.** Pas joué du tout :

- les versions d'Elin différentes par le salon Steam (seule la connexion locale a été essayée) ;
- le nom de la faction réglé par un invité ; le fait de ne pas courir après un ennemi hors de vue (« ne pas
  vagabonder » lui-même) ; le score d'un concert dans une quête de musique jouée par l'host ;
- les quêtes à donjon à deux : les tests prennent la quête et sortent par des appels directs au code du jeu, pas par
  le dialogue ni en marchant jusqu'au bord ; pas de test à trois joueurs ni de coupure de connexion dans la zone ;
- la quête de récolte prise par l'invité : un test a échoué une fois sur Elin 23.352 (ce que l'invité livre n'a pas
  compté), pas encore rejoué ; à surveiller ;
- la carte au trésor d'un invité sur la carte du monde avec l'host ;
- noyade en eau profonde, ticket d'hôtesse, fenêtres d'alias / de retour du vide / de caisse de récolte, karma d'un
  visiteur chez un invité, tri du sac, achat au même instant ;
- vol à la tire, investir dans une ville, pinceau, runes d'arme à distance ;
- le temps que met l'écran d'un invité à se recharger quand l'host revient (pas mesuré entre deux PC).

Limites connues : le temps du monde suit encore l'host ; la défense à deux n'existe pas ; la servante, le type et
la mise en réserve d'un résident, et les réglages des coffres, faits par un invité, ne valent que sur son écran ; le
mode construction d'un invité (sols, murs, marques miner / couper) ne se fait que sur son écran : pour l'instant,
c'est l'host qui doit construire la base ; quelques accidents rares (deux joueurs qui construisent sur la même case,
monture en double au retour d'un voyage). Liste complète : `dev/DOCUMENTATION.md`.

## À essayer à deux

1. Un deuxième joueur qui rejoint par Steam ; l'hébergeur qui part (un autre reprend) ; le mode avec Elin entre deux
   PC ; par Internet avec un mot de passe.
2. Quêtes à donjon à deux, dans les deux sens : l'host prend une quête, l'invité répond Oui à la boîte, puis une
   autre fois Non ; l'invité prend une quête « subjuguer », « récolte » ou « musique », l'host répond Oui, puis une
   autre fois Non.
3. L'host revient sur une carte tenue par l'invité : combien de temps l'écran de l'invité met-il à se recharger ?
   (à chronométrer)
4. La carte au trésor, lue puis creusée par l'invité sur la carte du monde, avec l'host.
5. Ce qui n'a jamais été joué : un visiteur chez un invité (les gardes le voient-ils comme criminel après un vol ?),
   le tri du sac, « déjà vendu » quand deux joueurs achètent au même instant, le message qui nomme l'host avant le
   rechargement, le ticket d'hôtesse, les fenêtres d'alias / de retour du vide / de caisse de récolte, l'eau
   profonde, le vol à la tire, investir dans une ville, le pinceau, les runes d'arme à distance, le concert d'une
   quête de musique.
6. L'invité règle la base : recherche et compétences du foyer (payé une fois, résultat vu chez l'host), politiques,
   lit, étiquette de vente, note, nom de la base et d'un téléporteur : l'autre joueur doit le voir.
7. Un échange : un objet équipé, un sac plein, un objet qu'on ne peut pas lâcher.
8. Un invité qui offre un objet pris dans une pile (le don doit arriver chez l'host) ; une monture déjà prise.
9. Deux joueurs sur une version d'Elin différente : l'avertissement, la case de l'host, et un MOD de version
   différente qui doit rester refusé.

Si quelque chose ne va pas : [les tickets](https://github.com/devmarcpro/elin-together/issues), avec les fichiers
`Player.log` et `ElinMP/Logs/Session_<date>.log` des deux joueurs.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly** (compilé pour EA 23.352). Chacun télécharge `ElinTogether-independance-0.26.463.zip`, le décompresse et
lance `Installer.bat` (`Desinstaller.bat` fait l'inverse). **Tous les joueurs doivent avoir exactement ce zip.**
Une version d'Elin un peu différente entre joueurs n'empêche plus de se connecter. `LISEZMOI.txt` dans le zip
explique le reste. Pour héberger : lancer Elin par Steam, charger une partie qui a un terrain revendiqué, puis
Échap → Mods → Elin Together.

---

# Elin Together "independence" 0.26.463

## Who it is for

For those already playing with 0.26.442, and for those who want to try, with one or more friends, an Elin where the
guest plays like a solo player. **Every player must install the same zip**: this version does not connect to the
Workshop version, nor to any other version of the fork. It is built for the new version of Elin (EA 23.352).

**Status: experimental.** Everything is tested on one PC with two game windows (in-game test suites). Very little
has been played between two PCs over Steam, and nothing that is new in this version has been tried on two PCs. Back
up your saves first (`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`).

## What is new

- **Different Elin versions: no more wall.** Only the MOD's version must be the same for everyone. Two players who
  do not have the same version of Elin can connect; they are told by a warning. A checkbox on the host's side
  ("Require the same Elin version", unchecked by default) asks for the same Elin version again. Tested on a local
  connection only; through the Steam lobby: not played.
- **Home base settings changed by a guest.** Research and hearth skills are real requests to the host: it checks,
  pays once, and everyone sees the result (0.26.442 refused with a message). Policies, beds, sale tags, notes, the
  name of the base, of the faction and of a teleporter set by one player are seen by the other, both ways.
- **"Don't wander" is each player's own**, like "keep distance": it is the setting of the companion's player, not
  the host's.
- **Dungeon quests for two when the guest took the quest**: besides "subdue", **harvest** and **music** quests can
  be played by two. Defense quests are still settled alone.

## What is fixed

- An item given by a guest, taken out of a stack, now reaches the host (before: the gift had no effect).
- A mount that already carries someone is refused to a second rider.
- A guest chopping a log with an axe gets its planks, and the log is used up.
- A guest's prayer heals its companions too.
- Food in a guest's bag goes off like the host's.

## What has not been tested for real yet

Tested with two windows on one PC. **Nothing that is new has been played between two PCs.** Not played at all:

- different Elin versions through the Steam lobby (only the local connection was tried);
- the faction name set by a guest; not chasing an enemy out of sight ("don't wander" itself); the score of a
  concert in a music quest played by the host;
- dungeon quests for two: the tests take the quest and leave through direct calls to the game's code, not through
  the dialog or by walking to the edge; no three-player test, no connection loss inside the zone;
- the harvest quest taken by the guest: one test failed once on Elin 23.352 (what the guest delivered did not
  count), not replayed yet; keep an eye on it;
- a guest's treasure map on the world map with the host;
- drowning in deep water, hostess ticket, alias / void return / harvest chest windows, a visitor's karma on a
  guest's map, bag sorting, two purchases at the same instant;
- pickpocketing, investing in a town, the brush, ranged-weapon runes;
- how long a guest's screen takes to reload when the host returns (not measured between two PCs).

Known limits: the world's clock still follows the host; defense quests for two do not exist; the maid, a resident's
type and reserve, and chest settings, changed by a guest, only apply on its own screen; a guest's build mode (floors,
walls, mine / chop marks) only works on its own screen: for now, the host has to build the base; a few rare
accidents (two players building on the same tile, a mount existing twice after a trip). Full list:
`dev/DOCUMENTATION.md` (in French).

## To try with two players

1. A second player joining over Steam; the host leaving (another takes over); the mode with Elin between two PCs;
   over the Internet with a password.
2. Dungeon quests for two, both ways: the host takes a quest, the guest answers Yes to the box, then No another
   time; the guest takes a "subdue", "harvest" or "music" quest, the host answers Yes, then No another time.
3. The host returns to a map held by the guest: how long does the guest's screen take to reload? (to be timed)
4. The treasure map, read then dug by the guest on the world map, with the host.
5. What has never been played: a visitor on a guest's map (do the guards see it as a criminal after a theft?), bag
   sorting, "already sold" when two players buy at the same instant, the message that names the host before the
   reload, hostess ticket, alias / void return / harvest chest windows, deep water, pickpocketing, investing in a
   town, the brush, ranged-weapon runes, the concert of a music quest.
6. The guest changes the base: research and hearth skills (paid once, result seen by the host), policies, bed, sale
   tag, note, name of the base and of a teleporter: the other player must see it.
7. A trade: an equipped item, a full bag, an item that cannot be dropped.
8. A guest giving an item taken out of a stack (the gift must reach the host); a mount that is already taken.
9. Two players on different Elin versions: the warning, the host's checkbox, and a MOD of a different version that
   must still be refused.

If something goes wrong: [the issues](https://github.com/devmarcpro/elin-together/issues), with both players'
`Player.log` and `ElinMP/Logs/Session_<date>.log`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the
**Nightly** branch (built for EA 23.352). Each player downloads `ElinTogether-independance-0.26.463.zip`, unzips it
and runs `Installer.bat` (`Desinstaller.bat` switches back). **Every player must have exactly this zip.** A slightly
different Elin version between players no longer prevents connecting. The installer and its notes (`LISEZMOI.txt` in
the zip) are in French. To host: launch Elin through Steam, load a save that has a claimed land, then Esc → Mods →
Elin Together.
