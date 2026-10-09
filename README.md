# Elin Together — "independence" fork

English | [Français](README_fr.md) | [中文](README_zh.md) | [日本語](README_ja.md)

[![Latest release](https://img.shields.io/github/v/release/devmarcpro/elin-together?include_prereleases&label=latest%20release)](https://github.com/devmarcpro/elin-together/releases)

A fork of [Elin Together](https://github.com/ElinTogether/ElinTogether), the multiplayer mod for
[Elin](https://store.steampowered.com/app/2135150/Elin/), with one goal: **in game, no difference between the host
and the other players**. Everyone goes where they want, with their own companions, quests, fame and money, while
the world (story, home base, guilds) stays shared. The world itself no longer has to live on one player's PC.

The original mod keeps the whole party on the host's map and treats the other players as teammates of the host.
Its authors consider separate maps out of scope; this fork is where that is tried. All credit for the mod itself
goes to them (see [Credits](#credits)).

> **Status: experimental, not ready for a real release.** Every version is a pre-release, built for Elin's Nightly
> branch. Most of it is checked by automated in-game tests on one PC (two to five game windows). It has been played
> for real by one small group only, and each evening found defects the tests had missed. Several recent fixes were
> published **without having been played at all**. What is missing before a real release is listed in
> [What is left before a real release](#what-is-left-before-a-real-release). Back up your saves first:
> `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`.

**Contents**

1. [What it changes](#what-it-changes)
2. [Install](#install)
3. [Your first game together](#your-first-game-together)
4. [Keeping the world online: the depot](#keeping-the-world-online-the-depot)
5. [Games with mods](#games-with-mods)
6. [Settings](#settings)
7. [How it works](#how-it-works)
8. [Known limits](#known-limits)
9. [What is left before a real release](#what-is-left-before-a-real-release)
10. [How it is tested](#how-it-is-tested)
11. [If something goes wrong](#if-something-goes-wrong)
12. [Build](#build)
13. [Credits](#credits)

## What it changes

### Everyone goes where they want

- **Independent travel.** A player leaves for another map without the host. The map and what was done there are
  kept, progress is saved every minute while away, and chat works across maps.
- **Shared maps.** A player can join another player on their map, host or not. If the one holding the map leaves,
  another takes over.
- **Nobody is dragged along.** When the host changes map, the others stay where they are. A player enters a map by
  its entrance; nobody is teleported onto the host.
- **Each at their own pace.** A monster acts when the player it fights acts, not at the host's pace, and a guest
  walks as smoothly as the host.
- **Your time is your own.** A player who goes to bed sleeps at once; the night only passes for the world when
  everyone sleeps at the same time. When another player travels or sleeps, the date moves on, but you are no
  hungrier, your food does not rot and your quest deadlines do not move.

### To each player their own

- **Companions** follow the player who recruited them, whatever the way (dialog, monster ball, mount, bought
  animal), travel with them, count in that player's ally limit and obey that player's orders.
- **Random quests, fame and karma.** Five quests each, with their reward. Crime too: the player who did it loses
  the karma, and guards only chase that player.
- **Money.** The money of a shipping sale goes to whoever put the item in the chest; a guest pays a bill with its
  own gold.
- **Your character.** When joining, you get the character you played, with no question asked; a new player makes
  one on the game's creation screen. The host can also let players bring a character from one of their solo saves.
- **Your settings.** Windows, auto combat, bag sorting and companion orders stay yours at every map change and
  reconnection.

### One world for everyone

- **Story.** Story quests are in one log: anyone starts, advances and finishes them. Dialog memory, key items and
  debt are shared.
- **Home base.** A guest builds like the host (floors, walls, furniture, mining, digging, cutting, zones, the
  terrain tool) and what one builds is seen by the other at once. Research, hearth skills, policies, residents and
  chest settings can be managed by any player. The host can keep the base to itself with one checkbox.
- **Guilds, affinity, codex, bank.** Joining a guild counts for the group, an inhabitant's affinity is the same for
  all, the cards one player collects reach everyone's codex, and the bank shows the same content everywhere.
- **Dungeon quests.** Any player can take a quest that has its own zone. When one sets out, the other gets a Yes/No
  box to come along: the zone is shared and the reward goes to whoever took the quest.
- **Between players.** A trade window (both put items and gold, both confirm), duels where nobody dies and nothing
  is lost, and no killing outside a duel.

### A guest plays like a solo player

Dozens of fixes so that what works for the host works for a guest: death and will, the god's gifts, altars, traps,
spellbooks, the healer, blessings, investing, runes, auto-dump, tools held in hand, Kettle's copy shop, bringing a
companion back at the barman's, windows that used to open on the host's screen… The list is in
[`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md) (French).

### The world does not depend on the host's PC

- **A depot keeps the world**: a private GitHub repository, a shared folder, or a small server application. The
  first player there takes the world and hosts it, every save goes back, and when they leave the next one takes
  over.
- **A world that changes hands.** Whoever takes the world over plays their own character; the former host gets
  theirs back when joining. If someone already hosts, you are sent into their game instead of opening a copy.
- **Nothing left for the host to do.** The world saves itself every 2 minutes while others play, and a world
  already shared opens to Steam friends as soon as it is loaded.
- **A dropped link is harmless.** A guest who loses the connection comes back into the game by itself (it tries
  for 3 minutes).
- **The games stay in agreement.** No message is dropped when the link is saturated. Every 2 seconds the games
  compare a few numbers per map, and a map that keeps differing is reloaded in place.
- **A dedicated server**, like a Minecraft server: an Elin nobody plays keeps the world running.

### The same mods for everyone

- **The mods of the game are fetched by themselves** when you join, and Elin restarts once with them. A player can
  choose to keep them, so that this restart happens once and never again for that game.
- **Different Elin versions can play together.** Only the mod's version must be the same for everyone; players on
  another Elin version are let in with a warning.

Almost all of this is a **checkbox on the host's side**: unticked, the mod behaves like the original. See
[Settings](#settings).

## Install

You need Elin on Steam, on the **Nightly** branch (Steam → right-click Elin → Properties → Betas), and the
[YK Framework](https://steamcommunity.com/sharedfiles/filedetails/?id=3400020753) mod. Subscribing to
[Elin Together](https://steamcommunity.com/sharedfiles/filedetails/?id=3773298709) on the Workshop brings it along.
Launch Elin once after subscribing, then close it.

1. Download `ElinTogether-independance.zip` from the
   [Releases page](https://github.com/devmarcpro/elin-together/releases).
2. Unzip the whole folder and run `Installer.bat`. It finds Elin, copies the mod into `Elin\Package\Mod_ElinTogether`
   and switches from the Workshop version to this one in the game's mod list.
3. Launch Elin through Steam.

`Desinstaller.bat` switches back to the Workshop version; nothing is deleted, the former state is kept in
`Elin\_ElinTogether_sauvegarde`. The installer and its notes (`LISEZMOI.txt`) are in French; the steps are also on
each release page.

**On a Mac** (Elin in CrossOver, Whisky or Wine): download `ElinTogether-independance-mac.zip`, unzip it, open
Terminal, type `bash` and a space, drag `Installer-Mac.command` into the window and press Enter. It is the same
mod. Not tried on a real Mac yet.

**Every player must install the same release.** This fork does not talk to the Workshop version, nor to another
version of itself: a player on another version is refused with a message that names both versions. Each release is
built for one Elin build, named in its title.

**Updating**: download the new zip and run `Installer.bat` again. Your settings are kept.

## Your first game together

The mod's panel opens with the *Elin Together* button on the title screen, or Esc → Mods → Elin Together in game.
Its tabs are *Lobby*, *Server Setting* (the host's rules) and *Client Settings*, plus *Session Info* once a game is
open.

**The host**

1. Starts a new game or loads a save. A game can only be opened to others once the world has a **claimed land**:
   in a new game, talk to Ashland, pick up the deed he drops, read it and answer yes.
2. Opens the game: *Start Server* in the Lobby tab. A world that was already shared opens to Steam friends by
   itself when it is loaded.
3. Invites: *Invite Friend* in the Lobby tab, or lets friends use *Join Game* on their name in the Steam friends
   list.

**A guest**

1. Joins from the title screen: accepts a Steam invite, uses *Join Game* in the Steam friends list, or picks the
   game in the Lobby tab. *Join by address* is for a server.
2. The first time in that world, makes a character on the game's own creation screen. Later it gets that character
   back with no question.
3. If the game has Workshop mods the guest does not have, Elin closes and restarts once with them, then comes back
   into the game by itself: see [Games with mods](#games-with-mods). **This is not a crash.**

**Then**

- Everyone plays as in a solo game: walk out of the map alone, take quests at the board, build in the base, sleep
  when you want.
- The host's rules are in *Server Setting*; a change applies at once, for everyone.
- When the host leaves, the session ends for everyone unless the world is in a depot (next section).

## Keeping the world online: the depot

A depot keeps the shared world outside any player's saves, so the group does not depend on one person being
there. Each player who may host sets it once, in *Client Settings*: **Depot**, and **Depot key** when there is a
password or a key. A friend who only joins needs neither.

| Depot | What it takes | "Depot" setting |
|---|---|---|
| Private GitHub repository | A GitHub account for one player of the group. No PC left on, no port to open. | `github:owner/repository` |
| Elin Together Server (`ElinTogetherServer.exe`, in the zip) | A PC that stays on. Elin is not needed on it. TCP port 55557. | `host:55557`, or just *Join by address* |
| Shared folder | A folder every player can reach, shared or synced. | The path of the folder |

Then, in the Lobby tab:

- **Put this save on the server**, with a save loaded and the game not yet open to others: that save becomes the
  world of the depot. The game goes back to the title screen and loads the world again from the depot: from then on
  it is that world you play.
- **Take the world from the server and host it**, from the title screen: you get the latest world and host it;
  the others join you through Steam. If someone already hosts, the button names them and lets you join their game.
- Every save goes back to the depot, at most every 5 minutes and once more when quitting. When the host leaves,
  anyone can take the world. If the host crashes, the world frees itself after 3 minutes, and up to 5 minutes of
  play can be lost.

**With GitHub**, the player who owns the repository:

1. creates an empty **private** repository on github.com, only for this world (the mod refuses a public one);
2. creates a fine-grained access token (Settings → Developer settings → Fine-grained tokens) limited to that
   repository, with *Contents: Read and write*;
3. sets **Depot** to `github:owner/repository` and pastes the token into **Depot key**;
4. gives both to the friends who may host. They need no GitHub account.

The key stays in plain text in the mod's settings file on each PC; it only opens that repository and is revoked in
one click. A world over 20 MB zipped is refused. GitHub keeps every version of the world, which is a free backup
and also means the repository grows with each save: about one small commit a minute while someone hosts, and a
copy of the world every 5 minutes. Delete it and create a new one when it gets large. The depot also holds
`modlist.txt`, the mods of the world.

**Dedicated server.** `ElinTogetherServer.exe` has a second mode, "With Elin on this PC: the world runs all the
time": Elin runs behind without a window and the players use *Join by address* (`host:55556`, UDP). `Serveur.bat`
does the same with a game window. Windows only.

## Games with mods

Elin loads its mods when it starts, so a player cannot receive a mod in the middle of a run. This is what the mod
does about it.

**When you join** (or take a world from a depot), the mod compares your mods with the reference list: the
`modlist.txt` of the depot when the world comes from one, else the host's mods. If Workshop mods are missing:

1. they are downloaded by Steam, without your account subscribing to anything;
2. Elin closes and restarts **once** with exactly the mods of that game;
3. it brings you back into the game by itself. If it does not restart, start Elin by hand within half an hour.

By default your own mod list is back at the next start of Elin. The price: Elin restarts again at the first join
of **every** start. Two ways to avoid that:

- **Tick "Keep the mods of the game (subscribe on the Workshop)"** in *Client Settings*. Your Steam account
  subscribes to the mods of the game and they stay on in your own list. Elin restarts once more, then no longer for
  that game, even after closing Elin. To undo, unsubscribe on the Workshop or switch them off in the Mod Viewer.
- Or subscribe to those mods yourself on the Workshop.

To keep your own mods and only be told what differs, untick "Fetch the mods of the game by itself".

Good to know:

- A mod installed by hand, outside the Workshop, cannot be downloaded: its name is shown.
- The mod that brings the language you read the game in is never switched off.
- A join refused because of mods names them: missing, to install by hand, extra.
- **These mods are chosen by the host and their code runs on your PC: use this with people you trust.**
- AutoAct and Dynamic Riding are supported. For other mods, compatibility is the original's.

## Settings

### Host: the *Server Setting* tab

Each new behaviour has its own checkbox and a line of explanation in game. The rules are the host's and apply to
everyone as soon as they change.

| Checkbox | Default | Ticked |
|---|---|---|
| Independent travel | on | Everyone goes where they want, alone or together. Off: everyone follows the host. |
| Players choose their character when joining | off | A joining player picks one of its characters in this world, or makes a new one. Off: the one it played last. |
| Players can bring a character from their own saves | off | The character, its equipment, bag, gold, fame and karma. Not its companions, base, quests or bank. The save is only read. |
| Random quests, fame and karma per player | on | 5 random quests each, with their reward, fame and karma. Story quests stay shared. |
| Shipping per player | on | Shipping money goes to the player who put the item in. Off: all to the host. |
| Trade window between players | on | Click another player to trade items and gold. Both confirm. |
| Other players can use build mode | on | The other players build in the base; they pay the gold and the materials. Off: only the host builds. |
| Only the host manages the base | off | What the other players ask of the base (research, policies, residents, build mode…) is refused. |
| Duels between players | on | "Challenge to a duel" on another player's character. Nobody dies, both are healed, nothing is lost. |
| Players can kill each other | off | Off: a strike that would kill another player's character leaves it at 0 hit points. |
| Combat on each player's time | on | A monster acts when the player it fights acts: nobody waits. Takes over turn-based combat. |
| Each player on its own clock | on | A guest walks and acts as smoothly as the host, not at the pace of the network. |
| Every player walks at the pace of a solo game | on | The length of a step no longer depends on the other players' speed. |
| One date for the whole world | on | Time passed by a player alone on another map counts for everyone. Off: only the host's date counts. |
| What time does to the world happens once | on | Weather, expired quests, taxes, salaries and letters are handled by one game only. |
| Everyone sleeps for themselves | on | A player who goes to bed sleeps at once. The night passes for the world when all sleep at the same time. |
| Time only jumps when everyone jumps | on | A step on the world map only moves the date when all the players travel together. |
| Tax on the most famous player | on | The monthly tax is computed on the highest fame among the connected players. Off: on the host's. |
| Auto-dump spares hand and tool belt | on | Auto-dump leaves what you hold and what is in your tool belt. Off: as in the game. |
| Players come back by themselves after a connection loss | on | A player who loses the connection joins the game again by itself, for 3 minutes. |
| Repair the map by itself | on | A player whose map no longer matches the host's loads it again, at most once every 30 seconds. |
| The world is saved by itself while others play | on | Every 2 minutes while another player is in the game, and when the last one leaves. |
| The game opens to friends by itself when a world is loaded | on | Friends can join without the host starting the server by hand. |
| The other players keep a copy of the world | off | After each automatic save, every player's PC keeps a copy of the world, outside its own saves. |
| No world reload when the host and a player meet again (new) | off | The player stays on its map, or loads that one map, instead of the whole world. |
| Show the mods of the game to the players | on | The mod list is known before joining, and a refused player is told which mods differ. |
| Require the same Elin version | off | Players on another version of Elin are refused. Off: let in with a warning. |
| Turn-Based Combat | on | The original's rule. No effect while "Combat on each player's time" is on. |
| Shared Average Speed | off | The original's rule: one speed for all players, the average. |

### Player: the *Client Settings* tab

| Setting | Default | What it does |
|---|---|---|
| Bind Ping Key | P | The key that pings a place on the map for the others. |
| Depot | empty | Where the shared world is kept: `github:owner/repository`, `host:55557` or a folder. |
| Depot key | empty | The password of the server, or the GitHub access key. Never shown again once typed. |
| Fetch the mods of the game by itself | on | Missing Workshop mods are downloaded and Elin restarts once with the mods of the game. |
| Keep the mods of the game (subscribe on the Workshop) | off | Your Steam account subscribes to them and they stay on: no restart the next time. |

These settings are in `Elin\BepInEx\config\dk.elinplugins.elintogether.cfg`. That file holds the depot key in plain
text: do not share it.

## How it works

### The original design

One game, the host's, simulates the world. Every change (a step, a strike, an item picked up) leaves it as a small
message, a **delta**, that the other games apply. The other games send their actions to the host as requests. The
host is the reference: when two games disagree, its version wins.

The fork keeps that and adds the following.

### Leaving the host's map: zone leases

A player who walks out of the host's map asks the host for a **lease** on the map it goes to. With the lease, its
own game loads its copy of the world and simulates that map itself: monsters, time, items. Its link with the host
stays open for chat, quests and dialog memory.

- Every minute (a **checkpoint**), and when it comes back, it sends the map and its character to the host, which
  stays the reference. A crash loses what happened since the last checkpoint.
- A dungeon quest works the same way, on a new zone created for the occasion and destroyed afterwards.
- Each lease reserves a range of numbers for the quests created on that map, so two games never give the same
  number to two different quests.

### Meeting on a map: zone sessions

The holder of a lease can open that map to others: it becomes the host **for that map**, and the others connect to
it as guests, on top of their link with the real host. When the holder leaves, the lease is **handed over** to a
player who stays, and the others reconnect to that one. The same mechanism is used when the host itself leaves its
map: the first player who stays receives the lease.

When a player walks into a map someone else holds, it receives that map from its holder. Without the checkbox "No
world reload when the host and a player meet again", it first receives a fresh copy of the whole world, which is
why the screen reloads.

### To each player their own

- **Companions** carry the number of their player. They follow that player, travel with it and count in its ally
  limit only.
- **Random quests**: each game keeps in its journal only the random quests of its own player. The host stores
  everyone's in the save, with each player's fame and karma, and gives them back when the player arrives.
- **Shipping**: every item put in the chest is marked with the number of whoever put it. At 5 a.m. the host sells
  everything, keeps the accounts per player and sends each one its money, or keeps it for an absent player.
- **Karma and crime**: the game removes karma "from the player" where the action is settled. The mod finds the
  player behind the killer or behind the task and sends the penalty to that one. When a guard looks at someone,
  "is the player a criminal?" is asked about the player it looks at.
- **Combat and pace**: a monster bound to a player only moves when that player takes a turn. Each game runs on its
  own clock, so a guest's steps do not wait for the network.

### One world for everyone

- **Story quests**: the host holds the only journal. A dialog played by a guest runs in the guest's game; what it
  changes in the world (a quest that moves on, a land claimed, a character who joins) is sent to the host, which
  does it for everyone. What the dialog gives is created by the host at the guest's feet, once.
- **Base**: research, hearth skills, policies and resident settings are requests to the host, which checks, pays
  once and sends the result to everyone. In build mode, the guest's game prepares the task (place, mine, cut) and
  sends it to the game that holds the map, which carries it out with the guest's gold and materials. The game that
  simulates a map sends, at the end of each frame, the state of every tile that changed.
- **Affinity, guilds, codex**: the game of the player who acts computes, the host keeps the value and sends it to
  all.
- **Trade**: the game that simulates the map holds the "table". It receives the intentions (invite, accept, offer,
  confirm), sends the state to both players and makes the transfer in one go, after checking again that every item
  and every coin still exists.
- **Players against players**: a strike that would kill another player's character leaves it at 0 hit points,
  unless both are in a duel, where the fight ends at that floor and both are healed.

### Time

There is one date for the world: the furthest ahead. What time does to the world (weather, taxes, salaries,
expired quests) is done once, by one game. What time does to a player (hunger, food that rots, quest deadlines)
is counted per player, so another player's trip or night costs you nothing. A player who goes to bed sleeps its own
night in a few seconds; the world's night only passes when everyone sleeps at the same time.

### Joining, and staying in agreement

1. **Handshake**: the two games compare the mod's version (must be the same), Elin's version (a warning) and the
   list of mods.
2. **Character**: the host says which characters of this world are yours; a new player makes one.
3. **World copy**: the host sends its save; your game loads it.
4. **Map**: the host sends the state of its map, then the tile where your character stands. What the others did
   while you were loading is kept and replayed afterwards.

After that, every 2 seconds the games compare a few numbers per map (how many things, how many characters, a
checksum). A difference that lasts is written in the logs, and the map is loaded again in place, at most once every
30 seconds and never during a fight or with a menu open. A guest whose link drops tries the same game again every
5 seconds for 3 minutes.

### The depot

A depot is the world as one archive (`world.zip`) plus a lock that says who hosts (`lock.json`). The host renews
the lock every minute; a lock that has not been renewed for 3 minutes is free. With GitHub, every write names the
version it replaces: of two players writing at once, GitHub accepts one, and that refusal **is** the lock. Nothing
is ever forced, and the history keeps every world.

The save of a world remembers whose its local character is. Loaded by another player who has a character in it,
the two are exchanged before anything is played: the one who takes the world plays its own, the former one waits
for its player.

### Where things are on your PC

| What | Where |
|---|---|
| The mod | `Elin\Package\Mod_ElinTogether` |
| Its settings | `Elin\BepInEx\config\dk.elinplugins.elintogether.cfg` |
| Its logs | `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\ElinMP\Logs\Session_<date>.log` |
| The game's log | `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\Player.log` |
| Saves | `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin\Save` |
| The world taken from a depot | `…\Save\world_depot` (replaced each time the world is taken) |

The code is described file by file in [`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md), section 4 (French).

## Known limits

- **Played for real by one small group only.** Much of the newest work has only run on the test bench, and some of
  it not at all. "Not played" in a release note or a commit message means exactly that.
- **When the host leaves or crashes, no guest takes the world over by itself.** Someone takes it from the depot by
  hand.
- **One date for the world**, that of the player furthest ahead; only its effects (hunger, rot, deadlines) are per
  player. When the host sleeps alone, the date still moves by about 40 minutes. On the world map, when everyone
  travels together, only the host's steps move it.
- During the few seconds of a night of its own, a player can be attacked: the world goes on for the others.
- When the host and a guest meet again on a map, the guest's screen reloads. The checkbox "No world reload when
  the host and a player meet again" avoids it; it is new and off by default.
- On the host's screen, walking guests can move in jumps of three tiles.
- A player refused by the holder of a map still receives the whole world.
- **More than three players**: five game windows were tested on one PC, never five real PCs. Expect the game to
  slow down as players are added.
- Dungeon quests for two, when the guest took the quest: subdue, harvest and music quests. Defense quests are
  settled alone.
- Duels have no arena, betting or give-up button. Equipped items cannot be traded.
- Mods: Elin restarts once at the first join (see [Games with mods](#games-with-mods)). A mod removed from the game
  later stays subscribed for a player who chose to keep the mods. Not tried on Steam Deck, Linux or a Mac.
- A few rare conflicts are known and not fixed: two players building on the same tile, a mount existing twice
  after a trip.

The full list is in [`dev/DOCUMENTATION.md`](dev/DOCUMENTATION.md), section 6 (French).

## What is left before a real release

This fork is published as pre-releases for a group of friends. Here is what stands between that and a version one
could recommend to anyone.

**1. Play what was published without being played**

- Joining with a mounted character, and dialogs for a player with a language mod (0.26.605).
- "Keep the mods of the game" (0.26.608): the real subscription, then a second start with no restart.
- The story beyond its first steps: the fix that let the main quest move on again (0.26.597) was played up to the
  axe and the gold, not further.
- The Mac installer, on a real Mac. Steam Deck and Linux.

**2. Open leads**

- On a brand-new world, a guest who sleeps alone was seen waking up still exhausted and unable to act. It may be a
  tutorial dialog of the game that the test does not click; not settled.
- Three warnings of the mod when a saved game is loaded again with a guest ("Removing quest from player chara"):
  not looked at.
- The sleep test suite gives different failures from one run to the next on a slow PC: the suite or the mod, not
  settled.

**3. Missing pieces**

- **The world going on when the host leaves or crashes**: a guest taking over by itself, with no click. Designed,
  not started. Today the session ends and someone takes the world from the depot by hand.
- **A copy of the world on every player's PC by default**, so that a group with no depot loses nothing when the
  host is away. The checkbox exists and is off; the hand-over from such a copy is not done.
- **Mods**: the restart at the first join is still there the first time. A game whose mod list changes is not
  handled for players who kept the mods.
- **Duels**: arena, betting, give-up button.
- **Defense quests for two** when the guest took the quest.

**4. Proof on real PCs**

- Almost everything is proven on one PC, over the local network. Steam lobbies, invitations and relays between
  real PCs are only covered by the few real evenings.
- More than three players on real PCs, and how slow it gets.
- A long game: hours of play, a big world, a full base.

**5. Before recommending it**

- Follow Elin's updates: each release is built for one Nightly build.
- An installer and notes in English (they are in French).
- The Chinese and Japanese READMEs are shorter than this one and were not proofread by a native speaker.
- Decide what happens with the original project: this fork changes the heart of the mod and is not meant to be
  merged as it is.

## How it is tested

A change is meant to come with an in-game test, named in its commit message; when it was published without one,
the commit and the release note say "not played". The tests drive real game windows through a debug bridge (Debug
builds only): a host window and one to four guest windows on one PC.

- **Suites by subject** (`dev/_tools/*_suite.py`): travel, shared maps, quests, trade, base, building, duels,
  sleep, death, the depot, mods… Each prints what it checks and what it does **not** play like a player.
- **`first_time_suite.py`**: two players playing together for the first time on a brand-new world, through the
  game's own screens: character creation, the opening text, the deed, opening the game, the guest joining, Ashland's
  gifts, then save, both games closed, started again and joined again.
- **`dialog_walk_suite.py`**: a hunt. Each player walks to every character of the map and tries every choice of
  its menus; a loop, a game error, two games that no longer agree afterwards or a doubled item is a defect.
- **The bot** (`dev/_tools/bot.py`): plays at random on one window and checks that the games still agree.

What the bench cannot prove: Steam between two real PCs, a real mouse, and anything nobody thought of testing.
The real evenings found those. The rule of the project: read the logs before concluding, and say what was not
played.

## If something goes wrong

- The host unticks the checkbox involved: for that point the mod behaves like the original again.
- A player whose game no longer matches the others' types `emp.reconnect_self` in the console.
- Elin closed by itself at the first join: it is the restart for the mods, see [Games with mods](#games-with-mods).
- Report it [here](https://github.com/devmarcpro/elin-together/issues), with every player's `Player.log` and
  `ElinMP/Logs/Session_<date>.log` from `%USERPROFILE%\AppData\LocalLow\Lafrontier\Elin`. Please do not report
  fork problems to the original project.

## Build

Environment variables: `ElinGamePath` (root folder of the game) and `SteamContentPath`
(`steamapps/workshop/content`, for `YKFramework.dll`). .NET SDK 11.0 preview, see `global.json`.

```ps
git clone https://github.com/devmarcpro/elin-together
cd elin-together
dotnet restore ./ElinTogether --locked-mode
dotnet build ./ElinTogether -c ReleaseNightly
```

`dev/make_release.ps1` builds the two zips of a release, Windows and Mac. The development setup (several game
windows on one PC, the in-game test suites, the debug bridge) is described in [`dev/SETUP.md`](dev/SETUP.md)
(French). The day-by-day journal of the fork is [`dev/MODLOG.md`](dev/MODLOG.md) (French).

## Credits

The mod is the work of the Elin Together team: [DK](https://github.com/gottyduke) and
[Redgeioz](https://github.com/Redgeioz) (code, framework), [105gun](https://github.com/105gun) (code),
[Han](https://github.com/chuahan), Omega, [InuiDame](https://github.com/InuiDame),
[Drakeny](https://github.com/Drakeny) (testing), noa (Elin). MIT license, see [LICENSE](LICENSE).

The fork's changes were written with an AI coding assistant (Claude Code), directed by the fork's owner. No game
file and no decompiled game code is in this repository.
