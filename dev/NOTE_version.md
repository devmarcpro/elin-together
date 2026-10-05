# Elin Together « indépendance » VERSION

(English below / version anglaise plus bas)

## Pour qui

Pour ceux qui jouent déjà avec la 0.26.399, et pour ceux qui veulent essayer à deux, ou plus, un Elin où l'invité
joue comme un joueur solo. **Tous les joueurs doivent installer le même zip** : cette version ne se connecte ni à
la version du Workshop, ni à une autre version du fork.

**État : expérimental.** Tout est testé sur un seul PC avec deux fenêtres du jeu (suites de tests en jeu, plus de
900 vérifications). Très peu de chose a été joué entre deux PC par Steam, et rien de ce qui est nouveau dans cette
version n'a été essayé à deux PC. Faites une copie de vos sauvegardes avant
(`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`).

## Ce qui est nouveau

- **Quêtes à donjon à deux.** Quand un joueur part en quête, l'autre voit une boîte Oui/Non (15 secondes, sans
  réponse = non) pour l'accompagner. Oui : la zone est commune, la récompense va à celui qui a pris la quête, et
  quand il sort tout le monde sort. L'accompagnant peut aussi rentrer seul. Dans les deux sens ; quand c'est
  l'invité qui a la quête : quêtes « subjuguer » seulement pour l'instant (récolte, musique et défense restent à
  régler seul).
- **Un invité joue comme un joueur solo.** Des dizaines de corrections d'égalité host / invité depuis la 0.26.399 (voir plus bas, et
  `dev/DOCUMENTATION.md`).
- **Consigne « ne pas s'éloigner » propre à chaque joueur** : c'est celle du joueur du compagnon, pas celle de
  l'host. (« Ne pas vagabonder » suit encore le jeu qui simule.)
- **Échange plus sûr** : il refuse ce que le jeu solo refuse de donner (objet qu'on ne peut pas lâcher, propriété
  d'un habitant, cadeau, objet lié), il refuse avant tout transfert si le sac de l'autre est plein, et il dit
  pourquoi. Les objets équipés ne s'échangent toujours pas : le jeu l'explique.
- **Base réglée par un invité** : la recherche et les compétences du foyer sont refusées avec un message (avant,
  l'invité payait sans rien obtenir).
- **Karma d'un visiteur** sur une carte tenue par un invité : les gardes le voient.
- **Messages plus clairs** : le second acheteur d'un même objet apprend qu'il est parti ; l'invité est prévenu de
  qui revient sur sa carte avant que son écran se recharge.

## Ce qui est corrigé

Pour un invité, qui avait des différences avec l'host :

- Mort : l'invité qui meurt chez l'host après le jour 90 perd une part de son or, lettre de testament comprise,
  comme en solo ; la prime de la guilde des guerriers va au joueur derrière le tueur.
- Dieu : chaque joueur reçoit une fois les cadeaux de son dieu ; la bénédiction est calculée comme celle d'un joueur ;
  les autels (invention, soin…) servent celui qui les touche ; quitter son dieu punit l'invité, une fois.
- Pièges et grimoires : tirés dans le jeu du joueur concerné (sommeil, cécité, paralysie demandés à l'host) ; un
  échec use le livre.
- Guérisseur payant et bénédiction des prêtresses : ils soignent et bénissent vraiment l'invité et ses compagnons.
- Un invité sous 20 % de vie ne prend plus peur et peut frapper.
- Gestes tenus en main, rejoués chez l'host : ticket de meuble, seringues, puits, stéthoscope, laisse ; pied-de-biche ;
  ticket d'hôtesse ; fenêtres de parchemin d'alias, de retour du vide et de caisse de récolte.
- Runes : la fenêtre s'ouvre chez celui qui s'en sert, la rune est posée et usée dans les deux jeux (celle de l'host
  n'arrivait jamais chez l'invité).
- Investir dans une boutique ou une ville arrive chez l'host (avant : payé pour rien).
- Rangement automatique propre à chaque joueur ; tri du sac propre à chaque joueur.
- Radio, juke-box, liste de lecture, livres des résidents et de l'équipe, détecteur, roue, vue de carte, pinceau :
  la fenêtre ne s'ouvre que chez celui qui s'en sert.
- Abattage et vol à la tire par un invité : l'endurance perdue est la sienne, plus celle de l'host (abattage : le karma aussi) ; un
  habitant frappé par un invité appelle ses voisins ; la faucille et la source chaude profitent à l'invité.
- Une recette lue par un joueur n'est apprise qu'une fois par l'autre ; la carte au trésor se cherche dans le sac
  de celui qui creuse.
- Noyade en eau profonde : l'invité perd son souffle comme un joueur.

## Ce qui n'est pas encore testé en vrai

Testé à deux fenêtres sur un seul PC, presque pas entre deux PC. Pas joué du tout :

- tout ce qui est nouveau, entre deux PC (voir la liste ci-dessous) ;
- les quêtes à donjon à deux : les tests prennent la quête et sortent par des appels directs au code du jeu, pas par
  le dialogue ni en marchant jusqu'au bord ; pas de test à trois joueurs ni de coupure de connexion dans la zone ;
- la carte au trésor d'un invité sur la carte du monde avec l'host ;
- noyade en eau profonde (pas d'eau profonde sur la carte de test), ticket d'hôtesse, fenêtres d'alias / de retour
  du vide / de caisse de récolte, karma d'un visiteur chez un invité, tri du sac, achat au même instant ;
- vol à la tire, investir dans une ville, pinceau, runes d'arme à distance ;
- le temps que met l'écran d'un invité à se recharger quand l'host revient (pas mesuré entre deux PC).

Limites connues : le temps du monde suit encore l'host ; lit, étiquettes de vente, notes et politiques réglés par un
invité ne valent que sur son écran ; quelques accidents rares (deux joueurs qui construisent sur la même case,
monture en double au retour d'un voyage). Liste complète : `dev/DOCUMENTATION.md`.

## À essayer à deux

1. Un deuxième joueur qui rejoint par Steam ; l'hébergeur qui part (un autre reprend) ; le mode avec Elin entre deux PC ;
   par Internet avec un mot de passe.
2. L'host prend une quête à donjon : l'invité répond Oui à la boîte, puis une autre fois Non.
3. L'invité prend une quête « subjuguer » : l'host répond Oui, puis une autre fois Non.
4. La carte au trésor, lue puis creusée par l'invité sur la carte du monde, avec l'host.
5. Un échange : un objet équipé, un sac plein, un objet qu'on ne peut pas lâcher.
6. L'invité règle la base (recherche, compétences du foyer) : il doit voir un message, sans rien payer.
7. L'host revient sur une carte tenue par l'invité : combien de temps l'écran de l'invité met-il à se recharger ?
8. Un visiteur chez un invité : les gardes le voient-ils comme criminel après un vol ?

Si quelque chose ne va pas : [les tickets](https://github.com/devmarcpro/elin-together/issues), avec les fichiers
`Player.log` et `ElinMP/Logs/Session_<date>.log` des deux joueurs.

## Installer

Il faut [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) et Elin sur le canal
**Nightly** (compilé pour EA 23.351). Chacun télécharge `ElinTogether-independance-VERSION.zip`, le décompresse et
lance `Installer.bat` (`Desinstaller.bat` fait l'inverse). **Tous les joueurs doivent avoir exactement ce zip.**
`LISEZMOI.txt` dans le zip explique le reste. Pour héberger : lancer Elin par Steam, charger une partie qui a un
terrain revendiqué, puis Échap → Mods → Elin Together.

---

# Elin Together "independence" VERSION

## Who it is for

For those already playing with 0.26.399, and for those who want to try, with one or more friends, an Elin where the
guest plays like a solo player. **Every player must install the same zip**: this version does not connect to the
Workshop version, nor to any other version of the fork.

**Status: experimental.** Everything is tested on one PC with two game windows (in-game test suites, over 900
checks). Very little has been played between two PCs over Steam, and nothing that is new in this version has been
tried on two PCs. Back up your saves first (`%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`).

## What is new

- **Dungeon quests for two.** When one player sets out on a quest, the other sees a Yes/No box (15 seconds, no
  answer = no) to come along. Yes: the zone is shared, the reward goes to whoever took the quest, and when that
  player leaves everyone leaves. The companion may also go home alone. It works both ways; when the guest took the
  quest: "subdue" quests only for now (harvest, music and defense quests are still settled alone).
- **A guest plays like a solo player.** Dozens of host / guest equality fixes since 0.26.399 (see below, and
  `dev/DOCUMENTATION.md`, in French).
- **"Keep distance" is each player's own**: it is the setting of the companion's player, not the host's. ("Don't
  wander" still follows the game that simulates.)
- **Safer trade**: it refuses what the solo game refuses to give away (an item you cannot drop, an inhabitant's
  property, a gift, a bound item), it refuses before moving anything when the other's bag is full, and it says
  why. Equipped items still cannot be traded: the game explains it.
- **Home base settings changed by a guest**: research and hearth skills are refused with a message (before, the
  guest paid and got nothing).
- **A visitor's karma** on a map held by a guest: the guards see it.
- **Clearer messages**: the second buyer of the same item learns it is gone; the guest is told who is coming to its
  map before its screen reloads.

## What is fixed

For a guest, who differed from the host:

- Death: a guest who dies on the host's map after day 90 loses a share of its gold, will letter included, as in
  solo; the fighters' guild bounty goes to the player behind the killer.
- God: each player gets the gifts of its god once; the blessing is worked out as for a player; shrines (invention,
  healing...) serve whoever touches them; leaving one's god punishes the guest, once.
- Traps and spellbooks: rolled in the game of the player concerned (sleep, blindness, paralysis asked of the
  host); a failure uses up the book.
- The paid healer and the priestesses' blessing really heal and bless the guest and its companions.
- A guest under 20% hit points no longer takes fright and can still strike.
- Held-item acts, replayed on the host: furniture ticket, syringes, well, stethoscope, leash; crowbar; hostess
  ticket; windows of the alias scroll, the void return and the harvest chest.
- Runes: the window opens for the user, the rune is set and used up in both games (the host's own rune never
  reached the guest).
- Investing in a shop or a town reaches the host (before: paid for nothing).
- Auto-dump is each player's own; bag sorting is each player's own.
- Radio, jukebox, playlist, resident and roster books, detector, wheel, map view, brush: the window opens only for
  the one who uses them.
- Slaughter and pickpocketing by a guest: the stamina lost is the guest's, no longer the host's (slaughter: the karma too); an
  inhabitant struck by a guest calls its neighbours; the sickle and the hot spring benefit the guest.
- A recipe read by one player is learnt once by the other; a treasure map is looked for in the bag of whoever digs.
- Drowning in deep water: the guest loses its breath as a player does.

## What has not been tested for real yet

Tested with two windows on one PC, almost not between two PCs. Not played at all:

- everything new, between two PCs (see the list below);
- dungeon quests for two: the tests take the quest and leave through direct calls to the game's code, not through
  the dialog or by walking to the edge; no three-player test, no connection loss inside the zone;
- a guest's treasure map on the world map with the host;
- drowning in deep water (no deep water on the test map), hostess ticket, alias / void return / harvest chest
  windows, a visitor's karma on a guest's map, bag sorting, two purchases at the same instant;
- pickpocketing, investing in a town, the brush, ranged-weapon runes;
- how long a guest's screen takes to reload when the host returns (not measured between two PCs).

Known limits: the world's clock still follows the host; beds, sale tags, notes and policies set by a guest only
apply on its own screen; a few rare accidents (two players building on the same tile, a mount existing twice after
a trip). Full list: `dev/DOCUMENTATION.md`.

## To try with two players

1. A second player joining over Steam; the host leaving (another takes over); the mode with Elin between two PCs;
   over the Internet with a password.
2. The host takes a dungeon quest: the guest answers Yes to the box, then No another time.
3. The guest takes a "subdue" quest: the host answers Yes, then No another time.
4. The treasure map, read then dug by the guest on the world map, with the host.
5. A trade: an equipped item, a full bag, an item that cannot be dropped.
6. The guest changes the base (research, hearth skills): it should see a message and pay nothing.
7. The host returns to a map held by the guest: how long does the guest's screen take to reload?
8. A visitor on a guest's map: do the guards see it as a criminal after a theft?

If something goes wrong: [the issues](https://github.com/devmarcpro/elin-together/issues), with both players'
`Player.log` and `ElinMP/Logs/Session_<date>.log`.

## Install

Requires [YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) and Elin on the
**Nightly** branch (built for EA 23.351). Each player downloads `ElinTogether-independance-VERSION.zip`, unzips it
and runs `Installer.bat` (`Desinstaller.bat` switches back). **Every player must have exactly this zip.** The
installer and its notes (`LISEZMOI.txt` in the zip) are in French. To host: launch Elin through Steam, load a save
that has a claimed land, then Esc → Mods → Elin Together.
